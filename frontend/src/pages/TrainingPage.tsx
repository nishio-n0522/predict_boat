/**
 * 学習実行ページ
 */

import React, { useState, useEffect, useRef } from 'react';
import { Play, Square, AlertCircle, CheckCircle2 } from 'lucide-react';
import type { ModelType, TrainingProgress } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export default function TrainingPage() {
  const [modelType, setModelType] = useState<ModelType>('lightgbm');
  const [datasetPath, setDatasetPath] = useState('data/processed/training_dataset.csv');
  const [parameters, setParameters] = useState({
    lightgbm: { num_boost_round: 1000 },
    transformer: { d_model: 128, nhead: 8, num_layers: 3, batch_size: 32, epochs: 50, lr: 0.001 },
    bayesian: { draws: 2000, tune: 2000, chains: 4 },
  });

  const [isTraining, setIsTraining] = useState(false);
  const [progress, setProgress] = useState<TrainingProgress | null>(null);
  const [taskId, setTaskId] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const startTraining = async () => {
    try {
      setIsTraining(true);
      setProgress(null);

      // タスクIDを生成
      const newTaskId = crypto.randomUUID();
      setTaskId(newTaskId);

      // WebSocket接続
      const wsUrl = API_BASE_URL.replace('http', 'ws') + `/api/train/ws/${newTaskId}`;
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected');
        // 学習パラメータを送信
        ws.send(JSON.stringify({
          model_type: modelType,
          dataset_path: datasetPath,
          parameters: parameters[modelType],
        }));
      };

      ws.onmessage = (event) => {
        const data: TrainingProgress = JSON.parse(event.data);
        setProgress(data);

        if (data.status === 'completed' || data.status === 'failed') {
          setIsTraining(false);
          ws.close();
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setIsTraining(false);
      };

      ws.onclose = () => {
        console.log('WebSocket closed');
        setIsTraining(false);
      };
    } catch (error) {
      console.error('Training error:', error);
      setIsTraining(false);
    }
  };

  const stopTraining = () => {
    if (wsRef.current) {
      wsRef.current.close();
    }
    setIsTraining(false);
  };

  const updateParameter = (key: string, value: any) => {
    setParameters({
      ...parameters,
      [modelType]: {
        ...parameters[modelType],
        [key]: value,
      },
    });
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">モデル学習</h1>

      {/* モデル選択 */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">モデルタイプ</h2>
        <div className="grid grid-cols-3 gap-4">
          {(['lightgbm', 'transformer', 'bayesian'] as ModelType[]).map((type) => (
            <button
              key={type}
              onClick={() => setModelType(type)}
              className={`p-4 rounded-lg border-2 transition-colors ${
                modelType === type
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="font-semibold capitalize">{type}</div>
              <div className="text-sm text-gray-600 mt-1">
                {type === 'lightgbm' && '勾配ブースティング'}
                {type === 'transformer' && '時系列Transformer'}
                {type === 'bayesian' && '階層ベイズ'}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* データセット設定 */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">データセット</h2>
        <div>
          <label className="block text-sm font-medium mb-2">データセットパス</label>
          <input
            type="text"
            value={datasetPath}
            onChange={(e) => setDatasetPath(e.target.value)}
            className="w-full px-3 py-2 border rounded-lg"
            disabled={isTraining}
          />
        </div>
      </div>

      {/* パラメータ設定 */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">パラメータ</h2>

        {modelType === 'lightgbm' && (
          <div>
            <label className="block text-sm font-medium mb-2">Boosting Rounds</label>
            <input
              type="number"
              value={parameters.lightgbm.num_boost_round}
              onChange={(e) => updateParameter('num_boost_round', parseInt(e.target.value))}
              className="w-full px-3 py-2 border rounded-lg"
              disabled={isTraining}
            />
          </div>
        )}

        {modelType === 'transformer' && (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">Epochs</label>
              <input
                type="number"
                value={parameters.transformer.epochs}
                onChange={(e) => updateParameter('epochs', parseInt(e.target.value))}
                className="w-full px-3 py-2 border rounded-lg"
                disabled={isTraining}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Batch Size</label>
              <input
                type="number"
                value={parameters.transformer.batch_size}
                onChange={(e) => updateParameter('batch_size', parseInt(e.target.value))}
                className="w-full px-3 py-2 border rounded-lg"
                disabled={isTraining}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Learning Rate</label>
              <input
                type="number"
                step="0.0001"
                value={parameters.transformer.lr}
                onChange={(e) => updateParameter('lr', parseFloat(e.target.value))}
                className="w-full px-3 py-2 border rounded-lg"
                disabled={isTraining}
              />
            </div>
          </div>
        )}

        {modelType === 'bayesian' && (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">Draws</label>
              <input
                type="number"
                value={parameters.bayesian.draws}
                onChange={(e) => updateParameter('draws', parseInt(e.target.value))}
                className="w-full px-3 py-2 border rounded-lg"
                disabled={isTraining}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Tune</label>
              <input
                type="number"
                value={parameters.bayesian.tune}
                onChange={(e) => updateParameter('tune', parseInt(e.target.value))}
                className="w-full px-3 py-2 border rounded-lg"
                disabled={isTraining}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Chains</label>
              <input
                type="number"
                value={parameters.bayesian.chains}
                onChange={(e) => updateParameter('chains', parseInt(e.target.value))}
                className="w-full px-3 py-2 border rounded-lg"
                disabled={isTraining}
              />
            </div>
          </div>
        )}
      </div>

      {/* 学習実行ボタン */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <button
          onClick={isTraining ? stopTraining : startTraining}
          className={`w-full py-3 px-6 rounded-lg font-semibold flex items-center justify-center gap-2 transition-colors ${
            isTraining
              ? 'bg-red-500 hover:bg-red-600 text-white'
              : 'bg-blue-500 hover:bg-blue-600 text-white'
          }`}
        >
          {isTraining ? (
            <>
              <Square className="w-5 h-5" />
              学習を停止
            </>
          ) : (
            <>
              <Play className="w-5 h-5" />
              学習を開始
            </>
          )}
        </button>
      </div>

      {/* 進捗表示 */}
      {progress && (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center gap-3 mb-4">
            {progress.status === 'completed' && <CheckCircle2 className="w-6 h-6 text-green-500" />}
            {progress.status === 'failed' && <AlertCircle className="w-6 h-6 text-red-500" />}
            {(progress.status === 'starting' || progress.status === 'running') && (
              <div className="w-6 h-6 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
            )}
            <h2 className="text-xl font-semibold">進捗状況</h2>
          </div>

          {/* プログレスバー */}
          <div className="mb-4">
            <div className="flex justify-between text-sm mb-1">
              <span>{progress.current_step || 'Unknown'}</span>
              <span>{Math.round(progress.progress * 100)}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${progress.progress * 100}%` }}
              />
            </div>
          </div>

          <p className="text-gray-700 mb-4">{progress.message}</p>

          {/* メトリクス */}
          {progress.metrics && (
            <div className="bg-gray-50 rounded p-4">
              <h3 className="font-semibold mb-2">メトリクス</h3>
              <div className="grid grid-cols-2 gap-2 text-sm">
                {Object.entries(progress.metrics).map(([key, value]) => (
                  <div key={key}>
                    <span className="text-gray-600">{key}:</span>{' '}
                    <span className="font-mono">{value}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
