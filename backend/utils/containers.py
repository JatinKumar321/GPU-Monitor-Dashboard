import subprocess
import json
import re
import platform # Added for OS detection

def get_lxc_info():
    """
    Fetches LXC container information using the 'lxc' command-line tool.
    Attempts to get container name, status, IP addresses, and basic resource usage.
    This function is only applicable to Linux systems with LXC installed.

    Returns:
        list: A list of dictionaries, where each dictionary represents an LXC container (on Linux).
              Returns an error dictionary if 'lxc' command fails or parsing issues occur.
              Returns a specific message if run on a non-Linux OS.
    """
    current_os = platform.system()
    if current_os != "Linux":
        message = f"LXC container monitoring is specific to Linux. Current OS: {current_os}"
        print(message)
        return {"status": "not_applicable", "message": message, "data": []}

    try:
        # Get a list of all containers in JSON format
        list_command = ["lxc", "list", "--format", "json"]
        process = subprocess.Popen(list_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate(timeout=20)

        if process.returncode != 0:
            error_message = f"Error executing 'lxc list': {stderr.strip()}"
            print(error_message)
            return {"error": "Failed to list LXC containers", "details": stderr.strip(), "data": []}

        containers_data = json.loads(stdout)
        detailed_containers_info = []

        for container in containers_data:
            name = container.get("name")
            info = {
                "name": name,
                "status": container.get("status"),
                "type": container.get("type"),
                "ip_addresses": [],
                "memory_usage_mb": None,
                "memory_total_mb": None, # If available from limits
                "disk_usage": None, # This is highly dependent on storage backend
                "user_associated": "N/A (Requires custom logic)",
                "gpus_used": "N/A (Requires advanced GPU process correlation)"
            }

            # Extract IP addresses (ipv4 and ipv6)
            if container.get("state") and container["state"].get("network"):
                for iface, iface_data in container["state"]["network"].items():
                    for addr_info in iface_data.get("addresses", []):
                        if addr_info.get("family") == "inet":
                            info["ip_addresses"].append(f"{addr_info.get('address')}/{addr_info.get('netmask')} (ipv4)")
                        elif addr_info.get("family") == "inet6":
                            info["ip_addresses"].append(f"{addr_info.get('address')}/{addr_info.get('netmask')} (ipv6)")
            
            # Attempt to get memory usage if the container is running
            if name and container.get("status", "").lower() == "running":
                try:
                    mem_command = ["lxc", "info", name]
                    mem_process = subprocess.Popen(mem_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    mem_stdout, mem_stderr = mem_process.communicate(timeout=10)

                    if mem_process.returncode == 0:
                        # Example parsing, this might need adjustment based on 'lxc info' output format
                        current_mem_match = re.search(r"Memory usage:\n\s*Current:\s*([\d\.]+)(KiB|MiB|GiB)", mem_stdout, re.MULTILINE)
                        if current_mem_match:
                            val, unit = float(current_mem_match.group(1)), current_mem_match.group(2)
                            if unit == "GiB": val *= 1024
                            if unit == "KiB": val /= 1024
                            info["memory_usage_mb"] = round(val, 2)
                        
                        mem_limit_match = re.search(r"Memory limits:\n\s*Hard:\s*([\d\.]+)(KiB|MiB|GiB)", mem_stdout, re.MULTILINE)
                        if mem_limit_match:
                            val, unit = float(mem_limit_match.group(1)), mem_limit_match.group(2)
                            if unit == "GiB": val *= 1024
                            if unit == "KiB": val /= 1024
                            info["memory_total_mb"] = round(val, 2)
                except subprocess.TimeoutExpired:
                    print(f"Timeout getting info for LXC container {name}")
                except Exception as e_info:
                    print(f"Error getting detailed info for LXC container {name}: {e_info}")
            
            # Note on Disk Usage:
            # Disk usage is complex as it depends on the storage backend (dir, LVM, ZFS, btrfs).
            # For ZFS/btrfs, 'lxc storage info <pool_name>' might be useful, or direct ZFS/btrfs commands.
            # For dir backend, it's harder to isolate per-container usage without quotas.
            # 'lxc config get <container_name> security.disk_quota' or similar might exist.

            detailed_containers_info.append(info)

        return detailed_containers_info # On Linux, this will be the list of dicts

    except FileNotFoundError:
        error_message = "'lxc' command not found. Make sure LXC is installed and in PATH (Linux only)."
        print(error_message)
        return {"error": error_message, "data": []}
    except json.JSONDecodeError as e:
        error_message = f"Failed to parse JSON from 'lxc list': {e}"
        print(error_message)
        return {"error": error_message, "details": stdout, "data": []} # Include stdout for debugging
    except subprocess.TimeoutExpired:
        error_message = "'lxc list' command timed out."
        print(error_message)
        return {"error": error_message, "data": []}
    except Exception as e:
        error_message = f"An unexpected error occurred in get_lxc_info: {e}"
        print(error_message)
        return {"error": "An unexpected error occurred", "details": str(e), "data": []}

    # Enhanced information retrieval for each container
    enhanced_info = []
    for container in detailed_containers_info:
        container_name = container.get("name")
        container_status = container.get("status")

        # For running containers, get detailed info
        if container_status and container_status.lower() == "running":
            try:
                process_info = subprocess.Popen(["lxc", "info", container_name, "--format", "json"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                stdout_info, stderr_info = process_info.communicate(timeout=10)

                if process_info.returncode == 0:
                    info_data = json.loads(stdout_info)
                    container_details = {
                        "name": container_name,
                        "status": info_data.get("status"),
                        "ipv4": [addr["address"] for addr in info_data.get("network", {}).get("eth0", {}).get("addresses", []) if addr["family"] == "inet"],
                        "ipv6": [addr["address"] for addr in info_data.get("network", {}).get("eth0", {}).get("addresses", []) if addr["family"] == "inet6"],
                        "memory_usage_mb": "N/A",
                        "user_owner": info_data.get("config", {}).get("user.owner", "N/A"),
                        "disk_devices": [],
                        "gpu_devices": []
                    }

                    # Memory usage
                    memory_usage_bytes = info_data.get("memory", {}).get("usage")
                    if memory_usage_bytes is not None:
                        container_details["memory_usage_mb"] = round(memory_usage_bytes / (1024*1024), 2)
                    else:
                        container_details["memory_usage_mb"] = "N/A"

                    # Disk usage
                    disk_devices = []
                    for device_name, device_info in info_data.get("devices", {}).items():
                        if device_info.get("type") == "disk":
                            usage = device_info.get("usage", {})
                            disk_devices.append({
                                "name": device_name,
                                "path": device_info.get("path", "N/A"),
                                "pool": device_info.get("pool", "N/A"),
                                "total": usage.get("total", "N/A"), # May not always be available
                                "used": usage.get("used", "N/A")   # May not always be available
                            })
                    container_details["disk_devices"] = disk_devices if disk_devices else "No disk devices found or usage not reported."
                    
                    # GPU passthrough info (basic check if any GPU devices are listed)
                    gpu_devices = []
                    for device_name, device_info in info_data.get("devices", {}).items():
                        if device_info.get("type") == "gpu" or device_info.get("type") == "mdev": # mdev for mediated devices
                            gpu_devices.append({
                                "name": device_name,
                                "vendor": device_info.get("vendor"),
                                "product": device_info.get("product"),
                                "pci_address": device_info.get("pci") # Example, actual key might vary
                            })
                    container_details["gpu_devices"] = gpu_devices if gpu_devices else "No GPU devices configured."

                    enhanced_info.append(container_details)
                else:
                    enhanced_info.append({"error": f"Failed to get info for {container_name}: {stderr_info.strip()}"})
            except Exception as e:
                enhanced_info.append({"error": f"Exception while getting info for {container_name}: {str(e)}"})
        else:
            # For non-running containers, we can still return basic info
            basic_info = {
                "name": container.get("name"),
                "status": container.get("status"),
                "type": container.get("type"),
                "ip_addresses": container.get("ip_addresses"),
                "memory_usage_mb": container.get("memory_usage_mb"),
                "user_associated": container.get("user_associated"),
                "gpus_used": container.get("gpus_used"),
                "disk_usage": container.get("disk_usage")
            }
            enhanced_info.append(basic_info)

    return enhanced_info

if __name__ == '__main__':
    # For testing the function directly
    # This will only work if run on a system with LXC installed and configured.
    lxc_details = get_lxc_info()
    print(json.dumps(lxc_details, indent=4))
