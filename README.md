# 競艇データ分析用

## めも

1. データの期間: 2020/04/01 ~ 2023/09/06
2. データベース設計: .db_design/db_design.dio 論理設計を参照

## 環境構築

1. リポジトリをクローン  
   `git clone https://github.com/nishio-n0522/predict_boat.git`
2. 仮想環境のセットアップ  
   `python -m venv .venv`
3. 仮想環境のアクティベート  
   [Windows] `.venv/Scripts/activate`  
   [Mac] `source .venv/bin/activate`
4. ライブラリのインストール  
   `pip install -r requirements.txt`

## ディレクトリ構成

|- .db_design
| |- db_design.dio: : データベース設計
|- samples: 競艇過去データを抽出する対象のテキストデータのサンプルディレクトリ
|- data: データ保存用ディレクトリ
| |- boatrace_scraped: 全ボートレース場からスクレイピングしたデータの保存先
|- db: それぞれの db のテーブル作成用のスクリプトがまとめられたディレクトリ
| |- session_stats.py: 節間成績テーブル
| |- live_info.py: 直前情報テーブル
|- dl_parameters.py: 試合前のパラメータ情報ファイルをダウンロードするためのスクリプト
|- dl_records.py: 試合後のレース結果ファイルをダウンロードするためのスクリプト
|- boatrace_venues.py: 全24場の競艇場情報管理モジュール
|- scrape_boatrace.py: 全ボートレース場対応の汎用スクレイピングスクリプト
|- scrape_all_venues.py: 複数会場を一括でスクレイピングするスクリプト
|- scrape_tokuyama.py: ボートレース徳山専用スクレイピングスクリプト（後方互換性のため残存）
|- save_scraped_data.py: スクレイピングしたデータをデータベースに保存するスクリプト
|- extract_records_data.py: テキストファイルから必要な情報を取得し、データベースに保管するためのスクリプト
|- README.md: この説明そのものの markdown
|- SCRAPING_GUIDE.md: スクレイピング機能の詳細な使用ガイド
|- requirements.txt: 必要なライブラリ情報が記載されたテキストファイル
|- uncompress_data.py: ダウンロードしたファイルを解凍するためのスクリプト
|- sqlite.sqlite3

## 新機能: 全ボートレース場対応のスクレイピング

全国24場の競艇場公式サイトから、レース開催日の全レース(1~12R)のデータをスクレイピングする機能を実装しました。

### 対応会場（全24場）

桐生、戸田、江戸川、平和島、多摩川、浜名湖、蒲郡、常滑、津、三国、びわこ、住之江、尼崎、鳴門、丸亀、児島、宮島、徳山、下関、若松、芦屋、福岡、唐津、大村

### 取得できるデータ

1. **節間成績**: 選手の節間（開催期間中）の成績（勝率、着順率など）
2. **直前情報**: 展示タイム、チルト、進入コース、オッズなど
3. **レース詳細**: レース名、天候、風速、波高など

### クイックスタート

#### 1. 単一会場のスクレイピング

```bash
# 会場名で指定
python scrape_boatrace.py 徳山

# 会場IDで指定（1-24）
python scrape_boatrace.py 18

# 特定の日付を指定
python scrape_boatrace.py 徳山 -d 2024-01-15
```

#### 2. 複数会場の一括スクレイピング

```bash
# 今日開催されている全会場を自動取得してスクレイピング
python scrape_all_venues.py

# 特定の会場のみ（カンマ区切り）
python scrape_all_venues.py -v 1,2,18

# 全会場を対象（開催有無に関わらず）
python scrape_all_venues.py --all

# 並列処理で高速化（最大3会場同時）
python scrape_all_venues.py --all -p -w 3
```

#### 3. データベースに保存

```bash
# スクレイピング結果をデータベースに保存
python save_scraped_data.py data/boatrace_scraped/tokuyama_20240115.json
```

### 対応している会場一覧の確認

```bash
# Pythonで確認
python boatrace_venues.py

# 出力例:
# 1. 桐生 (kiryu) - https://www.kiryu-kyotei.com/
# 2. 戸田 (toda) - https://www.boatrace-toda.jp/
# ...
```

### 詳細な使い方

詳細な使用方法、カスタマイズ方法については [SCRAPING_GUIDE.md](SCRAPING_GUIDE.md) を参照してください。

### 注意事項

- 実際のサイト構造に合わせて、スクレイピングコードのカスタマイズが必要な場合があります
- サーバーに負荷をかけないよう、適切な待機時間を設定してください（デフォルト: 2秒/レース）
- 並列処理は最大3ワーカーを推奨（サーバー負荷を考慮）
- サイトの利用規約を確認し、遵守してください
