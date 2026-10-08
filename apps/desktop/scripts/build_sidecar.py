"""Run using build venv Python; final users need no Python installation."""
from pathlib import Path
import subprocess,sys
root=Path(__file__).resolve().parents[1]
triple=subprocess.check_output(['rustc','--print','host-tuple'],text=True).strip()
args=[sys.executable,'-m','PyInstaller','--noconfirm','--clean','--onefile','--name','sports-os-sidecar-'+triple,
      '--distpath',str(root/'src-tauri/binaries'),'--workpath',str(root/'build/sidecar'),'--specpath',str(root/'build'),
      '--collect-submodules','ticketbook','--collect-submodules','openpyxl','--collect-all','docx','--collect-all','pdfplumber','--collect-all','pdfminer','--collect-all','pypdfium2','--collect-all','pypdfium2_raw','--copy-metadata','personal-sports-event-os']
try:  # screenshot reading is bundled when the OCR extra is installed (pip install .[ocr]); its model files ship inside
    import rapidocr_onnxruntime  # noqa: F401
    args+=['--collect-all','rapidocr_onnxruntime','--collect-submodules','PIL']
except ImportError:
    print('rapidocr_onnxruntime not installed: building without screenshot reading')
args+=[str(root/'scripts/sidecar_entry.py')]
subprocess.run(args,check=True)
