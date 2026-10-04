#!/usr/bin/env python3
import sys
import os
import subprocess
import warnings
import psutil

# Suppress deprecation and library warnings for clean terminal CLI UX
warnings.filterwarnings("ignore")

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

# Neon ANSI Color Tokens (Terminal HUD Theme)
class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    UNDERLINE = "\033[4m"

    # Neon Foreground Colors
    RED = "\033[91m"       # Errors, problems, high CPU / memory
    GREEN = "\033[92m"     # Healthy, safe, listening, resolved
    YELLOW = "\033[93m"    # PIDs, caution, warnings
    BLUE = "\033[94m"      # Info, usernames, borders
    MAGENTA = "\033[95m"   # Ports, actions, commands
    CYAN = "\033[96m"      # Headers, banners, system titles
    WHITE = "\033[97m"     # Primary text, process names
    GRAY = "\033[90m"      # Subdued dividers and borders

    # Badges
    BADGE_ERR = "\033[1;101;97m ✖ ERROR \033[0m"
    BADGE_WARN = "\033[1;103;30m ⚠ WARN \033[0m"
    BADGE_OK = "\033[1;102;30m ✔ OK \033[0m"
    BADGE_AI = "\033[1;106;30m ⚡ GEMMA-4 AI \033[0m"
    BADGE_PORT = "\033[1;45;97m ⬡ PORT \033[0m"

def print_banner(subtitle="AI Terminal Doctor"):
    bar = "═" * 63
    print(f"\n{C.CYAN}{C.BOLD}⚡ FRAMEWORK MAGNIFIER {C.RESET}{C.MAGENTA}v1.0{C.RESET} {C.GRAY}│{C.RESET} {C.GREEN}{subtitle}{C.RESET}")
    print(f"{C.BLUE}{bar}{C.RESET}")

def _run(cmd: list, **kwargs):
    """Cross-platform subprocess wrapper. On Windows, joins list to string for shell=True."""
    if os.name == 'nt':
        return subprocess.run(' '.join(cmd), shell=True, **kwargs)
    return subprocess.run(cmd, **kwargs)

def get_gemini_model():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print(f"\n{C.BADGE_ERR} {C.RED}{C.BOLD}GEMINI_API_KEY environment variable is not set.{C.RESET}", file=sys.stderr)
        print(f"{C.YELLOW}Tip: Get a free key at {C.CYAN}{C.UNDERLINE}https://aistudio.google.com{C.RESET}{C.YELLOW} and run:{C.RESET}", file=sys.stderr)
        print(f"  {C.GREEN}export GEMINI_API_KEY=\"your_api_key_here\"{C.RESET}\n", file=sys.stderr)
        sys.exit(1)
        
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    model_name = os.environ.get("MAGNIFIER_MODEL", "gemma-4")
    return genai.GenerativeModel(model_name)

def analyze_with_ai(prompt: str):
    model = get_gemini_model()
    try:
        print(f"\n{C.BADGE_AI} {C.CYAN}{C.BOLD}Diagnosing with Google Gemma-4...{C.RESET}\n")
        response = model.generate_content(prompt)
        print(f"{C.GREEN}{response.text}{C.RESET}")
    except Exception as e:
        print(f"\n{C.BADGE_ERR} {C.RED}Failed to communicate with AI: {e}{C.RESET}", file=sys.stderr)

def list_processes(sort_by_memory=False):
    title = "Top 10 Processes by Memory" if sort_by_memory else "Top 10 Processes by CPU"
    print_banner(title)

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

    header = f"{'PID':>8} │ {'CPU%':>6} │ {'Memory (MB)':>11} │ {'Username':<12} │ {'Process Name'}"
    print(f"{C.CYAN}{C.BOLD}{header}{C.RESET}")
    print(f"{C.BLUE}{'─' * 8}┼{'─' * 8}┼{'─' * 13}┼{'─' * 14}┼{'─' * 16}{C.RESET}")
    
    for p in processes:
        pid = p['pid']
        cpu_val = p['cpu_percent'] if p['cpu_percent'] is not None else 0.0
        mem_mb = (p['memory_info'].rss / 1024 / 1024) if p['memory_info'] else 0.0
        user = p['username'] or "N/A"
        name = p['name']

        # Neon Color Highlighting based on thresholds
        if cpu_val >= 30.0:
            cpu_str = f"{C.RED}{C.BOLD}{cpu_val:>6.1f}{C.RESET}"
        elif cpu_val >= 10.0:
            cpu_str = f"{C.YELLOW}{cpu_val:>6.1f}{C.RESET}"
        else:
            cpu_str = f"{C.GREEN}{cpu_val:>6.1f}{C.RESET}"

        if mem_mb >= 500.0:
            mem_str = f"{C.RED}{C.BOLD}{mem_mb:>11.1f}{C.RESET}"
        elif mem_mb >= 250.0:
            mem_str = f"{C.YELLOW}{mem_mb:>11.1f}{C.RESET}"
        else:
            mem_str = f"{C.WHITE}{mem_mb:>11.1f}{C.RESET}"

        pid_str = f"{C.YELLOW}{pid:>8}{C.RESET}"
        user_str = f"{C.BLUE}{user:<12}{C.RESET}"
        name_str = f"{C.WHITE}{C.BOLD}{name}{C.RESET}"

        print(f"{pid_str} {C.GRAY}│{C.RESET} {cpu_str} {C.GRAY}│{C.RESET} {mem_str} {C.GRAY}│{C.RESET} {user_str} {C.GRAY}│{C.RESET} {name_str}")

    print(f"{C.BLUE}{'═' * 63}{C.RESET}\n")

