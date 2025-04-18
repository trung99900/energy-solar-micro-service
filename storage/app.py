from dotenv import load_dotenv
# Load environment variables from .env file  
load_dotenv()
import os

import connexion, yaml, logging, logging.config, json, os
from connexion import NoContent

from base import Base
from energy_consumption import EnergyConsumption
from solar_generation import SolarGeneration
from flask import jsonify
from pykafka import KafkaClient
from pykafka.common import OffsetType
from pykafka.exceptions import KafkaException

from threading import Thread
from dateutil import parser
import random
import time
from sqlalchemy import create_engine, select, func
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
# user = db_config['user']
user = os.getenv('DB_USER')
# password = db_config['password']
password = os.getenv('DB_PASSWORD')
hostname = db_config['hostname']
port = db_config['port']
db = db_config['db']

# Create the SQLAlchemy engine using the database configuration
engine = create_engine(
    f'mysql://{user}:{password}@{hostname}:{port}/{db}',
    pool_size=100,
    max_overflow=50,
    pool_recycle=1800,
    pool_pre_ping=True
)

Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)

class KafkaWrapper:
    """ Kafka wrapper for consumer """
    def __init__(self, hostname, topic):
        self.hostname = hostname
        self.topic = topic
        self.client = None
        self.consumer = None
        self.connect()

    def connect(self):
        """Infinite loop: will keep trying"""
        while True:
            logger.debug("Trying to connect to Kafka...")
            if self.make_client():
                if self.make_consumer():
                    break
            # Sleeps for a random amount of time (0.5 to 1.5s)
            time.sleep(random.randint(500, 1500) / 1000)

    def make_client(self):
        """
        Runs once, makes a client and sets it on the instance.
        Returns: True (success), False (failure)
        """
        if self.client is not None:
            return True
        try:
            self.client = KafkaClient(hosts=self.hostname)
            logger.info("Kafka client created!")
            return True
        except KafkaException as e:
            msg = f"Kafka error when making client: {e}"
            logger.warning(msg)
            self.client = None
            self.consumer = None
            return False

    def make_consumer(self):
        """
        Runs once, makes a consumer and sets it on the instance.
        Returns: True (success), False (failure)
        """
        if self.consumer is not None:
            return True
        if self.client is None:
            return False
        try:
            topic = self.client.topics[str.encode(self.topic)]
            self.consumer = topic.get_simple_consumer(
                consumer_group=b'event_group',
                reset_offset_on_start=False,
                auto_offset_reset=OffsetType.LATEST
            )
            logger.info("Kafka consumer created")
        except KafkaException as e:
            msg = f"Make error when making consumer: {e}"
            logger.warning(msg)
            self.client = None
            self.consumer = None
            return False

    def messages(self):
        """Generator method that catches exceptions in the consumer loop"""
        if self.consumer is None:
            self.connect()
        while True:
            try:
                for msg in self.consumer:
                    yield msg
            except KafkaException as e:
                msg = f"Kafka issue in consumer: {e}"
                logger.warning(msg)
                self.client = None
                self.consumer = None
                self.connect()

kafka_wrapper = KafkaWrapper(f"{app_config['kafka']['events']['hostname']}:{app_config['kafka']['events']['port']}", app_config['kafka']['events']['topic'])

def process_messages():
    """ Process event messages """
    # Connect to Kafka
    kafka_host = f"{app_config['kafka']['events']['hostname']}:{app_config['kafka']['events']['port']}"
    client = KafkaClient(hosts=kafka_host)
    topic = client.topics[str.encode(app_config['kafka']['events']['topic'])]

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
            receive_energy_consumption_event(payload)
        elif msg["type"] == "solar-generation":
            receive_solar_generation_event(payload)

        # Commit the new message as being read
        consumer.commit_offsets()

def get_energy_consumption_event(start_timestamp, end_timestamp):
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

def get_solar_generation_event(start_timestamp, end_timestamp):
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

def receive_energy_consumption_event(event):
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

def receive_solar_generation_event(event):
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

def get_count():
    logger.info("get_count")
    session = DBSession()
    try:
        energy_consumption_count = session.query(func.count(EnergyConsumption.id)).scalar()  
        solar_generation_count = session.query(func.count(SolarGeneration.id)).scalar()

        result = {
            "energy_consumption_count": energy_consumption_count,
            "solar_generation_count": solar_generation_count
        }
        logger.info("Count of events: %s", result)
        return jsonify(result), 200
    
    except Exception as e:
        logger.error("Error counting energy consumption events: %s", str(e))
        return {"error": "Internal server error"}, 500

def get_energy_consumption_event_ids():
    """ Get all energy consumption event IDs """
    session = DBSession()
    try:
        statement = select(EnergyConsumption.id, EnergyConsumption.trace_id)
        results = session.execute(statement).all()
        ids = [
            {"event_id": str(row[0]), "trace_id": str(row[1])}
            for row in results
        ]
        logger.info("Found %d energy consumption event IDs", len(ids))
        return jsonify(ids), 200
    except Exception as e:
        logger.error("Error querying energy consumption event IDs: %s", str(e))
        return {"error": "Internal server error"}, 500
    finally:
        session.close()

def get_solar_generation_event_ids():
    """ Get all solar generation event IDs """
    session = DBSession()
    try:
        statement = select(SolarGeneration.id, SolarGeneration.trace_id)  
        results = session.execute(statement).all()  
        ids = [  
            {"event_id": str(row[0]), "trace_id": str(row[1])}  
            for row in results  
        ]  
        logger.info("Found %d solar generation event IDs", len(ids))  
        return jsonify(ids), 200  
    except Exception as e:  
        logger.error("Error querying solar generation event IDs: %s", str(e))  
        return {"error": "Internal server error"}, 500  
    finally:  
        session.close()
        
# Create the Connexion app
app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yml", base_path="/storage", strict_validation=True, validate_responses=True)

if __name__ == "__main__":
    # Run the consumer in a separate thread
    setup_kafka_thread()
    app.run(port=8090, host="0.0.0.0")