# FIDPS Dataset Generator

## Overview

This suite of scripts is designed to generate a comprehensive dataset for the Formation Integrity Damage Prevention System (FIDPS). The dataset includes LWD/MWD sensor data and corresponding borehole images with various formation damage types.

## Features

### 🔧 Sensor Data
- Simulated LWD/MWD data
- 20+ operational parameters
- Simulation of various formation damage types
- Anomaly detection and risk calculation
- Multiple output formats (CSV, Parquet, JSON)

### 🖼️ Image Data
- Synthetic borehole images
- Simulation of 9 formation damage types
- Variable dimensions based on depth
- Correlation with sensor data

### 🔗 Data Correlation
- Temporal correlation between images and sensor data
- Comprehensive metadata
- Mapping files for traceability

## File Structure

```
dataset/
├── data_generator.py           # LWD/MWD sensor data generation
├── make_dataset.py            # Borehole image generation
├── unified_dataset_generator.py # Unified data generation
├── generate_fidps_dataset.py  # Main script
├── fidps_config.json         # Configuration file (auto-generated)
└── README.md                 # This file
```

## Installation & Setup

### Prerequisites

```bash
pip install pandas numpy matplotlib opencv-python pyarrow tqdm
```

### Quick Start

```bash
# Generate dataset with default settings
python generate_fidps_dataset.py

# Generate for 7 days with 50 images per day
python generate_fidps_dataset.py --days 7 --images 50

# Use custom configuration file
python generate_fidps_dataset.py --config my_config.json
```

## Usage Guide

### 1. Create Configuration File

```bash
python generate_fidps_dataset.py --create-config
```

This command creates a `fidps_config.json` file with default settings.

### 2. Edit Configuration

Edit the `fidps_config.json` file:

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

### 3. Generate Dataset

```bash
# Check configuration without generation
python generate_fidps_dataset.py --dry-run

# Generate dataset
python generate_fidps_dataset.py
```

## Command Line Options

| Option | Description |
|--------|-------------|
| `--config, -c` | Path to configuration file |
| `--create-config` | Create default configuration file |
| `--output, -o` | Output directory |
| `--days, -d` | Duration in days |
| `--images, -i` | Number of images per day |
| `--start-date, -s` | Start date (YYYY-MM-DD) |
| `--quiet, -q` | Suppress verbose output |
| `--dry-run` | Show configuration without generation |

## Output Structure

```
fidps_dataset/
├── sensor_data/              # Sensor data
│   ├── real_time_data.csv
│   ├── historical_data.parquet
│   ├── anomaly_data.json
│   └── ml_training_data.parquet
├── images/                   # Borehole images
│   ├── borehole_00001.png
│   ├── borehole_00002.png
│   └── ...
├── metadata/                 # Metadata
│   └── image_metadata.json
├── correlations/            # Correlations
│   ├── image_sensor_correlations.csv
│   └── image_sensor_correlations.json
├── dataset_summary.json     # Dataset summary
└── generation_config.json   # Used configuration
```

## Formation Damage Types

1. **Clay Swelling** - Clay swelling
2. **Drilling Induced** - Drilling-induced damage
3. **Fluid Loss** - Fluid loss
4. **Scale Formation** - Scale formation
5. **Emulsion Blockage** - Emulsion blockage
6. **Rock Fluid Interaction** - Rock-fluid interaction
7. **Completion Damage** - Completion damage
8. **Stress Corrosion** - Stress corrosion
9. **Surface Filtration** - Surface filtration

## Sensor Parameters

### Main Parameters
- Annulus Pressure
- Bottomhole Temperature
- Mud Viscosity
- Flow Rate
- Pump Pressure
- Vibration (X, Y, Z)
- Torque
- Weight on Bit

### Calculated Parameters
- Damage Risk Score
- Quality Index
- Equipment Status
- Alarms

## Usage Examples

### Generate Small Dataset for Testing

```bash
python generate_fidps_dataset.py --days 3 --images 10 --output test_dataset
```

### Generate Large Dataset for Model Training

```bash
python generate_fidps_dataset.py --days 90 --images 100 --output training_dataset
```

### Usage in Python Code

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

## Important Notes

1. **Memory**: Generating large numbers of images requires significant memory
2. **Time**: Each image takes approximately 1-2 seconds to generate
3. **Storage**: Each image is approximately 100-500 KB in size
4. **Correlations**: Images are correlated with sensor data based on time and damage risk

