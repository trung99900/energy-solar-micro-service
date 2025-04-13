import connexion, yaml, logging, logging.config, json, os
from connexion import NoContent

from base import Base
from energy_consumption import EnergyConsumption
from solar_generation import SolarGeneration
from flask import jsonify
from pykafka import KafkaClient
from pykafka.common import OffsetType

from threading import Thread
from dateutil import parser
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker

# Load app configuration (fall back to defaults if missing)  
config_path = os.getenv("APP_CONF", "config/app_conf_dev.yml")
log_path = os.getenv("LOG_CONF", "config/log_conf_dev.yml")

# Load the configuration from app_conf.yml
with open('config_path', 'r') as f:
    app_config = yaml.safe_load(f.read())

# Configure logging
with open('log_path', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

# Extract database configuration details from environment variables or app config  
db_user = os.getenv("DB_USER", app_config['datastore'].get('user', 'root'))  
db_password = os.getenv("DB_PW", app_config['datastore'].get('password', 'password'))  
db_hostname = os.getenv("DB_HOST", app_config['datastore'].get('hostname', 'db'))  
db_port = os.getenv("DB_PORT", app_config['datastore'].get('port', '3306'))  
db_name = os.getenv("DB_NAME", app_config['datastore'].get('db', 'default_db'))

# Log the DB connection details (without the password)  
logger.info(f"Connecting to database {db_name} at {db_hostname}:{db_port} as user {db_user}")

# Create the SQLAlchemy engine using the updated configuration  
try:  
    engine = create_engine(f'mysql+pymysql://{db_user}:{db_password}@{db_hostname}:{db_port}/{db_name}')  
    Base.metadata.bind = engine  
    DBSession = sessionmaker(bind=engine)  
    logger.info("Database engine created successfully.")  
except Exception as e:  
    logger.error(f"Error creating database engine: {e}")  
    raise e

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
        energy_consumption_count = select(func.count()).select_from(EnergyConsumption)
        solar_generation_count = select(func.count()).select_from(SolarGeneration)

        session.close()

        count = {
            "energy_consumption_count": energy_consumption_count,
            "solar_generation_count": solar_generation_count
        }
        logger.info("Count of events: %s", count)
        return jsonify(count), 200
    
    except Exception as e:
        logger.error("Error counting energy consumption events: %s", str(e))
        return {"error": "Internal server error"}, 500

def get_energy_consumption_event_ids():
    """ Get all energy consumption event IDs """
    session = DBSession()
    try:
        statement = select(EnergyConsumption.id)
        results = [
            result[0]
            for result in session.execute(statement).scalars().all()
        ]
        logger.info("Found %d energy consumption event IDs", len(results))
        return jsonify(results), 200
    except Exception as e:
        logger.error("Error querying energy consumption event IDs: %s", str(e))
        return {"error": "Internal server error"}, 500
    finally:
        session.close()

def get_solar_generation_event_ids():
    """ Get all solar generation event IDs """
    session = DBSession()
    try:
        statement = select(SolarGeneration.id)
        results = [
            result[0]
            for result in session.execute(statement).scalars().all()
        ]
        logger.info("Found %d solar generation event IDs", len(results))
        return jsonify(results), 200
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