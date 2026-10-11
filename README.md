# CineMatch: Personalized Movie Recommendation System

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.3-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.5-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Vite](https://img.shields.io/badge/Vite-6.4-646CFF?logo=vite&logoColor=white)](https://vitejs.dev/)
[![Tailwind CSS](https://img.shields.io/badge/TailwindCSS-3.4-38B2AC?logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![E2E Tests](https://img.shields.io/badge/Tests-159%20Passed%20(100%25)-brightgreen?logo=pytest&logoColor=white)](https://pytest.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An enterprise-grade, full-stack Movie Recommendation System replicating the algorithmic foundations of **Furtado & Singh (2020)** (*"An empirical evaluation of collaborative filtering algorithms in movie recommendation"*, *Research in International Business and Finance*). 

Featuring a modern **cyber-cinematic streaming interface**, dual-database resilience (PostgreSQL with zero-config SQLite fallback), authentic **TMDB** media synchronization with official YouTube trailer playback, and real-time recommendation updates via **online Ridge regression fold-in** ($<50\text{ms}$).

---

## Table of Contents
1. [Key Features](#key-features)
2. [System Architecture](#system-architecture)
3. [Core Machine Learning Concepts](#core-machine-learning-concepts)
4. [Tech Stack](#tech-stack)
5. [Prerequisites & Requirements](#prerequisites--requirements)
6. [Step-by-Step Installation & Setup](#step-by-step-installation--setup)
7. [Running the Application](#running-the-application)
8. [Automated Testing Suite (159 Tests)](#automated-testing-suite-159-tests)
9. [Supervisor Demonstration & Defense Guide](#supervisor-demonstration--defense-guide)
10. [Frequently Asked Questions (Supervisor Q&A)](#frequently-asked-questions-supervisor-qa)

---

## Key Features

- **Personalized Recommendation Engine**:
  - **Item-Based Collaborative Filtering (Item-KNN)** with **Adjusted Cosine Similarity** and shrinkage penalty.
  - **Funk-SVD Matrix Factorization** with biased Stochastic Gradient Descent (SGD).
  - **Frequent Itemset Mining (Association Rules)** for *"Users Also Watched"* discovery.
- **Instant Online Fold-In**:
  - Sub-50ms closed-form **Ridge regression solver** that projects new user ratings into the precomputed latent item factor matrix ($p_u = (Q^T Q + \lambda I)^{-1} Q^T r_u$) without costly model retraining.
- **Cold-Start Gating Protocol**:
  - Enforces the paper's strict requirement: new accounts must rate at least **6 starter movies** before recommendations unlock.
- **Authentic Theatrical Media**:
  - Direct integration with **The Movie Database (TMDB)** API for verified posters, backdrops, cast, directors, and dynamic official YouTube theatrical trailer embedding.
- **Dual-Database Reliability**:
  - Automatic fallback between PostgreSQL (production) and SQLite (`cinematch.db`) with dynamic schema translation (`cinematch.*` $\leftrightarrow$ `sqlite.*`).
- **Modern Streaming UI (7 Stitch Screens)**:
  - Curated Feed, Pre-SignIn Hero, Onboarding Setup, Global Leaderboard, Watchlist, Auth, and Profile Settings.

---

## System Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                      Client Layer (React 18 + Vite)                    │
│  • Material 3 Dark Palette (#10131a, #1c202a, #c0c1ff, #4cd7f6)       │
│  • Routes: / (Home), /feed (Feed), /onboarding, /watchlist, /rankings  │
│  • Dynamic YouTube Modal Player & Live Star Rating Fold-in Widgets     │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │ REST API (/api/v1) + Bearer JWT
┌────────────────────────────────────▼───────────────────────────────────┐
│                      API Service Layer (FastAPI)                       │
│  • Endpoints: /movies, /ratings, /recommendations, /watchlist, /auth   │
│  • Cold-Start Gating Gatekeeper (HTTP 403 until ratings >= 6)          │
│  • User List Management & Session Tokens (Bcrypt + HS256 JWT)          │
└───────────────────┬────────────────────────────────┬───────────────────┘
                    │                                │
┌───────────────────▼───────────────┐   ┌────────────▼───────────────────┐
│        Machine Learning Core      │   │    External Media & Storage    │
│  • Funk-SVD (Biased SGD Latent)   │   │  • The Movie Database (TMDB)   │
│  • Item-KNN (Adjusted Cosine)     │   │    API Key & Read Access Token │
│  • Sub-50ms Ridge Online Fold-in  │   │  • YouTube Dynamic Video ID    │
│  • Association Rule Co-occurrence │   │  • Dual DB: PostgreSQL/SQLite  │
└───────────────────────────────────┘   └────────────────────────────────┘
```

---

## Core Machine Learning Concepts

### 1. Item-Based Collaborative Filtering (Item-KNN)
Rather than comparing raw user profiles, Item-KNN measures pairwise similarities between movie items based on the rating patterns of users who rated both:
$$\text{sim}(i, j) = \frac{\sum_{u \in U_{ij}} (r_{u,i} - \bar{r}_u)(r_{u,j} - \bar{r}_u)}{\sqrt{\sum_{u \in U_{ij}} (r_{u,i} - \bar{r}_u)^2} \sqrt{\sum_{u \in U_{ij}} (r_{u,j} - \bar{r}_u)^2} + \lambda_{\text{shrink}}}$$
- **Adjusted Cosine**: Subtracts the user's mean rating $\bar{r}_u$ to neutralize individual user rating bias (some users rate everything 5 stars; others rarely give 4).
- **Shrinkage Penalty ($\lambda_{\text{shrink}} = 10$)**: Dampens similarity scores between items with very few co-raters to prevent false-positive high correlations.

### 2. Funk-SVD Matrix Factorization
Decomposes the sparse rating matrix $R \in \mathbb{R}^{|U| \times |I|}$ into user latent factor matrix $P \in \mathbb{R}^{|U| \times k}$ and item latent factor matrix $Q \in \mathbb{R}^{|I| \times k}$:
$$\hat{r}_{u,i} = \mu + b_u + b_i + p_u \cdot q_i^T$$
- **Objective Loss**:
  $$\min_{P, Q, b} \sum_{(u,i) \in R_{\text{train}}} (r_{u,i} - \hat{r}_{u,i})^2 + \lambda (\|p_u\|_2^2 + \|q_i\|_2^2 + b_u^2 + b_i^2)$$
- Optimized via Stochastic Gradient Descent (SGD) with early stopping.

### 3. Online Ridge Regression Fold-In ($<50\text{ms}$)
In a production system, retraining the entire SVD model every time a user rates a movie is computationally prohibitive. CineMatch implements **closed-form Ridge regression fold-in**:
$$p_u = (Q^T Q + \lambda I)^{-1} Q^T (r_u - \mu - b_I)$$
This instantaneously computes the new user vector $p_u$ in under **50 milliseconds**, updating recommendations live without full matrix retrain.

### 4. Cold-Start Mitigation & Threshold
Users with fewer than 6 ratings have undefined or noisy latent projections. In accordance with Furtado & Singh (2020), CineMatch redirects new users to an interactive **Taste Onboarding** flow requiring $\ge 6$ selections before personalized collaborative recommendations are computed.

---

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, Uvicorn, SQLAlchemy 2.0, Pydantic v2, PyJWT, Passlib (Bcrypt).
- **Machine Learning**: NumPy, SciPy, Scikit-Learn, Pandas.
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Material Symbols, Lucide React.
- **Database**: SQLite (built-in default `cinematch.db`) / PostgreSQL (optional production).
- **Testing**: Pytest, Pytest-Asyncio, HTTPX, Respx.
- **External APIs**: The Movie Database (TMDB) API v3.

---

## Prerequisites & Requirements

- **Python**: Version `3.11` or `3.12` installed.
- **Node.js**: Version `18.0+` or `20.0+` with `npm`.
- **Git**: Installed and available on your PATH.
- **Package Manager**: [uv](https://docs.astral.sh/uv/) (recommended for instant Python environments) or standard `python -m venv`.

---

## Step-by-Step Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/Saurabh-Niwate/Movie-Recommendation-System-Using-ML.git
cd Movie-Recommendation-System-Using-ML
```

### 2. Configure Environment Variables
Copy the example environment file:
```bash
cp .env.example .env
```
*(On Windows PowerShell: `copy .env.example .env`)*

Your `.env` file comes pre-configured for automatic SQLite mode. You can optionally add your TMDB credentials:
```ini
TMDB_API=43962557578f3b9e690a5c1b9cab4d17
TMDB_READ_TOKEN=your_tmdb_read_access_token
```

### 3. Backend Setup

Using **uv** (recommended):
```bash
uv sync
```

*Or using standard Python virtual environment:*
```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -r pyproject.toml
```

### 4. Frontend Setup
```bash
cd frontend
npm install
npm run build
cd ..
```

---

## Running the Application

### 1. Start the Backend API Server
```bash
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
The interactive Swagger API documentation will be accessible at:
- **API Base**: `http://127.0.0.1:8000`
- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **OpenAPI JSON**: `http://127.0.0.1:8000/openapi.json`

### 2. Start the Frontend Development Server
In a separate terminal:
```bash
cd frontend
npm run dev
```
Open your browser at **`http://localhost:5173`**.

---

## Automated Testing Suite (159 Tests)

Run the full end-to-end and unit test suite verifying single-user authentication, cold-start gating, fold-in updates, and TMDB media resolution:

```bash
uv run python -m pytest tests/
```

Expected result:
```
====================== 159 passed in 40.13s =======================
```

---

## Supervisor Demonstration & Defense Guide

Follow this structured roadmap when presenting your project to your supervisor or evaluator:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        LIVE DEMO ROADMAP (10 MIN)                      │
│                                                                        │
│  [0:00 - 2:00]  Problem Statement & Pre-SignIn Catalog Exploration   │
│  [2:00 - 4:00]  Cold-Start Gating & Taste Onboarding (6 Ratings)       │
│  [4:00 - 6:30]  Personalized Feed, 96% Match & Authentic TMDB Trailers │
│  [6:30 - 8:30]  Real-Time Online Fold-In Experiment (<50ms Update)     │
│  [8:30 - 10:00] Algorithm Modes & Mathematical Defense (Item-KNN/SVD) │
└────────────────────────────────────────────────────────────────────────┘
```

### Phase 1: Problem Statement & Exploration (0:00 – 2:00)
- **What to open**: Browser at `http://localhost:5173`.
- **What to do**:
  1. Scroll through the landing page showing modern releases (*Dune: Part Two*, *Oppenheimer*, *Spider-Man: Across the Spider-Verse*).
  2. Click on a movie card to open the **Movie Detail Modal**. Point out the authentic metadata (director, cast, release year, runtime).
  3. Click **"Watch Trailer"**: Show that it loads the official YouTube trailer matching the title.
- **What to explain to supervisor**:
  > *"Traditional recommendation tutorials use static CSV files with synthetic placeholders. CineMatch bridges theoretical ML with production streaming architectures, syncing real-time TMDB artwork and official trailers with dual-database persistence."*

### Phase 2: Cold-Start Gating Demonstration (2:00 – 4:00)
- **What to do**:
  1. Click **"Sign Up Free"** (or go to `/auth`).
  2. Create a new account (e.g. `supervisor@demo.com`).
  3. Notice that the application **automatically directs the user to the Taste Onboarding page** (`/onboarding`) and blocks access to the personalized feed.
  4. Show the circular progress meter: *"0 of 6 mandatory ratings selected"*.
  5. Try to enter the feed early — show that the button is disabled and the backend returns `403 Forbidden` if accessed directly.
  6. Rate 6 starter movies across Sci-Fi, Drama, and Action.
  7. Watch the progress bar hit 100% and the button unlock: *"Finish Setup & Enter Feed"*.
- **What to explain to supervisor**:
  > *"This enforces the fundamental Cold-Start Protocol from Furtado & Singh (2020). Users with fewer than 6 ratings suffer from severe sparsity where latent factors cannot reliably converge. Our system gates access until statistical confidence is established."*

### Phase 3: Personalized Feed & Multi-Row Recommendations (4:00 – 6:30)
- **What to do**:
  1. Click **"Finish Setup & Enter Feed"** to enter `/feed`.
  2. Showcase the **Personalized Billboard Hero**, matched to the user's top-rated genre.
  3. Walk through the distinct recommendation carousels:
     - **Top Picks For You**: Blended recommendations with high affinity percentages (e.g., *96% Match*).
     - **Because You Liked [Movie]**: Item-KNN Adjusted Cosine similarity row.
     - **More Like This**: Frequent itemset co-occurrence associations.
  4. Click **"Watchlist"** (+ icon) on any movie and navigate to `/watchlist` to show real-time synchronization.
- **What to explain to supervisor**:
  > *"The feed is not a single generic list. It employs multi-tier collaborative filtering: Funk-SVD for global latent factorization, Item-KNN for item-to-item similarity with shrinkage penalties, and Association Rules for viewer co-occurrence patterns."*

### Phase 4: Real-Time Online Fold-In Live Test (6:30 – 8:30)
- **What to do**:
  1. Note the current Top Picks on the feed.
  2. Find an unexpected movie (e.g., rate a classic Noir or Animation film with 5 stars).
  3. Submit the rating: note the instantaneous sub-50ms feedback.
  4. Refresh or re-evaluate the feed: demonstrate how the recommendations instantly adapt to the newly rated genre.
- **What to explain to supervisor**:
  > *"In traditional systems, incorporating new user ratings requires retrained batches overnight. We implemented analytical Ridge regression fold-in: $p_u = (Q^T Q + \lambda I)^{-1} Q^T r_u$. Because the item matrix $Q$ is precomputed and fixed, solving for user vector $p_u$ takes less than 50 milliseconds."*

### Phase 5: Recommendation Modes & Profile Settings (8:30 – 10:00)
- **What to do**:
  1. Navigate to `/profile`.
  2. Show the **Genre Preferences** sliders and the **6-Axis Viewing Taste Radar** SVG.
  3. Point out the **Recommendation Mode Selector**:
     - *Personalized Match (Funk-SVD)*
     - *Similar Titles (Item-KNN Adjusted Cosine)*
     - *Viewer Favorites (Association Rules)*
  4. Open the terminal and run `uv run python -m pytest tests/` to display all **159 automated tests passing**.
- **What to explain to supervisor**:
  > *"Every algorithm is modular and benchmarked. Our test suite validates all 5 architectural tiers: single-user authentication, media resolution, cold-start gating, online fold-in, and database resilience."*

---

## Frequently Asked Questions (Supervisor Q&A)

**Q1: Why did you use Adjusted Cosine Similarity instead of standard Pearson Correlation or Cosine?**  
> *Answer:* Standard cosine similarity ignores differences in user rating scales (user optimism/pessimism). Adjusted cosine subtracts each user's average rating $\bar{r}_u$ from the pairwise calculation across common raters $U_{ij}$, standardizing user scales. We also add a shrinkage factor $\lambda = 10$ to penalize pairs with very few common raters, matching Furtado & Singh (2020) Eq. (1).

**Q2: What is the RMSE benchmark of your algorithms?**  
> *Answer:* Replicating Table 5 of Furtado & Singh (2020) on MovieLens:
> - **Funk-SVD Matrix Factorization**: Test RMSE $\approx 0.909$
> - **Item-KNN with Adjusted Cosine**: Test RMSE $\approx 0.961$  
> Funk-SVD outperforms Item-KNN due to latent dimensionality reduction ($k=20$), but Item-KNN provides superior explainability (*"Because you watched X"*).

**Q3: How does the system handle high traffic or database failures?**  
> *Answer:* The backend features dual-database resilience. In production, it connects to PostgreSQL with connection pooling. If PostgreSQL is offline or unreachable, SQLAlchemy automatically catches the timeout within 3 seconds and seamlessly translates queries to local SQLite (`cinematch.db`) with zero downtime.

**Q4: How are trailers matched without errors?**  
> *Answer:* The backend queries TMDB's `/movie/{tmdb_id}/videos` endpoint dynamically, filtering specifically for `site: "YouTube"` and `type: "Trailer"`, sorted by official channel release date. The client then embeds the verified video ID into an isolated YouTube iframe modal.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
