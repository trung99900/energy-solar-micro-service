/* UPDATE THESE VALUES TO MATCH YOUR SETUP */  

const PROCESSING_STATS_API_URL = "http://3.96.141.95:8100/stats";  
const ANALYZER_API_URL = {  
    stats: "http://3.96.141.95:8110/stats",  
    energy_consumption: "http://3.96.141.95:8090/events/energy-consumption",  
    solar_generation: "http://3.96.141.95:8090/events/solar-generation",  
};  

// Fetch and process the API responses  
const makeReq = (url, cb) => {  
    fetch(url)  
        .then((res) => {  
            if (!res.ok) {  
                throw new Error(`Failed to fetch ${url}: ${res.statusText}`);  
            }  
            return res.json();  
        })  
        .then((result) => {  
            console.log("Received data: ", result);  
            cb(result);  
        })  
        .catch((error) => {  
            console.error(error.message);  
            updateErrorMessages(error.message);  
        });  
};  

// Update specific code divs with response data  
const updateCodeDiv = (result, elemId) => {  
    const elem = document.getElementById(elemId);  
    if (elem) {  
        elem.innerText = JSON.stringify(result, null, 2);  
    }  
};  

// Fetch all stats and update the page  
const getStats = () => {  
    document.getElementById("last-updated-value").innerText = getLocaleDateStr();  

    makeReq(PROCESSING_STATS_API_URL, (result) =>  
        updateCodeDiv(result, "processing-stats")  
    );  
    makeReq(ANALYZER_API_URL.stats, (result) =>  
        updateCodeDiv(result, "analyzer-stats")  
    );  
    makeReq(ANALYZER_API_URL.energy_consumption, (result) =>  
        updateCodeDiv(result, "event-energy-consumption")  
    );  
    makeReq(ANALYZER_API_URL.solar_generation, (result) =>  
        updateCodeDiv(result, "event-solar-generation")  
    );  
};  

// Display error messages for failed requests  
const updateErrorMessages = (message) => {  
    const id = Date.now();  
    const msg = document.createElement("div");  
    msg.id = `error-${id}`;  
    msg.innerHTML = `<p>Something happened at ${getLocaleDateStr()}!</p><code>${message}</code>`;  
    document.getElementById("messages").style.display = "block";  
    document.getElementById("messages").prepend(msg);  
    setTimeout(() => {  
        const elem = document.getElementById(`error-${id}`);  
        if (elem) {  
            elem.remove();  
        }  
    }, 7000);  
};  

// Get the current date and time for display  
const getLocaleDateStr = () => new Date().toLocaleString();  

// Set up stats fetching on page load  
const setup = () => {  
    getStats();  
    setInterval(() => getStats(), 4000); // Update every 4 seconds  
};  

document.addEventListener("DOMContentLoaded", setup);  