const fetchStats = async () => {  
    try {  
        const response = await fetch('http://35.182.227.248:8100/stats');  
        const data = await response.json();  
        document.getElementById('stats').innerText = JSON.stringify(data);  

        // Extract last updated time  
        const lastUpdated = new Date(data.last_updated);  
        document.getElementById('lastUpdated').innerText = lastUpdated.toLocaleString();  
    } catch (err) {  
        console.error("Error fetching stats:", err);  
    }  
};  

const fetchEvent = async () => {  
    try {  
        const response = await fetch('http://<CLOUD_VM_IP>:8110/event');  
        const data = await response.json();  
        document.getElementById('event').innerText = JSON.stringify(data);  
    } catch (err) {  
        console.error("Error fetching event:", err);  
    }  
};  

// Update every 2-4 seconds  
setInterval(() => {  
    fetchStats();  
    fetchEvent();  
}, 3000);