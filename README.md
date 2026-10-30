# Matchscore

Cross-platform sports scores application for Football, Basketball and Tennis. The web UI is also the Android app's Capacitor web layer. SportAPI credentials are kept exclusively on the FastAPI backend.

## Included

- Live, all, upcoming and finished score filters, date selection and sport switching.
- Match centre with overview, team statistics, lineups, incidents and head-to-head sections.
- Competition search, standings and season-winner history.
- Player search, profile, career season/team pairs and recent event lookup.
- Club search, profile, squad and transfer history lookup.
- Local favourites and dark/light themes.
- Responsive desktop/mobile layout and Capacitor Android wrapper configuration.
- Backend caching, bounded retry, graceful errors and API-key isolation.

## 1. Configure the API

The key previously pasted into chat should be revoked/rotated before deployment. Add the new key to the backend environment as `RAPIDAPI_KEY`. Never add it to `frontend/`, `package.json`, the Android bundle, or a public repository.

The provider host is `sportapi7.p.rapidapi.com`. Subscribe to the SportAPI plan on RapidAPI and confirm the plan permits the routes used by your app.

## 2. Run the website locally

```bash
cd backend
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Set `RAPIDAPI_KEY` in your shell or copy `.env.example` to `.env` and export the value (FastAPI does not automatically load `.env`; use your host's environment-variable settings or install python-dotenv and load it explicitly).

```bash
# Windows PowerShell
$env:RAPIDAPI_KEY="YOUR_ROTATED_KEY"
uvicorn main:app --reload --port 8000

# macOS/Linux
export RAPIDAPI_KEY="YOUR_ROTATED_KEY"
uvicorn main:app --reload --port 8000
```

Open http://localhost:8000. Health check: http://localhost:8000/api/health.

## 3. Android build

Install Node.js LTS, Android Studio and the Android SDK. From the project root:

```bash
npm install
npx cap add android
npx cap sync android
npx cap open android
```

Build/run the Android app from Android Studio. For a release APK/AAB, use Android Studio's **Build > Generate Signed Bundle / APK**. Keep the backend deployed over HTTPS and point the Android web layer at your production backend when preparing a release; do not ship the RapidAPI key in the app.

## 4. Deployment

Deploy the FastAPI app and `frontend/` together on a Python-capable host. Set `RAPIDAPI_KEY` and a strict `ALLOWED_ORIGINS`. Use HTTPS. For multiple backend workers or instances, replace the in-memory cache with Redis so requests share cached results. Set an API usage budget/alerts on RapidAPI.

## API route notes

The backend exposes `/api/sports/{sport}/live`, `/api/sports/{sport}/date/{date}` and a constrained generic read-only proxy at `/api/proxy/api/v1/...`. SportAPI's public endpoint reference documents scheduled events, event detail/incidents/lineups/statistics, standings, player season stats and career team/season pairs, competition winners, search, team profiles and squad data. Some route variants and response shapes can differ by sport or subscription; the frontend handles missing data and shows provider errors instead of inventing scores or ratings.

Club-specific trophy cabinet is not yet guaranteed by the documented response routes. The current UI links trophy history to competition seasonal winners and clearly marks when a verified team-honours feed is unavailable.

## Notes

- Times are rendered in `Africa/Accra` (Ghana time).
- Live score refresh is manual in this first scaffold; the backend cache is short-lived. A production deployment should add a managed polling strategy/push channel and tune it to your RapidAPI quota.
- Favourites and theme preference are stored locally on the device/browser. Cross-device accounts/sync require an authentication and database layer.
- API images use the provider's image CDN. Confirm the provider's terms and branding requirements before public launch.
