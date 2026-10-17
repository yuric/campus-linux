#!/usr/bin/env python3
"""Root fixture setup only. Invoke explicitly in the owned disposable guest.
This creates a throwaway trust anchor, a test-only polkit action and no product keys.
Use --cleanup to remove exactly the fixture paths and disposable package.
"""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path('/var/lib/campus-982-tauri-spike')
HELPER = Path('/usr/local/libexec/campus-982-tauri-spike-install')
POLICY = Path('/usr/share/polkit-1/actions/dev.projectcampus.spike982.tauriinstall.policy')
RULE = Path('/etc/polkit-1/rules.d/00-campus-982-tauri-spike.rules')
MARKER = Path('/etc/campus-982-tauri-disposable-guest')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--user', required=True)
    p.add_argument('--fixture', type=Path, required=True)
    p.add_argument('--verifier', type=Path)
    p.add_argument('--mode', choices=('allow', 'deny', 'prompt'), default='prompt')
    p.add_argument('--cleanup', action='store_true')
    args = p.parse_args()
    assert os.getuid() == 0 and sys.platform == 'linux'
    # Named owned guest, not a generic owner workstation.
    assert Path('/etc/hostname').read_text().strip() == 'lima-campus-linux-d5-noble-arm64'
    assert args.user in ('campusqa', 'yuri')
    if args.cleanup:
        # Keep the verifier/action/trust anchor intact if dpkg cannot remove it.
        subprocess.run(['/usr/bin/dpkg', '--remove', 'campus-982-disposable-spike'], check=True)
        status = subprocess.run(['/usr/bin/dpkg-query', '-W', '-f=${db:Status-Status}',
                                 'campus-982-disposable-spike'], capture_output=True, text=True)
        if not (status.returncode == 1 or (status.returncode == 0 and status.stdout.strip() in ('not-installed', 'config-files'))):
            raise RuntimeError('Disposable package removal not verified; fixture preserved')
        if Path('/usr/lib/campus-982-disposable-spike/helper').exists():
            raise RuntimeError('Disposable helper still present; fixture preserved')
        RULE.unlink(missing_ok=True)
        POLICY.unlink(missing_ok=True)
        HELPER.unlink(missing_ok=True)
        Path('/usr/local/libexec/campus-982-tauri-signature-verify').unlink(missing_ok=True)
        if ROOT.exists():
            shutil.rmtree(ROOT)
        MARKER.unlink(missing_ok=True)
        print('removed test-only root fixture; user repositories/provider files untouched')
        return
    assert not ROOT.is_symlink() and not args.fixture.is_symlink()
    ROOT.mkdir(mode=0o700, exist_ok=True)
    ROOT.chmod(0o700)
    MARKER.write_text('Disposable mechanism probe for #982; no release authority.\n')
    MARKER.chmod(0o600)
    shutil.copyfile(args.fixture / 'tauri-minisign/public-key.b64', ROOT / 'public-key.b64')
    (ROOT / 'public-key.b64').chmod(0o400)
    HELPER.parent.mkdir(exist_ok=True)
    shutil.copyfile(Path(__file__).with_name('privileged-tauri-install.py'), HELPER)
    HELPER.chmod(0o755)
    assert args.verifier and args.verifier.is_file()
    verifier = Path('/usr/local/libexec/campus-982-tauri-signature-verify')
    shutil.copyfile(args.verifier, verifier)
    verifier.chmod(0o755)
    POLICY.write_text('''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE policyconfig PUBLIC "-//freedesktop//DTD PolicyKit Policy Configuration 1.0//EN" "http://www.freedesktop.org/standards/PolicyKit/1/policyconfig.dtd">
<policyconfig><vendor>Campus disposable #982 fixture</vendor>
<action id="dev.projectcampus.spike982.tauriinstall">
<description>Install disposable Campus mechanism fixture</description>
<message>Authenticate to install the disposable Campus #982 test package</message>
<defaults><allow_any>no</allow_any><allow_inactive>no</allow_inactive><allow_active>auth_admin</allow_active></defaults>
<annotate key="org.freedesktop.policykit.exec.path">/usr/local/libexec/campus-982-tauri-spike-install</annotate>
</action></policyconfig>\n''')
    POLICY.chmod(0o644)
    if args.mode == 'prompt':
        RULE.unlink(missing_ok=True)
    else:
        answer = 'YES' if args.mode == 'allow' else 'NO'
        RULE.write_text('polkit.addRule(function(action, subject) {\n'
                        '  if (action.id == "dev.projectcampus.spike982.tauriinstall" && subject.user == "' + args.user + '")\n'
                        '    return polkit.Result.' + answer + ';\n});\n')
        RULE.chmod(0o644)
    print('test fixture prepared; polkit mode=' + args.mode + '; synthetic minisign key, exact Tauri verification functions; NOT owner release key')


if __name__ == '__main__':
    main()
