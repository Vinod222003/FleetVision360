import getpass
import psycopg2

password = getpass.getpass("Enter PostgreSQL password: ")

try:
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="fleetvision360",
        user="postgres",
        password=password
    )

    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM dim_vehicle")
    vehicles = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM fact_delivery")
    deliveries = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM fact_gps")
    gps = cur.fetchone()[0]

    print()
    print("=" * 50)
    print("PostgreSQL Backend Connection: SUCCESS")
    print("=" * 50)
    print("Vehicles   :", vehicles)
    print("Deliveries :", deliveries)
    print("GPS rows   :", gps)
    print("=" * 50)

    cur.close()
    conn.close()

except Exception as e:
    print()
    print("PostgreSQL connection FAILED")
    print("Error:", e)
