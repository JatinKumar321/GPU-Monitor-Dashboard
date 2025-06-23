# GPU Monitor Dashboard

A web-based dashboard to monitor server resources with a focus on NVIDIA GPU details and LXC container information.

## Description

This project provides a real-time monitoring solution for servers, displaying key system statistics including:
*   Overall system stats: CPU, RAM, and Disk usage.
*   NVIDIA GPU information: Utilization, memory usage, temperature, etc. (via `nvidia-smi`).
*   LXC container information: User/owner, CPU/RAM usage, and storage details (via `lxc` commands).
*   A "Live Stats" view similar to `htop` or `top` for a quick overview of running processes.

The application consists of a Python Flask backend that collects system data and exposes it through a REST API, and an HTML/CSS/JavaScript frontend for data presentation.

## Features

*   **Comprehensive Overview:** Dashboard view showing key metrics at a glance.
*   **Detailed Sections:** Dedicated views for CPU, GPU, RAM/Disk, LXC containers, and Live System Stats.
*   **Real-time Data:** "Refresh All Data" button to fetch the latest information.
*   **Cross-Platform Backend (Partial):** Core backend logic attempts to support Linux, Windows, and macOS for system stats, with GPU and LXC info primarily for Linux.
*   **Simple REST API:** Easy-to-understand API endpoints for fetching data.
*   **Lightweight Frontend:** Vanilla HTML, CSS, and JavaScript for the user interface.

## Prerequisites

*   **Python 3.x**
*   **Flask** (`pip install Flask`)
*   **NVIDIA Drivers:** Required on the host system for GPU monitoring.
*   **NVIDIA CUDA Toolkit (for WSL):** If running in WSL and intending to monitor the GPU from within WSL, the CUDA toolkit and drivers need to be accessible within the WSL environment.
*   **LXC/LXD:** Required on Linux systems (or WSL 2 configured for LXD) for container monitoring.
*   **PowerShell (for Windows):** For fetching system stats on Windows.

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/JatinKumar321/GPU-Monitor-Dashboard.git
    cd gpu-monitor-dashboard
    ```

2.  **Backend Setup:**
    *   Navigate to the `backend` directory:
        ```bash
        cd backend
        ```
    *   **Create a virtual environment (recommended):**
        ```bash
        python3 -m venv venv
        source venv/bin/activate  # On Linux/macOS
        # OR
        .\venv\Scripts\activate # On Windows (PowerShell)
        ```
    *   **Install dependencies:**
        ```bash
        pip install -r requirements.txt
        ```
        *(Note: `requirements.txt` currently only lists Flask. Add other dependencies if any are introduced.)*

3.  **Frontend:**
    *   The frontend files (`index.html`, `style.css`, `script.js`) are located in the `frontend` directory and are served directly by the Flask backend. No separate build step is required.

## Running the Application

1.  **Start the Flask backend server:**
    *   Ensure you are in the `backend` directory.
    *   If you created a virtual environment, make sure it's activated.
    *   Run the Flask application:
        ```bash
        python app.py
        ```
    *   By default, the application will be accessible at `http://127.0.0.1:5000`.

2.  **Open the dashboard in your web browser:**
    *   Navigate to `http://127.0.0.1:5000`.

## API Endpoints

The backend exposes the following API endpoints:

*   `GET /api/gpu-info`: Returns NVIDIA GPU information.
*   `GET /api/ram-disk`: Returns RAM and disk usage statistics.
*   `GET /api/cpu-info`: Returns CPU information.
*   `GET /api/lxc`: Returns LXC container details.
*   `GET /api/live-stats`: Returns live system process information (similar to `top`).

## Technologies Used

*   **Backend:** Python, Flask
*   **Frontend:** HTML, CSS, JavaScript
*   **System Commands:** `nvidia-smi`, `lxc`, `top`, `df`, `free`, `psutil` (Python library, implicitly via system commands for some stats), `Get-Process` (PowerShell).

## WSL (Windows Subsystem for Linux) Setup Notes

*   **WSL 2 Required for LXD:** LXD (and its `snapd` dependency) requires WSL 2. If you are on WSL 1, you will need to upgrade your distribution.
    ```powershell
    # In PowerShell/CMD:
    wsl.exe -l -v
    wsl.exe --set-version <YourDistroName> 2
    ```
*   **LXD Installation in WSL 2:**
    ```bash
    # In WSL terminal:
    sudo apt update
    sudo apt install lxd
    sudo lxd init # Follow the prompts, defaults are usually fine for local use.
    sudo usermod -aG lxd $USER # Add your user to the lxd group
    newgrp lxd # Apply group changes or restart the terminal
    ```
*   **NVIDIA GPU Access in WSL 2:**
    *   Ensure you have the latest NVIDIA drivers installed on your Windows host.
    *   Install the NVIDIA CUDA Toolkit *inside* your WSL 2 distribution. Follow NVIDIA's official documentation for this. This will make `nvidia-smi` available within WSL.

