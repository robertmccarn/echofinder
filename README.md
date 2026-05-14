# EchoFinder

> **Find the modern echo of the music you love.**

EchoFinder is a music discovery application designed to help users find newer, active, and emerging artists (debuted within the last 0–5 years) who carry forward the musical DNA of their favorite legacy artists from the 2000s and 2010s.

---

## 🎓 Learning-First Development Approach

This project is built with a **learning-first** mindset. Instead of jumping straight into a complex web framework, we are following a structured evolution:
1.  **Research & Scripting:** Understanding external APIs and data relationships through simple Python scripts.
2.  **Prototyping:** Building the core recommendation logic in a transparent, readable way.
3.  **Productionizing:** Transitioning the proven logic into a robust **FastAPI** backend and **Next.js** frontend.

Every part of this repository is documented to explain *why* decisions were made, making it a resource for learning full-stack development.

---

## 🚀 Current Status

The project is currently in the **Prototyping Phase**. We have successfully built a Python-based recommendation engine that combines signals from Spotify, MusicBrainz, and Last.fm.

### **Existing Scripts (`/backend/scripts`)**
- `spotify_lookup.py`: Resolves artist names to Spotify IDs and retrieves basic metadata.
- `musicbrainz_lookup.py`: Retrieves "Begin Dates" to verify artist emergence and heritage.
- `lastfm_lookup.py`: Fetches artist tags and "Similar Artist" graphs.
- `recommendation_prototype.py`: The core engine. It crawls 1st and 2nd-degree similarity graphs and calculates an **Echo Score** based on emergence and tag similarity.

---

## 🛠 Tech Stack

- **Frontend:** Next.js, React, TypeScript, Tailwind CSS (Planned)
- **Backend:** Python FastAPI (In Transition)
- **Database:** PostgreSQL with pgvector (Planned)
- **APIs:** Spotify Web API, MusicBrainz API, Last.fm API

---

## 📋 MVP Scope
- **Three Entry Paths:** Search by Artist, Genre, or Scene.
- **Echo Profile Generation:** Analyze "Legacy Anchors" to define a user's sound DNA.
- **Emerging Artist Filtering:** Strictly prioritize artists from the last 0–5 years.
- **Explainable Results:** Tell the user *why* an artist was recommended.
- **Spotify Integration:** Create playlists directly from the app.

---

## ⚙️ Setup & Execution (Windows PowerShell)

### **1. Prerequisites**
- Python 3.10+
- A [Spotify Developer](https://developer.spotify.com/) account.
- A [Last.fm API](https://www.last.fm/api) key.

### **2. Environment Configuration**
Copy the example environment file and fill in your API keys:
```powershell
cp .env.example .env
```

### **3. Backend Setup**
Create a virtual environment and install dependencies:
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### **4. Running the Prototype**
Verify the recommendation engine with our default legacy seeds (Manchester Orchestra, Thrice, The Decemberists):
```powershell
python scripts/recommendation_prototype.py
```

---

## 📅 Next Steps
1.  **Taxonomy Definition:** Formalize the internal tag/mood mapping.
2.  **FastAPI Implementation:** Build the first API endpoints to serve prototype results.
3.  **Database Migration:** Initialize the PostgreSQL schema to cache artist data.

For more details, see the [`/docs`](./docs) folder.

## Development Workflow

EchoFinder uses `test-main` as the active integration branch and `main` as the stable release branch. See [Development Workflow](./docs/development-workflow.md) for branch, review, validation, and release rules.

## Review Automation

EchoFinder includes a local PR review helper for repeatable validation before merging into `test-main`. See [PR Review Automation](./docs/pr-review-automation.md) for usage, recommendations, and safety rules.
