# CineMatch E2E Test Infrastructure & Verification Framework

## 1. Overview & Architectural Philosophy

The CineMatch End-to-End (E2E) testing framework provides opaque-box verification of the movie recommendation platform replicating Furtado & Singh (2020). The suite verifies full-stack functionality across the FastAPI REST API, recommendation algorithms (Funk-SVD with online fold-in, Item-KNN with adjusted cosine similarity and shrinkage, Association Rules with lift), database schema integrity, and client interaction workflows.

### 1.1 Testing Principles
1. **Opaque-Box Requirement Verification**: Tests treat the system as a black box with specified input stimuli and observable external outputs (HTTP status codes, JSON response schemas, recommendation distributions, ranking stability, mathematical properties).
2. **Explicit Expected Output Derivation**: Every test derives its expected outputs directly from the research paper (*Furtado & Singh 2020*), `PROJECT.md`, `ORIGINAL_REQUEST.md`, and mathematical properties of collaborative filtering.
3. **State Isolation & Clean Teardown**: Each test initializes its required profile state, executes isolated mutations, and restores state via test fixture lifecycle hooks (`profile_state_reset`).
4. **Dual Execution Target Compatibility**: The test suite can run against:
   - The standalone mock-backed contract server (`tests/e2e/contracts/mock_app.py`) for offline, isolated validation.
   - The live running FastAPI service (`http://localhost:8000`) or ASGI application (`backend.app.main:app`).

---

## 2. The 4-Tier Test Architecture

```
                          ┌──────────────────────────────────────────────┐
                          │    Tier 4: Real-World Application Scenarios  │
                          │   (Multi-persona journeys, audit sessions)   │
                          ├──────────────────────────────────────────────┤
                          │    Tier 3: Cross-Feature Interactions        │
                          │ (Pairwise reactivity, live fold-in, toggles) │
                          ├──────────────────────────────────────────────┤
                          │    Tier 2: Boundary & Corner Cases           │
                          │ (Cold-start 0/5/6/7, empty query, fallbacks) │
                          ├──────────────────────────────────────────────┤
                          │    Tier 1: Feature Coverage                  │
                          │ (>=5 per feature: Profiles, Billboard, etc.) │
                          └──────────────────────────────────────────────┘
```

---

## 3. Tier 1: Feature Coverage Matrix (>= 5 Tests per Feature)

Tier 1 validates primary happy-path behavior, schema conformity, and data integrity across the 5 core user-facing features.

### 3.1 Feature 1: User Profiles & Identity Management
| Test ID | Test Name | Target Endpoint | Stimulus / Input | Expected Result / Assertion |
|---|---|---|---|---|
| `T1.1.1` | `test_list_all_profiles` | `GET /api/v1/profiles` | Empty query | Status 200; returns exactly 3 pre-seeded profiles: Neel, Nitin, Mukesh; all have `id`, `name`, `avatar`, `bio`, `ratings_count`, `is_cold_start`. |
| `T1.1.2` | `test_get_profile_neel` | `GET /api/v1/profiles/neel` | `id=neel` | Status 200; `name="Neel"`, `is_cold_start=False`, `ratings_count >= 14`, taste cluster includes "Action" / "Sci-Fi". |
| `T1.1.3` | `test_get_profile_nitin` | `GET /api/v1/profiles/nitin` | `id=nitin` | Status 200; `name="Nitin"`, `is_cold_start=False`, `ratings_count >= 14`, taste cluster includes "Drama" / "Romance". |
| `T1.1.4` | `test_get_profile_mukesh` | `GET /api/v1/profiles/mukesh` | `id=mukesh` | Status 200; `name="Mukesh"`, `is_cold_start=True`, `ratings_count=0` initially. |
| `T1.1.5` | `test_get_nonexistent_profile` | `GET /api/v1/profiles/unknown_user` | `id=unknown_user` | Status 404 Not Found; error envelope with descriptive `detail`. |

