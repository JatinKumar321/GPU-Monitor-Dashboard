import subprocess
import csv
import io

def get_gpu_info():
    """
    Fetches GPU information using nvidia-smi.
    Returns a list of dictionaries, where each dictionary represents a GPU,
    or a dictionary with an error message if something goes wrong.
    """
    try:
        # Command to get GPU info in CSV format
        # Adjust fields as needed. For more fields, see `nvidia-smi --help-query-gpu`
        command = [
            "nvidia-smi",
            "--query-gpu=name,pci.bus_id,driver_version,temperature.gpu,utilization.gpu,utilization.memory,memory.total,memory.free,memory.used",
            "--format=csv,noheader,nounits"
        ]
        # Note: On Windows, nvidia-smi is typically in C:\Program Files\NVIDIA Corporation\NVSMI\
        # Ensure this path is in your system's PATH environment variable.
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=False)
        stdout, stderr = process.communicate(timeout=15) # Added timeout

        if process.returncode != 0:
            error_message = f"Error executing nvidia-smi (code {process.returncode}): {stderr.strip()}"
            print(error_message)
            return {"error": "Failed to execute nvidia-smi", "details": stderr.strip()}

        gpu_info_list = []
        # Use io.StringIO to treat the string output as a file for the csv reader
        csv_reader = csv.reader(io.StringIO(stdout))
        for row in csv_reader:
            if not row or len(row) < 9:  # Skip empty rows or rows with insufficient data
                continue
            try:
                gpu_info_list.append({
                    "name": row[0].strip(),
                    "pci_bus_id": row[1].strip(),
                    "driver_version": row[2].strip(),
                    "temperature_gpu": float(row[3].strip()) if row[3].strip().replace('.', '', 1).isdigit() else row[3].strip(),
                    "utilization_gpu": float(row[4].strip()) if row[4].strip().replace('.', '', 1).isdigit() else row[4].strip(), # %
                    "utilization_memory": float(row[5].strip()) if row[5].strip().replace('.', '', 1).isdigit() else row[5].strip(), # %
                    "memory_total_mb": float(row[6].strip()) if row[6].strip().replace('.', '', 1).isdigit() else row[6].strip(), # MiB
                    "memory_free_mb": float(row[7].strip()) if row[7].strip().replace('.', '', 1).isdigit() else row[7].strip(), # MiB
                    "memory_used_mb": float(row[8].strip()) if row[8].strip().replace('.', '', 1).isdigit() else row[8].strip(), # MiB
                })
            except ValueError as e:
                print(f"ValueError parsing row {row}: {e}")
                # Optionally skip this GPU or add placeholder data
                continue
        return gpu_info_list
    except FileNotFoundError:
        error_message = "nvidia-smi command not found. Make sure NVIDIA drivers are installed and nvidia-smi is in your system's PATH."
        print(error_message)
        return {"error": error_message}
    except subprocess.TimeoutExpired:
        error_message = "nvidia-smi command timed out."
        print(error_message)
        return {"error": error_message}
    except Exception as e:
        error_message = f"An unexpected error occurred in get_gpu_info: {e}"
        print(error_message)
        return {"error": "An unexpected error occurred", "details": str(e)}

if __name__ == '__main__':
    # For testing the function directly
    info = get_gpu_info()
    # Pretty print the JSON output
    import json
    print(json.dumps(info, indent=4))
