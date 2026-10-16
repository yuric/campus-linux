#!/usr/bin/env python3
"""UNEXECUTED fresh-inode proposal for 10834/1318. Requires review and a NEW explicit guest lease.

Fixed disposable guest/paths only. No download, launch or policy edit.
Extract only the existing pinned archive into NEW root-owned exclusive inodes.
Never trust ownership changes or process scans to revoke old writable descriptors.
"""
import argparse
import datetime
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import socket
import stat
import sys
import zipfile

ARCHIVE_SHA = '502296281cab3c333bd5193e2eaed11c3bb28eabd7a451a49776a3e5a9468f8c'
EXECUTABLE_SHA = '730d44d5aefb6a969b209cf8ee3e843bd873a06c297bf2c409fbb1cebcb3e6bc'
HELPER_SHA = '243acfa0e6bab02b34580c2f426704dcd256c4072f494192c02b2256ea7740bb'
EXPECTED_FILES = {
    "LICENSE": "5154e165bd6c2cc0cfbcd8916498c7abab0497923bafcd5cb07673fe8480087d",
    "LICENSES.chromium.html": "3375e2a9bd7bc631738fde10be6548a76efe8cf5e4b8826b8140ba8b0c4d6353",
    "chrome-sandbox": "243acfa0e6bab02b34580c2f426704dcd256c4072f494192c02b2256ea7740bb",
    "chrome_100_percent.pak": "891176da5eee33b54352fdb1407a8e09a2bd48c7eb2077311e75787de33a095e",
    "chrome_200_percent.pak": "b3ce9953a50959e9c1a018d6512742f48cee0dbf53644ea952909418bd7c2b3e",
    "chrome_crashpad_handler": "b3d0f15fe548488da4f81aec53224f7ab5f28a9a56100263b86a388d22f341db",
    "electron": "730d44d5aefb6a969b209cf8ee3e843bd873a06c297bf2c409fbb1cebcb3e6bc",
    "icudtl.dat": "da53f0b69843aaa43315f0f210a67e4a874b0be338f3dae08ff57b8afe76ab0d",
    "libffmpeg.so": "d3ef797176f8654d3c676a793a51258d93574aad69afd6d7571399fb3eab42cb",
    "libvk_swiftshader.so": "761de2cd1ab7baa982caaceaa3d53501d729f2047bea0a71ce8cd1193025f4a5",
    "libvulkan.so.1": "9b413cc04f1ffec074c21cd81532338adc85a02963c98cf986903916d8e7d916",
    "locales/af.pak": "9abd48c6c1f34e14dcad66131a9cc8624b4e850ebf692b05a66fb18d5c537588",
    "locales/am.pak": "28545e9a72220ddca39f7d7b36eacb3b661a3cc40d212b7e56be21d90f5ee71b",
    "locales/ar.pak": "267687bf1ed07628b03f02d095b253141a4cbc6b80f0bfec6007ca0556260e5f",
    "locales/bg.pak": "96741df7a895b1d4894db0fd5e5db4f761849eb0e5ebadf6f3f27daf16723ebe",
    "locales/bn.pak": "eaa31ac7166ef4c5c61bf6e4a9b0a0b4cb1825e1b57e5a45f76faa65dc0d113f",
    "locales/ca.pak": "3f86be184e95323c14604836b8eaf8935fc24f9cd2308cb207be26c318d8f287",
    "locales/cs.pak": "cffb35f66f25ef7dac62b05213dfa787ecddf2533518c02276d8fbe828f541e8",
    "locales/da.pak": "14cfcdfecb80d8575d273d8ec03317ae51c3e2c976c862ab774f9af9c7c4557b",
    "locales/de.pak": "7d4874ca52ac298dbc4c01d91c1c6a549008dbefc2d0c8f52154d872dce4979f",
    "locales/el.pak": "114158bd5f674169564173a12612922259a8acc50076c228c2214659924ee018",
    "locales/en-GB.pak": "550775b16b4716e610232e6b06e35a95c4c6ce2dedbd2a26747f8dc8f08d8aeb",
    "locales/en-US.pak": "e37db76f0a15a4b2a3cbd365bd4f06b0d8dc91fb9a83c03b7cd38503c23c044b",
    "locales/es-419.pak": "aaacff94a6407a7d487a455889a544f6107107cccb82393a27e9bf593d1b943d",
    "locales/es.pak": "b3256546e28dffff82c3d00abae9ad2141cf7bb940e5e39620f6ae30b488dcea",
    "locales/et.pak": "41f78768a3ef702356653ab005522a20407e0dbbe7b0ea323683072520f11191",
    "locales/fa.pak": "365520460dd4b662f8dfa14969eb066b7c1c98ae255ecfd705c1692a1ed784f1",
    "locales/fi.pak": "fb7379246632c90a58a8f7155e390ca583f9d73b6c6ae26baf9bf4878be184df",
    "locales/fil.pak": "7c6c76af71a7d60733a01014c19d9544409d5facd6001fb9058fc8ae8062cf54",
    "locales/fr.pak": "95b11fc7368d9f4367534e89456cceda009468abe2423821a11fe1dd1a7b4604",
    "locales/gu.pak": "309dcf4484d9479eeb68dcc7d745f17dfa0ffc4e6b112751de704ce62e8aecbe",
    "locales/he.pak": "5764ba9a2261b2ded07f3c3afa8f003594b29f58c73b322f1d89479907a97ca2",
    "locales/hi.pak": "b4d36beed004905461637b0c60eacc6d8eca49ba47ba262ed04d68c88b826bf4",
    "locales/hr.pak": "6937159b11ac75bee2c8046a5150596acee10a7c10c75a2469a752175f9e9e99",
    "locales/hu.pak": "d6add186bc8bd342ef5d35cba5261c8c847ecb529697b7c003016435997c9fdc",
    "locales/id.pak": "06c550187e7dd49cf0210ac9bcf4401c10e96ed777ccc8fd07e914a9337de9b7",
    "locales/it.pak": "b02a5de9de434266991a9e37a6bcced44b65ae3c164e4920a736eb350f745ecb",
    "locales/ja.pak": "4b51a3023136f05ae2c0b8e041e262eed3f6d5fa87c782892cba36e10d904b3c",
    "locales/kn.pak": "875859c2b88312ff3644c6cadd65dd8b5057e336a0a2bea512fbffa7c85695a7",
    "locales/ko.pak": "8c98d075840cb4800016c6df141183b3ec69cfe20df38ea759f2274259a86666",
    "locales/lt.pak": "b7e01915d9f1131743aaa7b1c262c7ef685c10d8621f2437e46ebefe980a6efc",
    "locales/lv.pak": "22fc0a3e04e7772c7df2f4c74e928ceb4046edc8c1688dbc4f04676f00944952",
    "locales/ml.pak": "fffb1b403dd4a62f0116fb39a961a73dd0766049bdc23118c90f4360971e225b",
    "locales/mr.pak": "0f5879b812517af23c9655347b08852c8e8f5c399b288466a8ec717d397e94d6",
    "locales/ms.pak": "ce1f9c8cfe5b2705b281d3480e0df992ab36f3518956100564eb9edae5d03dbb",
    "locales/nb.pak": "36c2e3f5d4e920e8e0411878df2cbd4a92bd9e553e9e427b3aae355bfb9fc955",
    "locales/nl.pak": "5cceeeff48b3aad830116126f8f15b3bfddf682bbdf986b3a266e0e72ff463d1",
    "locales/pl.pak": "35e0d1578baa9c9441c83383aade35d69c03bc2307783c639c01b156015a11a8",
    "locales/pt-BR.pak": "907226d904de6a571a80289ef6a8072bad867b1f63ec37fcd735c30763af970d",
    "locales/pt-PT.pak": "540b4f6c0d58d8f0315a8e4fbee49e41b6fbfe2b9c2065b8f28b069619c132ba",
    "locales/ro.pak": "b7c3b4af988ec26f8f3a3fa789cdbe46712a14497e47cba6266c9f0e808e57f7",
    "locales/ru.pak": "b011f8c753fa33f9aa91732590ca13a791824a7fd94a8f35c41330fe346de11a",
    "locales/sk.pak": "8c743c91af3dd53fd5c36e88061a62dddb2b91687ec779e7958774f436486dac",
    "locales/sl.pak": "a692040613f2fe76800c33d000a9a62277b1fc98bd056ce7f4f5ee06f6b0ec9d",
    "locales/sr.pak": "92bac4af059cea0f2f72293fde0cc665b8554c00653b26611cfcc6e98b4971e8",
    "locales/sv.pak": "54cf311648f8688effc4cfd70a580b85b837e67dd9e5f194d9f761202a27ebba",
    "locales/sw.pak": "3475068a7e3b8205444f914d7d29421fb45b87c008594984f3e7b04cff22b2d3",
    "locales/ta.pak": "e4053fb503c08d94b7364b10a74abc04506d15f67ad74b9ea66185999ea177df",
    "locales/te.pak": "4955104544daf89da718e7f584ad66fe35dd4ca219c245697de2929acb317ec8",
    "locales/th.pak": "2272de996ac5c553cf01f406e6f708cb98ad419708355fb4969cb91ec8031e56",
    "locales/tr.pak": "f690918f136d8c5bad9853c358670e60475999d0faafb36d36001c4fa7ec4f8b",
    "locales/uk.pak": "26ddf342bb13d674df20162ff1a955edc56e6ffc64bc846953e7b2be8827fe80",
    "locales/ur.pak": "203e225739beb9879eebb08d08d9aa17b80f02320049f03d453156ff53170da8",
    "locales/vi.pak": "4dcf8fe139c4355a8999137098532662e5af79d7b464c6e2faab686605d7ad8d",
    "locales/zh-CN.pak": "aec678d57f7644157d8d7d1007cd03c9efbc7ef54488df2f856989179a563e42",
    "locales/zh-TW.pak": "deba23736da06f4e2633cbecab98e7b9c3ae8b6b7245c08b89f63581fa47f1f4",
    "resources.pak": "7fee8f5de6db250469244546544dfc3b7585f6bbaa0a1f9608ac8b4a884db9cd",
    "resources/default_app.asar": "0eb2491b0a9ac94790389d39c09dd5005c6c1f0665842943829bbd0193f6cc4f",
    "snapshot_blob.bin": "44a6f7eed34b2e1fb635d009f5d6a9c6202d4e5bf9abd1d5b62e3fb41792ec60",
    "v8_context_snapshot.bin": "f5275a8e152e444d28bffd3b46d05372827c788ea806590125a525af1b315e60",
    "version": "afc7dca2c2eeb1e1395b1ad6612cde12d991d28bd7cbf4e5fdfd65934447324a",
    "vk_swiftshader_icd.json": "c9eef28b6b984fec220ef0abfecc40b502d46946706e47bfe97707027cb818bd"
}
ARCHIVE_BYTES = 124393671
PAYLOAD_BYTES = 302048805
EXPECTED_FILE_COUNT = 72
SOURCE = Path('/home/campusqa/spike982/g8-electron-1288')
ARCHIVE_NAME = 'electron-v44.8.0-linux-arm64.zip'
PARENT = Path('/opt/campus-linux-spike982')
NAME = 'electron-44.8.0-' + EXECUTABLE_SHA
TARGET = PARENT / NAME
LEDGER = PARENT / ('.' + NAME + '-fresh-1318.json')


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def regular(path, maximum):
    """Read one bounded, non-linked regular inode through a no-follow descriptor."""
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1,
                'Not a unique regular file: ' + str(path))
        require(before.st_size <= maximum, 'Oversized file: ' + str(path))
        data = stream.read(maximum + 1)
        after = os.fstat(stream.fileno())
        stable = ('st_dev', 'st_ino', 'st_mode', 'st_uid', 'st_gid', 'st_nlink',
                  'st_size', 'st_mtime_ns', 'st_ctime_ns')
        require(len(data) == before.st_size
                and all(getattr(before, k) == getattr(after, k) for k in stable),
                'File changed while reading: ' + str(path))
    return data, before


