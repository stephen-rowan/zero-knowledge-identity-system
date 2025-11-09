"""
CLI entry point wrapper that ensures proper module resolution.
"""

import sys
from pathlib import Path

# Add project root to path to ensure both zkidentity and cli modules can be found
# This file is in zkidentity/, so parent.parent is the project root
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Now import and run the actual CLI
try:
    from cli.main import main
except ImportError as e:
    # Fallback: try to add the path more explicitly
    import os
    project_root_str = str(project_root.resolve())
    if project_root_str not in sys.path:
        sys.path.insert(0, project_root_str)
    from cli.main import main

if __name__ == '__main__':
    main()

