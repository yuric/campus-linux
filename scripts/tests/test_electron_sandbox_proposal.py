"""Host input and mocked installer checks. Never operate privileged paths or a guest."""
import hashlib
import importlib.util
import io
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from contextlib import ExitStack
from types import SimpleNamespace
import zipfile

SOURCE = Path(__file__).resolve().parents[2] / 'spikes/982/environment/electron-sandbox-operator.py'
spec = importlib.util.spec_from_file_location('sandbox_proposal', SOURCE)
operator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(operator)


class SandboxProposalInputs(unittest.TestCase):
    def test_regular_rejects_symlinks_hardlinks_and_oversize(self):
        with tempfile.TemporaryDirectory() as name:
            p = Path(name) / 'file'
            p.write_bytes(b'public fixture')
            self.assertEqual(operator.regular(p, 32)[0], b'public fixture')
            with self.assertRaisesRegex(RuntimeError, '^Oversized file: '):
                operator.regular(p, 1)
            link = Path(name) / 'link'
            link.symlink_to(p)
            with self.assertRaises(OSError):
                operator.regular(link, 32)
            link.unlink()
            os.link(p, link)
            with self.assertRaisesRegex(RuntimeError, '^Not a unique regular file: '):
                operator.regular(p, 32)

    def archive(self, extra=None):
        stream = io.BytesIO()
        contents = {'electron': b'executable', 'chrome-sandbox': b'h' * 17048,
                    'LICENSE': b'license', 'LICENSES.chromium.html': b'licenses'}
        with zipfile.ZipFile(stream, 'w') as z:
            for name, data in contents.items():
                info = zipfile.ZipInfo(name)
                info.external_attr = (stat.S_IFREG | 0o755) << 16
                z.writestr(info, data)
            if extra:
                name, mode = extra
                info = zipfile.ZipInfo(name)
                info.external_attr = mode << 16
                z.writestr(info, b'bad')
        data = stream.getvalue()
        return data, contents

    def validate_fixture(self, extra=None):
        data, contents = self.archive(extra)
        values = dict(ARCHIVE_BYTES=len(data), ARCHIVE_SHA=hashlib.sha256(data).hexdigest(),
                      PAYLOAD_BYTES=sum(map(len, contents.values())) + (3 if extra else 0),
                      EXECUTABLE_SHA=hashlib.sha256(contents['electron']).hexdigest(),
                      HELPER_SHA=hashlib.sha256(contents['chrome-sandbox']).hexdigest(),
                      EXPECTED_FILE_COUNT=len(contents),
                      EXPECTED_FILES={name: hashlib.sha256(value).hexdigest()
                                      for name, value in contents.items()})
        with patch.multiple(operator, **values):
            return operator.archive_manifest(data)

    def test_authenticated_manifest_preserves_licenses_and_exact_helper(self):
        files, directories = self.validate_fixture()
        self.assertEqual(files['chrome-sandbox']['bytes'], 17048)
        self.assertEqual(files['chrome-sandbox']['mode'], 0o755)
        self.assertEqual(set(files), {'electron', 'chrome-sandbox', 'LICENSE',
                                     'LICENSES.chromium.html'})
        self.assertEqual(directories, set())

    def test_archive_refuses_traversal_symlink_privilege_and_duplicate(self):
        for extra, guard in [
                (('../escape', stat.S_IFREG | 0o644), 'Unsafe/duplicate archive name'),
                (('/absolute', stat.S_IFREG | 0o644), 'Unsafe/duplicate archive name'),
                (('link', stat.S_IFLNK | 0o777), 'Unexpected archive type'),
                (('suid', stat.S_IFREG | 0o4755), 'Privileged/encrypted archive'),
                (('electron', stat.S_IFREG | 0o755), 'Unsafe/duplicate archive name')]:
            with self.subTest(extra=extra), self.assertRaisesRegex(RuntimeError, '^' + guard + '$'):
                self.validate_fixture(extra)

    def test_full_manifest_refuses_missing_or_wrong_member_digest(self):
        data, contents = self.archive()
        pins = dict(ARCHIVE_BYTES=len(data), ARCHIVE_SHA=hashlib.sha256(data).hexdigest(),
                    PAYLOAD_BYTES=sum(map(len, contents.values())),
                    EXECUTABLE_SHA=hashlib.sha256(contents['electron']).hexdigest(),
                    HELPER_SHA=hashlib.sha256(contents['chrome-sandbox']).hexdigest(),
                    EXPECTED_FILE_COUNT=len(contents),
                    EXPECTED_FILES={name: hashlib.sha256(value).hexdigest()
                                    for name, value in contents.items()})
        for mismatch in ('missing', 'wrong_digest'):
            expected = dict(pins['EXPECTED_FILES'])
            if mismatch == 'missing':
                expected.pop('LICENSE')
            else:
                expected['LICENSE'] = '0' * 64
            with patch.multiple(operator, **dict(pins, EXPECTED_FILES=expected)):
                guard = ('Expected exactly 72 vendor files' if mismatch == 'missing'
                         else 'Full pinned vendor manifest mismatch')
                with self.subTest(mismatch=mismatch), self.assertRaisesRegex(RuntimeError, '^' + guard + '$'):
                    operator.archive_manifest(data)

    def mocked_install(self, fail_after_privilege=False):
        helper = b'h' * 17048
        archive = b'authenticated immutable buffer fixture'
        manifest = ({}, set())
        state = SimpleNamespace(st_dev=9, st_ino=10, st_uid=0, st_gid=0,
                                st_nlink=1, st_size=17048, st_mode=stat.S_IFREG | 0o755)
        target, parent = MagicMock(), MagicMock()
        target.stat.return_value = state
        events = []
        with ExitStack() as stack:
            for name, value in dict(TARGET=target, PARENT=parent,
                                    HELPER_SHA=hashlib.sha256(helper).hexdigest()).items():
                stack.enter_context(patch.object(operator, name, value))
            stack.enter_context(patch.object(operator, 'directory_chain'))
            stack.enter_context(patch.object(operator.os.path, 'lexists', return_value=False))
            read = stack.enter_context(patch.object(operator, 'regular', return_value=(archive, state)))
            inspect = stack.enter_context(patch.object(operator, 'archive_manifest', return_value=manifest))
            extract = stack.enter_context(patch.object(operator, 'extract_fresh',
                                                       side_effect=lambda *args: events.append('extract')))
            def verify(*args, **kwargs):
                events.append('verify')
                if fail_after_privilege and kwargs.get('privileged'):
                    raise RuntimeError('synthetic final verification failure')
            stack.enter_context(patch.object(operator, 'verify_tree', side_effect=verify))
            stack.enter_context(patch.object(operator, 'write_ledger'))
            stack.enter_context(patch.object(operator.os, 'open', return_value=71))
            stack.enter_context(patch.object(operator.os, 'fstat', return_value=state))
            stack.enter_context(patch.object(operator.os, 'read', return_value=helper))
            mode = stack.enter_context(patch.object(operator.os, 'fchmod',
                                                    side_effect=lambda fd, value: events.append(value)))
            close = stack.enter_context(patch.object(operator.os, 'close'))
            stack.enter_context(patch('builtins.print'))
            if fail_after_privilege:
                with self.assertRaisesRegex(RuntimeError, 'synthetic final'):
                    operator.install()
            else:
                operator.install()
            read.assert_called_once_with(operator.SOURCE / operator.ARCHIVE_NAME, operator.ARCHIVE_BYTES)
            inspect.assert_called_once_with(archive)
            self.assertIs(extract.call_args.args[0], archive)
            extract.assert_called_once_with(archive, manifest)
            self.assertLess(events.index('verify'), events.index(0o4755))
            close.assert_called_once_with(71)
            return [call.args[1] for call in mode.call_args_list]

    def test_install_uses_same_buffer_and_verifies_before_privilege(self):
        self.assertEqual(self.mocked_install(), [0o4755])

    def test_post_privilege_failure_revokes_through_retained_descriptor(self):
        self.assertEqual(self.mocked_install(fail_after_privilege=True), [0o4755, 0o755])

    def test_pinned_archive_rejects_untrusted_bytes_before_zip_parsing(self):
        with self.assertRaisesRegex(RuntimeError, 'Archive pin mismatch'):
            operator.archive_manifest(b'untrusted')


if __name__ == '__main__':
    unittest.main()