### 3.2 Feature 2: Hero Billboard Section
| Test ID | Test Name | Target Endpoint | Stimulus / Input | Expected Result / Assertion |
|---|---|---|---|---|
| `T1.2.1` | `test_billboard_neel_action_scifi` | `GET /api/v1/recommendations/billboard?profile_id=neel` | `profile_id=neel` | Status 200; hero movie has genres intersecting `{"Action", "Sci-Fi", "Adventure"}`; match % >= 85%. |
| `T1.2.2` | `test_billboard_nitin_drama_romance` | `GET /api/v1/recommendations/billboard?profile_id=nitin` | `profile_id=nitin` | Status 200; hero movie has genres intersecting `{"Drama", "Romance"}`; match % >= 85%. |
| `T1.2.3` | `test_billboard_mukesh_cold_start` | `GET /api/v1/recommendations/billboard?profile_id=mukesh` | `profile_id=mukesh` (0 ratings) | Status 200; returns popular baseline hero title without 500 error; includes title, synopsis, poster. |
| `T1.2.4` | `test_billboard_metadata_completeness` | `GET /api/v1/recommendations/billboard?profile_id=neel` | `profile_id=neel` | Status 200; payload contains `movie_id`, `title`, `synopsis`, `backdrop_path`, `match_percentage`, `genres`, `year`. |
| `T1.2.5` | `test_billboard_match_score_bounds` | `GET /api/v1/recommendations/billboard?profile_id=neel` | `profile_id=neel` | Status 200; `50 <= match_percentage <= 100` and integer type. |

### 3.3 Feature 3: Recommendation Carousels
| Test ID | Test Name | Target Endpoint | Stimulus / Input | Expected Result / Assertion |
|---|---|---|---|---|
| `T1.3.1` | `test_top_picks_carousel_structure` | `GET /api/v1/profiles/neel/recommendations?limit=10` | `limit=10` | Status 200; returns 10 items; scores strictly descending: `score[i] >= score[i+1]`. |
| `T1.3.2` | `test_because_you_liked_carousel` | `GET /api/v1/recommendations/because-you-liked?profile_id=neel` | `profile_id=neel` | Status 200; payload contains `seed_movie` and non-empty `recommendations` list; seed movie is among user's high-rated titles. |
| `T1.3.3` | `test_also_watched_association_rules` | `GET /api/v1/recommendations/also-watched/2571` | `movie_id=2571` (The Matrix) | Status 200; returns association rules co-occurrence lift items; every item has `lift > 1.0`. |
| `T1.3.4` | `test_genre_carousel_filtering` | `GET /api/v1/movies/search?genre=Action&limit=10` | `genre=Action` | Status 200; 100% of returned items have "Action" in their genres array. |
| `T1.3.5` | `test_carousels_no_unrated_duplicates` | `GET /api/v1/profiles/neel/recommendations?limit=20` | `profile_id=neel` | Status 200; no duplicate movie IDs in top recommendations. |

### 3.4 Feature 4: Title Detail Modal & Interactive Ratings
| Test ID | Test Name | Target Endpoint | Stimulus / Input | Expected Result / Assertion |
|---|---|---|---|---|
| `T1.4.1` | `test_movie_detail_schema` | `GET /api/v1/movies/1` | `movie_id=1` (Toy Story) | Status 200; returns `title="Toy Story"`, `year=1995`, `genres`, `synopsis`, `cast`, `director`. |
| `T1.4.2` | `test_movie_detail_nonexistent` | `GET /api/v1/movies/999999` | `movie_id=999999` | Status 404 Not Found; error envelope with descriptive `detail`. |
| `T1.4.3` | `test_submit_rating_valid` | `POST /api/v1/profiles/neel/ratings` | `{"movie_id": 1, "rating": 4.5}` | Status 200; returns `{"status": "ok", "ratings_count": int, "unlocked": bool}`; ratings count increments. |
| `T1.4.4` | `test_more_like_this_items` | `GET /api/v1/recommendations/also-watched/1` | `movie_id=1` | Status 200; returns related titles with non-negative similarity/lift. |
| `T1.4.5` | `test_starter_movies_grid` | `GET /api/v1/movies/starter` | None | Status 200; returns 24 curated popular starter titles spanning diverse genres. |

### 3.5 Feature 5: Model Lab Dashboard
| Test ID | Test Name | Target Endpoint | Stimulus / Input | Expected Result / Assertion |
|---|---|---|---|---|
| `T1.5.1` | `test_leaderboard_all_models` | `GET /api/v1/model-lab/leaderboard` | None | Status 200; contains metrics for `popularity`, `item_knn`, `funk_svd`; Funk-SVD & Item-KNN have higher NDCG@10 and lower RMSE than Popularity. |
| `T1.5.2` | `test_convergence_curve_epochs` | `GET /api/v1/model-lab/convergence` | None | Status 200; returns list of epoch points; epoch 1 loss > epoch 20 loss (downward convergence). |
| `T1.5.3` | `test_model_compare_side_by_side` | `GET /api/v1/model-lab/compare?profile_id=neel` | `profile_id=neel` | Status 200; returns parallel recommendation lists for `item_knn` and `funk_svd`. |
| `T1.5.4` | `test_explain_funk_svd_math` | `GET /api/v1/model-lab/explain?profile_id=neel&movie_id=2571&model=funk_svd` | `funk_svd` | Status 200; returns `global_mean`, `user_bias`, `item_bias`, `latent_dot_product`, `predicted_score`. Sum satisfies: $\hat{r} = \mu + b_u + b_i + \mathbf{p}_u \cdot \mathbf{q}_i$. |
| `T1.5.5` | `test_explain_item_knn_math` | `GET /api/v1/model-lab/explain?profile_id=neel&movie_id=2571&model=item_knn` | `item_knn` | Status 200; returns `user_mean`, `neighbors` with adjusted cosine similarities and user ratings. |

