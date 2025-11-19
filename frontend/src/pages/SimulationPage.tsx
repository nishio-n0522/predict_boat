/**
 * シミュレーション結果表示ページ
 */

import React, { useState, useEffect } from 'react';
import { Play, TrendingUp, TrendingDown } from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
} from 'recharts';
import { modelsApi } from '../services/api';
import type { ModelInfo } from '../types';

const API_BASE_URL = 'http://localhost:8000';

interface SimulationResult {
  request_info: any;
  models: ModelSimulationResult[];
  comparison: any;
}

interface ModelSimulationResult {
  model_name: string;
  metrics: SimulationMetrics;
  time_series: TimeSeriesDataPoint[];
  race_results: RaceSimulationResult[];
}

interface SimulationMetrics {
  total_races: number;
  hit_count: number;
  hit_rate: number;
  total_bet: number;
  total_refund: number;
  total_profit: number;
  recovery_rate: number;
  max_profit: number;
  max_loss: number;
  consecutive_wins: number;
  consecutive_losses: number;
}

interface TimeSeriesDataPoint {
  date: string;
  cumulative_profit: number;
  cumulative_bet: number;
  cumulative_refund: number;
  recovery_rate: number;
  race_count: number;
}

interface RaceSimulationResult {
  race_date: string;
  stadium_id: number;
  stadium_name: string;
  race_index: number;
  predicted_boats: number[];
  actual_order: number[];
  bet_amount: number;
  refund_amount: number;
  profit: number;
  hit: boolean;
}

const COLORS = [
  '#3b82f6', // blue
  '#ef4444', // red
  '#10b981', // green
  '#f59e0b', // amber
  '#8b5cf6', // purple
  '#ec4899', // pink
];

