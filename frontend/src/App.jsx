import { useEffect, useMemo, useState, useRef } from "react"
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  Legend
} from "recharts"

import "./App.css"
import "leaflet/dist/leaflet.css"
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from "react-leaflet"
import "leaflet.marker.slideto"


function FitFleetBounds({ positions }) {
  const map = useMap()

  useEffect(() => {
    if (!positions || positions.length === 0) {
      return
    }

    if (positions.length === 1) {
      map.setView(positions[0], 12)
      return
    }

    const bounds = positions.map(position => position)
    map.fitBounds(bounds, {
      padding: [40, 40],
      maxZoom: 13
    })
  }, [positions, map])

  return null
}

function AnimatedMarker({ gps, vehicleInfo }) {
  const markerRef = useRef(null)

  useEffect(() => {
    const marker = markerRef.current

    if (!marker || gps.latitude == null || gps.longitude == null) {
      return
    }

    marker.slideTo(
      [Number(gps.latitude), Number(gps.longitude)],
      {
        duration: 9000,
        keepAtCenter: false
      }
    )
  }, [gps.latitude, gps.longitude])

  return (
    <Marker
      ref={markerRef}
      position={[Number(gps.latitude), Number(gps.longitude)]}
    >
      <Popup>
        <strong>{gps.vehicle_id}</strong>
        <br />
        Type: {vehicleInfo?.vehicle_type || vehicleInfo?.type || "Vehicle"}
        <br />
        Model: {vehicleInfo?.model || "Fleet Vehicle"}
        <br />
        Speed: {Number(gps.speed).toFixed(1)} km/h
        <br />
        Status: {
          Number(gps.speed) === 0
            ? "Stopped"
            : Number(gps.speed) < 10
              ? "Idle"
              : "Moving"
        }
      </Popup>
    </Marker>
  )
}

