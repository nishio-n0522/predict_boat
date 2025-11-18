/**
 * モデル比較ページ
 */

import React, { useState, useEffect } from 'react';
import { Play } from 'lucide-react';
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, Legend, ResponsiveContainer } from 'recharts';
import { modelsApi, predictionApi } from '../services/api';
import type { ModelInfo } from '../types';

export default function ComparisonPage() {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [selectedModels, setSelectedModels] = useState<Record<string, string>>({});
  const [raceDate, setRaceDate] = useState('2023-08-01');
  const [stadiumId, setStadiumId] = useState(1);
  const [raceIndex, setRaceIndex] = useState(1);
  const [comparison, setComparison] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadModels();
  }, []);

  const loadModels = async () => {
    try {
      const data = await modelsApi.list();
      setModels(data.models);
    } catch (error) {
      console.error('Failed to load models:', error);
    }
  };

  const toggleModel = (modelName: string, modelPath: string) => {
    const newSelection = { ...selectedModels };
    if (newSelection[modelName]) {
      delete newSelection[modelName];
    } else {
      newSelection[modelName] = modelPath;
    }
    setSelectedModels(newSelection);
  };

  const runComparison = async () => {
    if (Object.keys(selectedModels).length === 0) {
      alert('少なくとも1つのモデルを選択してください');
      return;
    }

    setLoading(true);
    try {
      const result = await predictionApi.compare({
        model_paths: selectedModels,
        race_date: raceDate,
        stadium_id: stadiumId,
        race_index: raceIndex,
      });
      setComparison(result);
    } catch (error) {
      console.error('Comparison failed:', error);
      alert('比較に失敗しました');
    } finally {
      setLoading(false);
    }
  };

  // レーダーチャート用データ
  const prepareRadarData = () => {
    if (!comparison || !comparison.predictions) return [];

    const boatNumbers = [1, 2, 3, 4, 5, 6];
    return boatNumbers.map((boatNum) => {
      const data: any = { boat: `${boatNum}号艇` };

      Object.entries(comparison.predictions).forEach(([modelName, prediction]: [string, any]) => {
        const boat = prediction.boats.find((b: any) => b.boat_number === boatNum);
        if (boat) {
          data[modelName] = (boat.probability * 100).toFixed(1);
        }
      });

      return data;
    });
  };

  return (
    <div className="max-w-7xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">モデル比較</h1>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-6">
        {/* 左側: モデル選択 */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">モデル選択</h2>
            <div className="space-y-2">
              {models.map((model) => (
                <label key={model.name} className="flex items-center gap-2 p-2 hover:bg-gray-50 rounded cursor-pointer">
                  <input
                    type="checkbox"
                    checked={!!selectedModels[model.name]}
                    onChange={() => toggleModel(model.name, model.path)}
                    className="w-4 h-4"
                  />
                  <div className="flex-1">
                    <div className="font-medium text-sm">{model.name}</div>
                    <div className="text-xs text-gray-500">{model.model_type}</div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* レース情報 */}
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

            <button
              onClick={runComparison}
              disabled={Object.keys(selectedModels).length === 0 || loading}
              className="w-full mt-4 bg-blue-500 hover:bg-blue-600 text-white py-3 px-6 rounded-lg font-semibold flex items-center justify-center gap-2 disabled:bg-gray-300"
            >
              {loading ? (
                <div className="w-5 h-5 border-4 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <Play className="w-5 h-5" />
              )}
              比較を実行
            </button>
          </div>
        </div>

        {/* 右側: 比較結果 */}
        <div className="lg:col-span-3 space-y-6">
          {comparison && (
            <>
              {/* レーダーチャート */}
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-xl font-semibold mb-4">各艇の確率比較</h2>
                <ResponsiveContainer width="100%" height={400}>
                  <RadarChart data={prepareRadarData()}>
                    <PolarGrid />
                    <PolarAngleAxis dataKey="boat" />
                    <PolarRadiusAxis angle={90} domain={[0, 100]} />
                    {Object.keys(selectedModels).map((modelName, index) => (
                      <Radar
                        key={modelName}
                        name={modelName}
                        dataKey={modelName}
                        stroke={`hsl(${index * 120}, 70%, 50%)`}
                        fill={`hsl(${index * 120}, 70%, 50%)`}
                        fillOpacity={0.3}
                      />
                    ))}
                    <Legend />
                  </RadarChart>
                </ResponsiveContainer>
              </div>

              {/* 推奨艇の比較 */}
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-xl font-semibold mb-4">推奨艇の比較</h2>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left p-3">モデル</th>
                        <th className="text-left p-3">推奨3艇</th>
                        <th className="text-left p-3">期待的中率</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(comparison.predictions).map(([modelName, prediction]: [string, any]) => (
                        <tr key={modelName} className="border-b hover:bg-gray-50">
                          <td className="p-3 font-medium">{modelName}</td>
                          <td className="p-3">
                            <span className="inline-block bg-blue-100 text-blue-800 px-3 py-1 rounded font-mono">
                              {prediction.recommended_boats.join(' - ')}
                            </span>
                          </td>
                          <td className="p-3">{(prediction.expected_hit_rate * 100).toFixed(1)}%</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* モデル間一致度 */}
              {comparison.comparison?.agreement_matrix && (
                <div className="bg-white rounded-lg shadow p-6">
                  <h2 className="text-xl font-semibold mb-4">モデル間一致度</h2>
                  <div className="grid grid-cols-2 gap-4">
                    {Object.entries(comparison.comparison.agreement_matrix).map(([key, value]: [string, any]) => (
                      <div key={key} className="bg-gray-50 rounded p-4">
                        <div className="text-sm text-gray-600 mb-1">{key.replace('_vs_', ' vs ')}</div>
                        <div className="flex items-center gap-2">
                          <div className="flex-1 bg-gray-200 rounded-full h-4">
                            <div
                              className="bg-green-500 h-4 rounded-full"
                              style={{ width: `${value * 100}%` }}
                            />
                          </div>
                          <div className="font-semibold">{(value * 100).toFixed(0)}%</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 各艇の統計 */}
              {comparison.comparison?.boat_avg_probabilities && (
                <div className="bg-white rounded-lg shadow p-6">
                  <h2 className="text-xl font-semibold mb-4">各艇の統計（全モデル平均）</h2>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    {Object.entries(comparison.comparison.boat_avg_probabilities).map(([boat, stats]: [string, any]) => (
                      <div key={boat} className="bg-gray-50 rounded p-4">
                        <div className="text-lg font-bold mb-2">{boat}号艇</div>
                        <div className="space-y-1 text-sm">
                          <div>平均: {(stats.mean * 100).toFixed(1)}%</div>
                          <div>標準偏差: {(stats.std * 100).toFixed(1)}%</div>
                          <div className="text-gray-600">
                            範囲: {(stats.min * 100).toFixed(1)}% ~ {(stats.max * 100).toFixed(1)}%
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}

          {!comparison && (
            <div className="bg-white rounded-lg shadow p-12 text-center text-gray-500">
              モデルを選択して「比較を実行」ボタンをクリックしてください
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
