import random
from locust import HttpUser, task, between


class OrderUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task
    def create_order(self):
        self.client.post(
            "/orders",
            json={
                "customer_id": random.randint(1, 1000),
                "restaurant_id": random.randint(1, 100),
                "value": random.randint(100, 1000),
                "pickup_lat": 28.61,
                "pickup_lon": 77.20,
                "drop_lat": 28.70,
                "drop_lon": 77.10,
            },
        )
