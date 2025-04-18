/* UPDATE THESE VALUES TO MATCH YOUR SETUP */
const VM_IP = window.ENV.VM_IP;
const PROCESSING_STATS_API_URL = `http://${VM_IP}/processing/stats`;
const CONSISTENCY_CHECK_API_URL = `http://${VM_IP}/consistency_check/checks`;
const CONSISTENCY_UPDATE_API_URL = `http://${VM_IP}/consistency_check/update`;

// Function to generate a random integer for the index parameter
const generateRandomIndex = () => Math.floor(Math.random() * 10);

const ANALYZER_API_URL = {
    stats: `http://${VM_IP}/analyzer/stats`,
    energy_consumption: (index) => `http://${VM_IP}/analyzer/events/energy-consumption?index=${index}`,
    solar_generation: (index) => `http://${VM_IP}/analyzer/events/solar-generation?index=${index}`,
};

const ANOMALY_API_URL = {
    energy_consumption: `http://${VM_IP}/anomaly_detector/anomalies?event_type=energy-consumption`,  
    solar_generation: `http://${VM_IP}/anomaly_detector/anomalies?event_type=solar-generation`,
}

// Helper function to make HTTP requests
const makeReq = (url, cb) => {
    fetch(url)
        .then(res => res.json())
        .then((result) => {
            console.log("Received data: ", result)
            cb(result);
        }).catch((error) => {
            updateErrorMessages(error.message)
        })
}

// Helper function to update content dynamically
const updateCodeDiv = (result, elemId) => document.getElementById(elemId).innerText = JSON.stringify(result)

// Helper function to get the current time in locale string format
const getLocaleDateStr = () => (new Date()).toLocaleString()

// Fetch and display general statistics
const getStats = () => {
    document.getElementById("last-updated-value").innerText = getLocaleDateStr()

    // Fetch and update processing stats
    makeReq(PROCESSING_STATS_API_URL, (result) => updateCodeDiv(result, "processing-stats"))

    // Fetch and update analyzer stats
    makeReq(ANALYZER_API_URL.stats, (result) => updateCodeDiv(result, "analyzer-stats"))

    // Fetch and update energy consumption event data by a random index
    const energyIndex = generateRandomIndex();
    makeReq(ANALYZER_API_URL.energy_consumption(energyIndex), (result) =>
        updateCodeDiv(result, "event-energy-consumption")
    )

    // Fetch and update solar generation event data by a random index
    const solarIndex = generateRandomIndex();
    makeReq(ANALYZER_API_URL.solar_generation(solarIndex), (result) =>
        updateCodeDiv(result, "event-solar-generation")
    )

    // Fetch and update consistency checks results
    makeReq(CONSISTENCY_CHECK_API_URL, (result) =>
        updateCodeDiv(result, "consistency-check")
    );

    // Add this line for anomaly fetching
    fetchAndDisplayAnomalies();
}

const updateErrorMessages = (message) => {
    const id = Date.now()
    console.log("Creation", id)
    msg = document.createElement("div")
    msg.id = `error-${id}`
    msg.innerHTML = `<p>Something happened at ${getLocaleDateStr()}!</p><code>${message}</code>`
    document.getElementById("messages").style.display = "block"
    document.getElementById("messages").prepend(msg)
    setTimeout(() => {
        const elem = document.getElementById(`error-${id}`)
        if (elem) { elem.remove() }
    }, 7000)
}

const setup = () => {
    getStats()
    setInterval(() => getStats(), 4000) // Update every 4 seconds

    const updateBtn = document.getElementById("update")
    if (updateBtn) {
        updateBtn.addEventListener("click", () => {
            fetch(CONSISTENCY_UPDATE_API_URL, { method: "POST" })
                .then(response => response.json())
                .then(data => console.log("Update successful:", data))
                .catch(error => console.error("Error updating:", error));
        });
    }
}

function fetchAndDisplayAnomalies() {
    fetchAnomalyList(ANOMALY_API_URL.energy_consumption, 'anomaly-energy-consumption');
    fetchAnomalyList(ANOMALY_API_URL.solar_generation, 'anomaly-solar-generation');
}

function fetchAnomalyList(url, elementId) {
    fetch(url)
        .then((response) => {
            if (response.status === 204) return []; // No anomalies
            if (!response.ok) throw new Error(`API error: ${response.status}`);
            return response.json();
        })
        .then((data) => {
            renderAnomalyList(data, elementId);
        })
        .catch((err) => {
            document.getElementById(elementId).innerHTML = `<li>Error loading anomalies</li>`;
            updateErrorMessages("Anomaly fetch: " + err.message);
        });
}

function renderAnomalyList(list, elementId) {
    const ul = document.getElementById(elementId);
    ul.innerHTML = '';
    if (!list || list.length === 0) {
        ul.innerHTML = '<li>None</li>';
        return;
    }
    for (const item of list) {
        // Highlight "Too High" and "Too Low" with appropriate CSS classes
        const anomalyClass = item.anomaly_type === "Too High"
            ? "anomaly-high"
            : (item.anomaly_type === "Too Low" ? "anomaly-low" : "");
        const li = document.createElement('li');
        li.innerHTML = `
            <b><span class="${anomalyClass}">${item.description}</span></b><br>
            <span>Event ID: ${item.event_id}</span><br>
            <span>Trace ID: ${item.trace_id}</span>
        `;
        ul.appendChild(li);
    }
}


document.addEventListener('DOMContentLoaded', setup)

// document.getElementById("update").addEventListener("click", () => {
//     fetch(CONSISTENCY_UPDATE_API_URL, { method: "POST" })
//         .then(response => response.json())
//         .then(data => console.log("Update successful:", data))
//         .catch(error => console.error("Error updating:", error));
// });