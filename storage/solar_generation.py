from sqlalchemy import Column, Integer, String, Float, DateTime  
from sqlalchemy.sql.functions import now  
from base import Base  

class SolarGeneration(Base):  
    """ Solar Generation """  

    __tablename__ = "solar_generation"  

    id = Column(Integer, primary_key=True, autoincrement=True)  
    device_id = Column(String(250), nullable=False)  # UUID format  
    timestamp = Column(String(100), nullable=False)  
    power_generated = Column(Float, nullable=False)  # in kWh  
    temperature = Column(Float, nullable=False)  # in degrees Celsius  
    date_created = Column(DateTime, nullable=False)
    trace_id = Column(String(250), nullable=False)

    def __init__(self, device_id, timestamp, power_generated, temperature, trace_id):  
        """ Initializes a solar generation reading """  
        self.device_id = device_id  
        self.timestamp = timestamp  
        self.power_generated = power_generated  
        self.temperature = temperature
        self.date_created = now() # Set the date/time record is created
        self.trace_id = trace_id

    def to_dict(self):  
        """ Dictionary Representation of a solar generation reading """  
        dict = {}
        dict["id"] = self.id  
        dict["device_id"] = self.device_id  
        dict["timestamp"] = self.timestamp
        dict["power_generated"] = self.power_generated  
        dict["temperature"] = self.temperature
        dict["date_created"] = self.date_created
        dict["trace_id"] = self.trace_id
        
        return dict