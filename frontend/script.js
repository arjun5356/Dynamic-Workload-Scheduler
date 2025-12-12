const API_URL = "http://127.0.0.1:8000";

// State elements
const elTick = document.getElementById("tick-count");
const elCpuGrid = document.getElementById("cpu-grid");
const elActiveList = document.getElementById("active-list");
const elLogContainer = document.getElementById("log-container");

// Inputs
const inpPid = document.getElementById("inp-pid");
const inpArrival = document.getElementById("inp-arrival");
const inpBurst = document.getElementById("inp-burst");
const inpCount = document.getElementById("inp-count");
const selAlgorithm = document.getElementById("algorithm-select");

// Buttons binding
document.getElementById("btn-start").addEventListener("click", startSimulation);
document.getElementById("btn-pause").addEventListener("click", pauseSimulation);
document.getElementById("btn-reset").addEventListener("click", resetSimulation);
document.getElementById("btn-add").addEventListener("click", addProcess);
document.getElementById("btn-generate").addEventListener("click", generateProcesses);

// Poll Timer
let pollInterval = null;
let nextManualPid = 1;

function startPolling() {
    if (pollInterval) clearInterval(pollInterval);
    pollInterval = setInterval(fetchState, 500); // 0.5s poll
}

function stopPolling() {
    if (pollInterval) clearInterval(pollInterval);
    pollInterval = null;
}

// API Calls

async function startSimulation() {
    const algo = selAlgorithm.value;
    try {
        await fetch(`${API_URL}/start`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ selected_algorithm: algo })
        });
        startPolling();
    } catch (e) { console.error(e); }
}

async function pauseSimulation() {
    try {
        await fetch(`${API_URL}/pause`, { method: "POST" });
        // Don't stop polling, we still want to see state even if paused (it just won't change tick)
    } catch (e) { console.error(e); }
}

async function resetSimulation() {
    try {
        await fetch(`${API_URL}/reset`, { method: "POST" });
        // Refresh UI immediately
        fetchState();
    } catch (e) { console.error(e); }
}

async function addProcess() {
    // If user provided a PID, use it. Else generate simple sequential P_Manual_x to avoid collision with backend Px?
    // Or just use "Process X".
    let pid = inpPid.value;
    if (!pid) {
        pid = "P" + nextManualPid++;
    }

    const arrival = parseInt(inpArrival.value) || 0;
    const burst = parseInt(inpBurst.value) || 5;

    try {
        await fetch(`${API_URL}/add_process`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ pid, arrival_time: arrival, burst_time: burst })
        });
        // Clear inputs?
        inpPid.value = "";
    } catch (e) { console.error(e); }
}

async function generateProcesses() {
    const count = parseInt(inpCount.value) || 5;
    try {
        await fetch(`${API_URL}/generate_processes`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ count })
        });
    } catch (e) { console.error(e); }
}

async function fetchState() {
    try {
        const res = await fetch(`${API_URL}/state`);
        const data = await res.json();
        render(data);
    } catch (e) { console.error(e); }
}

// Rendering

function render(data) {
    elTick.textContent = data.tick;

    // Title Update
    const elTitle = document.getElementById("active-processes-title");
    if (data.tick === 0 && !data.running && !data.finished) {
        elTitle.textContent = "Added Processes";
    } else {
        elTitle.textContent = "Remaining Processes";
    }

    // Button State
    const btnStart = document.getElementById("btn-start");
    if (data.finished) {
        btnStart.disabled = true;
    } else {
        btnStart.disabled = false;
    }

    // Execution Summary Logic
    const elSummary = document.getElementById("summary-section");
    const elSummaryContent = document.getElementById("summary-content");
    const elDetails = document.getElementById("details-section");
    const elDetailsBody = document.getElementById("details-body");

    if (data.finished && data.metrics) {
        elSummary.style.display = "block";
        elDetails.style.display = "block";

        const m = data.metrics;
        elSummaryContent.innerHTML = `
            <div><strong>Average Waiting Time:</strong> ${m.avg_waiting_time}</div>
            <div><strong>Average Turnaround Time:</strong> ${m.avg_turnaround_time}</div>
            <div style="margin-top:5px; margin-bottom:5px;">
                <strong>CPU Utilization:</strong><br>
                CPU1: ${m.cpu_utilization[0]}% | CPU2: ${m.cpu_utilization[1]}% | CPU3: ${m.cpu_utilization[2]}% | CPU4: ${m.cpu_utilization[3]}%
            </div>
            <div><strong>Load Balance Variance:</strong> ${m.variance}</div>
        `;

        if (data.completed_details) {
            elDetailsBody.innerHTML = data.completed_details.map(t => `
                <tr>
                    <td>${t.pid}</td>
                    <td>${t.arrival}</td>
                    <td>${t.burst}</td>
                    <td>${t.start}</td>
                    <td>${t.finish}</td>
                    <td>${t.waiting}</td>
                    <td>${t.turnaround}</td>
                </tr>
            `).join("");
        }
    } else {
        elSummary.style.display = "none";
        elDetails.style.display = "none";
    }

    // Render Processors
    elCpuGrid.innerHTML = "";
    data.processors.forEach(cpu => {
        // Queue width calculation (scale factor e.g. 10px per item)
        const qWidth = Math.min(cpu.queue_length * 10, 200); // max 200px

        const card = document.createElement("div");
        card.className = "cpu-card";
        card.innerHTML = `
            <div class="cpu-title">CPU ${cpu.id}</div>
            <div class="cpu-status">${cpu.current ? "Busy" : "Idle"}</div>
            <div class="cpu-current">Current: ${cpu.current || "-"}</div>
            <div class="cpu-work">Work Done: ${cpu.executed_count}</div>
            <div class="cpu-queue-container">
                <div class="cpu-queue-bar" style="width: ${qWidth}px;"></div>
            </div>
            <div class="cpu-queue-text">${cpu.queue_length} in queue</div>
        `;
        elCpuGrid.appendChild(card);
    });

    // Render Active List
    elActiveList.innerHTML = "";
    if (data.finished && data.active_tasks.length === 0) {
        const div = document.createElement("div");
        div.className = "process-item";
        div.style.textAlign = "center";
        div.style.color = "green";
        div.style.fontWeight = "bold";
        div.textContent = "All processes executed successfully.";
        elActiveList.appendChild(div);
    } else {
        data.active_tasks.forEach(task => {
            const div = document.createElement("div");
            div.className = "process-item";
            div.textContent = `${task.pid} • Arr:${task.arrival_time} • Burst:${task.burst_time} • Rem:${task.remaining_time}`;
            elActiveList.appendChild(div);
        });
    }

    // Render Logs (Re-render entire list for simplicity, or just append?)
    // Re-rendering is easier to prevent duplicates without ID tracking. 
    // Optimization: Only update if log length changed.

    // Check if user is near bottom BEFORE updating content
    const isAtBottom = (elLogContainer.scrollHeight - elLogContainer.scrollTop - elLogContainer.clientHeight) < 50;

    elLogContainer.innerHTML = data.log.map(l => `<div class="log-entry">${l}</div>`).join("");

    // Scroll to bottom only if we were already there
    if (isAtBottom) {
        elLogContainer.scrollTop = elLogContainer.scrollHeight;
    }
}

// Initial fetch
fetchState();
startPolling();

