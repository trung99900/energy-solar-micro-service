/* UPDATE THESE VALUES TO MATCH YOUR SETUP */

const PROCESSING_STATS_API_URL = "http://35.182.241.239:8100/stats"
const ANALYZER_API_URL = {
    stats: "http://35.182.241.239:8110/stats",
    energy_consumption: "http://35.182.241.239:8110/events/energy-consumption",
    solar_generation: "http://35.182.241.239:8110/events/solar-generation" 
}

// Function to generate a random integer for the index parameter  
const generateRandomIndex = (min = 1, max = 100) => Math.floor(Math.random() * (max - min + 1)) + min;

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

    // makeReq(ANALYZER_API_URL.energy_consumption, (result) => updateCodeDiv(result, "event-energy-consumption"))
    // makeReq(ANALYZER_API_URL.solar_generation, (result) => updateCodeDiv(result, "event-solar-generation"))
    
    // Generate URLs with dynamic indices for the energy consumption and solar generation  
    const energyConsumptionUrl = `${ANALYZER_API_URL.energy_consumption}?index=${generateRandomIndex()}`;  
    const solarGenerationUrl = `${ANALYZER_API_URL.solar_generation}?index=${generateRandomIndex()}`;  

    makeReq(energyConsumptionUrl, (result) => updateCodeDiv(result, "event-energy-consumption"));  
    makeReq(solarGenerationUrl, (result) => updateCodeDiv(result, "event-solar-generation"));
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
    setInterval(() => getStats(), 3000) // Update every 3 seconds
}

document.addEventListener('DOMContentLoaded', setup)