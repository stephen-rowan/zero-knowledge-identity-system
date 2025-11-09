"""
CLI entry point that can be run as: python -m zkidentity
Also used as the setuptools entry point.
"""

import sys
import os
import site
from pathlib import Path

# Get the project root directory
# This file is in zkidentity/, so parent.parent is the project root
_current_file = Path(__file__).resolve()
_project_root = _current_file.parent.parent.resolve()
_project_root_str = str(_project_root)

# Ensure site-packages are processed (including .pth files for editable installs)
_site_packages = _project_root / ".venv" / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages"
if _site_packages.exists():
    site_packages_str = str(_site_packages)
    if site_packages_str not in sys.path:
        site.addsitedir(site_packages_str)
    # Explicitly install editable finder if .pth file wasn't processed
    try:
        import __editable___zkidentity_0_1_0_finder
        __editable___zkidentity_0_1_0_finder.install()
    except ImportError:
        pass

# Add project root to Python path if not already there
# This ensures both zkidentity and cli modules can be imported
if _project_root_str not in sys.path:
    sys.path.insert(0, _project_root_str)

# Now import and run CLI
try:
    from cli.main import main
except ImportError as e:
    # If import fails, try one more time with explicit path manipulation
    import site
    # Add site-packages
    venv_site_packages = _project_root / ".venv" / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages"
    if venv_site_packages.exists():
        site.addsitedir(str(venv_site_packages))
    
    # Try import again
    try:
        from cli.main import main
    except ImportError:
        print(f"Error: Could not import cli.main. Project root: {_project_root_str}", file=sys.stderr)
        print(f"Python path: {sys.path[:3]}", file=sys.stderr)
        raise

if __name__ == '__main__':
    sys.exit(main())
