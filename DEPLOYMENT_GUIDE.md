# 🚀 FIDPS Deployment Guide

راهنمای کامل نصب و راه‌اندازی سیستم FIDPS

---

## 📋 پیش‌نیازها

### Software Requirements:
- ✅ **Docker Desktop** 4.0+ ([دانلود](https://www.docker.com/products/docker-desktop))
- ✅ **Docker Compose** 2.0+ (معمولاً همراه Docker Desktop)
- ✅ **Git** (اختیاری)
- ✅ **16GB RAM** (حداقل، 32GB توصیه می‌شود)
- ✅ **20GB Storage** (حداقل)
- ✅ **4+ CPU Cores**

### System Requirements:
- Windows 10/11, macOS 10.15+, یا Linux
- Enabled Virtualization (BIOS/UEFI)
- Administrator/root access

---

## 🎯 روش نصب

### روش 1: خودکار (پیشنهادی) ⭐

```powershell
# 1. Docker Desktop را باز کنید و صبر کنید تا کاملاً اجرا شود

# 2. PowerShell را به عنوان Administrator اجرا کنید

# 3. به دایرکتوری پروژه بروید
cd "C:\path\to\FIDPS"

# 4. اجرای اسکریپت
.\start-fidps-complete.ps1
```

این اسکریپت:
- ✅ Docker را بررسی می‌کند
- ✅ تمام سرویس‌ها را build می‌کند
- ✅ دیتابیس‌ها را راه‌اندازی می‌کند
- ✅ همه containers را start می‌کند
- ✅ وضعیت سرویس‌ها را نمایش می‌دهد

**زمان تقریبی:** 10-15 دقیقه (اولین بار)

---

### روش 2: دستی

```powershell
# 1. Build و Start همه سرویس‌ها
docker-compose up -d --build

# 2. بررسی وضعیت
docker-compose ps

# 3. مشاهده لاگ‌ها
docker-compose logs -f
```

---

## ✅ بررسی نصب

### 1. چک کردن Docker:

```powershell
docker version
docker-compose version
```

### 2. چک کردن سرویس‌ها:

```powershell
docker-compose ps
```

همه سرویس‌ها باید **Up** و **healthy** باشند.

### 3. چک کردن Dashboard:

مرورگر باز کنید: **http://localhost**

باید صفحه Dashboard نمایش داده شود.

### 4. چک کردن Health:

```powershell
# API Dashboard
curl http://localhost:8000/health

# RTO Service
curl http://localhost:8002/health

# PdM Service
curl http://localhost:8003/health

# ML Service
curl http://localhost:8080/health
```

همه باید `{"status":"healthy"}` برگردانند.

---

## 🌐 دسترسی به سرویس‌ها

| Service | URL | Credentials |
|---------|-----|-------------|
| **Dashboard** | http://localhost | - |
| API Dashboard | http://localhost:8000 | - |
| API Docs | http://localhost:8000/docs | - |
| RTO Service | http://localhost:8002/docs | - |
| PdM Service | http://localhost:8003/docs | - |
| ML Service | http://localhost:8080/docs | - |
| **Grafana** | http://localhost:3000 | admin / fidps_grafana_password_2024 |
| Prometheus | http://localhost:9090 | - |
| InfluxDB | http://localhost:8086 | fidps_user / fidps_influx_password_2024 |
| Kafka UI | http://localhost:8082 | - |
| MinIO | http://localhost:9001 | fidps_admin / fidps_minio_password_2024 |

---

## 🧪 تست سیستم

### Test 1: RTO Optimization

```powershell
curl -X POST http://localhost:8002/api/v1/rto/optimize `
  -H "Content-Type: application/json" `
  -d '{
    "current_params": {
      "weight_on_bit": 25,
      "rotary_speed": 120,
      "flow_rate": 400,
      "mud_weight": 12.5,
      "depth": 2500
    },
    "damage_type": "DT-02",
    "damage_probability": 0.7,
    "well_id": "WELL-001"
  }'
```

**Expected:** JSON response با recommended parameters

---

### Test 2: PdM Prediction

```powershell
curl -X POST http://localhost:8003/api/v1/pdm/predict `
  -H "Content-Type: application/json" `
  -d '{
    "well_id": "WELL-001",
    "timestamp": "2024-01-01T12:00:00Z",
    "current_risk": 0.65,
    "damage_type": "DT-02",
    "damage_probability": 0.7,
    "depth": 2500,
    "weight_on_bit": 25,
    "rotary_speed": 120,
    "flow_rate": 400,
    "mud_weight": 12.5
  }'
```

**Expected:** JSON response با time-to-failure و preventative actions

---

### Test 3: Dashboard API

```powershell
# Get Wells
curl http://localhost:8000/api/v1/wells

# Get Anomalies
curl http://localhost:8000/api/v1/anomalies/active

# System Status
curl http://localhost:8000/api/v1/system/status
```

---

## 📊 Monitoring Setup

### 1. Grafana Login:

1. مرورگر: **http://localhost:3000**
2. Username: `admin`
3. Password: `fidps_grafana_password_2024`
4. Import dashboards از: `monitoring/grafana/`

### 2. Prometheus:

- URL: **http://localhost:9090**
- Explore: `http://localhost:9090/graph`
- Query example: `up`

### 3. InfluxDB:

- URL: **http://localhost:8086**
- Login: `fidps_user` / `fidps_influx_password_2024`

---

## 🛠️ مدیریت

### مشاهده لاگ‌ها:

```powershell
# همه سرویس‌ها
docker-compose logs -f

# یک سرویس خاص
docker-compose logs -f api-dashboard
docker-compose logs -f rto-service
docker-compose logs -f pdm-service
docker-compose logs -f ml-anomaly-detection
```

### متوقف کردن:

```powershell
# متوقف کردن همه
docker-compose down

# متوقف کردن یک سرویس
docker-compose stop rto-service
```

### راه‌اندازی مجدد:

```powershell
# راه‌اندازی مجدد یک سرویس
docker-compose restart rto-service

# راه‌اندازی مجدد همه
docker-compose restart
```

### کاملاً پاک کردن:

```powershell
# متوقف و حذف containers و volumes
docker-compose down -v

# حذف images
docker-compose down --rmi all
```

---

## 🐛 Troubleshooting

### مشکل 1: Port در حال استفاده

```powershell
# پیدا کردن process
netstat -ano | findstr :8000

# Kill process
taskkill /PID <pid> /F
```

### مشکل 2: Docker Desktop نمی‌چرخد

**راه حل:**
1. Docker Desktop را restart کنید
2. Resources را افزایش دهید (Settings > Resources)
3. WSL2 را بررسی کنید (Windows)
4. Hyper-V را enable کنید (Windows)

### مشکل 3: Service نمی‌چرخد

```powershell
# مشاهده لاگ
docker-compose logs -f <service-name>

# بررسی وضعیت
docker-compose ps

# راه‌اندازی مجدد
docker-compose restart <service-name>

# کاملاً rebuild
docker-compose up -d --build --force-recreate <service-name>
```

### مشکل 4: Database Connection Failed

```powershell
# بررسی logs databases
docker-compose logs postgres
docker-compose logs mongodb

# راه‌اندازی مجدد databases
docker-compose restart postgres mongodb

# صبر کنید
Start-Sleep -Seconds 20
```

### مشکل 5: Out of Memory

**راه حل:**
1. Docker Desktop > Settings > Resources
2. Memory: **16GB** (minimum)
3. CPUs: **4** (minimum)
4. Apply & Restart

---

## 📈 Performance Tips

### 1. Resource Allocation:

- **RAM**: 16GB+ توصیه می‌شود
- **CPU**: 4+ cores
- **Disk**: SSD بهتر از HDD

### 2. Docker Settings:

```json
{
  "memoryMiB": 16384,
  "cpus": 4,
  "diskSizeMiB": 51200
}
```

### 3. Network:

از Bridge network استفاده کنید (پیش‌فرض در docker-compose.yml)

---

## 🔐 Security Notes

### Development Environment:
- همه credentials در docker-compose.yml هستند (فقط development)
- در production از secrets management استفاده کنید

### Production Deployment:
1. Environment variables را externalize کنید
2. SSL/TLS برای HTTPS
3. Authentication برای APIs
4. Network isolation

---

## 📞 Support

### Documentation:
- `QUICK_START.md` - راهنمای سریع
- `IMPLEMENTATION_SUMMARY.md` - خلاصه پیاده‌سازی
- `PROJECT_STATUS.md` - وضعیت پروژه
- `README.md` - SRS و مستندات کامل

### Logs Location:

```
logs/
├── api-dashboard/
├── rto-service/
├── pdm-service/
├── ml-anomaly-detection/
└── ...
```

---

## ✅ Checklist نهایی

قبل از استفاده، مطمئن شوید:

- [ ] Docker Desktop اجرا شده
- [ ] همه سرویس‌ها Up هستند
- [ ] Dashboard در http://localhost باز می‌شود
- [ ] همه health checks موفق هستند
- [ ] Grafana login می‌شود
- [ ] API tests موفق هستند

---

**سیستم آماده استفاده است! 🎉**

برای سوالات یا مشکلات، لاگ‌ها را بررسی کنید: `docker-compose logs -f`

