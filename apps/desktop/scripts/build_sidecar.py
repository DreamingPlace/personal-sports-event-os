"""Run using build venv Python; final users need no Python installation."""
from pathlib import Path
import subprocess,sys
root=Path(__file__).resolve().parents[1]
triple=subprocess.check_output(['rustc','--print','host-tuple'],text=True).strip()
args=[sys.executable,'-m','PyInstaller','--noconfirm','--clean','--onefile','--name','sports-os-sidecar-'+triple,
      '--distpath',str(root/'src-tauri/binaries'),'--workpath',str(root/'build/sidecar'),'--specpath',str(root/'build'),
      '--collect-submodules','ticketbook','--collect-submodules','openpyxl','--copy-metadata','personal-sports-event-os']
args+=[str(root/'scripts/sidecar_entry.py')]
subprocess.run(args,check=True)
