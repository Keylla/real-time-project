import json
import time
import random
from kafka import KafkaProducer
from faker import Faker

faker = Faker()

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def generate_trip():
    return {
        "partner_id": faker.uuid4(),
        "trip_id": faker.uuid4(),
        "start_time": faker.date_time_this_year().isoformat(),
        "end_time": faker.date_time_this_year().isoformat(),
        "distance_km": round(random.uniform(1, 100), 2),
        "city": faker.city()
    }

while True:
    trip = generate_trip()
    producer.send('trips', value=trip)
    print(f"Sent trip: {trip}")
    time.sleep(2)
