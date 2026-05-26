import subprocess
from pathlib import Path
from hatchling.builders.hooks.plugin.interface import BuildHookInterface

class CustomBuildHook(BuildHookInterface):
    def initialize(self, version, build_data):
        base_dir = Path(__file__).parent.resolve()
        assets_dir = base_dir / "src" / "assets"
        xml_file = assets_dir / "resources.xml"
        output_file = base_dir / "src" / "resources.gresource"

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