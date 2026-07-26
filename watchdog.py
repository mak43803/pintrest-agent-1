import sys
import os
import time
import subprocess
import shutil
import re
import logging
from pathlib import Path

# Force stdout/stderr to use UTF-8 to prevent charmap UnicodeEncodeErrors in Windows background tasks
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s │ %(levelname)-8s │ %(message)s")
logger = logging.getLogger("pinterest_agent.watchdog")

def get_ollama_model_name():
    """Dynamically find installed Qwen model from local Ollama endpoint."""
    try:
        import urllib.request
        import json
        req = urllib.request.Request("http://localhost:11434/api/tags")
        with urllib.request.urlopen(req, timeout=5) as res:
            data = json.loads(res.read().decode("utf-8"))
            models = [m.get("name") for m in data.get("models", [])]
            for m in models:
                if "qwen" in m.lower():
                    return m
            if models:
                return models[0]
    except Exception:
        pass
    return "qwen3:8b"


def call_ai_for_fix(traceback_str, source_file_path, file_content):
    """
    Sends the traceback and buggy file content to local Ollama (Qwen)
    to generate a code fix.
    """
    prompt = f"""
    The Pinterest AI Agent crashed with the following Python traceback:
    
    CRASH TRACEBACK:
    {traceback_str}
    
    The error occurred in the file '{source_file_path}'.
    Here is the current content of '{source_file_path}':
    
    SOURCE CODE:
    ```python
    {file_content}
    ```
    
    Identify the bug causing the traceback. Correct the code to fix the bug.
    Make sure you preserve all existing functionality, comments, and structure.
    Return the ENTIRE corrected Python file code inside a single code block marked with ```python.
    Do not add extra explanations or conversational text.
    """

    model_name = get_ollama_model_name()
    logger.info(f"Calling local Ollama server (model: '{model_name}') for self-healing code repair...")
    
    import urllib.request
    import json
    
    ollama_url = "http://localhost:11434/api/generate"
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False
    }
    try:
        req = urllib.request.Request(
            ollama_url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        # 3600 seconds (1 Hour) timeout buffer for slow local laptop CPUs
        with urllib.request.urlopen(req, timeout=3600) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            return res_data.get("response", "")
    except Exception as e:
        logger.error(f"Local Ollama model '{model_name}' call failed: {e}")
        
    return None

def extract_code_block(response_text):
    """Extracts python code block from markdown response."""
    if not response_text:
        return None
    match = re.search(r'```python\s*(.*?)\s*```', response_text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1)
    # If no markdown block, return raw response if it looks like code
    if "import " in response_text or "def " in response_text:
        return response_text
    return None

def parse_traceback_file(traceback_str):
    """
    Parses traceback to find the last file belonging to the project that caused the crash.
    """
    # Find all file paths in project directory from traceback
    project_dir = os.getcwd().lower()
    matches = re.findall(r'File "([^"]+)", line (\d+)', traceback_str)
    
    for file_path, line_num in reversed(matches):
        full_path = os.path.abspath(file_path)
        if full_path.lower().startswith(project_dir) and "watchdog" not in file_path:
            return full_path
    return None

def monitor_and_run():
    logger.info("=== STARTING PINTEREST AGENT WATCHDOG RUNNER ===")
    
    while True:
        logger.info("Starting Pinterest main.py script...")
        # Run main.py as a subprocess, saving stdout/stderr output
        process = subprocess.Popen(
            [sys.executable, "main.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8"
        )
        
        # Monitor outputs and log them
        stderr_accumulator = []
        while process.poll() is None:
            # Read stdout dynamically (includes stderr)
            line = process.stdout.readline()
            if line:
                stderr_accumulator.append(line)
                sys.stdout.write(line)
                sys.stdout.flush()
                
        # Process completed. Check exit code
        exit_code = process.poll()
        logger.info(f"Process exited with code: {exit_code}")
        
        if exit_code == 0:
            logger.info("Pinterest Agent process finished clean cycle. Auto-restarting main.py in 10s for 24/7 continuous operation...")
            time.sleep(10)
            continue
        else:
            logger.error("Pinterest Agent crashed! Starting Auto-Code-Repair (Self-Healing)...")
            
            # Read remainder of stdout since stderr is redirected
            remaining_stdout = process.stdout.read()
            stderr_accumulator.append(remaining_stdout)
            sys.stdout.write(remaining_stdout)
            sys.stdout.flush()
            
            traceback_str = "".join(stderr_accumulator)
            
            # Identify the project file that crashed
            crashed_file_path = parse_traceback_file(traceback_str)
            if not crashed_file_path or not os.path.exists(crashed_file_path):
                logger.error("Could not determine project file path from crash traceback. Restarting main.py in 60s...")
                time.sleep(60)
                continue
                
            logger.info(f"Targeting crashed file for repair: '{crashed_file_path}'")
            
            # Read crashed file content
            with open(crashed_file_path, "r", encoding="utf-8") as f:
                file_content = f.read()
                
            # Call AI backend to generate fix
            ai_response = call_ai_for_fix(traceback_str, crashed_file_path, file_content)
            corrected_code = extract_code_block(ai_response)
            
            if corrected_code and len(corrected_code.strip()) > 50:
                logger.info("AI generated a potential fix. Running validation checks...")
                
                # Create backup of current file
                backup_path = crashed_file_path + f".bak_{int(time.time())}"
                shutil.copy(crashed_file_path, backup_path)
                logger.info(f"Created source file backup: '{backup_path}'")
                
                # Write corrected code to file
                with open(crashed_file_path, "w", encoding="utf-8") as f:
                    f.write(corrected_code)
                    
                # Run syntax verification check using py_compile module
                try:
                    import py_compile
                    py_compile.compile(crashed_file_path, doraise=True)
                    logger.info("✅ Code syntax check passed! Auto-patched file successfully.")
                except Exception as compile_err:
                    logger.error(f"❌ AI generated invalid Python syntax: {compile_err}. Restoring backup...")
                    # Restore backup
                    shutil.copy(backup_path, crashed_file_path)
                    
            else:
                logger.error("AI response was invalid or empty. Could not generate code repair.")
                
            logger.info("Restarting Pinterest Agent main.py in 60 seconds...")
            time.sleep(60)

if __name__ == "__main__":
    try:
        monitor_and_run()
    except KeyboardInterrupt:
        logger.info("Watchdog stopped by user.")
