#!/usr/bin/env python3
import sys
import os
import subprocess
import psutil
import google.generativeai as genai

# Configuration
_PIP = 'pip' if os.name == 'nt' else 'pip3'

DEPENDENCY_MANAGERS = {
    'requirements.txt': [_PIP, 'freeze'],
    'package.json': ['npm', 'list', '--depth=0'],
    'Cargo.toml': ['cargo', 'tree'],
    'Gemfile': ['bundle', 'list'],
    'go.mod': ['go', 'list', '-m', 'all'],
    'composer.json': ['composer', 'show'],
    'pom.xml': ['mvn', 'dependency:list'],
    'build.gradle': ['gradle', 'dependencies'],
}

def _run(cmd: list, **kwargs):
    """Cross-platform subprocess wrapper. On Windows, joins list to string for shell=True."""
    if os.name == 'nt':
        return subprocess.run(' '.join(cmd), shell=True, **kwargs)
    return subprocess.run(cmd, **kwargs)

def get_gemini_model():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)
        
    genai.configure(api_key=api_key)
    model_name = os.environ.get("MAGNIFIER_MODEL", "gemma-4")
    return genai.GenerativeModel(model_name)

def analyze_with_ai(prompt: str):
    model = get_gemini_model()
    try:
        print("Analyzing with AI...\n")
        response = model.generate_content(prompt)
        print(response.text)
    except Exception as e:
        print(f"Failed to communicate with AI: {e}", file=sys.stderr)

def list_processes(sort_by_memory=False):
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'username']):
        try:
            processes.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if sort_by_memory:
        processes = sorted(processes, key=lambda p: (p['memory_info'].rss if p['memory_info'] else 0), reverse=True)
    else:
        processes = sorted(processes, key=lambda p: (p['cpu_percent'] if p['cpu_percent'] else 0), reverse=True)

    processes = processes[:10]

    header = f"{'PID':>8} | {'CPU%':>6} | {'Memory (MB)':>11} | {'Username':<12} | {'Process Name'}"
    print(header)
    print("-" * len(header))
    for p in processes:
        pid = p['pid']
        cpu = f"{p['cpu_percent']:.1f}" if p['cpu_percent'] is not None else "0.0"
        mem = f"{(p['memory_info'].rss / 1024 / 1024):.1f}" if p['memory_info'] else "0.0"
        user = p['username'] or "N/A"
        name = p['name']
        print(f"{pid:>8} | {cpu:>6} | {mem:>11} | {user:<12} | {name}")

def list_ports():
    header = f"{'Port':>6} | {'PID':>8} | {'State':<12} | {'Process Name'}"
    print(header)
    print("-" * len(header))
    
    seen_ports = set()
    for conn in psutil.net_connections(kind='inet'):
        if conn.status != 'LISTEN' or not conn.laddr:
            continue
            
        port = conn.laddr.port
        if port in seen_ports:
            continue
        seen_ports.add(port)
            
        pid = conn.pid
        state = conn.status
        try:
            name = psutil.Process(pid).name() if pid else "Unknown"
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            name = "Unknown"
            
        print(f"{port:>6} | {pid or '-':>8} | {state:<12} | {name}")

def analyze_pid(pid: int):
    try:
        proc = psutil.Process(pid)
        info = proc.as_dict(attrs=['name', 'cmdline', 'exe', 'username', 'status'])
        prompt = (f"Analyze this process running on my system:\n"
                  f"Name: {info['name']}\n"
                  f"Command Line: {info['cmdline']}\n"
                  f"Executable Path: {info['exe']}\n"
                  f"User: {info['username']}\n"
                  f"Status: {info['status']}\n\n"
                  f"Briefly explain what this process does and if it is safe to have running.")
        analyze_with_ai(prompt)
    except psutil.NoSuchProcess:
        print(f"Error: Process with PID {pid} not found.", file=sys.stderr)
    except psutil.AccessDenied:
        print(f"Error: Access denied to read process {pid}.", file=sys.stderr)

def analyze_port(port: int):
    target_conn = None
    for conn in psutil.net_connections(kind='inet'):
        if conn.laddr and conn.laddr.port == port and conn.status == 'LISTEN':
            target_conn = conn
            break
            
    if not target_conn:
        print(f"No listening process found on port {port}.", file=sys.stderr)
        return
        
    pid = target_conn.pid
    try:
        info = psutil.Process(pid).as_dict(attrs=['name', 'cmdline', 'exe']) if pid else {}
        prompt = (f"A process is listening on network port {port}.\n"
                  f"Process details: {info}\n\n"
                  f"Briefly explain what this application is and why it might be using port {port}. Is it safe?")
        analyze_with_ai(prompt)
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        print(f"Error: Could not retrieve details for the process on port {port}.", file=sys.stderr)