export default function SimulationPage() {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [selectedModels, setSelectedModels] = useState<Record<string, string>>({});
  const [startDate, setStartDate] = useState('2023-07-01');
  const [endDate, setEndDate] = useState('2023-08-01');
  const [betType, setBetType] = useState('boxed_trifecta');
  const [betAmount, setBetAmount] = useState(100);
  const [result, setResult] = useState<SimulationResult | null>(null);
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

  const runSimulation = async () => {
    if (Object.keys(selectedModels).length === 0) {
      alert('少なくとも1つのモデルを選択してください');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/simulation/run`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model_paths: selectedModels,
          start_date: startDate,
          end_date: endDate,
          bet_type: betType,
          bet_amount: betAmount,
        }),
      });

      if (!response.ok) {
        throw new Error('Simulation failed');
      }

      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error('Simulation failed:', error);
      alert('シミュレーションに失敗しました');
    } finally {
      setLoading(false);
    }
  };

  // 時系列データを準備
  const prepareTimeSeriesData = () => {
    if (!result || result.models.length === 0) return [];

    // 全モデルの日付を収集
    const allDates = new Set<string>();
    result.models.forEach((model) => {
      model.time_series.forEach((point) => {
        allDates.add(point.date);
      });
    });

    // 日付ごとにデータを集約
    return Array.from(allDates)
      .sort()
      .map((date) => {
        const dataPoint: any = { date };
        result.models.forEach((model) => {
          const point = model.time_series.find((p) => p.date === date);
          if (point) {
            dataPoint[model.model_name] = point.cumulative_profit;
          }
        });
        return dataPoint;
      });
  };

  // モデル比較データを準備
  const prepareComparisonData = () => {
    if (!result) return [];

    return result.models.map((model) => ({
      name: model.model_name,
      hit_rate: (model.metrics.hit_rate * 100).toFixed(2),
      recovery_rate: model.metrics.recovery_rate.toFixed(2),
      profit: model.metrics.total_profit,
    }));
  };

  return (
    <div className="max-w-7xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">払い戻しシミュレーション</h1>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-6">
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
            <h2 className="text-xl font-semibold mb-4">シミュレーション設定</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">開始日</label>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">終了日</label>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">舟券種類</label>
                <select
                  value={betType}
                  onChange={(e) => setBetType(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg"
                >
                  <option value="boxed_trifecta">3連複ボックス</option>
                  <option value="trifecta">3連単ボックス</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">1点あたりの賭け金（円）</label>
                <input
                  type="number"
                  min="100"
                  step="100"
                  value={betAmount}
                  onChange={(e) => setBetAmount(parseInt(e.target.value))}
                  className="w-full px-3 py-2 border rounded-lg"
                />
              </div>
            </div>

            <button
              onClick={runSimulation}
              disabled={loading || Object.keys(selectedModels).length === 0}
              className="w-full mt-4 bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? (
                <>実行中...</>
              ) : (
                <>
                  <Play className="w-5 h-5" />
                  シミュレーション実行
                </>
              )}
            </button>
          </div>
        </div>

        {/* 右側: 結果表示 */}
        <div className="lg:col-span-3">
          {!result ? (
            <div className="bg-white rounded-lg shadow p-12 text-center text-gray-500">
              <p className="text-lg">モデルと期間を選択してシミュレーションを実行してください</p>
            </div>
          ) : (
            <div className="space-y-6">
              {/* メトリクスカード */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {result.models.map((model, index) => (
                  <div key={model.model_name} className="bg-white rounded-lg shadow p-6">
                    <h3 className="font-semibold text-lg mb-4 flex items-center gap-2">
                      <div
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: COLORS[index % COLORS.length] }}
                      />
                      {model.model_name}
                    </h3>
                    <div className="space-y-3 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">総レース数</span>
                        <span className="font-semibold">{model.metrics.total_races}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">的中数</span>
                        <span className="font-semibold">{model.metrics.hit_count}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">的中率</span>
                        <span className="font-semibold">
                          {(model.metrics.hit_rate * 100).toFixed(2)}%
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">回収率</span>
                        <span className="font-semibold">
                          {model.metrics.recovery_rate.toFixed(2)}%
                        </span>
                      </div>
                      <div className="flex justify-between border-t pt-2">
                        <span className="text-gray-600">総収支</span>
                        <span
                          className={`font-bold ${
                            model.metrics.total_profit >= 0 ? 'text-green-600' : 'text-red-600'
                          }`}
                        >
                          {model.metrics.total_profit >= 0 ? (
                            <TrendingUp className="inline w-4 h-4 mr-1" />
                          ) : (
                            <TrendingDown className="inline w-4 h-4 mr-1" />
                          )}
                          {model.metrics.total_profit.toLocaleString()}円
                        </span>
                      </div>
                      <div className="flex justify-between text-xs">
                        <span className="text-gray-600">最大連勝</span>
                        <span>{model.metrics.consecutive_wins}</span>
                      </div>
                      <div className="flex justify-between text-xs">
                        <span className="text-gray-600">最大連敗</span>
                        <span>{model.metrics.consecutive_losses}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* 収支の時系列グラフ */}
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-xl font-semibold mb-4">累積収支の推移</h3>
                <ResponsiveContainer width="100%" height={400}>
                  <LineChart data={prepareTimeSeriesData()}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    {result.models.map((model, index) => (
                      <Line
                        key={model.model_name}
                        type="monotone"
                        dataKey={model.model_name}
                        stroke={COLORS[index % COLORS.length]}
                        strokeWidth={2}
                        dot={false}
                      />
                    ))}
                  </LineChart>
                </ResponsiveContainer>
              </div>

              {/* モデル比較バーチャート */}
              {result.models.length > 1 && (
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-xl font-semibold mb-4">モデル比較</h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <h4 className="font-semibold mb-2 text-sm">的中率</h4>
                      <ResponsiveContainer width="100%" height={200}>
                        <BarChart data={prepareComparisonData()}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="name" />
                          <YAxis />
                          <Tooltip />
                          <Bar dataKey="hit_rate" fill="#3b82f6" />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                    <div>
                      <h4 className="font-semibold mb-2 text-sm">回収率</h4>
                      <ResponsiveContainer width="100%" height={200}>
                        <BarChart data={prepareComparisonData()}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="name" />
                          <YAxis />
                          <Tooltip />
                          <Bar dataKey="recovery_rate" fill="#10b981" />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                    <div>
                      <h4 className="font-semibold mb-2 text-sm">総収支</h4>
                      <ResponsiveContainer width="100%" height={200}>
                        <BarChart data={prepareComparisonData()}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="name" />
                          <YAxis />
                          <Tooltip />
                          <Bar dataKey="profit" fill="#f59e0b" />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
