import connexion, yaml, logging, logging.config, json, httpx, uuid  
from connexion import NoContent 
from datetime import datetime
from pykafka import KafkaClient

# MAX_EVENTS = 5  
# EVENT_FILE = "events.json"

with open('config/app_conf_dev.yml', 'r') as f:  
    app_config = yaml.safe_load(f.read())

with open('config/log_conf_dev.yml', 'r') as f:  
    log_config = yaml.safe_load(f.read())  
    logging.config.dictConfig(log_config)  
    
logger = logging.getLogger('basicLogger') 

def receive_energy_consumption_event(body):  
    # Generate trace_id and uuid for the event
    body["trace_id"] = str(uuid.uuid4())
    body["uuid"] = str(uuid.uuid4())
    # uses the configuration values to connect to Kafka and select the “events” topic
    client = KafkaClient(hosts=f"{app_config['kafka']['events']['hostname']}:{app_config['kafka']['events']['port']}")
    topic = client.topics[str.encode(app_config['kafka']['events']['topic'])]
    producer = topic.get_sync_producer()
    # JSON message
    msg = {
            "type": "energy-consumption",
            "datetime": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "payload": body
    }
    # The event is serialized to JSON and encoded as UTF-8 before being sent. A log statement is recorded 
    msg_str = json.dumps(msg)
    producer.produce(msg_str.encode('utf-8'))
    logger.info(f"Produced energy-consumption event with trace_id {body['trace_id']}")
    return NoContent, 201 # returns and HTTP 201 response 

def receive_solar_generation_event(body):  
    # Generate trace_id and uuid for the event
    body["trace_id"] = str(uuid.uuid4())
    body["uuid"] = str(uuid.uuid4())
    
    client = KafkaClient(hosts=f"{app_config['kafka']['events']['hostname']}:{app_config['kafka']['events']['port']}")
    topic = client.topics[str.encode(app_config['kafka']['events']['topic'])]
    producer = topic.get_sync_producer()
    msg = {
            "type": "solar-generation",
            "datetime": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "payload": body
    }
    msg_str = json.dumps(msg)
    producer.produce(msg_str.encode('utf-8'))
    logger.info(f"Produced solar-generation event with trace_id {body['trace_id']}")
    return NoContent, 201
   
# Create the Connexion app  
app = connexion.FlaskApp(__name__, specification_dir='')  
# app.add_api("openapi.yml", strict_validation=True, validate_responses=True)
app.add_api("openapi.yml", base_path="/receiver", strict_validation=True, validate_responses=True)

if __name__ == "__main__":  
    app.run(port=8080, host="0.0.0.0")