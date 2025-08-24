import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pyarrow as pa
import pyarrow.parquet as pq
import random
from enum import Enum
import json

class DamageType(Enum):
    CLAY_IRON_CONTROL = "DT-01"
    DRILLING_INDUCED = "DT-02"
    FLUID_LOSS = "DT-03"
    SCALE_SLUDGE = "DT-04"
    NEAR_WELLBORE_EMULSIONS = "DT-05"
    ROCK_FLUID_INTERACTION = "DT-06"
    COMPLETION_DAMAGE = "DT-07"
    STRESS_CORROSION = "DT-08"
    SURFACE_FILTRATION = "DT-09"
    ULTRA_CLEAN_FLUIDS = "DT-10"

class DataRetentionTier(Enum):
    REAL_TIME = "PostgreSQL (Hot)"
    HISTORICAL = "PostgreSQL (Warm)"
    ANOMALY = "MongoDB"
    RAW_SENSOR = "S3 Glacier (Cold)"
    ML_TRAINING = "S3 Standard"

class LWD_MWD_DataGenerator:
    def __init__(self):
        # Operational parameter ranges (realistic values for oil/gas drilling)
        self.param_ranges = {
            # Depth and position measurements
            'depth': (0, 5000),
            'hole_depth': (0, 5000),
            'bit_depth': (0, 5000),
            'inclination': (0, 90),
            'azimuth': (0, 360),
            'dogleg_severity': (0, 10),
            
            # Pressure measurements
            'annulus_pressure': (0, 500),
            'standpipe_pressure': (0, 1000),
            'bottomhole_pressure': (0, 1500),
            'pore_pressure': (0, 1200),
            'mud_pressure': (0, 1000),
            'pressure_diff': (0, 200),
            
            # Temperature measurements
            'bottomhole_temp': (20, 200),
            'mud_temp_in': (10, 80),
            'mud_temp_out': (15, 90),
            'temp_diff': (0, 50),
            
            # Drilling parameters
            'weight_on_bit': (0, 50),
            'torque': (0, 40),
            'rotary_speed': (0, 200),
            'rate_of_penetration': (0, 50),
            'flow_rate': (0, 4000),
            'pump_pressure': (0, 5000),
            
            # Mud properties
            'mud_density': (1.0, 2.5),
            'mud_viscosity': (10, 80),
            'mud_ph': (8.0, 12.0),
            'chloride_content': (1000, 50000),
            'solids_content': (0, 20),
            'mud_rheology': (10, 60),
            'filter_cake_thickness': (0, 10),
            
            # Formation evaluation
            'gamma_ray': (0, 200),
            'resistivity': (0.1, 1000),
            'neutron_porosity': (0, 0.4),
            'density_porosity': (0, 0.4),
            'sonic_slowness': (40, 200),
            'permeability_index': (0, 1000),
            
            # Vibration and mechanical
            'vibration_x': (0, 20),
            'vibration_y': (0, 20),
            'vibration_z': (0, 20),
            'shock': (0, 50),
            
            # Additional operational data
            'hook_load': (0, 500),
            'block_position': (0, 50),
            'pump_stroke': (0, 120),
            'total_gas': (0, 100),
            'c1_gas': (0, 100),
            'c2_gas': (0, 50),
            'co2_content': (0, 10),
            'h2s_content': (0, 0.1),
            
            # Damage indicators
            'skin_factor': (-5, 20),
            'productivity_index': (0, 100),
            'injectivity_index': (0, 100),
            'damage_ratio': (0, 2),
        }
        
        # Equipment status codes
        self.equipment_status = ['NORMAL', 'WARNING', 'CRITICAL', 'MAINTENANCE_REQUIRED']
        
        # Alarm states
        self.alarm_states = ['NORMAL', 'WARNING', 'CRITICAL', 'EMERGENCY']
        
        # Damage type probabilities
        self.damage_probabilities = {
            DamageType.CLAY_IRON_CONTROL: 0.15,
            DamageType.DRILLING_INDUCED: 0.25,
            DamageType.FLUID_LOSS: 0.20,
            DamageType.SCALE_SLUDGE: 0.10,
            DamageType.NEAR_WELLBORE_EMULSIONS: 0.08,
            DamageType.ROCK_FLUID_INTERACTION: 0.07,
            DamageType.COMPLETION_DAMAGE: 0.05,
            DamageType.STRESS_CORROSION: 0.04,
            DamageType.SURFACE_FILTRATION: 0.03,
            DamageType.ULTRA_CLEAN_FLUIDS: 0.03
        }
        
        # Retention periods
        self.retention_periods = {
            DataRetentionTier.REAL_TIME: timedelta(days=90),
            DataRetentionTier.HISTORICAL: timedelta(days=5*365),
            DataRetentionTier.ANOMALY: timedelta(days=2*365),
            DataRetentionTier.RAW_SENSOR: timedelta(days=7*365),
            DataRetentionTier.ML_TRAINING: None  # Indefinite
        }

    def generate_timestamps(self, start_date, duration_days, frequency_sec=1):
        """Generate timestamps for the specified duration"""
        total_seconds = duration_days * 24 * 60 * 60
        return [start_date + timedelta(seconds=i) for i in range(0, total_seconds, frequency_sec)]
    
    def generate_realistic_data(self, base_value, range_tuple, timestamp, trend_factor=0.0001, noise_factor=0.05):
        """Generate realistic time-series data with trends and noise"""
        min_val, max_val = range_tuple
        
        # Create a time-based trend
        time_factor = timestamp.timestamp() / 3600
        trend = np.sin(time_factor * trend_factor) * (max_val - min_val) * 0.1
        
        # Add some random noise
        noise = np.random.normal(0, (max_val - min_val) * noise_factor)
        
        # Calculate final value
        value = base_value + trend + noise
        
        # Ensure value stays within operational range
        return max(min_val, min(max_val, value))
    
    def simulate_damage_effects(self, current_values, damage_type, severity):
        """Simulate the effects of specific damage types on operational parameters"""
        modified_values = current_values.copy()
        
        if damage_type == DamageType.CLAY_IRON_CONTROL:
            # Clay swelling effects
            modified_values['mud_viscosity'] *= (1 + severity * 0.3)
            modified_values['skin_factor'] += severity * 5
            modified_values['pressure_diff'] *= (1 + severity * 0.2)
            
        elif damage_type == DamageType.DRILLING_INDUCED:
            # Mechanical damage effects
            modified_values['torque'] *= (1 + severity * 0.4)
            modified_values['vibration_z'] *= (1 + severity * 0.5)
            modified_values['rate_of_penetration'] *= (1 - severity * 0.3)
            
        elif damage_type == DamageType.FLUID_LOSS:
            # Fluid loss effects
            modified_values['flow_rate'] *= (1 - severity * 0.6)
            modified_values['annulus_pressure'] *= (1 - severity * 0.4)
            modified_values['mud_density'] *= (1 + severity * 0.1)
            
        elif damage_type == DamageType.SCALE_SLUDGE:
            # Scale formation effects
            modified_values['pump_pressure'] *= (1 + severity * 0.5)
            modified_values['permeability_index'] *= (1 - severity * 0.7)
            modified_values['skin_factor'] += severity * 8
            
        elif damage_type == DamageType.NEAR_WELLBORE_EMULSIONS:
            # Emulsion effects
            modified_values['mud_viscosity'] *= (1 + severity * 0.8)
            modified_values['productivity_index'] *= (1 - severity * 0.6)
            
        elif damage_type == DamageType.ROCK_FLUID_INTERACTION:
            # Rock-fluid incompatibility
            modified_values['resistivity'] *= (1 + severity * 0.4)
            modified_values['skin_factor'] += severity * 4
            
        elif damage_type == DamageType.COMPLETION_DAMAGE:
            # Completion damage
            modified_values['productivity_index'] *= (1 - severity * 0.9)
            modified_values['injectivity_index'] *= (1 - severity * 0.9)
            
        elif damage_type == DamageType.STRESS_CORROSION:
            # Stress corrosion effects
            modified_values['vibration_x'] *= (1 + severity * 0.6)
            modified_values['vibration_y'] *= (1 + severity * 0.6)
            modified_values['shock'] *= (1 + severity * 0.8)
            
        elif damage_type == DamageType.SURFACE_FILTRATION:
            # Surface filtration issues
            modified_values['filter_cake_thickness'] *= (1 + severity * 2)
            modified_values['solids_content'] *= (1 + severity * 0.5)
            
        elif damage_type == DamageType.ULTRA_CLEAN_FLUIDS:
            # Ultra-clean fluid management
            modified_values['chloride_content'] *= (1 - severity * 0.9)
            modified_values['solids_content'] *= (1 - severity * 0.9)
        
        return modified_values
    
    def generate_damage_event(self, current_depth, current_time):
        """Generate a formation damage event with specific characteristics"""
        if random.random() < 0.001:  # 0.1% chance of damage event per record
            damage_type = random.choices(
                list(self.damage_probabilities.keys()),
                weights=list(self.damage_probabilities.values())
            )[0]
            
            severity = random.uniform(0.1, 1.0)  # Severity from 10% to 100%
            duration = timedelta(hours=random.uniform(1, 48))
            
            return {
                'damage_type': damage_type.value,
                'damage_name': damage_type.name,
                'severity': severity,
                'start_time': current_time,
                'end_time': current_time + duration,
                'depth_interval': (current_depth, current_depth + random.uniform(10, 100)),
                'detection_confidence': random.uniform(0.7, 0.95)
            }
        
        return None
    
    def determine_retention_tier(self, data_type, is_anomaly=False):
        """Determine the appropriate storage tier based on data type"""
        if is_anomaly:
            return DataRetentionTier.ANOMALY
        elif data_type in ['raw_sensor', 'formation_evaluation']:
            return DataRetentionTier.RAW_SENSOR
        elif data_type == 'ml_training':
            return DataRetentionTier.ML_TRAINING
        else:
            # For operational data, split between real-time and historical
            return random.choice([DataRetentionTier.REAL_TIME, DataRetentionTier.HISTORICAL])
    
    def generate_dataset(self, start_date, duration_days, output_path):
        """Generate the complete dataset with formation damage patterns"""
        print(f"Generating {duration_days} days of LWD/MWD data with formation damage patterns...")
        
        timestamps = self.generate_timestamps(start_date, duration_days)
        total_records = len(timestamps)
        
        # Initialize data storage
        data = {col: [] for col in self.param_ranges.keys()}
        metadata_fields = [
            'timestamp', 'equipment_status', 'battery_voltage', 'internal_temp',
            'vibration_level', 'pressure_alarm', 'temperature_alarm', 'gas_alarm',
            'drilling_phase', 'damage_event', 'retention_tier', 'data_quality_score',
            'formation_type', 'lithology', 'damage_risk_score'
        ]
        
        for field in metadata_fields:
            data[field] = []
        
        # Initialize base values
        current_values = {param: random.uniform(*self.param_ranges[param]) 
                         for param in self.param_ranges.keys()}
        
        current_depth = 0
        drilling_rate = random.uniform(10, 30)
        active_damage_event = None
        
        for i, timestamp in enumerate(timestamps):
            if i % 100000 == 0:
                print(f"Processing record {i}/{total_records} ({i/total_records*100:.1f}%)")
            
            # Update depth
            if random.random() > 0.05:
                current_depth += drilling_rate / (24 * 60 * 60)
            current_depth = min(current_depth, self.param_ranges['depth'][1])
            
            # Check for new damage events
            if active_damage_event is None:
                damage_event = self.generate_damage_event(current_depth, timestamp)
                if damage_event:
                    active_damage_event = damage_event
                    print(f"New damage event: {damage_event['damage_name']} at depth {current_depth:.1f}m")
            
            # Apply damage effects if active
            if active_damage_event and timestamp <= active_damage_event['end_time']:
                severity = active_damage_event['severity']
                current_values = self.simulate_damage_effects(
                    current_values, 
                    DamageType(active_damage_event['damage_type']), 
                    severity
                )
                damage_risk = severity
            else:
                active_damage_event = None
                damage_risk = random.uniform(0, 0.1)
            
            # Update parameters
            for param in self.param_ranges.keys():
                new_value = self.generate_realistic_data(
                    current_values[param], 
                    self.param_ranges[param],
                    timestamp
                )
                data[param].append(new_value)
                current_values[param] = new_value
            
            # Add metadata
            data['timestamp'].append(timestamp)
            data['damage_risk_score'].append(damage_risk)
            
            # Generate additional metadata
            equipment_status = random.choice(self.equipment_status)
            data['equipment_status'].append(equipment_status)
            data['battery_voltage'].append(round(random.uniform(22.0, 29.0), 2))
            data['internal_temp'].append(round(random.uniform(15.0, 85.0), 1))
            data['vibration_level'].append(round(random.uniform(0.1, 5.0), 2))
            
            # Generate alarms based on current values
            data['pressure_alarm'].append('CRITICAL' if current_values['annulus_pressure'] > 450 else 
                                         'WARNING' if current_values['annulus_pressure'] > 400 else 'NORMAL')
            data['temperature_alarm'].append('CRITICAL' if current_values['bottomhole_temp'] > 180 else 
                                           'WARNING' if current_values['bottomhole_temp'] > 160 else 'NORMAL')
            data['gas_alarm'].append('CRITICAL' if current_values['total_gas'] > 80 else 
                                    'WARNING' if current_values['total_gas'] > 60 else 'NORMAL')
            
            # Determine retention tier
            is_anomaly = any(alarm != 'NORMAL' for alarm in [
                data['pressure_alarm'][-1], 
                data['temperature_alarm'][-1], 
                data['gas_alarm'][-1]
            ])
            retention_tier = self.determine_retention_tier('operational', is_anomaly)
            data['retention_tier'].append(retention_tier.value)
            
            data['data_quality_score'].append(random.uniform(0.85, 0.99))
            data['drilling_phase'].append(self.generate_drilling_phase(current_depth))
            
            # Store damage event info
            if active_damage_event:
                data['damage_event'].append(json.dumps(active_damage_event))
            else:
                data['damage_event'].append(None)
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Add formation data
        formation_data = []
        for depth in df['depth']:
            formation_data.append(self.generate_formation_data(depth))
        
        formation_df = pd.DataFrame(formation_data)
        df = pd.concat([df, formation_df], axis=1)
        
        # Save data to appropriate formats based on retention tier
        self.save_data_by_tier(df, output_path)
        
        print("Data generation complete!")
        return df
    
    def save_data_by_tier(self, df, output_path):
        """Save data to different storage formats based on retention tier"""
        print("Saving data to appropriate storage tiers...")
        
        # Real-time data (PostgreSQL format - CSV for simulation)
        real_time_mask = df['retention_tier'] == DataRetentionTier.REAL_TIME.value
        df[real_time_mask].to_csv(f"{output_path}/real_time_data.csv", index=False)
        
        # Historical data (PostgreSQL)
        historical_mask = df['retention_tier'] == DataRetentionTier.HISTORICAL.value
        df[historical_mask].to_csv(f"{output_path}/historical_data.csv", index=False)
        
        # Anomaly data (MongoDB format - JSON)
        anomaly_mask = df['retention_tier'] == DataRetentionTier.ANOMALY.value
        df[anomaly_mask].to_json(f"{output_path}/anomaly_data.json", orient='records', lines=True)
        
        # Raw sensor data (Parquet for S3)
        raw_sensor_data = df[['timestamp', 'depth'] + list(self.param_ranges.keys())]
        raw_sensor_data['date'] = raw_sensor_data['timestamp'].dt.date
        table = pa.Table.from_pandas(raw_sensor_data)
        pq.write_to_dataset(
            table,
            root_path=f"{output_path}/raw_sensor_data",
            partition_cols=['date'],
            compression='SNAPPY'
        )
        
        # ML training data (Parquet)
        ml_data = df.copy()
        ml_data['date'] = ml_data['timestamp'].dt.date
        ml_table = pa.Table.from_pandas(ml_data)
        pq.write_to_dataset(
            ml_table,
            root_path=f"{output_path}/ml_training_data",
            partition_cols=['date'],
            compression='SNAPPY'
        )

# Configuration and execution
if __name__ == "__main__":
    generator = LWD_MWD_DataGenerator()
    
    start_date = datetime(2024, 1, 1)
    duration_days = 180  # 6 months
    output_path = "formation_damage_dataset"
    
    df = generator.generate_dataset(start_date, duration_days, output_path)
    
    # Print summary
    print(f"\nDataset Summary:")
    print(f"Total records: {len(df):,}")
    print(f"Time range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    print(f"Damage events: {df['damage_event'].notna().sum()}")
    
    # Damage type distribution
    damage_events = df[df['damage_event'].notna()]['damage_event'].apply(
        lambda x: json.loads(x)['damage_name'] if x else None
    )
    print("\nDamage Event Distribution:")
    print(damage_events.value_counts())
