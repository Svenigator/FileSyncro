# build.py
import subprocess
import sys
import platform

spec = "FileSyncro-mac.spec" if platform.system() == "Darwin" else "FileSyncro.spec"
subprocess.run([sys.executable, "-m", "PyInstaller", spec, "--clean"], check=True)
print(f"Build complete — output in dist/")
