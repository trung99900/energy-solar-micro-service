# import sqlite3  

# # Connect to the SQLite database (or create it if it doesn't exist)  
# conn = sqlite3.connect('events.sqlite')  

# # Create a cursor object to execute SQL commands  
# c = conn.cursor()  

# # Create the energy_consumption table  
# c.execute('''  
#           CREATE TABLE energy_consumption (  
#               id INTEGER PRIMARY KEY ASC,   
#               device_id VARCHAR(250) NOT NULL,   
#               timestamp VARCHAR(100) NOT NULL,   
#               energy_consumed FLOAT NOT NULL,   
#               voltage FLOAT NOT NULL,   
#               date_created VARCHAR(100) NOT NULL)                
#           ''')

# # Create the solar_generation table  
# c.execute('''  
#           CREATE TABLE solar_generation (  
#               id INTEGER PRIMARY KEY ASC,   
#               device_id VARCHAR(250) NOT NULL,   
#               timestamp VARCHAR(100) NOT NULL,   
#               power_generated FLOAT NOT NULL,   
#               temperature FLOAT NOT NULL,   
#               date_created VARCHAR(100) NOT NULL)  
#           ''')

# # Commit the changes and close the connection  
# conn.commit()  
# conn.close()

import MySQLdb  

# Connect to the MySQL database  
conn = MySQLdb.connect(  
    host="localhost",         
    user="huutrung",    
    passwd="123456",  
    db="lab04_ConfigLogging"  
)  

# Create a cursor object to execute SQL commands  
c = conn.cursor()  

c.execute('''  
          CREATE TABLE IF NOT EXISTS energy_consumption (  
            id INT AUTO_INCREMENT PRIMARY KEY,   
            device_id VARCHAR(250) NOT NULL,   
            timestamp VARCHAR(100) NOT NULL,   
            energy_consumed FLOAT NOT NULL,   
            voltage FLOAT NOT NULL,   
            date_created VARCHAR(100) NOT NULL,
            trace_id VARCHAR(250) NOT NULL
          )  
          ''')  

c.execute('''  
          CREATE TABLE IF NOT EXISTS solar_generation (  
            id INT AUTO_INCREMENT PRIMARY KEY,   
            device_id VARCHAR(250) NOT NULL,   
            timestamp VARCHAR(100) NOT NULL,   
            power_generated FLOAT NOT NULL,   
            temperature FLOAT NOT NULL,   
            date_created VARCHAR(100) NOT NULL,
            trace_id VARCHAR(250) NOT NULL  
          )  
          ''')  

conn.commit()  
conn.close()