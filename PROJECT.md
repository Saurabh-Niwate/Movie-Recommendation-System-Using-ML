# Project: CineMatch Recommender System

Full-stack movie recommendation system replicating Furtado & Singh (2020) with Item-KNN (Adjusted Cosine & shrinkage), Funk-SVD (fast SGD & closed-form online fold-in), Association Rules (lift), PostgreSQL database, layered FastAPI backend, and Netflix-clone React/TypeScript frontend.

## Architecture

```
                                 [ Browser Client ]
                           React 18 + TS + Tailwind CSS
                         (Browse, Onboarding, Model Lab)
                                        │
                                        ▼ HTTP REST (JSON)
                         [ FastAPI Application Server ]
                  ┌─────────────────────┼─────────────────────┐
                  ▼                     ▼                     ▼
          [ Router Layer ]      [ Service Layer ]     [ Repository Layer ]
          - /api/v1/profiles    - RecommendationEngine - PostgreSQL Engine
          - /api/v1/movies      - FoldInService        - cinematch.movies
          - /api/v1/ratings     - ModelLabService      - cinematch.profiles
          - /api/v1/model-lab   - TMDBClient Fallback  - cinematch.ratings
                  │                     │                     │
                  ▼                     ▼                     ▼
         [ Model Registry ]    [ In-Memory Caching ]   [ PostgreSQL 18 ]
         - FunkSVD (Ridge)     - TTLCache (60s)        - Dedicated schema:
         - ItemKNN (Cos/Shrink)- Profile invalidation    `cinematch`
         - AssociationRules    - Immediate refetch
         - BayesianPopularity
                  │
                  ▼ Reads / Writes
       [ artifacts/v1/ Storage ]
       - id_maps.json, funk_svd.npz, item_knn.npz,
       - associations.parquet, profiles.json, metrics.json
```

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| F1 | MovieLens 1M Data Pipeline | Download, contiguous 0-based user/item indexing, temporal 80/20 train/test + 10% val split, title cleaning | M1 | R1 |
| F2 | Bayesian Popularity Baseline | Bayesian weighted rating baseline with catalog mean and vote count threshold | M1 | R1 |
| F3 | Item-KNN Recommender | Replicate Furtado & Singh (2020) Table 5 with Adjusted Cosine similarity and significance shrinkage (User B Trance = 4.0) | M1 | R1, Table 5 |
| F4 | Funk-SVD with Fast SGD | Biased matrix factorization ($p_u, q_i, b_u, b_i$) trained with Numba-accelerated SGD (15 epochs in ~2s) | M1 | R1 |
| F5 | Closed-Form Online Fold-in | Analytical Ridge regression user vector solver $(Q_u^T Q_u + \Lambda)^{-1} Q_u^T y_u$ for real-time rating updates without retrain | M1, M3 | R1, R2 |
| F6 | Association Rules (Lift) | Co-occurrence matrix and Lift metric computation for "Users also watched" | M1 | R1 |
| F7 | Genre KMeans Demo Profiles | KMeans ($k=4$) on genre distributions isolating Neel (Action/Sci-Fi), Nitin (Drama/Romance), and Mukesh (Cold-start) | M1 | R1 |
| F8 | Offline Metrics & CLI | Evaluation harness computing RMSE, MAE, Precision@10, Recall@10, NDCG@10, Catalog Coverage@10 saved to `artifacts/v1/metrics.json` via `recsys evaluate` | M1 | R1, Acceptance |
| F9 | ML Test Suite | Complete unit test suite in `ml/tests/` verifying Table 5, shrinkage, SGD convergence, fold-in, metrics | M1 | Acceptance |
| F10 | PostgreSQL Schema `cinematch` | Isolated database schema in PostgreSQL 18 with tables `movies`, `profiles`, `ratings`, `user_lists` | M2 | R2 |
| F11 | Alembic Migrations | Migration environment configured for `cinematch` schema with upgrade/downgrade scripts | M2 | R2 |
| F12 | Database Seed Script | Pre-seed profiles Neel (`user_idx=2955`), Nitin (`user_idx=2583`), Mukesh (0 ratings), and MovieLens catalog movies | M2 | R2 |
| F13 | TMDB API Client & Fallback | Integration client with TMDB v3 API and deterministic offline fallback metadata generator (SVG posters, synopses) | M2 | R2 |
| F14 | Layered FastAPI Backend | REST service (`routers -> services -> repositories`), dependency injection, sync SQLAlchemy 2.0 with connection pool | M3 | R2 |
| F15 | Model Registry & Caching | In-memory model registry loading `artifacts/v1/`, TTLCache, immediate profile cache invalidation on rating | M3 | R2 |
| F16 | Real-time Fold-in Endpoint | `POST /api/v1/profiles/{id}/ratings` persisting rating, solving fold-in user factor, and invalidating cache in <50ms | M3 | R2 |
| F17 | Model Lab Explainability API | Math breakdown endpoints returning Funk-SVD biases/factors and Item-KNN neighbor weights & rating deviations | M3 | R2 |
| F18 | Backend Test Suite | API integration test suite in `backend/tests/` covering profiles, movies, ratings, recommendations, explainability | M3 | Acceptance |
| F19 | Frontend React/Vite/Tailwind Scaffold | Modern dark-themed Netflix clone UI scaffolded in `frontend/` with strict TypeScript configuration | M4 | R3 |
| F20 | Profile Picker Screen | "Who's watching?" screen with avatars and descriptions for Neel, Nitin, and Mukesh | M4 | R3 |
| F21 | Cold-Start Onboarding (Mukesh) | Mandatory 6-movie rating onboarding screen replicating Furtado & Singh rule with search bar, starter grid, and locked "Generate Recommendations" button | M4 | R3, Paper |
| F22 | Netflix Browse Page | Billboard hero banner with backdrop and match %, carousels: "Top Picks", "Because you liked", "Users also watched", genres | M4 | R3 |
| F23 | Title Detail Modal | Interactive modal with backdrop, synopsis, cast/crew, interactive 1-5 star ratings, and "More like this" | M4 | R3 |
| F24 | Interactive Model Lab Dashboard | Dashboard with live leaderboard from `metrics.json`, Funk-SVD convergence curves, side-by-side comparison, math breakdowns | M4 | R3 |
| F25 | Frontend TypeScript Build Verification | Production build compile via `cd frontend && npm run build` with zero TypeScript errors | M4 | Acceptance |
| F26 | E2E Requirement Test Suite (Tiers 1-4) | Comprehensive opaque-box E2E test suite covering feature coverage, boundaries, cross-feature reactivity, and user journeys | E2E Track | Acceptance |
| F27 | Final E2E Integration & Verification | Pass 100% of E2E tests, verifying Neel vs Nitin distinct rows, Mukesh gating, real-time fold-in updates, Model Lab toggle | M5 | Acceptance |
| F28 | Adversarial Coverage Hardening (Tier 5) | White-box stress testing and edge-case hardening | M5 | Acceptance |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | ML Core & Recommender Pipeline | F1-F9: Furtado & Singh Table 5 KNN, Funk-SVD fast SGD, online fold-in, association rules, Bayesian popularity, KMeans profiles, offline metrics, CLI, ml/tests | None | DONE |
| M2 | Database Schema & Backend Infrastructure | F10-F13: PostgreSQL schema cinematch, Alembic migrations, SQLAlchemy models, seed data (Neel, Nitin, Mukesh, movies), TMDB client fallback | None | DONE |
| M3 | FastAPI Service & Model Integration | F14-F18: Layered architecture, model registry, online fold-in endpoints, caching, Model Lab explainability endpoint, backend/tests | M1, M2 | DONE |
| M4 | Netflix-Clone Frontend Core | F19-F25: React + TypeScript + Vite + Tailwind, profile picker, cold-start onboarding 6 ratings, browse page, billboard, carousels, modal, Model Lab UI | None | DONE |
| E2E | E2E Testing Track | F26: Opaque-box requirement-driven test infrastructure & test cases (Tiers 1-4) publishing TEST_READY.md | None | DONE |
| M5 | Final E2E Integration & Hardening | F27-F28: Pass 100% E2E tests (Tiers 1-4) & Phase 2 adversarial coverage hardening (Tier 5) | M1, M2, M3, M4, E2E | IN_PROGRESS |

