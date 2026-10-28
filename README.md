# Food Verse AI — Multimodal Food Intelligence Platform

Food Verse AI is an end-to-end multimodal food intelligence platform combining computer vision, visual quality control, hygiene auditing, and dietary intelligence.

Built with **FastAPI (Python 3.10)** on the backend and **React + Vite (JavaScript/JSX)** on the frontend.

---

## 🌟 Six Core Modules

| Module | Engine / AI Technology | Status | Key Features |
| :--- | :--- | :--- | :--- |
| **1. Core Setup & Environment** | FastAPI, CORS, Pydantic, Vite | ✅ **Implemented** | Health checks, OpenAPI docs, JWT auth, SQLite |
| **2. Food Recognition & Nutrition** | ViT (`nateraw/food`), Spatial Cropping | ✅ **Implemented** | Multi-dish recognition, Top-5 scoring, macro breakdown |
| **3. Freshness & Spoilage Detection** | HSV/RGB texture variance pipeline | ✅ **Implemented** | Browning/mold detection, surface metrics, storage advice |
| **4. Restaurant Hygiene Monitoring** | OpenCV frame extraction + optional Groq Vision | ✅ **Implemented** | Image & video uploads, violation cards, downloadable reports |
| **5. Smart Cooking Assistant** | Dynamic culinary engine + optional LLM | ✅ **Implemented** | Pantry photo input, step-by-step recipes, substitutions |
| **6. Personalized Meal Planner** | Mifflin-St Jeor BMR/TDEE engine | ✅ **Implemented** | Biometric inputs, allergen blacklisting, 7-day schedule |

---

## 🚀 Quickstart Guide (Windows PowerShell)

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm (Node 22 LTS recommended; **Node 24 works** with Vite ≥8)

---

### Step 1: Backend Setup

```powershell
cd backend

# Create & activate virtual environment
python -m venv venv_new
.\venv_new\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Optional: configure a cloud AI key (not required – demo mode works without one)
Copy-Item ..\.env.example .env
# Edit .env and set GROQ_API_KEY or GEMINI_API_KEY if desired

# Run the full test suite (120 tests, ~14 s)
pytest

# Start the API server
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Backend endpoints:
- **Health:** `http://127.0.0.1:8000/health`
- **Swagger UI:** `http://127.0.0.1:8000/docs`
- **ReDoc:** `http://127.0.0.1:8000/redoc`

### Render Backend Deployment (CPU)

Use the repository's `render.yaml` Blueprint settings, or apply the same values to the existing Render web service:

- **Root Directory:** `backend`
- **Environment variable:** `PYTHON_VERSION=3.10.10`
- **Build Command:** `python -m pip install --no-cache-dir -r requirements-render.txt && python verify_render_install.py`
- **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1`

The Render requirements pin the Python dependencies and reference exact CPython 3.10 Linux x86_64 CPU-only PyTorch wheels. The build-time import check fails if runtime modules are missing or a CUDA-enabled PyTorch build is installed. One worker prevents multiple application processes from each loading another copy of Food-101. The classifier remains loaded at startup for real inference. Its full-precision weights are about 328 MiB before Python, framework, and inference memory are included, so a 512 MiB runtime is not a reliable fit; use an instance with more memory if startup or inference still exceeds the limit.

---

### Step 2: Frontend Setup

> **Important (Node 24 + Windows Junction):** Always run `npm run dev` from the **physical project path** (e.g. `C:\Users\radhe\Desktop\food-verse-ai\frontend`), not from a Junction/symlink. Running through a Junction causes a Vite 6.x dep-metadata crash on Node 24.

```powershell
# Navigate to the physical path
cd C:\Users\radhe\Desktop\food-verse-ai\frontend

# Install dependencies
npm install

# Option A – Hot-reload dev server (HMR)
npm run dev        # → http://localhost:5173

# Option B – Verified production build + preview
npm run build      # compiles to dist/
npm run preview    # → http://localhost:4173
```

---

## 📡 API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Service readiness & model status |
| `/api/v1/capabilities` | GET | Feature flags & provider info |
| `/api/v1/auth/register` | POST | Create user account |
| `/api/v1/auth/login` | POST | JWT login |
| `/api/v1/food/recognize` | POST | Image → ViT food classification + nutrition |
| `/api/v1/food/freshness` | POST | Image → freshness/spoilage assessment |
| `/api/v1/hygiene/audit` | POST | Image or video → hygiene compliance score |
| `/api/v1/hygiene/report/{id}` | GET | Download audit report (JSON / Markdown) |
| `/api/v1/cooking/assistant` | POST | Ingredients + optional photo → recipe |
| `/api/v1/meal-plan/generate` | POST | Biometrics + goals → 7-day meal plan |
| `/api/v1/history` | GET | Analysis history (auth required) |
| `/api/v1/profile` | GET / PUT | User profile |

---

## 🛡️ Disclaimers
- **No API keys required** — all six modules run locally in demo mode without any cloud credentials.
- **Optional AI upgrade** — set `GROQ_API_KEY` or `GEMINI_API_KEY` in `.env` to enable multimodal LLM vision.
- Freshness and nutrition estimates are visual estimations, not certified clinical or bacteriological assays.
