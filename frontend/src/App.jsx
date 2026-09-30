import { useEffect, useState } from "react"
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from "recharts"

import "./App.css"
import "leaflet/dist/leaflet.css"
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet"


function App() {
  const [dashboard, setDashboard] = useState(null)
  const [vehicles, setVehicles] = useState([])
  const [silverGps, setSilverGps] = useState([])
  const [fuelPrediction, setFuelPrediction] = useState(null)
  const [routes, setRoutes] = useState([])
  const [fuel, setFuel] = useState([])
  const [maintenance, setMaintenance] = useState([])
  const [fleetStatus, setFleetStatus] = useState(null)
  const [deliveryPerformance, setDeliveryPerformance] = useState(null)
  const [fuelAnalytics, setFuelAnalytics] = useState([])
  const [maintenanceAnalytics, setMaintenanceAnalytics] = useState([])
  const latestSilverGps = Object.values(
  silverGps.reduce((latest, gps) => {
    if (
      !latest[gps.vehicle_id] ||
      new Date(gps.timestamp) > new Date(latest[gps.vehicle_id].timestamp)
    ) {
      latest[gps.vehicle_id] = gps
    }

    return latest
  }, {})
)

  useEffect(() => {
  fetch("http://127.0.0.1:8000/api/dashboard")
    .then((response) => response.json())
    .then((data) => setDashboard(data))
    .catch((error) => console.error("Dashboard API Error:", error))

  const fetchSilverGps = () => {
    fetch("http://127.0.0.1:8000/api/silver/gps")
      .then((response) => response.json())
      .then((data) => {
        setSilverGps(data.gps)
        console.log("Silver GPS records:", data.gps.length)
      })
      .catch((error) => console.error("Silver GPS error:", error))
  }

  fetch(
  "http://127.0.0.1:8000/api/ml/fuel-prediction?distance_km=100&speed_kmh=60&fuel_level=70"
)
  .then((response) => response.json())
  .then((data) => {
    setFuelPrediction(data)
    console.log("ML Fuel Prediction:", data)
  })
  .catch((error) =>
    console.error("ML Fuel Prediction Error:", error)
  )

  fetchSilverGps()

  const silverGpsInterval = setInterval(fetchSilverGps, 10000)

  fetch("http://127.0.0.1:8000/api/fleet/live")
    .then((response) => response.json())
    .then((data) => setVehicles(data.vehicles))
    .catch((error) => console.error("Fleet API Error:", error))

  fetch("http://127.0.0.1:8000/api/routes")
    .then((response) => response.json())
    .then((data) => setRoutes(data.routes))
    .catch((error) => console.error("Routes API Error:", error))

  fetch("http://127.0.0.1:8000/api/fuel")
    .then((response) => response.json())
    .then((data) => setFuel(data.fuel))
    .catch((error) => console.error("Fuel API Error:", error))

  fetch("http://127.0.0.1:8000/api/fuel/analytics")
    .then((response) => response.json())
    .then((data) => setFuelAnalytics(data.fuel_analytics))
    .catch((error) =>
      console.error("Fuel Analytics API Error:", error)
    )

  fetch("http://127.0.0.1:8000/api/maintenance/analytics")
    .then((response) => response.json())
    .then((data) => setMaintenanceAnalytics(data.maintenance_analytics))
    .catch((error) =>
      console.error("Maintenance Analytics API Error:", error)
    )

  fetch("http://127.0.0.1:8000/api/maintenance")
    .then((response) => response.json())
    .then((data) => setMaintenance(data.maintenance))
    .catch((error) => console.error("Maintenance API Error:", error))

  fetch("http://127.0.0.1:8000/api/fleet/status")
    .then((response) => response.json())
    .then((data) => setFleetStatus(data))
    .catch((error) => console.error("Fleet Status API Error:", error))

  fetch("http://127.0.0.1:8000/api/delivery-performance")
    .then((response) => response.json())
    .then((data) => setDeliveryPerformance(data))
    .catch((error) =>
      console.error("Delivery Performance API Error:", error)
    )

  return () => {
    clearInterval(silverGpsInterval)
  }
}, [])

  if (!dashboard) {
    return <h2 className="loading">Loading FleetVision 360...</h2>
  }

  return (
    <div className="app">

      <header className="header">
        <div>
          <h1>FleetVision 360</h1>
          <p>Fleet Intelligence Dashboard</p>
        </div>

        <div className="status">
          <span></span> System Online
        </div>
      </header>

      <main>

        <h2>Dashboard Overview</h2>

        <div className="cards">

          <div className="card">
            <div className="icon">🚚</div>
            <div>
              <p>Vehicles</p>
              <h3>{dashboard.vehicles}</h3>
            </div>
          </div>

          <div className="card">
            <div className="icon">👨‍✈️</div>
            <div>
              <p>Drivers</p>
              <h3>{dashboard.drivers}</h3>
            </div>
          </div>

          <div className="card">
            <div className="icon">🛣️</div>
            <div>
              <p>Routes</p>
              <h3>{dashboard.routes}</h3>
            </div>
          </div>

          <div className="card">
            <div className="icon">📦</div>
            <div>
              <p>Deliveries</p>
              <h3>{dashboard.deliveries.toLocaleString()}</h3>
            </div>
          </div>

          <div className="card">
            <div className="icon">⏱️</div>
            <div>
              <p>On-Time Delivery</p>
              <h3>{dashboard.on_time_delivery_rate_percent}%</h3>
            </div>
          </div>

          <div className="card">
            <div className="icon">⛽</div>
            <div>
              <p>Fuel Cost</p>
              <h3>₹{dashboard.fuel_cost.toLocaleString()}</h3>
            </div>
          </div>

          <div className="card">
            <div className="icon">🔧</div>
            <div>
              <p>Maintenance Orders</p>
              <h3>{dashboard.maintenance_work_orders}</h3>
            </div>
          </div>

        </div>
        <section className="fuel-analytics-section">
  <h2>Fuel Analytics</h2>

  <div className="fuel-chart-card">
    <ResponsiveContainer width="100%" height={350}>
      <BarChart data={fuelAnalytics}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="fuel_type" />
        <YAxis />
        <Tooltip />
        <Bar dataKey="total_liters" name="Fuel Liters" />
      </BarChart>
    </ResponsiveContainer>
  </div>
</section>
        <section className="delivery-performance-section">
  <h2>Delivery Performance</h2>

  <div className="delivery-performance-card">
    <div>
      <p>Total Completed Deliveries</p>
      <h3>{deliveryPerformance?.total_deliveries ?? 0}</h3>
    </div>

    <div>
      <p>Delivered</p>
      <h3>{deliveryPerformance?.delivered ?? 0}</h3>
    </div>

    <div>
      <p>Delayed</p>
      <h3>{deliveryPerformance?.delayed ?? 0}</h3>
    </div>

    <div>
      <p>Delivery Performance</p>
      <h3>
        {deliveryPerformance?.on_time_rate_percent ?? 0}%
      </h3>
    </div>
  </div>
</section>

<section className="maintenance-analytics-section">
  <h2>Maintenance Analytics</h2>

  <div className="maintenance-chart-card">
    <ResponsiveContainer width="100%" height={350}>
      <BarChart
        data={[
          {
            priority: "High",
            total_cost: 8790659.66
          },
          {
            priority: "Medium",
            total_cost: 9137636.23
          },
          {
            priority: "Low",
            total_cost: 8602673.89
          }
        ]}
      >
        <CartesianGrid strokeDasharray="3 3" />

        <XAxis dataKey="priority" />

        <YAxis
  tickFormatter={(value) =>
    `₹${(value / 100000).toFixed(0)}L`
  }
/>

        <Tooltip
          formatter={(value) =>
            `₹${Number(value).toLocaleString("en-IN")}`
          }
        />

        <Bar
          dataKey="total_cost"
          name="Maintenance Cost"
        />
      </BarChart>
    </ResponsiveContainer>
  </div>
</section>
        <section className="fleet-status-section">
  <h2>Fleet Status</h2>

  <div className="status-cards">
    <div className="status-card">
      <span>🟢</span>
      <div>
        <p>Moving</p>
        <h3>{fleetStatus?.moving ?? 0}</h3>
      </div>
    </div>

    <div className="status-card">
      <span>🟡</span>
      <div>
        <p>Idle</p>
        <h3>{fleetStatus?.idle ?? 0}</h3>
      </div>
    </div>

    <div className="status-card">
      <span>🔴</span>
      <div>
        <p>Stopped</p>
        <h3>{fleetStatus?.stopped ?? 0}</h3>
      </div>
    </div>

    <div className="status-card">
      <span>🚚</span>
      <div>
        <p>Total Vehicles</p>
        <h3>{fleetStatus?.total ?? 0}</h3>
      </div>
    </div>
  </div>
</section>

<section className="fleet-map-section">
  <h2>Live Fleet Map</h2>

  <div className="fleet-map-card">
    <MapContainer
      center={[15.3173, 75.7139]}
      zoom={6}
      style={{ height: "500px", width: "100%" }}
    >
      <TileLayer
        attribution='&copy; OpenStreetMap contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

{latestSilverGps.map((gps) => {
  const vehicleInfo = vehicles.find(
    (v) => v.vehicle_id === gps.vehicle_id
  )

  return (
    <Marker
      key={gps.vehicle_id}
      position={[
        gps.latitude,
        gps.longitude
      ]}
    >
      <Popup>
        <strong>{gps.vehicle_id}</strong>
        <br />
        Type: {vehicleInfo?.type ?? "N/A"}
        <br />
        Model: {vehicleInfo?.model ?? "N/A"}
        <br />
        Speed: {gps.speed} km/h
      </Popup>
    </Marker>
  )
})}
    </MapContainer>
  </div>
</section>
                <section className="fleet-section">
          <h2>Live Fleet</h2>

          <div className="fleet-table-container">
            <table className="fleet-table">
              <thead>
                <tr>
                  <th>Vehicle ID</th>
                  <th>Type</th>
                  <th>Model</th>
                  <th>Depot</th>
                  <th>Speed</th>
                  <th>Status</th>
                  <th>Latitude</th>
                  <th>Longitude</th>
                  <th>Last Update</th>
                </tr>
              </thead>

              <tbody>
                {vehicles.map((vehicle) => (
                  <tr key={vehicle.vehicle_id}>
                    <td>{vehicle.vehicle_id}</td>
                    <td>{vehicle.type}</td>
                    <td>{vehicle.model}</td>
                    <td>{vehicle.depot_id}</td>
                    <td>{vehicle.speed} km/h</td>
                    <td>
                     {Number(vehicle.speed) > 5
                        ? "Moving"
                        : Number(vehicle.speed) > 0
                         ? "Idle"
                          : "Stopped"}
                    </td>
                    <td>{vehicle.latitude}</td>
                    <td>{vehicle.longitude}</td>
                    <td>{vehicle.timestamp}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
                <section className="map-section">
          <h2>Fleet Map</h2>

          <MapContainer
            center={[20.5937, 78.9629]}
            zoom={5}
            className="fleet-map"
          >
            <TileLayer
              attribution='&copy; OpenStreetMap contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />

            {vehicles.map((vehicle) => {
  const speed = Number(vehicle.speed) || 0

  let status = "Stopped"

  if (speed > 5) {
    status = "Moving"
  } else if (speed > 0) {
    status = "Idle"
  }

  return (
    <Marker
                key={vehicle.vehicle_id}
                position={[
                  vehicle.latitude,
                  vehicle.longitude
                ]}
              >
                <Popup>
                  <strong>{vehicle.vehicle_id}</strong>
                  <br />
                  Type: {vehicle.type}
                  <br />
                  Model: {vehicle.model}
                  <br />
                  Speed: {vehicle.speed} km/h
                  <br />
                  Status: {status}
                  <br />
                  Depot: {vehicle.depot_id}
                </Popup>
              </Marker>
               )
            })}
          </MapContainer>
        </section>

                <section className="routes-section">
          <h2>Routes</h2>

          <div className="routes-table-container">
            <table className="routes-table">
              <thead>
                <tr>
                  <th>Route ID</th>
                  <th>Origin</th>
                  <th>Destination</th>
                  <th>Distance</th>
                  <th>Expected Duration</th>
                </tr>
              </thead>

              <tbody>
                {routes.map((route) => (
                  <tr key={route.route_key}>
                    <td>{route.route_id}</td>
                    <td>{route.origin}</td>
                    <td>{route.destination}</td>
                    <td>{route.distance_km} km</td>
                    <td>{route.expected_duration_min} min</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="fuel-section">
  <h2>Fuel Records</h2>

  <div className="fuel-table-container">
    <table className="fuel-table">
      <thead>
        <tr>
          <th>Vehicle ID</th>
          <th>Timestamp</th>
          <th>Fuel Type</th>
          <th>Liters</th>
          <th>Amount</th>
          <th>Odometer</th>
        </tr>
      </thead>

      <tbody>
        {fuel.map((record) => (
          <tr key={record.fuel_key}>
            <td>{record.vehicle_id}</td>
            <td>{record.timestamp}</td>
            <td>{record.fuel_type}</td>
            <td>{record.liters} L</td>
            <td>₹{record.amount}</td>
            <td>{record.odometer_km} km</td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>
</section>
<section className="maintenance-section">
  <h2>Maintenance Records</h2>

  <div className="maintenance-table-container">
    <table className="maintenance-table">
      <thead>
        <tr>
          <th>Work Order</th>
          <th>Vehicle ID</th>
          <th>Issue</th>
          <th>Priority</th>
          <th>Opened</th>
          <th>Closed</th>
          <th>Cost</th>
          <th>Downtime</th>
        </tr>
      </thead>

      <tbody>
        {maintenance.map((record) => (
          <tr key={record.maintenance_key}>
            <td>{record.work_order_id}</td>
            <td>{record.vehicle_id}</td>
            <td>{record.issue}</td>
            <td>{record.priority}</td>
            <td>{record.opened_at}</td>
            <td>{record.closed_at}</td>
            <td>₹{record.cost}</td>
            <td>{record.downtime_hours} hrs</td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>
</section>
<section className="silver-gps-section">
  <h2>Silver GPS Data</h2>

  <div className="silver-gps-card">
    <p>
      GPS records processed by PySpark: <strong>{silverGps.length}</strong>
    </p>

    <div className="silver-gps-table">
      <table>
        <thead>
          <tr>
            <th>Vehicle ID</th>
            <th>Timestamp</th>
            <th>Latitude</th>
            <th>Longitude</th>
            <th>Speed (km/h)</th>
          </tr>
        </thead>

        <tbody>
          {silverGps.slice(0, 10).map((gps, index) => (
            <tr key={`${gps.vehicle_id}-${gps.timestamp}-${index}`}>
              <td>{gps.vehicle_id}</td>
              <td>{gps.timestamp}</td>
              <td>{gps.latitude}</td>
              <td>{gps.longitude}</td>
              <td>{gps.speed}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  </div>
</section>

<section className="ml-prediction-section">
  <h2>ML Fuel Prediction</h2>

  <div className="ml-prediction-card">
    <div>
      <p>Distance</p>
      <h3>{fuelPrediction?.distance_km ?? 0} km</h3>
    </div>

    <div>
      <p>Speed</p>
      <h3>{fuelPrediction?.speed_kmh ?? 0} km/h</h3>
    </div>

    <div>
      <p>Fuel Level</p>
      <h3>{fuelPrediction?.fuel_level ?? 0}%</h3>
    </div>

    <div>
      <p>Predicted Consumption</p>
      <h3>
        {fuelPrediction?.predicted_fuel_consumption ?? 0}
      </h3>
    </div>

    <div>
      <p>Model</p>
      <h3>{fuelPrediction?.model ?? "Loading..."}</h3>
    </div>
  </div>
</section>
      </main>

    </div>
  )
}

export default App
