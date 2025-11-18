# ボートレース予測AIシステム - 統合ドキュメント

## 目次

1. [プロジェクト概要](#1-プロジェクト概要)
2. [システムアーキテクチャ](#2-システムアーキテクチャ)
3. [機械学習モデル](#3-機械学習モデル)
4. [ウェブアプリケーション](#4-ウェブアプリケーション)
5. [セットアップ](#5-セットアップ)
6. [使用方法](#6-使用方法)
7. [API仕様](#7-api仕様)
8. [ディレクトリ構造](#8-ディレクトリ構造)
9. [開発ガイド](#9-開発ガイド)
10. [トラブルシューティング](#10-トラブルシューティング)

---

## 1. プロジェクト概要

### 1.1 目的

日本のボートレース（競艇）の予測を行うAIシステム。一般戦およびG3戦を対象に、3連単ボックス買いのための3艇を推奨します。

### 1.2 対象レース

- **対象**: 一般戦、G3戦
- **除外**: G2、G1、PSG1、SG

### 1.3 予測目標

6艇のうち、以下を予測：
- 最も舟券内（3着以内）に来ると思われる2艇
- 残り4艇のうち、3艇目の候補
- 推奨3連単ボックス（6組の買い目）

### 1.4 主な機能

1. **3種類の機械学習モデル**
   - LightGBM（勾配ブースティング）
   - Transformer（時系列Transformer + Feature-wise Attention）
   - 階層ベイズモデル（PyMC）

2. **統一インターフェース**
   - すべてのモデルで同じ予測API
   - 一貫した結果フォーマット

3. **ウェブアプリケーション**
   - モデル学習（リアルタイム進捗表示）
   - レース予測（特徴量重要度付き）
   - モデル比較（視覚化）

### 1.5 技術スタック

| カテゴリ | 技術 |
|---------|------|
| **機械学習** | LightGBM, PyTorch, PyMC |
| **バックエンド** | FastAPI, WebSocket, Uvicorn |
| **フロントエンド** | React 18, TypeScript, Vite |
| **スタイリング** | TailwindCSS |
| **可視化** | Recharts, Matplotlib |
| **データベース** | SQLite, SQLAlchemy |
| **その他** | SHAP, Captum, ArviZ |

---

## 2. システムアーキテクチャ

### 2.1 全体構成

```
┌─────────────────────────────────────────────────────────┐
│                    フロントエンド                          │
│              React + TypeScript + Vite                   │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ 学習画面  │  │ 予測画面  │  │ 比較画面  │             │
│  └──────────┘  └──────────┘  └──────────┘             │
└───────────────────┬─────────────────────────────────────┘
                    │ HTTP / WebSocket
┌───────────────────▼─────────────────────────────────────┐
│                   バックエンド API                         │
│                    FastAPI                               │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ 学習API   │  │ 予測API   │  │モデル管理 │             │
│  └──────────┘  └──────────┘  └──────────┘             │
└───────────────────┬─────────────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────────────┐
│                 機械学習モデル層                           │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  │
│  │  LightGBM    │  │ Transformer  │  │ 階層ベイズ    │  │
│  │              │  │              │  │              │  │
│  │ - 訓練       │  │ - 訓練       │  │ - 訓練       │  │
│  │ - 予測       │  │ - 予測       │  │ - 予測       │  │
│  │ - 評価       │  │ - 評価       │  │ - 評価       │  │
│  └──────────────┘  └──────────────┘  └─────────────┘  │
└───────────────────┬─────────────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────────────┐
│                  データ層                                 │
│                                                          │
│  ┌──────────────────┐      ┌──────────────────┐        │
│  │ SQLite DB        │      │ 訓練済みモデル     │        │
│  │ - レース結果      │      │ - .pkl ファイル   │        │
│  │ - 選手データ      │      │ - .pt ファイル    │        │
│  │ - モーターデータ  │      │ - .nc ファイル    │        │
│  └──────────────────┘      └──────────────────┘        │
└─────────────────────────────────────────────────────────┘
```

### 2.2 通信フロー

#### 学習フロー
```
フロントエンド → POST /api/train (タスクID取得)
             → WebSocket /api/train/ws/{task_id} (進捗受信)
             ← 進捗メッセージ（0% → 100%）
             ← 完了通知
```

#### 予測フロー
```
フロントエンド → POST /api/predict (予測リクエスト)
             ← レース予測結果
             → POST /api/predict/feature-importance
             ← 特徴量重要度
```

#### 比較フロー
```
フロントエンド → POST /api/predict/compare (複数モデル指定)
             ← 各モデルの予測結果
             ← 比較メトリクス（一致度、統計）
```

---

## 3. 機械学習モデル

### 3.1 モデル一覧

| モデル | 特徴 | 訓練速度 | 予測速度 | 精度 | 解釈性 | 不確実性 |
|--------|------|----------|----------|------|--------|----------|
| LightGBM | 勾配ブースティング | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ✗ |
| Transformer | Feature-wise Attention | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✗ |
| 階層ベイズ | 部分プーリング | ⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✓ |

### 3.2 LightGBMモデル

#### 概要
勾配ブースティング決定木による二値分類（3着以内 vs 4着以下）。

#### ファイル構成
```
ml_models/
├── train_model.py          # 訓練スクリプト
├── predict.py              # 予測スクリプト
└── evaluate.py             # 評価スクリプト
```

#### 主要クラス
- `BoatRacePredictor`: モデルのラッパー
- `LightGBMRacePredictor`: 予測インターフェース
- `ModelEvaluator`: 評価ロジック

#### 特徴量重要度
- **手法**: Gain-based Importance
- **取得方法**: `model.feature_importance(importance_type='gain')`

#### 訓練コマンド
```bash
python ml_models/train_model.py \
    --dataset data/processed/training_dataset.csv \
    --output models_trained/lightgbm_model.pkl \
    --num-boost-round 1000
```

#### 予測コマンド
```bash
python ml_models/predict.py \
    --model models_trained/lightgbm_model.pkl \
    --date 2023-08-01 \
    --stadium 1 \
    --race 1
```

### 3.3 Transformerモデル

#### 概要
時系列Transformerモデル + Feature-wise Attention Gate。各特徴量に学習可能な重要度を付与。

#### アーキテクチャ
```python
Input (1, 6, n_features)
  ↓
Feature Gating (学習可能な重み)
  ↓
Positional Encoding (艇番情報)
  ↓
Transformer Encoder (Multi-head Self-Attention)
  ↓
Output Projection
  ↓
Sigmoid
  ↓
Output (1, 6) - 各艇の3着以内確率
```

#### ファイル構成
```
ml_models/
├── transformer_model.py           # モデル定義
├── train_transformer.py           # 訓練スクリプト
├── predict_transformer.py         # 予測スクリプト
├── evaluate_transformer.py        # 評価スクリプト
└── feature_importance_analyzer.py # 重要度分析
```

#### 特徴量重要度
- **手法1**: Attention Weights（Feature Gateの重み）
- **手法2**: Integrated Gradients（勾配ベース）
- **手法3**: SHAP Approximation（Shapley値）

#### 訓練コマンド
```bash
python ml_models/train_transformer.py \
    --dataset data/processed/training_dataset.csv \
    --output models_trained/transformer_model.pt \
    --d-model 128 \
    --nhead 8 \
    --num-layers 3 \
    --batch-size 32 \
    --epochs 50 \
    --lr 0.001
```

### 3.4 階層ベイズモデル

#### 概要
PyMCを用いた階層ベイズモデル。選手・モーター・競艇場のランダム効果を階層構造でモデル化。

#### モデル構造
```python
# ハイパープライア（階層の分散）
σ_player ~ HalfCauchy(2)
σ_motor ~ HalfCauchy(2)
σ_stadium ~ HalfCauchy(1)

# ランダム効果
θ_player ~ Normal(0, σ_player)  # 選手効果
θ_motor ~ Normal(0, σ_motor)    # モーター効果
θ_stadium ~ Normal(0, σ_stadium) # 競艇場効果

# 固定効果
β ~ Normal(0, 1)  # 特徴量係数
α ~ Normal(0, 5)  # 切片

# 線形予測子
η = α + θ_player[i] + θ_motor[j] + θ_stadium[k] + X·β

# 観測モデル
p = sigmoid(η)
y ~ Bernoulli(p)
```

#### ファイル構成
```
ml_models/
├── hierarchical_bayesian_model.py  # モデル定義
├── train_bayesian.py               # 訓練スクリプト
├── predict_bayesian.py             # 予測スクリプト
└── evaluate_bayesian.py            # 評価スクリプト
```

#### 特徴
1. **部分プーリング**: データ量の異なる選手を公平に扱う
2. **不確実性定量化**: 予測に標準偏差と95%信頼区間を付与
3. **階層構造**: 個体差を自動学習
4. **収束診断**: R-hat統計量で品質確認

#### 訓練コマンド
```bash
python ml_models/train_bayesian.py \
    --dataset data/processed/training_dataset.csv \
    --output models_trained/bayesian_model.pkl \
    --draws 2000 \
    --tune 2000 \
    --chains 4
```

#### 予測出力例
```
1号艇: 0.456 ± 0.032 (95% CI: [0.393, 0.518])
2号艇: 0.234 ± 0.028 (95% CI: [0.179, 0.289])
3号艇: 0.189 ± 0.025 (95% CI: [0.140, 0.238])
```

### 3.5 統一インターフェース

すべてのモデルは`RacePredictionResult`を返却し、以下のメソッドを提供：

```python
# 共通インターフェース
result = predictor.predict_race(race_date, stadium_id, race_index)

# 利用可能なメソッド
result.get_top2_boats()           # 上位2艇
result.get_third_candidate()      # 3番手候補
result.get_recommended_boats()    # 推奨3艇
result.print_summary()            # 結果サマリー表示
```

### 3.6 特徴量一覧

各モデルで使用する特徴量（約20-25個）：

**選手関連**
- 全国勝率、全国2連対率、全国3連対率
- 当地勝率、当地2連対率、当地3連対率
- 平均スタートタイミング
- 過去N日の勝率、2連対率、3連対率

**モーター・ボート関連**
- モーター2連対率、3連対率
- ボート番号

**レース条件**
- 競艇場ID
- レース番号
- 天候、風速、波高
- 気温、水温

**過去実績**
- 過去同条件での成績
- 最近の調子

---

## 4. ウェブアプリケーション

### 4.1 バックエンド (FastAPI)

#### 4.1.1 API構成

**学習API** (`/api/train`)
```python
POST /api/train
  → 学習タスクを作成し、タスクIDを返却

WebSocket /api/train/ws/{task_id}
  → リアルタイムで学習進捗を送信
  → 進捗: {status, progress, message, current_step, metrics}

DELETE /api/train/{task_id}
  → 学習をキャンセル
```

**推論API** (`/api/predict`)
```python
POST /api/predict
  → 単一モデルでレース予測
  → 入力: {model_path, model_type, race_date, stadium_id, race_index}
  → 出力: RacePrediction

POST /api/predict/compare
  → 複数モデルで予測を比較
  → 入力: {model_paths: {name: path}, race_date, stadium_id, race_index}
  → 出力: {predictions, comparison}

POST /api/predict/feature-importance
  → 特徴量重要度を取得
  → 入力: {model_path, model_type, top_n}
  → 出力: {model_type, method, features[]}
```

**モデル管理API** (`/api/models`)
```python
GET /api/models
  → 訓練済みモデル一覧

GET /api/models/{model_name}
  → モデル詳細情報

DELETE /api/models/{model_name}
  → モデルを削除
```

#### 4.1.2 サービス層

**TrainingService** (`backend/services/training_service.py`)
- `train_lightgbm()`: LightGBM学習
- `train_transformer()`: Transformer学習
- `train_bayesian()`: 階層ベイズ学習
- 各メソッドは`AsyncIterator[TrainingProgress]`を返却

**PredictionService** (`backend/services/prediction_service.py`)
- `predict_race()`: 単一モデル予測
- `predict_multi_models()`: 複数モデル比較
- `get_feature_importance()`: 特徴量重要度取得

#### 4.1.3 スキーマ (Pydantic)

```python
# 学習リクエスト
class TrainingRequest(BaseModel):
    model_type: Literal["lightgbm", "transformer", "bayesian"]
    dataset_path: str
    parameters: Dict[str, Any]

# 学習進捗
class TrainingProgress(BaseModel):
    status: Literal["starting", "running", "completed", "failed"]
    progress: float  # 0.0 ~ 1.0
    message: str
    current_step: Optional[str]
    metrics: Optional[Dict[str, float]]

# 予測リクエスト
class PredictionRequest(BaseModel):
    model_path: str
    model_type: str
    race_date: date
    stadium_id: int
    race_index: Optional[int]

# レース予測結果
class RacePrediction(BaseModel):
    race_date: date
    stadium_id: int
    race_index: int
    boats: List[BoatPrediction]
    recommended_boats: List[int]
    expected_hit_rate: float
    has_uncertainty: bool
```

### 4.2 フロントエンド (React + TypeScript)

#### 4.2.1 ページ構成

**1. ホームページ** (`App.tsx`)
- 3つの機能へのナビゲーション
- プロジェクト概要表示

**2. 学習実行ページ** (`TrainingPage.tsx`)

機能:
- モデルタイプ選択（LightGBM / Transformer / 階層ベイズ）
- データセットパス指定
- パラメータ調整UI
- WebSocketによるリアルタイム進捗表示
- プログレスバー、現在のステップ表示
- 完了時のメトリクス表示

主要コンポーネント:
```tsx
- モデル選択タブ
- データセット入力フォーム
- パラメータ調整フォーム（モデルごとに動的）
- 進捗表示エリア
  - ステータスアイコン
  - プログレスバー
  - メッセージ
  - メトリクステーブル
```

**3. 推論実行ページ** (`PredictionPage.tsx`)

機能:
- モデル選択ドロップダウン
- レース情報入力（日付、競艇場ID、レース番号）
- 各艇の3着以内確率表示（プログレスバー）
- 推奨3艇の強調表示
- 特徴量重要度の棒グラフ（Recharts）

主要コンポーネント:
```tsx
- 設定パネル（左側）
  - モデル選択
  - レース情報入力
  - 予測実行ボタン
- 結果表示パネル（右側）
  - レース情報サマリー
  - 各艇の確率バー
  - 推奨艇ボックス
  - 特徴量重要度チャート
```

**4. モデル比較ページ** (`ComparisonPage.tsx`)

機能:
- 複数モデル選択（チェックボックス）
- レーダーチャートで確率比較
- 推奨艇の比較テーブル
- モデル間一致度の表示
- 各艇の統計（平均、標準偏差、範囲）

主要コンポーネント:
```tsx
- モデル選択パネル（左側）
  - チェックボックスリスト
  - レース情報入力
  - 比較実行ボタン
- 比較結果パネル（右側）
  - レーダーチャート（Recharts）
  - 推奨艇比較テーブル
  - 一致度マトリクス
  - 各艇の統計カード
```

#### 4.2.2 状態管理

各ページで`useState`を使用した状態管理:

```tsx
// 学習ページ
const [modelType, setModelType] = useState<ModelType>('lightgbm');
const [parameters, setParameters] = useState({...});
const [isTraining, setIsTraining] = useState(false);
const [progress, setProgress] = useState<TrainingProgress | null>(null);

// 予測ページ
const [selectedModel, setSelectedModel] = useState<ModelInfo | null>(null);
const [prediction, setPrediction] = useState<RacePrediction | null>(null);
const [featureImportance, setFeatureImportance] = useState<...>(null);

// 比較ページ
const [selectedModels, setSelectedModels] = useState<Record<string, string>>({});
const [comparison, setComparison] = useState<any>(null);
```

#### 4.2.3 API通信

**APIサービス** (`services/api.ts`)
```typescript
// モデル管理
modelsApi.list()
modelsApi.get(modelName)
modelsApi.delete(modelName)

// 予測
predictionApi.predict(request)
predictionApi.compare(request)
predictionApi.getFeatureImportance(modelPath, modelType, topN)
```

**WebSocket通信** (学習進捗)
```typescript
const ws = new WebSocket(wsUrl);
ws.onopen = () => ws.send(JSON.stringify(config));
ws.onmessage = (event) => {
  const progress = JSON.parse(event.data);
  setProgress(progress);
};
```

#### 4.2.4 スタイリング

TailwindCSSを使用したユーティリティファーストスタイリング:

```tsx
// カードレイアウト
className="bg-white rounded-lg shadow p-6 mb-6"

// ボタン
className="bg-blue-500 hover:bg-blue-600 text-white py-3 px-6 rounded-lg"

// プログレスバー
className="w-full bg-gray-200 rounded-full h-2"
className="bg-blue-500 h-2 rounded-full transition-all"

// グリッドレイアウト
className="grid grid-cols-1 lg:grid-cols-3 gap-6"
```

---

## 5. セットアップ

### 5.1 前提条件

- Python 3.9以上
- Node.js 18以上
- npm または yarn
- Git LFS（データベースファイル用）

### 5.2 リポジトリのクローン

```bash
git clone <repository-url>
cd predict_boat

# Git LFSでデータベースを取得
git lfs pull
```

### 5.3 バックエンドのセットアップ

```bash
# 仮想環境の作成（推奨）
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係のインストール
pip install -r requirements.txt
```

### 5.4 フロントエンドのセットアップ

```bash
cd frontend

# 依存関係のインストール
npm install

# 環境変数の設定
cp .env.example .env
```

`.env`ファイルを編集:
```env
VITE_API_BASE_URL=http://localhost:8000
```

### 5.5 データベースの確認

```bash
# データベースファイルの確認
file data/sqlite.sqlite3

# SQLiteデータベースとして認識されることを確認
```

---

## 6. 使用方法

### 6.1 サーバーの起動

#### ターミナル1: バックエンド
```bash
# プロジェクトルートで実行
python backend/main.py
```

起動確認:
- サーバー: http://localhost:8000
- APIドキュメント: http://localhost:8000/docs
- ヘルスチェック: http://localhost:8000/health

#### ターミナル2: フロントエンド
```bash
cd frontend
npm run dev
```

起動確認:
- アプリケーション: http://localhost:5173

### 6.2 ウェブアプリの使用

#### 6.2.1 モデルの学習

1. http://localhost:5173 にアクセス
2. 「モデル学習」をクリック
3. モデルタイプを選択:
   - **LightGBM**: 高速・高精度
   - **Transformer**: 解釈性重視
   - **階層ベイズ**: 不確実性定量化
4. パラメータを調整:
   - LightGBM: Boosting Rounds（デフォルト: 1000）
   - Transformer: Epochs, Batch Size, Learning Rate
   - Bayesian: Draws, Tune, Chains
5. 「学習を開始」ボタンをクリック
6. リアルタイムで進捗を確認
7. 完了後、メトリクスを確認

#### 6.2.2 レースの予測

1. 「レース予測」ページに移動
2. 学習済みモデルを選択
3. レース情報を入力:
   - レース日（例: 2023-08-01）
   - 競艇場ID（1-24）
   - レース番号（1-12）
4. 「予測を実行」ボタンをクリック
5. 結果を確認:
   - 各艇の3着以内確率
   - 推奨3連単ボックス
   - 期待的中率
   - 特徴量重要度（棒グラフ）

#### 6.2.3 モデルの比較

1. 「モデル比較」ページに移動
2. 比較したいモデルを選択（チェックボックス）
3. レース情報を入力
4. 「比較を実行」ボタンをクリック
5. 結果を確認:
   - レーダーチャート（各艇の確率）
   - 推奨艇の比較テーブル
   - モデル間一致度
   - 各艇の統計（平均、標準偏差、範囲）

### 6.3 コマンドラインでの使用

#### データセット作成
```bash
python ml_models/build_dataset.py \
    --start-date 2020-04-01 \
    --end-date 2023-09-06 \
    --output data/processed/training_dataset.csv
```

#### LightGBM学習
```bash
python ml_models/train_model.py \
    --dataset data/processed/training_dataset.csv \
    --output models_trained/lightgbm_model.pkl \
    --num-boost-round 1000
```

#### Transformer学習
```bash
python ml_models/train_transformer.py \
    --dataset data/processed/training_dataset.csv \
    --output models_trained/transformer_model.pt \
    --epochs 50
```

#### 予測実行
```bash
python ml_models/predict.py \
    --model models_trained/lightgbm_model.pkl \
    --date 2023-08-01 \
    --stadium 1 \
    --race 1
```

#### モデル評価
```bash
python ml_models/evaluate.py \
    --model models_trained/lightgbm_model.pkl \
    --start-date 2023-07-01 \
    --end-date 2023-09-06
```

---

## 7. API仕様

### 7.1 学習API

#### POST /api/train
学習タスクを作成

**リクエスト:**
```json
{
  "model_type": "lightgbm",
  "dataset_path": "data/processed/training_dataset.csv",
  "parameters": {
    "num_boost_round": 1000
  }
}
```

**レスポンス:**
```json
{
  "task_id": "uuid-string",
  "model_type": "lightgbm",
  "status": "queued",
  "message": "学習タスクが開始されました"
}
```

#### WebSocket /api/train/ws/{task_id}
学習進捗をストリーミング

**送信メッセージ:**
```json
{
  "model_type": "lightgbm",
  "dataset_path": "data/processed/training_dataset.csv",
  "parameters": {...}
}
```

**受信メッセージ:**
```json
{
  "status": "running",
  "progress": 0.5,
  "message": "訓練中...",
  "current_step": "訓練中",
  "metrics": {
    "train_size": 10000,
    "val_size": 2000
  }
}
```

### 7.2 推論API

#### POST /api/predict
レース予測

**リクエスト:**
```json
{
  "model_path": "models_trained/lightgbm_model.pkl",
  "model_type": "lightgbm",
  "race_date": "2023-08-01",
  "stadium_id": 1,
  "race_index": 1
}
```

**レスポンス:**
```json
{
  "race_date": "2023-08-01",
  "stadium_id": 1,
  "race_index": 1,
  "boats": [
    {
      "boat_number": 1,
      "probability": 0.456,
      "std": null,
      "ci_lower": null,
      "ci_upper": null
    },
    ...
  ],
  "recommended_boats": [1, 2, 3],
  "expected_hit_rate": 0.293,
  "has_uncertainty": false
}
```

#### POST /api/predict/compare
複数モデル比較

**リクエスト:**
```json
{
  "model_paths": {
    "LightGBM": "models_trained/lightgbm_model.pkl",
    "Transformer": "models_trained/transformer_model.pt"
  },
  "race_date": "2023-08-01",
  "stadium_id": 1,
  "race_index": 1
}
```

**レスポンス:**
```json
{
  "race_info": {...},
  "predictions": {
    "LightGBM": {...},
    "Transformer": {...}
  },
  "comparison": {
    "recommended_comparison": {...},
    "agreement_matrix": {
      "LightGBM_vs_Transformer": 0.67
    },
    "boat_avg_probabilities": {...}
  }
}
```

#### POST /api/predict/feature-importance
特徴量重要度

**リクエスト:**
```json
{
  "model_path": "models_trained/lightgbm_model.pkl",
  "model_type": "lightgbm",
  "top_n": 20
}
```

**レスポンス:**
```json
{
  "model_type": "lightgbm",
  "method": "Gain-based Importance",
  "features": [
    {
      "feature_name": "player_national_win_rate",
      "importance": 1250.5,
      "rank": 1
    },
    ...
  ]
}
```

### 7.3 モデル管理API

#### GET /api/models
モデル一覧

**レスポンス:**
```json
{
  "models": [
    {
      "name": "lightgbm_model",
      "model_type": "lightgbm",
      "path": "models_trained/lightgbm_model.pkl",
      "created_at": "2024-01-01T12:00:00",
      "file_size": 1024000,
      "metadata": {}
    },
    ...
  ],
  "total": 3
}
```

#### GET /api/models/{model_name}
モデル詳細

#### DELETE /api/models/{model_name}
モデル削除

---

## 8. ディレクトリ構造

```
predict_boat/
├── README.md                       # プロジェクト概要
├── WEBAPP_README.md                # ウェブアプリ説明
├── DOCUMENTATION.md                # 本ドキュメント
├── requirements.txt                # Python依存関係
├── .gitignore
│
├── db/                             # データベース定義
│   ├── db_setting.py              # SQLAlchemy設定
│   └── *.py                       # テーブル定義
│
├── data/                           # データ
│   ├── sqlite.sqlite3             # SQLiteデータベース (Git LFS)
│   └── processed/                 # 処理済みデータ
│       └── training_dataset.csv
│
├── ml_models/                      # 機械学習モデル
│   ├── README.md                  # モデル説明
│   │
│   ├── race_grade_classifier.py   # レース分類
│   ├── feature_engineering.py     # 特徴量抽出
│   ├── build_dataset.py           # データセット構築
│   │
│   ├── predict.py                 # 予測共通クラス (RacePredictionResult)
│   │
│   ├── train_model.py             # LightGBM訓練
│   ├── predict.py                 # LightGBM予測 (LightGBMRacePredictor)
│   ├── evaluate.py                # LightGBM評価
│   │
│   ├── transformer_model.py       # Transformer定義
│   ├── train_transformer.py       # Transformer訓練
│   ├── predict_transformer.py     # Transformer予測 (TransformerRacePredictor)
│   ├── evaluate_transformer.py    # Transformer評価
│   ├── feature_importance_analyzer.py  # 重要度分析
│   │
│   ├── hierarchical_bayesian_model.py  # ベイズモデル定義
│   ├── train_bayesian.py          # ベイズ訓練
│   ├── predict_bayesian.py        # ベイズ予測 (BayesianRacePredictor)
│   └── evaluate_bayesian.py       # ベイズ評価
│
├── models_trained/                 # 訓練済みモデル保存先
│   ├── *.pkl                      # LightGBM, Bayesianモデル
│   ├── *.pt                       # Transformerモデル
│   ├── *.nc                       # Bayesian MCMCトレース
│   └── *.png                      # 可視化結果
│
├── backend/                        # バックエンドAPI
│   ├── __init__.py
│   ├── main.py                    # FastAPIアプリ
│   │
│   ├── routers/                   # APIルーター
│   │   ├── __init__.py
│   │   ├── train.py              # 学習API
│   │   ├── predict.py            # 推論API
│   │   └── models.py             # モデル管理API
│   │
│   ├── services/                  # ビジネスロジック
│   │   ├── __init__.py
│   │   ├── training_service.py   # 学習サービス
│   │   └── prediction_service.py # 推論サービス
│   │
│   └── schemas/                   # Pydanticスキーマ
│       ├── __init__.py
│       ├── train.py              # 学習スキーマ
│       ├── predict.py            # 推論スキーマ
│       └── models.py             # モデルスキーマ
│
└── frontend/                       # フロントエンド
    ├── package.json
    ├── tsconfig.json
    ├── vite.config.ts
    ├── tailwind.config.js
    ├── postcss.config.js
    ├── index.html
    ├── .env.example
    │
    └── src/
        ├── main.tsx              # エントリーポイント
        ├── App.tsx               # メインアプリ
        ├── index.css             # グローバルCSS
        │
        ├── pages/                # ページコンポーネント
        │   ├── TrainingPage.tsx       # 学習ページ
        │   ├── PredictionPage.tsx     # 予測ページ
        │   └── ComparisonPage.tsx     # 比較ページ
        │
        ├── services/             # APIサービス
        │   └── api.ts
        │
        └── types/                # 型定義
            └── index.ts
```

---

## 9. 開発ガイド

### 9.1 新しいモデルの追加

#### ステップ1: モデルクラスの実装
```python
# ml_models/my_new_model.py
class MyNewModelPredictor:
    def __init__(self, model_path: str):
        # モデル読み込み
        pass

    def predict_race(
        self,
        race_date: dt.date,
        stadium_id: int,
        race_index: int
    ) -> RacePredictionResult:
        # 予測実行
        # ...
        return RacePredictionResult(
            race_date=race_date,
            stadium_id=stadium_id,
            race_index=race_index,
            predictions=result_df
        )

    def close(self):
        # リソース解放
        pass
```

#### ステップ2: バックエンドサービスに追加
```python
# backend/services/training_service.py
async def train_my_new_model(
    self,
    task_id: str,
    dataset_path: str,
    output_path: str,
    parameters: Dict[str, Any]
) -> AsyncIterator[TrainingProgress]:
    # 学習ロジック
    yield TrainingProgress(...)
```

```python
# backend/services/prediction_service.py
def predict_race(self, model_path, model_type, ...):
    if model_type == "my_new_model":
        predictor = MyNewModelPredictor(model_path)
    # ...
```

#### ステップ3: フロントエンドに追加
```typescript
// frontend/src/types/index.ts
export type ModelType = 'lightgbm' | 'transformer' | 'bayesian' | 'my_new_model';

// frontend/src/pages/TrainingPage.tsx
const [parameters, setParameters] = useState({
  // ...
  my_new_model: { param1: value1, param2: value2 },
});
```

### 9.2 新しいAPIエンドポイントの追加

#### ステップ1: スキーマ定義
```python
# backend/schemas/my_schema.py
from pydantic import BaseModel

class MyRequest(BaseModel):
    field1: str
    field2: int

class MyResponse(BaseModel):
    result: str
```

#### ステップ2: ルーター作成
```python
# backend/routers/my_router.py
from fastapi import APIRouter
from backend.schemas.my_schema import MyRequest, MyResponse

router = APIRouter(prefix="/api/my", tags=["my"])

@router.post("", response_model=MyResponse)
async def my_endpoint(request: MyRequest):
    # 処理
    return MyResponse(result="...")
```

#### ステップ3: メインアプリに登録
```python
# backend/main.py
from backend.routers import my_router

app.include_router(my_router.router)
```

### 9.3 新しいページの追加

#### ステップ1: ページコンポーネント作成
```tsx
// frontend/src/pages/MyPage.tsx
import React from 'react';

export default function MyPage() {
  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">My Page</h1>
      {/* コンテンツ */}
    </div>
  );
}
```

#### ステップ2: ルート追加
```tsx
// frontend/src/App.tsx
import MyPage from './pages/MyPage';

<Routes>
  {/* 既存ルート */}
  <Route path="/my-page" element={<MyPage />} />
</Routes>
```

#### ステップ3: ナビゲーション追加
```tsx
// frontend/src/App.tsx (ナビゲーションバー)
<Link to="/my-page" className="px-4 py-2 rounded hover:bg-gray-100">
  My Page
</Link>
```

### 9.4 コーディング規約

#### Python
- PEP 8に従う
- 型ヒントを使用
- Docstringを記述（Google Style）
- 関数は単一責任の原則に従う

```python
def calculate_win_rate(
    wins: int,
    total_races: int
) -> float:
    """
    勝率を計算

    Args:
        wins: 勝利数
        total_races: 総レース数

    Returns:
        勝率（0.0〜1.0）

    Raises:
        ValueError: total_racesが0の場合
    """
    if total_races == 0:
        raise ValueError("total_races must be greater than 0")
    return wins / total_races
```

#### TypeScript
- ESLint推奨設定に従う
- 型を明示的に定義
- コンポーネントは関数コンポーネント
- propsに型を定義

```typescript
interface MyComponentProps {
  title: string;
  count: number;
  onUpdate: (value: number) => void;
}

export default function MyComponent({ title, count, onUpdate }: MyComponentProps) {
  // ...
}
```

### 9.5 テスト

#### バックエンドテスト（例）
```python
# tests/test_prediction_service.py
import pytest
from backend.services.prediction_service import PredictionService

def test_predict_race():
    service = PredictionService()
    result = service.predict_race(
        model_path="models_trained/lightgbm_model.pkl",
        model_type="lightgbm",
        race_date=date(2023, 8, 1),
        stadium_id=1,
        race_index=1
    )
    assert result.race_date == date(2023, 8, 1)
    assert len(result.boats) == 6
```

#### フロントエンドテスト（例）
```typescript
// tests/PredictionPage.test.tsx
import { render, screen } from '@testing-library/react';
import PredictionPage from '../src/pages/PredictionPage';

test('renders prediction page', () => {
  render(<PredictionPage />);
  expect(screen.getByText('レース予測')).toBeInTheDocument();
});
```

---

## 10. トラブルシューティング

### 10.1 バックエンド関連

#### エラー: ModuleNotFoundError
```
ModuleNotFoundError: No module named 'fastapi'
```

**解決方法:**
```bash
pip install -r requirements.txt
```

#### エラー: Address already in use
```
ERROR: [Errno 48] Address already in use
```

**解決方法:**
```bash
# ポート8000を使用しているプロセスを確認
lsof -i :8000

# プロセスを停止
kill -9 <PID>

# または別のポートを使用
uvicorn backend.main:app --port 8001
```

#### エラー: Database file not found
```
FileNotFoundError: data/sqlite.sqlite3
```

**解決方法:**
```bash
# Git LFSでデータベースを取得
git lfs pull

# ファイル確認
file data/sqlite.sqlite3
# 出力: data/sqlite.sqlite3: SQLite 3.x database
```

### 10.2 フロントエンド関連

#### エラー: npm install失敗
```
npm ERR! code ERESOLVE
```

**解決方法:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps
```

#### エラー: CORS policy
```
Access to XMLHttpRequest blocked by CORS policy
```

**解決方法:**
`backend/main.py`のCORS設定を確認:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # フロントエンドのURL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### エラー: WebSocket connection failed
```
WebSocket connection to 'ws://localhost:8000/api/train/ws/...' failed
```

**解決方法:**
1. バックエンドが起動しているか確認
2. ブラウザのコンソールでエラー詳細を確認
3. ファイアウォール設定を確認

### 10.3 モデル関連

#### エラー: モデル読み込み失敗
```
FileNotFoundError: models_trained/lightgbm_model.pkl
```

**解決方法:**
```bash
# モデルが存在するか確認
ls -la models_trained/

# 存在しない場合は学習を実行
python ml_models/train_model.py \
    --dataset data/processed/training_dataset.csv \
    --output models_trained/lightgbm_model.pkl
```

#### エラー: CUDA out of memory (Transformer)
```
RuntimeError: CUDA out of memory
```

**解決方法:**
```bash
# CPUで実行
# または
# バッチサイズを削減
python ml_models/train_transformer.py \
    --batch-size 16  # デフォルト32から削減
```

#### エラー: PyMC sampling failed (Bayesian)
```
SamplingError: Chain did not converge
```

**解決方法:**
```bash
# チューニング数を増やす
python ml_models/train_bayesian.py \
    --tune 5000 \  # デフォルト2000から増加
    --draws 5000

# またはサンプルサイズを削減
python ml_models/train_bayesian.py \
    --sample-size 5000  # データサブセット
```

### 10.4 パフォーマンス最適化

#### 学習が遅い
- **LightGBM**: `num_boost_round`を削減
- **Transformer**: `batch_size`を増加、`epochs`を削減
- **Bayesian**: `sample_size`でデータをサブサンプリング

#### 予測が遅い
- モデルをメモリにキャッシュ
- バッチ予測を使用
- LightGBMを優先使用（最速）

#### メモリ不足
```bash
# データセットをサンプリング
python ml_models/build_dataset.py \
    --start-date 2023-01-01 \  # 期間を短縮
    --end-date 2023-03-31
```

---

## 11. 今後の拡張案

### 11.1 機能拡張

- [ ] オッズ情報の統合
- [ ] コース別成績の追加特徴量
- [ ] アンサンブルモデル（3モデルの組み合わせ）
- [ ] リアルタイム予測API
- [ ] モバイル対応UI
- [ ] ユーザー認証・権限管理
- [ ] 予測履歴の保存・管理
- [ ] バックテスト機能

### 11.2 モデル改善

- [ ] XGBoost、CatBoostの追加
- [ ] LSTMモデルの実装
- [ ] Ensembleモデル
- [ ] AutoML統合
- [ ] ハイパーパラメータ自動最適化
- [ ] オンライン学習

### 11.3 インフラ

- [ ] Docker化
- [ ] Kubernetes対応
- [ ] CI/CDパイプライン
- [ ] モニタリング（Prometheus, Grafana）
- [ ] ロギング（ELK Stack）
- [ ] 本番環境デプロイ手順

---

## 12. ライセンス

MIT License

---

## 13. 貢献

プルリクエストを歓迎します！

貢献手順:
1. このリポジトリをフォーク
2. 新しいブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

---

## 14. サポート・お問い合わせ

問題が発生した場合:
1. このドキュメントのトラブルシューティングセクションを確認
2. GitHubのIssuesで既存の問題を検索
3. 新しいIssueを作成（再現手順を含める）

---

## 15. 変更履歴

### v1.0.0 (2024-01-XX)
- 初回リリース
- LightGBM、Transformer、階層ベイズモデルの実装
- 統一インターフェース
- FastAPI + Reactウェブアプリケーション

---

**最終更新日**: 2024年1月

**作成者**: Claude Code

**バージョン**: 1.0.0
