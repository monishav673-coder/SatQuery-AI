# SATQUERY AI — Interactive Vision-Language Assistant for Multimodal Remote Sensing Image Analysis (SIH26167)

> **Smart India Hackathon (SIH) Problem Statement:** SIH26167  
> **Core Concept:** An Agentic AI-powered Remote Sensing Analysis Platform that transforms natural language text queries and satellite imagery (Optical, SAR, Multitemporal, or Coordinates) into quantified geospatial findings, dynamic confidence metrics, visual evidence overlays, and executive PDF reports without requiring users to configure underlying computer vision models.

---

## 1. Project Architecture & Directory Structure

```
c:\Users\MONISHA.V\OneDrive\Desktop\Anti SAT\
│
├── Frontend/                           # User Interface & Localization
│   ├── index.html                      # Single Page Application (Login + Dashboard + History)
│   ├── css/
│   │   └── style.css                   # Space / Dark Navy UI Design System (Glassmorphism)
│   └── js/
│       ├── i18n.js                     # 9 Indian Languages Translation Engine
│       ├── auth.js                     # User Authentication & Session Persistence
│       ├── dashboard.js                # Analysis Controller, Upload Handlers & Results Renderer
│       └── api.js                      # Centralized REST API Service
│
├── Backend/                            # Modular Python Backend
│   ├── app.py                          # Flask Entrypoint & Static Server
│   ├── requirements.txt                # Python Dependencies
│   ├── database.py                     # SQLite ORM & Secure Password Hashing
│   │
│   ├── agent/                          # Agentic Intelligence Layer
│   │   ├── controller.py               # Master Orchestrator
│   │   ├── planner.py                  # Query Intent Decomposition & Task Planner
│   │   └── router.py                   # Specialist Model Router
│   │
│   ├── specialists/                    # Computer Vision & Remote Sensing Specialists
│   │   ├── building_detection.py       # Structural Edge & Spectral Roof Detector (BBoxes & Directions)
│   │   ├── water_detection.py          # RGB-NDWI & HSV Water Body Segmentation Specialist
│   │   ├── agriculture.py              # VARI & ExG Vegetation Index Canopy Analyzer
│   │   ├── land_cover.py               # 5-Class BigEarthNet Aligned Land Cover Classifier
│   │   ├── change_detection.py         # Sub-pixel ORB Alignment & Radiometric Delta-E Change Analyzer
│   │   ├── optical_analysis.py         # Spectral Entropy & Sharpness Radiometric Analyzer
│   │   ├── sar_analysis.py             # Radar Backscatter & Speckle Filtering Specialist
│   │   ├── optical_sar_fusion.py       # Feature-Level Optical-SAR Decision Fusion Specialist
│   │   └── vqa.py                      # Vision-Language Natural Language Synthesizer
│   │
│   ├── services/                       # Core Analytical Services
│   │   ├── image_processing.py         # Image Normalization, Alignment & Compass Mapping
│   │   ├── geospatial.py               # Reverse Geocoding & Satellite Tile Retrieval
│   │   ├── confidence.py               # Multi-factor Mathematical Confidence Calculator
│   │   ├── evidence.py                 # OpenCV High-Resolution Annotation Overlay Engine
│   │   └── report.py                   # ReportLab Executive PDF Report Engine
│   │
│   ├── routers/                        # REST API Blueprints
│   │   ├── auth.py                     # Authentication (Register, Login, Language)
│   │   ├── analysis.py                 # Main Multimodal /api/analyze Endpoint
│   │   ├── location.py                 # /api/analyze-location Endpoint
│   │   ├── reports.py                  # /api/reports/<id> JSON & PDF Endpoints
│   │   └── history.py                  # /api/history Archive Endpoint
│   │
│   ├── uploads/                        # Temporary Storage for Uploads & Visual Evidence
│   └── reports/                        # Generated PDF Reports Storage
│
├── samples/                            # Curated Satellite Imagery for 1-Click SIH Evaluation
│   ├── single_sample.jpg               # Single Optical Scene (Urban + Water + Agriculture)
│   ├── optical_sample.jpg              # Sentinel-2 Optical Tile
│   ├── sar_sample.jpg                  # Sentinel-1 SAR Radar Intensity Tile
│   ├── before_sample.jpg               # Pre-event Satellite Scene (T1)
│   └── after_sample.jpg                # Post-event Satellite Scene (T2)
│
├── satquery.db                         # SQLite Database
├── generate_samples.py                 # Sample Generator Script
├── test_backend.py                     # Integration Test Suite
├── test_live_server.py                 # Live HTTP Socket Test Suite
├── .env.example                        # Environment Configuration Template
├── .gitignore                          # Git Ignore File
└── README.md                           # Documentation
```

---

## 2. Technologies Used

