# FIDPS Dashboard Demo

This directory contains live demo dashboards for the FIDPS (Formation Integrity & Damage Prevention System).

## 📁 Available Dashboards

### 1. HTML Dashboard Demo (`dashboard-html-demo.html`)

**A standalone, fully interactive HTML dashboard with real-time monitoring capabilities.**

**Features:**
- ✅ Real-time gauge visualization with SVG
- ✅ Live chart updates (sensor data & noise analysis)
- ✅ Responsive design
- ✅ No backend required - works standalone
- ✅ Modern UI with dark theme

**How to Run:**
```bash
# Simply open the HTML file in any browser
open dashboard-html-demo.html

# Or serve it with a local server
python -m http.server 8080
# Then navigate to: http://localhost:8080/dashboard-html-demo.html
```

**Live Demo:**
- The dashboard updates gauge values every 2 seconds
- Charts refresh every 3 seconds with simulated data
- All visualizations are interactive and responsive

---

### 2. React Dashboard (`frontend-react/`)

**Full-featured React application with complete FIDPS functionality.**

**Features:**
- ✅ Modern React + TypeScript + Tailwind CSS
- ✅ Real-time WebSocket connections
- ✅ Multiple pages (Dashboard, Wells, Anomalies, etc.)
- ✅ Integrated with backend APIs
- ✅ Professional UI/UX

**Pages:**
- **Overview** (`/`) - Main dashboard
- **Wells** (`/wells`) - Well management
- **Real-Time Monitoring** (`/realtime-monitoring`) - Live gauge visualization ⭐ NEW
- **Anomalies** (`/anomalies`) - Anomaly detection
- **Damage Diagnostics** (`/damage-diagnostics`) - ML diagnostics
- **RTO Control** (`/rto-control`) - Optimization control
- **Data Quality** (`/data-quality`) - Quality metrics
- **System** (`/system`) - System status

**How to Run:**
```bash
cd frontend-react
npm install
npm run dev
# Open http://localhost:5173
```

---

## 🎨 Design Philosophy

Both dashboards are inspired by industrial monitoring systems but customized for **FIDPS** (drilling operations):

- **Purpose:** Monitor formation integrity during drilling operations
- **Focus:** Real-time sensor data, anomaly detection, and damage prevention
- **Visualization:** Gauges, charts, and indicators for critical parameters
- **User Experience:** Clean, modern, and responsive

---

## 🔗 Quick Links

### HTML Dashboard
- **File:** `dashboard-html-demo.html`
- **Usage:** Standalone demo or quick prototyping
- **Best for:** Immediate visualization without setup

### React Dashboard
- **Directory:** `frontend-react/`
- **Usage:** Full application with backend integration
- **Best for:** Production deployment and development

---

## 📊 Components Included

### Gauges
- Frequency monitoring
- Pressure gauges (absolute, static, dynamic)
- Temperature sensors
- Flow rate indicators
- Vibration monitors

### Charts
- Real-time sensor data
- Noise analysis
- Anomaly distribution
- Histograms
- Time-series visualization

### Control Panels
- System selection
- Parameter filtering
- Sensor configuration
- Real-time controls

---

## 🚀 Production Deployment

### HTML Dashboard
The HTML dashboard can be deployed using any static hosting:
- GitHub Pages
- Netlify
- Vercel
- Simple HTTP server

### React Dashboard
See `DEPLOYMENT_GUIDE.md` for full deployment instructions including:
- Docker containerization
- Nginx configuration
- Environment variables
- CI/CD pipelines

---

## 🎯 Integration

Both dashboards are designed to integrate with the FIDPS backend:

**Backend Endpoints:**
- `GET /api/v1/dashboard/metrics` - Overview metrics
- `GET /api/v1/sensor-data/latest/:well_id` - Latest sensor data
- `GET /api/v1/anomalies/recent` - Recent anomalies
- `WebSocket /ws` - Real-time data stream

---

## 📝 Notes

- The HTML dashboard is a **standalone demo** and doesn't require the backend
- The React dashboard requires the full FIDPS stack to be running
- Both dashboards use simulated data for demonstration purposes
- Production deployment should connect to real data sources

---

**Last Updated:** 3 November 2025  
**Version:** 1.0.0  
**Status:** ✅ Demo Ready

