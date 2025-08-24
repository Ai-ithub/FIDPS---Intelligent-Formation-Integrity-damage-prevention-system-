# 🛢️ Software Requirements Specification (SRS)
## **Intelligent Formation Integrity & Damage Prevention System (FIDPS)**

**Version:** 1.1
**Date:** October 26, 2023
**Status:** Draft for Review

---

## 1. Introduction

### 1.1 Purpose
This document specifies the requirements for the **Intelligent Formation Integrity & Damage Prevention System (FIDPS)**, an integrated software platform designed to **identify, predict, analyze, and prevent** formation damage in real-time during oil and gas drilling, completion, and production operations. FIDPS leverages machine learning, physical simulations, and a robust data pipeline to enhance decision-making and optimize operational efficiency.

### 1.2 System Scope
FIDPS is a comprehensive system that ingests real-time and historical data from field sensors (MWD/LWD), validates it, processes it through machine learning models for prediction and classification, runs simulations for deeper analysis, and presents all insights through an interactive visual dashboard. It is designed for use by drilling engineers, production managers, and petrophysicists in both onshore and offshore environments.

### 1.3 Definitions and Acronyms

| Term/Acronym | Description |
| :--- | :--- |
| **FIDPS** | Formation Integrity & Damage Prevention System |
| **MWD/LWD** | Measurement/Logging While Drilling |
| **ECD** | Equivalent Circulating Density |
| **OBM/WBM** | Oil/Water-Based Mud |
| **SHAP** | SHapley Additive exPlanations (for model interpretability) |
| **FEM** | Finite Element Method (for simulations) |
| **RMSE/MAE** | Root Mean Squared Error / Mean Absolute Error (model metrics) |
| **R²** | Coefficient of Determination (model metric) |

---

## 2. Overall Description

### 2.1 Vision
To become the industry-standard platform for proactive formation damage management, significantly reducing non-productive time (NPT) and completion costs by transforming raw operational data into actionable, predictive insights.

### 2.2 Key Features
- **Real-Time Data Validation:** A robust pipeline to clean, validate, and tag incoming sensor data.
- **Multi-Model ML Engine:** Employs a suite of algorithms (XGBoost, LSTM, GRU, etc.) for classification, regression, and anomaly detection.
- **Physical Simulation Integration:** Uses OpenFOAM/FEniCS for simulating damage processes like fluid loss and emulsion formation.
- **Interactive Dashboard:** A web-based UI for real-time monitoring, historical analysis, and alert management.
- **Synthetic Data Generation:** A module for creating high-fidelity synthetic data to augment training and testing.

### 2.3 Constraints
- Requires high-frequency (≥1 Hz), high-integrity sensor data streams.
- Performance is dependent on GPU resources for model training and complex simulations.
- Must be operable in environments with intermittent network connectivity.

---

## 3. Functional Requirements (FR)

### **FR-1: Data Ingestion & Validation Pipeline**
- **FR-1.1:** The system shall ingest real-time data streams from MWD/LWD tools and historical databases.
- **FR-1.2:** The system shall validate all incoming data against predefined domain rules (value ranges, null checks, unit consistency).
- **FR-1.3:** The system shall tag and log anomalous records for review while routing clean data to downstream modules.

### **FR-2: Machine Learning Core**
- **FR-2.1:** The system shall classify the type of formation damage (from the predefined list of 10 types) using ensemble models (XGBoost/LightGBM).
- **FR-2.2:** The system shall predict continuous values (e.g., fluid loss volume) using regression models (XGBoost Regression, Polynomial Regression).
- **FR-2.3:** The system shall forecast time-series-based risks (e.g., emulsion onset) using recurrent neural networks (LSTM/GRU).
- **FR-2.4:** The system shall identify novel or hidden damage patterns using unsupervised clustering algorithms (KMeans, DBSCAN).
- **FR-2.5:** The system shall detect anomalous operational conditions using anomaly detection algorithms (Isolation Forest, Autoencoders).

### **FR-3: Simulation Module**
- **FR-3.1:** The system shall run finite element simulations (via OpenFOAM/FEniCS) to model physical damage processes for a given set of parameters.
- **FR-3.2:** The system shall allow users to configure and submit simulation scenarios via the API.

### **FR-4: Dashboard & Visualization**
- **FR-4.1:** The dashboard shall display real-time operational parameters (Pressure, ECD, Temperature, RPM, etc.) in time-series charts.
- **FR-4.2:** The dashboard shall visually differentiate between validated and anomalous data points.
- **FR-4.3:** The dashboard shall present ML predictions (damage type, risk score) and model explanations (e.g., SHAP force plots).
- **FR-4.4:** The dashboard shall provide filtering capabilities by well, depth, date range, and damage type.

