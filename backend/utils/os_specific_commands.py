import platform
import subprocess

def get_live_system_stats():
    system = platform.system()
    try:
        if system == "Linux":
            # top -b -n 1: batch mode, 1 iteration
            process = subprocess.run(["top", "-b", "-n", "1"], capture_output=True, text=True, check=True, timeout=15)
            return process.stdout
        elif system == "Windows":
            # Get-Process, sort by WorkingSet (WS), take top 30, format as table
            # CPU is total CPU seconds, WS is in bytes
            cmd = [
                "powershell", "-Command",
                "Get-Process | Sort-Object WS -Descending | Select-Object -First 30 -Property ProcessName, Id, WS, CPU, Path | Format-Table -AutoSize"
            ]
            process = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=15)
            return process.stdout
        elif system == "Darwin": # macOS
            # top -l 1: 1 sample. -o cpu: sort by cpu. -n 30: show 30 processes.
            process = subprocess.run(["top", "-l", "1", "-o", "cpu", "-n", "30"], capture_output=True, text=True, check=True, timeout=15)
            return process.stdout
        else:
            return f"Unsupported OS: {system}"
    except subprocess.CalledProcessError as e:
        return f"Command failed: {e}\nOutput: {e.stderr}"
    except subprocess.TimeoutExpired:
        return "Command timed out after 15 seconds."
    except FileNotFoundError:
        return "Command not found. Ensure it is in your PATH."
    except Exception as e:
        return f"An unexpected error occurred: {e}"

if __name__ == '__main__':
    # For direct testing
    stats = get_live_system_stats()
    print(stats)
