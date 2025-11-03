# 🚀 Quick Start Guide - React Dashboard

## نصب سریع در 3 مرحله

### 1️⃣ نصب Dependencies
```bash
cd frontend-react
npm install --legacy-peer-deps
```

### 2️⃣ راه‌اندازی Backend
```bash
# از root directory
docker-compose up -d api-dashboard kafka postgres mongodb redis
```

### 3️⃣ اجرای Frontend
```bash
cd frontend-react
npm run dev
```

**✅ Done!** Dashboard در `http://localhost:5173` باز می‌شود.

---

## 🎯 دسترسی‌ها

| Service | URL | Default Credentials |
|---------|-----|---------------------|
| React Dashboard | http://localhost:5173 | - |
| Backend API | http://localhost:8000 | - |
| API Docs | http://localhost:8000/docs | - |
| Grafana | http://localhost:3000 | admin / fidps_grafana_password |
| Prometheus | http://localhost:9090 | - |
| Kafka UI | http://localhost:8080 | - |

---

## 🔍 تست اولیه

بعد از راه‌اندازی:

1. ✅ Dashboard باید بارگذاری شود
2. ✅ Connection status = "Connected" شود
3. ✅ Metrics نمایش داده شوند (اگر داده باشد)
4. ✅ Navigation کار کند

---

## 📝 نکات مهم

- Backend باید روی پورت 8000 باشد
- WebSocket اتصال خودکار برقرار می‌کند
- اگر داده نبود، dashboard با sample data کار می‌کند

---

## 🐳 Docker Option

```bash
# همه چیز در یک دستور
docker-compose up

# Dashboard در http://localhost
# Backend در http://localhost:8000
```

---

**Dashboard آماده استفاده است! 🎉**

