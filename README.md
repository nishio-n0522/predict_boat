# ボートレース予測AI

## 概要

LightGBMを使用したボートレース予測AIです。一般戦およびG3戦を対象に、3連単ボックス買いのための3艇を推奨します。

### 予測内容
- **6艇のうち最も舟券内（3着以内）にくると思われる2艇の予測と確率**
- **残り4艇のうち、3着以内になる確率の高い舟と確率**
- **3連単ボックス買い（6点）の推奨**

### 新機能
- **リアルタイム予測**: 当日の出走表を自動取得して予測実行
- **全24場対応**: すべてのボートレース場からデータをスクレイピング可能
- **複数の予測モデル**: LightGBM、ルールベース、Transformerなど

## データ情報

1. データの期間: 2020/04/01 ~ 2023/09/06
2. データベース設計: .db_design/db_design.dio 論理設計を参照
3. 対象グレード: 一般戦、G3（G2, G1, PSG1, SGは対象外）

## 環境構築

1. リポジトリをクローン
   ```bash
   git clone https://github.com/nishio-n0522/predict_boat.git
   cd predict_boat
   ```

2. 仮想環境のセットアップ
   ```bash
   python -m venv .venv
   ```

3. 仮想環境のアクティベート
   - Windows: `.venv/Scripts/activate`
   - Mac/Linux: `source .venv/bin/activate`

4. ライブラリのインストール
   ```bash
   pip install -r requirements.txt
   ```

5. データベースのダウンロード（Git LFS使用時）
   ```bash
   git lfs pull
   ```

## 使い方

### クイックスタート（機械学習モデル）

```bash
# 1. 訓練データセットの構築
python ml_models/build_dataset.py

# 2. モデルの訓練
python ml_models/train_model.py

# 3. レースを予測
python ml_models/predict.py --date 2023-08-01 --stadium 1 --race 1
```

詳細な使い方は [ml_models/README.md](ml_models/README.md) を参照してください。

### クイックスタート（リアルタイム予測）

```bash
# 徳山1Rの予測（当日の出走表を自動取得）
python predict_race.py 徳山 1

# 会場IDで指定
python predict_race.py 18 1

# JSON形式で出力
python predict_race.py 徳山 1 --json
```

詳細な使い方は [PREDICTION_GUIDE.md](PREDICTION_GUIDE.md) を参照してください。

### クイックスタート（データスクレイピング）

```bash
# 単一会場のスクレイピング
python scrape_boatrace.py 徳山

# 複数会場の一括スクレイピング
python scrape_all_venues.py --all

# データベースに保存
python save_scraped_data.py data/boatrace_scraped/tokuyama_20240115.json
```

詳細な使い方は [SCRAPING_GUIDE.md](SCRAPING_GUIDE.md) を参照してください。

### クイックスタート（Web RPA実験）

**⚠️ 重要**: Web RPA機能は教育目的のみに提供されています。利用規約を遵守し、承認された環境でのみ使用してください。

```bash
# 実験サンプルの実行
python web_rpa/example_experiment.py

# ブラウザ初期化の実験
# 対話型メニューから実験を選択
```

詳細な使い方は [WEB_RPA_GUIDE.md](WEB_RPA_GUIDE.md) を参照してください。

## ディレクトリ構成

```
predict_boat/
├── .db_design/              データベース設計
│   └── db_design.dio
├── db/                      データベーススキーマ定義
│   ├── __init__.py
│   ├── db_setting.py       DB接続設定
│   ├── player.py           選手テーブル
│   ├── motor.py            モーターテーブル
│   ├── boat.py             ボートテーブル
│   ├── each_race_results.py レース結果テーブル
│   ├── session_stats.py    節間成績テーブル（NEW）
│   ├── live_info.py        直前情報テーブル（NEW）
│   └── ...
├── ml_models/              機械学習モデル
│   ├── README.md           詳細な使い方ガイド
│   ├── race_grade_classifier.py  レースグレード分類
│   ├── feature_engineering.py    特徴量エンジニアリング
│   ├── build_dataset.py          データセット構築
│   ├── train_model.py            モデル訓練
│   ├── predict.py                予測実行
│   ├── evaluate.py               モデル評価
│   ├── transformer_model.py      Transformerモデル（NEW）
│   ├── hierarchical_bayesian_model.py ベイズモデル（NEW）
│   └── ...
├── prediction/             リアルタイム予測モジュール（NEW）
│   ├── __init__.py
│   ├── data_preprocessor.py    データ前処理
│   └── inference_engine.py     推論エンジン
├── web_rpa/                Web RPA実験用フレームワーク（NEW）
│   ├── __init__.py
│   ├── config.py            設定管理
│   ├── base_automation.py   ベース自動化クラス
│   ├── boatrace_rpa_experiment.py ボートレース実験用RPA
│   ├── example_experiment.py      実験サンプルスクリプト
│   ├── screenshots/         スクリーンショット保存先
│   └── logs/                ログファイル保存先
├── backend/                Webアプリケーションバックエンド（NEW）
│   ├── main.py             FastAPI アプリケーション
│   ├── routers/            APIルーター
│   ├── schemas/            データスキーマ
│   └── services/           ビジネスロジック
├── frontend/               Webアプリケーションフロントエンド（NEW）
│   ├── src/                Reactソースコード
│   ├── package.json        依存関係
│   └── ...
├── data/                    データ保存先
│   ├── processed/           前処理済みデータ
│   ├── features/            特徴量データ
│   └── boatrace_scraped/    スクレイピングデータ（NEW）
├── models_trained/          訓練済みモデル保存先
├── boatrace_venues.py      全24場の競艇場情報（NEW）
├── scrape_boatrace.py      汎用スクレイピングスクリプト（NEW）
├── scrape_all_venues.py    一括スクレイピングスクリプト（NEW）
├── fetch_live_data.py      リアルタイム出走表取得（NEW）
├── predict_race.py         リアルタイム予測アプリケーション（NEW）
├── save_scraped_data.py    データベース保存スクリプト（NEW）
├── dl_parameters.py        パラメータダウンロード
├── dl_records.py           レース結果ダウンロード
├── extract_records_data.py データ抽出
├── uncompress_data.py      データ解凍
├── check_db_structure.py   DB構造確認
├── requirements.txt        依存ライブラリ
├── sqlite.sqlite3          データベースファイル
├── README.md               このファイル
├── SCRAPING_GUIDE.md       スクレイピングガイド（NEW）
├── PREDICTION_GUIDE.md     予測機能ガイド（NEW）
├── WEB_RPA_GUIDE.md        Web RPA実験ガイド（NEW）
├── DOCUMENTATION.md        システムドキュメント（NEW）
└── WEBAPP_README.md        Webアプリガイド（NEW）
```

