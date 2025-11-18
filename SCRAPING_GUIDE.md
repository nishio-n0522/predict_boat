# ボートレース徳山スクレイピング機能 使用ガイド

## 概要

ボートレース徳山の公式サイト (https://www.boatrace-tokuyama.jp/) から、レース開催日の全レース(1~12R)のデータをスクレイピングし、データベースに保存する機能です。

## 取得できるデータ

### 1. 節間成績
- 選手の節間（開催期間中）の成績
- 1着率、2着率、3着率
- 勝率
- 出走回数、着順回数

### 2. 直前情報
- 展示タイム
- チルト（角度）
- 進入コース予想
- スタート展示評価
- モーター調整内容
- 体重・調整体重
- オッズ情報

## セットアップ

### 1. 必要なライブラリのインストール

```bash
pip install -r requirements.txt
```

追加された主なライブラリ:
- `beautifulsoup4`: HTMLパース用
- `lxml`: 高速パーサー
- `selenium`: 動的コンテンツのスクレイピング用
- `webdriver-manager`: ChromeDriverの自動管理

### 2. データベーステーブルの作成

新しく追加されたテーブル:
- `session_stats`: 節間成績テーブル
- `live_info`: 直前情報テーブル

Pythonでテーブルを作成:

```python
from db.db_setting import session_factory
from db.session_stats import SessionStats
from db.live_info import LiveInfo

session = session_factory()
# テーブルが自動的に作成されます
```

## 使用方法

### 基本的な使い方

#### 1. スクレイピングのみ実行（JSONファイルに保存）

```bash
# 今日の日付でスクレイピング
python scrape_tokuyama.py

# 特定の日付でスクレイピング
python scrape_tokuyama.py 2024-01-15
```

実行結果:
- `data/tokuyama_scraped/tokuyama_YYYYMMDD.json` にデータが保存されます

#### 2. JSONファイルからデータベースに保存

```bash
python save_scraped_data.py data/tokuyama_scraped/tokuyama_20240115.json
```

#### 3. スクレイピングとデータベース保存を一度に実行

scrape_tokuyama.pyに以下の機能を追加して使用:

```python
from scrape_tokuyama import TokuyamaRaceScraper
from save_scraped_data import ScrapedDataSaver
from datetime import date

# スクレイパーとセーバーを初期化
scraper = TokuyamaRaceScraper(use_selenium=False)
saver = ScrapedDataSaver()

try:
    # データを取得
    target_date = date.today()
    data = scraper.scrape_all_races(target_date, save_dir="./data/tokuyama_scraped")

    # データベースに保存（オプション）
    # result = saver.save_session_stats(data['session_stats'])
    # result = saver.save_live_info(...)

finally:
    scraper.close()
    saver.close()
```

## カスタマイズ方法

### 1. URL構造の調整

ボートレース徳山の実際のサイト構造に合わせて、`scrape_tokuyama.py` の以下の部分を修正してください:

```python
# レース一覧ページのURL
possible_urls = [
    f"{self.BASE_URL}/race/{date_str}/",
    f"{self.BASE_URL}/races/{date_str}/",
    # 実際のURLパターンを追加
]

# レース詳細ページのURL
possible_urls = [
    f"{self.BASE_URL}/race/{date_str}/{race_number:02d}/",
    # 実際のURLパターンを追加
]
```

### 2. HTMLパーサーのカスタマイズ

サイトの実際のHTML構造に合わせて、以下のメソッドを修正してください:

#### レース詳細のパース (`_parse_race_detail`)

```python
def _parse_race_detail(self, soup: BeautifulSoup, target_date: date, race_number: int) -> Dict:
    # レース名
    race_name_elem = soup.select_one('h1, .race-title, .race-name')
    if race_name_elem:
        detail['race_name'] = race_name_elem.get_text(strip=True)

    # 天候情報
    weather_elem = soup.select_one('.weather-info')
    # ...実際のセレクタに合わせて調整
```

#### 節間成績のパース (`_parse_session_stats`)

```python
def _parse_session_stats(self, soup: BeautifulSoup, target_date: date) -> List[Dict]:
    # 実際のテーブル構造に合わせて実装
    stat_rows = soup.select('table.stats-table tr')
    for row in stat_rows:
        # 選手番号、成績などを抽出
        player_id = row.select_one('.player-id').get_text(strip=True)
        # ...
```

#### 直前情報のパース (`_parse_live_info`)

```python
def _parse_live_info(self, soup: BeautifulSoup, target_date: date, race_number: int) -> Dict:
    # 展示タイム
    exhibition_elem = soup.select_one('.exhibition-time')
    if exhibition_elem:
        info['exhibition_time'] = float(exhibition_elem.get_text(strip=True))
    # ...
```

### 3. 動的コンテンツへの対応

JavaScriptで生成されるコンテンツがある場合は、Seleniumを使用:

```python
# use_selenium=True に変更
scraper = TokuyamaRaceScraper(use_selenium=True, headless=True)
```

## 実際のサイト構造の調査方法

### 1. ブラウザの開発者ツールを使用

1. Chrome/Firefoxでサイトを開く
2. F12キーで開発者ツールを開く
3. ElementsタブでHTML構造を確認
4. 必要なデータのCSSセレクタをコピー

### 2. URLパターンの特定

実際のサイトで以下を確認:
- レース一覧ページのURL
- 各レース詳細ページのURL
- 節間成績ページのURL
- 直前情報ページのURL

例:
```
https://www.boatrace-tokuyama.jp/race/20240115/
https://www.boatrace-tokuyama.jp/race/20240115/01/
https://www.boatrace-tokuyama.jp/race/20240115/racer/
```

### 3. テストスクリプトでの確認

```python
from scrape_tokuyama import TokuyamaRaceScraper
from datetime import date

scraper = TokuyamaRaceScraper(use_selenium=False)

# 特定のURLでテスト
url = "https://www.boatrace-tokuyama.jp/race/20240115/"
html = scraper.get_page_content(url)

from bs4 import BeautifulSoup
soup = BeautifulSoup(html, 'lxml')

# HTML構造を確認
print(soup.prettify())
```

## 自動実行の設定

### cronでの定期実行（Linux/Mac）

12R終了後（通常17:30頃）に自動実行:

```bash
# crontab -e で編集
30 17 * * * cd /path/to/predict_boat && /path/to/.venv/bin/python scrape_tokuyama.py >> logs/scrape.log 2>&1
```

### Windowsタスクスケジューラ

1. タスクスケジューラを開く
2. 「基本タスクの作成」を選択
3. トリガー: 毎日 17:30
4. アクション: プログラムの起動
   - プログラム: `C:\path\to\.venv\Scripts\python.exe`
   - 引数: `scrape_tokuyama.py`
   - 開始: `C:\path\to\predict_boat`

## トラブルシューティング

### 1. SSL証明書エラー

```python
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
```

または、requestsの場合:

```python
response = self.session.get(url, verify=False)
```

### 2. タイムアウトエラー

タイムアウト時間を延長:

```python
response = self.session.get(url, timeout=60)  # 60秒に延長
```

### 3. 文字化け

エンコーディングを明示的に指定:

```python
response.encoding = 'utf-8'  # または 'shift-jis', 'euc-jp'
```

### 4. 動的コンテンツが取得できない

Seleniumを使用して待機時間を調整:

```python
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

wait = WebDriverWait(self.driver, 20)  # 20秒まで待機
element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.target-class')))
```

## データの確認

### 保存されたJSONファイルの確認

```bash
cat data/tokuyama_scraped/tokuyama_20240115.json | python -m json.tool
```

### データベースの確認

```python
from db.db_setting import session_factory
from db.session_stats import SessionStats
from db.live_info import LiveInfo

session = session_factory()

# 節間成績を確認
stats = session.query(SessionStats).filter_by(date='2024-01-15').all()
for stat in stats:
    print(f"選手ID: {stat.player_id}, 勝率: {stat.session_win_rate}")

# 直前情報を確認
live_infos = session.query(LiveInfo).filter_by(date='2024-01-15', race_index=1).all()
for info in live_infos:
    print(f"{info.boat_number}号艇: 展示タイム={info.exhibition_time}")
```

## 注意事項

1. **アクセス頻度**: サーバーに負荷をかけないよう、適切な待機時間（2-3秒）を設定してください
2. **robots.txt**: サイトのrobots.txtを確認し、クローリングが許可されているか確認してください
3. **利用規約**: サイトの利用規約に違反しないよう注意してください
4. **データの正確性**: スクレイピングしたデータの正確性は保証されません。必要に応じて検証してください
5. **サイト構造の変更**: 公式サイトの構造が変更された場合、パーサーの修正が必要です

## 今後の拡張案

- [ ] 他のボートレース場にも対応
- [ ] リアルタイムオッズの取得
- [ ] レース結果の自動取得
- [ ] 異常値検出・データ検証機能
- [ ] Web UIの実装
- [ ] APIサーバー化

## サポート

問題が発生した場合は、以下を確認してください:

1. ログファイルの内容
2. 実際のサイトのHTML構造
3. ネットワーク接続
4. 必要なライブラリのバージョン

詳細なエラーメッセージと共にIssueを作成してください。
