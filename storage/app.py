import connexion, yaml, logging, logging.config, json, httpx, uuid
from connexion import NoContent

from base import Base
from energy_consumption import EnergyConsumption
from solar_generation import SolarGeneration
from flask import Flask, request, jsonify
from pykafka import KafkaClient
from pykafka.common import OffsetType

import datetime
from threading import Thread
from dateutil import parser
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

# Load the configuration from app_conf.yml  
with open('config/app_conf_dev.yml', 'r') as f:  
    app_config = yaml.safe_load(f.read())  

# Configure logging
with open('config/log_conf_dev.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    print(log_config)
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

# Extract database configuration details from the config file  
db_config = app_config['datastore']  
user = db_config['user']  
password = db_config['password']  
hostname = db_config['hostname']  
port = db_config['port']  
db = db_config['db'] 

# Create the SQLAlchemy engine using the database configuration
engine = create_engine(f'mysql://{user}:{password}@{hostname}:{port}/{db}')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)  

def process_messages():  
    """ Process event messages """  
    # Connect to Kafka  
    kafka_host = f"{app_config['events']['hostname']}:{app_config['events']['port']}"
    client = KafkaClient(hosts=kafka_host)
    topic = client.topics[str.encode(app_config['events']['topic'])]
    
    # Create a consume on a consumer group, that only reads new messages
    # (uncommitted messages) when the service re-starts (i.e., it doesn't
    # read all the old messages from the history in the message queue).  
    consumer = topic.get_simple_consumer(  
        consumer_group=b'event_group',  
        reset_offset_on_start=False,  
        auto_offset_reset=OffsetType.LATEST  
    )
    # This is a blocking loop - it will wait for new messages  
    for msg in consumer:        
        msg_str = msg.value.decode('utf-8')  
        msg = json.loads(msg_str)  
        logger.info("consummed message: %s" % msg)

        payload = msg["payload"]            

        # Process based on the event type  
        if msg["type"] == "energy-consumption":  
            receiveEnergyConsumptionEvent(payload)
        elif msg["type"] == "solar-generation":
            receiveSolarGenerationEvent(payload) 

        # Commit the new message as being read  
        consumer.commit_offsets()
   
# with open('log_conf.yml', 'r') as f:  
#     log_config = yaml.safe_load(f.read())  
# logging.config.dictConfig(log_config)  
# logger = logging.getLogger('basicLogger')

# def make_session():  
#     return sessionmaker(bind=engine)()

# def receiveEnergyConsumptionEvent(body):
#     """ Receives an energy consumption reading """
    
#     session = DBSession()
#     logger.info(f"Response for event energy_consumption (id: {body['trace_id']}) has status 201")
#     ec = EnergyConsumption(body["device_id"], 
#                            body["timestamp"], 
#                            body["energy_consumed"], 
#                            body["voltage"],
#                            body["trace_id"])
    
#     logger.info(f"Energy consumption event (id: {body['trace_id']}) received")
#     logger.debug(f"Stored event Energy consumption_report with a trace id of {body['trace_id']}")

#     session.add(ec)
#     session.commit()
    
#     session.close()

#     return NoContent, 201
    
# def receiveSolarGenerationEvent(body):
#     """ Receives a solar generation reading """
    
#     session = DBSession()
#     logger.info(f"Response for event solar_generation (id: {body['trace_id']}) has status 201")

#     sg = SolarGeneration(body["device_id"], 
#                          body["timestamp"], 
#                          body["power_generated"], 
#                          body["temperature"],
#                          body["trace_id"])
    
#     logger.info(f"Solar generation event (id: {body['trace_id']}) received")
#     logger.debug(f"Stored Solar generation_report with a trace id of {body['trace_id']}")

#     session.add(sg)
#     session.commit()
#     session.close()

#     return NoContent, 201