## Interface Contracts

### 1. Model Artifacts (`artifacts/v1/`)
- `id_maps.json`: `{"user2idx": {id: idx}, "idx2user": {idx: id}, "movie2idx": {id: idx}, "idx2movie": {idx: id}}`
- `funk_svd.npz`: `P` (users x f), `Q` (items x f), `b_u` (users), `b_i` (items), `mu` (float)
- `item_knn.npz`: sparse similarity matrix `S` (items x items), `item_means`, `global_mean`
- `associations.parquet` or `associations.json`: `{item_idx: [{"item_idx": j, "lift": float, "cooccurrence": int}]}`
- `profiles.json`: `{neel: {user_idx: 2955, name: "Neel", genres: ["Action", "Sci-Fi"]}, nitin: {user_idx: 2583, name: "Nitin", genres: ["Drama", "Romance"]}, mukesh: {user_idx: null, name: "Mukesh", ratings_count: 0}}`
- `metrics.json`: `{"popularity": {...}, "item_knn": {...}, "funk_svd": {...}}`

### 2. Backend API (`/api/v1` and `/api`)
- `GET /api/v1/profiles`: returns list of profiles with `id, name, avatar, bio, ratings_count, is_cold_start`.
- `GET /api/v1/profiles/{id}`: returns profile details.
- `GET /api/v1/profiles/{id}/recommendations?model={funk_svd|item_knn}&limit=20`: returns personalized recommendations. If profile is Mukesh and ratings_count < 6, returns `403 Forbidden` (`{"detail": "Cold start profile requires at least 6 ratings"}`).
- `GET /api/v1/recommendations/billboard?profile_id={id}`: returns hero movie recommendation.
- `GET /api/v1/recommendations/because-you-liked?profile_id={id}`: returns top item and KNN similar items.
- `GET /api/v1/recommendations/also-watched/{movie_id}`: returns association rules lift items.
- `GET /api/v1/movies/starter`: returns 24 diverse popular titles for cold-start onboarding.
- `GET /api/v1/movies/search?q={query}`: returns matching movies.
- `GET /api/v1/movies/{id}`: returns movie details (synopsis, cast, backdrop, poster, genres).
- `POST /api/v1/profiles/{id}/ratings`: body `{"movie_id": int, "rating": float}`. Saves rating, executes online fold-in, updates user vector, invalidates cache, returns `{"status": "ok", "ratings_count": int, "unlocked": bool}`.
- `GET /api/v1/model-lab/leaderboard`: returns parsed `artifacts/v1/metrics.json`.
- `GET /api/v1/model-lab/convergence`: returns Funk-SVD epoch loss and validation RMSE history.
- `GET /api/v1/model-lab/compare?profile_id={id}`: returns side-by-side top 10 items from Item-KNN vs Funk-SVD.
- `GET /api/v1/model-lab/explain?profile_id={id}&movie_id={movie_id}&model={model}`:
  - For Funk-SVD: returns `{mu, user_bias, item_bias, dot_product, latent_breakdown: [...], predicted_score}`.
  - For Item-KNN: returns `{user_mean, neighbors: [{movie_id, title, similarity, rating, contribution}], predicted_score}`.

## Code Layout & Ownership
- `ml/`: Owned exclusively by Milestone M1 workers.
  - `ml/src/recsys/config.py` (fix `parents[3]`)
  - `ml/src/recsys/models/funk_svd.py`
  - `ml/src/recsys/models/item_knn.py`
  - `ml/src/recsys/models/association_rules.py`
  - `ml/src/recsys/profiles/cluster.py`
  - `ml/src/recsys/cli.py`
  - `ml/tests/`
- `backend/`: Owned exclusively by Milestones M2 and M3 workers.
  - `backend/app/core/config.py`, `database.py`
  - `backend/app/models/` (SQLAlchemy models)
  - `backend/app/schemas/` (Pydantic schemas)
  - `backend/app/repositories/`
  - `backend/app/services/`
  - `backend/app/routers/`
  - `backend/app/main.py`
  - `backend/alembic/`
  - `backend/scripts/seed.py`
  - `backend/tests/`
- `frontend/`: Owned exclusively by Milestone M4 workers.
  - `frontend/src/` (components, pages, api, context, types)
  - `frontend/package.json`, `vite.config.ts`, `tailwind.config.js`, `tsconfig.json`
- `tests/e2e/`: Owned exclusively by E2E Testing Track workers.
