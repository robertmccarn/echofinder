# EchoFinder Backend

Welcome to the **EchoFinder Backend**. This folder contains the "intelligence" of the application, including the data collection scripts, the scoring engine, and eventually, the FastAPI web server.

---

## 📁 Folder Structure

### `scripts/`
This is where the initial research and prototyping happen. Before writing API endpoints, we use these scripts to test our logic.
- `spotify_lookup.py`: Checks if an artist exists on Spotify and gets their unique ID.
- `musicbrainz_lookup.py`: Finds out when an artist started and what they are known for (tags).
- `lastfm_lookup.py`: Finds similar artists and descriptive "vibe" tags.
- `recommendation_prototype.py`: **The main event.** This script combines all the others to find "Modern Echoes."

### `schema.sql`
A draft of our PostgreSQL database structure. This defines how we will eventually store artists, users, and feedback.

### `requirements.txt`
A list of all Python libraries needed to run the project.

---

## 🛠 Setup Instructions (PowerShell)

### 1. Create a Virtual Environment
A virtual environment keeps the project's libraries separate from your computer's main Python installation.
```powershell
python -m venv venv
```

### 2. Activate the Environment
```powershell
.\venv\Scripts\Activate.ps1
```
*(You should see `(venv)` appear in your prompt.)*

### 3. Install Libraries
```powershell
pip install -r requirements.txt
```

---

## 🏃 Running the Prototype
Once your environment is set up and your `.env` file is configured with API keys (see root README), you can run the prototype:
```powershell
python scripts/recommendation_prototype.py
```

### **Refactored Prototype Features**
The prototype has been updated for better performance and MVP correctness:
- **0–5 Year Emerging Artist Scope:** Strictly enforces the discovery window. For 2026, this means artists who emerged between **2021–2026**.
- **Modern Candidate Pool:** Introduced a manual data layer (`backend/data/modern_candidate_pool.json`) to surface true 2021+ emerging artists. This solves the "Legacy Bias" of standard similarity APIs while in the prototyping phase.
- **Artist Classifications:**
    - **Modern Echo:** The primary goal. Artists who debuted within the last 5 years.
    - **Breakout Recent:** Older artists who have gained significant new traction (simulated in prototype).
    - **Bridge Artist:** Older favorites (e.g., 2000s/2010s) that share DNA but are not "new" discoveries.
- **Fast Mode:** Enable `FAST_MODE = True` to quickly validate logic with fewer API calls.
- **Improved Runtime:** Uses aggressive caching and intelligent filtering to skip expensive metadata lookups for irrelevant candidates.

### **How to Interpret the Output**
- **Modern Echoes:** These are your true new discoveries.
- **Bridge Artists:** These explain the *lineage* of the sound (how we got from the seed to the echo).
- **Excluded:** Candidates that were too old, too dissimilar, or lacked reliable data.

### **Performance Choices**
- **Manual Pool Integration:** The manual pool is integrated into the recommendation pipeline, allowing us to score and validate "known good" modern matches against our legacy seeds.
- **Rate-Limit Awareness:** API calls to MusicBrainz and Last.fm are "expensive" due to rate limits and network latency. Caching is our primary tool for reducing this overhead.
- **Candidate Filtering:** We filter by emergence year *before* expensive tag similarity calculations where possible to save on API calls.
- **Deep Discovery Limit:** We limit 2nd-degree similarity crawls to avoid "exploding" the candidate pool into thousands of irrelevant results.

---

## ⏩ Evolution to FastAPI
Currently, this backend consists of standalone scripts. In the next phase of development, we will:
1.  **Wrap this logic in FastAPI:** Creating URL endpoints like `/recommend` that the frontend can call.
2.  **Add a Database:** Using SQLAlchemy to save artist data so we don't have to call the APIs every single time.
3.  **Add Async Logic:** Allowing the backend to handle many users at once without slowing down.
