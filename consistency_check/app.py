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

def run_consistency_check():
    start_time = time.time()
    logger.info("Starting consistency check...")

    # Fetch counts and IDs from services
    try:
        processing_stats = requests.get(app_config['processing']['url'] + '/stats').json()
        analyzer_stats = requests.get(app_config['analyzer']['url'] + '/stats').json()
        storage_stats = requests.get(app_config['storage']['url'] + '/stats').json()

        analyzer_ids = requests.get(app_config['analyzer']['url'] + '/ids').json()
        storage_ids = requests.get(app_config['storage']['url'] + '/ids').json()
    except Exception as e:
        logger.error(f"Error fetching data from services: {e}")
        return {"message": "Error fetching data from services"}, 500

    # Compare IDs
    missing_in_db = [event for event in analyzer_ids if event not in storage_ids]
    missing_in_queue = [event for event in storage_ids if event not in analyzer_ids]

    # Save results to JSON file
    results = {
        "last_updated": datetime.utcnow().isoformat(),
        "counts": {
            "processing": processing_stats,
            "analyzer": analyzer_stats,
            "storage": storage_stats
        },
        "missing_in_db": missing_in_db,
        "missing_in_queue": missing_in_queue
    }

    with open(app_config['datastore']['filename'], 'w') as f:
        json.dump(results, f)

    processing_time = int((time.time() - start_time) * 1000)
    logger.info(f"Consistency check completed | processing_time_ms={processing_time} | "
                f"missing_in_db={len(missing_in_db)} | missing_in_queue={len(missing_in_queue)}")

    return {"processing_time_ms": processing_time}, 200

def get_consistency_results():
    try:
        with open(app_config['datastore']['filename'], 'r') as f:
            results = json.load(f)
        return results, 200
    except FileNotFoundError:
        return {"message": "No consistency check results found"}, 404

# Create the Connexion app  
app = connexion.FlaskApp(__name__, specification_dir='')
print("Loading API specification...")
app.add_api("consistency_check.yml", base_path="/consistency_check", strict_validation=True, validate_responses=True)

if "CORS_ALLOW_ALL" in os.environ and os.environ["CORS_ALLOW_ALL"] == "yes":
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
    