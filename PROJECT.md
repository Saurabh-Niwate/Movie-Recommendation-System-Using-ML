# Project: CineMatch Movie Recommendation System

## Architecture
CineMatch is a full-stack ML-powered personalized movie recommendation system featuring a cyber-cinematic dark user interface, resilient dual-database persistence, offline TMDB media generation, and a real-time recommendation engine with sub-50ms analytical Ridge regression fold-in.

```
┌────────────────────────────────────────────────────────────────────────┐
│                          Frontend (React 18 + Vite)                    │
│  7 Stitch Screens: 01 Watchlist | 02 Feed | 03 Auth | 04 Rankings     │
│                    05 Onboarding | 06 Pre-SignIn Home | 07 Profile     │
│  Design System: Material 3 Cyber Dark, Plus Jakarta Sans, Inter        │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │ HTTP / REST (/api/v1)
┌────────────────────────────────────▼───────────────────────────────────┐
│                          Backend (FastAPI)                             │
│  Routers: profiles, movies, ratings, recommendations, watchlist, tmdb  │
│  Cold-Start Gating: 6-movie rating threshold (403 Forbidden until met)  │
│  Fold-in Engine: Sub-50ms Ridge regression update + cache invalidation  │
└───────────────┬────────────────────────────────────────┬───────────────┘
                │                                        │
┌───────────────▼───────────────┐        ┌───────────────▼───────────────┐
│     Resilient Database Layer   │        │     TMDB & Media Service      │
│  Primary: PostgreSQL (port 5432)│        │  Live TMDB API (Bearer / Key) │
│  Fallback: SQLite (cinematch.db)│       │  Deterministic SVG Generator  │
│  Schema: schema_translate_map │        │  (Posters, Backdrops, Synopsis)│
│  Auto-seed: 24 starter movies, │        └───────────────────────────────┘
│  Neel (18 ratings), Nitin (14) │
└────────────────────────────────┘
```

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| F01 | Database SQLite Fallback | Automatic fallback from PostgreSQL to `cinematch.db` with schema translation (`cinematch` -> `None`) and table creation | M1 | Survey Data & R3 |
| F02 | Auto-Seeding Pipeline | Embedded self-contained seeding of 24 starter movies and baseline personas (Neel, Nitin, Mukesh) without requiring external parquet files | M1 | Survey Data & R3 |
| F03 | TMDB Offline SVG Fallback | Deterministic base64 SVG poster and backdrop generation for offline media resilience | M1 | Survey Data & R3 |
| F04 | Watchlist API CRUD | Repository, service, and routes (`GET`, `POST`, `DELETE`) for profile watchlists using `cinematch.user_lists` | M2 | Survey Backend & R2 |
| F05 | Movie Catalog API | `GET /api/v1/movies` endpoint with genre filtering, title search, and vote/rating sorting | M2 | Survey Backend & R2 |
| F06 | Profile Management & Reset | `POST /api/v1/profiles` (registration) and `POST /api/v1/profiles/reset` (persona state reset for E2E testing) | M2 | Survey Backend & R2 |
| F07 | Cold-Start Gating & Fold-In | 6-movie cold-start gating enforcement (403 Forbidden) and sub-50ms analytical Ridge fold-in upon rating submission | M2 | Survey Backend & R2 |
| F08 | Design System & Token Integration | Stitch cyber-cinematic dark theme tokens, Google Fonts (`Plus Jakarta Sans`, `Inter`), Material Symbols in Vite/Tailwind | M3 | Survey Frontend & R1 |
| F09 | Pre-SignIn Home (`06`) | Hero discovery, search with ⌘K, genre pills, Quick Roll randomizer, star rating widgets, 6-rating calibration tracker, Cosine Similarity drawer | M3 | Survey Frontend & R1 |
| F10 | Taste Onboarding (`05`) | Interactive movie selection, 6-movie cold-start circular progress gauge, live counters, unlockable recommendation synthesis CTA | M3 | Survey Frontend & R1 |
| F11 | Post-SignIn Feed (`02`) | Personalized billboard hero, Taste DNA chips, 98% Affinity resonance gauge, Top Picks for You (5 cols), Because You Loved, Users Also Watched | M3 | Survey Frontend & R1 |
| F12 | Global Rankings & Ratings (`04`) | Multi-genre leaderboard, #1 Dune podium spotlight, period tabs, 1–5 star rating submission triggering real-time fold-in, watchlist tracking | M3 | Survey Frontend & R1 |
| F13 | Auth & Profile Switcher (`03`) | Sign In / Sign Up tabbed card with 1-click persona switching (Neel, Nitin, Mukesh, New User) | M3 | Survey Frontend & R1 |
| F14 | Watchlist Page (`01`) | Saved titles catalog, Grid vs List layout switch, telemetry stats bar (runtime, avg rating, unwatched ratio), streaming tags, remove/stream actions | M3 | Survey Frontend & R1 |
| F15 | Profile & Vector Settings (`07`) | Taste affinity continuous sliders, 6-axis dimensional SVG radar chart, rating history, RecSys model switch (`funk_svd` vs `item_knn`) | M3 | Survey Frontend & R1 |
| F16 | Static Mount & Local Hosting | Single-command or integrated hosting serving API and frontend assets on localhost | M4 | Survey Backend & R4 |
| F17 | Multi-Tier E2E Test Suite | Comprehensive opaque-box test suite (Tiers 1-4) verifying all features across all 7 screens | E2E-Track | Dual-Track Specs |
| F18 | Adversarial Coverage Hardening | Tier 5 white-box stress testing, edge-case probing, and verification gate | M4 (Phase 2) | Dual-Track Specs |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Database Resilience & Media Fallback | SQLite auto-fallback probe, schema translation, embedded starter catalog & persona auto-seeder, TMDB offline SVG pipeline | none | DONE |
| M2 | Backend API Harmonization & Watchlist | Watchlist repository/service/router (`GET`, `POST`, `DELETE`), catalog listing `GET /api/v1/movies`, profile registration/reset, static file mounting | M1 | PLANNED |
| M3 | Frontend 7-Screen Migration & Integration | Complete replacement/upgrade of `frontend/src/` with the 7 Stitch screens, Tailwind tokens, design system, API integration, and Watchlist context | M2 | PLANNED |
| E2E | E2E Testing Suite (Tiers 1-4) | Requirement-driven multi-tier test harness covering all 18 features (Tiers 1-4) | none | PLANNED |
| M4 | Final Integration, Test Pass & Hardening | 100% E2E test pass across all tiers, Tier 5 adversarial testing, local server execution and live browser verification | M3, E2E | PLANNED |

