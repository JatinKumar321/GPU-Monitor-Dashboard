document.addEventListener('DOMContentLoaded', () => {
    const API_BASE_URL = ''; // Assuming Flask serves frontend and API from the same origin

    // Content sections
    const sections = {
        overview: document.getElementById('overview-section'),
        cpu: document.getElementById('cpu-section'),
        gpu: document.getElementById('gpu-section'),
        ramDisk: document.getElementById('ram-disk-section'),
        lxc: document.getElementById('lxc-section'),
        liveStats: document.getElementById('live-stats-section'), // New section
    };

    // Data display elements
    const elements = {
        // Overview specific
        overviewCpu: document.getElementById('overview-cpu').querySelector('pre'),
        overviewRam: document.getElementById('overview-ram').querySelector('pre'),
        overviewDisk: document.getElementById('overview-disk').querySelector('pre'),
        // Detailed sections
        cpuInfo: document.getElementById('cpu-info'),
        gpuInfo: document.getElementById('gpu-info'),
        ramInfo: document.getElementById('ram-info'),
        diskInfo: document.getElementById('disk-info'),
        lxcInfo: document.getElementById('lxc-info'), // This is the container for the rich HTML
        liveStatsDisplay: document.getElementById('live-stats-display'), // New element for live stats <pre>
        timestamp: document.getElementById('timestamp'),
    };

    // Navigation buttons
    const navButtons = {
        overview: document.getElementById('btn-overview'),
        cpu: document.getElementById('btn-cpu'),
        gpu: document.getElementById('btn-gpu'),
        ramDisk: document.getElementById('btn-ram-disk'),
        lxc: document.getElementById('btn-lxc'),
        liveStats: document.getElementById('btn-live-stats'), // New button
    };
    const refreshAllButton = document.getElementById('btn-refresh-all');

    // Helper function to fetch data
    async function fetchData(endpoint, expectJson = true) {
        try {
            const response = await fetch(`${API_BASE_URL}/api/${endpoint}`);
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
            }
            if (expectJson) {
                return await response.json();
            }
            return await response.text(); // For plain text responses
        } catch (error) {
            console.error(`Error fetching ${endpoint}:`, error);
            if (expectJson) {
                return { error: `Failed to load data from ${endpoint}. ${error.message}` };
            }
            return `Error fetching ${endpoint}: ${error.message}`;
        }
    }

    // Helper function to display data (handles errors and formats JSON)
    function displayData(element, data) {
        if (data && data.error) {
            element.textContent = `Error: ${data.error}`;
            if(data.details) element.textContent += `\nDetails: ${data.details}`;
        } else if (data && data.status === "not_applicable"){
            element.textContent = data.message;
        } else if (data && Object.keys(data).length > 0) {
            element.textContent = JSON.stringify(data, null, 2);
        } else if (data && Array.isArray(data) && data.length === 0) {
            element.textContent = "No data available or applicable for this system.";
        } 
        else {
            element.textContent = "No data returned or an unknown error occurred.";
        }
    }

    // --- Data Loading Functions ---
    async function loadCpuInfo() {
        const data = await fetchData('cpu-info');
        displayData(elements.cpuInfo, data);
        // Also update overview if it's just a summary
        if (Array.isArray(data) && data.length > 0) {
            // Assuming the first entry is representative for the overview
            const core = data[0]; 
            elements.overviewCpu.textContent = `${core.Name || core.model_name || 'Unknown CPU'} (${core.NumberOfCores || 'N/A'} Cores, ${core.NumberOfLogicalProcessors || 'N/A'} Threads)`;
        } else if (data && typeof data === 'object' && !Array.isArray(data) && Object.keys(data).length > 0) { // Handle single CPU object case (already good)
            const core = data;
            elements.overviewCpu.textContent = `${core.Name || core.model_name || 'Unknown CPU'} (${core.NumberOfCores || 'N/A'} Cores, ${core.NumberOfLogicalProcessors || 'N/A'} Threads)`;
        }
         else if (data && data.error) {
            elements.overviewCpu.textContent = `Error: ${data.error}`;
        } else {
            elements.overviewCpu.textContent = "CPU data not available or in unexpected format.";
        }
    }

    async function loadGpuInfo() {
        const data = await fetchData('gpu-info');
        displayData(elements.gpuInfo, data);
        // Update overview with GPU info if available, otherwise default to CPU info already set
        if (Array.isArray(data) && data.length > 0) {
            const gpuSummary = data.map(gpu => `${gpu.name} (Memory: ${gpu.memory_total} MiB, Util: ${gpu.utilization_gpu} %)`).join('\\n');
            // If there's GPU info, prepend it or replace CPU, depending on desired layout.
            // For now, let's assume if GPU exists, it's the primary interest for this slot in overview.
            elements.overviewCpu.textContent = gpuSummary; // Potentially rename overviewCpu to overviewSystemCompute or similar
        } else if (data && data.error) {
            // elements.overviewCpu.textContent += `\\nGPU Error: ${data.error}`; // Append GPU error or handle differently
        }
        // If no GPU data, the CPU info (set by loadCpuInfo) will remain.
    }

    async function loadRamDiskInfo() {
        const data = await fetchData('ram-disk');
        if (data && !data.error) {
            displayData(elements.ramInfo, data.ram);
            displayData(elements.diskInfo, data.disk);
            // Overview update
            if (data.ram && !data.ram.error) {
                elements.overviewRam.textContent = `Total: ${data.ram.total_mb || 'N/A'} MB, Used: ${data.ram.used_mb || 'N/A'} MB, Available: ${data.ram.available_mb || 'N/A'} MB`;
            } else {
                elements.overviewRam.textContent = (data.ram && data.ram.error) || "RAM data not available.";
            }
            if (data.disk && Array.isArray(data.disk)) {
                const diskSummary = data.disk.map(d => 
                    `${d.filesystem || d.mounted_on || d.caption || 'N/A'}: ${d.used_gb || d.used_str || 'N/A'} GB used of ${d.total_gb || d.total_str || 'N/A'} GB (${d.use_percent || d.use_percent_str || 'N/A'})`
                ).join('\n'); // Changed from '\\n' to '\n'
                elements.overviewDisk.textContent = diskSummary || "Disk data not available.";
            } else if (data.disk && data.disk.error) {
                elements.overviewDisk.textContent = data.disk.error;
            } else {
                elements.overviewDisk.textContent = "Disk data not available or in unexpected format.";
            }
        } else {
            const errorMsg = (data && data.error) || "Failed to load RAM/Disk data.";
            elements.ramInfo.textContent = errorMsg;
            elements.diskInfo.textContent = errorMsg;
            elements.overviewRam.textContent = errorMsg;
            elements.overviewDisk.textContent = errorMsg;
        }
    }

    async function loadLxcInfo() { // Renamed from the previous simple version
        await fetchLxcData(); // fetchLxcData updates its own specific section ('lxc-data')
    }

    async function loadLiveStats() {
        elements.liveStatsDisplay.textContent = "Loading live stats...";
        const data = await fetchData('live-stats', false); // false because we expect plain text
        elements.liveStatsDisplay.textContent = data;
    }

    function updateTimestamp() {
        elements.timestamp.textContent = new Date().toLocaleString();
    }

    async function loadAllData() {
        // Show a loading indicator if you have one
        // Clear previous overview data to avoid confusion during refresh
        elements.overviewCpu.textContent = "Loading...";
        elements.overviewRam.textContent = "Loading...";
        elements.overviewDisk.textContent = "Loading...";

        await loadCpuInfo(); // Load CPU info first
        await loadGpuInfo(); // Then load GPU info, which might overwrite the CPU field in overview
        await loadRamDiskInfo();
        await loadLxcInfo(); 
        await loadLiveStats(); // Load live stats
        
        updateTimestamp();
        // Hide loading indicator
    }

    // --- Navigation --- 
    function showSection(sectionName) {
        Object.values(sections).forEach(section => {
            section.style.display = 'none';
        });
        Object.values(navButtons).forEach(button => {
            button.classList.remove('active');
        });

        if (sections[sectionName]) {
            sections[sectionName].style.display = 'block';
        }
        if (navButtons[sectionName]) {
            navButtons[sectionName].classList.add('active');
        }
    }

    navButtons.overview.addEventListener('click', () => showSection('overview'));
    navButtons.cpu.addEventListener('click', () => showSection('cpu'));
    navButtons.gpu.addEventListener('click', () => showSection('gpu'));
    navButtons.ramDisk.addEventListener('click', () => showSection('ramDisk'));
    navButtons.lxc.addEventListener('click', () => showSection('lxc'));
    navButtons.liveStats.addEventListener('click', () => {
        showSection('liveStats');
        loadLiveStats(); // Load live stats when section is shown
    });

    refreshAllButton.addEventListener('click', loadAllData);

    // Initial load
    showSection('overview'); // Show overview by default
    loadAllData(); // This will call the individual loaders including fetchLxcData indirectly or directly based on your setup.
    // fetchLxcData(); // This line might be redundant if loadAllData -> loadLxcInfo -> fetchLxcData path is correctly set up.
                       // Or if loadLxcInfo directly calls the /api/lxc and updates elements.lxcInfo
                       // For clarity, ensure loadLxcInfo is the one that calls displayData(elements.lxcInfo, data);
                       // and fetchLxcData is the one that builds the complex HTML for the LXC section.
                       // Let's adjust: loadLxcInfo will call fetchLxcData.

    // --- LXC Data Fetching ---
    async function fetchLxcData() {
        try {
            const response = await fetch('/api/lxc');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            const lxcSection = document.getElementById('lxc-data');
            if (data.error) {
                lxcSection.innerHTML = `<p>Error fetching LXC data: ${data.error}</p><p>${data.message || ''}</p>`;
                return;
            }
            if (data.message) { // Handle cases like "LXC commands not available on this OS"
                lxcSection.innerHTML = `<p>${data.message}</p>`;
                return;
            }

            let html = '<h2>LXC Container Information</h2>';
            if (data.length === 0) {
                html += '<p>No LXC containers found.</p>';
            } else {
                data.forEach(container => {
                    html += `
                        <div class="container-card">
                            <h3>${container.name} (Status: ${container.status})</h3>
                            <p><strong>Owner:</strong> ${container.user_owner || 'N/A'}</p>
                            <p><strong>IPv4:</strong> ${container.ipv4 && container.ipv4.length > 0 ? container.ipv4.join(', ') : 'N/A'}</p>
                            <p><strong>IPv6:</strong> ${container.ipv6 && container.ipv6.length > 0 ? container.ipv6.join(', ') : 'N/A'}</p>
                            <p><strong>Memory Usage:</strong> ${container.memory_usage_mb} MB</p>
                            <h4>Disk Devices:</h4>
                    `;
                    if (Array.isArray(container.disk_devices)) {
                        if (container.disk_devices.length > 0) {
                            html += '<ul>';
                            container.disk_devices.forEach(disk => {
                                html += `<li>
                                    <strong>${disk.name}</strong> (Path: ${disk.path}, Pool: ${disk.pool})
                                    ${disk.total && disk.used ? `- Usage: ${disk.used} / ${disk.total}` : ' (Usage N/A)'}
                                </li>`;
                            });
                            html += '</ul>';
                        } else {
                            html += '<p>No disk devices found or usage not reported.</p>';
                        }
                    } else {
                         html += `<p>${container.disk_devices}</p>`; // Handles the "No disk devices..." string directly
                    }

                    html += '<h4>GPU Devices:</h4>';
                    if (Array.isArray(container.gpu_devices)) {
                        if (container.gpu_devices.length > 0) {
                            html += '<ul>';
                            container.gpu_devices.forEach(gpu => {
                                html += `<li>
                                    <strong>${gpu.name || 'N/A'}</strong>
                                    ${gpu.vendor ? `(Vendor: ${gpu.vendor}` : ''}
                                    ${gpu.product ? `, Product: ${gpu.product}` : ''}
                                    ${gpu.pci_address ? `, PCI: ${gpu.pci_address}` : ''})
                                </li>`;
                            });
                            html += '</ul>';
                        } else {
                            html += '<p>No GPU devices configured for this container.</p>';
                        }
                    } else {
                        html += `<p>${container.gpu_devices}</p>`; // Handles the "No GPU devices..." string directly
                    }
                    html += '</div>';
                });
            }
            lxcSection.innerHTML = html;
        } catch (error) {
            document.getElementById('lxc-data').innerHTML = `<p>Failed to load LXC data: ${error.message}</p>`;
            console.error('Error fetching LXC data:', error);
        }
    }

    // Adjusting loadLxcInfo to use the detailed fetchLxcData for the LXC section
    async function loadLxcInfo() { // Renamed from the previous simple version
        await fetchLxcData(); // fetchLxcData updates its own specific section ('lxc-data')
    }
});