def getEnergyConsumptionEvent(start_timestamp, end_timestamp):  
    """ Get solar generation events filtered by timestamps """  
    try:  
        # start = datetime.datetime.fromisoformat(start_timestamp)  
        # end = datetime.datetime.fromisoformat(end_timestamp)
        start = parser.parse(start_timestamp)
        end = parser.parse(end_timestamp)
    except ValueError:  
        logger.error("Invalid timestamp format")
        return {"error": "Invalid timestamp format"}, 400  

    session = DBSession()  
    try:  
        # Query energy consumption events within the given time range
        statement = select(EnergyConsumption).where(  
            EnergyConsumption.date_created >= start,  
            EnergyConsumption.date_created < end  
        )  
        results = [
            result.to_dict() 
            for result in session.execute(statement).scalars().all()
        ]
        logger.info("Found %d energy consumption readings (start: %s, end: %s)", len(results), start, end)
        return jsonify(results), 200  
    except Exception as e:
        logger.error("Error querying energy consumption events: %s", str(e))  
        return {"error": "Internal server error"}, 500  
    finally:  
        session.close()    

def getSolarGenerationEvent(start_timestamp, end_timestamp):  
    """ Get solar generation events filtered by timestamps """  
    try:  
        # Parse timestamps to datetime objects  
        # start = datetime.datetime.fromisoformat(start_timestamp)  
        # end = datetime.datetime.fromisoformat(end_timestamp)
        start = parser.parse(start_timestamp)
        end = parser.parse(end_timestamp)
    except ValueError:  
        logger.error("Invalid timestamp format")  
        return {"error": "Invalid timestamp format"}, 400  

    session = DBSession()  
    try:  
        # Query solar generation events within the given range  
        statement = select(SolarGeneration).where(  
            SolarGeneration.date_created >= start,  
            SolarGeneration.date_created < end  
        )  
        results = [  
            result.to_dict()  
            for result in session.execute(statement).scalars().all()  
        ]  
        logger.info("Found %d solar generation readings (start: %s, end: %s)", len(results), start, end)  
        return jsonify(results), 200  
    except Exception as e:  
        logger.error("Error querying solar generation events: %s", str(e))  
        return {"error": "Internal server error"}, 500  
    finally:  
        session.close()

def receiveEnergyConsumptionEvent(event):  
    """Store an energy consumption event into the database."""  
    logger.debug(f"finally")
    session = DBSession()  
    try:  
        ec = EnergyConsumption(  
            event["device_id"],  
            event["timestamp"],  
            event["energy_consumed"],  
            event["voltage"],  
            event["trace_id"]  
        )  
        session.add(ec)  
        session.commit()  
        logger.info(f"Stored Energy Consumption event with trace_id {event['trace_id']}")  
    except Exception as e:  
        logger.error(f"Error storing Energy Consumption event: {e}")  
        session.rollback()  
    finally:  
        session.close()  

def receiveSolarGenerationEvent(event):  
    logger.info(event)
    """Store a solar generation event into the database."""  
    session = DBSession()  
    try:  
        sg = SolarGeneration(  
            event["device_id"],  
            event["timestamp"],  
            event["power_generated"],  
            event["temperature"],  
            event["trace_id"]  
        )  
        session.add(sg)  
        session.commit()  
        logger.info(f"Stored Solar Generation event with trace_id {event['trace_id']}")  
    except Exception as e:  
        logger.error(f"Error storing Solar Generation event: {e}")  
        session.rollback()  
    finally:  
        session.close()

def setup_kafka_thread():  
    """ Create threads to consume messages from multiple topics """  
    t = Thread(target=process_messages)
    t.setDaemon(True)
    t.start()

# Create the Connexion app  
app = connexion.FlaskApp(__name__, specification_dir='')  
app.add_api("openapi.yml", strict_validation=True, validate_responses=True)  

if __name__ == "__main__":
    # Run the consumer in a separate thread  
    setup_kafka_thread()
    app.run(port=8090, host="0.0.0.0")