## Interface Contracts

### Watchlist API (`cinematch.user_lists`)
- `GET /api/v1/profiles/{profile_id}/watchlist`
  - Response: `list[MovieWatchlistResponse]` (movie metadata, tmdb_id, poster_url, backdrop_url, release_year, genres, added_at)
- `POST /api/v1/profiles/{profile_id}/watchlist/{movie_id}`
  - Response: `{"status": "added", "profile_id": str, "movie_id": str}` (HTTP 201)
- `DELETE /api/v1/profiles/{profile_id}/watchlist/{movie_id}`
  - Response: `{"status": "removed", "profile_id": str, "movie_id": str}` (HTTP 200)

### Catalog API
- `GET /api/v1/movies?genre={genre}&search={query}&sort={top_rated|recent}&limit={int}&offset={int}`
  - Response: `{"items": list[MovieSummary], "total": int, "genre": str}`

### Profile Reset API
- `POST /api/v1/profiles/reset`
  - Payload: `{"profile_id": str}` (or empty for all default personas)
  - Response: `{"status": "reset", "profile_id": str}`

### Cold-Start Gating API Contract
- `GET /api/v1/profiles/{profile_id}/recommendations`
  - If `profile.ratings_count < 6`: HTTP 403 Forbidden `{"detail": "Cold start profile requires at least 6 ratings"}`
  - If `profile.ratings_count >= 6`: HTTP 200 OK `{"recommendations": list[MovieRecommendation], "model": str, "latency_ms": float}`

### Database Resilience Contract
- Connection probe attempts PostgreSQL first (`postgresql+psycopg://...`).
- Upon connection error / authentication failure / unreachable host:
  - Automatically instantiates SQLite engine: `sqlite:///cinematch.db`
  - Applies `execution_options={"schema_translate_map": {"cinematch": None}}`
  - Enables `PRAGMA foreign_keys=ON`
  - Executes `Base.metadata.create_all()`
  - Triggers auto-seed if profile count == 0.

## Code Layout
- `backend/app/core/database.py`: Database engine instantiation, resilient connection fallback.
- `backend/app/core/config.py`: Environment configuration.
- `backend/app/models/`: SQLAlchemy models (`base.py`, `profile.py`, `movie.py`, `rating.py`, `user_list.py`).
- `backend/app/repositories/`: Data access layer (`profile_repository.py`, `movie_repository.py`, `rating_repository.py`, `user_list_repository.py`).
- `backend/app/services/`: Business logic (`rating_service.py`, `recommendation_service.py`, `watchlist_service.py`, `tmdb.py`).
- `backend/app/routers/`: FastAPI endpoints (`profiles.py`, `movies.py`, `ratings.py`, `recommendations.py`, `watchlist.py`, `tmdb.py`).
- `backend/scripts/seed.py`: Robust database seeding with embedded starter dataset.
- `frontend/src/pages/`:
  - `HomePage.tsx` (Screen 06 Pre-SignIn Home)
  - `OnboardingPage.tsx` (Screen 05 Taste Onboarding)
  - `BrowsePage.tsx` (Screen 02 Post-SignIn Feed)
  - `RankingsPage.tsx` (Screen 04 Global Rankings & Ratings)
  - `AuthPage.tsx` (Screen 03 Authentication & Profile Switcher)
  - `WatchlistPage.tsx` (Screen 01 Watchlist)
  - `ProfilePage.tsx` (Screen 07 Profile & Vector Settings)
  - `ModelLabPage.tsx` (Model Explainability & Metrics)
- `frontend/src/context/`: `ProfileContext.tsx`, `WatchlistContext.tsx`, `ModelContext.tsx`.
- `tests/e2e/`: Multi-tier test suite covering Tiers 1-4.
