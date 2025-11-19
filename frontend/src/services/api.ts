/**
 * APIサービス
 */

import axios from 'axios';
import type {
  ModelInfo,
  PredictionRequest,
  RacePrediction,
  MultiModelPredictionRequest,
  FeatureImportanceResponse,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// モデル管理API
export const modelsApi = {
  list: async (): Promise<{ models: ModelInfo[]; total: number }> => {
    const response = await api.get('/api/models');
    return response.data;
  },

  get: async (modelName: string): Promise<ModelInfo> => {
    const response = await api.get(`/api/models/${modelName}`);
    return response.data;
  },

  delete: async (modelName: string): Promise<void> => {
    await api.delete(`/api/models/${modelName}`);
  },
};

// 推論API
export const predictionApi = {
  predict: async (request: PredictionRequest): Promise<RacePrediction> => {
    const response = await api.post('/api/predict', request);
    return response.data;
  },

  compare: async (request: MultiModelPredictionRequest) => {
    const response = await api.post('/api/predict/compare', request);
    return response.data;
  },

  getFeatureImportance: async (
    modelPath: string,
    modelType: string,
    topN: number = 20
  ): Promise<FeatureImportanceResponse> => {
    const response = await api.post('/api/predict/feature-importance', {
      model_path: modelPath,
      model_type: modelType,
      top_n: topN,
    });
    return response.data;
  },
};

export default api;
