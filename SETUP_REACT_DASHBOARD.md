# راهنمای نصب و راه‌اندازی React Dashboard برای FIDPS

## ✅ تکمیل شده: React.js Dashboard پیاده‌سازی شده

Dashboard React.js با موفقیت پیاده‌سازی شد! این راهنما مراحل نصب و راه‌اندازی را شرح می‌دهد.

---

## 📁 ساختار پروژه

```
frontend-react/
├── src/
│   ├── components/
│   │   ├── Dashboard/          # کامپوننت‌های داشبورد
│   │   │   ├── MetricCard.tsx
│   │   │   ├── SensorDataChart.tsx
│   │   │   ├── AnomalyDistributionChart.tsx
│   │   │   └── RecentAlerts.tsx
│   │   └── Layout/              # کامپوننت‌های Layout
│   │       ├── Layout.tsx
│   │       ├── Navbar.tsx
│   │       └── Sidebar.tsx
│   ├── pages/                   # صفحات اصلی
│   │   ├── Dashboard.tsx
│   │   ├── DamageDiagnosticsPage.tsx  (FR-5.3 ✅)
│   │   ├── RTOControlPage.tsx         (FR-5.5 ✅)
│   │   ├── WellsPage.tsx
│   │   ├── AnomaliesPage.tsx
│   │   ├── DataQualityPage.tsx
│   │   └── SystemPage.tsx
│   ├── store/                   # State management (Zustand)
│   │   ├── useWebSocketStore.ts
│   │   └── useAppStore.ts
│   ├── services/                # API services
│   │   └── api.ts
│   ├── types/                   # TypeScript types
│   │   └── index.ts
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css
├── public/
│   └── oil-well.svg
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
├── Dockerfile
└── nginx.conf
```

---

## 🚀 نصب و راه‌اندازی

### پیش‌نیازها

- Node.js 18+ نصب شده باشد
- npm یا yarn نصب شده باشد

### مراحل نصب

```bash
# 1. ورود به دایرکتوری پروژه
cd frontend-react

# 2. نصب dependencies
npm install

# 3. راه‌اندازی dev server
npm run dev
```

Dashboard در آدرس `http://localhost:5173` در دسترس خواهد بود.

### Build برای Production

```bash
# ساخت build production
npm run build

# مشاهده preview build
npm run preview
```

---

## 🎯 قابلیت‌های پیاده‌سازی شده

### ✅ FR-5.1: React.js Technology
- ✅ پروژه React 18 + TypeScript + Vite
- ✅ Tailwind CSS برای styling
- ✅ Optimized bundle با Vite

### ✅ FR-5.2: Real-Time Monitoring Panel
- ✅ Active Wells Counter
- ✅ Anomalies Today Counter  
- ✅ Critical Alerts Counter
- ✅ Data Quality Score
- ✅ Real-time WebSocket Connection
- ✅ Live Metrics Updates

### ✅ FR-5.3: Damage Diagnostics Panel
- ✅ نمایش تمام 10 نوع Damage (DT-01 to DT-10)
- ✅ Current Prediction Display
- ✅ Probability & Confidence Visualization
- ✅ Contributing Factors Analysis
- ✅ Interactive Status Indicators

### ✅ FR-5.4: TSDB Visualization
- ✅ Time-series Charts با Chart.js
- ✅ Real-time Sensor Data Display
- ✅ Historical Data Support
- ✅ Responsive Chart Components

### ✅ FR-5.5: RTO Control Panel
- ✅ Current vs Recommended Parameters
- ✅ Expected Improvement Metrics
- ✅ Risk Reduction Display
- ✅ Approve/Reject Workflow
- ✅ Real-time Recommendation Queue

### ✅ FR-5.6: Real-Time Data Flow
- ✅ WebSocket Integration
- ✅ Connection Status Indicator
- ✅ Live Anomaly Alerts
- ✅ System Health Monitoring
- ✅ Kafka Pipeline Visualization (UI ready)

---

## 🔌 Integration با Backend

### API Endpoints

Dashboard با این endpoints ادغام شده است:

- `GET /api/v1/dashboard/metrics` - Dashboard KPIs
- `GET /api/v1/wells` - List of wells
- `GET /api/v1/anomalies/recent` - Recent anomalies
- `GET /api/v1/validation/results` - Data quality
- `GET /api/v1/system/status` - System health
- `POST /api/v1/anomalies/{id}/acknowledge` - Acknowledge anomaly

### WebSocket Endpoints

- `ws://localhost:8000/ws/dashboard/{client_id}` - Real-time updates
- Supports subscription types:
  - `all_wells` - All well data
  - `anomalies` - Anomaly alerts
  - `system_metrics` - System metrics

---

## 🎨 UI/UX Features

- ✅ **Modern Design** - Clean, professional interface
- ✅ **Responsive Layout** - Works on mobile, tablet, desktop
- ✅ **Dark/Light Mode** - Theme support (ready)
- ✅ **Real-time Updates** - Live data streaming
- ✅ **Interactive Charts** - Chart.js visualization
- ✅ **Toast Notifications** - User feedback
- ✅ **Loading States** - Skeleton loaders
- ✅ **Error Handling** - Graceful error messages

---

## 📦 Deployment

### Docker Deployment

```bash
# Build image
docker build -t fidps-frontend ./frontend-react

# Run container
docker run -p 80:80 fidps-frontend
```

### Docker Compose

Dashboard در `docker-compose.yml` اضافه شده و به صورت خودکار اجرا می‌شود:

```bash
docker-compose up
```

Dashboard در `http://localhost` در دسترس خواهد بود.

---

## 🔄 Migration از HTML/JS Dashboard

Dashboard قدیمی (HTML/JS) هنوز در `api-dashboard/templates/dashboard.html` موجود است اما React dashboard جدید جایگزین آن شده است.

**نقاط برتری React Dashboard:**
- ✅ Component-based architecture
- ✅ Type safety با TypeScript
- ✅ Better state management
- ✅ Modern build tools (Vite)
- ✅ Code splitting
- ✅ Better performance
- ✅ Easier maintenance

---

## 🧪 Testing

```bash
# Run tests
npm test

# Run linter
npm run lint
```

---

## 📝 Next Steps

برای تکمیل کامل Dashboard، این موارد باقی مانده است:

1. **Integration با InfluxDB** - برای real-time TSDB queries
2. **Complete Wells Page** - نمایش جزئیات wells
3. **Complete Anomalies Page** - مدیریت کامل anomalies
4. **Data Quality Visualizations** - نمودارهای کیفیت داده
5. **System Health Dashboard** - نمایش جزئیات سیستم

---

## 🐛 Troubleshooting

### مشکل: WebSocket اتصال نمی‌گیرد

**راه حل:** مطمئن شوید backend API روی پورت 8000 در حال اجرا است:
```bash
cd api-dashboard
python app.py
```

### مشکل: Cannot resolve module errors

**راه حل:** Dependencies را دوباره نصب کنید:
```bash
rm -rf node_modules package-lock.json
npm install
```

### مشکل: Port 80 already in use

**راه حل:** Port را در docker-compose.yml تغییر دهید:
```yaml
ports:
  - "8080:80"  # از 8080 استفاده کنید
```

---

## 📚 Documentation

- **React Docs:** https://react.dev
- **Vite Docs:** https://vitejs.dev
- **Tailwind CSS:** https://tailwindcss.com
- **Chart.js:** https://www.chartjs.org
- **Zustand:** https://github.com/pmndrs/zustand

---

**نکته:** برای جزئیات بیشتر در مورد API endpoints، لطفاً `api-dashboard/README.md` را مطالعه کنید.

