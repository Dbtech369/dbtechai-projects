import os
import time
import json
import base64
import subprocess
import pyautogui
from anthropic import Anthropic
from core.executor import execute_shell

client = Anthropic()

def capture_screen():
    """Takes a screenshot and returns it as base64 for Claude."""
    subprocess.run(["scrot", "current_screen.png"], capture_output=True)
    with open("current_screen.png", "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")

def execute_action(action_data):
    """Executes the action Claude decided on."""
    try:
        action = action_data.get("action")
        if action == "click":
            x, y = action_data["x"], action_data["y"]
            print(f" -> Clicking at ({x}, {y})")
            pyautogui.click(x, y)
        elif action == "right_click":
            x, y = action_data["x"], action_data["y"]
            print(f" -> Right-clicking at ({x}, {y})")
            pyautogui.rightClick(x, y)
        elif action == "double_click":
            x, y = action_data["x"], action_data["y"]
            print(f" -> Double-clicking at ({x}, {y})")
            pyautogui.doubleClick(x, y)
        elif action == "type":
            text = action_data["text"]
            print(f" -> Typing: {text}")
            pyautogui.write(text, interval=0.05)
        elif action == "press":
            key = action_data["key"]
            print(f" -> Pressing: {key}")
            pyautogui.press(key)
        elif action == "hotkey":
            keys = action_data["keys"]
            print(f" -> Hotkey: {keys}")
            pyautogui.hotkey(*keys)
        elif action == "scroll":
            x, y = action_data["x"], action_data["y"]
            direction = action_data.get("direction", "down")
            amount = action_data.get("amount", 3)
            print(f" -> Scrolling {direction} at ({x}, {y})")
            pyautogui.scroll(amount if direction == "up" else -amount, x=x, y=y)
        elif action == "wait":
            print(" -> Waiting...")
            time.sleep(2)
        elif action == "shell":
            command = action_data.get("command", "")
            print(f" -> Running shell: {command}")
            result = execute_shell(command, timeout=action_data.get("timeout", 30))
            if result["stdout"]:
                print(f"     stdout: {result['stdout'][:500]}")
            if result["stderr"]:
                print(f"     stderr: {result['stderr'][:500]}")
            print(f"     exit code: {result['returncode']}")
        elif action == "done":
            return True
    except Exception as e:
        print(f"Action error: {e}")
    return False

def run_agent(goal):
    """Main agent loop using Claude."""
    print(f"\nGoal: {goal}\n" + "="*50)
    
    messages = []
    
    system_prompt = """You are an AI agent controlling a computer. You see screenshots and decide actions.
    
Always respond with ONLY a JSON object, no markdown, no explanation:
{"action": "click", "x": 500, "y": 300}

Available actions:
{"action": "click", "x": int, "y": int}
{"action": "right_click", "x": int, "y": int}
{"action": "double_click", "x": int, "y": int}
{"action": "type", "text": "string"}
{"action": "press", "key": "enter/escape/tab/space etc"}
{"action": "hotkey", "keys": ["ctrl", "c"]}
{"action": "scroll", "x": int, "y": int, "direction": "up/down", "amount": int}
{"action": "shell", "command": "your terminal command here", "timeout": 30}
{"action": "wait"}
{"action": "done"}

Be precise with coordinates. Think step by step about what to do next."""

    while True:
        # Capture screen
        screenshot_b64 = capture_screen()
        
        # Add screenshot to messages
        messages.append({
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": screenshot_b64
                    }
                },
                {
                    "type": "text",
                    "text": f"Goal: {goal}\nWhat is the next action?"
                }
            ]
        })
        
        # Ask Claude
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=4000,
            system=system_prompt,
            messages=messages
        )
        
        reply = response.content[0].text.strip()
        print(f"Claude: {reply}")
        
        # Add Claude's response to history
        messages.append({
            "role": "assistant", 
            "content": reply
        })
        
        # Parse and execute
        try:
            clean = reply.replace("```json", "").replace("```", "").strip()
            action_data = json.loads(clean)
            done = execute_action(action_data)
            if done:
                print("\n✓ Goal accomplished!")
                break
        except json.JSONDecodeError:
            print(f"Could not parse action: {reply}")
        
        time.sleep(5)  # Small delay between steps

if __name__ == "__main__":
    goal = input("What do you want the agent to do? ")
    run_agent(goal)
