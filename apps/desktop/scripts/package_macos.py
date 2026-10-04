"""Archive only sealed macOS bundles; signature validity is NOT Gatekeeper trust."""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def verify(app):
    app = Path(app).resolve()
    if not (app / 'Contents/_CodeSignature/CodeResources').is_file():
        raise ValueError('BLOCK: missing bundle resource seal')
    subprocess.run(['/usr/bin/codesign', '--verify', '--deep', '--strict',
                    '--verbose=2', str(app)], check=True, capture_output=True, text=True)
    # Check every shipped executable, including the frozen Python sidecar.
    for binary in (app / 'Contents/MacOS').iterdir():
        if binary.is_file():
            subprocess.run(['/usr/bin/codesign', '--verify', '--strict', str(binary)],
                           check=True, capture_output=True, text=True)


def package(app, archive):
    app, archive = Path(app).resolve(), Path(archive).resolve()
    if archive.suffix != '.zip':
        raise ValueError('Archive must end in .zip')
    if archive.exists():
        raise FileExistsError(archive)
    verify(app)
    archive.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='sports-package-', dir=archive.parent) as temp:
        temp = Path(temp)
        candidate = temp / archive.name
        subprocess.run(['/usr/bin/ditto', '-c', '-k', '--sequesterRsrc', '--keepParent',
                        str(app), str(candidate)], check=True)
        extracted = temp / 'extracted'
        subprocess.run(['/usr/bin/ditto', '-x', '-k', str(candidate), str(extracted)], check=True)
        verify(extracted / app.name)
        digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
        # Do not expose an archive until its extracted signature has passed.
        with archive.open('xb') as output, candidate.open('rb') as source:
            shutil.copyfileobj(source, output)
    return dict(archive=str(archive), sha256=digest, signature='PASS',
                archive_roundtrip='PASS', gatekeeper='NOT_ASSESSED', notarization='NOT_ASSESSED')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('app', type=Path)
    parser.add_argument('archive', type=Path)
    args = parser.parse_args()
    verify(args.app)
    subprocess.run([sys.executable, str(Path(__file__).with_name('smoke_packaged.py')),
                    str(args.app.resolve() / 'Contents/MacOS/sports-os-sidecar')], check=True)
    print(json.dumps(package(args.app, args.archive), indent=2))
