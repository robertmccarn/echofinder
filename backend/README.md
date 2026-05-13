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

---

## ⏩ Evolution to FastAPI
Currently, this backend consists of standalone scripts. In the next phase of development, we will:
1.  **Wrap this logic in FastAPI:** Creating URL endpoints like `/recommend` that the frontend can call.
2.  **Add a Database:** Using SQLAlchemy to save artist data so we don't have to call the APIs every single time.
3.  **Add Async Logic:** Allowing the backend to handle many users at once without slowing down.
