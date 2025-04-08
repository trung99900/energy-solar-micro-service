/* UPDATE THESE VALUES TO MATCH YOUR SETUP */

// const PROCESSING_STATS_API_URL = "http://3.99.189.212:8100/stats"
const PROCESSING_STATS_API_URL = "/processing/stats";
const ANALYZER_API_URL = {
    // stats: "http://3.99.189.212:8110/stats",
    stats: "/analyzer/stats",
    // energy_consumption: "http://3.99.189.212:8110/events/energy-consumption",
    energy_consumption: "/analyzer/events/energy-consumption",
    // solar_generation: "http://3.99.189.212:8110/events/solar-generation"
    solar_generation: "/analyzer/events/solar-generation"
}

const CONSISTENCY_CHECKS_API_URL = "/checks";
const CONSISTENCY_UPDATE_API_URL = "/update";

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

// Fetch the latest consistency check results
const fetchConsistencyChecks = () => {
    fetch(CONSISTENCY_CHECKS_API_URL)
        .then(res => {
            if (res.status === 404) {
                throw new Error("No consistency checks have been run yet.");
            }
            return res.json();
        })
        .then(result => {
            console.log("Received consistency check results: ", result);
            updateConsistencyResults(result);
        })
        .catch(error => {
            updateErrorMessages(error.message);
        });
};

// Trigger the consistency check (POST to /update)
const triggerConsistencyCheck = () => {
    fetch(CONSISTENCY_UPDATE_API_URL, { method: "POST" })
        .then(res => res.json())
        .then(result => {
            console.log("Consistency check triggered", result);
            updateLastUpdatedTime();
            fetchConsistencyChecks(); // Reload the results after running the checks
        })
        .catch(error => {
            updateErrorMessages(error.message);
        });
};

// Update consistency results on the page
const updateConsistencyResults = (result) => {
    document.getElementById("last-updated-value").innerText = result.last_updated;

    // Update counts
    document.getElementById("db-stats").innerText = JSON.stringify(result.counts.db, null, 2);
    document.getElementById("queue-stats").innerText = JSON.stringify(result.counts.queue, null, 2);
    document.getElementById("processing-stats").innerText = JSON.stringify(result.counts.processing, null, 2);

    // Update missing events
    document.getElementById("missing-in-db").innerText = JSON.stringify(result.missing_in_db, null, 2);
    document.getElementById("missing-in-queue").innerText = JSON.stringify(result.missing_in_queue, null, 2);
};

// Update the last updated time when consistency checks are triggered
const updateLastUpdatedTime = () => {
    document.getElementById("last-updated-value").innerText = (new Date()).toLocaleString();
};

document.addEventListener('DOMContentLoaded', () => {
    // Initial fetch of stats and consistency results
    fetchConsistencyChecks();
    document.getElementById("trigger-check-btn").addEventListener("click", triggerConsistencyCheck);
});
