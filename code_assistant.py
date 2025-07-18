import os
from dotenv import load_dotenv
from groq import Groq
import textwrap

load_dotenv()

class CodeAssistant:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.available_models = {
            "1": {"name": "mixtral-8x7b-32768", "description": "Fast and capable (recommended)"},
            "2": {"name": "llama3-8b-8192", "description": "Lightweight and efficient"},
            "3": {"name": "llama3-70b-8192", "description": "Most powerful (slower)"}
        }
        self.model = self.available_models["1"]["name"]  # Default to Mixtral
        self.system_prompt = textwrap.dedent("""
            You are an expert Python programming assistant. Follow these guidelines:
            1. Provide clear, concise, and correct code solutions
            2. Explain complex parts of the code
            3. Suggest optimizations when relevant
            4. Include error handling examples
            5. Recommend best practices
        """)
        self.conversation_history = []
        
    def select_model(self):
        """Allow user to select a different model"""
        print("\nAvailable models:")
        for key, model in self.available_models.items():
            print(f"{key}. {model['name']} - {model['description']}")
        
        while True:
            choice = input("\nSelect model (1-3) or 'c' to cancel: ")
            if choice.lower() == 'c':
                return
            if choice in self.available_models:
                self.model = self.available_models[choice]["name"]
                print(f"Model changed to {self.model}")
                return
            print("Invalid choice. Please try again.")

    def get_code_assistance(self, prompt):
        """Get coding assistance from Groq API"""
        try:
            messages = [
                {"role": "system", "content": self.system_prompt},
                *self.conversation_history,
                {"role": "user", "content": prompt}
            ]
            
            response = self.client.chat.completions.create(
                messages=messages,
                model=self.model,
                temperature=0.3,
                max_tokens=4000  # Increased for longer code examples
            )
            
            assistant_response = response.choices[0].message.content
            self.conversation_history.extend([
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": assistant_response}
            ])
            
            return assistant_response
            
        except Exception as e:
            return f"API Error: {str(e)}"

    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        return "Conversation history cleared."

    def run(self):
        """Main interactive loop"""
        print("\nPython Code Assistant (type 'help' for commands)")
        print("----------------------------------------------")
        
        while True:
            user_input = input("\nYour coding question: ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() == 'exit':
                break
                
            if user_input.lower() == 'help':
                print("\nAvailable commands:")
                print("help - Show this help")
                print("model - Change AI model")
                print("clear - Clear conversation history")
                print("exit - Quit the program")
                continue
                
            if user_input.lower() == 'model':
                self.select_model()
                continue
                
            if user_input.lower() == 'clear':
                print(self.clear_history())
                continue
            
            response = self.get_code_assistance(user_input)
            print("\nAssistant:")
            print(response)

if __name__ == "__main__":
    assistant = CodeAssistant()
    assistant.run()