def _get_listening_ports():
    """Retrieve listening ports safely across all platforms (handles macOS non-root permissions)."""
    ports_map = {}
    try:
        for conn in psutil.net_connections(kind='inet'):
            if conn.status == 'LISTEN' and conn.laddr:
                p = conn.laddr.port
                if p not in ports_map:
                    ports_map[p] = (conn.pid, conn.status)
        return ports_map
    except (psutil.AccessDenied, PermissionError):
        pass

    for p in psutil.process_iter(['pid', 'name']):
        try:
            for c in p.net_connections(kind='inet'):
                if c.status == 'LISTEN' and c.laddr:
                    port = c.laddr.port
                    if port not in ports_map:
                        ports_map[port] = (p.info['pid'], c.status)
        except (psutil.NoSuchProcess, psutil.AccessDenied, PermissionError):
            continue
    return ports_map

def list_ports():
    print_banner("Active Network Port Scanner")
    header = f"{'Port':>7} │ {'PID':>8} │ {'State':<10} │ {'Process Name'}"
    print(f"{C.CYAN}{C.BOLD}{header}{C.RESET}")
    print(f"{C.BLUE}{'─' * 9}┼{'─' * 10}┼{'─' * 12}┼{'─' * 28}{C.RESET}")
    
    ports_map = _get_listening_ports()
    for port in sorted(ports_map.keys()):
        pid, state = ports_map[port]
        try:
            name = psutil.Process(pid).name() if pid else "Unknown"
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            name = "Unknown"
            
        port_str = f"{C.MAGENTA}{C.BOLD}{port:>7}{C.RESET}"
        pid_str = f"{C.YELLOW}{pid or '-':>8}{C.RESET}"
        state_str = f"{C.GREEN}{C.BOLD}{state:<10}{C.RESET}"
        name_str = f"{C.WHITE}{C.BOLD}{name}{C.RESET}"
        print(f"{port_str} {C.GRAY}│{C.RESET} {pid_str} {C.GRAY}│{C.RESET} {state_str} {C.GRAY}│{C.RESET} {name_str}")

    print(f"{C.BLUE}{'═' * 63}{C.RESET}\n")

def analyze_pid(pid: int):
    print_banner(f"Process Intelligence Report [PID {pid}]")
    try:
        proc = psutil.Process(pid)
        info = proc.as_dict(attrs=['name', 'cmdline', 'exe', 'username', 'status', 'cpu_percent', 'memory_info'])
        print(f"{C.CYAN}Process Name:{C.RESET}    {C.WHITE}{C.BOLD}{info['name']}{C.RESET}")
        print(f"{C.CYAN}User:{C.RESET}            {C.BLUE}{info['username']}{C.RESET}")
        print(f"{C.CYAN}Executable:{C.RESET}      {C.YELLOW}{info['exe']}{C.RESET}")
        print(f"{C.CYAN}Command Line:{C.RESET}    {C.MAGENTA}{' '.join(info['cmdline']) if info['cmdline'] else 'N/A'}{C.RESET}")
        print(f"{C.CYAN}Status:{C.RESET}          {C.GREEN}{info['status']}{C.RESET}")

        prompt = (f"Analyze this process running on my system:\n"
                  f"Name: {info['name']}\n"
                  f"Command Line: {info['cmdline']}\n"
                  f"Executable Path: {info['exe']}\n"
                  f"User: {info['username']}\n"
                  f"Status: {info['status']}\n\n"
                  f"Briefly explain what this process does and if it is safe to have running.")
        analyze_with_ai(prompt)
    except psutil.NoSuchProcess:
        print(f"\n{C.BADGE_ERR} {C.RED}Process with PID {pid} not found.{C.RESET}", file=sys.stderr)
    except psutil.AccessDenied:
        print(f"\n{C.BADGE_ERR} {C.RED}Access denied to read process {pid}. Try running with sudo.{C.RESET}", file=sys.stderr)

