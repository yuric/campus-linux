#!/usr/bin/env python3
"""Build a disposable verifier from exact pinned Tauri verification functions.
Downloads hash-pinned source into scratch; rustc only, no Cargo index or product deps.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile
import urllib.request

PINS = (
    ('tauri-plugin-updater', '2.14.0', '7259989d4fe11b2bf51f7d671642249b1837c4ae2da1430dc713ae38f98ceeec', None, ()),
    ('minisign-verify', '0.3.0', '871285dc19d8d0ebe0eef3d0e99a205f2a71363b122632cbbfa4a6c370a960ce', '2018', ()),
    ('base64', '0.22.1', '72b3254f16251a8381aa12e40e3c4d2f0199f8c6508fbecb9d91f575e0fbb8c6', '2018', ('std', 'alloc')),
    ('semver', '1.0.28', '8a7852d02fc848982e0c167ef163aaff9cd91dc640ba85e263cb1ce46fae51cd', '2021', ('std',)),
)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    out = args.output.absolute()
    out.mkdir(mode=0o700, parents=True, exist_ok=False)
    paths = {}
    receipts = []
    commands = []
    for name, version, checksum, edition, features in PINS:
        url = f'https://static.crates.io/crates/{name}/{name}-{version}.crate'
        data = urllib.request.urlopen(url, timeout=60).read()
        assert digest(data) == checksum
        (out / (name + '.crate')).write_bytes(data)
        with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as archive:
            for member in archive.getmembers():
                path = Path(member.name)
                assert not path.is_absolute() and '..' not in path.parts
                assert member.isdir() or member.isfile()
            archive.extractall(out, filter='data')
        paths[name] = out / (name + '-' + version)
        receipts.append({'crate': name, 'version': version, 'url': url, 'sha256': checksum})
        if edition:
            command = ['rustc', '--crate-name', name.replace('-', '_'), '--crate-type=rlib', '--edition=' + edition, str(paths[name] / 'src/lib.rs'), '-o', str(out / ('lib' + name.replace('-', '_') + '.rlib'))]
            for feature in features:
                command.extend(['--cfg', 'feature="' + feature + '"'])
            commands.append(command)
            result = subprocess.run(command, capture_output=True, text=True)
            (out / (name + '-build.log')).write_text(result.stdout + result.stderr)
            result.check_returncode()
    source = (paths['tauri-plugin-updater'] / 'src/updater.rs').read_text()
    functions = source[source.index('fn verify_signature('):source.index('\n#[cfg(windows)]', source.index('fn verify_signature('))]
    header = '''use base64::Engine;
use minisign_verify::{PublicKey, Signature};
use semver::Version;
use std::str::FromStr;
type Result<T> = std::result::Result<T, Error>;
#[derive(Debug)] enum Error { Decode, Signature, SignatureUtf8(String), MissingSignedVersion, SignedVersionMismatch { signed: String, announced: String } }
impl From<base64::DecodeError> for Error { fn from(_: base64::DecodeError) -> Self { Self::Decode } }
impl From<minisign_verify::Error> for Error { fn from(_: minisign_verify::Error) -> Self { Self::Signature } }
'''
    footer = '''
fn main() {
 let args: Vec<String> = std::env::args().collect();
 if args.len() != 5 { std::process::exit(2); }
 let data = std::fs::read(&args[1]).unwrap();
 let signature = std::fs::read_to_string(&args[2]).unwrap();
 let key = std::fs::read_to_string(&args[3]).unwrap();
 // Always require an authenticated signed version; no old-signature fallback.
 match verify_signature(&data, signature.trim(), key.trim(), &args[4], true) {
  Ok(()) => println!("verified exact bytes and authenticated version with upstream Tauri functions"),
  Err(_) => { eprintln!("signature or authenticated version rejected"); std::process::exit(1); }
 }
}
'''
    source_path = out / 'verify.rs'
    source_path.write_text(header + functions + footer)
    executable = out / 'tauri-signature-verify'
    command = ['rustc', '--edition=2021', str(source_path), '-o', str(executable)]
    for name in ('minisign_verify', 'base64', 'semver'):
        command.extend(['--extern', name + '=' + str(out / ('lib' + name + '.rlib'))])
    commands.append(command)
    result = subprocess.run(command, capture_output=True, text=True)
    (out / 'verifier-build.log').write_text(result.stdout + result.stderr)
    result.check_returncode()
    report = {'scope': 'exact source-extracted updater2.14.0 verification functions; not full installed updater', 'crates': receipts, 'source_functions_sha256': digest(functions.encode()), 'wrapper_sha256': digest(source_path.read_bytes()), 'binary_sha256': digest(executable.read_bytes()), 'rustc': subprocess.check_output(['rustc', '--version'], text=True).strip(), 'commands': commands, 'require_signed_version': True}
    (out / 'verifier-build.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
