import json
import time
from datetime import datetime, timezone

vehicle_id = "V101"

latitude = 12.9716
longitude = 77.5946
speed = 45

while True:
    gps_record = {
        "vehicle_id": vehicle_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "latitude": latitude,
        "longitude": longitude,
        "speed": speed
    }

    print(json.dumps(gps_record))

    # Simulate vehicle movement
    latitude += 0.0001
    longitude += 0.0001

    time.sleep(5)