/**
 * 推論実行ページ
 */

import React, { useState, useEffect } from 'react';
import { Play, TrendingUp } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { modelsApi, predictionApi } from '../services/api';
import type { ModelInfo, RacePrediction, FeatureImportanceResponse } from '../types';

export default function PredictionPage() {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [selectedModel, setSelectedModel] = useState<ModelInfo | null>(null);
  const [raceDate, setRaceDate] = useState('2023-08-01');
  const [stadiumId, setStadiumId] = useState(1);
  const [raceIndex, setRaceIndex] = useState(1);

  const [prediction, setPrediction] = useState<RacePrediction | null>(null);
  const [featureImportance, setFeatureImportance] = useState<FeatureImportanceResponse | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadModels();
  }, []);

  const loadModels = async () => {
    try {
      const data = await modelsApi.list();
      setModels(data.models);
      if (data.models.length > 0) {
        setSelectedModel(data.models[0]);
      }
    } catch (error) {
      console.error('Failed to load models:', error);
    }
  };

  const runPrediction = async () => {
    if (!selectedModel) return;

    setLoading(true);
    try {
      const result = await predictionApi.predict({
        model_path: selectedModel.path,
        model_type: selectedModel.model_type as any,
        race_date: raceDate,
        stadium_id: stadiumId,
        race_index: raceIndex,
      });
      setPrediction(result);

      // 特徴量重要度も取得
      const importance = await predictionApi.getFeatureImportance(
        selectedModel.path,
        selectedModel.model_type,
        20
      );
      setFeatureImportance(importance);
    } catch (error) {
      console.error('Prediction failed:', error);
      alert('予測に失敗しました');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">レース予測</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        {/* 左側: 設定パネル */}
        <div className="lg:col-span-1 space-y-6">
          {/* モデル選択 */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">モデル選択</h2>
            <select
              value={selectedModel?.name || ''}
              onChange={(e) => {
                const model = models.find((m) => m.name === e.target.value);
                setSelectedModel(model || null);
              }}
              className="w-full px-3 py-2 border rounded-lg mb-2"
            >
              {models.map((model) => (
                <option key={model.name} value={model.name}>
                  {model.name} ({model.model_type})
                </option>
              ))}
            </select>
            {selectedModel && (
              <div className="text-sm text-gray-600 mt-2">
                <div>タイプ: {selectedModel.model_type}</div>
                {selectedModel.created_at && (
                  <div>作成日: {new Date(selectedModel.created_at).toLocaleDateString()}</div>
                )}
              </div>
            )}
          </div>

          {/* レース情報入力 */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">レース情報</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">レース日</label>
                <input
                  type="date"
                  value={raceDate}
                  onChange={(e) => setRaceDate(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">競艇場ID</label>
                <input
                  type="number"
                  min="1"
                  max="24"
                  value={stadiumId}
                  onChange={(e) => setStadiumId(parseInt(e.target.value))}
                  className="w-full px-3 py-2 border rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">レース番号</label>
                <input
                  type="number"
                  min="1"
                  max="12"
                  value={raceIndex}
                  onChange={(e) => setRaceIndex(parseInt(e.target.value))}
                  className="w-full px-3 py-2 border rounded-lg"
                />
              </div>
            </div>
          </div>

          {/* 予測実行ボタン */}
          <button
            onClick={runPrediction}
            disabled={!selectedModel || loading}
            className="w-full bg-blue-500 hover:bg-blue-600 text-white py-3 px-6 rounded-lg font-semibold flex items-center justify-center gap-2 disabled:bg-gray-300"
          >
            {loading ? (
              <div className="w-5 h-5 border-4 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <Play className="w-5 h-5" />
            )}
            予測を実行
          </button>
        </div>

        {/* 右側: 結果表示 */}
        <div className="lg:col-span-2 space-y-6">
          {/* 予測結果 */}
          {prediction && (
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold mb-4">予測結果</h2>

              {/* レース情報 */}
              <div className="bg-gray-50 rounded p-4 mb-4">
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">日付:</span> {prediction.race_date}
                  </div>
                  <div>
                    <span className="text-gray-600">場ID:</span> {prediction.stadium_id}
                  </div>
                  <div>
                    <span className="text-gray-600">レース:</span> {prediction.race_index}R
                  </div>
                </div>
              </div>

              {/* 各艇の確率 */}
              <div className="mb-6">
                <h3 className="font-semibold mb-3">各艇の3着以内確率</h3>
                <div className="space-y-2">
                  {prediction.boats.map((boat) => (
                    <div key={boat.boat_number} className="flex items-center gap-3">
                      <div className="w-12 text-center font-semibold">{boat.boat_number}号艇</div>
                      <div className="flex-1">
                        <div className="bg-gray-200 rounded-full h-8 relative">
                          <div
                            className="bg-blue-500 h-8 rounded-full flex items-center justify-end pr-2 text-white font-semibold text-sm transition-all"
                            style={{ width: `${boat.probability * 100}%` }}
                          >
                            {(boat.probability * 100).toFixed(1)}%
                          </div>
                        </div>
                      </div>
                      {boat.std !== undefined && (
                        <div className="w-24 text-xs text-gray-600">
                          ± {(boat.std * 100).toFixed(1)}%
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* 推奨購入 */}
              <div className="bg-blue-50 border-2 border-blue-200 rounded-lg p-4">
                <h3 className="font-semibold mb-2 flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-blue-600" />
                  3連単ボックス買い推奨
                </h3>
                <div className="text-2xl font-bold text-blue-600 mb-2">
                  {prediction.recommended_boats.join(' - ')} (6点)
                </div>
                <div className="text-sm text-gray-700">
                  期待的中率: {(prediction.expected_hit_rate * 100).toFixed(1)}%
                </div>
              </div>
            </div>
          )}

          {/* 特徴量重要度 */}
          {featureImportance && (
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold mb-4">
                特徴量重要度 ({featureImportance.method})
              </h2>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart
                  data={featureImportance.features.slice(0, 10)}
                  layout="vertical"
                  margin={{ left: 150 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis type="category" dataKey="feature_name" width={140} />
                  <Tooltip />
                  <Bar dataKey="importance" fill="#3b82f6" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
