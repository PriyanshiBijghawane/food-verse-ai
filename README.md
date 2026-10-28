# Food Verse AI — Multimodal Food Intelligence Platform

Food Verse AI is an end-to-end multimodal food intelligence platform combining computer vision, visual quality control, hygiene auditing, and dietary intelligence.

Built with **FastAPI (Python)** on the backend and **React + Vite (JavaScript/JSX)** on the frontend.

---

## 🌟 Six Core Modules

| Module | Engine / AI Technology | Status | Key Features |
| :--- | :--- | :--- | :--- |
| **1. Core Setup & Environment** | FastAPI, CORS, Pydantic, Vite | ✅ **Fully Implemented** | Health checks, OpenAPI documentation, environment variable safety |
| **2. Food Recognition & Nutrition** | Vision Transformer (`nateraw/food` fine-tuned ViT-101), Spatial Cropping | ✅ **Fully Implemented** | Real multi-dish spatial recognition, Top-5 candidate scoring, portion & macro calculations |
| **3. Freshness & Spoilage Detection** | Multi-spectral HSV/RGB texture variance & color histogram pipeline | ✅ **Fully Implemented** | Spoilage detection, oxidation browning, mold cues, safe handling & storage guidance |
| **4. Restaurant Hygiene Monitoring** | Frame extraction via OpenCV, local CV analytics & optional Groq Vision | ✅ **Fully Implemented** | Image & video uploads, station observations, violation severity grading, downloadable audit reports |
| **5. Smart Cooking Assistant** | Dynamic culinary synthesis engine & optional Groq/OpenAI LLM | ✅ **Fully Implemented** | Multimodal photo & text inputs, step-by-step instructions, timers, ingredient substitutions |
| **6. Personalized Meal Planner** | Mifflin-St Jeor metabolic calculations & deterministic dietary scheduler | ✅ **Fully Implemented** | BMR/TDEE calculation, 5 daily meal occasions, strict allergen exclusions, 7-day schedule |

---

## 🚀 Quickstart Guide (Windows PowerShell)

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm

---

### Step 1: Backend Setup & Launch

1. Open PowerShell and navigate to the backend directory:
   ```powershell
   cd backend
   ```

2. Activate the virtual environment (or create one):
   ```powershell
   # If creating a new virtual environment:
   # python -m venv venv
   .\venv_new\Scripts\Activate.ps1
   ```

3. (Optional) Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

4. Configure environment variables (optional for external cloud AI):
   ```powershell
   Copy-Item ..\.env.example .env
   # Edit .env to add optional GROQ_API_KEY or OPENAI_API_KEY if desired
   ```

5. Run the test suite:
   ```powershell
   pytest
   ```
   *(All 43 tests pass across all modules).*

6. Launch the FastAPI server:
   ```powershell
   uvicorn main:app --host 127.0.0.1 --port 8000 --reload
   ```
   The backend API will be live at:
   - API Root & Health: `http://127.0.0.1:8000/health`
   - Interactive Swagger Docs: `http://127.0.0.1:8000/docs`
   - Alternative ReDoc: `http://127.0.0.1:8000/redoc`

---

### Step 2: Frontend Setup & Launch

1. Open a new PowerShell terminal and navigate to the frontend directory:
   ```powershell
   cd frontend
   ```

2. Install frontend dependencies:
   ```powershell
   npm install
   ```

3. Build production bundle (verified build):
   ```powershell
   npm run build
   ```

4. Start the development server:
   ```powershell
   npm run dev
   ```
   The frontend UI will be running at `http://localhost:5173`.

---

## 📡 API Endpoints Reference

### Health & Core
- `GET /health` — Service readiness and vision model status.

### Epic 2: Food Recognition & Nutrition
- `POST /api/v1/food/recognize` — Multi-part image upload (`file`). Performs ViT inference and spatial multi-dish decomposition.
- `GET /api/v1/food/nutrition?food={name}` — Returns macro and micronutrient estimates from the nutrition knowledge graph.

### Epic 3: Freshness & Spoilage Detection
- `POST /api/v1/food/freshness` — Multi-part image upload (`file`), optional `food_hint` query string. Extracts visual surface indicators, browning, discoloration, and mold cues.

### Epic 4: Restaurant Hygiene Monitoring
- `POST /api/v1/hygiene/audit` — Multi-part media upload (`file`: image max 15MB or video max 60MB). Analyzes kitchen frames and outputs compliance score (0-100), cleanliness score, and violation logs.
- `GET /api/v1/hygiene/report/{audit_id}?format=json|markdown` — Downloads formatted audit reports.

### Epic 5: Smart Cooking Assistant
- `POST /api/v1/cooking/assistant` — Form data: `ingredients`, `dietary_preference`, `cuisine`, `max_time_minutes`, `skill_level`, and optional `image`. Synthesizes structured recipes with prep time, cooking timers, substitutions, and nutrition estimates.

### Epic 6: Personalized Meal Planner
- `POST /api/v1/meal-plan/generate` — JSON payload with biometrics (`age`, `height_cm`, `weight_kg`, `activity_level`), goal, diet type, and strict `allergies` / `food_restrictions`. Generates 5 eating occasions with consistent calorie sums and a 7-day schedule.

---

## 🛡️ Robust Local Fallbacks & Disclaimers
- **Zero Required External Secrets:** All six modules operate autonomously out-of-the-box without requiring cloud API keys. Local computer vision, heuristics, and mathematical nutritional graphs guarantee reliable local execution.
- **Optional LLM Enhancements:** If `GROQ_API_KEY` or `OPENAI_API_KEY` is present in your environment, the platform seamlessly upgrades to multimodal LLM vision and reasoning.
- **Safety Disclaimers:** All freshness and nutrition estimates are transparently identified as visual estimations rather than certified clinical or bacteriological inspections.
