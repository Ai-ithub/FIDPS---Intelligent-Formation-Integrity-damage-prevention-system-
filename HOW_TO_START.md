# 🚀 راهنمای نصب و راه‌اندازی FIDPS

## ⚠️ مهم: Docker Desktop نصب نیست!

روی سیستم شما **Docker Desktop** نصب نیست. برای راه‌اندازی FIDPS باید ابتدا Docker را نصب کنید.

---

## 📥 گام 1: نصب Docker Desktop

### Windows:

1. **دانلود Docker Desktop:**
   - به آدرس بروید: **https://www.docker.com/products/docker-desktop**
   - دکمه **"Download for Windows"** را کلیک کنید
   - فایل installer را دانلود کنید (Docker Desktop Installer.exe)

2. **نصب:**
   - فایل دانلود شده را اجرا کنید
   - گزینه **"Use WSL 2 instead of Hyper-V"** را انتخاب کنید (توصیه می‌شود)
   - مراحل نصب را تکمیل کنید
   - سیستم را **Restart** کنید

3. **راه‌اندازی:**
   - Docker Desktop را باز کنید
   - صبر کنید تا docker daemon کاملاً start شود (یک whale icon در system tray)
   - WSL 2 را نصب کرده باشید

---

## 🏃 گام 2: راه‌اندازی FIDPS

پس از نصب Docker Desktop:

```powershell
# از PowerShell یا CMD
cd "C:\Users\asus\Documents\companies\ithub\AI\products\clones\fidps\FIDPS---Intelligent-Formation-Integrity-damage-prevention-system-"

# روش 1: اسکریپت خودکار (پیشنهادی)
.\start-fidps-complete.ps1

# یا روش 2: Docker Compose مستقیم
docker compose up -d --build
```

---

## ⏱️ زمان راه‌اندازی

- **اولین بار:** 15-20 دقیقه (برای build کردن images)
- **دفعات بعدی:** 3-5 دقیقه

---

## ✅ بررسی نصب

```powershell
# بررسی وضعیت سرویس‌ها
docker compose ps

# مشاهده لاگ‌ها
docker compose logs -f
```

---

## 🌐 دسترسی

بعد از راه‌اندازی، مرورگر را باز کنید:

- **Main Dashboard:** http://localhost
- **API Dashboard:** http://localhost:8000
- **RTO Service:** http://localhost:8002/docs
- **PdM Service:** http://localhost:8003/docs
- **Grafana:** http://localhost:3000
- **Prometheus:** http://localhost:9090

---

## 📚 اطلاعات بیشتر

برای جزئیات بیشتر به این فایل‌ها مراجعه کنید:

- `DEPLOYMENT_GUIDE.md` - راهنمای کامل deployment
- `QUICK_START.md` - Quick start guide
- `IMPLEMENTATION_SUMMARY.md` - خلاصه پیاده‌سازی
- `start-fidps-complete.ps1` - اسکریپت خودکار

---

**نکته:** اگر Docker Desktop نصب دارید ولی از PATH نیست، احتمالاً باید PowerShell را restart کنید.