def directory_chain(path, root_owned=False):
    for p in [*reversed(path.parents), path]:
        s = p.lstat()
        require(stat.S_ISDIR(s.st_mode), 'Non-directory/symlink ancestor: ' + str(p))
        if root_owned:
            require(s.st_uid == s.st_gid == 0 and not s.st_mode & 0o022,
                    'Writable or non-root ancestor: ' + str(p))


def archive_manifest(data):
    """Authenticated in-memory archive, not a caller-supplied checksum manifest."""
    require(len(data) == ARCHIVE_BYTES and sha(data) == ARCHIVE_SHA, 'Archive pin mismatch')
    files, directories, names = {}, set(), set()
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        entries = archive.infolist()
        require(sum(x.file_size for x in entries) == PAYLOAD_BYTES, 'Payload size mismatch')
        for item in entries:
            name = item.filename.rstrip('/')
            p = PurePosixPath(name)
            require(name and not p.is_absolute() and '..' not in p.parts
                    and str(p) == name and name not in names, 'Unsafe/duplicate archive name')
            names.add(name)
            mode = item.external_attr >> 16
            require(not mode & 0o7000 and not item.flag_bits & 1, 'Privileged/encrypted archive')
            require('\\' not in name and '\x00' not in item.orig_filename, 'Unsafe archive name')
            if item.is_dir():
                require(stat.S_IFMT(mode) in (0, stat.S_IFDIR)
                        and (mode & 0o777) == 0o755 and item.file_size == 0,
                        'Unexpected archive directory type/mode/size')
                directories.add(name)
            else:
                require(stat.S_IFMT(mode) in (0, stat.S_IFREG), 'Unexpected archive type')
                require((mode & 0o777) in (0o644, 0o755), 'Unexpected file mode')
                h = hashlib.sha256()
                total = 0
                with archive.open(item) as stream:
                    for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                        total += len(chunk)
                        require(total <= item.file_size, 'Expanded file exceeds bound')
                        h.update(chunk)
                require(total == item.file_size, 'Expanded size mismatch')
                files[name] = dict(bytes=item.file_size, sha256=h.hexdigest(), mode=(mode & 0o777) or 0o644)
            directories.update(str(parent) for parent in p.parents if str(parent) != '.')
    require(not directories.intersection(files), 'File/directory archive collision')
    require(files['electron']['sha256'] == EXECUTABLE_SHA, 'Executable pin mismatch')
    require(files['chrome-sandbox']['sha256'] == HELPER_SHA
            and files['chrome-sandbox']['bytes'] == 17048, 'Sandbox helper pin mismatch')
    require({'LICENSE', 'LICENSES.chromium.html'} <= files.keys(), 'Missing licenses')
    require(len(files) == len(EXPECTED_FILES) == EXPECTED_FILE_COUNT, 'Expected exactly 72 vendor files')
    require({name: row['sha256'] for name, row in files.items()} == EXPECTED_FILES,
            'Full pinned vendor manifest mismatch')
    return files, directories


