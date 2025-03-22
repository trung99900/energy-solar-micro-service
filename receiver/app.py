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

# def receiveEnergyConsumptionEvent(body):  
#     log_event("energy", body)  
#     return NoContent, 201  

# def receiveSolarGenerationEvent(body):  
#     log_event("solar", body)  
#     return NoContent, 201  

def receiveEnergyConsumptionEvent(body):  
    # Generate trace_id and uuid for the event
    body["trace_id"] = str(uuid.uuid4())
    body["uuid"] = str(uuid.uuid4())
    # uses the configuration values to connect to Kafka and select the “events” topic
    client = KafkaClient(hosts=f"{app_config['events']['hostname']}:{app_config['events']['port']}")
    topic = client.topics[str.encode(app_config['events']['topic'])]
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

def receiveSolarGenerationEvent(body):  
    # Generate trace_id and uuid for the event
    body["trace_id"] = str(uuid.uuid4())
    body["uuid"] = str(uuid.uuid4())
    
    client = KafkaClient(hosts=f"{app_config['events']['hostname']}:{app_config['events']['port']}")
    topic = client.topics[str.encode(app_config['events']['topic'])]
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

# STORAGE_SERVICE_URL = "http://localhost:8090"

# def receiveEnergyConsumptionEvent(body):  
#     """Forward energy consumption data to the storage service"""  
#     body["trace_id"] = str(uuid.uuid4())
#     #Loging when an event is received
#     logger.info(f"Received event Energy Consumption with a trace id of {body['trace_id']}")
#     response = httpx.post(app_config['events']['energy-consumption']['url'], json=body)  
#     #Loging the responde of storage service
#     logger.info(f"Received event Energy Consumption with a trace id of {body['trace_id']} has status code {response.status_code}")
    
#     return NoContent, response.status_code  

# def receiveSolarGenerationEvent(body):  
#     """Forward solar generation data to the storage service"""
    
#     body["trace_id"] = str(uuid.uuid4())
#     #Loging when an event is received
#     logger.info(f"Received event Solar Generation report with a trace id of {body['trace_id']}")
#     response = httpx.post(app_config['events']['solar-generation']['url'], json=body)
#     #Loging the responde of storage service
#     logger.info(f"Received event Solar Generation report with a trace id of {body['trace_id']} has status code {response.status_code}")
#     return NoContent, response.status_code

# def log_event(event_type, event_data):  
#     try:  
#         # Read the existing data from the file  
#         with open(EVENT_FILE, "r") as file:  
#             data = json.load(file)  
#     except (FileNotFoundError, json.JSONDecodeError):  
#         # Initialize the file if it doesn't exist or is invalid  
#         data = {"num_energy": 0, "recent_energy": [], "num_solar": 0, "recent_solar": []}  

#     # Update the counts and recent events  
#     timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")  
#     event_entry = {  
#         "msg_data": f"Device {event_data['device_id']} reported {event_type} data.",  
#         "received_timestamp": timestamp  
#     }  

#     if event_type == "energy":  
#         data["num_energy"] += 1  
#         data["recent_energy"].insert(0, event_entry)  
#         if len(data["recent_energy"]) > MAX_EVENTS:  
#             data["recent_energy"].pop()  
#     elif event_type == "solar":  
#         data["num_solar"] += 1  
#         data["recent_solar"].insert(0, event_entry)  
#         if len(data["recent_solar"]) > MAX_EVENTS:  
#             data["recent_solar"].pop()  

#     # Write the updated data back to the file  
#     with open(EVENT_FILE, "w") as file:  
#         json.dump(data, file, indent=4)

   
# Create the Connexion app  
app = connexion.FlaskApp(__name__, specification_dir='')  
app.add_api("openapi.yml", strict_validation=True, validate_responses=True)  

if __name__ == "__main__":  
    app.run(port=8080, host="0.0.0.0")