function App() {
  const API = import.meta.env.VITE_API_URL

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
  const [lastRefresh, setLastRefresh] = useState(new Date())
  const [loading, setLoading] = useState(false)
  const [activePage, setActivePage] = useState("Dashboard")

  const pageVisible = (page) => ({
    display: activePage === page ? "block" : "none"
  })

  const navigationItems = [
    { name: "Dashboard", icon: "D" },
    { name: "Fleet", icon: "F" },
    { name: "Routes", icon: "R" },
    { name: "Deliveries", icon: "DL" },
    { name: "Fuel", icon: "F" },
    { name: "Maintenance", icon: "M" },
    { name: "ML Predictions", icon: "ML" },
    { name: "Alerts", icon: "A" }
  ]


  const [vehicleFilter, setVehicleFilter] = useState("All")
  const [routeFilter, setRouteFilter] = useState("All")
  const [statusFilter, setStatusFilter] = useState("All")

  const loadData = async () => {
    setLoading(true)

    try {
      const requests = await Promise.all([
        fetch(`${API}/api/dashboard`).then(r => r.json()),
        fetch(`${API}/api/silver/gps`).then(r => r.json()),
        fetch(`${API}/api/ml/fuel-prediction?distance_km=100&speed_kmh=60&fuel_level=70`).then(r => r.json()),
        fetch(`${API}/api/fleet/live`).then(r => r.json()),
        fetch(`${API}/api/routes`).then(r => r.json()),
        fetch(`${API}/api/fuel`).then(r => r.json()),
        fetch(`${API}/api/fuel/analytics`).then(r => r.json()),
        fetch(`${API}/api/maintenance/analytics`).then(r => r.json()),
        fetch(`${API}/api/maintenance`).then(r => r.json()),
        fetch(`${API}/api/fleet/status`).then(r => r.json()),
        fetch(`${API}/api/delivery-performance`).then(r => r.json())
      ])

      setDashboard(requests[0])
      setSilverGps(requests[1].gps || [])
      setFuelPrediction(requests[2])
      setVehicles(requests[3].vehicles || [])
      setRoutes(requests[4].routes || [])
      setFuel(requests[5].fuel || [])
      setFuelAnalytics(requests[6].fuel_analytics || [])
      setMaintenanceAnalytics(requests[7].maintenance_analytics || [])
      setMaintenance(requests[8].maintenance || [])
      setFleetStatus(requests[9])
      setDeliveryPerformance(requests[10])
      setLastRefresh(new Date())
    } catch (error) {
      console.error("Dashboard refresh error:", error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()

    const interval = setInterval(() => {
      fetch(`${API}/api/silver/gps`)
        .then(r => r.json())
        .then(data => setSilverGps(data.gps || []))
        .catch(error => console.error("GPS refresh error:", error))
    }, 10000)

    return () => clearInterval(interval)
  }, [])

  const liveAlerts = silverGps
    .filter(gps => Number(gps.speed) > 70)
    .sort((a, b) => Number(b.speed) - Number(a.speed))
    .slice(0, 10)

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

  const vehicleTrails = silverGps.reduce((trails, gps) => {
    if (
      gps.latitude == null ||
      gps.longitude == null ||
      !gps.vehicle_id
    ) {
      return trails
    }

    if (!trails[gps.vehicle_id]) {
      trails[gps.vehicle_id] = []
    }

    trails[gps.vehicle_id].push({
      timestamp: new Date(gps.timestamp).getTime(),
      position: [Number(gps.latitude), Number(gps.longitude)]
    })

    return trails
  }, {})

  Object.keys(vehicleTrails).forEach(vehicleId => {
    vehicleTrails[vehicleId] = vehicleTrails[vehicleId]
      .sort((a, b) => a.timestamp - b.timestamp)
      .slice(-15)
      .map(point => point.position)
  })

  const getVehicleStatus = (speed) => {
    const value = Number(speed) || 0
    if (value > 5) return "Moving"
    if (value > 0) return "Idle"
    return "Stopped"
  }

  const filteredVehicles = useMemo(() => {
    return vehicles.filter(vehicle => {
      const vehicleMatch =
        vehicleFilter === "All" || vehicle.vehicle_id === vehicleFilter

      const statusMatch =
        statusFilter === "All" ||
        getVehicleStatus(vehicle.speed) === statusFilter

      return vehicleMatch && statusMatch
    })
  }, [vehicles, vehicleFilter, statusFilter])

  const filteredRoutes = useMemo(() => {
    if (routeFilter === "All") return routes
    return routes.filter(route => route.route_id === routeFilter)
  }, [routes, routeFilter])

  const fleetStatusChart = [
    { name: "Moving", value: fleetStatus?.moving ?? 0 },
    { name: "Idle", value: fleetStatus?.idle ?? 0 },
    { name: "Stopped", value: fleetStatus?.stopped ?? 0 }
  ]

  const maintenanceChart =
    maintenanceAnalytics.length > 0
      ? maintenanceAnalytics
      : [
          { priority: "High", total_cost: 0 },
          { priority: "Medium", total_cost: 0 },
          { priority: "Low", total_cost: 0 }
        ]

  if (!dashboard) {
    return <div className="loading">Loading FleetVision 360...</div>
  }

  return (
    <div className="app">

      <aside className="sidebar">
        <div className="sidebar-logo">
          <div className="logo-mark">FV</div>
          <div>
            <h2>FleetVision</h2>
            <span>360</span>
          </div>
        </div>

        <nav className="sidebar-nav">
          {navigationItems.map((item) => (
            <button
              key={item.name}
              className={`nav-item ${activePage === item.name ? "active" : ""}`}
              onClick={() => setActivePage(item.name)}
            >
              <span className="nav-icon">{item.icon}</span>
              <span>{item.name}</span>
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <span className="online-dot"></span>
          System Online
        </div>
      </aside>

      <main className="main-content">

      <header className="header">
        <div>
          <h1>FleetVision 360</h1>
          <p>Fleet Intelligence & Operations Command Center</p>
        </div>

        <div className="header-right">
          <div className="status">
            <span></span>
            System Online
          </div>

          <button className="refresh-btn" onClick={loadData}>
            {loading ? "Refreshing..." : "Refresh Data"}
          </button>
        </div>
      </header>

      <main>

        <section className="control-panel" style={pageVisible("Dashboard")}>
          <div>
            <label>Vehicle</label>
            <select
              value={vehicleFilter}
              onChange={e => setVehicleFilter(e.target.value)}
            >
              <option value="All">All Vehicles</option>
              {vehicles.map(vehicle => (
                <option key={vehicle.vehicle_id} value={vehicle.vehicle_id}>
                  {vehicle.vehicle_id}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label>Route</label>
            <select
              value={routeFilter}
              onChange={e => setRouteFilter(e.target.value)}
            >
              <option value="All">All Routes</option>
              {routes.map(route => (
                <option key={route.route_id} value={route.route_id}>
                  {route.route_id}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label>Status</label>
            <select
              value={statusFilter}
              onChange={e => setStatusFilter(e.target.value)}
            >
              <option value="All">All Status</option>
              <option value="Moving">Moving</option>
              <option value="Idle">Idle</option>
              <option value="Stopped">Stopped</option>
            </select>
          </div>

          <div className="refresh-info">
            Last refresh:
            <strong>{lastRefresh.toLocaleTimeString()}</strong>
          </div>
        </section>

        <section className="page-title" style={pageVisible("Dashboard")}>
          <div>
            <h2>Executive Overview</h2>
            <p>Real-time fleet performance and operational intelligence</p>
          </div>
        </section>

        <section className="cards" style={pageVisible("Dashboard")}>

          <div className="card">
            <div className="icon">TR</div>
            <div>
              <p>Vehicles</p>
              <h3>{dashboard.vehicles}</h3>
            </div>
          </div>

          <div className="card">
            <div className="icon">DR</div>
            <div>
              <p>Drivers</p>
              <h3>{dashboard.drivers}</h3>
            </div>
          </div>

          <div className="card">
            <div className="icon">RT</div>
            <div>
              <p>Routes</p>
              <h3>{dashboard.routes}</h3>
            </div>
          </div>

          <div className="card">
            <div className="icon">DL</div>
            <div>
              <p>Deliveries</p>
              <h3>{dashboard.deliveries.toLocaleString()}</h3>
            </div>
          </div>

          <div className="card">
            <div className="icon">OT</div>
            <div>
              <p>On-Time Delivery</p>
              <h3>{dashboard.on_time_delivery_rate_percent}%</h3>
            </div>
          </div>

          <div className="card">
            <div className="icon">FC</div>
            <div>
              <p>Fuel Cost</p>
              <h3>&#8377;{Number(dashboard.fuel_cost).toLocaleString("en-IN")}</h3>
            </div>
          </div>

          <div className="card">
            <div className="icon">MT</div>
            <div>
              <p>Maintenance Orders</p>
              <h3>{dashboard.maintenance_work_orders}</h3>
            </div>
          </div>

        </section>

        <section className="analytics-grid" style={pageVisible("Dashboard")}>

          <div className="panel">
            <div className="panel-header">
              <div>
                <h2>Fleet Status</h2>
                <p>Current vehicle operating state</p>
              </div>
            </div>

            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={fleetStatusChart}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  innerRadius={55}
                  label
                >
                  {fleetStatusChart.map((entry, index) => (
                    <Cell key={index} fill={["#f59e0b", "#22c55e", "#ef4444"][index % 3]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>



        </section>

        <section className="panel full-panel" style={pageVisible("Deliveries")}>
          <div className="panel">
            <div className="panel-header">
              <div>
                <h2>Delivery Performance</h2>
                <p>Completed delivery monitoring</p>
              </div>
            </div>

            <div className="performance-grid">
              <div>
                <span>Total</span>
                <strong>{deliveryPerformance?.total_deliveries ?? 0}</strong>
              </div>

              <div>
                <span>Delivered</span>
                <strong>{deliveryPerformance?.delivered ?? 0}</strong>
              </div>

              <div>
                <span>Delayed</span>
                <strong>{deliveryPerformance?.delayed ?? 0}</strong>
              </div>

              <div>
                <span>Performance</span>
                <strong>
                  {deliveryPerformance?.on_time_rate_percent ?? 0}%
                </strong>
              </div>
            </div>

            <ResponsiveContainer width="100%" height={190}>
              <BarChart
                data={[
                  {
                    name: "Deliveries",
                    Delivered: deliveryPerformance?.delivered ?? 0,
                    Delayed: deliveryPerformance?.delayed ?? 0
                  }
                ]}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="Delivered" fill="#22c55e" />
                <Bar dataKey="Delayed" fill="#ef4444" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>


        <section className="analytics-grid" style={pageVisible("Dashboard")}>

          <div className="panel">
            <div className="panel-header">
              <div>
                <h2>Fuel Analytics</h2>
                <p>Consumption by fuel type</p>
              </div>
            </div>

            <ResponsiveContainer width="100%" height={320}>
              <BarChart data={fuelAnalytics}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="fuel_type" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="total_liters" name="Fuel Liters" fill="#06b6d4" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="panel">
            <div className="panel-header">
              <div>
                <h2>Maintenance Cost</h2>
                <p>Maintenance expenditure by priority</p>
              </div>
            </div>

            <ResponsiveContainer width="100%" height={320}>
              <BarChart data={maintenanceChart}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="priority" />
                <YAxis
                  tickFormatter={value =>
                    `${String.fromCharCode(8377)}${(value / 100000).toFixed(0)}L`
                  }
                />
                <Tooltip
                  formatter={value =>
                    `${String.fromCharCode(8377)}${Number(value).toLocaleString("en-IN")}`
                  }
                />
                <Legend />
                <Bar dataKey="total_cost" name="Maintenance Cost" fill="#a855f7" />
              </BarChart>
            </ResponsiveContainer>
          </div>

        </section>

        <section className="panel full-panel" style={pageVisible("Fleet")}>
          <div className="panel-header">
            <div>
              <h2>Live Fleet Map</h2>
              <p>Latest GPS position processed through the Silver layer</p>
            </div>
            <span className="live-badge">LIVE</span>
          </div>

          <MapContainer
            center={[15.3173, 75.7139]}
            zoom={6}
            style={{ height: "500px", width: "100%" }}
          >
            <TileLayer
              attribution="&copy; OpenStreetMap contributors"
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />

            {latestSilverGps.map(gps => {
              const vehicleInfo = vehicles.find(
                v => v.vehicle_id === gps.vehicle_id
              )

              const trail = vehicleTrails[gps.vehicle_id] || []

              return (
                <div key={gps.vehicle_id} style={{ display: "contents" }}>
                  {trail.length > 1 && (
                    <Polyline
                      positions={trail}
                      pathOptions={{
                        color: "#22c55e",
                        weight: 4,
                        opacity: 0.75
                      }}
                    />
                  )}

                  <AnimatedMarker
                    gps={gps}
                    vehicleInfo={vehicleInfo}
                  />

                </div>
              )
            })}
          </MapContainer>
        </section>

        <section className="panel full-panel" style={pageVisible("Fleet")}>
          <div className="panel-header">
            <div>
              <h2>Fleet Operations</h2>
              <p>{filteredVehicles.length} vehicles shown</p>
            </div>
          </div>

          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Vehicle</th>
                  <th>Type</th>
                  <th>Model</th>
                  <th>Depot</th>
                  <th>Speed</th>
                  <th>Status</th>
                  <th>Latitude</th>
                  <th>Longitude</th>
                </tr>
              </thead>

              <tbody>
                {filteredVehicles.slice(0, 30).map(vehicle => (
                  <tr key={vehicle.vehicle_id}>
                    <td><strong>{vehicle.vehicle_id}</strong></td>
                    <td>{vehicle.type}</td>
                    <td>{vehicle.model}</td>
                    <td>{vehicle.depot_id}</td>
                    <td>{vehicle.speed} km/h</td>
                    <td>
                      <span className={`status-pill ${getVehicleStatus(vehicle.speed).toLowerCase()}`}>
                        {getVehicleStatus(vehicle.speed)}
                      </span>
                    </td>
                    <td>{vehicle.latitude}</td>
                    <td>{vehicle.longitude}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="panel full-panel" style={pageVisible("Routes")}>
          <div className="panel-header">
            <div>
              <h2>Routes</h2>
              <p>Route network overview</p>
            </div>
          </div>

          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Route</th>
                  <th>Origin</th>
                  <th>Destination</th>
                  <th>Distance</th>
                  <th>Duration</th>
                </tr>
              </thead>

              <tbody>
                {filteredRoutes.slice(0, 12).map(route => (
                  <tr key={route.route_key}>
                    <td><strong>{route.route_id}</strong></td>
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

        <section className="panel full-panel" style={pageVisible("ML Predictions")}>
          <div className="panel-header">
            <div>
              <h2>ML Fuel Prediction</h2>
              <p>Machine-learning consumption estimate</p>
            </div>
            <span className="ml-badge">ML</span>
          </div>

          <div className="ml-grid">
            <div>
              <span>Distance</span>
              <strong>{fuelPrediction?.distance_km ?? 0} km</strong>
            </div>

            <div>
              <span>Speed</span>
              <strong>{fuelPrediction?.speed_kmh ?? 0} km/h</strong>
            </div>

            <div>
              <span>Fuel Level</span>
              <strong>{fuelPrediction?.fuel_level ?? 0}%</strong>
            </div>

            <div>
              <span>Predicted Consumption</span>
              <strong>{fuelPrediction?.predicted_fuel_consumption ?? 0}</strong>
            </div>
          </div>

          <div className="model-name">
            Model: {fuelPrediction?.model ?? "Loading..."}
          </div>
        </section>

        <section className="panel full-panel" style={pageVisible("Alerts")}>
          <div className="panel-header">
            <div>
              <h2>Operational Alerts</h2>
              <p>Live exceptions detected from incoming GPS data</p>
            </div>
          </div>

          <div className="alerts-grid">
            <div className="alert-card">
              <strong>{liveAlerts.length}</strong>
              <span>Live Overspeed Alerts</span>
            </div>

            <div className="alert-card">
              <strong>{fleetStatus?.stopped ?? 0}</strong>
              <span>Stopped Vehicles</span>
            </div>

            <div className="alert-card">
              <strong>{fleetStatus?.idle ?? 0}</strong>
              <span>Idle Vehicles</span>
            </div>

            <div className="alert-card">
              <strong>{deliveryPerformance?.delayed ?? 0}</strong>
              <span>Delayed Deliveries</span>
            </div>
          </div>

          <div className="table-container" style={{ marginTop: "20px" }}>
            <table>
              <thead>
                <tr>
                  <th>Vehicle</th>
                  <th>Speed</th>
                  <th>Status</th>
                  <th>Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {liveAlerts.length > 0 ? (
                  liveAlerts.map((gps, index) => (
                    <tr key={`${gps.vehicle_id}-${gps.timestamp}-${index}`}>
                      <td>{gps.vehicle_id}</td>
                      <td>{Number(gps.speed).toFixed(1)} km/h</td>
                      <td>
                        <span className="status-pill delayed">Overspeed</span>
                      </td>
                      <td>{gps.timestamp}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="4">
                      No live overspeed alerts detected
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>

        <section className="panel full-panel" style={pageVisible("Fuel")}>
          <div className="panel-header">
            <div>
              <h2>Fuel Records</h2>
              <p>Recent fuel transactions</p>
            </div>
          </div>

          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Vehicle</th>
                  <th>Timestamp</th>
                  <th>Fuel Type</th>
                  <th>Liters</th>
                  <th>Amount</th>
                  <th>Odometer</th>
                </tr>
              </thead>

              <tbody>
                {fuel.slice(0, 15).map(record => (
                  <tr key={record.fuel_key}>
                    <td>{record.vehicle_id}</td>
                    <td>{record.timestamp}</td>
                    <td>{record.fuel_type}</td>
                    <td>{record.liters} L</td>
                    <td>?{Number(record.amount).toLocaleString("en-IN")}</td>
                    <td>{record.odometer_km} km</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="panel full-panel" style={pageVisible("Maintenance")}>
          <div className="panel-header">
            <div>
              <h2>Maintenance Records</h2>
              <p>Recent maintenance activity</p>
            </div>
          </div>

          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Work Order</th>
                  <th>Vehicle</th>
                  <th>Issue</th>
                  <th>Priority</th>
                  <th>Cost</th>
                  <th>Downtime</th>
                </tr>
              </thead>

              <tbody>
                {maintenance.slice(0, 15).map(record => (
                  <tr key={record.maintenance_key}>
                    <td>{record.work_order_id}</td>
                    <td>{record.vehicle_id}</td>
                    <td>{record.issue}</td>
                    <td>{record.priority}</td>
                    <td>?{Number(record.cost).toLocaleString("en-IN")}</td>
                    <td>{record.downtime_hours} hrs</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="panel full-panel" style={pageVisible("Fleet")}>
          <div className="panel-header">
            <div>
              <h2>PySpark Silver GPS</h2>
              <p>
                Processed GPS records:
                <strong> {silverGps.length.toLocaleString()}</strong>
              </p>
            </div>
          </div>

          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Vehicle</th>
                  <th>Timestamp</th>
                  <th>Latitude</th>
                  <th>Longitude</th>
                  <th>Speed</th>
                </tr>
              </thead>

              <tbody>
                {silverGps.slice(0, 10).map((gps, index) => (
                  <tr key={`${gps.vehicle_id}-${gps.timestamp}-${index}`}>
                    <td>{gps.vehicle_id}</td>
                    <td>{gps.timestamp}</td>
                    <td>{gps.latitude}</td>
                    <td>{gps.longitude}</td>
                    <td>{gps.speed} km/h</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

      </main>

      <footer>
        FleetVision 360 • Fleet Intelligence Platform
      </footer>

    </main>
    </div>
  )
}

export default App
