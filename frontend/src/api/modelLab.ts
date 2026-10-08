import {
  ModelMetrics,
  ConvergenceData,
  ModelComparisonRow,
  ExplainabilityData,
} from '../types/modelLab';
import { apiFetch } from './client';
import {
  MOCK_LEADERBOARD,
  MOCK_CONVERGENCE,
  MOCK_SIDE_BY_SIDE,
  getMockExplainability,
} from '../data/mockModelLab';

export async function fetchLeaderboard(): Promise<ModelMetrics[]> {
  try {
    return await apiFetch<ModelMetrics[]>('/model-lab/leaderboard');
  } catch {
    return MOCK_LEADERBOARD;
  }
}

export async function fetchConvergence(): Promise<ConvergenceData> {
  try {
    return await apiFetch<ConvergenceData>('/model-lab/convergence');
  } catch {
    return MOCK_CONVERGENCE;
  }
}

export async function fetchComparison(profileId = 'neel'): Promise<ModelComparisonRow[]> {
  try {
    return await apiFetch<ModelComparisonRow[]>(`/model-lab/compare?profile_id=${profileId}`);
  } catch {
    return MOCK_SIDE_BY_SIDE;
  }
}

export async function fetchExplainability(
  profileId: string,
  movieId: number,
  model: 'funk_svd' | 'item_knn' = 'funk_svd',
  title = 'The Matrix (1999)'
): Promise<ExplainabilityData> {
  try {
    return await apiFetch<ExplainabilityData>(
      `/model-lab/explain?profile_id=${profileId}&movie_id=${movieId}&model=${model}`
    );
  } catch {
    return getMockExplainability(movieId, title, model);
  }
}
