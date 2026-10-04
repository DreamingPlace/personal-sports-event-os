"""Native signing regression checks; skipped explicitly on non-macOS hosts."""
import importlib.util
import json
import plistlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('package_macos', ROOT / 'apps/desktop/scripts/package_macos.py')
packaging = importlib.util.module_from_spec(spec)
spec.loader.exec_module(packaging)


class PackagingConfigTests(unittest.TestCase):
    def test_explicit_signing_and_version_consistency(self):
        config = json.loads((ROOT / 'apps/desktop/src-tauri/tauri.conf.json').read_text())
        package = json.loads((ROOT / 'apps/desktop/package.json').read_text())
        self.assertEqual(config['bundle']['macOS']['signingIdentity'], '-')
        self.assertEqual(config['version'], package['version'])
        entitlements = plistlib.loads((ROOT / 'apps/desktop/src-tauri' /
                                      config['bundle']['macOS']['entitlements']).read_bytes())
        self.assertEqual(entitlements, {'com.apple.security.cs.disable-library-validation': True})
        self.assertTrue(config['bundle']['macOS'].get('hardenedRuntime', True))


@unittest.skipUnless(sys.platform == 'darwin', 'macOS codesign/ditto required')
class MacPackagingTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='sports-sign-test-')
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.app = self.root / 'Synthetic.app'
        contents = self.app / 'Contents'
        (contents / 'MacOS').mkdir(parents=True)
        (contents / 'Resources').mkdir()
        shutil.copyfile('/usr/bin/true', contents / 'MacOS/synthetic')
        (contents / 'MacOS/synthetic').chmod(0o755)
        (contents / 'Info.plist').write_bytes(plistlib.dumps(dict(
            CFBundleIdentifier='local.synthetic.sign-test', CFBundleExecutable='synthetic',
            CFBundlePackageType='APPL', CFBundleVersion='1')))
        (contents / 'Resources/demo.txt').write_text('SYNTHETIC')
        self.archive = self.root / 'test.zip'

    def sign(self):
        subprocess.run(['/usr/bin/codesign', '--force', '--sign', '-', str(self.app)],
                       check=True, capture_output=True)

    def test_unsealed_bundle_is_blocked_without_artifact(self):
        with self.assertRaisesRegex(ValueError, 'resource seal'):
            packaging.package(self.app, self.archive)
        self.assertFalse(self.archive.exists())

    def test_sealed_bundle_survives_archive_roundtrip(self):
        self.sign()
        result = packaging.package(self.app, self.archive)
        self.assertEqual(result['archive_roundtrip'], 'PASS')
        self.assertEqual(result['gatekeeper'], 'NOT_ASSESSED')
        self.assertEqual(len(result['sha256']), 64)

    def test_tampered_resource_is_blocked(self):
        self.sign()
        (self.app / 'Contents/Resources/demo.txt').write_text('CHANGED')
        with self.assertRaises(subprocess.CalledProcessError):
            packaging.package(self.app, self.archive)
        self.assertFalse(self.archive.exists())

    def test_existing_archive_is_not_overwritten(self):
        self.archive.write_bytes(b'preserve')
        with self.assertRaises(FileExistsError):
            packaging.package(self.app, self.archive)
        self.assertEqual(self.archive.read_bytes(), b'preserve')
