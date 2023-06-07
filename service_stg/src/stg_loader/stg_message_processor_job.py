import time
from datetime import datetime
from logging import Logger
from app_config import AppConfig
from stg_loader.repository.stg_repository import StgRepository
from lib.kafka_connect import KafkaConsumer
from lib.kafka_connect import KafkaProducer
from lib.redis import RedisClient
import json

class StgMessageProcessor:
    # def __init__(self, logger):
    #     self._logger = logger
    def __init__(self,
                 kafka_consumer: KafkaConsumer,
                 kafka_producer: KafkaProducer,
                 redis_client: RedisClient,
                 stg_Repository: StgRepository,
                 batch_size: int,
                 logger: Logger) -> None:
        self._logger = logger
        self._consumer = kafka_consumer
        self._producer = kafka_producer
        self._redis = redis_client
        self._stg_repository = stg_Repository
        self._batch_size = batch_size

    # функция, которая будет вызываться по расписанию.
    def run(self) -> None:
        # Пишем в лог, что джоб был запущен.
        # self._logger.info(f"{datetime.utcnow()}: START")

        for i in range(self._batch_size):
            msg = self._consumer.consume()

            if msg is None:
                self._logger.info('msg is not received ----- break')
                break

            if "object_id" in msg:
                pass
            else:
                self._logger.info('MSG has no "object_id", skip to next msg')
                continue 

            object_id = msg["object_id"]
            object_type = msg["object_type"]
            payload = msg["payload"]
            str_payload = json.dumps(payload)

            user = json.dumps(payload["user"])
            user_id = payload["user"]["id"]
            restaurant = json.dumps(payload["restaurant"])
            restaurant_id = payload["restaurant"]["id"]

            order_date = payload["date"]
            cost = payload["cost"]
            payment = payload["payment"]
            final_status = payload["final_status"]
            products = payload["order_items"]

            try:
                self._stg_repository.order_events_insert(object_id, object_type, order_date, str_payload)
            except Exception as E:
                self._logger.info('------------------')
                self._logger.info('Error inserting into pg: ' + str(E))


            redis_user = self._redis.get(user_id)
            redis_restaurant = self._redis.get(restaurant_id)

            menu = redis_restaurant["menu"]

            msg_out = {}
            msg_out["object_id"] = object_id
            msg_out["object_type"] = object_type

            payload_out = {}
            payload_out["id"] = object_id
            payload_out["date"] = order_date
            payload_out["cost"] = cost
            payload_out["payment"] = payment
            payload_out["status"] = final_status

            user = {}
            user["id"] = user_id
            user["name"] = redis_user["name"]
            payload_out["user"] = user

            restaurant={}
            restaurant["id"] = restaurant_id
            restaurant["name"] = redis_restaurant["name"]
            payload_out["restaurant"] = restaurant

            for product in products:
                product_id = product["id"]
                product["category"] = "not found"

                for menu_item in menu:
                    if menu_item["_id"] == product_id:
                        product["category"] = menu_item["category"]
                        break 

                if product["category"] == "not found":
                    raise Exception("category for product_id " + product_id + " not found in restaurant " + restaurant_id)

            payload_out["products"] = products

            msg_out["payload"] = payload_out

            try:
                self._producer.produce(msg_out)
                self._logger.info('produced to topic "' + self._producer.topic + '" ------')
                #self._logger.info('msg_out = ' + json.dumps(msg_out))
            except Exception as E:   
                self._logger.info('ERROR producing to topic "' + self._producer.topic + '": ' + str(E))
                self._logger.info('msg_out = ' + json.dumps(msg_out))

        # Пишем в лог, что джоб успешно завершен.
        # self._logger.info(f"{datetime.utcnow()}: FINISH")