### **FR-5: Alerting & Reporting**
- **FR-5.1:** The system shall trigger visual and auditory alerts in the dashboard when predicted values exceed critical thresholds.
- **FR-5.2:** The system shall generate summary reports of damage events, model performance, and operational recommendations.

### **FR-6: Data Management**
- **FR-6.1:** The system shall generate synthetic data for model development and testing, mimicking the statistical properties of real field data.
- **FR-6.2:** The system shall store structured data in PostgreSQL and semi-structured data (logs, model artifacts) in MongoDB.

---

## 4. Formation Damage Types Covered

The system shall detect, classify, and analyze the following formation damage types:

| Damage Type ID | Damage Type | Description |
| :--- | :--- | :--- |
| **DT-01** | **Clay & Iron Control** | Chemical interactions with clay and iron minerals causing swelling, dispersion, or migration |
| **DT-02** | **Drilling-Induced Damage** | Mechanical and pressure-related damage during drilling operations (e.g., mud invasion, fines migration) |
| **DT-03** | **Fluid Loss** | Loss of drilling or stimulation fluids into the formation |
| **DT-04** | **Scale/Sludge Incompatibility** | Formation of inorganic or organic deposits (scale, asphaltenes, paraffins) |
| **DT-05** | **Near-Wellbore Emulsions** | Emulsion formation near the wellbore reducing effective permeability |
| **DT-06** | **Rock/Fluid Interaction** | Incompatibility between formation rock and fluids leading to permeability reduction |
| **DT-07** | **Completion Damage** | Loss of connectivity between formation and completion system |
| **DT-08** | **Stress/Corrosion Cracking** | Cracks caused by stress or corrosion mechanisms |
| **DT-09** | **Surface Filtration** | Surface fluid filtration disruptions affecting well productivity |
| **DT-10** | **Ultra-Clean Fluids Control** | Management of high-purity fluids during stimulation operations |

---

## 5. Non-Functional Requirements (NFR)

| ID | Category | Requirement |
| :--- | :--- | :--- |
| **NFR-1** | **Performance** | The data validation pipeline must process records at a frequency of ≥1 Hz. |
| **NFR-2** | **Performance** | Model inference (prediction) must occur with a latency of <5 seconds from data receipt. |
| **NFR-3** | **Reliability** | The system must be able to handle temporary network outages with data buffering and replay capabilities. |
| **NFR-4** | **Scalability** | The architecture must support data ingestion and analysis for at least 50 concurrent wells. |
| **NFR-5** | **Security** | All data transmissions must be encrypted with TLS. Access must be controlled via Role-Based Access Control (RBAC). |
| **NFR-6** | **Maintainability** | The codebase must be modular, well-documented, and accompanied by a CI/CD pipeline. |
| **NFR-7** | **Usability** | The dashboard must be intuitive and require less than 2 hours of training for a field engineer to use effectively. |

---

## 6. System Architecture & Data

### 6.1 High-Level Architecture
```
[Data Sources: Sensors, Historians] 
    → [Kafka Stream] 
    → [Data Validation Microservice (FR-1)] 
    → [Clean Data Storage (PostgreSQL)]
        → [ML Prediction Microservice (FR-2)]
        → [Simulation Service (FR-3)]
    → [Dashboard Backend (FastAPI)]
        → [React.js Frontend (FR-4, FR-5)]
    → [Data Lakes (MongoDB, Cloud Storage)]
```

### 6.2 Data Schema (Key Fields)
The system will utilize a schema including, but not limited to, the following fields:
`well_id, timestamp, depth, mud_type, rpm, spp, flow_rate, viscosity, temperature, ecd, shale_content, lithology, ph, cl_concentration, oil_water_ratio, damage_type_label`

---

## 7. Appendices

### 7.1 Setup Instructions
```bash
git clone https://github.com/your-org/fidps.git
cd fidps
pip install -r requirements.txt
# Run data generation
python generate_synthetic_data.py
# Start the backend API
uvicorn dashboard.backend.app.main:app --reload
# (Separate Terminal) Start the frontend
cd dashboard/frontend && npm install && npm start
```

### 7.2 Technology Stack
| Layer | Technology |
| :--- | :--- |
| **Data/ML** | Python, Pandas, NumPy, Scikit-learn, XGBoost, TensorFlow, OpenFOAM |
| **Backend** | FastAPI, Kafka, PostgreSQL, MongoDB |
| **Frontend** | React.js, D3.js, Plotly, Grafana (for ops) |
| **Infrastructure** | Docker, Kubernetes (future), AWS/GCP |

---
<br>

