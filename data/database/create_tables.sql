CREATE TABLE IF NOT EXISTS energy_consumption (  
            id INT AUTO_INCREMENT PRIMARY KEY,   
            device_id VARCHAR(250) NOT NULL,   
            timestamp VARCHAR(100) NOT NULL,   
            energy_consumed FLOAT NOT NULL,   
            voltage FLOAT NOT NULL,   
            date_created VARCHAR(100) NOT NULL,
            trace_id VARCHAR(250) NOT NULL
          );

CREATE TABLE IF NOT EXISTS solar_generation (  
            id INT AUTO_INCREMENT PRIMARY KEY,   
            device_id VARCHAR(250) NOT NULL,   
            timestamp VARCHAR(100) NOT NULL,   
            power_generated FLOAT NOT NULL,   
            temperature FLOAT NOT NULL,   
            date_created VARCHAR(100) NOT NULL,
            trace_id VARCHAR(250) NOT NULL  
          );