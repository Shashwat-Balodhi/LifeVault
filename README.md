# 🧠 LifeVault — AI-Powered Personal Memory Assistant

> Transform normal file storage into an intelligent semantic memory layer.  
> Built for the **VIT–SanDisk Hackathon 2026**.

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green?logo=fastapi)
![Streamlit](https://img.shields.io/badge/Streamlit-1.41-red?logo=streamlit)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_DB-orange)

---

## 🌟 What is LifeVault?

LifeVault is an **on-device personal memory assistant** that understands the *content* inside your files — not just filenames. Drop images, PDFs, text files, or documents into a folder, and LifeVault will:

- 🔍 **Semantically index** everything using AI embeddings
- 🧠 **Understand** what's *inside* each file (CLIP for images, MiniLM for text)
- 💬 **Search with natural language** — "photos from the beach", "notes about machine learning"
- 🏷️ **Auto-tag** images using zero-shot classification
- 📊 **Visualize** your memory timeline
- 🎲 **Surprise you** with random memories

**Everything runs locally.** No cloud. No subscriptions. Your memories stay yours.

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────┐
│                    LIFEVAULT SYSTEM                    │
├──────────────────────────────────────────────────────┤
│                                                        │
│   Watchdog ──▶ Ingestion Pipeline ──▶ ChromaDB         │
│                     │                     ▲             │
│                AI Models                  │             │
│              (CLIP + MiniLM             Query           │
│               + EasyOCR)              Engine            │
│                                   (+ Gemini)           │
│                                         │              │
│   Streamlit ◀──── FastAPI ◀─────────────┘              │
│                                                        │
└──────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
lifevault/
├── backend/
│   ├── main.py                 # FastAPI app + ingestion orchestration
│   ├── ingestion/
│   │   ├── file_watcher.py     # Real-time folder monitoring
│   │   ├── image_processor.py  # CLIP embedding + OCR
│   │   ├── doc_processor.py    # PDF/DOCX/TXT processing
│   │   └── metadata_extractor.py  # EXIF + filesystem metadata
│   ├── ai/
│   │   ├── embedder.py         # Model loading (singleton)
│   │   ├── vector_store.py     # ChromaDB operations
│   │   ├── query_engine.py     # Semantic search + Gemini intent
│   │   └── auto_tagger.py      # Zero-shot image classification
│   └── utils/
│       ├── config.py           # Environment configuration
│       └── logger.py           # Logging setup
├── frontend/
│   └── app.py                  # Streamlit UI
├── data/
│   └── chroma_db/              # Vector database (auto-created)
├── sample_files/               # Drop files here!
├── requirements.txt
├── .env
└── README.md
```

---

## 🚀 Installation

### Prerequisites

- Python 3.11+
- pip
- (Optional) CUDA-capable GPU for faster processing

### Step 1: Clone & Setup

```bash
cd lifevault

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

> ⚠️ **First run** will download AI models (~500MB for CLIP, ~90MB for MiniLM).  
> This only happens once — models are cached locally.

### Step 3: Configure

Edit the `.env` file:

```env
# Required: Get from https://aistudio.google.com/apikey
GEMINI_API_KEY=your_actual_key_here

# Optional: Change the watch folder
WATCH_FOLDER=./sample_files
```

> If you don't set a Gemini key, search still works — it just skips the intent-parsing step.

### Step 4: Add Sample Files

Drop some images, PDFs, text files, or documents into the `sample_files/` folder.

---

## 🏃 Running LifeVault

### Terminal 1: Start the Backend

```bash
cd lifevault
python -m backend.main
```

Or with uvicorn directly:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### Terminal 2: Start the Frontend

```bash
streamlit run frontend/app.py
```

The app will open at `http://localhost:8501`.

---

## 🔍 Example Usage

### Search Queries

| Query | What happens |
|-------|-------------|
| "sunset photos" | CLIP finds visually similar sunset images |
| "notes about machine learning" | MiniLM finds semantically relevant documents |
| "photos with people" | Zero-shot tags match "people", "portrait", "group photo" |
| "documents from last week" | Gemini parses time intent + file type filter |
| "cat pictures" | CLIP embeddings match cat imagery |

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/api/search` | POST | Semantic search |
| `/api/stats` | GET | Indexing statistics |
| `/api/all-files` | GET | All indexed file metadata |
| `/api/surprise` | GET | Random memory |
| `/api/ingest` | POST | Manual file ingestion |
| `/api/thumbnail` | GET | File thumbnails |

---

## 🧠 AI Models Used

| Model | Purpose | Dimensions | Size |
|-------|---------|-----------|------|
| **OpenCLIP ViT-B-32** | Image embeddings + zero-shot tags | 512 | ~400MB |
| **all-MiniLM-L6-v2** | Text/document embeddings | 384 | ~90MB |
| **EasyOCR** | Text extraction from images | — | ~100MB |
| **Google Gemini Flash** | Query intent parsing (API) | — | Cloud |

---

## ⚡ Performance

- **100+ files**: Processes smoothly
- **Search**: < 2 second response time
- **Indexing**: ~1-3 seconds per file (GPU) / 3-8 seconds (CPU)
- **Storage**: Fully local via ChromaDB

---

## 🏆 Built For

**VIT–SanDisk Hackathon 2026**

*Transforming storage from passive containers to intelligent memory systems.*

---

## 📄 License

MIT License — Built with ❤️ for the hackathon.
