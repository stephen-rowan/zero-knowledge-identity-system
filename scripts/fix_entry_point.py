#!/usr/bin/env python3
"""
Post-install script to fix the zkidentity entry point script.
This ensures the editable finder is installed before importing zkidentity.
Run this after: pip install -e .
"""

import sys
from pathlib import Path

# Find the entry point script
venv_bin = Path(__file__).parent.parent / ".venv" / "bin" / "zkidentity"

if not venv_bin.exists():
    print(f"Error: Entry point script not found at {venv_bin}")
    sys.exit(1)

# Read the current script
with open(venv_bin, 'r') as f:
    content = f.read()

# Check if fix is already applied
if "__editable___zkidentity_0_1_0_finder" in content:
    print("Entry point script already has the fix applied.")
    sys.exit(0)

# Find the site-packages directory
venv_root = venv_bin.parent.parent
python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
site_packages = venv_root / "lib" / f"python{python_version}" / "site-packages"

# Create the fixed script
fixed_content = f"""#!/{venv_bin.parent}/python{python_version}
# Ensure editable finder is installed before importing zkidentity
import sys
import site
site_packages = '{site_packages}'
if site_packages not in sys.path:
    site.addsitedir(site_packages)
try:
    import __editable___zkidentity_0_1_0_finder
    __editable___zkidentity_0_1_0_finder.install()
except ImportError:
    pass
from zkidentity.__main__ import main
if __name__ == '__main__':
    if sys.argv[0].endswith('.exe'):
        sys.argv[0] = sys.argv[0][:-4]
    sys.exit(main())
"""

# Write the fixed script
with open(venv_bin, 'w') as f:
    f.write(fixed_content)

# Make it executable
venv_bin.chmod(0o755)

print(f"Successfully fixed entry point script at {venv_bin}")

