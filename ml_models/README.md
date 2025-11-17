# ボートレース予測AI - 使い方ガイド

## 概要

ボートレース予測AI。一般戦およびG3戦を対象に、3連単ボックス買いのための3艇を推奨します。

### 利用可能なモデル

1. **LightGBM** - 勾配ブースティング（高速・高精度）
2. **Transformer** - 時系列Transformerモデル（Feature-wise Attention搭載）
3. **Hierarchical Bayesian** - 階層ベイズモデル（不確実性定量化・部分プーリング）

## 予測方針

- **6艇のうち最も舟券内（3着以内）にくると思われる2艇を予測**
- **残り4艇のうち、3着以内になる確率の高い艇を予測**
- **3連単ボックス買い（6点）を想定**

## セットアップ

### 1. 必要なライブラリのインストール

```bash
pip install -r requirements.txt
```

### 2. データベースの準備

データベース（sqlite.sqlite3）がGit LFSで管理されている場合は、以下のコマンドでダウンロードします:

```bash
git lfs pull
```

## 使い方

### ステップ1: 訓練データセットの構築

データベースから特徴量を抽出し、訓練用データセットを作成します。

```bash
python ml_models/build_dataset.py \
    --start-date 2020-04-01 \
    --end-date 2023-09-06 \
    --output data/processed/training_dataset.csv
```

**オプション:**
- `--start-date`: 開始日（デフォルト: 2020-04-01）
- `--end-date`: 終了日（デフォルト: 2023-09-06）
- `--output`: 出力先パス
- `--all-grades`: 全グレードを対象（デフォルトは一般戦・G3のみ）

**処理時間:** データ量によって数十分〜数時間かかる場合があります。

### ステップ2: モデルの訓練

#### 2-A: LightGBMモデル

```bash
python ml_models/train_model.py \
    --dataset data/processed/training_dataset.csv \
    --output models_trained/lightgbm_model.pkl \
    --num-boost-round 1000
```

**オプション:**
- `--dataset`: 訓練データセットのパス
- `--output`: モデル保存先パス
- `--num-boost-round`: ブースティングラウンド数（デフォルト: 1000）

**出力:**
- `models_trained/lightgbm_model.pkl`: 訓練済みモデル
- `models_trained/feature_importance.png`: 特徴量重要度のグラフ

#### 2-B: Transformerモデル

```bash
python ml_models/train_transformer.py \
    --dataset data/processed/training_dataset.csv \
    --output models_trained/transformer_model.pt \
    --d-model 128 \
    --nhead 8 \
    --num-layers 3 \
    --batch-size 32 \
    --epochs 50 \
    --lr 0.001 \
    --use-feature-gating
```

**オプション:**
- `--dataset`: 訓練データセットのパス
- `--output`: モデル保存先パス
- `--d-model`: モデルの次元数（デフォルト: 128）
- `--nhead`: Attentionヘッド数（デフォルト: 8）
- `--num-layers`: Transformerレイヤー数（デフォルト: 3）
- `--batch-size`: バッチサイズ（デフォルト: 32）
- `--epochs`: エポック数（デフォルト: 50）
- `--lr`: 学習率（デフォルト: 0.001）
- `--use-feature-gating`: Feature-wise Attention を使用

**出力:**
- `models_trained/transformer_model.pt`: 訓練済みモデル
- `models_trained/learning_curve.png`: 学習曲線

**特徴:**
- **Feature-wise Attention**: 各特徴量に学習可能な重要度を付与
- **Attention Weights**: どの特徴が重要かを可視化可能
- **事前重要度の組み込み**: ドメイン知識を初期値として利用可能

#### 2-C: 階層ベイズモデル

```bash
python ml_models/train_bayesian.py \
    --dataset data/processed/training_dataset.csv \
    --output models_trained/bayesian_model.pkl \
    --draws 2000 \
    --tune 2000 \
    --chains 4
```

**オプション:**
- `--dataset`: 訓練データセットのパス
- `--output`: モデル保存先パス
- `--draws`: MCMCサンプリング数（デフォルト: 2000）
- `--tune`: チューニング数（デフォルト: 2000）
- `--chains`: MCMCチェーン数（デフォルト: 4）
- `--cores`: 並列コア数（デフォルト: 4）

