from sqlalchemy import Column, Integer, String, Float, DateTime  
from sqlalchemy.sql.functions import now  
from base import Base
import datetime  

class EnergyConsumption(Base):  
    """ Energy Consumption """  

    __tablename__ = "energy_consumption"  

    id = Column(Integer, primary_key=True, autoincrement=True)  
    device_id = Column(String(250), nullable=False)  # UUID format  
    timestamp = Column(String(100), nullable=False)  
    energy_consumed = Column(Float, nullable=False)  # in kWh  
    voltage = Column(Float, nullable=False)  # in volts  
    date_created = Column(DateTime, nullable=False)
    trace_id = Column(String(250), nullable=False)  

    def __init__(self, device_id, timestamp, energy_consumed, voltage, trace_id):  
        """ Initializes an energy consumption reading """  
        self.device_id = device_id  
        self.timestamp = timestamp  
        self.energy_consumed = energy_consumed  
        self.voltage = voltage
        self.date_created = datetime.datetime.now() # Set the date/time record is created
        self.trace_id = trace_id

    def to_dict(self):  
        """ Dictionary Representation of an energy consumption reading """  
        dict = {}
        dict['id'] = self.id  
        dict['device_id'] = self.device_id  
        dict['timestamp'] = self.timestamp  
        dict['energy_consumed'] = self.energy_consumed  
        dict['voltage'] = self.voltage  
        dict['date_created'] = self.date_created
        dict['trace_id'] = self.trace_id
        
        
        return dict