def analyze_port(port: int):
    print_banner(f"Port Intelligence Report [Port {port}]")
    ports_map = _get_listening_ports()
    if port not in ports_map:
        print(f"\n{C.BADGE_WARN} {C.YELLOW}No listening process found on port {port}.{C.RESET}", file=sys.stderr)
        return
        
    pid, state = ports_map[port]
    print(f"{C.BADGE_PORT} {C.MAGENTA}{C.BOLD}Port {port}{C.RESET} {C.GRAY}│{C.RESET} State: {C.GREEN}{state}{C.RESET} {C.GRAY}│{C.RESET} PID: {C.YELLOW}{pid}{C.RESET}")

    try:
        info = psutil.Process(pid).as_dict(attrs=['name', 'cmdline', 'exe']) if pid else {}
        if info:
            print(f"{C.CYAN}Application:{C.RESET}     {C.WHITE}{C.BOLD}{info.get('name')}{C.RESET}")
            print(f"{C.CYAN}Executable:{C.RESET}      {C.YELLOW}{info.get('exe')}{C.RESET}")
            print(f"{C.CYAN}Command:{C.RESET}         {C.MAGENTA}{' '.join(info.get('cmdline')) if info.get('cmdline') else 'N/A'}{C.RESET}")

        prompt = (f"A process is listening on network port {port}.\n"
                  f"Process details: {info}\n\n"
                  f"Briefly explain what this application is and why it might be using port {port}. Is it safe?")
        analyze_with_ai(prompt)
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        print(f"\n{C.BADGE_WARN} {C.YELLOW}Could not retrieve full process details for port {port}.{C.RESET}", file=sys.stderr)

def run_command(command_args: list):
    print_banner("Live Command Runner & AI Diagnosis")
    cmd_str = ' '.join(command_args)
    print(f"{C.CYAN}{C.BOLD}Executing:{C.RESET} {C.MAGENTA}{cmd_str}{C.RESET}\n")

    try:
        result = _run(command_args, capture_output=True, text=True)
        if result.stdout:
            print(f"{C.BLUE}┌── {C.CYAN}Standard Output{C.RESET} {C.BLUE}{'─' * 44}┐{C.RESET}")
            print(f"{C.WHITE}{result.stdout.strip()}{C.RESET}")
            print(f"{C.BLUE}└──{'─' * 60}┘{C.RESET}\n")
            
        if result.returncode != 0:
            print(f"{C.BADGE_ERR} {C.RED}{C.BOLD}Command failed with Exit Code: {result.returncode}{C.RESET}\n")
            if result.stderr:
                print(f"{C.RED}┌── {C.RED}{C.BOLD}Error Log Output{C.RESET} {C.RED}{'─' * 43}┐{C.RESET}")
                print(f"{C.RED}{result.stderr.strip()}{C.RESET}")
                print(f"{C.RED}└──{'─' * 60}┘{C.RESET}\n")

            prompt = (f"The following command failed: `{' '.join(command_args)}`\n"
                      f"Exit Code: {result.returncode}\n\n"
                      f"Error Output:\n{result.stderr}\n\n"
                      f"Please explain the root cause of the error. Specifically, diagnose if any version dependency is not installed or if an installed version is unsuitable for the project, and provide numbered steps to fix it.")
            analyze_with_ai(prompt)
        else:
            print(f"{C.BADGE_OK} {C.GREEN}{C.BOLD}Command completed successfully (Exit Code: 0){C.RESET}\n")
    except FileNotFoundError:
        print(f"\n{C.BADGE_ERR} {C.RED}Command '{command_args[0]}' not found.{C.RESET}", file=sys.stderr)