def verify_tree(root, manifest, privileged=False):
    files, directories = manifest
    directory_chain(root, root_owned=True)
    seen_files, seen_dirs, identities = set(), set(), set()
    for base, dirs, names in os.walk(root, followlinks=False):
        for name in dirs + names:
            p = Path(base) / name
            rel = str(p.relative_to(root))
            s = p.lstat()
            identities.add((s.st_dev, s.st_ino))
            require(s.st_dev == root.stat().st_dev, 'Unexpected mount boundary')
            require(s.st_uid == 0, 'Unexpected owner')
            require(s.st_gid == 0, 'Unexpected group')
            if stat.S_ISDIR(s.st_mode):
                require(rel in directories, 'Unexpected directory: ' + rel)
                require(stat.S_IMODE(s.st_mode) == 0o755,
                        'Unexpected directory mode')
                seen_dirs.add(rel)
                continue
            require(stat.S_ISREG(s.st_mode) and s.st_nlink == 1 and rel in files,
                    'Unexpected type/link/file: ' + rel)
            expected = files[rel]
            data, observed = regular(p, expected['bytes'])
            require(sha(data) == expected['sha256'], 'Content mismatch: ' + rel)
            mode = expected['mode']
            if privileged and rel == 'chrome-sandbox':
                mode = 0o4755
            require(stat.S_IMODE(observed.st_mode) == mode, 'Mode mismatch: ' + rel)
            require(len(data) == expected['bytes'], 'Size mismatch: ' + rel)
            seen_files.add(rel)
    require(seen_files == files.keys() and seen_dirs == directories, 'Incomplete tree membership')
    identities.add((root.stat().st_dev, root.stat().st_ino))
    return identities


