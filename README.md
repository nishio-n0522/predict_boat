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