def run_command(command_args: list):
    print(f"Executing: {' '.join(command_args)}")
    try:
        result = _run(command_args, capture_output=True, text=True)
        if result.stdout:
            print("--- Output ---")
            print(result.stdout)
            
        if result.returncode != 0:
            print("--- Error ---")
            print(result.stderr)
            prompt = (f"The following command failed: `{' '.join(command_args)}`\n"
                      f"Exit Code: {result.returncode}\n\n"
                      f"Error Output:\n{result.stderr}\n\n"
                      f"Please explain the root cause of the error. Specifically, diagnose if any version dependency is not installed or if an installed version is unsuitable for the project, and provide numbered steps to fix it.")
            analyze_with_ai(prompt)
    except FileNotFoundError:
        print(f"Error: Command '{command_args[0]}' not found.", file=sys.stderr)

def check_dependencies():
    print("Checking dependencies across project files...\n")
    files_content = {}
    installed = ""
    
    for filename, cmd in DEPENDENCY_MANAGERS.items():
        if os.path.exists(filename):
            print(f"Found {filename}. Fetching local environment info...")
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    files_content[filename] = f.read()[:2000]
                
                res = _run(cmd, capture_output=True, text=True)
                installed += f"Output from {' '.join(cmd)}:\n{res.stdout[:2000]}\n"
            except Exception as e:
                installed += f"Failed to run {' '.join(cmd)}: {e}\n"
                
    if not files_content:
        print("No supported dependency files found in the current directory.", file=sys.stderr)
        return
        
    prompt = (f"Analyze these dependency files:\n{files_content}\n\n"
              f"Compare them against the installed packages/environment:\n{installed}\n\n"
              f"Diagnose which version dependency is not installed, and diagnose if any version is unsuitable or incompatible for the project. Provide clear OS-agnostic commands to fix it.")
    analyze_with_ai(prompt)

def analyze_errors_from_stdin():
    if sys.stdin.isatty():
        print("Error: No piped input detected. Use something like `make 2>&1 | python magnifier.py --errors`", file=sys.stderr)
        sys.exit(1)
        
    error_text = sys.stdin.read().strip()
    if not error_text:
        print("No error text provided via stdin.")
        return
        
    prompt = (f"The following error log was generated during a process:\n\n"
              f"```\n{error_text}\n```\n\n"
              f"Please explain the root cause of these errors. Specifically, diagnose if any version dependency is not installed or if an installed version is unsuitable for the project, and provide numbered steps to fix them.")
    analyze_with_ai(prompt)

def main():
    if len(sys.argv) == 1:
        list_processes(sort_by_memory=False)
        return

    arg1 = sys.argv[1]
    
    if arg1 == "--mem":
        list_processes(sort_by_memory=True)
    elif arg1 == "--ports":
        list_ports()
    elif arg1 == "--errors":
        analyze_errors_from_stdin()
    elif arg1 == "check-deps":
        check_dependencies()
    elif arg1 == "port":
        if len(sys.argv) > 2 and sys.argv[2].isdigit():
            analyze_port(int(sys.argv[2]))
        else:
            print("Error: Please provide a valid port number.", file=sys.stderr)
    elif arg1 == "run" and len(sys.argv) >= 3 and sys.argv[2] == "--":
        command_args = sys.argv[3:]
        if not command_args:
            print("Error: Please provide a command to run.", file=sys.stderr)
        else:
            run_command(command_args)
    elif arg1.isdigit():
        analyze_pid(int(arg1))
    else:
        print("Usage:", file=sys.stderr)
        print("  python magnifier.py", file=sys.stderr)
        print("  python magnifier.py --mem", file=sys.stderr)
        print("  python magnifier.py --ports", file=sys.stderr)
        print("  python magnifier.py <pid>", file=sys.stderr)
        print("  python magnifier.py port <num>", file=sys.stderr)
        print("  python magnifier.py check-deps", file=sys.stderr)
        print("  python magnifier.py run -- <cmd>", file=sys.stderr)
        print("  <cmd> 2>&1 | python magnifier.py --errors", file=sys.stderr)

if __name__ == "__main__":
    main()