---

## 4. Tier 2: Boundary & Corner Cases (>= 5 Tests per Category)

Tier 2 verifies strict constraint enforcement, edge conditions, malformed input handling, and graceful degradation.

### 4.1 Category 1: Mukesh Cold-Start Rating Threshold (Furtado & Singh 2020)
*Rule: Cold-start users require >= 6 ratings before personalized recommendations unlock.*
| Test ID | Test Name | Stimulus / Condition | Expected Result / Assertion |
|---|---|---|---|
| `T2.1.1` | `test_mukesh_0_ratings_forbidden` | Mukesh has 0 ratings; `GET /api/v1/profiles/mukesh/recommendations` | Status 403 Forbidden; detail specifies at least 6 ratings required. |
| `T2.1.2` | `test_mukesh_1_rating_forbidden` | Rate 1 movie; `GET /api/v1/profiles/mukesh/recommendations` | Status 403 Forbidden; detail indicates 5 more ratings needed. |
| `T2.1.3` | `test_mukesh_5_ratings_forbidden` | Rate 5 movies; `GET /api/v1/profiles/mukesh/recommendations` | Status 403 Forbidden; boundary condition $5 < 6$ enforced. |
| `T2.1.4` | `test_mukesh_6_ratings_unlocked` | Rate 6th movie; `GET /api/v1/profiles/mukesh/recommendations` | Status 200 OK; recommendation list unlocks immediately! |
| `T2.1.5` | `test_mukesh_7_ratings_stable` | Rate 7th movie; `GET /api/v1/profiles/mukesh/recommendations` | Status 200 OK; profile remains unlocked and recommendations re-ranked. |

### 4.2 Category 2: Rating Value Limits & Validation
| Test ID | Test Name | Stimulus / Condition | Expected Result / Assertion |
|---|---|---|---|
| `T2.2.1` | `test_rating_minimum_boundary_1_0` | Submit `rating=1.0` | Status 200 OK; accepted as minimum valid star rating. |
| `T2.2.2` | `test_rating_maximum_boundary_5_0` | Submit `rating=5.0` | Status 200 OK; accepted as maximum valid star rating. |
| `T2.2.3` | `test_rating_below_minimum_rejected` | Submit `rating=0.0` or `-1.0` | Status 422 Unprocessable Entity; rejection validation error. |
| `T2.2.4` | `test_rating_above_maximum_rejected` | Submit `rating=5.5` or `10.0` | Status 422 Unprocessable Entity; rejection validation error. |
| `T2.2.5` | `test_rerating_updates_existing` | Submit rating 3.0 for Movie X, then rating 5.0 for Movie X | Status 200 OK; rating count does NOT increase duplicate; rating updated. |

### 4.3 Category 3: Catalog Search Edge Cases & Adversarial Inputs
| Test ID | Test Name | Stimulus / Condition | Expected Result / Assertion |
|---|---|---|---|
| `T2.3.1` | `test_search_empty_query` | `GET /api/v1/movies/search?q=` | Status 200 OK; returns empty list or default starter titles without 500 error. |
| `T2.3.2` | `test_search_whitespace_only` | `GET /api/v1/movies/search?q=%20%20%20` | Status 200 OK; trimmed query handled safely. |
| `T2.3.3` | `test_search_special_regex_characters` | `GET /api/v1/movies/search?q=(.*)+[\w]?` | Status 200 OK; meta-characters escaped; no unhandled regex exception. |
| `T2.3.4` | `test_search_nonexistent_token` | `GET /api/v1/movies/search?q=xyzqwertynotfound999` | Status 200 OK; returns `[]` empty list with 0 matches. |
| `T2.3.5` | `test_search_single_character` | `GET /api/v1/movies/search?q=M` | Status 200 OK; returns valid titles matching 'M' within limit. |