def quiescent(identities):
    """Fail closed on an active fixture UID or an outstanding inode FD/mapping.

    No signals or service edits. A separate normal logout and sole guest lease are
    prerequisites: chown alone does not revoke an already-open writable descriptor.
    """
    for p in Path('/proc').iterdir():
        if not p.name.isdigit() or int(p.name) == os.getpid():
            continue
        try:
            status = (p / 'status').read_text()
            uids = next(line.split()[1:] for line in status.splitlines() if line.startswith('Uid:'))
            require('1000' not in uids, 'Fixture user still has process ' + p.name)
            for fd in (p / 'fd').iterdir():
                try:
                    s = fd.stat()
                except FileNotFoundError:
                    continue
                require((s.st_dev, s.st_ino) not in identities, 'Runtime descriptor held by ' + p.name)
            for line in (p / 'maps').read_text().splitlines():
                fields = line.split()
                major, minor = (int(x, 16) for x in fields[3].split(':'))
                require((os.makedev(major, minor), int(fields[4])) not in identities,
                        'Runtime mapping held by ' + p.name)
        except FileNotFoundError:
            # Disappearing process/descriptor is normal; all other read errors refuse.
            continue


def write_ledger(record, exclusive=False):
    flags = os.O_WRONLY | os.O_NOFOLLOW | (os.O_CREAT | os.O_EXCL if exclusive else os.O_TRUNC)
    fd = os.open(LEDGER, flags, 0o600)
    with os.fdopen(fd, 'w') as stream:
        s = os.fstat(stream.fileno())
        require(s.st_uid == s.st_gid == 0 and s.st_nlink == 1 and stat.S_IMODE(s.st_mode) == 0o600,
                'Unsafe ledger')
        json.dump(record, stream, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def extract_fresh(data, manifest):
    """Only write new inodes beneath an inaccessible root-owned target."""
    files, directories = manifest
    runtime = TARGET / 'runtime'
    runtime.mkdir(mode=0o700)  # exclusive; no existing tree is adopted
    for name in sorted(directories, key=lambda name: (name.count('/'), name)):
        (runtime / name).mkdir(mode=0o700)
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for name, expected in files.items():
            path = runtime / name
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            with os.fdopen(fd, 'wb') as output, archive.open(name) as source:
                observed = os.fstat(output.fileno())
                require(observed.st_uid == observed.st_gid == 0 and observed.st_nlink == 1
                        and stat.S_ISREG(observed.st_mode), 'New inode ownership/type')
                total, digest = 0, hashlib.sha256()
                while True:
                    chunk = source.read(min(1024 * 1024, expected['bytes'] - total + 1))
                    if not chunk:
                        break
                    total += len(chunk)
                    require(total <= expected['bytes'], 'Extraction exceeds pinned size')
                    output.write(chunk)
                    digest.update(chunk)
                require(total == expected['bytes'] and digest.hexdigest() == expected['sha256'],
                        'Fresh extraction content mismatch')
                output.flush()
                os.fsync(output.fileno())
                os.fchmod(output.fileno(), expected['mode'])
    for name in sorted(directories, key=lambda name: -name.count('/')):
        (runtime / name).chmod(0o755)
    runtime.chmod(0o755)


def install():
    directory_chain(SOURCE)
    directory_chain(Path('/opt'), root_owned=True)
    require(not os.path.lexists(TARGET) and not os.path.lexists(LEDGER),
            'Never overwrite a prior installation/receipt')
    # Read the existing archive ONCE; the same immutable buffer is authenticated,
    # inspected and extracted. The user-writable old extraction is never consumed.
    archive, _ = regular(SOURCE / ARCHIVE_NAME, ARCHIVE_BYTES)
    manifest = archive_manifest(archive)
    if not os.path.lexists(PARENT):
        PARENT.mkdir(mode=0o755)
        PARENT.chmod(0o755)
    directory_chain(PARENT, root_owned=True)
    TARGET.mkdir(mode=0o700)
    t = TARGET.stat()
    record = dict(version=2, target=str(TARGET), device=t.st_dev, inode=t.st_ino,
                  archive_sha256=ARCHIVE_SHA, helper_sha256=HELPER_SHA,
                  source_sha256=sha(Path(__file__).read_bytes()), state='reserved',
                  manifest=manifest[0], directories=sorted(manifest[1]),
                  utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    write_ledger(record, exclusive=True)
    helper = TARGET / 'runtime/chrome-sandbox'
    helper_fd = None
    try:
        extract_fresh(archive, manifest)
        verify_tree(TARGET / 'runtime', manifest)
        helper_fd = os.open(helper, os.O_RDONLY | os.O_NOFOLLOW)
        hs = os.fstat(helper_fd)
        require(hs.st_uid == hs.st_gid == 0 and hs.st_nlink == 1
                and hs.st_size == 17048 and stat.S_ISREG(hs.st_mode)
                and sha(os.read(helper_fd, 17049)) == HELPER_SHA, 'Exact fresh helper required')
        record.update(state='verified-fresh-root-owned', helper_inode=hs.st_ino,
                      helper_device=hs.st_dev)
        write_ledger(record)
        # Only this retained, freshly-created, verified root-owned inode gains SUID.
        os.fchmod(helper_fd, 0o4755)
        verify_tree(TARGET / 'runtime', manifest, privileged=True)
        TARGET.chmod(0o755)
        record['state'] = 'installed-not-launched'
        write_ledger(record)
        print(json.dumps(record, indent=2))
    except BaseException:
        # Never mask privilege-clear failure as a completed rollback. The exact fd
        # remains held through the attempt; incomplete trees need reviewed recovery.
        if helper_fd is not None:
            os.fchmod(helper_fd, 0o755)
        record['state'] = 'failed; retained for reviewed recovery'
        write_ledger(record)
        raise
    finally:
        if helper_fd is not None:
            os.close(helper_fd)


def rollback():
    directory_chain(PARENT, root_owned=True)
    raw, ls = regular(LEDGER, 65536)
    require(ls.st_uid == ls.st_gid == 0 and stat.S_IMODE(ls.st_mode) == 0o600, 'Unsafe ledger')
    record = json.loads(raw)
    require(record['version'] == 2 and record['target'] == str(TARGET) and record['archive_sha256'] == ARCHIVE_SHA,
            'Wrong ownership receipt')
    s = TARGET.lstat()
    require(stat.S_ISDIR(s.st_mode) and s.st_uid == s.st_gid == 0
            and (s.st_dev, s.st_ino) == (record['device'], record['inode']), 'Target replaced')
    directory_chain(TARGET, root_owned=True)
    helper = TARGET / 'runtime/chrome-sandbox'
    data, hs = regular(helper, 17048)
    require(sha(data) == HELPER_SHA and (hs.st_dev, hs.st_ino) == (record.get('helper_device'), record.get('helper_inode')),
            'Helper identity unconfirmed; manual reviewed recovery required')
    # Revoke privileged bit BEFORE validation/removal. Failure retains this root tree.
    fd = os.open(helper, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        observed = os.fstat(fd)
        require((observed.st_dev, observed.st_ino) == (hs.st_dev, hs.st_ino),
                'Helper changed before privilege clearing')
        os.fchmod(fd, 0o755)
    finally:
        os.close(fd)
    record['state'] = 'rollback-privilege-cleared'
    write_ledger(record)
    manifest = (record['manifest'], set(record['directories']))
    require(len(manifest[0]) == EXPECTED_FILE_COUNT
            and {name: row['sha256'] for name, row in manifest[0].items()} == EXPECTED_FILES
            and sum(row['bytes'] for row in manifest[0].values()) == PAYLOAD_BYTES,
            'Wrong pinned manifest in root ledger')
    identities = verify_tree(TARGET / 'runtime', manifest)
    quiescent(identities)
    require({p.name for p in TARGET.iterdir()} == {'runtime'}, 'Unexpected target entries')
    require(shutil.rmtree.avoids_symlink_attacks, 'Descriptor-safe removal unavailable')
    shutil.rmtree(TARGET)
    record['state'] = 'removed; external ownership receipt retained'
    write_ledger(record)
    print(json.dumps(record, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['install', 'rollback'])
    parser.add_argument('--approved-source-sha256', required=True)
    parser.add_argument('--execute-under-new-lease', action='store_true', required=True)
    args = parser.parse_args()
    require(socket.gethostname() == 'lima-campus-linux-d5-noble-arm64' and os.geteuid() == 0,
            'Only root in the explicitly leased disposable Lima guest')
    require(sha(Path(__file__).read_bytes()) == args.approved_source_sha256, 'Unreviewed source bytes')
    os.umask(0o077)
    # Set only explicit per-file modes; no authentication, kernel or service operations.
    (install if args.action == 'install' else rollback)()


if __name__ == '__main__':
    main()
