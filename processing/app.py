from flask import Flask, jsonify  
from apscheduler.schedulers.background import BackgroundScheduler  
import requests, json, logging.config, yaml, os, connexion, httpx  
from datetime import datetime

# from connexion.middleware import MiddlewarePosition
# from starlette.middleware.cors import CORSMiddleware


# Load configuration  
with open('config/app_conf_dev.yml', 'r') as f:  
    app_config = yaml.safe_load(f)  

# Logging setup  
with open('config/log_conf_dev.yml', 'r') as f:  
    log_config = yaml.safe_load(f.read())  
    logging.config.dictConfig(log_config)  

logger = logging.getLogger('basicLogger')  

# Initialize statistics  
stats_file = app_config['datastore']['filename']  

# Scheduler interval  
scheduler_interval = app_config['scheduler']['interval']  

# Eventstore URLs  
energy_consumption_url = app_config['eventstores']['energy_consumption']['url']  
solar_generation_url = app_config['eventstores']['solar_generation']['url']  

def load_stats():  
    """Load statistics from the JSON file."""  
    if not os.path.exists(stats_file):  
        return {  
            "num_energy_events": 0,  
            "max_energy_consumed": 0,  
            "num_solar_events": 0,  
            "max_power_generated": 0,  
            "last_updated": "1970-01-01T00:00:00Z"
        }  
    with open(stats_file, 'r') as f:  
        return json.load(f)  

def save_stats(stats):  
    """Save statistics to the JSON file."""  
    with open(stats_file, 'w') as f:  
        json.dump(stats, f, indent=4)  

from datetime import datetime, timezone  

def populate_stats():  
    logger.info("Processing started")  

    # Load existing stats  
    try:  
        stats = load_stats()  
    except Exception as e:  
        logger.error("Failed to load statistics: %s", str(e))  
        stats = {  
            "num_energy_events": 0,  
            "max_energy_consumed": 0,  
            "num_solar_events": 0,  
            "max_power_generated": 0,  
            "last_updated": "1970-01-01T00:00:00Z"  
        }  

    # Construct default timestamps  
    last_updated = stats.get('last_updated')
    end_timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")  

    logger.info(f"Fetching events from {last_updated} to {end_timestamp}")  

    # Process energy consumption and solar generation events  
    for event, url_key in [("energy", "energy_consumption"), ("solar", "solar_generation")]:  
        try:  
            response = httpx.get(app_config['eventstores'][url_key]['url'], params={  
                "start_timestamp": last_updated,  
                "end_timestamp": end_timestamp  
            })  

            if response.status_code != 200:  
                logger.error(f"Failed to fetch {event} events: Status {response.status_code}")  
                continue  

            events = response.json()  
            logger.info(f"Received {len(events)} {event} events")  

            if event == "energy":  
                # Increment the number of energy events  
                stats['num_energy_events'] += len(events)  

                # Update the maximum energy consumed  
                max_energy = max([e['energy_consumed'] for e in events], default=0)  
                stats['max_energy_consumed'] = max(stats['max_energy_consumed'], max_energy)  

            elif event == "solar":  
                # Increment the number of solar events  
                stats['num_solar_events'] += len(events)  

                # Update the maximum power generated  
                max_power = max([s['power_generated'] for s in events], default=0)  
                stats['max_power_generated'] = max(stats['max_power_generated'], max_power)  

        except Exception as e:  
            logger.error(f"Error processing {event} events: {str(e)}")  
            continue  

    # Update last_updated timestamp and save stats  
    stats['last_updated'] = end_timestamp  
    try:  
        save_stats(stats)  # Save the updated stats  
        logger.info("Statistics updated successfully")  
    except Exception as e:  
        logger.error("Failed to save statistics: %s", str(e))  

    logger.info("Processing completed")  

def get_stats():  
    logger.info("Fetching statistics")  
    stats = load_stats()  
    if not stats:  
        logger.error("Statistics do not exist")  
        return jsonify({"error": "No statistics available"}), 404  
    logger.debug("Statistics fetched: %s", stats)  
    logger.info("Statistics fetched")  
    return jsonify(stats), 200  

def init_scheduler():  
    sched = BackgroundScheduler(daemon=True)  
    sched.add_job(populate_stats, 'interval', seconds=app_config['scheduler']['interval'])  
    sched.start()  

# Create the Connexion app  
app = connexion.FlaskApp(__name__, specification_dir='')  
app.add_api("stats.yml", strict_validation=True, validate_responses=True)  

# app.add_middleware(
# CORSMiddleware,
# position=MiddlewarePosition.BEFORE_EXCEPTION,
# allow_origins=["*"],
# allow_credentials=True,
# allow_methods=["*"],
# allow_headers=["*"],
# )
if __name__ == "__main__":  
    init_scheduler()  
    app.run(port=8100, host="0.0.0.0")