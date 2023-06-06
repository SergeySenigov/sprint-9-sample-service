from flask import Flask
import logging
import os
from app_config import AppConfig

app = Flask(__name__)

@app.get('/health')
def health():
    return ', '.join([
                     'healthy from hello',
                     str(os.getenv('KAFKA_HOST')), 
                     str(os.getenv('KAFKA_PORT'))
                     ])

if __name__ == '__main__':
    print('__name__ is main')

    # for i in dir(app):
    #     print(i)
    app.logger.setLevel(logging.INFO)
    print ('set level INFO')

    config = AppConfig()

    print(config.CERTIFICATE_PATH)
    print(config.DEFAULT_JOB_INTERVAL)
    print(config.kafka_consumer_group)
    print(config.kafka_consumer_topic)
    print(config.kafka_consumer_username)
    print(config.kafka_host)
    print(config.kafka_port)
    print(config.kafka_producer_password)
    print(config.kafka_producer_topic)
    print(config.kafka_producer_username)
    print(config.pg_warehouse_dbname)
    print(config.pg_warehouse_port)
    print(config.pg_warehouse_dbname)

    # стартуем Flask-приложение.
    app.run(debug=True, host='0.0.0.0', use_reloader=True)
else:    
    print('__name__ is not main')