### 4.4 Category 4: Missing Assets & Graceful Fallbacks
| Test ID | Test Name | Stimulus / Condition | Expected Result / Assertion |
|---|---|---|---|
| `T2.4.1` | `test_missing_poster_fallback_present` | Inspect movie item with null TMDB poster | `poster_path` returns deterministic SVG/placeholder URI or non-null fallback string. |
| `T2.4.2` | `test_missing_backdrop_fallback` | Inspect movie item with null TMDB backdrop | `backdrop_path` returns fallback URI or styled dark gradient indicator. |
| `T2.4.3` | `test_empty_genres_handling` | Movie with unassigned genre list | Handles safely; returns `genres: []` rather than null pointer exception. |
| `T2.4.4` | `test_tmdb_timeout_resilience` | Simulate offline TMDB or invalid key | Movie details endpoint returns MovieLens local metadata without 502/504 gateway error. |
| `T2.4.5` | `test_unrated_movie_cold_item_similarity` | Request `also-watched` for item with zero co-occurrences | Status 200 OK; returns empty list `[]` or popular fallback without crashing. |

### 4.5 Category 5: Pagination & Limit Bounds
| Test ID | Test Name | Stimulus / Condition | Expected Result / Assertion |
|---|---|---|---|
| `T2.5.1` | `test_recommendation_limit_minimum_1` | `GET /api/v1/profiles/neel/recommendations?limit=1` | Returns exactly 1 top recommendation. |
| `T2.5.2` | `test_recommendation_limit_standard_20` | `GET /api/v1/profiles/neel/recommendations?limit=20` | Returns exactly 20 items. |
| `T2.5.3` | `test_recommendation_limit_zero_rejected` | `GET /api/v1/profiles/neel/recommendations?limit=0` | Status 422 Unprocessable Entity; limit must be >= 1. |
| `T2.5.4` | `test_recommendation_limit_negative_rejected` | `GET /api/v1/profiles/neel/recommendations?limit=-5` | Status 422 Unprocessable Entity. |
| `T2.5.5` | `test_recommendation_limit_capped_100` | `GET /api/v1/profiles/neel/recommendations?limit=500` | Status 200/422; payload safely capped at maximum (e.g. 100) or rejected. |

---

## 5. Tier 3: Cross-Feature Interactions (Pairwise Verification)

Tier 3 verifies end-to-end multi-module contracts and state synchronization between components.

### 5.1 Neel vs Nitin Contrast & Low Jaccard Similarity
- **Contract Rule**: Neel (Action/Sci-Fi) and Nitin (Drama/Romance) must receive distinctly divergent recommendation rows reflecting their distinct preference distributions.
- **Mathematical Specification**:
  $$Jaccard(T_{\text{Neel}}, T_{\text{Nitin}}) = \frac{|T_{\text{Neel}} \cap T_{\text{Nitin}}|}{|T_{\text{Neel}} \cup T_{\text{Nitin}}|} \le 0.20$$
  where $T$ represents the top 10 recommended movie titles.
- **Genre Concentration**:
  $$\frac{\text{Count}(\text{Action} \lor \text{Sci-Fi} \in T_{\text{Neel}})}{|T_{\text{Neel}}|} \ge 0.60$$
  $$\frac{\text{Count}(\text{Drama} \lor \text{Romance} \in T_{\text{Nitin}})}{|T_{\text{Nitin}}|} \ge 0.60$$

### 5.2 Real-Time Online Fold-in Without Retrain (< 100ms)
- **Contract Rule**: When a user rates a new movie in the detail modal, the ML user latent factor $\mathbf{p}_u$ is updated via closed-form Ridge regression:
  $$\mathbf{p}_u = \left( \sum_{i \in R_u} \mathbf{q}_i \mathbf{q}_i^T + \lambda \mathbf{I} \right)^{-1} \sum_{i \in R_u} (r_{ui} - \mu - b_i) \mathbf{q}_i$$
- **Latency Specification**: Rating submission, analytical fold-in solution, and cache invalidation execute in $< 100\text{ms}$ (measured via response time or `fold_in_time_ms`).
- **Reactivity Specification**: The subsequent `GET /api/v1/profiles/{id}/recommendations` reflects the new rating's genre/latent bias without requiring an offline training job (`recsys train-all`).

