/**
 * リアルタイムダッシュボードページ
 * 当日のレース予測と結果を表示
 */

import React, { useState, useEffect } from 'react';
import { RefreshCw, CheckCircle, Circle, Clock } from 'lucide-react';
import { modelsApi } from '../services/api';
import type { ModelInfo } from '../types';

const API_BASE_URL = 'http://localhost:8000';

interface DashboardData {
  target_date: string;
  races: RacePredictionWithResult[];
  summary: DashboardSummary;
}

interface RacePredictionWithResult {
  race_date: string;
  stadium_id: number;
  stadium_name: string;
  race_index: number;
  predicted_boats: Record<string, number[]>;
  actual_order: number[] | null;
  is_finished: boolean;
  results: Record<string, RaceResult> | null;
}

interface RaceResult {
  hit: boolean;
  bet_amount: number;
  refund_amount: number;
  profit: number;
}

interface DashboardSummary {
  total_races: number;
  finished_races: number;
  pending_races: number;
  model_summaries: Record<string, ModelSummary>;
}

interface ModelSummary {
  hits: number;
  hit_rate: number;
  total_bet: number;
  total_refund: number;
  profit: number;
  recovery_rate: number;
}

export default function DashboardPage() {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [selectedModels, setSelectedModels] = useState<Record<string, string>>({});
  const [targetDate, setTargetDate] = useState(new Date().toISOString().split('T')[0]);
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(false);

  useEffect(() => {
    loadModels();
  }, []);

  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;
    if (autoRefresh && Object.keys(selectedModels).length > 0) {
      interval = setInterval(() => {
        loadDashboard();
      }, 30000); // 30秒ごとに更新
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh, selectedModels, targetDate]);

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

  const loadDashboard = async () => {
    if (Object.keys(selectedModels).length === 0) {
      alert('少なくとも1つのモデルを選択してください');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/simulation/dashboard`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          target_date: targetDate,
          model_paths: selectedModels,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to load dashboard');
      }

      const result = await response.json();
      setData(result);
    } catch (error) {
      console.error('Failed to load dashboard:', error);
      alert('ダッシュボードの読み込みに失敗しました');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">リアルタイムダッシュボード</h1>
        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="w-4 h-4"
            />
            自動更新（30秒）
          </label>
          <button
            onClick={loadDashboard}
            disabled={loading}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 flex items-center gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            更新
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* 左側: 設定パネル */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">モデル選択</h2>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {models.map((model) => (
                <label
                  key={model.name}
                  className="flex items-center gap-2 p-2 hover:bg-gray-50 rounded cursor-pointer"
                >
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

          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">対象日</h2>
            <input
              type="date"
              value={targetDate}
              onChange={(e) => setTargetDate(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg"
            />
          </div>

          {/* サマリー */}
          {data && (
            <div className="bg-white rounded-lg shadow p-6 mt-6">
              <h2 className="text-xl font-semibold mb-4">サマリー</h2>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">総レース数</span>
                  <span className="font-semibold">{data.summary.total_races}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">終了</span>
                  <span className="font-semibold text-green-600">
                    {data.summary.finished_races}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">未確定</span>
                  <span className="font-semibold text-gray-500">
                    {data.summary.pending_races}
                  </span>
                </div>
              </div>

              {Object.keys(data.summary.model_summaries).length > 0 && (
                <div className="mt-4 pt-4 border-t">
                  <h3 className="font-semibold mb-2">モデル別成績</h3>
                  {Object.entries(data.summary.model_summaries).map(([name, summary]) => (
                    <div key={name} className="mb-4 p-3 bg-gray-50 rounded">
                      <div className="font-medium text-sm mb-2">{name}</div>
                      <div className="space-y-1 text-xs">
                        <div className="flex justify-between">
                          <span className="text-gray-600">的中率</span>
                          <span>{(summary.hit_rate * 100).toFixed(1)}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">回収率</span>
                          <span>{summary.recovery_rate.toFixed(1)}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">収支</span>
                          <span
                            className={summary.profit >= 0 ? 'text-green-600' : 'text-red-600'}
                          >
                            {summary.profit >= 0 ? '+' : ''}
                            {summary.profit.toLocaleString()}円
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* 右側: レース一覧 */}
        <div className="lg:col-span-3">
          {!data ? (
            <div className="bg-white rounded-lg shadow p-12 text-center text-gray-500">
              <p className="text-lg">モデルと日付を選択してダッシュボードを読み込んでください</p>
            </div>
          ) : (
            <div className="space-y-4">
              {data.races.map((race) => (
                <div key={`${race.stadium_id}-${race.race_index}`} className="bg-white rounded-lg shadow">
                  <div className="p-4 border-b bg-gray-50 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      {race.is_finished ? (
                        <CheckCircle className="w-5 h-5 text-green-600" />
                      ) : (
                        <Clock className="w-5 h-5 text-gray-400" />
                      )}
                      <div>
                        <h3 className="font-semibold">
                          {race.stadium_name} 第{race.race_index}レース
                        </h3>
                        <p className="text-sm text-gray-600">{race.race_date}</p>
                      </div>
                    </div>
                    <div className="text-sm">
                      {race.is_finished ? (
                        <span className="text-green-600 font-semibold">確定</span>
                      ) : (
                        <span className="text-gray-500">未確定</span>
                      )}
                    </div>
                  </div>

                  <div className="p-4">
                    {/* モデルごとの予測 */}
                    <div className="space-y-3">
                      {Object.entries(race.predicted_boats).map(([modelName, boats]) => {
                        const result = race.results?.[modelName];
                        const isHit = result?.hit ?? false;

                        return (
                          <div
                            key={modelName}
                            className={`p-3 rounded ${
                              race.is_finished
                                ? isHit
                                  ? 'bg-green-50 border border-green-200'
                                  : 'bg-red-50 border border-red-200'
                                : 'bg-gray-50'
                            }`}
                          >
                            <div className="flex items-center justify-between mb-2">
                              <div className="flex items-center gap-2">
                                <span className="font-medium text-sm">{modelName}</span>
                                {race.is_finished && (
                                  <>
                                    {isHit ? (
                                      <CheckCircle className="w-4 h-4 text-green-600" />
                                    ) : (
                                      <Circle className="w-4 h-4 text-red-400" />
                                    )}
                                  </>
                                )}
                              </div>
                              {result && (
                                <div className="text-sm">
                                  <span
                                    className={`font-semibold ${
                                      result.profit >= 0 ? 'text-green-600' : 'text-red-600'
                                    }`}
                                  >
                                    {result.profit >= 0 ? '+' : ''}
                                    {result.profit.toLocaleString()}円
                                  </span>
                                </div>
                              )}
                            </div>

                            <div className="flex items-center gap-4 text-sm">
                              <div>
                                <span className="text-gray-600">予測: </span>
                                <span className="font-semibold">
                                  {boats.join('-')}
                                </span>
                              </div>
                              {race.actual_order && (
                                <div>
                                  <span className="text-gray-600">結果: </span>
                                  <span className="font-semibold">
                                    {race.actual_order.slice(0, 3).join('-')}
                                  </span>
                                </div>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              ))}

              {data.races.length === 0 && (
                <div className="bg-white rounded-lg shadow p-12 text-center text-gray-500">
                  <p className="text-lg">対象日のレースデータがありません</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
