# FIDPS Dataset Generator

## نمای کلی

این مجموعه اسکریپت‌ها برای تولید دیتاست جامع سیستم پیشگیری از آسیب یکپارچگی سازند (FIDPS) طراحی شده است. دیتاست شامل داده‌های سنسور LWD/MWD و تصاویر مرتبط گمانه با انواع آسیب‌های سازندی می‌باشد.

## ویژگی‌ها

### 🔧 داده‌های سنسور
- داده‌های LWD/MWD شبیه‌سازی شده
- شامل 20+ پارامتر عملیاتی
- شبیه‌سازی انواع آسیب‌های سازندی
- تشخیص ناهنجاری و محاسبه ریسک
- فرمت‌های مختلف خروجی (CSV, Parquet, JSON)

### 🖼️ داده‌های تصویری
- تصاویر مصنوعی گمانه
- شبیه‌سازی 9 نوع آسیب سازندی
- ابعاد متغیر بر اساس عمق
- ارتباط با داده‌های سنسور

### 🔗 ارتباط داده‌ها
- ارتباط زمانی بین تصاویر و داده‌های سنسور
- متادیتای جامع
- فایل‌های mapping برای ردیابی ارتباطات

## ساختار فایل‌ها

```
dataset/
├── data_generator.py           # تولید داده‌های سنسور LWD/MWD
├── make_dataset.py            # تولید تصاویر گمانه
├── unified_dataset_generator.py # تولید یکپارچه داده‌ها
├── generate_fidps_dataset.py  # اسکریپت اصلی
├── fidps_config.json         # فایل پیکربندی (ایجاد خودکار)
└── README.md                 # این فایل
```

## نصب و راه‌اندازی

### پیش‌نیازها

```bash
pip install pandas numpy matplotlib opencv-python pyarrow tqdm
```

### استفاده سریع

```bash
# تولید دیتاست با تنظیمات پیش‌فرض
python generate_fidps_dataset.py

# تولید برای 7 روز با 50 تصویر در روز
python generate_fidps_dataset.py --days 7 --images 50

# استفاده از فایل پیکربندی سفارشی
python generate_fidps_dataset.py --config my_config.json
```

## راهنمای استفاده

### 1. ایجاد فایل پیکربندی

```bash
python generate_fidps_dataset.py --create-config
```

این دستور فایل `fidps_config.json` را با تنظیمات پیش‌فرض ایجاد می‌کند.

### 2. ویرایش پیکربندی

فایل `fidps_config.json` را ویرایش کنید:

```json
{
  "time_settings": {
    "start_date": "2024-01-01",
    "duration_days": 30
  },
  "image_settings": {
    "images_per_day": 20,
    "damage_probability": 0.7
  },
  "output_settings": {
    "base_path": "my_fidps_dataset"
  }
}
```

### 3. تولید دیتاست

```bash
# بررسی پیکربندی بدون تولید
python generate_fidps_dataset.py --dry-run

# تولید دیتاست
python generate_fidps_dataset.py
```

## گزینه‌های خط فرمان

| گزینه | توضیح |
|--------|-------|
| `--config, -c` | مسیر فایل پیکربندی |
| `--create-config` | ایجاد فایل پیکربندی پیش‌فرض |
| `--output, -o` | دایرکتوری خروجی |
| `--days, -d` | مدت زمان به روز |
| `--images, -i` | تعداد تصاویر در روز |
| `--start-date, -s` | تاریخ شروع (YYYY-MM-DD) |
| `--quiet, -q` | حذف خروجی‌های تفصیلی |
| `--dry-run` | نمایش پیکربندی بدون تولید |

## ساختار خروجی

```
fidps_dataset/
├── sensor_data/              # داده‌های سنسور
│   ├── real_time_data.csv
│   ├── historical_data.parquet
│   ├── anomaly_data.json
│   └── ml_training_data.parquet
├── images/                   # تصاویر گمانه
│   ├── borehole_00001.png
│   ├── borehole_00002.png
│   └── ...
├── metadata/                 # متادیتا
│   └── image_metadata.json
├── correlations/            # ارتباطات
│   ├── image_sensor_correlations.csv
│   └── image_sensor_correlations.json
├── dataset_summary.json     # خلاصه دیتاست
└── generation_config.json   # پیکربندی استفاده شده
```

## انواع آسیب‌های سازندی

1. **Clay Swelling** - تورم رس
2. **Drilling Induced** - آسیب ناشی از حفاری
3. **Fluid Loss** - از دست دادن سیال
4. **Scale Formation** - تشکیل رسوب
5. **Emulsion Blockage** - انسداد امولسیون
6. **Rock Fluid Interaction** - تعامل سنگ-سیال
7. **Completion Damage** - آسیب تکمیل
8. **Stress Corrosion** - خوردگی تنشی
9. **Surface Filtration** - فیلتراسیون سطحی

## پارامترهای سنسور

### پارامترهای اصلی
- فشار حلقوی (Annulus Pressure)
- دمای ته چاه (Bottomhole Temperature)
- ویسکوزیته گل (Mud Viscosity)
- نرخ جریان (Flow Rate)
- فشار پمپ (Pump Pressure)
- ارتعاشات (Vibration X, Y, Z)
- گشتاور (Torque)
- وزن روی بیت (Weight on Bit)

### پارامترهای محاسبه شده
- امتیاز ریسک آسیب (Damage Risk Score)
- شاخص کیفیت (Quality Index)
- وضعیت تجهیزات (Equipment Status)
- آلارم‌ها (Alarms)

## مثال‌های کاربرد

### تولید دیتاست کوچک برای تست

```bash
python generate_fidps_dataset.py --days 3 --images 10 --output test_dataset
```

### تولید دیتاست بزرگ برای آموزش مدل

```bash
python generate_fidps_dataset.py --days 90 --images 100 --output training_dataset
```

### استفاده در کد Python

```python
from unified_dataset_generator import UnifiedDatasetGenerator
from datetime import datetime

generator = UnifiedDatasetGenerator()
sensor_data, images, correlations = generator.generate_unified_dataset(
    start_date=datetime(2024, 1, 1),
    duration_days=7,
    num_images_per_day=20,
    output_path="my_dataset"
)
```

## نکات مهم

1. **حافظه**: تولید تصاویر زیاد نیاز به حافظه بالا دارد
2. **زمان**: تولید هر تصویر حدود 1-2 ثانیه زمان می‌برد
3. **فضای ذخیره**: هر تصویر حدود 100-500 کیلوبایت حجم دارد
4. **ارتباطات**: تصاویر بر اساس زمان و ریسک آسیب با داده‌های سنسور مرتبط می‌شوند

## عیب‌یابی

### خطاهای رایج

**خطا: ModuleNotFoundError**
```bash
pip install -r requirements.txt
```

**خطا: Memory Error**
- تعداد تصاویر در روز را کاهش دهید
- مدت زمان تولید را کوتاه‌تر کنید

**خطا: Invalid date format**
- از فرمت YYYY-MM-DD استفاده کنید

## مشارکت

برای گزارش باگ یا پیشنهاد بهبود، لطفاً issue ایجاد کنید.

## مجوز

این پروژه تحت مجوز MIT منتشر شده است.