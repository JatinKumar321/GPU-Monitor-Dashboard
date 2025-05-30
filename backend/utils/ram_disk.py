import subprocess
import re
import csv # Added for wmic parsing
import io  # Added for wmic parsing

def get_ram_disk_info():
    """
    Fetches RAM and Disk usage information.
    For RAM, it tries to use `systeminfo` on Windows or `free -m` on Linux.
    For Disk, it tries to use `wmic logicaldisk` on Windows or `df -hP` on Linux.
    Returns a dictionary with RAM and disk stats, or an error message.
    """
    ram_info = {}
    disk_info = []
    error_messages = []

    # --- RAM Information --- 
    try:
        # Try Windows-specific command first
        ram_process = subprocess.Popen(["systeminfo"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=False)
        ram_stdout, ram_stderr = ram_process.communicate(timeout=20)

        if ram_process.returncode == 0:
            total_mem_match = re.search(r"Total Physical Memory:\s*([\d,]+(?:\.\d+)?)\s*MB", ram_stdout, re.IGNORECASE)
            avail_mem_match = re.search(r"Available Physical Memory:\s*([\d,]+(?:\.\d+)?)\s*MB", ram_stdout, re.IGNORECASE)
            
            if total_mem_match and avail_mem_match:
                total_mem_mb = int(float(total_mem_match.group(1).replace(",", "")))
                avail_mem_mb = int(float(avail_mem_match.group(1).replace(",", "")))
                ram_info = {
                    "total_mb": total_mem_mb,
                    "available_mb": avail_mem_mb,
                    "used_mb": total_mem_mb - avail_mem_mb,
                    "source": "systeminfo (Windows)"
                }
            else:
                # This case might mean systeminfo ran but couldn't parse, try Linux next
                raise Exception("Could not parse RAM info from systeminfo output.")
        else:
            # systeminfo failed (e.g. non-Windows or other error)
            raise Exception(f"systeminfo command failed with code {ram_process.returncode}: {ram_stderr.strip()}")

    except Exception as e_win_ram: # Catching any exception from the Windows block
        # print(f"Windows RAM info failed: {e_win_ram}. Trying Linux fallback.")
        error_messages.append(f"Windows RAM command error: {str(e_win_ram)}")
        try:
            # Linux/macOS command for RAM
            ram_process_linux = subprocess.Popen(["free", "-m"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            ram_stdout_linux, ram_stderr_linux = ram_process_linux.communicate(timeout=10)
            if ram_process_linux.returncode == 0:
                lines = ram_stdout_linux.strip().splitlines()
                if len(lines) > 1:
                    # Mem: total used free shared buff/cache available
                    parts = lines[1].split() # Second line contains actual memory data
                    ram_info = {
                        "total_mb": int(parts[1]),
                        "used_mb": int(parts[2]),
                        "free_mb": int(parts[3]),
                        "available_mb": int(parts[6]), # 'available' is usually more relevant than 'free'
                        "source": "free -m (Linux/macOS)"
                    }
                else:
                    ram_info = {"error": "Could not parse 'free -m' output."}
                    error_messages.append(ram_info["error"])
            else:
                ram_info = {"error": f"'free -m' failed (code {ram_process_linux.returncode}): {ram_stderr_linux.strip()}"}
                error_messages.append(ram_info["error"])
        except FileNotFoundError:
            ram_info = {"error": "'free -m' command not found. RAM info unavailable."}
            error_messages.append(ram_info["error"])
        except subprocess.TimeoutExpired:
            ram_info = {"error": "'free -m' command timed out."}
            error_messages.append(ram_info["error"])
        except Exception as e_nix_ram:
            ram_info = {"error": f"Error processing 'free -m': {str(e_nix_ram)}"}
            error_messages.append(ram_info["error"])

    # --- Disk Information --- 
    try:
        # Try Windows-specific command first
        disk_command = ["wmic", "logicaldisk", "get", "DeviceID,FreeSpace,Size", "/FORMAT:CSV"]
        disk_process = subprocess.Popen(disk_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=False)
        disk_stdout, disk_stderr = disk_process.communicate(timeout=15)

        if disk_process.returncode == 0 and disk_stdout.strip():
            # Skip the first line which is usually "Node,DeviceID,FreeSpace,Size"
            # And any other blank lines before the actual data
            lines = disk_stdout.strip().splitlines()
            actual_data_started = False
            temp_disk_info = []
            for line in lines:
                if not line.strip(): continue # Skip blank lines
                if line.lower().startswith("node,"):
                    actual_data_started = True
                    continue
                if not actual_data_started and line.strip(): # Handle cases where Node might be on its own line
                    if line.strip().lower() == "node": # Check if it is the header from wmic output
                         actual_data_started = True
                         continue
                
                # If we are past the header (or if no explicit header was found but we have data lines)
                # A typical data line: DESKTOP-XYZ,C:,123456789,987654321
                parts = line.strip().split(",")
                if len(parts) == 4 and parts[1].endswith(":") and parts[2].isdigit() and parts[3].isdigit():
                    device_id = parts[1]
                    free_space_bytes = int(parts[2])
                    total_size_bytes = int(parts[3])
                    if total_size_bytes > 0:
                        temp_disk_info.append({
                            "filesystem": device_id,
                            "total_gb": round(total_size_bytes / (1024**3), 2),
                            "free_gb": round(free_space_bytes / (1024**3), 2),
                            "used_gb": round((total_size_bytes - free_space_bytes) / (1024**3), 2),
                            "use_percent": round(((total_size_bytes - free_space_bytes) / total_size_bytes) * 100, 1),
                            "source": "wmic (Windows)"
                        })
            if temp_disk_info:
                disk_info = temp_disk_info
            elif not error_messages or "RAM" in error_messages[-1]: # only raise if no disk info found and no prior specific disk error
                 raise Exception("WMIC executed but no disk data parsed.")
        else:
            raise Exception(f"wmic command failed with code {disk_process.returncode}: {disk_stderr.strip()}")

    except Exception as e_win_disk:
        # print(f"Windows disk info failed: {e_win_disk}. Trying Linux fallback.")
        error_messages.append(f"Windows disk command error: {str(e_win_disk)}")
        try:
            # Linux/macOS command for disk
            disk_process_linux = subprocess.Popen(["df", "-hP"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            disk_stdout_linux, disk_stderr_linux = disk_process_linux.communicate(timeout=10)
            if disk_process_linux.returncode == 0:
                lines = disk_stdout_linux.strip().split('\n')
                temp_disk_info_linux = []
                if len(lines) > 1:
                    for line in lines[1:]: # Skip header line
                        parts = line.split()
                        if len(parts) >= 6:
                             # Filesystem Size Used Avail Use% Mounted on
                            total_str = parts[1]
                            used_str = parts[2]
                            avail_str = parts[3]
                            use_percent_str = parts[4]
                            temp_disk_info_linux.append({
                                "filesystem": parts[0],
                                "total_str": total_str,
                                "used_str": used_str,
                                "available_str": avail_str,
                                "use_percent_str": use_percent_str,
                                "mounted_on": parts[5],
                                "source": "df -hP (Linux/macOS)"
                            })
                if temp_disk_info_linux:
                    disk_info = temp_disk_info_linux
                else:
                    disk_info = {"error": "Could not parse 'df -hP' output."}
                    error_messages.append(str(disk_info["error"]))
            else:
                disk_info = {"error": f"'df -hP' failed (code {disk_process_linux.returncode}): {disk_stderr_linux.strip()}"}
                error_messages.append(str(disk_info["error"]))
        except FileNotFoundError:
            disk_info = {"error": "'df -hP' command not found. Disk info unavailable."}
            error_messages.append(str(disk_info["error"]))
        except subprocess.TimeoutExpired:
            disk_info = {"error": "'df -hP' command timed out."}
            error_messages.append(str(disk_info["error"]))
        except Exception as e_nix_disk:
            disk_info = {"error": f"Error processing 'df -hP': {str(e_nix_disk)}"}
            error_messages.append(str(disk_info["error"]))

    result = {
        "ram": ram_info if ram_info else {"error": "RAM information could not be determined."},
        "disk": disk_info if (isinstance(disk_info, list) and disk_info) else disk_info if isinstance(disk_info, dict) and "error" in disk_info else {"error": "Disk information could not be determined."}
    }
    
    # Consolidate errors if specific data sections failed but others might have succeeded
    final_errors = []
    if isinstance(result["ram"], dict) and "error" in result["ram"]:
        final_errors.append(f"RAM Error: {result['ram']['error']}")
    if isinstance(result["disk"], dict) and "error" in result["disk"]:
        final_errors.append(f"Disk Error: {result['disk']['error']}")
    elif isinstance(result["disk"], list) and not result["disk"]:
         final_errors.append("Disk Error: No disk information was populated.")

    if final_errors:
        result["errors_encountered"] = final_errors
        # If all main sections failed, it implies a broader issue
        if len(final_errors) == 2 or ( (not result["ram"] or "error" in result["ram"]) and (not result["disk"] or "error" in result["disk"]) ) :
             # If both failed, it's likely the initial error messages list is more relevant
             if error_messages and len(error_messages) > 1:
                 result["errors_encountered"] = error_messages # Show more detailed subprocess errors

    return result

if __name__ == '__main__':
    info = get_ram_disk_info()
    import json
    print(json.dumps(info, indent=4))
