# Original User Request

## Initial Request — 2026-10-06T15:21:56Z

Use multiple agents to parallelize the tasks.

Build a full-stack movie recommendation system (Netflix clone UI, FastAPI backend, PostgreSQL database, and machine learning models replicating Furtado & Singh (2020) with Item-KNN, Funk-SVD matrix factorization, and association rules).

Working directory: /home/yoogkadu/Documents/SEM 5/ML project
Integrity mode: development

## Requirements

### R1. Machine Learning Core & Offline Evaluation
- Download and prepare MovieLens 1M dataset with contiguous ID indexing and temporal 80/20 per-user train/test split (+10% validation split).
- Implement Popularity Bayesian weighted rating baseline.
- Implement the paper's Item-based Collaborative Filtering using K-Nearest Neighbors with Adjusted Cosine Similarity and significance shrinkage.
- Implement Funk-SVD (biased matrix factorization) with fast SGD training and closed-form online fold-in for new profile ratings.
- Implement association rules (co-occurrence lift) for "users also watched".
- Implement KMeans clustering on user genre distributions to select 2 representative demo users (Neel and Nitin) with distinct movie preferences.
- Evaluate all models using RMSE, MAE, Precision@10, Recall@10, NDCG@10, and Catalog Coverage@10. Save metrics and model artifacts to `artifacts/v1/`.

### R2. Backend Service & Database
- PostgreSQL database using local connection details from `.env` in dedicated schema `cinematch`.
- Alembic migrations and models for movies, profiles, ratings, and user lists.
- FastAPI REST service with layered architecture (`routers -> services -> repositories/infra`), model registry, in-memory caching, and online fold-in.
- Pre-seed profiles: Neel (Action/Sci-Fi demo), Nitin (Drama/Romance demo), and Mukesh (empty cold-start profile).
- TMDB API client integration framework built against TMDB v3 docs (supporting graceful fallback when `TMDB_API` key is added later).
- Model Lab explainability endpoint returning mathematical breakdown of predictions (SVD biases + latent factors, KNN neighbor contributions).

### R3. Netflix-Clone Frontend
- Modern React + TypeScript + Vite web interface with Tailwind CSS dark theme.
- Profile picker screen ("Who's watching?" with Neel, Nitin, and Mukesh).
- Cold-start onboarding screen requiring rating of at least 6 movies (the paper's rule) before unlocking recommendations for Mukesh.
- Netflix-style browse page with billboard, "Top Picks", "Because you liked...", "Users also watched", and genre carousels.
- Title detail modal with backdrop, predicted match %, cast/crew, "More like this", and rating controls.
- Interactive Model Lab dashboard displaying live model leaderboard (NDCG, RMSE), training convergence curves, and side-by-side comparison.

## Acceptance Criteria

### Automated Verification
- [ ] `uv run pytest ml/tests -q` passes all tests, including reproduction of the paper's Table 5 KNN calculation.
- [ ] `uv run recsys evaluate --models popularity,item_knn,funk_svd` executes and generates `artifacts/v1/metrics.json` showing Item-KNN and Funk-SVD outperforming Popularity baseline on NDCG@10 and RMSE.
- [ ] `uv run pytest backend/tests -q` passes all API integration tests.
- [ ] `cd frontend && npm run build` compiles with zero TypeScript errors.

### Functional Verification
- [ ] Switching between profiles Neel and Nitin produces distinctly different recommendation rows.
- [ ] Profile Mukesh is blocked from recommendations until rating at least 6 movies in onboarding.
- [ ] Submitting a new rating updates recommendation rows without retraining the global model.
- [ ] Model Lab allows toggling between Item-KNN and Funk-SVD with visible score changes.
