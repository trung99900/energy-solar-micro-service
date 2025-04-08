from flask import jsonify
import httpx, json, os, logging.config, yaml, connexion
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

# JSON datastore file
RESULT_FILE = app_config['datastore']['filename']

def update_consistency_check():
    """Perform a consistency check and update the results."""
    logger.info("Starting consistency check process")
    start_time = time.time()  # Track the start time for performance measurement

    try:
        # Fetch data from services
        processing_stats = fetch_processing_stats()
        analyzer_stats = fetch_analyzer_stats()
        analyzer_ids = fetch_analyzer_ids()
        storage_stats = fetch_storage_stats()
        storage_ids = fetch_storage_ids()

        # Compare data and determine discrepancies
        results = compare_data_with_ids(processing_stats, analyzer_stats, storage_stats, analyzer_ids, storage_ids)

        # Save results to the JSON datastore
        save_results(results)

        # Calculate processing time
        end_time = time.time()
        processing_time_ms = int((end_time - start_time) * 1000)

        logger.info(
            f"Consistency checks completed | processing_time_ms={processing_time_ms} | "
            f"missing_in_db={len(results['missing_in_db'])} | missing_in_queue={len(results['missing_in_queue'])}"
        )

        return jsonify({"processing_time_ms": processing_time_ms}), 200

    except Exception as e:
        logger.error(f"Error during consistency check: {e}")
        return jsonify({"error": "Internal server error"}), 500

def fetch_processing_stats():
    """Fetch stats from the processing service."""
    processing_url = app_config['processing']['url'] + '/processing/stats'
    response = httpx.get(processing_url)

    if response.status_code != 200:
        raise ValueError("Failed to fetch processing stats")

    logger.info("Fetched processing stats successfully")
    return response.json()

def fetch_analyzer_stats():
    """Fetch stats from the analyzer service."""
    analyzer_url = app_config['analyzer']['url'] + '/analyzer/stats'
    response = httpx.get(analyzer_url)

    if response.status_code != 200:
        raise ValueError("Failed to fetch analyzer stats")

    logger.info("Fetched analyzer stats successfully")
    return response.json()

def fetch_analyzer_ids():
    """Fetch event IDs and trace IDs from the analyzer service."""
    analyzer_ids_url = app_config['analyzer']['url'] + '/analyzer/events/energy-consumption/ids'
    response = httpx.get(analyzer_ids_url)

    if response.status_code != 200:
        raise ValueError("Failed to fetch analyzer event IDs")

    logger.info("Fetched analyzer event IDs successfully")
    return response.json()

def fetch_storage_stats():
    """Fetch stats from the storage service."""
    storage_url = app_config['storage']['url'] + '/storage/stats'
    response = httpx.get(storage_url)

    if response.status_code != 200:
        raise ValueError("Failed to fetch storage stats")

    logger.info("Fetched storage stats successfully")
    return response.json()

def fetch_storage_ids():
    """Fetch event IDs and trace IDs from the storage service."""
    storage_ids_url = app_config['storage']['url'] + '/storage/event-ids/energy-consumption'
    response = httpx.get(storage_ids_url)

    if response.status_code != 200:
        raise ValueError("Failed to fetch storage event IDs")

    logger.info("Fetched storage event IDs successfully")
    return response.json()

def compare_data_with_ids(processing_stats, analyzer_stats, storage_stats, analyzer_ids, storage_ids):
    """Compare data across services and identify missing events."""
    logger.info("Comparing data for consistency...")

    # Extract trace IDs from IDs data
    analyzer_trace_ids = {event["trace_id"] for event in analyzer_ids}
    storage_trace_ids = {event["trace_id"] for event in storage_ids}

    # Identify discrepancies
    missing_in_db = [
        event for event in analyzer_ids if event["trace_id"] not in storage_trace_ids
    ]
    missing_in_queue = [
        event for event in storage_ids if event["trace_id"] not in analyzer_trace_ids
    ]

    # Prepare results
    results = {
        "processing": processing_stats,
        "analyzer": analyzer_stats,
        "storage": storage_stats,
        "missing_in_db": missing_in_db,
        "missing_in_queue": missing_in_queue,
        "last_updated": datetime.utcnow().isoformat()
    }

    logger.info("Data comparison completed successfully")
    return results

def save_results(results):
    """Save the results to the JSON file."""
    with open(RESULT_FILE, 'w') as f:
        json.dump(results, f, indent=4)
    logger.info("Results successfully saved to JSON file")

def get_results():
    """Get the latest consistency check results."""
    logger.info("Fetching results from JSON datastore file")

    if not os.path.exists(RESULT_FILE):
        return jsonify({"error": "No results available"}), 404

    with open(RESULT_FILE, 'r') as f:
        results = json.load(f)

    return jsonify(results), 200

# Add the `/checks` endpoint
def get_checks():
    """Return the result of the latest consistency check."""
    logger.info("Retrieving the latest consistency check result")

    if not os.path.exists(RESULT_FILE):
        logger.warning("No consistency results available yet")
        return jsonify({"error": "No consistency checks have been run yet"}), 404

    try:
        # Read the results from the JSON file
        with open(RESULT_FILE, 'r') as f:
            results = json.load(f)

        return jsonify(results), 200

    except Exception as e:
        logger.error(f"Error reading the consistency results: {e}")
        return jsonify({"error": "Internal server error"}), 500

# Create the Connexion app  
app = connexion.FlaskApp(__name__, specification_dir='')
# app.add_api("openapi.yml", strict_validation=True, validate_responses=True)
app.add_api("openapi.yml", base_path="/analyzer", strict_validation=True, validate_responses=True)

if "CORS_ALLOW_ALL" in os.environ and os.environ["CORS_ALLOW_ALL"] == "yes":
    app.add_middleware(
        CORSMiddleware,
        position=MiddlewarePosition.BEFORE_EXCEPTION,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Add routes to the Flask application
app.add_url_rule('/update', 'update_consistency_check', update_consistency_check, methods=['POST'])
app.add_url_rule('/results', 'get_results', get_results, methods=['GET'])
app.add_url_rule('/checks', 'get_checks', get_checks, methods=['GET'])

if __name__ == '__main__':
    app.run(port=8120, host='0.0.0.0')
    