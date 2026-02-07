import subprocess
import sys
result = subprocess.run(['git', 'checkout', 'templates/base.html'], cwd='d:\\Safety.uz', capture_output=True, text=True)
print("Return code:", result.returncode)
print("Stdout:", result.stdout)
print("Stderr:", result.stderr)
