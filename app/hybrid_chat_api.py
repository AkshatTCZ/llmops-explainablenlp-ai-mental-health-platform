"""
API wrapper for hybrid_chat.py to be called from Node.js
Takes command line arguments and returns JSON output.
"""

import sys
import json
import traceback
from pathlib import Path
import os

# Add parent directory to path to import hybrid modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Change to project root to ensure relative imports work
os.chdir(project_root)

try:
    from hybrid.hybrid_chat import HybridChat
except ImportError as e:
    error_result = {
        "error": f"Failed to import hybrid_chat: {str(e)}",
        "traceback": traceback.format_exc(),
        "python_path": sys.path
    }
    print(json.dumps(error_result), file=sys.stderr)
    sys.exit(1)

# Global chat instances
chat_instances = {}

def main():
    if len(sys.argv) < 3:
        error_result = {
            "error": "Usage: python hybrid_chat_api.py <sessionId> <message> [reset]"
        }
        print(json.dumps(error_result), file=sys.stderr)
        sys.exit(1)
    
    session_id = sys.argv[1]
    message = sys.argv[2]
    reset = len(sys.argv) > 3 and sys.argv[3].lower() == 'true'
    
    try:
        # Get or create chat instance
        if reset or session_id not in chat_instances:
            chat_instances[session_id] = HybridChat()
            if reset:
                chat_instances[session_id].reset_conversation()
        
        chat = chat_instances[session_id]
        
        # Get response
        response = chat.detect_and_respond(message)
        emotion = chat.get_current_emotion()
        
        result = {
            "response": response,
            "emotion": emotion,
            "sessionId": session_id
        }
        
        print(json.dumps(result))
        sys.stdout.flush()
        
    except Exception as e:
        error_result = {
            "error": str(e),
            "traceback": traceback.format_exc(),
            "sessionId": session_id
        }
        print(json.dumps(error_result), file=sys.stderr)
        sys.stderr.flush()
        sys.exit(1)

if __name__ == "__main__":
    main()

