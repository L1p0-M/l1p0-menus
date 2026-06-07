import subprocess
import os
import re

pkgbuild_path = "./PKGBUILD"

if not os.path.exists(pkgbuild_path):
    print("PKGBUILD not found!")
    exit(1)

try:
    git_out = subprocess.check_output(["git", "describe", "--long", "--tags"], text=True).strip()
    parts = git_out.split("-")
    tag = parts[0]
    new_version = f"{tag}.r{parts[1]}.{parts[2][1:]}"
    print(f"new version: {new_version}")
except Exception as e:
    print(f"Git error: {e}")
    exit(1)

with open(pkgbuild_path, "r") as f:
    content = f.read()

if not re.search(r"^pkgver=", content, re.MULTILINE):
    print("pkgver not found!")
    exit(1)

updated_content = re.sub(r"^pkgver=.*", f"pkgver={new_version}", content, flags=re.MULTILINE)

with open(pkgbuild_path, "w") as f:
    f.write(updated_content)

print("PKGBUILD updated successfully.")