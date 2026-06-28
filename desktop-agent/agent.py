

import os
import time
import json
import pyautogui
from PIL import Image
from google import genai

# Initialize the Gemini Client
# It automatically picks up the GEMINI_API_KEY environment variable
client = genai.Client()

def capture_screen():
    """Takes a screenshot and saves it locally for the agent to analyze."""
    os.system("scrot current_screen.png")
    return "current_screen.png"

def execute_action(action_data):
    """Parses the AI decision and moves the mouse or keyboard."""
    try:
        action = action_data.get("action")
        if action == "click":
            x, y = action_data["x"], action_data["y"]
            print(f" -> Moving mouse to ({x}, {y}) and clicking.")
            pyautogui.click(x, y)
        elif action == "type":
            text = action_data["text"]
            print(f" -> Typing text: {text}")
            pyautogui.write(text, interval=0.05)
            pyautogui.press("enter")
        elif action == "wait":
            print(" -> Waiting 2 seconds for screen to load...")
            time.sleep(2)
    except Exception as e:
        print(f"Hardware execution error: {e}")

def run_agent_loop(goal):
    """The continuous perception-action cycle."""
    print(f"Starting agent task: {goal}\n" + "="*40)
    
    while True:
        # 1. Perceive
        image_path = capture_screen()
        screen_img = Image.open(image_path)
        
        # 2. Plan (Instruct the model to act as an OS operator)
        prompt = f"""
        You are an AI assistant controlling a computer system. Your ultimate goal is: "{goal}".
        Based on this screenshot, decide the very next primitive step. 
        Respond STRICTLY in JSON format with no markdown block formatting.
        
        Options:
        {{"action": "click", "x": int, "y": int}}
        {{"action": "type", "text": "string"}}
        {{"action": "wait"}}
        {{"action": "done"}}
        """
        
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[screen_img, prompt]
            )
            
            # Clean up response string if the model wrapped it in markdown code blocks
            clean_text = response.text.strip().replace("```json", "").replace("```", "")
            action_data = json.loads(clean_text)
            
            if action_data.get("action") == "done":
                print("========================================\nGoal successfully accomplished!")
                break
                
            # 3. Act
            execute_action(action_data)
            time.sleep(15) # Buffer to let the OS register the input
            
        except Exception as e:
            print(f"Loop processing error: {e}")
            break

if __name__ == "__main__":
    # Define a simple test task
    task = "Click the center of the screen"
    run_agent_loop(task)
