# build.py
import subprocess
import sys

subprocess.run([sys.executable, "-m", "PyInstaller", "FileSyncro.spec", "--clean"], check=True)
print("Build complete — executable in dist/")
