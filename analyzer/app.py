import connexion, yaml, logging, logging.config, json, os 
from flask import jsonify  
from pykafka import KafkaClient
# from sqlalchemy import create_engine, select

from connexion.middleware import MiddlewarePosition
from starlette.middleware.cors import CORSMiddleware


# Load the configuration from app_conf.yml  
with open('config/app_conf_dev.yml', 'r') as f:  
    app_config = yaml.safe_load(f.read())  

# Configure logging  
with open('config/log_conf_dev.yml', 'r') as f:  
    log_config = yaml.safe_load(f.read())  
    logging.config.dictConfig(log_config)  

logger = logging.getLogger('basicLogger')  

def getEnergyConsumptionEvent(index):  
    """  
    Endpoint to retrieve an event of type 'EnergyConsumption'.  
    """  
    return get_event("energy-consumption", index)  

def getSolarGenerationEvent(index):  
    """  
    Endpoint to retrieve an event of type 'SolarGeneration'.  
    """  
    return get_event("solar-generation", index)

def get_event(event_type, index):  
    """  
    Retrieve a specific event from the Kafka queue based on the index and event type. 
     
    """
    try:  
        client = KafkaClient(hosts=f"{app_config['events']['hostname']}:{app_config['events']['port']}")
        topic = client.topics[app_config["events"]["topic"].encode()]  
        consumer = topic.get_simple_consumer(reset_offset_on_start=True, consumer_timeout_ms=1000)  
        counter = 0  
        for msg in consumer:  
            if msg is None:  
                break  

            message = msg.value.decode("utf-8")  
            data = json.loads(message) 

            # Filter events by type and match the requested index  
            if data["type"] == event_type:  
                if counter == index:  
                    logger.info(data["payload"])
                    return jsonify(data["payload"]), 200  
                counter += 1  

        # If the index is not found  
        return {"message": f"No message at index {index} for {event_type}!"}, 404  

    except Exception as e:  
        logger.error(f"Error retrieving event: {e}")  
        return {"message": "Internal server error"}, 500    

def getEventStats():  
    """  
    Retrieve statistics about the events in the Kafka queue.  
    """  
    logger.info("Retrieving event statistics")
    try:  
        client = KafkaClient(hosts=f"{app_config['events']['hostname']}:{app_config['events']['port']}")
        topic = client.topics[app_config["events"]["topic"].encode()]  
        consumer = topic.get_simple_consumer(reset_offset_on_start=True, consumer_timeout_ms=1000)  

        stats = {"num_energy_consumption": 0, "num_solar_generation": 0}  

        for msg in consumer:
            if msg is None:  
                break  

            message = msg.value.decode("utf-8")  
            data = json.loads(message)  

            # Increment counters based on event type  
            if data["type"] == "energy-consumption": 
                stats["num_energy_consumption"] += 1  
            elif data["type"] == "solar-generation":  
                stats["num_solar_generation"] += 1

        logger.info(stats)
        return jsonify(stats), 200  

    except Exception as e:  
        logger.error(f"Error retrieving stats: {e}")  
        return {"message": "Internal server error"}, 500    

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

if __name__ == "__main__":  
    app.run(port=8110, host="0.0.0.0")