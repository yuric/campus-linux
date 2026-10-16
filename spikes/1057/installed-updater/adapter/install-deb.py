#!/usr/bin/python3 -I
"""Disposable #1057 fixture installer. Fixed identity/trust; no production use."""
import fcntl
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile

PACKAGE = "campus-updater-1057"
TRUST = Path("/etc/campus-updater-1057")
LIB = Path("/usr/lib/campus-updater-1057")
STATE = Path("/var/lib/campus-updater-1057")
APP = Path("/usr/bin/campus-updater-1057")
HELPER = LIB / "inert-helper.txt"
ENV = {"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "LANG": "C", "LC_ALL": "C"}
VERSIONS = {"1.0.0", "2.0.0", "3.0.0"}
# Admission narrows these defensive ceilings to the actually measured fixtures.
ABSOLUTE_PACKAGE_LIMIT = 256 * 1024 * 1024
ABSOLUTE_DATA_LIMIT = 512 * 1024 * 1024
SIGNATURE_LIMIT = 8192
ADMISSION_LIMIT = 1024 * 1024


class Refused(Exception):
    pass


def require(condition, reason):
    if not condition:
        raise Refused(reason)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def root_path(path, directory=False):
    """Reject symbolic links or writable components in a fixed trusted path."""
    path = Path(path)
    require(path.is_absolute(), "trust_path_not_absolute")
    for component in reversed((path, *path.parents)):
        info = component.lstat()
        require(info.st_uid == 0 and not info.st_mode & 0o022,
                "trust_path_not_root_owned_readonly")
        require(not stat.S_ISLNK(info.st_mode), "trust_path_symlink")
        if component != path or directory:
            require(stat.S_ISDIR(info.st_mode), "trust_path_not_directory")
        else:
            require(stat.S_ISREG(info.st_mode), "trust_path_not_regular")


def open_regular(path, limit, caller_uid=None):
    require(Path(path).is_absolute(), "source_path_not_absolute")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    try:
        info = os.fstat(fd)
        require(stat.S_ISREG(info.st_mode), "source_not_regular")
        require(0 < info.st_size <= limit, "source_size_outside_measured_bound")
        if caller_uid is not None:
            require(info.st_uid == caller_uid, "source_not_owned_by_caller")
        return fd
    except BaseException:
        os.close(fd)
        raise


def copy_to_stage(source, destination, limit, caller_uid):
    source_fd = open_regular(source, limit, caller_uid)
    total = 0
    hashed = hashlib.sha256()
    try:
        with os.fdopen(source_fd, "rb", closefd=True) as incoming:
            output_fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                                os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
            with os.fdopen(output_fd, "wb", closefd=True) as output:
                while True:
                    block = incoming.read(min(1024 * 1024, limit + 1 - total))
                    if not block:
                        break
                    total += len(block)
                    require(total <= limit, "source_grew_past_measured_bound")
                    output.write(block)
                    hashed.update(block)
                output.flush()
                os.fsync(output.fileno())
    except BaseException:
        Path(destination).unlink(missing_ok=True)
        raise
    return total, hashed.hexdigest()


def read_limited(path, limit):
    fd = open_regular(path, limit)
    with os.fdopen(fd, "rb") as stream:
        value = stream.read(limit + 1)
    require(len(value) <= limit, "trusted_file_grew")
    return value


def ar_members(data):
    require(data[:8] == b"!<arch>\n", "not_debian_ar")
    offset, members = 8, {}
    while offset < len(data):
        header = data[offset:offset + 60]
        require(len(header) == 60 and header[58:] == b"`\n", "invalid_ar_header")
        name = header[:16].decode("ascii").strip().rstrip("/")
        require(name not in members and name in {
            "debian-binary", "control.tar.gz", "control.tar.xz", "control.tar",
            "data.tar.gz", "data.tar.xz", "data.tar"}, "unexpected_ar_member")
        size = int(header[48:58].decode("ascii").strip())
        require(size >= 0, "negative_ar_member_size")
        offset += 60
        require(offset + size <= len(data), "truncated_ar_member")
        members[name] = data[offset:offset + size]
        offset += size + (size % 2)
    require(offset == len(data), "trailing_ar_bytes")
    require(len(members) == 3 and members.get("debian-binary") == b"2.0\n",
            "unexpected_debian_ar_shape")
    return members


def canonical_name(name):
    while name.startswith("./"):
        name = name[2:]
    name = name.rstrip("/")
    require(not name.startswith("/") and ".." not in PurePosixPath(name).parts,
            "unsafe_archive_path")
    require(str(PurePosixPath(name)) == name or name == "", "noncanonical_archive_path")
    return name


def allowed_data_path(name, directory):
    fixed = {"usr/bin/campus-updater-1057", "usr/lib/campus-updater-1057/inert-helper.txt",
             "usr/share/applications/campus-updater-1057.desktop"}
    icon = re.fullmatch(r"usr/share/icons/hicolor/[1-9][0-9]*x[1-9][0-9]*/apps/campus-updater-1057\.png", name)
    directories = {"", "usr", "usr/bin", "usr/lib", "usr/lib/campus-updater-1057",
                   "usr/share", "usr/share/applications", "usr/share/icons", "usr/share/icons/hicolor"}
    icon_directory = re.fullmatch(r"usr/share/icons/hicolor/[1-9][0-9]*x[1-9][0-9]*(/apps)?", name)
    return (name in directories or icon_directory is not None) if directory else (name in fixed or icon is not None)


def tar_schema(blob, control, data_limit):
    entries, names, total, control_text = [], set(), 0, None
    with tarfile.open(fileobj=io.BytesIO(blob), mode="r:*") as archive:
        for member in archive:
            require(len(entries) < 128, "archive_member_count_bound")
            name = canonical_name(member.name)
            require(name not in names, "duplicate_archive_path")
            names.add(name)
            require(member.isfile() or member.isdir(), "archive_special_file_or_link")
            require(member.uid == 0 and member.gid == 0, "archive_nonroot_owner")
            require(not member.mode & 0o7022, "archive_unsafe_mode")
            require(not member.pax_headers, "archive_pax_extensions")
            directory = member.isdir()
            if control:
                require((directory and name == "") or
                        (not directory and name in {"control", "md5sums"}),
                        "package_scripts_or_unreviewed_control_member")
            else:
                require(allowed_data_path(name, directory), "unreviewed_fixture_data_path")
            require(0 <= member.size <= data_limit, "archive_member_size_bound")
            total += member.size
            require(total <= data_limit, "archive_expanded_size_bound")
            entry = {"path": name, "type": "directory" if directory else "file",
                     "mode": member.mode, "uid": member.uid, "gid": member.gid,
                     "size": member.size}
            if not directory:
                content = archive.extractfile(member).read(data_limit + 1)
                require(len(content) == member.size, "archive_content_size_mismatch")
                entry["sha256"] = digest(content)
                if control and name == "control":
                    control_text = content.decode("utf-8")
            entries.append(entry)
    return sorted(entries, key=lambda entry: entry["path"]), total, control_text


def package_record(data, data_limit=ABSOLUTE_DATA_LIMIT):
    require(0 < len(data) <= ABSOLUTE_PACKAGE_LIMIT, "fixture_package_absolute_bound")
    members = ar_members(data)
    control_names = [name for name in members if name.startswith("control.tar")]
    data_names = [name for name in members if name.startswith("data.tar")]
    require(len(control_names) == len(data_names) == 1, "missing_package_archive")
    controls, control_size, control_text = tar_schema(members[control_names[0]], True, 65536)
    payload, payload_size, _ = tar_schema(members[data_names[0]], False, data_limit)
    require(control_text is not None, "missing_control")
    # Use Debian's actual parser for installation; extract only fixed identity fields here.
    fields = {}
    for line in control_text.splitlines():
        if line.startswith((" ", "\t")) or not line:
            continue
        key, sep, value = line.partition(":")
        require(sep and key not in fields, "duplicate_or_invalid_control_field")
        fields[key] = value.strip()
    require(fields.get("Package") == PACKAGE, "wrong_package_identity")
    require(fields.get("Version") in VERSIONS, "unreviewed_fixture_version")
    require(fields.get("Architecture") in {"arm64", "amd64"}, "unreviewed_fixture_architecture")
    require(not ({"Pre-Depends", "Conflicts", "Breaks", "Replaces", "Provides", "Essential"} & fields.keys()),
            "unreviewed_package_relation")
    paths = {entry["path"]: entry for entry in payload}
    require(paths.get(str(APP)[1:], {}).get("type") == "file", "missing_fixture_app")
    require(paths.get(str(HELPER)[1:], {}).get("type") == "file", "missing_fixture_helper")
    require(paths[str(APP)[1:]]["mode"] == 0o755, "fixture_app_mode")
    require(paths[str(HELPER)[1:]]["mode"] == 0o644, "fixture_helper_mode")
    return {"sha256": digest(data), "size": len(data), "version": fields["Version"],
            "architecture": fields["Architecture"], "expanded_data_bytes": payload_size,
            "expanded_control_bytes": control_size, "ar_members": sorted(members),
            "control": controls, "data": payload}


def validate_admission(value):
    require(set(value) == {"schema", "package", "architecture", "max_package_bytes",
                           "max_expanded_data_bytes", "packages"}, "admission_schema")
    require(value["schema"] == 1 and value["package"] == PACKAGE, "admission_identity")
    require(value["architecture"] in {"arm64", "amd64"}, "admission_architecture")
    records = value["packages"]
    require(len(records) == 3 and {record["version"] for record in records} == VERSIONS,
            "admission_versions")
    require(all(record["architecture"] == value["architecture"] for record in records),
            "admission_mixed_architecture")
    require(len({record["sha256"] for record in records}) == 3, "admission_duplicate_hash")
    require(value["max_package_bytes"] == max(record["size"] for record in records) <= ABSOLUTE_PACKAGE_LIMIT,
            "admission_measured_package_bound")
    require(value["max_expanded_data_bytes"] == max(record["expanded_data_bytes"] for record in records) <= ABSOLUTE_DATA_LIMIT,
            "admission_measured_data_bound")
    return value


def run(command):
    return subprocess.run(command, env=ENV, cwd="/", stdin=subprocess.DEVNULL,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          text=True, timeout=120, check=False)


def verify_staged(package, signature, admission, verifier=run):
    package_bytes = read_limited(package, admission["max_package_bytes"])
    package_hash = digest(package_bytes)
    admitted = next((record for record in admission["packages"] if record["sha256"] == package_hash), None)
    require(admitted is not None, "package_not_in_exact_fixture_admission")
    require(admitted["size"] == len(package_bytes), "admitted_size_mismatch")
    verified = verifier([str(LIB / "verify-signature"), str(TRUST / "public-key.txt"),
                         str(package), str(signature)])
    require(verified.returncode == 0, "signature_verification_failed")
    signed = json.loads(verified.stdout)
    require(set(signed) == {"version"}, "signature_verifier_output_schema")
    record = package_record(package_bytes, admission["max_expanded_data_bytes"])
    require(record == admitted, "exact_fixture_schema_mismatch")
    require(signed["version"] == record["version"], "signed_version_differs_from_package")
    return record


def installed_identity(admission, runner=run):
    query = runner(["/usr/bin/dpkg-query", "--show", "--showformat=${db:Status-Status}\t${Version}\t${Architecture}", PACKAGE])
    require(query.returncode == 0, "fixture_not_installed")
    parts = query.stdout.strip().split("\t")
    require(len(parts) == 3 and parts[0] == "installed", "fixture_not_fully_installed")
    version, architecture = parts[1:]
    require(version in VERSIONS and architecture == admission["architecture"], "installed_identity_unreviewed")
    # An existing maintainer script would also run during an upgrade; forbid it.
    for extension in ("preinst", "postinst", "prerm", "postrm", "triggers"):
        require(not Path(f"/var/lib/dpkg/info/{PACKAGE}.{extension}").exists(), "installed_maintainer_script")
    return version


def require_forward_version(candidate, installed, runner=run):
    comparison = runner(["/usr/bin/dpkg", "--compare-versions", candidate, "gt", installed])
    require(comparison.returncode == 0, "signed_same_or_lower_version")


def installed_hashes():
    result = {}
    for name, path in (("app", APP), ("helper", HELPER)):
        root_path(path)
        result[name] = digest(read_limited(path, ABSOLUTE_PACKAGE_LIMIT))
    return result


def expected_hashes(record):
    indexed = {entry["path"]: entry for entry in record["data"]}
    return {"app": indexed[str(APP)[1:]]["sha256"], "helper": indexed[str(HELPER)[1:]]["sha256"]}


def main(argv):
    report = {"status": "refused", "phase": "admission"}
    stage = None
    before = None
    lock_fd = None
    dpkg_lock_fd = None
    try:
        require(os.geteuid() == 0, "root_via_polkit_required")
        require(len(argv) == 2, "expected_package_and_signature_paths")
        # pkexec authenticates the caller; root-only provisioning does not invoke this entry point.
        caller_text = os.environ.get("PKEXEC_UID", "")
        require(caller_text.isdecimal() and int(caller_text) > 0, "polkit_caller_required")
        caller_uid = int(caller_text)
        for path in (Path(__file__), LIB / "verify-signature", TRUST / "public-key.txt", TRUST / "admission.json"):
            root_path(path)
        root_path(STATE, directory=True)
        require(stat.S_IMODE(STATE.stat().st_mode) == 0o700, "state_must_be_private")
        admission = validate_admission(json.loads(read_limited(TRUST / "admission.json", ADMISSION_LIMIT)))
        lock_fd = os.open(STATE / "install.lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
        lock_info = os.fstat(lock_fd)
        require(lock_info.st_uid == 0 and stat.S_ISREG(lock_info.st_mode)
                and not lock_info.st_mode & 0o077, "invalid_installer_lock")
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        # dpkg's frontend lock serializes authenticated version comparison with install.
        # The child is told the frontend already holds it and acquires dpkg's backend lock.
        root_path(Path("/var/lib/dpkg/lock-frontend"))
        dpkg_lock_fd = os.open("/var/lib/dpkg/lock-frontend", os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC)
        fcntl.lockf(dpkg_lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        before = installed_hashes()
        report["before"] = before
        installed = installed_identity(admission)
        report["installed_version"] = installed
        current_record = next(record for record in admission["packages"] if record["version"] == installed)
        require(before == expected_hashes(current_record), "installed_fixture_bytes_differ")
        stage = Path(tempfile.mkdtemp(prefix="stage-", dir=STATE))
        report["phase"] = "root_staging"
        size, package_hash = copy_to_stage(argv[0], stage / "package.deb", admission["max_package_bytes"], caller_uid)
        copy_to_stage(argv[1], stage / "package.sig", SIGNATURE_LIMIT, caller_uid)
        report.update({"package_sha256": package_hash, "package_bytes": size})
        report["phase"] = "signature_and_schema"
        record = verify_staged(stage / "package.deb", stage / "package.sig", admission)
        report["authenticated_version"] = record["version"]
        report["phase"] = "forward_version"
        require_forward_version(record["version"], installed)
        report["phase"] = "dpkg"
        # No shell, password, sudo, other package, dependency fetch or stock updater fallback.
        installed_result = subprocess.run(
            ["/usr/bin/dpkg", "--no-triggers", "--install", str(stage / "package.deb")],
            env={**ENV, "DPKG_FRONTEND_LOCKED": "true"}, cwd="/", stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=120, check=False)
        report["dpkg_exit"] = installed_result.returncode
        require(installed_result.returncode == 0, "dpkg_failed_recovery_evidence_required")
        require(installed_identity(admission) == record["version"], "installed_version_mismatch")
        require(installed_hashes() == expected_hashes(record), "installed_fixture_bytes_mismatch")
        report.update({"status": "accepted", "phase": "complete"})
    except Refused as error:
        report["reason"] = str(error)
    except (OSError, ValueError, KeyError, TypeError, tarfile.TarError, subprocess.SubprocessError) as error:
        # Do not print caller-controlled paths, package text, verifier stderr or environment.
        report["reason"] = type(error).__name__
    finally:
        if stage is not None:
            shutil.rmtree(stage)
        if before is not None:
            try:
                report["after"] = installed_hashes()
                report["app_helper_unchanged"] = report["after"] == before
            except (OSError, Refused):
                report["after"] = "unavailable"
        if lock_fd is not None:
            os.close(lock_fd)
        if dpkg_lock_fd is not None:
            os.close(dpkg_lock_fd)
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "accepted" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
