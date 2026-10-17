#!/usr/bin/env python3
"""Disposable source audit, never imports/builds a product or installs an update."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import urllib.request

CRATE_URL = 'https://static.crates.io/crates/tauri-plugin-updater/tauri-plugin-updater-2.14.0.crate'
CRATE_SHA256 = '7259989d4fe11b2bf51f7d671642249b1837c4ae2da1430dc713ae38f98ceeec'
SOURCE_SHA256 = '79ed11ecdb3d22410f71d7adb9f7bcbcab00f888cd8892e2268639085df044ce'


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--crate', type=Path)
    args = p.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    data = args.crate.read_bytes() if args.crate else urllib.request.urlopen(CRATE_URL, timeout=60).read()
    assert hashlib.sha256(data).hexdigest() == CRATE_SHA256
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as tar:
        source = tar.extractfile('tauri-plugin-updater-2.14.0/src/updater.rs').read()
        vcs = json.load(tar.extractfile('tauri-plugin-updater-2.14.0/.cargo_vcs_info.json'))
    assert hashlib.sha256(source).hexdigest() == SOURCE_SHA256
    text = source.decode()
    method = text[text.index("    fn get_urls<'a>("):text.index('\n}\n', text.index("    fn get_urls<'a>("))]
    harness = r'''
extern crate self as log;
#[macro_export] macro_rules! debug { ($($arg:tt)*) => {}; }
use std::collections::HashMap;
type Url = String;
type Result<T> = std::result::Result<T, Error>;
#[derive(Debug)] enum Error { UnsupportedOs, TargetsNotFound(Vec<String>), Missing }
struct RemoteRelease { entries: HashMap<String, (Url, String)> }
impl RemoteRelease {
 fn download_url(&self, t: &str) -> Result<&Url> { self.entries.get(t).map(|x| &x.0).ok_or(Error::Missing) }
 fn signature(&self, t: &str) -> Result<&String> { self.entries.get(t).map(|x| &x.1).ok_or(Error::Missing) }
}
struct Installer(&'static str);
impl Installer { fn name(&self) -> &'static str { self.0 } }
fn updater_os() -> Option<&'static str> { Some("linux") }
struct Updater { target: Option<String>, arch: &'static str }
impl Updater {
''' + method + r'''
}
fn main() {
 let mut release = RemoteRelease { entries: HashMap::new() };
 for arch in ["aarch64", "x86_64"] {
  for format in ["deb", "appimage"] {
   let key = format!("linux-{arch}-{format}");
   release.entries.insert(key.clone(), (format!("https://example.invalid/{key}"), format!("signature-{key}")));
  }
 }
 for arch in ["aarch64", "x86_64"] {
  for format in ["deb", "appimage"] {
   let key = format!("linux-{arch}-{format}");
   let u = Updater { target: None, arch };
   let (url, sig) = u.get_urls(&release, &Some(Installer(format))).unwrap();
   assert_eq!(url, &format!("https://example.invalid/{key}"));
   assert_eq!(sig, &format!("signature-{key}"));
   println!("PASS source-extracted bundle selection {key}");
  }
 }
 release.entries.remove("linux-aarch64-deb");
 release.entries.insert("linux-aarch64".into(), ("https://example.invalid/wrong.AppImage".into(), "wrong-signature".into()));
 let automatic = Updater { target: None, arch: "aarch64" };
 assert_eq!(automatic.get_urls(&release, &Some(Installer("deb"))).unwrap().0, "https://example.invalid/wrong.AppImage");
 println!("OBSERVED automatic generic fallback permits cross-format URL");
 let strict = Updater { target: Some("linux-aarch64-deb".into()), arch: "aarch64" };
 assert!(strict.get_urls(&release, &Some(Installer("deb"))).is_err());
 println!("PASS explicit bundle target rejects generic fallback");
}
'''
    (args.output / 'selection.rs').write_text(harness)
    elevation = text[text.index('    fn try_install_with_privileges('):text.index('\n}\n', text.index('    fn try_install_with_privileges('))]
    report = {
        'source_url': CRATE_URL, 'crate_sha256': CRATE_SHA256,
        'source_sha256': SOURCE_SHA256, 'vcs': vcs,
        'selection_scope': 'exact extracted get_urls method, fake RemoteRelease and installer/arch inputs; NOT installed artifact selection',
        'elevation_has_pkexec': 'Command::new("pkexec")' in elevation,
        'elevation_has_gui_password': '.get_password_graphically()' in elevation,
        'elevation_has_sudo_stdin_password': '.arg("-S")' in elevation,
        'g5_stock_deb_result': 'FAIL: password fallback and no privileged independent signature verification',
        'selection_execution': 'BLOCKED: rustc unavailable',
    }
    if shutil.which('rustc'):
        with tempfile.TemporaryDirectory(prefix='campus-982-selection-') as tmp:
            exe = str(Path(tmp) / 'selection')
            compile_result = subprocess.run(['rustc', '--edition=2021', str(args.output / 'selection.rs'), '-o', exe], capture_output=True, text=True)
            (args.output / 'compile.log').write_text(compile_result.stdout + compile_result.stderr)
            compile_result.check_returncode()
            run = subprocess.run([exe], capture_output=True, text=True, check=True)
            (args.output / 'selection.log').write_text(run.stdout + run.stderr)
            report['selection_execution'] = 'PASS: six source-extracted cases; not product end-to-end'
            report['rustc'] = subprocess.check_output(['rustc', '--version'], text=True).strip()
    (args.output / 'audit.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
