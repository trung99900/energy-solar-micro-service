/* UPDATE THESE VALUES TO MATCH YOUR SETUP */

// const PROCESSING_STATS_API_URL = "http://3.99.189.212:8100/stats"
const PROCESSING_STATS_API_URL = "http://35.182.156.12/processing/stats";

// Function to generate a random integer for the index parameter  
const generateRandomIndex = (min = 1, max = 100) => Math.floor(Math.random() * (max - min + 1)) + min;

const ANALYZER_API_URL = {
    // stats: "http://3.99.189.212:8110/stats",
    stats: 'http://35.182.156.12/analyzer/stats',
    // energy_consumption: "http://3.99.189.212:8110/events/energy-consumption",
    energy_consumption: 'http://35.182.156.12/analyzer/events/energy-consumption?index=${generateRandomIndex()}',
    // solar_generation: "http://3.99.189.212:8110/events/solar-generation"
    solar_generation: 'http://35.182.156.12/analyzer/events/solar-generation=index=${generateRandomIndex()}'
}

const CONSISTENCY_CHECKS_API_URL = 'http://35.182.156.12/consistency_check/checks';
const CONSISTENCY_UPDATE_API_URL = 'http://35.182.156.12/consistency_check/update';

// This function fetches and updates the general statistics
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

const updateCodeDiv = (result, elemId) => document.getElementById(elemId).innerText = JSON.stringify(result)

const getLocaleDateStr = () => (new Date()).toLocaleString()

const getStats = () => {
    document.getElementById("last-updated-value").innerText = getLocaleDateStr()
    
    makeReq(PROCESSING_STATS_API_URL, (result) => updateCodeDiv(result, "processing-stats"))
    makeReq(ANALYZER_API_URL.stats, (result) => updateCodeDiv(result, "analyzer-stats"))
    makeReq(ANALYZER_API_URL.energy_consumption, (result) => updateCodeDiv(result, "event-energy-consumption"))
    makeReq(ANALYZER_API_URL.solar_generation, (result) => updateCodeDiv(result, "event-solar-generation"))    
    makeReq(CONSISTENCY_CHECKS_API_URL, (result) => updateCodeDiv(result, "consistency-checks"))
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