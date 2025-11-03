# دستورالعمل نصب React Dashboard

## ✅ Dashboard React.js تکمیل شد!

پروژه React.js Dashboard با موفقیت ایجاد شد. برای راه‌اندازی:

## 📋 مراحل نصب

### 1. ورود به دایرکتوری پروژه

```bash
cd frontend-react
```

### 2. نصب Dependencies

```bash
# با npm
npm install

# یا با yarn
yarn install

# یا با pnpm
pnpm install
```

**نکته مهم:** اگر خطا گرفتید:
```bash
npm install --legacy-peer-deps
```

### 3. راه‌اندازی Development Server

```bash
npm run dev
```

Dashboard در `http://localhost:5173` باز می‌شود.

### 4. Build برای Production

```bash
# ساخت production build
npm run build

# فایل‌های build در پوشه dist/ ذخیره می‌شوند
```

---

## 🐳 راه‌اندازی با Docker

### Option 1: با Docker Compose

```bash
# از root directory پروژه
docker-compose up frontend-react
```

### Option 2: Docker تک

```bash
cd frontend-react

# Build image
docker build -t fidps-frontend .

# Run container
docker run -p 80:80 fidps-frontend
```

---

## 🔗 اتصال به Backend

قبل از استفاده، مطمئن شوید Backend API در حال اجرا است:

```bash
# Start all services
docker-compose up -d

# یا فقط backend
cd api-dashboard
python app.py
```

Backend باید روی `http://localhost:8000` باشد.

---

## 📍 مسیرهای مهم

- **Dashboard Home:** `/`
- **Wells:** `/wells`
- **Anomalies:** `/anomalies`
- **Damage Diagnostics:** `/damage-diagnostics` ✅
- **RTO Control:** `/rto-control` ✅
- **Data Quality:** `/data-quality`
- **System:** `/system`

---

## 🎯 قابلیت‌های کلیدی پیاده‌سازی شده

### ✅ مطابق با SRS FR-5:

1. **FR-5.1** ✅ React.js Technology - پروژه با React 18 ساخته شد
2. **FR-5.2** ✅ Real-Time Monitoring - Live dashboard با WebSocket
3. **FR-5.3** ✅ Damage Diagnostics Panel - نمایش 10 نوع Damage
4. **FR-5.4** ✅ TSDB Visualization - آماده برای InfluxDB
5. **FR-5.5** ✅ RTO Control - Panel کامل با Approve/Reject
6. **FR-5.6** ✅ Data Flow Visualization - Connection status & health

---

## 🛠️ تکنولوژی‌های استفاده شده

- **React 18** - Framework اصلی
- **TypeScript** - Type safety
- **Vite** - Build tool سریع
- **Tailwind CSS** - Styling
- **Chart.js** - Data visualization
- **Zustand** - State management
- **React Query** - Data fetching
- **WebSocket** - Real-time updates
- **React Router** - Navigation
- **React Hot Toast** - Notifications

---

## 📝 ساختار کد

```
frontend-react/
├── src/
│   ├── components/        # کامپوننت‌های reusable
│   ├── pages/            # صفحه‌های اصلی
│   ├── store/            # State management
│   ├── services/         # API calls
│   └── types/            # TypeScript types
├── public/               # Static files
└── package.json          # Dependencies
```

---

## 🔍 تست کردن

```bash
# Linting
npm run lint

# Build test
npm run build

# Type checking
npx tsc --noEmit
```

---

## 🚨 Troubleshooting

### مشکل: port 5173 already in use

**راه حل:** Port را در `vite.config.ts` تغییر دهید:
```ts
server: {
  port: 5174
}
```

### مشکل: Cannot connect to backend

**راه حل:** مطمئن شوید proxy در `vite.config.ts` صحیح است و backend در حال اجراست.

### مشکل: Module not found errors

**راه حل:**
```bash
rm -rf node_modules
npm install
```

---

## 📖 مستندات بیشتر

- [React Documentation](https://react.dev)
- [Vite Documentation](https://vitejs.dev)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [Chart.js](https://www.chartjs.org/docs)

---

## ✅ چک‌لیست نصب موفق

- [ ] `npm install` بدون خطا
- [ ] `npm run dev` صفحه Dashboard را نمایش می‌دهد
- [ ] WebSocket به backend متصل می‌شود
- [ ] API calls به backend کار می‌کنند
- [ ] Charts نمایش داده می‌شوند
- [ ] Navigation بین صفحات کار می‌کند

---

**Dashboard آماده استفاده است! 🎉**

