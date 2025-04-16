from flask import jsonify
import httpx, json, os, logging.config, yaml, connexion, requests
from datetime import datetime, timezone
import time

# Load configuration
with open('config/app_conf_dev.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

# Configure logging
with open('config/log_conf_dev.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

def request(method, url):
    event_data = None
    response = httpx.request(method, url)
    if response.status_code != 200:
        logger.error(f"Request for {url} events failed: {response.status_code}")
    else:
        event_data = json.loads(response.content.decode("utf-8"))
        logger.info(f"Request for {url} was successful")
    return event_data

def update_consistency_check():
    """Perform consistency checks for event counts and IDs across services."""
    start_time = time.time()
    logger.info("Starting consistency check...")

    try:
        # Fetch counts and IDs from services
        processing_stats = request("GET", f"{app_config['processing']['url']}/stats") or {}
        analyzer_stats = request("GET", f"{app_config['analyzer']['url']}/stats") or {}
        analyzer_energy_consumption_ids = request("GET", f"{app_config['analyzer']['url']}/event_ids/energy-consumption") or []
        analyzer_solar_generation_ids = request("GET", f"{app_config['analyzer']['url']}/event_ids/solar-generation") or []
        storage_stats = request("GET", f"{app_config['storage']['url']}/count") or {}
        storage_energy_consumption_ids = request("GET", f"{app_config['storage']['url']}/event_ids/energy-consumption") or []
        storage_solar_generation_ids = request("GET", f"{app_config['storage']['url']}/event_ids/solar-generation") or []

        logger.info("Successfully fetched stats from services.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error during HTTP request to services: {e}")
        return {"message": "Error fetching data from services"}, 500
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON response from services: {e}")
        return {"message": "Error parsing JSON from services"}, 500

    # process counts
    queue_counts = {
        "energy-consumption": analyzer_stats.get("num_energy_consumption", 0),
        "solar-generation": analyzer_stats.get("num_solar_generation", 0)
    }
    processing_count = {
        "energy-consumption": processing_stats.get("num_energy_consumption", 0),
        "solar-generation": processing_stats.get("num_solar_generation", 0)
    }

    # Compare
    analyzer_events_ids = analyzer_energy_consumption_ids + analyzer_solar_generation_ids
    storage_events_ids = storage_energy_consumption_ids + storage_solar_generation_ids
    missing_in_db = [event for event in analyzer_events_ids if event not in storage_events_ids]
    missing_in_queue = [event for event in storage_events_ids if event not in analyzer_events_ids]

    # Save results to JSON file
    last_updated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    results = {
        "last_updated": last_updated,
        "counts": {
            "processing": processing_count,
            "queue": queue_counts,
            "db": storage_stats,
        },
        "missing_in_db": missing_in_db,
        "missing_in_queue": missing_in_queue,
    }

    try:
        # Ensure directory exists BEFORE writing  
        data_file = app_config['datastore']['filename']
        dir_name = os.path.dirname(data_file)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

        with open(data_file, 'w') as f:
            json.dump(results, f, indent=4)
            logger.info("Results successfully saved to datastore.")
    except IOError as e:
        logger.error(f"Error writing to datastore: {e}")
        return {"message": "Error saving results to datastore"}, 500

    processing_time = int((time.time() - start_time) * 1000)
    logger.info(
        f"Consistency check completed | processing_time_ms={processing_time} | missing_in_db={len(missing_in_db)} | missing_in_queue={len(missing_in_queue)}"
    )

    return {"processing_time_ms": processing_time}, 200

def get_checks():
    """Fetch the most recent consistency check results."""
    try:
        with open(app_config['datastore']['filename'], 'r') as f:
            results = json.load(f)
            logger.debug(results)
        return results, 200
    except FileNotFoundError:
        logger.warning("No consistency checks have been run yet.")
        return {"message": "No consistency checks found"}, 404
    except json.JSONDecodeError as e:
        logger.error(f"Error reading JSON from datastore: {e}")
        return {"message": "Error reading results from datastore"}, 500

# Create the Connexion app
app = connexion.FlaskApp(__name__, specification_dir='')
print("Loading API specification...")
app.add_api(
    "consistency_check.yml",
    base_path="/consistency_check",
    strict_validation=True,
    validate_responses=True
)

if __name__ == '__main__':
    app.run(port=8120, host='0.0.0.0')