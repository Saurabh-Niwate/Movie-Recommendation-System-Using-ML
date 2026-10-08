export interface ModelMetrics {
  model_name: string;
  display_name: string;
  ndcg_10: number;
  rmse: number;
  mae: number;
  precision_10: number;
  recall_10: number;
  coverage_10: number;
  description: string;
}

export interface ConvergenceEpoch {
  epoch: number;
  train_loss: number;
  val_rmse: number;
}

export interface ConvergenceData {
  epochs: ConvergenceEpoch[];
  best_epoch: number;
  training_time_sec: number;
  algorithm: string;
}

export interface ModelComparisonRow {
  rank: number;
  movie_id: number;
  title: string;
  genres: string[];
  item_knn_score: number;
  item_knn_match: number;
  funk_svd_score: number;
  funk_svd_match: number;
}

export interface LatentBreakdown {
  factor_index: number;
  user_val: number;
  item_val: number;
  product: number;
}

export interface FunkSVDExplain {
  mu: number;
  user_bias: number;
  item_bias: number;
  dot_product: number;
  latent_breakdown: LatentBreakdown[];
  predicted_score: number;
}

export interface ItemKNNNeighbor {
  movie_id: number;
  title: string;
  similarity: number;
  rating: number;
  contribution: number;
}

export interface ItemKNNExplain {
  user_mean: number;
  neighbors: ItemKNNNeighbor[];
  predicted_score: number;
}

export interface ExplainabilityData {
  movie_id: number;
  title: string;
  model: 'funk_svd' | 'item_knn';
  funk_svd?: FunkSVDExplain;
  item_knn?: ItemKNNExplain;
}