### 5.3 Model Lab Toggle Synchronization (Item-KNN vs Funk-SVD)
- **Contract Rule**: Toggling between Item-KNN and Funk-SVD in the Model Lab selector or browse view must yield different predicted scores and item rank orderings:
  $$\exists i : \text{Score}_{\text{Item-KNN}}(i) \ne \text{Score}_{\text{Funk-SVD}}(i)$$
  $$\text{Ranking}_{\text{Item-KNN}} \ne \text{Ranking}_{\text{Funk-SVD}}$$
- Furthermore, the formula breakdown returned by `/model-lab/explain` strictly matches the active model's mathematical formulation.

### 5.4 Mukesh Onboarding Transition & Browse Unlock
- **Contract Rule**: The transition of Mukesh from unrated cold-start to active subscriber:
  1. Ratings count: $0 \rightarrow 5$ (Status 403 Forbidden on recommendations).
  2. 6th rating added (Status 200 OK on rating endpoint; `unlocked: true`, `is_cold_start: false`).
  3. Subsequent recommendations endpoint returns Status 200 OK with personalized items tailored to the 6 seeded ratings.

---

## 6. Tier 4: Real-World Application Scenarios (Full User Journeys)

Tier 4 validates complete end-to-end user lifecycles simulating real browser user sessions.

### 6.1 Scenario 1: Mukesh Complete Cold-Start Onboarding Journey (`test_mukesh_journey.py`)
1. **Initial Profile Exploration**:
   - Mukesh logs in / opens profile picker.
   - Verifies profile shows 0 ratings and `is_cold_start: true`.
2. **Access Gating Enforcement**:
   - Mukesh attempts to load personalized browse page.
   - Enforces 403 Forbidden block with descriptive prompt.
3. **Onboarding Search & Rating Pipeline**:
   - Fetches starter catalog grid (`GET /api/v1/movies/starter`).
   - Rates 6 distinct titles across target genres (e.g., 4 Action movies with 5 stars, 2 Romances with 1 star).
   - Tracks intermediate progress ($1/6, 2/6, \dots, 6/6$).
4. **Recommendation Unlock & Personalization**:
   - 6th rating flips profile status to `is_cold_start: false`.
   - Fetches personalized recommendations: verified to reflect strong Action bias (consistent with the 4 high ratings).

### 6.2 Scenario 2: Multi-Persona Catalog Auditing (`test_multi_persona_audit.py`)
1. **Concurrent Persona Sessions**:
   - Simultaneously queries recommendations for Neel, Nitin, and Mukesh (unlocked).
2. **Preference Isolation**:
   - Mutating Neel's ratings (adding ratings for Horror) alters Neel's recommendations without corrupting Nitin's or Mukesh's factor vectors or recommendations.
3. **Session Cache Invalidation**:
   - Validates that TTL/in-memory caches properly key on `profile_id` and invalidate only the mutated profile.

### 6.3 Scenario 3: Model Lab Algorithmic Deep Dive (`test_model_lab_deep_dive.py`)
1. **Leaderboard Audit**:
   - Audits that all 6 evaluation metrics (RMSE, MAE, Precision@10, Recall@10, NDCG@10, Catalog Coverage@10) conform to expected ordering:
     $$\text{NDCG}_{\text{Funk-SVD}} > \text{NDCG}_{\text{Item-KNN}} > \text{NDCG}_{\text{Popularity}}$$
     $$\text{RMSE}_{\text{Funk-SVD}} < \text{RMSE}_{\text{Item-KNN}} < \text{RMSE}_{\text{Popularity}}$$
2. **Mathematical Explainability Proof**:
   - Queries Funk-SVD explanation: verifies exact formula reconstruction $\hat{r} = \mu + b_u + b_i + \mathbf{p}_u \cdot \mathbf{q}_i$.
   - Queries Item-KNN explanation: verifies neighbor cosine weights $\sum s_{ij} (r_{uj} - \bar{r}_u) / \sum |s_{ij}|$.
3. **Training Convergence Proof**:
   - Validates that validation RMSE across epochs exhibits monotonic reduction or stable convergence.

---

## 7. Execution Commands & Environment Setup

### 7.1 Running the Automated E2E Suite
```bash
# Execute entire E2E test suite
uv run pytest tests/e2e -v

# Execute specific tiers
uv run pytest tests/e2e/tier1_features -v
uv run pytest tests/e2e/tier2_boundary_corner -v
uv run pytest tests/e2e/tier3_cross_feature -v
uv run pytest tests/e2e/tier4_real_world -v

# Run with target server URL (e.g. against running backend)
CINEMATCH_BASE_URL="http://localhost:8000" uv run pytest tests/e2e -v
```