- **Backend:** Python 3.10+, Flask, Flask-CORS, Werkzeug (PBKDF2 SHA-256 password hashing)
- **Computer Vision & Remote Sensing:** OpenCV (`cv2`), NumPy, PIL / Pillow, Rasterio, Torch / Torchvision, Ultralytics
- **Report Generation:** ReportLab (high-resolution PDF generation with dynamic tables, metrics, and figures)
- **Database:** SQLite 3 with relational schema for users and multimodal analysis records
- **Frontend:** Semantic HTML5, Vanilla CSS3 (Custom Design System with Glassmorphism, CSS Custom Properties, Responsive CSS Grid), Vanilla JavaScript (ES6 Modules)
- **Geospatial & Remote Sensing APIs:** OpenStreetMap Nominatim Reverse Geocoding, ArcGIS / Esri World Imagery Satellite Tile WMS

---

## 3. Remote Sensing Models & Specialist Algorithms

1. **Building Detection Specialist:**
   - Detects individual built-up structures, rooftop polygons, and building footprints.
   - Extracts bounding boxes `[x, y, w, h]`, area in pixels, individual confidence, and image-relative compass sector (`North`, `North-East`, etc.).
2. **Water Body Detection Specialist:**
   - Employs Normalized Difference Water Index (NDWI proxy) and HSV cyan-blue spectral thresholding.
   - Filters noise with morphological opening/closing, extracts connected components, calculates surface water coverage percentage, and counts distinct water bodies.
3. **Agriculture & Vegetation Specialist:**
   - Computes Visible Atmospherically Resistant Index ($\text{VARI} = \frac{G-R}{G+R-B}$) and Excess Green ($\text{ExG} = 2G - R - B$).
   - Calculates true vegetative canopy density and identifies dominant geographic quadrants.
4. **BigEarthNet Land Cover Classifier:**
   - Multi-class pixel classification mapping scenes into 5 Corine-compatible categories: **Agriculture / Vegetation**, **Built-up / Urban Infrastructure**, **Water Bodies**, **Bare Soil / Barren Land**, and **Other / Unclassified**.
5. **Multitemporal Differential Change Specialist:**
   - Sub-pixel ORB feature matching and Homography co-registration.
   - Delta-E color distance + radiometric luminance difference thresholding.
   - Categorizes changed regions into **Urban Expansion**, **Water Inundation / Expansion**, and **Vegetation Alteration**.
6. **Optical-SAR Feature Fusion Specialist:**
   - Co-registers optical multispectral reflectance with Synthetic Aperture Radar (SAR) microwave dielectric backscatter.
   - Cross-validates specular low-backscatter water regions and dihedral double-bounce corner reflection on urban structures.
7. **Vision-Language Semantic Assistant (VQA):**
   - Synthesizes exact detected metrics, spatial distributions, and user-specified query terms into an articulate, natural language response.

---

## 4. BigEarthNet Dataset Usage

- **Taxonomy Alignment:** The land cover classifier strictly implements the BigEarthNet-19 class nomenclature (Sentinel-2 multispectral standard).
- **Multi-Label Benchmark:** Provides reference class probabilities for built-up, arable land, pastures, permanent crops, inland waters, and bare soils.
- **Configurable Dataset Path:** Configured in `.env` via `BIGEARTHNET_DATASET_PATH` for offline training and fine-tuning pipelines.

---

## 5. Agentic AI Workflow

```
               [ User Natural-Language Query + Satellite Image / Coordinates ]
                                            │
                                            ▼
                                   [ Agent Controller ]
                                            │
                                            ▼
                                  [ Task Planner (NLP) ]
                     Decomposes query into required sub-stages
                                            │
                                            ▼
                                [ Specialist Router ]
         ┌──────────────────┬───────────────┴───────────────┬──────────────────┐
         ▼                  ▼                               ▼                  ▼
  [ Radiometric Spec ]  [ Building Spec ]            [ Water Spec ]     [ Agri/Canopy Spec ]
         │                  │                               │                  │
         └──────────────────┼───────────────────────────────┼──────────────────┘
                            │
                            ▼
          [ BigEarthNet Land Cover Classification ]
                            │
                            ▼
          [ Spatial Direction & Compass Orientation ]
                            │
                            ▼
          [ Multi-Factor Confidence Score Engine (/100) ]
                            │
                            ▼
          [ OpenCV Visual Evidence Overlay Generator ]
                            │
                            ▼
          [ Vision-Language Interpretation (VQA) ]
                            │
                            ▼
          [ Downloadable PDF Report + SQLite History ]
```

---

## 6. Multi-Language Support (9 Indian Languages)

The user interface features a real client-side i18n translation engine (`Frontend/js/i18n.js`) supporting:
1. **English (en)** — Default
2. **Tamil (ta)** — தமிழ்
3. **Hindi (hi)** — हिन्दी
4. **Telugu (te)** — తెలుగు
5. **Kannada (kn)** — ಕನ್ನಡ
6. **Malayalam (ml)** — മലയാളം
7. **Bengali (bn)** — বাংলা
8. **Marathi (mr)** — मराठी
9. **Gujarati (gu)** — ગુજરાતી

