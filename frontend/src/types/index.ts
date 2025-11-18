/**
 * 型定義
 */

export type ModelType = 'lightgbm' | 'transformer' | 'bayesian';

export interface TrainingRequest {
  model_type: ModelType;
  dataset_path?: string;
  output_path?: string;
  start_date?: string;
  end_date?: string;
  parameters?: Record<string, any>;
}

export interface TrainingProgress {
  status: 'starting' | 'running' | 'completed' | 'failed';
  progress: number;
  message: string;
  current_step?: string;
  metrics?: Record<string, number>;
}

export interface ModelInfo {
  name: string;
  model_type: string;
  path: string;
  created_at?: string;
  file_size?: number;
  metadata?: Record<string, any>;
}

export interface BoatPrediction {
  boat_number: number;
  probability: number;
  std?: number;
  ci_lower?: number;
  ci_upper?: number;
}

export interface RacePrediction {
  race_date: string;
  stadium_id: number;
  race_index: number;
  boats: BoatPrediction[];
  recommended_boats: number[];
  expected_hit_rate: number;
  has_uncertainty: boolean;
}

export interface PredictionRequest {
  model_path: string;
  model_type: ModelType;
  race_date: string;
  stadium_id: number;
  race_index?: number;
}

export interface MultiModelPredictionRequest {
  model_paths: Record<string, string>;
  race_date: string;
  stadium_id: number;
  race_index: number;
}

export interface FeatureImportance {
  feature_name: string;
  importance: number;
  rank: number;
}

export interface FeatureImportanceResponse {
  model_type: string;
  method: string;
  features: FeatureImportance[];
}