def check_dependencies():
    print_banner("Multi-Language Dependency Doctor")
    files_content = {}
    installed = ""
    
    found_any = False
    for filename, cmd in DEPENDENCY_MANAGERS.items():
        if os.path.exists(filename):
            found_any = True
            print(f"{C.BADGE_OK} {C.GREEN}Detected manifest:{C.RESET} {C.WHITE}{C.BOLD}{filename}{C.RESET} {C.GRAY}→ Querying runtime environment...{C.RESET}")
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    files_content[filename] = f.read()[:2000]
                
                res = _run(cmd, capture_output=True, text=True)
                installed += f"Output from {' '.join(cmd)}:\n{res.stdout[:2000]}\n"
            except Exception as e:
                installed += f"Failed to run {' '.join(cmd)}: {e}\n"
                
    if not found_any:
        print(f"\n{C.BADGE_WARN} {C.YELLOW}No supported dependency manifests found in current directory.{C.RESET}")
        print(f"{C.GRAY}Supported: requirements.txt, package.json, Cargo.toml, Gemfile, go.mod, composer.json, pom.xml, build.gradle{C.RESET}\n")
        return
        
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print(f"\n{C.BLUE}{'─' * 63}{C.RESET}")
        print(f"{C.CYAN}{C.BOLD}Local Manifest Preview:{C.RESET}")
        for fn in files_content:
            print(f"\n{C.MAGENTA}▶ {fn}:{C.RESET}")
            for line in files_content[fn].strip().splitlines()[:12]:
                print(f"  {C.WHITE}{line}{C.RESET}")

        print(f"\n{C.BADGE_AI} {C.YELLOW}AI Root-Cause Diagnosis available!{C.RESET}")
        print(f"{C.YELLOW}Tip: To enable Google Gemma-4 AI root-cause analysis, set your free API key:{C.RESET}")
        print(f"  {C.GREEN}export GEMINI_API_KEY=\"your_key_here\"{C.RESET} {C.GRAY}(free at https://aistudio.google.com){C.RESET}\n")
        return

    prompt = (f"Analyze these dependency files:\n{files_content}\n\n"
              f"Compare them against the installed packages/environment:\n{installed}\n\n"
              f"Diagnose which version dependency is not installed, and diagnose if any version is unsuitable or incompatible for the project. Provide clear OS-agnostic commands to fix it.")
    analyze_with_ai(prompt)

def analyze_errors_from_stdin():
    print_banner("Piped Stderr / Error Log Diagnostician")
    if sys.stdin.isatty():
        print(f"\n{C.BADGE_ERR} {C.RED}No piped input detected.{C.RESET}", file=sys.stderr)
        print(f"{C.YELLOW}Usage: {C.WHITE}cargo build 2>&1 | python3 magnifier.py --errors{C.RESET}\n", file=sys.stderr)
        sys.exit(1)
        
    error_text = sys.stdin.read().strip()
    if not error_text:
        print(f"\n{C.BADGE_WARN} {C.YELLOW}No error text provided via stdin.{C.RESET}")
        return

    print(f"{C.RED}┌── {C.RED}{C.BOLD}Captured Stderr Log{C.RESET} {C.RED}{'─' * 40}┐{C.RESET}")
    print(f"{C.RED}{error_text[:2000]}{C.RESET}")
    print(f"{C.RED}└──{'─' * 60}┘{C.RESET}\n")

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
            print(f"\n{C.BADGE_ERR} {C.RED}Please provide a valid port number (e.g. `python3 magnifier.py port 5432`).{C.RESET}\n", file=sys.stderr)
    elif arg1 == "run" and len(sys.argv) >= 3 and sys.argv[2] == "--":
        command_args = sys.argv[3:]
        if not command_args:
            print(f"\n{C.BADGE_ERR} {C.RED}Please provide a command to run (e.g. `python3 magnifier.py run -- npm build`).{C.RESET}\n", file=sys.stderr)
        else:
            run_command(command_args)
    elif arg1.isdigit():
        analyze_pid(int(arg1))
    else:
        print_banner("Help & Usage")
        print(f"{C.CYAN}Commands & Modes:{C.RESET}")
        print(f"  {C.GREEN}python3 magnifier.py{C.RESET}                {C.GRAY}Top 10 processes by CPU{C.RESET}")
        print(f"  {C.GREEN}python3 magnifier.py --mem{C.RESET}          {C.GRAY}Top 10 processes by Memory{C.RESET}")
        print(f"  {C.GREEN}python3 magnifier.py --ports{C.RESET}        {C.GRAY}Scan all listening TCP network ports{C.RESET}")
        print(f"  {C.GREEN}python3 magnifier.py <pid>{C.RESET}          {C.GRAY}AI explanation of what a PID is doing{C.RESET}")
        print(f"  {C.GREEN}python3 magnifier.py port <num>{C.RESET}    {C.GRAY}AI explanation of port usage & security{C.RESET}")
        print(f"  {C.GREEN}python3 magnifier.py check-deps{C.RESET}     {C.GRAY}Multi-language dependency drift doctor{C.RESET}")
        print(f"  {C.GREEN}python3 magnifier.py run -- <cmd>{C.RESET}   {C.GRAY}Run command with AI error diagnosis{C.RESET}")
        print(f"  {C.GREEN}<cmd> 2>&1 | python3 magnifier.py --errors{C.RESET}  {C.GRAY}Pipe error logs for AI triage{C.RESET}\n")

if __name__ == "__main__":
    main()
