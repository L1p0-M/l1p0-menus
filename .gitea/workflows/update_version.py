import subprocess
import os
import re

pkgbuild_path = "./PKGBUILD"
init_path = "./src/__init__.py"
INIT_VERSION = None
PKGBUILD_VERSION = None


def check_for_path(path):
    if not os.path.exists(pkgbuild_path):
        print("PKGBUILD not found!")
        exit(1)

def get_version(version_type="pkgbuild"):
    try:
        git_out = subprocess.check_output(["git", "describe", "--long", "--tags"], text=True).strip()
        parts = git_out.split("-")
        tag = parts[0]
        global PKGBUILD_VERSION
        PKGBUILD_VERSION = f"{tag}.r{parts[1]}.{parts[2][1:]}"
        global INIT_VERSION
        INIT_VERSION = f"{tag}"
        print(f"new version: {PKGBUILD_VERSION}")
    except Exception as e:
        print(f"Git error: {e}")
        exit(1)

def update_pkgbuild(new_version):
    with open(pkgbuild_path, "r") as f:
        content = f.read()

    if not re.search(r"^pkgver=", content, re.MULTILINE):
        print("pkgver not found!")
        exit(1)

    updated_content = re.sub(r"^pkgver=.*", f"pkgver={new_version}", content, flags=re.MULTILINE)

    with open(pkgbuild_path, "w") as f:
        f.write(updated_content)
    print("PKGBUILD updated successfully.")

def update_init(new_version):
    with open(init_path, "r") as f:
        content = f.read()

    if not re.search(r"^__version__ =", content, re.MULTILINE):
        print("Version not found!")
        exit(1)

    updated_content = re.sub(r"^__version__ =.*", f'__version__ = "{new_version}"', content, flags=re.MULTILINE)

    with open(init_path, "w") as f:
        f.write(updated_content)
    print("Init updated successfully.")

if __name__ == "__main__":
    check_for_path(pkgbuild_path)
    check_for_path(init_path)
    version = get_version()
    if PKGBUILD_VERSION:
        update_pkgbuild(PKGBUILD_VERSION)
    if INIT_VERSION:
        update_init(INIT_VERSION)



