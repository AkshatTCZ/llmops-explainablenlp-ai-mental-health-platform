"""
Local LLM interface using Ollama with phi3 model.
Sends prompts to Ollama and returns responses.
"""

import requests
import json
from typing import Optional

# Default Ollama configuration
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "phi3"

def generate_response(
    prompt: str,
    model: str = OLLAMA_MODEL,
    base_url: str = OLLAMA_BASE_URL,
    stream: bool = False,
    system: Optional[str] = None,
    **kwargs
) -> str:
    """
    Generate a response from Ollama using the specified model.
    
    Args:
        prompt: The user prompt to send to the model
        model: The model name to use (default: "phi3")
        base_url: The base URL for Ollama API (default: "http://localhost:11434")
        stream: Whether to stream the response (default: False)
        system: Optional system prompt to set the assistant's behavior
        **kwargs: Additional parameters to pass to Ollama API
    
    Returns:
        str: The generated response text
    
    Raises:
        requests.exceptions.RequestException: If the request to Ollama fails
        ConnectionError: If Ollama is not running or not accessible
    """
    url = f"{base_url}/api/generate"
    
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": stream
    }
    
    # Add system prompt if provided
    if system:
        payload["system"] = system
    
    # Add any additional parameters
    payload.update(kwargs)
    
    try:
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        
        if stream:
            # Handle streaming response
            full_response = ""
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    if "response" in data:
                        full_response += data["response"]
                    if data.get("done", False):
                        break
            return full_response
        else:
            # Handle non-streaming response
            data = response.json()
            return data.get("response", "")
            
    except requests.exceptions.ConnectionError:
        raise ConnectionError(
            f"Could not connect to Ollama at {base_url}. "
            "Make sure Ollama is running. You can start it with: ollama serve"
        )
    except requests.exceptions.Timeout:
        raise TimeoutError(
            "Request to Ollama timed out. The model may be taking too long to respond."
        )
    except requests.exceptions.HTTPError as e:
        raise requests.exceptions.RequestException(
            f"HTTP error from Ollama: {e.response.status_code} - {e.response.text}"
        )

def chat(
    messages: list,
    model: str = OLLAMA_MODEL,
    base_url: str = OLLAMA_BASE_URL,
    **kwargs
) -> str:
    """
    Send a chat conversation to Ollama and get a response.
    
    Args:
        messages: List of message dictionaries with "role" and "content" keys
                 Example: [{"role": "system", "content": "..."}, 
                           {"role": "user", "content": "..."}]
        model: The model name to use (default: "phi3")
        base_url: The base URL for Ollama API (default: "http://localhost:11434")
        **kwargs: Additional parameters to pass to Ollama API
    
    Returns:
        str: The generated response text
    """
    url = f"{base_url}/api/chat"
    
    payload = {
        "model": model,
        "messages": messages,
        "stream": False
    }
    
    # Add any additional parameters
    payload.update(kwargs)
    
    try:
        # Increased timeout to 300 seconds (5 minutes) for slower systems
        response = requests.post(url, json=payload, timeout=300)
        response.raise_for_status()
        
        data = response.json()
        return data.get("message", {}).get("content", "")
        
    except requests.exceptions.ConnectionError:
        raise ConnectionError(
            f"Could not connect to Ollama at {base_url}. "
            "Make sure Ollama is running. You can start it with: ollama serve"
        )
    except requests.exceptions.Timeout:
        raise TimeoutError(
            "Request to Ollama timed out. The model may be taking too long to respond."
        )
    except requests.exceptions.HTTPError as e:
        raise requests.exceptions.RequestException(
            f"HTTP error from Ollama: {e.response.status_code} - {e.response.text}"
        )

def check_ollama_connection(base_url: str = OLLAMA_BASE_URL) -> bool:
    """
    Check if Ollama is running and accessible.
    
    Args:
        base_url: The base URL for Ollama API (default: "http://localhost:11434")
    
    Returns:
        bool: True if Ollama is accessible, False otherwise
    """
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False

if __name__ == "__main__":
    # Example usage
    print("Testing Ollama connection...")
    
    if check_ollama_connection():
        print("✓ Ollama is running and accessible")
        
        # Test simple generation
        print("\nTesting simple generation...")
        response = generate_response("Hello! Can you tell me a short joke?")
        print(f"Response: {response}")
        
        # Test chat interface
        print("\nTesting chat interface...")
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is 2+2?"}
        ]
        chat_response = chat(messages)
        print(f"Chat Response: {chat_response}")
    else:
        print("✗ Ollama is not running or not accessible")
        print("Please start Ollama with: ollama serve")
        print("Or make sure phi3 model is installed: ollama pull phi3")

