from flask import jsonify
import httpx, json, os, logging.config, yaml, connexion, requests
from datetime import datetime
import time

from connexion.middleware import MiddlewarePosition
from starlette.middleware.cors import CORSMiddleware

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
        processing_stats = requests("GET", f"{app_config['processing']['url']}/stats")
        analyzer_stats = requests("GET", f"{app_config['analyzer']['url']}/stats")
        analyzer_ids = requests("GET", f"{app_config['analyzer']['url']}/events/ids").json()
        storage_stats = requests.get(f"{app_config['storage']['url']}/events/count").json()
        storage_ids = requests.get(f"{app_config['storage']['url']}/events/ids").json()
        logger.info("Successfully fetched stats from services.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error during HTTP request to services: {e}")
        return {"message": "Error fetching data from services"}, 500
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON response from services: {e}")
        return {"message": "Error parsing JSON from services"}, 500

    # Compare IDs
    missing_in_db = [event for event in analyzer_ids if event not in storage_ids]
    missing_in_queue = [event for event in storage_ids if event not in analyzer_ids]

    # Save results to JSON file
    results = {
        "last_updated": datetime.utcnow().isoformat(),
        "counts": {
            "processing": processing_stats,
            "analyzer": analyzer_stats,
            "storage": storage_stats,
        },
        "missing_in_db": missing_in_db,
        "missing_in_queue": missing_in_queue,
    }

    try:
        with open(app_config['datastore']['filename'], 'w') as f:
            json.dump(results, f)
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

# Add CORS middleware if needed
if os.getenv("CORS_ALLOW_ALL", "no").lower() == "yes":
    app.add_middleware(
        CORSMiddleware,
        position=MiddlewarePosition.BEFORE_EXCEPTION,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

if __name__ == '__main__':
    app.run(port=8120, host='0.0.0.0')