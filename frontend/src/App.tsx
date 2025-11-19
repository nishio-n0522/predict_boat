/**
 * メインアプリケーション
 */

import React from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { Home, Brain, TrendingUp, GitCompare, BarChart3, Monitor } from 'lucide-react';
import TrainingPage from './pages/TrainingPage';
import PredictionPage from './pages/PredictionPage';
import ComparisonPage from './pages/ComparisonPage';
import SimulationPage from './pages/SimulationPage';
import DashboardPage from './pages/DashboardPage';

function HomePage() {
  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold mb-4">ボートレース予測AI</h1>
        <p className="text-xl text-gray-600">
          機械学習を用いたボートレース予測システム
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Link
          to="/training"
          className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition-shadow"
        >
          <Brain className="w-12 h-12 text-blue-500 mb-4" />
          <h2 className="text-2xl font-bold mb-2">モデル学習</h2>
          <p className="text-gray-600">
            LightGBM、Transformer、階層ベイズモデルの学習を実行
          </p>
        </Link>

        <Link
          to="/prediction"
          className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition-shadow"
        >
          <TrendingUp className="w-12 h-12 text-green-500 mb-4" />
          <h2 className="text-2xl font-bold mb-2">レース予測</h2>
          <p className="text-gray-600">
            学習済みモデルを使用してレース結果を予測
          </p>
        </Link>

        <Link
          to="/comparison"
          className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition-shadow"
        >
          <GitCompare className="w-12 h-12 text-purple-500 mb-4" />
          <h2 className="text-2xl font-bold mb-2">モデル比較</h2>
          <p className="text-gray-600">
            複数のモデルの予測結果を比較分析
          </p>
        </Link>

        <Link
          to="/simulation"
          className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition-shadow"
        >
          <BarChart3 className="w-12 h-12 text-orange-500 mb-4" />
          <h2 className="text-2xl font-bold mb-2">シミュレーション</h2>
          <p className="text-gray-600">
            過去のレースで舟券購入をシミュレーション
          </p>
        </Link>

        <Link
          to="/dashboard"
          className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition-shadow"
        >
          <Monitor className="w-12 h-12 text-red-500 mb-4" />
          <h2 className="text-2xl font-bold mb-2">ダッシュボード</h2>
          <p className="text-gray-600">
            当日のレース予測と結果をリアルタイム表示
          </p>
        </Link>
      </div>

      <div className="mt-12 bg-blue-50 rounded-lg p-6">
        <h3 className="text-xl font-bold mb-4">利用可能なモデル</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <h4 className="font-semibold text-blue-600">LightGBM</h4>
            <p className="text-sm text-gray-600">勾配ブースティング（高速・高精度）</p>
          </div>
          <div>
            <h4 className="font-semibold text-green-600">Transformer</h4>
            <p className="text-sm text-gray-600">時系列Transformer（解釈性重視）</p>
          </div>
          <div>
            <h4 className="font-semibold text-purple-600">階層ベイズ</h4>
            <p className="text-sm text-gray-600">不確実性定量化・部分プーリング</p>
          </div>
        </div>
      </div>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-100">
        {/* ナビゲーションバー */}
        <nav className="bg-white shadow-md">
          <div className="max-w-7xl mx-auto px-6 py-4">
            <div className="flex items-center justify-between">
              <Link to="/" className="flex items-center gap-2 text-xl font-bold">
                <Home className="w-6 h-6" />
                ボートレース予測AI
              </Link>
              <div className="flex gap-4">
                <Link
                  to="/training"
                  className="px-4 py-2 rounded hover:bg-gray-100 transition-colors"
                >
                  学習
                </Link>
                <Link
                  to="/prediction"
                  className="px-4 py-2 rounded hover:bg-gray-100 transition-colors"
                >
                  予測
                </Link>
                <Link
                  to="/comparison"
                  className="px-4 py-2 rounded hover:bg-gray-100 transition-colors"
                >
                  比較
                </Link>
                <Link
                  to="/simulation"
                  className="px-4 py-2 rounded hover:bg-gray-100 transition-colors"
                >
                  シミュレーション
                </Link>
                <Link
                  to="/dashboard"
                  className="px-4 py-2 rounded hover:bg-gray-100 transition-colors"
                >
                  ダッシュボード
                </Link>
              </div>
            </div>
          </div>
        </nav>

        {/* コンテンツ */}
        <main className="py-8">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/training" element={<TrainingPage />} />
            <Route path="/prediction" element={<PredictionPage />} />
            <Route path="/comparison" element={<ComparisonPage />} />
            <Route path="/simulation" element={<SimulationPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
