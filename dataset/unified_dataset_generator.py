import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pyarrow as pa
import pyarrow.parquet as pq
import random
from enum import Enum
import json
import os
from tqdm import tqdm
import matplotlib.pyplot as plt
import cv2
from make_dataset import generate_synthetic_borehole_image, add_formation_damage, FormationDamageType
from data_generator import LWD_MWD_DataGenerator, DamageType

class UnifiedDatasetGenerator:
    """کلاس یکپارچه برای تولید داده‌های تصویری و غیرتصویری"""
    
    def __init__(self):
        self.lwd_mwd_generator = LWD_MWD_DataGenerator()
        self.damage_type_mapping = {
            DamageType.CLAY_IRON_CONTROL: FormationDamageType.CLAY_SWELLING,
            DamageType.DRILLING_INDUCED: FormationDamageType.DRILLING_INDUCED,
            DamageType.FLUID_LOSS: FormationDamageType.FLUID_LOSS,
            DamageType.SCALE_SLUDGE: FormationDamageType.SCALE_FORMATION,
            DamageType.NEAR_WELLBORE_EMULSIONS: FormationDamageType.EMULSION_BLOCKAGE,
            DamageType.ROCK_FLUID_INTERACTION: FormationDamageType.ROCK_FLUID_INTERACTION,
            DamageType.COMPLETION_DAMAGE: FormationDamageType.COMPLETION_DAMAGE,
            DamageType.STRESS_CORROSION: FormationDamageType.STRESS_CORROSION,
            DamageType.SURFACE_FILTRATION: FormationDamageType.SURFACE_FILTRATION
        }
    
    def generate_correlated_image_data(self, sensor_data_row, image_id):
        """تولید تصویر مرتبط با داده‌های سنسور"""
        # استخراج اطلاعات آسیب از داده‌های سنسور
        damage_risk = sensor_data_row.get('damage_risk_score', 0)
        depth = sensor_data_row.get('depth', 1000)
        
        # تعیین ابعاد تصویر بر اساس عمق
        if depth < 1000:
            height, width = 256, 128
        elif depth < 3000:
            height, width = 384, 192
        else:
            height, width = 512, 256
        
        # تعداد لایه‌ها بر اساس عمق
        num_layers = max(5, min(20, int(depth / 200)))
        
        # تولید تصویر پایه
        img = generate_synthetic_borehole_image(height=height, width=width, num_layers=num_layers)
        
        # تعیین نوع و شدت آسیب
        damage_type = FormationDamageType.NORMAL
        damage_severity = 0.0
        
        if damage_risk > 0.1:  # اگر ریسک آسیب بالا باشد
            # انتخاب نوع آسیب بر اساس پارامترهای سنسور
            if sensor_data_row.get('mud_viscosity', 0) > 60:
                damage_type = FormationDamageType.CLAY_SWELLING
            elif sensor_data_row.get('vibration_z', 0) > 15:
                damage_type = FormationDamageType.DRILLING_INDUCED
            elif sensor_data_row.get('flow_rate', 0) < 1000:
                damage_type = FormationDamageType.FLUID_LOSS
            elif sensor_data_row.get('pump_pressure', 0) > 4000:
                damage_type = FormationDamageType.SCALE_FORMATION
            else:
                damage_type = random.choice(list(FormationDamageType)[:-1])
            
            damage_severity = min(0.9, damage_risk * 1.2)
            img = add_formation_damage(img, damage_type, damage_severity)
        
        return img, {
            'image_id': image_id,
            'correlated_sensor_timestamp': sensor_data_row.get('timestamp'),
            'depth': depth,
            'damage_type': damage_type.value,
            'damage_severity': damage_severity,
            'sensor_damage_risk': damage_risk,
            'dimensions': {'height': height, 'width': width},
            'num_layers': num_layers
        }
    
    def generate_unified_dataset(self, start_date, duration_days, num_images_per_day=10, output_path="unified_fidps_dataset"):
        """تولید دیتاست یکپارچه شامل داده‌های سنسور و تصاویر مرتبط"""
        print(f"Generating unified FIDPS dataset for {duration_days} days...")
        
        # ایجاد دایرکتوری‌های خروجی
        os.makedirs(output_path, exist_ok=True)
        os.makedirs(f"{output_path}/sensor_data", exist_ok=True)
        os.makedirs(f"{output_path}/images", exist_ok=True)
        os.makedirs(f"{output_path}/metadata", exist_ok=True)
        os.makedirs(f"{output_path}/correlations", exist_ok=True)
        
        # تولید داده‌های سنسور
        print("Generating sensor data...")
        sensor_df = self.lwd_mwd_generator.generate_dataset(start_date, duration_days, f"{output_path}/sensor_data")
        
        # انتخاب نمونه‌هایی از داده‌های سنسور برای تولید تصاویر مرتبط
        total_images = duration_days * num_images_per_day
        selected_indices = np.random.choice(len(sensor_df), size=min(total_images, len(sensor_df)), replace=False)
        selected_sensor_data = sensor_df.iloc[selected_indices]
        
        print(f"Generating {len(selected_sensor_data)} correlated images...")
        
        image_metadata = []
        correlation_data = []
        
        for idx, (_, sensor_row) in enumerate(tqdm(selected_sensor_data.iterrows(), desc="Generating images")):
            # تولید تصویر مرتبط
            img, img_metadata = self.generate_correlated_image_data(sensor_row, idx)
            
            # ذخیره تصویر
            image_filename = f"borehole_{idx:05d}.png"
            plt.imsave(f"{output_path}/images/{image_filename}", img)
            
            # به‌روزرسانی متادیتا
            img_metadata['filename'] = image_filename
            img_metadata['generation_timestamp'] = datetime.now().isoformat()
            image_metadata.append(img_metadata)
            
            # ایجاد داده‌های ارتباطی
            correlation_entry = {
                'image_id': idx,
                'image_filename': image_filename,
                'sensor_row_index': sensor_row.name,
                'timestamp': sensor_row['timestamp'].isoformat() if hasattr(sensor_row['timestamp'], 'isoformat') else str(sensor_row['timestamp']),
                'depth': sensor_row['depth'],
                'damage_risk_score': sensor_row['damage_risk_score'],
                'key_sensor_values': {
                    'annulus_pressure': sensor_row.get('annulus_pressure', 0),
                    'bottomhole_temp': sensor_row.get('bottomhole_temp', 0),
                    'mud_viscosity': sensor_row.get('mud_viscosity', 0),
                    'vibration_z': sensor_row.get('vibration_z', 0),
                    'flow_rate': sensor_row.get('flow_rate', 0),
                    'pump_pressure': sensor_row.get('pump_pressure', 0)
                }
            }
            correlation_data.append(correlation_entry)
        
        # ذخیره متادیتای تصاویر
        with open(f"{output_path}/metadata/image_metadata.json", "w") as f:
            json.dump({
                "dataset_info": {
                    "name": "FIDPS Unified Image Dataset",
                    "version": "1.0",
                    "creation_date": datetime.now().isoformat(),
                    "total_images": len(image_metadata),
                    "time_range": {
                        "start": start_date.isoformat(),
                        "end": (start_date + timedelta(days=duration_days)).isoformat()
                    }
                },
                "images": image_metadata
            }, f, indent=2)
        
        # ذخیره داده‌های ارتباطی
        correlation_df = pd.DataFrame(correlation_data)
        correlation_df.to_csv(f"{output_path}/correlations/image_sensor_correlations.csv", index=False)
        correlation_df.to_json(f"{output_path}/correlations/image_sensor_correlations.json", orient='records', indent=2)
        
        # ایجاد خلاصه دیتاست
        dataset_summary = {
            "dataset_name": "FIDPS Unified Formation Integrity Dataset",
            "version": "1.0",
            "creation_date": datetime.now().isoformat(),
            "description": "Unified dataset containing both sensor data and correlated borehole images for formation integrity damage prevention",
            "components": {
                "sensor_data": {
                    "total_records": len(sensor_df),
                    "time_range_days": duration_days,
                    "parameters_count": len(sensor_df.columns),
                    "storage_formats": ["CSV", "Parquet", "JSON"]
                },
                "image_data": {
                    "total_images": len(image_metadata),
                    "image_types": ["synthetic_borehole"],
                    "damage_types": list(set([img['damage_type'] for img in image_metadata])),
                    "resolution_range": "256x128 to 512x256"
                },
                "correlations": {
                    "correlated_pairs": len(correlation_data),
                    "correlation_method": "temporal_and_risk_based"
                }
            },
            "file_structure": {
                "sensor_data/": "Raw sensor data in multiple formats",
                "images/": "Synthetic borehole images",
                "metadata/": "Image and dataset metadata",
                "correlations/": "Sensor-image correlation mappings"
            },
            "usage_notes": [
                "Images are correlated with sensor data based on timestamp and damage risk",
                "Damage severity in images reflects sensor-detected anomalies",
                "Use correlation files to link sensor readings with corresponding images"
            ]
        }
        
        with open(f"{output_path}/dataset_summary.json", "w") as f:
            json.dump(dataset_summary, f, indent=2)
        
        print(f"\nUnified dataset generation complete!")
        print(f"Output directory: {output_path}")
        print(f"Sensor records: {len(sensor_df):,}")
        print(f"Correlated images: {len(image_metadata)}")
        print(f"Correlation pairs: {len(correlation_data)}")
        
        return sensor_df, image_metadata, correlation_data

