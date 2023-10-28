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
|- dl_parameters.py: 試合前のパラメータ情報ファイルをダウンロードするためのスクリプト  
|- dl_records.py: 試合後のレース結果ファイルをダウンロードするためのスクリプト  
|- extract_records_data.py: テキストファイルから必要な情報を取得し、データベースに保管するためのスクリプト  
|- README.md: この説明そのものの markdown  
|- requirements.txt: 必要なライブラリ情報が記載されたテキストファイル  
|- uncompress_data.py: ダウンロードしたファイルを解凍するためのスクリプト  
|- db: それぞれの db のテーブル作成用のスクリプトがまとめられたディレクトリ
|- sqlite.sqlite3
