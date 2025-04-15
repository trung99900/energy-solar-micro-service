/* UPDATE THESE VALUES TO MATCH YOUR SETUP */

const PROCESSING_STATS_API_URL = "http://15.156.194.205/processing/stats";
const ANALYZER_API_URL = {
    stats: 'http://15.156.194.205/analyzer/stats',
    energy_consumption: (index) => `http://15.156.194.205/events/energy-consumption?index=${index}`,
    solar_generation: (index) => `http://15.156.194.205/events/solar-generation?index=${index}`,
};

const CONSISTENCY_CHECKS_API_URL = 'http://15.156.194.205/consistency_check/checks';
const CONSISTENCY_UPDATE_API_URL = 'http://15.156.194.205/consistency_check/update';

// Function to generate a random integer for the index parameter  
const generateRandomIndex = (min = 1, max = 100) => Math.floor(Math.random() * (max - min + 1)) + min;

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
    makeReq(PROCESSING_STATS_API_URL, (result) =>
        updateCodeDiv(result, "processing-stats")
    )

    // Fetch and update analyzer stats
    makeReq(ANALYZER_API_URL.stats, (result) =>
        updateCodeDiv(result, "analyzer-stats")
    )

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
    makeReq(CONSISTENCY_CHECK_API_URLS.checks, (result) =>
        updateCodeDiv(result, "consistency-checks")
    )
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
}

document.addEventListener('DOMContentLoaded', setup)

document.getElementById("update").addEventListener("click", () => {
    fetch(CONSISTENCY_UPDATE_API_URL, { method: "POST" })
        .then(response => response.json())
        .then(data => console.log("Update successful:", data))
        .catch(error => console.error("Error updating:", error));
});