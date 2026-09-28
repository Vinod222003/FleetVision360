import { useEffect, useState } from "react"
import "./App.css"
import "leaflet/dist/leaflet.css"
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet"


function App() {
  const [dashboard, setDashboard] = useState(null)
  const [vehicles, setVehicles] = useState([])
  const [routes, setRoutes] = useState([])
  const [fuel, setFuel] = useState([])
  const [maintenance, setMaintenance] = useState([])
  const [fleetStatus, setFleetStatus] = useState(null)
  const [deliveryPerformance, setDeliveryPerformance] = useState(null)

  useEffect(() => {
  fetch("http://127.0.0.1:8002/api/dashboard")
    .then((response) => response.json())
    .then((data) => setDashboard(data))
    .catch((error) => console.error("Dashboard API Error:", error))

  fetch("http://127.0.0.1:8002/api/fleet/live")
    .then((response) => response.json())
    .then((data) => setVehicles(data.vehicles))
    .catch((error) => console.error("Fleet API Error:", error))

   fetch("http://127.0.0.1:8002/api/routes")
  .then((response) => response.json())
  .then((data) => setRoutes(data.routes))
  .catch((error) => console.error("Routes API Error:", error))

  fetch("http://127.0.0.1:8002/api/fuel")
  .then((response) => response.json())
  .then((data) => setFuel(data.fuel))
  .catch((error) => console.error("Fuel API Error:", error))

  fetch("http://127.0.0.1:8002/api/maintenance")
  .then((response) => response.json())
  .then((data) => setMaintenance(data.maintenance))
  .catch((error) => console.error("Maintenance API Error:", error))

  fetch("http://127.0.0.1:8002/api/fleet/status")
  .then((response) => response.json())
  .then((data) => setFleetStatus(data))
  .catch((error) => console.error("Fleet Status API Error:", error))

  fetch("http://127.0.0.1:8002/api/delivery-performance")
  .then((response) => response.json())
  .then((data) => setDeliveryPerformance(data))
  .catch((error) =>
    console.error("Delivery Performance API Error:", error))
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
      </main>

    </div>
  )
}

export default App