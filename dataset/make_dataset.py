import numpy as np
import matplotlib.pyplot as plt
import os
from tqdm import tqdm
import shutil
import json
from datetime import datetime
from enum import Enum
import cv2

class FormationDamageType(Enum):
    CLAY_SWELLING = "clay_swelling"
    DRILLING_INDUCED = "drilling_induced"
    FLUID_LOSS = "fluid_loss"
    SCALE_FORMATION = "scale_formation"
    EMULSION_BLOCKAGE = "emulsion_blockage"
    ROCK_FLUID_INTERACTION = "rock_fluid_interaction"
    COMPLETION_DAMAGE = "completion_damage"
    STRESS_CORROSION = "stress_corrosion"
    SURFACE_FILTRATION = "surface_filtration"
    NORMAL = "normal"

def add_well_log_features(img):
    height, width, _ = img.shape
    
    # اضافه کردن خط عمودی نشانگر عمق در سمت چپ
    img[:, 0:3, :] = (0.1, 0.1, 0.1)
    
    # اضافه کردن نشانگرهای عمق
    for i in range(0, height, height//10):
        img[i:i+2, 0:10, :] = (0.1, 0.1, 0.1)
        
    # اضافه کردن خطوط افقی نازک برای نشان دادن مقیاس
    for i in range(0, height, height//20):
        img[i:i+1, :, :] *= 0.8
    
    return img

def add_formation_damage(img, damage_type, severity=0.5):
    """اضافه کردن انواع مختلف آسیب‌های سازندی به تصویر"""
    height, width, _ = img.shape
    damaged_img = img.copy()
    
    if damage_type == FormationDamageType.CLAY_SWELLING:
        # تورم رس - ایجاد نواحی تیره و متورم
        for _ in range(int(severity * 10)):
            y = np.random.randint(0, height-20)
            x = np.random.randint(0, width-10)
            h = np.random.randint(10, 30)
            w = np.random.randint(5, 15)
            damaged_img[y:y+h, x:x+w, :] *= 0.3
            
    elif damage_type == FormationDamageType.DRILLING_INDUCED:
        # آسیب مکانیکی - ایجاد شکستگی‌ها و ترک‌ها
        for _ in range(int(severity * 8)):
            y1 = np.random.randint(0, height)
            x1 = np.random.randint(0, width)
            length = np.random.randint(20, 80)
            angle = np.random.uniform(0, 2*np.pi)
            y2 = int(np.clip(y1 + length * np.sin(angle), 0, height-1))
            x2 = int(np.clip(x1 + length * np.cos(angle), 0, width-1))
            cv2.line(damaged_img, (x1, y1), (x2, y2), (0, 0, 0), thickness=2)
            
    elif damage_type == FormationDamageType.FLUID_LOSS:
        # از دست دادن سیال - ایجاد نواحی متخلخل
        for _ in range(int(severity * 15)):
            y = np.random.randint(0, height-5)
            x = np.random.randint(0, width-5)
            radius = np.random.randint(2, 8)
            cv2.circle(damaged_img, (x, y), radius, (0.8, 0.8, 0.8), -1)
            
    elif damage_type == FormationDamageType.SCALE_FORMATION:
        # تشکیل رسوب - ایجاد لایه‌های سفید
        for _ in range(int(severity * 12)):
            y = np.random.randint(0, height-3)
            x = np.random.randint(0, width)
            w = np.random.randint(10, width//2)
            damaged_img[y:y+3, x:min(x+w, width), :] = (0.9, 0.9, 0.9)
            
    elif damage_type == FormationDamageType.EMULSION_BLOCKAGE:
        # انسداد امولسیون - ایجاد نواحی کدر
        for _ in range(int(severity * 6)):
            y = np.random.randint(0, height-15)
            x = np.random.randint(0, width-15)
            h = np.random.randint(10, 25)
            w = np.random.randint(10, 25)
            noise = np.random.normal(0.5, 0.1, (h, w, 3))
            damaged_img[y:y+h, x:x+w, :] = np.clip(noise, 0, 1)
            
    elif damage_type == FormationDamageType.STRESS_CORROSION:
        # خوردگی تنشی - ایجاد نقاط خوردگی
        for _ in range(int(severity * 20)):
            y = np.random.randint(0, height)
            x = np.random.randint(0, width)
            radius = np.random.randint(1, 4)
            cv2.circle(damaged_img, (x, y), radius, (0.4, 0.2, 0.1), -1)
    
    return damaged_img

def generate_synthetic_borehole_image(height=256, width=128, num_layers=10, add_features=True):
    img = np.zeros((height, width, 3))
    layer_height = height // num_layers
    rock_colors = [
        (0.6, 0.4, 0.2),   # Shale
        (0.9, 0.8, 0.6),   # Limestone
        (0.7, 0.7, 0.7),   # Sandstone
        (0.4, 0.6, 0.2),   # Siltstone
        (0.2, 0.2, 0.2),   # Basalt
    ]
    
    # اضافه کردن ویژگی‌های بیشتر برای واقعی‌تر شدن تصاویر
    for i in range(num_layers):
        color = rock_colors[np.random.randint(0, len(rock_colors))]
        start = i * layer_height
        end = (i + 1) * layer_height
        
        # تغییر ضخامت لایه‌ها به صورت تصادفی
        if i < num_layers - 1 and np.random.random() > 0.7:
            thickness_variation = np.random.randint(-layer_height//4, layer_height//4)
            end += thickness_variation
            if end <= start:
                end = start + layer_height // 3
        
        img[start:end, :, :] = color
        
        # اضافه کردن بافت به لایه‌ها
        texture = np.random.normal(0, 0.05, (end-start, width, 3))
        img[start:end, :, :] += texture
        
        # اضافه کردن ترک‌ها و شکستگی‌ها
        if np.random.random() > 0.8:
            crack_pos = np.random.randint(0, width)
            crack_width = np.random.randint(1, 5)
            crack_length = np.random.randint(5, end-start)
            crack_start = np.random.randint(start, end-crack_length)
            img[crack_start:crack_start+crack_length, crack_pos:crack_pos+crack_width, :] *= 0.7
    
    # اضافه کردن نویز به کل تصویر
    img += np.random.normal(0, 0.02, img.shape)
    img = np.clip(img, 0, 1)
    
    if add_features:
        img = add_well_log_features(img)
    
    return img

def generate_enhanced_borehole_dataset(num_images=2000, output_dir="enhanced_borehole_dataset"):
    """تولید دیتاست پیشرفته با انواع آسیب‌های سازندی"""
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(f"{output_dir}/images", exist_ok=True)
    os.makedirs(f"{output_dir}/metadata", exist_ok=True)
    
    damage_types = list(FormationDamageType)
    dataset_metadata = []
    
    for i in tqdm(range(num_images), desc="Generating enhanced borehole images"):
        # تنوع در ابعاد تصویر
        height = np.random.choice([256, 320, 384, 512])
        width = np.random.choice([128, 160, 192, 256])
        num_layers = np.random.randint(5, 20)
        
        # تولید تصویر پایه
        img = generate_synthetic_borehole_image(height=height, width=width, num_layers=num_layers)
        
        # انتخاب نوع آسیب (70% احتمال آسیب، 30% نرمال)
        has_damage = np.random.random() < 0.7
        damage_type = FormationDamageType.NORMAL
        damage_severity = 0.0
        
        if has_damage:
            damage_type = np.random.choice(damage_types[:-1])  # حذف NORMAL از انتخاب
            damage_severity = np.random.uniform(0.2, 0.9)
            img = add_formation_damage(img, damage_type, damage_severity)
        
        # ذخیره تصویر
        image_filename = f"borehole_{i:05d}.png"
        plt.imsave(f"{output_dir}/images/{image_filename}", img)
        
        # ایجاد متادیتا
        metadata = {
            "image_id": i,
            "filename": image_filename,
            "timestamp": datetime.now().isoformat(),
            "dimensions": {
                "height": height,
                "width": width
            },
            "formation_properties": {
                "num_layers": num_layers,
                "depth_range": [i * 10, (i + 1) * 10]  # فرضی
            },
            "damage_info": {
                "has_damage": has_damage,
                "damage_type": damage_type.value,
                "severity": damage_severity,
                "damage_location": "distributed" if has_damage else "none"
            },
            "data_quality": {
                "resolution": "high",
                "noise_level": "low",
                "contrast": "normal"
            }
        }
        
        dataset_metadata.append(metadata)
        
        # ذخیره متادیتای فردی
        with open(f"{output_dir}/metadata/{image_filename.replace('.png', '_meta.json')}", "w") as f:
            json.dump(metadata, f, indent=2)
    
    # ذخیره متادیتای کل دیتاست
    with open(f"{output_dir}/dataset_metadata.json", "w") as f:
        json.dump({
            "dataset_info": {
                "name": "Enhanced Borehole Formation Damage Dataset",
                "version": "1.0",
                "creation_date": datetime.now().isoformat(),
                "total_images": num_images,
                "damage_distribution": {dt.value: sum(1 for m in dataset_metadata if m['damage_info']['damage_type'] == dt.value) for dt in damage_types}
            },
            "images": dataset_metadata
        }, f, indent=2)
    
    return dataset_metadata

# اجرای تولید دیتاست بهبود یافته
if __name__ == "__main__":
    dataset_metadata = generate_enhanced_borehole_dataset(num_images=2000)
    print(f"\nDataset generated successfully!")
    print(f"Total images: {len(dataset_metadata)}")
    
    # آمار آسیب‌ها
    damage_stats = {}
    for metadata in dataset_metadata:
        damage_type = metadata['damage_info']['damage_type']
        damage_stats[damage_type] = damage_stats.get(damage_type, 0) + 1
    
    print("\nDamage type distribution:")
    for damage_type, count in damage_stats.items():
        print(f"  {damage_type}: {count} images ({count/len(dataset_metadata)*100:.1f}%)")


# کپی تصاویر واقعی به دیتاست
real_images_dir = "path/to/real/well/logs"
if os.path.exists(real_images_dir):
    for i, fname in enumerate(os.listdir(real_images_dir)):
        if fname.endswith(('.png', '.jpg', '.jpeg')):
            shutil.copy(
                os.path.join(real_images_dir, fname),
                os.path.join(output_dir, f"real_{i:04d}.png")
            )