## 機能

### 1. 機械学習モデル（ml_models/）

LightGBMを使用した高精度な予測モデル。過去データから学習し、3連単ボックスを推奨。

- レースグレード自動分類
- 豊富な特徴量エンジニアリング
- モデル評価機能
- Transformerモデル対応
- 階層ベイズモデル対応

### 2. リアルタイム予測（predict_race.py）

当日の出走表を自動取得して即座に予測。

- 指定した会場・レース番号の出走表を自動取得
- データベースから過去データを参照
- 単勝・2連単・3連単の予測
- ルールベースモデル（統計的手法）
- 機械学習モデル対応

### 3. データスクレイピング（scrape_boatrace.py）

全24場のボートレース場から自動データ収集。

- 全国24場対応
- レース詳細、節間成績、直前情報を取得
- 並列処理対応
- データベース自動保存

### 4. Webアプリケーション（backend/ + frontend/）

ブラウザからアクセスできる予測インターフェース。

- 予測実行画面
- モデル訓練画面
- モデル比較画面
- REST API

### 5. Web RPA実験フレームワーク（web_rpa/）

**⚠️ 教育目的のみ**: Web自動化の実験用フレームワーク。

- Seleniumベースのブラウザ自動化
- 設定管理とエラーハンドリング
- スクリーンショット・ログ機能
- リトライロジック
- 人間らしい操作の模擬

**重要**: 利用規約を遵守し、承認された環境でのみ使用してください。実際の舟券購入ロジックは含まれていません（構造のみ提供）。

## 対応会場（全24場）

桐生、戸田、江戸川、平和島、多摩川、浜名湖、蒲郡、常滑、津、三国、びわこ、住之江、尼崎、鳴門、丸亀、児島、宮島、徳山、下関、若松、芦屋、福岡、唐津、大村

## 予測モデルの種類

### 1. LightGBMモデル（ml_models/train_model.py）
過去データから学習した高精度モデル

### 2. Transformerモデル（ml_models/train_transformer.py）
時系列データを考慮した深層学習モデル

### 3. 階層ベイズモデル（ml_models/train_bayesian.py）
不確実性を考慮した統計モデル

### 4. ルールベースモデル（prediction/inference_engine.py）
統計的手法による即時予測モデル

## ドキュメント

- **[ml_models/README.md](ml_models/README.md)**: 機械学習モデルの詳細
- **[PREDICTION_GUIDE.md](PREDICTION_GUIDE.md)**: リアルタイム予測機能の詳細
- **[SCRAPING_GUIDE.md](SCRAPING_GUIDE.md)**: スクレイピング機能の詳細
- **[DOCUMENTATION.md](DOCUMENTATION.md)**: システム全体のドキュメント
- **[WEBAPP_README.md](WEBAPP_README.md)**: Webアプリケーションの使い方

## 注意事項

### データスクレイピング
- 実際のサイト構造に合わせて、スクレイピングコードのカスタマイズが必要な場合があります
- サーバーに負荷をかけないよう、適切な待機時間を設定してください（デフォルト: 2秒/レース）
- 並列処理は最大3ワーカーを推奨（サーバー負荷を考慮）
- サイトの利用規約を確認し、遵守してください

### 予測機能
- 予測は統計的手法・機械学習モデルに基づくものであり、レース結果を保証するものではありません
- データベースに過去データがない場合、予測精度が低下する可能性があります
- 予測結果の使用は自己責任でお願いします

## ライセンス

このプロジェクトは個人利用目的で作成されています。

## 貢献

プルリクエストやイシューの報告を歓迎します。

## サポート

問題が発生した場合は、各ガイドドキュメントのトラブルシューティングセクションを参照してください。
