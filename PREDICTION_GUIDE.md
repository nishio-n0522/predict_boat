# ボートレース予測機能 使用ガイド

## 概要

ボートレースの予測機能を提供します。会場とレース番号を指定するだけで、当日の出走表データを自動取得し、AI/統計モデルによる予測を実行できます。

## 機能

### 1. リアルタイム出走表取得
- 指定した会場・レース番号の出走表を自動取得
- 選手情報、モーター情報、展示タイム、オッズなどを収集

### 2. 特徴量生成
- データベースから過去データを参照
- 選手の全国勝率・当地勝率
- モーター2連対率
- 節間成績
- 直前情報（展示タイム、チルト、体重など）

### 3. 予測エンジン
- 単勝・2連単・3連単の予測
- ルールベースモデル（統計的手法）
- 機械学習モデル対応（将来拡張可能）

## セットアップ

### 必要なライブラリのインストール

```bash
pip install -r requirements.txt
```

追加されたライブラリ:
- `numpy`: 数値計算
- `pandas`: データ処理
- `scikit-learn`: 機械学習（将来の拡張用）

## 使用方法

### 基本的な使い方

#### 1. 単一レースの予測

```bash
# 会場名とレース番号で予測
python predict_race.py 徳山 1

# 会場IDで指定
python predict_race.py 18 1

# 特定の日付を指定
python predict_race.py 徳山 1 -d 2024-01-15

# Seleniumを使用（動的コンテンツ対応）
python predict_race.py 徳山 1 -s
```

#### 2. JSON形式で出力

```bash
# JSON形式で結果を取得
python predict_race.py 徳山 1 --json
```

#### 3. 会場一覧の表示

```bash
# 全会場を表示
python predict_race.py --list
```

### Pythonコードから使用

```python
from datetime import date
from predict_race import RacePredictor

# 予測エンジンを初期化
predictor = RacePredictor()

try:
    # レース予測を実行
    result = predictor.predict_race(
        venue="徳山",  # または venue=18
        race_number=1,
        target_date=date.today()
    )

    # 結果を表示
    predictor.display_prediction(result)

    # または結果を取得して処理
    predictions = result['predictions']
    top3 = result['top3']
    quinella_top5 = result['quinella_top5']
    trifecta_top5 = result['trifecta_top5']

finally:
    predictor.close()
```

### 個別モジュールの使用

#### 出走表取得のみ

```python
from fetch_live_data import fetch_race_card_simple

# 出走表を取得
race_card = fetch_race_card_simple(venue="徳山", race_number=1)

print(f"会場: {race_card['venue_name']}")
print(f"レース名: {race_card['race_name']}")
print(f"艇数: {len(race_card['boats'])}")
```

#### データ前処理のみ

```python
from fetch_live_data import fetch_race_card_simple
from prediction.data_preprocessor import RaceDataPreprocessor

# 出走表を取得
race_card = fetch_race_card_simple("徳山", 1)

# 前処理
preprocessor = RaceDataPreprocessor()
try:
    features_df = preprocessor.preprocess_race_card(race_card)
    print(features_df)
finally:
    preprocessor.close()
```

#### 推論のみ

```python
from prediction.inference_engine import PredictionEngine
import pandas as pd

# 推論エンジンを初期化
engine = PredictionEngine()

# 特徴量DataFrame（6艇分）を用意
# features_df = ...

# 予測実行
result = engine.predict(features_df)

# 単勝予測
for pred in result['predictions']:
    print(f"{pred['rank']}位: {pred['boat_number']}号艇 ({pred['probability']:.1%})")

# 2連単予測
quinella = engine.predict_quinella(result['predictions'])
for b1, b2, prob in quinella[:5]:
    print(f"{b1}-{b2}: {prob:.2%}")

# 3連単予測
trifecta = engine.predict_trifecta(result['predictions'])
for b1, b2, b3, prob in trifecta[:5]:
    print(f"{b1}-{b2}-{b3}: {prob:.3%}")
```

## 予測結果の見方

### 出力例

```
============================================================
徳山 R1 - 予選
日付: 2024-01-15
モデル: rule_based
============================================================

【単勝予測】
◎ 1位: 1号艇 (確率:  35.2%, スコア: 0.723)
○ 2位: 3号艇 (確率:  22.5%, スコア: 0.651)
▲ 3位: 4号艇 (確率:  18.3%, スコア: 0.598)
   4位: 2号艇 (確率:  12.1%, スコア: 0.521)
   5位: 5号艇 (確率:   7.8%, スコア: 0.462)
   6位: 6号艇 (確率:   4.1%, スコア: 0.398)

推奨: 1-3-4

【2連単予測（上位5通り）】
1. 1-3 (確率: 7.92%)
2. 1-4 (確率: 6.45%)
3. 3-1 (確率: 5.06%)
4. 1-2 (確率: 4.26%)
5. 3-4 (確率: 4.12%)

【3連単予測（上位5通り）】
1. 1-3-4 (確率: 1.450%)
2. 1-3-2 (確率: 0.959%)
3. 1-4-3 (確率: 1.182%)
4. 3-1-4 (確率: 0.927%)
5. 1-4-2 (確率: 0.780%)
============================================================
```

