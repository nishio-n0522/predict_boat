# ボートレース予測AI

## 概要

LightGBMを使用したボートレース予測AIです。一般戦およびG3戦を対象に、3連単ボックス買いのための3艇を推奨します。

### 予測内容
- **6艇のうち最も舟券内（3着以内）にくると思われる2艇の予測と確率**
- **残り4艇のうち、3着以内になる確率の高い舟と確率**
- **3連単ボックス買い（6点）の推奨**

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

### クイックスタート

```bash
# 1. 訓練データセットの構築
python ml_models/build_dataset.py

# 2. モデルの訓練
python ml_models/train_model.py

# 3. レースを予測
python ml_models/predict.py --date 2023-08-01 --stadium 1 --race 1
```

詳細な使い方は [ml_models/README.md](ml_models/README.md) を参照してください。

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
│   └── ...
├── ml_models/              機械学習モデル（NEW）
│   ├── README.md           詳細な使い方ガイド
│   ├── race_grade_classifier.py  レースグレード分類
│   ├── feature_engineering.py    特徴量エンジニアリング
│   ├── build_dataset.py          データセット構築
│   ├── train_model.py            モデル訓練
│   ├── predict.py                予測実行
│   └── evaluate.py               モデル評価
├── data/                    データ保存先
│   ├── processed/           前処理済みデータ
│   └── features/            特徴量データ
├── models_trained/          訓練済みモデル保存先
├── samples/                 サンプルデータ
├── dl_parameters.py         パラメータダウンロード
├── dl_records.py            レース結果ダウンロード
├── extract_records_data.py  データ抽出
├── uncompress_data.py       データ解凍
├── check_db_structure.py    DB構造確認
├── requirements.txt         依存ライブラリ
├── sqlite.sqlite3           データベースファイル
└── README.md                このファイル
```

## 機能

### データ収集・管理
- ボートレース公式サイトからのデータダウンロード
- データベースへの格納・管理
- レース結果、選手情報、モーター/ボート性能など

### 機械学習モデル
- LightGBMによる3着以内確率予測
- 特徴量エンジニアリング
- モデル評価（的中率、回収率など）

### 予測機能
- 単一レース予測
- 複数レース一括予測
- 推奨購入艇の提示

## モデル性能（参考）

※実際のデータで訓練後に更新予定

```
予測対象: 一般戦・G3
期間: 2023年7月～9月（テスト期間）

的中率:
  3艇完全的中: XX%
  2艇的中: XX%

3連単ボックス買い:
  的中率: XX%
  回収率: XX%
```

## 開発ロードマップ

- [x] データベース構築
- [x] 特徴量エンジニアリング
- [x] LightGBMモデル実装
- [x] 予測・評価機能
- [ ] モデルの精度向上
- [ ] オッズ情報の追加
- [ ] リアルタイム予測API
- [ ] Web UI開発

## ライセンス

MIT License

## 注意事項

- このツールは予測の精度を保証するものではありません
- 実際の舟券購入は自己責任で行ってください
- ギャンブル依存症にご注意ください
=======
|- .db_design
| |- db_design.dio: : データベース設計
|- samples: 競艇過去データを抽出する対象のテキストデータのサンプルディレクトリ
|- data: データ保存用ディレクトリ
| |- tokuyama_scraped: ボートレース徳山からスクレイピングしたデータの保存先
|- db: それぞれの db のテーブル作成用のスクリプトがまとめられたディレクトリ
| |- session_stats.py: 節間成績テーブル
| |- live_info.py: 直前情報テーブル
|- dl_parameters.py: 試合前のパラメータ情報ファイルをダウンロードするためのスクリプト
|- dl_records.py: 試合後のレース結果ファイルをダウンロードするためのスクリプト
|- scrape_tokuyama.py: ボートレース徳山の公式サイトからレースデータをスクレイピングするスクリプト
|- save_scraped_data.py: スクレイピングしたデータをデータベースに保存するスクリプト
|- extract_records_data.py: テキストファイルから必要な情報を取得し、データベースに保管するためのスクリプト
|- README.md: この説明そのものの markdown
|- SCRAPING_GUIDE.md: スクレイピング機能の詳細な使用ガイド
|- requirements.txt: 必要なライブラリ情報が記載されたテキストファイル
|- uncompress_data.py: ダウンロードしたファイルを解凍するためのスクリプト
|- sqlite.sqlite3

## 新機能: ボートレース徳山スクレイピング

ボートレース徳山の公式サイトから、レース開催日の全レース(1~12R)のデータをスクレイピングする機能を追加しました。

### 取得できるデータ

1. **節間成績**: 選手の節間（開催期間中）の成績（勝率、着順率など）
2. **直前情報**: 展示タイム、チルト、進入コース、オッズなど

### クイックスタート

```bash
# 1. 今日の日付でスクレイピング実行
python scrape_tokuyama.py

# 2. 特定の日付でスクレイピング
python scrape_tokuyama.py 2024-01-15

# 3. スクレイピングしたデータをデータベースに保存
python save_scraped_data.py data/tokuyama_scraped/tokuyama_20240115.json
```

### 詳細な使い方

詳細な使用方法、カスタマイズ方法については [SCRAPING_GUIDE.md](SCRAPING_GUIDE.md) を参照してください。

### 注意事項

- 実際のサイト構造に合わせて、スクレイピングコードのカスタマイズが必要な場合があります
- サーバーに負荷をかけないよう、適切な待機時間を設定してください
- サイトの利用規約を確認し、遵守してください