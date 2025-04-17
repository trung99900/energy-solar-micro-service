import os
import logging.config
import yaml
import json
import time
from flask import Flask, request, jsonify
import connexion
from kafka import KafkaConsumer

with open('config/app_conf_dev.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

with open('config/log_conf_dev.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)
logger = logging.getLogger('basicLogger')

# --- Read threshold env vars (with defaults for dev) ---
ENERGY_CONSUMPTION_MAX = int(os.environ.get('ENERGY_CONSUMPTION_MAX', 10000))
SOLAR_GENERATION_MIN = int(os.environ.get('SOLAR_GENERATION_MIN', 10))
logger.info(f"Anomaly thresholds: ENERGY_CONSUMPTION_MAX={ENERGY_CONSUMPTION_MAX}, SOLAR_GENERATION_MIN={SOLAR_GENERATION_MIN}")

KAFKA_HOST = app_config['kafka']['events']['hostname']
KAFKA_PORT = app_config['kafka']['events']['port']
KAFKA_TOPIC = app_config['kafka']['events']['topic']
DATASTORE_FILE = app_config['datastore']['filename']

EVENT_TYPES = {"energy_consumption", "solar_generation"}

def find_anomalies():
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=f"{KAFKA_HOST}:{KAFKA_PORT}",
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='earliest',
        consumer_timeout_ms=2000
    )
    anomalies = []
    record_id = 1
    for msg in consumer:
        data = msg.value
        evtype = data.get('event_type')
        if evtype == "energy_consumption":
            val = data.get('consumption')
            if val is not None and val > ENERGY_CONSUMPTION_MAX:
                anomaly = {
                    "event_id": data.get("event_id"),
                    "trace_id": data.get("trace_id"),
                    "event_type": "energy_consumption",
                    "anomaly_type": "Too High",
                    "description": f"Detected: {val}; too high (threshold {ENERGY_CONSUMPTION_MAX})"
                }
                anomalies.append(anomaly)
                logger.debug(f"Anomaly detected: {anomaly}")
                record_id += 1
        elif evtype == "solar_generation":
            val = data.get('generation')
            if val is not None and val < SOLAR_GENERATION_MIN:
                anomaly = {
                    "event_id": data.get("event_id"),
                    "trace_id": data.get("trace_id"),
                    "event_type": "solar_generation",
                    "anomaly_type": "Too Low",
                    "description": f"Detected: {val}; too low (threshold {SOLAR_GENERATION_MIN})"
                }
                anomalies.append(anomaly)
                logger.debug(f"Anomaly detected: {anomaly}")
                record_id += 1
    consumer.close()
    return anomalies

def update_anomalies():
    logger.debug("PUT /update called")
    start = time.time()
    anomalies = find_anomalies()
    try:
        os.makedirs(os.path.dirname(DATASTORE_FILE), exist_ok=True)
        with open(DATASTORE_FILE, 'w') as f:
            json.dump(anomalies, f, indent=2)
        elapsed_ms = int((time.time() - start) * 1000)
        logger.info(f"{len(anomalies)} anomalies found and written to datastore in {elapsed_ms}ms")
    except Exception as e:
        logger.error(f"Error saving anomalies: {e}")
        return jsonify({"message": "Error saving anomalies"}), 500
    return jsonify({"anomalies_count": len(anomalies)}), 201

def get_anomalies(event_type=None):
    logger.debug(f"GET /anomalies received (event_type={event_type})")
    start = time.time()
    try:
        with open(DATASTORE_FILE, 'r') as f:
            anomalies = json.load(f)
    except FileNotFoundError:
        logger.error("Datastore missing")
        return jsonify({"message": "Anomaly datastore not found"}), 404
    except Exception as e:
        logger.error(f"Datastore error: {e}")
        return jsonify({"message": "Datastore is corrupted"}), 404

    # Filter by event_type if provided
    if event_type:
        if event_type not in EVENT_TYPES:
            return jsonify({"message": "Invalid Event Type, must be energy_consumption or solar_generation"}), 400
        filtered = [a for a in anomalies if a['event_type'] == event_type]
    else:
        filtered = anomalies

    elapsed_ms = int((time.time() - start) * 1000)
    logger.info(f"Anomalies retrieved in {elapsed_ms}ms")
    logger.debug(f"GET /anomalies returned {len(filtered)} records")
    if not filtered:
        return '', 204
    return jsonify(filtered), 200

app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api('anomaly.yml', base_path="/anomaly_detector", strict_validation=True, validate_responses=True)
if __name__ == "__main__":
    app.run(port=8130, host='0.0.0.0')