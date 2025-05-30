import os
from flask import Flask, jsonify, Response, send_from_directory

# Utility function imports
from utils.gpu import get_gpu_info
from utils.ram_disk import get_ram_disk_info
from utils.containers import get_lxc_info
from utils.cpu import get_cpu_info
from utils.os_specific_commands import get_live_system_stats # For Live Stats

# --- App Configuration ---
# Determine the absolute path for the frontend directory for robustness
# __file__ is the path to this file (app.py)
# os.path.dirname(__file__) is the 'backend' directory
# os.path.join(os.path.dirname(__file__), '..', 'frontend') navigates up and into 'frontend'
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))

app = Flask(__name__, static_folder=frontend_dir, static_url_path='')
# static_url_path='' means that files from static_folder are served from the root URL (e.g., /script.js)

# --- Frontend Serving ---
@app.route('/')
def index():
    """Serves the main index.html file."""
    return send_from_directory(app.static_folder, 'index.html')

# Flask will automatically handle serving other files (e.g., script.js, style.css)
# from the static_folder due to the static_url_path='' configuration.
# For example, a request to /script.js will serve frontend_dir/script.js.

# --- API Endpoints ---
@app.route('/api/gpu-info')
def gpu_info_route():
    return jsonify(get_gpu_info())

@app.route('/api/ram-disk')
def ram_disk_route():
    return jsonify(get_ram_disk_info())

@app.route('/api/cpu-info')
def cpu_info_route():
    return jsonify(get_cpu_info())

@app.route('/api/lxc')
def lxc_route():
    return jsonify(get_lxc_info())

@app.route('/api/live-stats')
def live_stats_route():
    """Serves live system statistics as plain text."""
    stats = get_live_system_stats()
    return Response(stats, mimetype='text/plain')

# --- Main Execution ---
if __name__ == '__main__':
    # Runs the Flask development server.
    # host='0.0.0.0' makes it accessible from other devices on the network.
    # debug=True enables debug mode (auto-reloads on code changes, provides debug info).
    app.run(debug=True, host='0.0.0.0', port=5000)
