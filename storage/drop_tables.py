# import sqlite3

# conn = sqlite3.connect('events.sqlite')

# c = conn.cursor()
# c.execute('''
#           DROP TABLE energy_consumption;
#           ''')
# c.execute('''
#           Drop TABLE solar_generation;
#           ''')

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
          DROP TABLE IF EXISTS energy_consumption;  
          ''')  

c.execute('''  
          DROP TABLE IF EXISTS solar_generation;  
          ''')  

conn.commit()  
conn.close()