### 記号の意味

- ◎: 本命（1位予測）
- ○: 対抗（2位予測）
- ▲: 単穴（3位予測）

### 確率の解釈

- 単勝確率: 各艇が1着になる確率
- 2連単確率: 指定した順番で1-2着になる確率
- 3連単確率: 指定した順番で1-2-3着になる確率

## 予測モデルについて

### ルールベースモデル（デフォルト）

統計的手法を用いた予測モデル。以下の特徴量を重み付けしてスコア化：

| 特徴量 | 重み |
|--------|------|
| 選手の全国勝率 | 30% |
| 選手の当地勝率 | 25% |
| 節間成績勝率 | 20% |
| モーター2連対率 | 15% |
| 展示タイム | 10% |
| オッズ（補正） | 5% |

計算式:
```
スコア = 全国勝率×0.30 + 当地勝率×0.25 + 節間勝率×0.20
       + モーター2連対率×0.15 + 展示タイムスコア×0.10
       + オッズスコア×0.05
```

確率への変換: ソフトマックス関数を使用

### 機械学習モデル（今後対応予定）

学習済みモデルを指定して使用可能：

```bash
python predict_race.py 徳山 1 -m models/trained_model.pkl
```

対応予定のモデル:
- ランダムフォレスト
- XGBoost
- ニューラルネットワーク

## ディレクトリ構成

```
|- prediction/
|  |- __init__.py: パッケージ初期化
|  |- data_preprocessor.py: データ前処理モジュール
|  |- inference_engine.py: 推論エンジン
|- fetch_live_data.py: リアルタイム出走表取得
|- predict_race.py: メイン予測アプリケーション
|- models/: 学習済みモデル保存先（今後追加）
```

## トラブルシューティング

### 1. データ取得エラー

```
エラー: 出走表の取得に失敗しました
```

**対処法**:
- サイトのURL構造が変更されている可能性があります
- `scrape_boatrace.py`のURLパターンを確認してください
- `-s`オプションでSeleniumを使用してみてください

### 2. 特徴量抽出エラー

```
エラー: 特徴量の抽出に失敗しました
```

**対処法**:
- データベースに過去データがない可能性があります
- 選手情報、モーター情報がDBに登録されているか確認してください

### 3. データベース接続エラー

```
エラー: データベースへの接続に失敗しました
```

**対処法**:
- `sqlite.sqlite3`が存在するか確認
- データベースファイルのパーミッションを確認

## カスタマイズ

### 予測モデルの重みを調整

`prediction/inference_engine.py`の`_calculate_boat_score`メソッドで重みを変更：

```python
def _calculate_boat_score(self, boat_features: pd.Series) -> float:
    score = 0.0

    # 重みを調整
    score += player_national_win_rate * 0.35  # 30% → 35%に変更
    score += player_local_win_rate * 0.20     # 25% → 20%に変更
    # ...

    return score
```

### 新しい特徴量の追加

1. `prediction/data_preprocessor.py`で特徴量を追加
2. `_extract_boat_features`メソッドに処理を追加
3. `get_feature_columns`メソッドにカラム名を追加

### 機械学習モデルの学習

```python
import pickle
from sklearn.ensemble import RandomForestClassifier
from prediction.data_preprocessor import RaceDataPreprocessor

# トレーニングデータを準備
# X_train, y_train = ...

# モデルを学習
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# モデルを保存
with open('models/rf_model.pkl', 'wb') as f:
    pickle.dump(model, f)

# 使用
# python predict_race.py 徳山 1 -m models/rf_model.pkl
```

## 今後の拡張予定

- [ ] 複数レースの一括予測
- [ ] 予測精度の評価機能
- [ ] 機械学習モデルの学習機能
- [ ] Web APIインターフェース
- [ ] 予測履歴の保存・分析
- [ ] オッズ変動の考慮
- [ ] 天候・水面状況の詳細分析

## 注意事項

1. **予測の正確性**: この予測は統計的手法に基づくものであり、レース結果を保証するものではありません
2. **データ更新**: データベースの過去データが最新でない場合、予測精度が低下する可能性があります
3. **サイト構造変更**: 公式サイトの構造変更により、データ取得が失敗する場合があります
4. **責任**: 予測結果の使用は自己責任でお願いします

## サポート

問題が発生した場合:

1. `-v`オプションで詳細ログを確認
2. データベースの状態を確認
3. 公式サイトのアクセス可否を確認

```bash
# 詳細ログ付きで実行
python predict_race.py 徳山 1 -v
```
