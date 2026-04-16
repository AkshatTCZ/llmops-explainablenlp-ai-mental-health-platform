"""
Test script to verify Python environment and imports work correctly.
Run this to debug import issues.
"""

import sys
import json
from pathlib import Path

print("Python version:", sys.version, file=sys.stderr)
print("Python path:", sys.executable, file=sys.stderr)
print("Current working directory:", Path.cwd(), file=sys.stderr)
print("Script location:", Path(__file__).parent, file=sys.stderr)

# Add parent directory to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
print("Project root:", project_root, file=sys.stderr)
print("Python path:", sys.path, file=sys.stderr)

try:
    print("Attempting to import hybrid modules...", file=sys.stderr)
    from hybrid.hybrid_chat import HybridChat
    print("SUCCESS: Import successful!", file=sys.stderr)
    
    result = {
        "status": "success",
        "message": "All imports successful"
    }
    print(json.dumps(result))
    
except ImportError as e:
    print(f"IMPORT ERROR: {e}", file=sys.stderr)
    import traceback
    print(traceback.format_exc(), file=sys.stderr)
    
    result = {
        "status": "error",
        "error": str(e),
        "traceback": traceback.format_exc()
    }
    print(json.dumps(result))
    sys.exit(1)
except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    import traceback
    print(traceback.format_exc(), file=sys.stderr)
    
    result = {
        "status": "error",
        "error": str(e),
        "traceback": traceback.format_exc()
    }
    print(json.dumps(result))
    sys.exit(1)