All headings, buttons, dropzone hints, placeholders, alerts, status indicators, and summary labels instantly switch language upon selection.

---

## 7. REST API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Service health status and specialist online checks |
| `POST` | `/api/auth/register` | User registration with password hashing |
| `POST` | `/api/auth/login` | User authentication |
| `POST` | `/api/auth/update-language` | Update preferred language |
| `POST` | `/api/analyze` | Main multimodal image analysis (Single, Optical+SAR, Multitemporal) |
| `POST` | `/api/analyze-location` | Coordinate analysis (Latitude, Longitude) with reverse geocoding |
| `GET` | `/api/reports/<id>` | Fetch analysis record JSON |
| `GET` | `/api/reports/<id>/pdf` | Download dynamic PDF analysis report |
| `GET` | `/api/history` | Retrieve user analysis history from SQLite |

---

## 8. Database Structure (`satquery.db`)

### `users` Table
- `id` (TEXT PRIMARY KEY)
- `email` (TEXT UNIQUE NOT NULL)
- `password_hash` (TEXT NOT NULL)
- `preferred_language` (TEXT DEFAULT 'en')
- `created_at` (TIMESTAMP DEFAULT CURRENT_TIMESTAMP)

### `analyses` Table
- `id` (TEXT PRIMARY KEY)
- `user_id` (TEXT, FOREIGN KEY)
- `user_email` (TEXT)
- `mode` (TEXT NOT NULL)
- `query` (TEXT NOT NULL)
- `confidence_score` (INTEGER)
- `confidence_level` (TEXT)
- `buildings_count` (INTEGER)
- `water_count` (INTEGER)
- `water_pct` (REAL)
- `agri_pct` (REAL)
- `result_json` (TEXT NOT NULL)
- `created_at` (TIMESTAMP DEFAULT CURRENT_TIMESTAMP)

---

## 9. Installation & Running Commands

### Step 1: Install Dependencies
```bash
pip install -r Backend/requirements.txt
```

### Step 2: Generate Sample Satellite Images (Optional)
```bash
python generate_samples.py
```

### Step 3: Run the Server
```bash
python Backend/app.py
```
The server will start on `http://127.0.0.1:5001`.

### Step 4: Open in Web Browser
Navigate to:
```
http://127.0.0.1:5001
```

---

## 10. Running Test Suites

Run backend integration tests:
```bash
python test_backend.py
```

Run live HTTP socket tests:
```bash
python test_live_server.py
```

---

## 11. How to Demonstrate to Smart India Hackathon Judges

1. **Login & Language Localization:**
   - Open `http://127.0.0.1:5001`.
   - Demonstrate the language dropdown: Select **Tamil** (தமிழ்) or **Hindi** (हिन्दी) to show immediate UI localization.
   - Enter `scientist@isro.gov.in` and password `SecurePassword123!` and click **Sign In** (or register a new user).
2. **Mode 1: Single Optical Satellite Image Analysis:**
   - Select **Mode 1: Single Image**.
   - Click **⚡ Load SIH Sample Scene** to load the satellite tile.
   - Leave the query: *"Identify buildings, water bodies and agricultural areas, and tell me where they are located."*
   - Click **ANALYZE WITH AGENTIC AI**.
   - Show the judges the live **Agentic AI Execution Pipeline** scanning steps.
   - Highlight the real **18 detected buildings**, **6 water bodies**, **34.6% agricultural canopy**, **BigEarthNet land cover distribution**, **spatial compass breakdown**, and the **high-res visual evidence overlay** with bounding boxes.
3. **Mode 2: Optical + SAR Multimodal Fusion:**
   - Switch to **Mode 2: Optical + SAR**.
   - Click **⚡ Load Optical + SAR Pair**.
   - Click **ANALYZE WITH AGENTIC AI**.
   - Show how SAR radar backscatter cross-validates optical surface detections.
4. **Mode 3: Multitemporal Change Detection:**
   - Switch to **Mode 3: Multitemporal Change**.
   - Click **⚡ Load Before & After Pair**.
   - Click **ANALYZE WITH AGENTIC AI**.
   - Show the quantified **15.5% overall surface change**, broken down into **Urban Expansion** and **Water Inundation**.
5. **Coordinate Location Analysis:**
   - Click **Analyze by Location (Lat / Lon)**.
   - Enter Latitude: `10.9601`, Longitude: `76.9500`.
   - Click **Analyze Coordinates** to show real reverse geocoding to Coimbatore, Tamil Nadu, and tile processing.
6. **PDF Report Download & History:**
   - Click **📄 Download PDF Report** to view the comprehensive, publication-ready PDF.
   - Navigate to the **History** tab to show persistent SQLite query archiving.
