"""
Hybrid chat system that combines emotion detection, style prompts, and local LLM
to generate natural, emotion-aware responses.
"""

try:
    from hybrid.emotion_detector import detect_emotion
    from hybrid.style_prompts import get_system_prompt, format_user_prompt, get_emotion_bucket
    from hybrid.local_llm import chat, check_ollama_connection
except ImportError:
    # Fallback for direct execution or if hybrid is not a package
    from emotion_detector import detect_emotion
    from style_prompts import get_system_prompt, format_user_prompt, get_emotion_bucket
    from local_llm import chat, check_ollama_connection
from typing import List, Dict, Optional

class HybridChat:
    """
    A hybrid chat system that uses emotion detection and style prompts
    to generate contextually appropriate responses.
    """
    
    def __init__(self, model: str = "phi3", base_url: str = "http://localhost:11434"):
        """
        Initialize the hybrid chat system.
        
        Args:
            model: The Ollama model to use (default: "phi3")
            base_url: The base URL for Ollama API (default: "http://localhost:11434")
        """
        self.model = model
        self.base_url = base_url
        self.conversation_history: List[Dict[str, str]] = []
        self.current_emotion: Optional[str] = None
        self.current_system_prompt: Optional[str] = None
        
        # Check Ollama connection
        if not check_ollama_connection(base_url):
            raise ConnectionError(
                f"Ollama is not running at {base_url}. "
                "Please start Ollama with: ollama serve"
            )
    
    def detect_and_respond(self, user_message: str, include_emotion_in_response: bool = False) -> str:
        """
        Detect emotion from user message and generate an appropriate response.
        
        Args:
            user_message: The user's message text
            include_emotion_in_response: Whether to include detected emotion info in the response
        
        Returns:
            str: The generated response from the LLM
        """
        # Detect emotion from user message
        emotion = detect_emotion(user_message)
        self.current_emotion = emotion
        
        # Get emotion bucket for style selection
        emotion_bucket = get_emotion_bucket(emotion)
        
        # Get system prompt based on detected emotion
        system_prompt = get_system_prompt(emotion)
        self.current_system_prompt = system_prompt
        
        # Format user message with emotion context
        formatted_user_message = format_user_prompt(emotion, user_message)
        
        # Build messages for chat API
        messages = []
        
        # Add system prompt if this is the first message or emotion changed
        if not self.conversation_history or self._should_update_system_prompt(emotion_bucket):
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        else:
            # Use existing system prompt from history
            if self.conversation_history and self.conversation_history[0].get("role") == "system":
                messages.append(self.conversation_history[0])
        
        # Add conversation history (excluding system message if already added)
        start_idx = 1 if messages and messages[0].get("role") == "system" else 0
        messages.extend(self.conversation_history[start_idx:])
        
        # Add current user message
        messages.append({
            "role": "user",
            "content": formatted_user_message
        })
        
        # Get response from local LLM
        try:
            response = chat(messages, model=self.model, base_url=self.base_url)
        except Exception as e:
            raise RuntimeError(f"Error generating response from LLM: {str(e)}")
        
        # Update conversation history
        self.conversation_history = messages
        self.conversation_history.append({
            "role": "assistant",
            "content": response
        })
        
        # Optionally include emotion info in response
        if include_emotion_in_response:
            return f"[Detected emotion: {emotion}] {response}"
        
        return response
    
    def _should_update_system_prompt(self, emotion_bucket: str) -> bool:
        """
        Determine if system prompt should be updated based on emotion bucket change.
        
        Args:
            emotion_bucket: The current emotion bucket
        
        Returns:
            bool: True if system prompt should be updated
        """
        if not self.conversation_history:
            return True
        
        # Check if first message is a system message
        if self.conversation_history[0].get("role") != "system":
            return True
        
        # For simplicity, we'll update if emotion bucket changed
        # In a more sophisticated implementation, you could track the last emotion bucket
        return True
    
    def reset_conversation(self):
        """Reset the conversation history."""
        self.conversation_history = []
        self.current_emotion = None
        self.current_system_prompt = None
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """
        Get the current conversation history.
        
        Returns:
            List of message dictionaries with 'role' and 'content' keys
        """
        return self.conversation_history.copy()
    
    def get_current_emotion(self) -> Optional[str]:
        """
        Get the emotion detected from the last user message.
        
        Returns:
            str: The emotion name, or None if no message has been processed yet
        """
        return self.current_emotion


def chat_with_emotion(user_message: str, model: str = "phi3", base_url: str = "http://localhost:11434") -> str:
    """
    Simple function to get an emotion-aware response for a single message.
    Creates a new chat instance for each call (no conversation history).
    
    Args:
        user_message: The user's message text
        model: The Ollama model to use (default: "phi3")
        base_url: The base URL for Ollama API (default: "http://localhost:11434")
    
    Returns:
        str: The generated response
    """
    chat_instance = HybridChat(model=model, base_url=base_url)
    return chat_instance.detect_and_respond(user_message)


if __name__ == "__main__":
    # Example usage
    print("="*60)
    print("Hybrid Chat System - Emotion-Aware Responses")
    print("="*60)
    
    try:
        # Create chat instance
        hybrid_chat = HybridChat()
        
        # Example conversations
        test_messages = [
            "I'm feeling really sad today. Nothing seems to be going right.",
            "I'm so excited! I just got accepted to my dream university!",
            "I'm really angry about what happened at work today.",
            "I'm feeling anxious about my upcoming presentation."
        ]
        
        print("\nTesting emotion-aware responses:\n")
        
        for i, message in enumerate(test_messages, 1):
            print(f"User: {message}")
            print(f"Detected emotion: {hybrid_chat.detect_and_respond(message, include_emotion_in_response=True)}")
            print("-" * 60)
            
            # Reset for each message to show different emotions
            hybrid_chat.reset_conversation()
        
        # Test conversation flow
        print("\n" + "="*60)
        print("Testing conversation flow (with history):")
        print("="*60)
        
        hybrid_chat.reset_conversation()
        
        user_msg1 = "I've been feeling really down lately."
        print(f"\nUser: {user_msg1}")
        response1 = hybrid_chat.detect_and_respond(user_msg1)
        print(f"Assistant: {response1}")
        print(f"Detected emotion: {hybrid_chat.get_current_emotion()}")
        
        user_msg2 = "I don't know what to do about it."
        print(f"\nUser: {user_msg2}")
        response2 = hybrid_chat.detect_and_respond(user_msg2)
        print(f"Assistant: {response2}")
        print(f"Detected emotion: {hybrid_chat.get_current_emotion()}")
        
    except ConnectionError as e:
        print(f"Error: {e}")
        print("\nPlease make sure:")
        print("1. Ollama is running: ollama serve")
        print("2. phi3 model is installed: ollama pull phi3")
    except Exception as e:
        print(f"Error: {e}")