**出力:**
- `models_trained/bayesian_model.pkl`: 訓練済みモデル（メタデータ）
- `models_trained/bayesian_model_trace.nc`: MCMCトレース（事後分布）

**特徴:**
- **階層構造**: 選手・モーター・競艇場のランダム効果を自動学習
- **部分プーリング**: データ量の異なる選手を公平に扱う
- **不確実性定量化**: 予測に信頼区間を付与
- **収束診断**: R-hat統計量で自動診断

**注意:**
- 計算時間が長い（数時間〜数十時間）
- 大規模データの場合はサブセットでの訓練を推奨

### ステップ3: レースの予測

訓練済みモデルを使用してレースを予測します。

#### 単一レースの予測

**LightGBM:**
```bash
python ml_models/predict.py \
    --model models_trained/lightgbm_model.pkl \
    --date 2023-08-01 \
    --stadium 1 \
    --race 1
```

**Transformer:**
```bash
python ml_models/predict_transformer.py \
    --model models_trained/transformer_model.pt \
    --date 2023-08-01 \
    --stadium 1 \
    --race 1
```

**階層ベイズ:**
```bash
python ml_models/predict_bayesian.py \
    --model models_trained/bayesian_model.pkl \
    --date 2023-08-01 \
    --stadium 1 \
    --race 1
```

**出力例:**
```
================================================================================
レース: 2023-08-01 場ID:1 R1
================================================================================

【全艇の予測確率】
--------------------------------------------------------------------------------
  1号艇: 0.456 (45.6%)
  2号艇: 0.234 (23.4%)
  3号艇: 0.189 (18.9%)
  4号艇: 0.067 (6.7%)
  5号艇: 0.034 (3.4%)
  6号艇: 0.020 (2.0%)

【推奨購入】
--------------------------------------------------------------------------------
確実に買う2艇:
  1番手: 1号艇 (確率: 0.456)
  2番手: 2号艇 (確率: 0.234)

3艇目の候補:
  3番手: 3号艇 (確率: 0.189)

3連単ボックス買い推奨:
  1-2-3 (6点)
  期待的中率: 0.293
================================================================================
```

**階層ベイズモデルの出力例（不確実性付き）:**
```
================================================================================
レース: 2023-08-01 場ID:1 R1
================================================================================

【全艇の予測確率（不確実性付き）】
--------------------------------------------------------------------------------
  1号艇: 0.456 ± 0.032 (95% CI: [0.393, 0.518])
  2号艇: 0.234 ± 0.028 (95% CI: [0.179, 0.289])
  3号艇: 0.189 ± 0.025 (95% CI: [0.140, 0.238])
  4号艇: 0.067 ± 0.015 (95% CI: [0.038, 0.096])
  5号艇: 0.034 ± 0.012 (95% CI: [0.011, 0.057])
  6号艇: 0.020 ± 0.009 (95% CI: [0.003, 0.037])

【推奨購入】
--------------------------------------------------------------------------------
確実に買う2艇:
  1番手: 1号艇 (確率: 0.456, 不確実性: 0.032)
  2番手: 2号艇 (確率: 0.234, 不確実性: 0.028)

3艇目の候補:
  3番手: 3号艇 (確率: 0.189, 不確実性: 0.025)

3連単ボックス買い推奨:
  1-2-3 (6点)
  期待的中率: 0.293
  予測信頼度: 高（不確実性が低い）
================================================================================
```

#### 全レースの予測

競艇場の全レース（1R〜12R）を一度に予測する場合:

**LightGBM:**
```bash
python ml_models/predict.py \
    --model models_trained/lightgbm_model.pkl \
    --date 2023-08-01 \
    --stadium 1
```

**Transformer:**
```bash
python ml_models/predict_transformer.py \
    --model models_trained/transformer_model.pt \
    --date 2023-08-01 \
    --stadium 1
```

