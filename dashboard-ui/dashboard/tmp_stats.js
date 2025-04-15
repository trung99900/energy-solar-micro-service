/* UPDATE THESE VALUES TO MATCH YOUR SETUP */  
const PROCESSING_STATS_API_URL = "http://15.223.197.74:8100/stats";  
const ANALYZER_API_URL = {  
  stats: "http://15.223.197.74:8110/stats",  
  energy_consumption: "http://15.223.197.74:8110/events/energy-consumption",  
  solar_generation: "http://15.223.197.74:8110/events/solar-generation",  
};  

// Function to generate a random integer for the index parameter  
const generateRandomIndex = (min = 1, max = 100) =>  
  Math.floor(Math.random() * (max - min + 1)) + min;  

// Function to make API requests and handle responses  
const makeReq = (url, cb) => {  
  fetch(url)  
    .then((res) => res.json())  
    .then((result) => {  
      console.log("Received data: ", result);  
      cb(result);  
    })  
    .catch((error) => {  
      updateErrorMessages(error.message);  
    });  
};  

// Update the content of a code block if the element exists  
const updateCodeDiv = (result, elemId) => {  
  const element = document.getElementById(elemId);  
  if (element) {  
    element.innerText = JSON.stringify(result, null, 2); // Beautify JSON for readability  
  } else {  
    console.warn(`Element with ID "${elemId}" not found.`);  
  }  
};  

// Get the current date and time as a string  
const getLocaleDateStr = () => new Date().toLocaleString();  

// Fetch and update the statistics  
const getStats = () => {  
  const lastUpdatedElement = document.getElementById("last-updated-value");  

  // Update the last-updated timestamp  
  if (lastUpdatedElement) {  
    lastUpdatedElement.innerText = getLocaleDateStr();  
  } else {  
    console.warn('Element with ID "last-updated-value" not found.');  
  }  

  // Fetch and update processing stats  
  makeReq(PROCESSING_STATS_API_URL, (result) =>  
    updateCodeDiv(result, "processing-stats")  
  );  

  // Fetch and update analyzer stats  
  makeReq(ANALYZER_API_URL.stats, (result) =>  
    updateCodeDiv(result, "analyzer-stats")  
  );  

  // Dynamically generate URLs for energy consumption and solar generation  
  const energyConsumptionUrl = `${ANALYZER_API_URL.energy_consumption}?index=${generateRandomIndex()}`;  
  const solarGenerationUrl = `${ANALYZER_API_URL.solar_generation}?index=${generateRandomIndex()}`;  

  // Fetch and update energy consumption event  
  makeReq(energyConsumptionUrl, (result) =>  
    updateCodeDiv(result, "event-energy-consumption")  
  );  

  // Fetch and update solar generation event  
  makeReq(solarGenerationUrl, (result) =>  
    updateCodeDiv(result, "event-solar-generation")  
  );  
};  

// Handle and display error messages  
const updateErrorMessages = (message) => {  
  const id = Date.now();  
  const messagesContainer = document.getElementById("messages");  

  if (messagesContainer) {  
    console.log("Creation", id);  
    const msg = document.createElement("div");  
    msg.id = `error-${id}`;  
    msg.innerHTML = `  
      <p>Something happened at ${getLocaleDateStr()}!</p>  
      <code>${message}</code>  
    `;  
    messagesContainer.style.display = "block";  
    messagesContainer.prepend(msg);  

    // Automatically remove error message after 7 seconds  
    setTimeout(() => {  
      const elem = document.getElementById(`error-${id}`);  
      if (elem) {  
        elem.remove();  
      }  
    }, 7000);  
  } else {  
    console.warn('Element with ID "messages" not found.');  
  }  
};  

// Initial setup function  
const setup = () => {  
  getStats();  
  setInterval(() => getStats(), 3000); // Update stats every 3 seconds  
};  

// Run the setup function after DOM content is fully loaded  
document.addEventListener("DOMContentLoaded", setup);