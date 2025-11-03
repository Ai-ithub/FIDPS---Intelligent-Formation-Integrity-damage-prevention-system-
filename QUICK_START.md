# 🚀 FIDPS Quick Start Guide

راهنمای سریع راه‌اندازی سیستم FIDPS

---

## ⚙️ پیش‌نیازها

### نرم‌افزارهای مورد نیاز:
1. **Docker Desktop** - [دانلود از اینجا](https://www.docker.com/products/docker-desktop)
2. **Docker Compose** - معمولاً همراه Docker Desktop نصب می‌شود
3. **Git** - برای clone کردن پروژه (اختیاری)

### سیستم مورد نیاز:
- **OS**: Windows 10/11, macOS, Linux
- **RAM**: حداقل 8GB (16GB توصیه می‌شود)
- **Storage**: حداقل 20GB فضای خالی
- **CPU**: حداقل 4 core

---

## 📥 نصب و راه‌اندازی

### روش 1: راه‌اندازی سریع (پیشنهادی)

```powershell
# 1. Clone پروژه (یا از فایل زیپ extract کنید)
git clone https://github.com/your-repo/FIDPS.git
cd FIDPS

# 2. Docker Desktop را باز کنید و صبر کنید تا به طور کامل راه‌اندازی شود

# 3. اجرای اسکریپت خودکار
.\start-all.ps1
```

### روش 2: راه‌اندازی دستی

```powershell
# 1. شروع infrastructure services
docker-compose up -d zookeeper postgres mongodb redis minio influxdb

# 2. شروع Kafka
docker-compose up -d kafka kafka-connect

# 3. شروع monitoring
docker-compose up -d prometheus grafana

# 4. شروع ML services
docker-compose up -d ml-anomaly-detection flink-validation

# 5. شروع RTO و PdM
docker-compose up -d rto-service pdm-service influxdb-connector

# 6. شروع Dashboard
docker-compose up -d api-dashboard frontend-react kafka-ui
```

---

## ✅ بررسی نصب

### 1. چک کردن وضعیت سرویس‌ها:

```powershell
docker-compose ps
```

همه سرویس‌ها باید `Up` باشند.

### 2. تست Dashboard:

مرورگر را باز کنید: **http://localhost**

باید صفحه Dashboard نمایش داده شود.

### 3. تست API:

```powershell
# Health check
curl http://localhost:8000/health

# RTO Service
curl http://localhost:8002/health

# PdM Service
curl http://localhost:8003/health

# ML Service
curl http://localhost:8080/health
```

---

## 🌐 دسترسی به سرویس‌ها

| سرویس | URL | Credentials |
|--------|-----|-------------|
| **React Dashboard** | http://localhost | - |
| **API Dashboard** | http://localhost:8000 | - |
| **API Docs** | http://localhost:8000/docs | - |
| **RTO Service** | http://localhost:8002 | - |
| **PdM Service** | http://localhost:8003 | - |
| **ML Service** | http://localhost:8080 | - |
| **Grafana** | http://localhost:3000 | admin / fidps_grafana_password_2024 |
| **Prometheus** | http://localhost:9090 | - |
| **InfluxDB** | http://localhost:8086 | fidps_user / fidps_influx_password_2024 |
| **Kafka UI** | http://localhost:8082 | - |
| **MinIO** | http://localhost:9001 | fidps_admin / fidps_minio_password_2024 |

---

## 🛠️ مدیریت سرویس‌ها

### مشاهده لاگ‌ها:

```powershell
# همه سرویس‌ها
docker-compose logs -f

# یک سرویس خاص
docker-compose logs -f api-dashboard
docker-compose logs -f rto-service
docker-compose logs -f pdm-service
```

### متوقف کردن:

```powershell
# متوقف کردن همه
docker-compose down

# متوقف کردن فقط یک سرویس
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
# متوقف و حذف همه containers و volumes
docker-compose down -v

# حذف images
docker-compose down --rmi all
```

---

## 📊 تست APIها

### RTO Service:

```bash
curl -X POST http://localhost:8002/api/v1/rto/optimize \
  -H "Content-Type: application/json" \
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

### PdM Service:

```bash
curl -X POST http://localhost:8003/api/v1/pdm/predict \
  -H "Content-Type: application/json" \
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

---

## 🐛 رفع مشکلات

### مشکل: Port در حال استفاده است

**راه حل:**
```powershell
# بررسی چه چیزی از port استفاده می‌کند
netstat -ano | findstr :8000

# یا در docker-compose.yml port را تغییر دهید
```

### مشکل: Docker Desktop نمی‌چرخد

**راه حل:**
1. Docker Desktop را Restart کنید
2. مطمئن شوید WSL2 نصب است (Windows)
3. Resources Docker را افزایش دهید (Settings > Resources)

### مشکل: سرویس start نمی‌شود

**راه حل:**
```powershell
# مشاهده لاگ‌های دقیق
docker-compose logs -f [service-name]

# بررسی healthcheck
docker-compose ps

# راه‌اندازی مجدد
docker-compose restart [service-name]
```

### مشکل: Database connection failed

**راه حل:**
```powershell
# صبر کنید تا databases کاملاً start شوند
docker-compose logs postgres
docker-compose logs mongodb

# بررسی credentials در docker-compose.yml
```

---

## 📚 اطلاعات بیشتر

- **مستندات کامل**: `README.md`
- **خلاصه پیاده‌سازی**: `IMPLEMENTATION_SUMMARY.md`
- **وضعیت پروژه**: `PROJECT_STATUS.md`
- **React Dashboard**: `FRONTEND_QUICKSTART.md`

---

## 🆘 نیاز به کمک؟

1. لاگ‌ها را بررسی کنید: `docker-compose logs -f`
2. مطمئن شوید Docker Desktop کاملاً راه‌اندازی شده
3. مطمئن شوید RAM و CPU کافی دارید
4. همه port‌ها آزاد هستند

---

**موفق باشید! 🎉**