**階層ベイズ:**
```bash
python ml_models/predict_bayesian.py \
    --model models_trained/bayesian_model.pkl \
    --date 2023-08-01 \
    --stadium 1
```

### ステップ4: モデルの評価

モデルの性能を評価し、的中率や回収率を計算します。

**LightGBM:**
```bash
python ml_models/evaluate.py \
    --model models_trained/lightgbm_model.pkl \
    --start-date 2023-07-01 \
    --end-date 2023-09-06
```

**Transformer:**
```bash
python ml_models/evaluate_transformer.py \
    --model models_trained/transformer_model.pt \
    --start-date 2023-07-01 \
    --end-date 2023-09-06
```

**階層ベイズ:**
```bash
python ml_models/evaluate_bayesian.py \
    --model models_trained/bayesian_model.pkl \
    --start-date 2023-07-01 \
    --end-date 2023-09-06
```

**出力例:**
```
================================================================================
モデル評価開始
================================================================================
期間: 2023-07-01 ~ 2023-09-06
対象: 一般戦・G3のみ

評価中: 100%|███████████████████████████| 1234/1234

================================================================================
評価完了
  評価レース数: 1200
  スキップ: 34
================================================================================

【評価結果サマリー】
================================================================================
総レース数: 1200

的中率:
  3艇完全的中: 360 レース (30.00%)
  2艇的中: 480 レース (40.00%)
  1艇的中: 300 レース (25.00%)

3連単ボックス買い（6点 x 100円 = 600円/レース）:
  的中: 360 レース (30.00%)
  総購入額: 720,000円
  総払戻額: 576,000円
  収支: -144,000円
  回収率: 80.00%
================================================================================
```

**階層ベイズモデルの出力例（不確実性指標付き）:**
```
================================================================================
階層ベイズモデル評価開始
================================================================================
期間: 2023-07-01 ~ 2023-09-06
対象: 一般戦・G3のみ

評価中: 100%|███████████████████████████| 1234/1234

================================================================================
評価完了
  評価レース数: 1200
  スキップ: 34
================================================================================

【評価結果サマリー】
================================================================================
総レース数: 1200

的中率:
  3艇完全的中: 360 レース (30.00%)
  2艇的中: 480 レース (40.00%)
  1艇的中: 300 レース (25.00%)

3連単ボックス買い（6点 x 100円 = 600円/レース）:
  的中: 360 レース (30.00%)
  総購入額: 720,000円
  総払戻額: 576,000円
  収支: -144,000円
  回収率: 80.00%

ベイズ特有の指標:
  平均不確実性: 0.023
================================================================================
```

## ファイル構成

```
ml_models/
├── README.md                        # このファイル
├── race_grade_classifier.py        # レースグレード分類
├── feature_engineering.py          # 特徴量エンジニアリング
├── build_dataset.py                 # データセット構築
│
├── train_model.py                   # LightGBMモデル訓練
├── predict.py                       # LightGBM予測実行
├── evaluate.py                      # LightGBMモデル評価
│
├── transformer_model.py             # Transformerモデル定義
├── train_transformer.py             # Transformer訓練
├── predict_transformer.py           # Transformer予測
├── evaluate_transformer.py          # Transformer評価
├── feature_importance_analyzer.py   # 特徴量重要度分析
│
├── hierarchical_bayesian_model.py   # 階層ベイズモデル定義
├── train_bayesian.py                # 階層ベイズ訓練
├── predict_bayesian.py              # 階層ベイズ予測
└── evaluate_bayesian.py             # 階層ベイズ評価

data/
├── processed/                       # 前処理済みデータ
│   └── training_dataset.csv        # 訓練データセット
└── features/                        # 特徴量データ

models_trained/
├── lightgbm_model.pkl              # LightGBM訓練済みモデル
├── transformer_model.pt            # Transformer訓練済みモデル
├── bayesian_model.pkl              # 階層ベイズモデル（メタデータ）
├── bayesian_model_trace.nc         # 階層ベイズMCMCトレース
├── feature_importance.png          # LightGBM特徴量重要度
├── learning_curve.png              # Transformer学習曲線
└── feature_importance_comparison.png  # 特徴量重要度比較
```