if __name__ == "__main__":
    # پیکربندی تولید دیتاست
    generator = UnifiedDatasetGenerator()
    
    start_date = datetime(2024, 1, 1)
    duration_days = 30  # یک ماه برای تست
    images_per_day = 20  # 20 تصویر در روز
    
    # تولید دیتاست یکپارچه
    sensor_data, image_metadata, correlations = generator.generate_unified_dataset(
        start_date=start_date,
        duration_days=duration_days,
        num_images_per_day=images_per_day,
        output_path="unified_fidps_dataset"
    )
    
    print("\n=== Dataset Statistics ===")
    print(f"Time period: {duration_days} days")
    print(f"Sensor data points: {len(sensor_data):,}")
    print(f"Generated images: {len(image_metadata)}")
    print(f"Average images per day: {len(image_metadata)/duration_days:.1f}")
    
    # آمار آسیب‌ها در تصاویر
    damage_stats = {}
    for img in image_metadata:
        damage_type = img['damage_type']
        damage_stats[damage_type] = damage_stats.get(damage_type, 0) + 1
    
    print("\nImage damage distribution:")
    for damage_type, count in damage_stats.items():
        percentage = (count / len(image_metadata)) * 100
        print(f"  {damage_type}: {count} images ({percentage:.1f}%)")