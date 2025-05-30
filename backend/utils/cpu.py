import subprocess
import re
import platform

def get_cpu_info():
    """
    Fetches CPU information using WMIC on Windows or /proc/cpuinfo on Linux.
    """
    cpu_info_list = []
    current_os = platform.system()

    if current_os == "Windows":
        try:
            command = ["wmic", "cpu", "get", "Name,Manufacturer,MaxClockSpeed,NumberOfCores,NumberOfLogicalProcessors,Description,Caption,SocketDesignation", "/FORMAT:CSV"]
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=False)
            stdout, stderr = process.communicate(timeout=15)

            if process.returncode != 0:
                return {"error": "Failed to execute wmic cpu", "details": stderr.strip()}

            lines = stdout.strip().splitlines()
            if len(lines) > 1:
                header = [h.strip() for h in lines[0].split(",")]
                for line in lines[1:]:
                    if not line.strip():
                        continue
                    values = [v.strip() for v in line.split(",")]
                    # The first column from WMIC CSV is often "Node"
                    if len(values) == len(header) +1: # Node,Name,Manufacturer...
                         values_to_zip = values[1:] # Skip node
                    elif len(values) == len(header):
                         values_to_zip = values
                    else:
                        continue # malformed line

                    info = dict(zip(header, values_to_zip))
                    # Basic parsing for numerical values if they exist
                    for key in ['MaxClockSpeed', 'NumberOfCores', 'NumberOfLogicalProcessors']:
                        if key in info and info[key].isdigit():
                            info[key] = int(info[key])
                    cpu_info_list.append(info)
            return cpu_info_list if cpu_info_list else {"error": "No CPU data parsed from wmic"}

        except FileNotFoundError:
            return {"error": "wmic command not found (should be available on Windows)."}
        except subprocess.TimeoutExpired:
            return {"error": "wmic cpu command timed out."}
        except Exception as e:
            return {"error": f"An unexpected error occurred while fetching CPU info on Windows: {e}"}

    elif current_os == "Linux":
        try:
            cpuinfo = {}
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if ":" in line:
                        key, value = line.split(":", 1)
                        key = key.strip()
                        value = value.strip()
                        if key == "processor": # Start of a new processor
                            if cpuinfo: # if cpuinfo is not empty, add it to list
                                cpu_info_list.append(cpuinfo)
                            cpuinfo = {'processor_id': value}
                        elif key in ["model name", "vendor_id", "cpu family", "model", "stepping", "cpu MHz", "cache size", "siblings", "core id", "cpu cores"]:
                            cpuinfo[key.replace(" ", "_")] = value
            if cpuinfo: # Add the last processor info
                cpu_info_list.append(cpuinfo)
            
            # Consolidate into one entry per physical CPU if possible, or simplify
            # For now, returning list of logical processors as parsed
            if not cpu_info_list:
                 return {"error": "Could not parse /proc/cpuinfo"}
            return cpu_info_list

        except FileNotFoundError:
            return {"error": "/proc/cpuinfo not found (should be available on Linux)."}
        except Exception as e:
            return {"error": f"An unexpected error occurred while fetching CPU info on Linux: {e}"}
    else:
        return {"error": f"CPU info not implemented for OS: {current_os}"}

if __name__ == '__main__':
    import json
    info = get_cpu_info()
    print(json.dumps(info, indent=4))