## 使用している特徴量

### 選手関連（約10次元）
- 全国勝率・連対率
- 地元勝率・連対率
- 年齢・体重
- 級別
- 過去成績（直近90日間）

### モーター・ボート（2次元）
- モーター2連対率
- ボート2連対率

### レース条件（5次元）
- 競艇場ID
- 天候
- 風向・風速
- 波高

### 当日情報（3次元）
- 展示タイム
- スタートタイミング
- 進入コース

**合計: 約20〜25次元**

## 注意事項

### データベースへのアクセス

- データベースファイル（sqlite.sqlite3）が必要です
- Git LFSを使用している場合は `git lfs pull` でダウンロードしてください

### 対象レース

- **対象:** 一般戦・G3戦
- **対象外:** G2・G1・PSG1・SG

### 計算時間

- **データセット構築:** 数十分〜数時間
- **モデル訓練:** 数分〜数十分
- **予測:** 1レースあたり数秒

### 精度について

- モデルの精度は訓練データの品質に依存します
- 定期的にモデルを再訓練することを推奨します
- 回収率100%以上を保証するものではありません

## トラブルシューティング

### エラー: "file is not a database"

→ Git LFSでデータベースをダウンロードしてください:
```bash
git lfs pull
```

### エラー: "レースが見つかりません"

→ 指定した日付・競艇場・レース番号が正しいか確認してください

### エラー: "モデルが訓練されていません"

→ モデルファイルのパスが正しいか確認してください

## Transformerモデルの特徴

### 1. Feature-wise Attention (特徴量方向のアテンション)

各特徴量に学習可能な重要度ゲートを適用します。

```python
# 事前重要度を設定可能
feature_importance = np.array([
    1.5,  # スタートタイミング（重要）
    1.3,  # 選手勝率（重要）
    0.8,  # 気温（やや重要でない）
    ...
])

model = BoatRaceTransformer(
    n_features=20,
    feature_importance=feature_importance,
    use_feature_gating=True
)
```

### 2. 特徴量重要度の可視化

3つの手法で重要度を分析可能:

- **Attention Weights**: Transformerのアテンション機構から重要度を取得
- **Integrated Gradients**: 勾配ベースの解釈手法
- **SHAP Approximation**: Shapley値による寄与度計算

```bash
# 特徴量重要度を分析
python -c "
from ml_models.transformer_model import BoatRaceTransformer
from ml_models.feature_importance_analyzer import FeatureImportanceAnalyzer

# モデル読み込み
model = ...

# 分析器作成
analyzer = FeatureImportanceAnalyzer(model, feature_names)

# 全手法で分析
results = analyzer.analyze_all_methods(X, save_dir='models_trained')
"
```

### 3. モデル比較

| 項目 | LightGBM | Transformer | 階層ベイズ |
|------|----------|-------------|----------|
| 訓練速度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐ |
| 予測速度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| 精度 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 解釈性 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| GPU対応 | ✗ | ✓ | △ |
| 不確実性定量化 | ✗ | ✗ | ✓ |
| 特徴量間の関係学習 | △ | ◎ | ○ |
| 事前知識の組み込み | △ | ◎ | ◎ |
| データ不均衡への対応 | △ | △ | ◎ |
| 階層構造の学習 | ✗ | ✗ | ✓ |

**推奨用途:**
- **LightGBM**: 高速推論が必要、大量のレースを一括予測
- **Transformer**: 精度重視、特徴量の関係性を重視、解釈性が重要
- **階層ベイズ**: 不確実性の定量化が必要、選手・モーター・競艇場の個体差を重視、データ不均衡がある場合

## 今後の改善案

- [x] LightGBMモデルの実装
- [x] Transformerモデルの実装
- [x] 階層ベイズモデルの実装
- [x] 特徴量重要度分析
- [ ] オッズ情報の追加
- [ ] コース別成績の追加
- [ ] アンサンブルモデル（LightGBM + Transformer + Bayesian）
- [ ] リアルタイム予測API
- [ ] Web UI の開発

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。
