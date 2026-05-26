import subprocess
from pathlib import Path
from hatchling.build.hooks.plugin.interface import BuildHookInterface

class CustomBuildHook(BuildHookInterface):
    def initialize(self, version, build_data):
        assets_dir = Path(self.root) / "src" / "assets"
        xml_file = assets_dir / "resources.xml"
        output_file = Path(self.root) / "src" / "resources.gresource"

        if xml_file.exists():
            print(f"Compiling GResource: {xml_file} to {output_file}")
            subprocess.run(
                [
                    "glib-compile-resources",
                    "--target", str(output_file),
                    "--sourcedir", str(assets_dir),
                    str(xml_file)
                ],
                check=True
            )
        else:
            print("Warning: resources.xml not found, skipping compilation.")