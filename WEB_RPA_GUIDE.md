# Web RPA実験用フレームワーク ガイド

## ⚠️ 重要な免責事項

**このフレームワークは教育目的のみに提供されています。**

### 必ず守ってください

1. **利用規約の遵守**: ボートレース公式サイトの利用規約を必ず確認し、遵守してください
2. **法令遵守**: すべての適用される法律と規制を遵守してください
3. **承認された環境のみ**: 承認されたテスト環境でのみ使用してください
4. **自己責任**: このコードの使用によるすべての結果について、あなた自身が全責任を負います

### 禁止事項

- ❌ 無断での自動化
- ❌ 利用規約に違反する行為
- ❌ 不正アクセス
- ❌ レート制限の無視
- ❌ 承認されていない自動取引

---

## 📁 ディレクトリ構成

```
web_rpa/
├── __init__.py                      # パッケージ初期化
├── config.py                         # 設定管理
├── base_automation.py                # ベース自動化クラス
├── boatrace_rpa_experiment.py        # ボートレース実験用RPA
├── example_experiment.py             # 実験サンプルスクリプト
├── screenshots/                      # スクリーンショット保存先
└── logs/                            # ログファイル保存先
```

---

## 🚀 セットアップ

### 1. 依存関係のインストール

既に`requirements.txt`に含まれていますが、必要なライブラリは以下の通りです：

```bash
pip install selenium webdriver-manager beautifulsoup4 lxml
```

### 2. 環境変数の設定（オプション）

認証情報を環境変数で管理する場合：

```bash
# .envファイルを作成（.gitignoreに追加すること！）
echo "BOATRACE_USERNAME=your_username" >> .env
echo "BOATRACE_PASSWORD=your_password" >> .env
echo "BOATRACE_PIN=your_pin" >> .env
```

**重要**: `.env`ファイルは絶対にGitにコミットしないでください！

### 3. ディレクトリの作成

```bash
mkdir -p web_rpa/screenshots web_rpa/logs
```

---

## 📖 基本的な使い方

### 実験サンプルの実行

```bash
python web_rpa/example_experiment.py
```

対話型メニューから各実験を選択できます：

1. **ブラウザ初期化とナビゲーション**: 基本的なブラウザ操作
2. **要素の検査**: ページ要素の検索と抽出
3. **ワークフロー構造**: RPAの典型的な処理フロー
4. **エラーハンドリング**: エラー処理とリトライロジック

---

## 🔧 コア機能

### 1. 設定管理 (`config.py`)

```python
from web_rpa.config import RPAConfig

# カスタム設定の作成
config = RPAConfig(
    headless=False,           # ヘッドレスモード（False=ブラウザ表示）
    page_load_timeout=30,     # ページ読み込みタイムアウト（秒）
    max_retries=3,            # 最大リトライ回数
    screenshot_on_error=True, # エラー時にスクリーンショット撮影
    log_level="INFO",         # ログレベル
)
```

#### 主な設定項目

| 設定項目 | 説明 | デフォルト値 |
|---------|------|------------|
| `headless` | ヘッドレスモード | `False` |
| `browser_type` | ブラウザの種類 | `"chrome"` |
| `page_load_timeout` | ページ読み込みタイムアウト（秒） | `30` |
| `max_retries` | 最大リトライ回数 | `3` |
| `screenshot_on_error` | エラー時スクリーンショット | `True` |
| `min_action_delay` | アクション間の最小遅延（秒） | `0.5` |
| `max_action_delay` | アクション間の最大遅延（秒） | `2.0` |

### 2. ベース自動化クラス (`base_automation.py`)

#### 基本的な使用例

```python
from web_rpa.base_automation import BaseWebAutomation
from selenium.webdriver.common.by import By

# コンテキストマネージャーで使用（自動クリーンアップ）
with BaseWebAutomation() as rpa:
    # ページに移動
    rpa.navigate_to("https://example.com")

    # 要素を安全に検索
    element = rpa.find_element_safe(By.ID, "some_id")
    if element:
        print(f"要素が見つかりました: {element.text}")

    # クリック（リトライ付き）
    success = rpa.click_element_safe(By.CSS_SELECTOR, ".button-class")

    # テキスト入力（人間らしいタイピング）
    rpa.input_text_safe(By.NAME, "username", "test_user")

    # スクリーンショット撮影
    rpa.take_screenshot("result.png")
```

#### 主要メソッド

| メソッド | 説明 | 戻り値 |
|---------|------|-------|
| `start()` | ブラウザを起動 | - |
| `stop()` | ブラウザを終了 | - |
| `navigate_to(url)` | URLに移動 | - |
| `find_element_safe(by, value)` | 要素を安全に検索 | WebElement or None |
| `click_element_safe(by, value)` | 要素を安全にクリック | bool |
| `input_text_safe(by, value, text)` | テキストを安全に入力 | bool |
| `take_screenshot(name)` | スクリーンショット撮影 | ファイルパス |
| `execute_with_retry(func)` | リトライ付きで関数実行 | 関数の戻り値 |

### 3. ボートレース実験用RPA (`boatrace_rpa_experiment.py`)

**⚠️ 注意**: このクラスのメソッドはほとんどがプレースホルダーです。実際のロジックは自分で実装する必要があります。

```python
from web_rpa.boatrace_rpa_experiment import create_experiment_instance

# インスタンス作成
rpa = create_experiment_instance(headless=False)

try:
    # ブラウザ起動
    rpa.start()

    # ログイン（実装必要）
    # success = rpa.login("username", "password")

    # レースページに移動（実装必要）
    # rpa.navigate_to_race(venue_id=18, race_number=1)

    # レース情報取得（実装必要）
    # race_info = rpa.get_race_information()

finally:
    # 必ずクリーンアップ
    rpa.stop()
```

#### 実装が必要なメソッド

以下のメソッドは**構造のみ**提供されており、実際のロジックは実装されていません：

- `login()`: ログイン処理
- `logout()`: ログアウト処理
- `navigate_to_race()`: レースページへの移動
- `get_race_information()`: レース情報の取得
- `select_bet_type()`: 舟券タイプの選択
- `place_bet_experimental()`: 舟券購入（**意図的に未実装**）
- `check_bet_history()`: 購入履歴の確認
- `check_balance()`: 残高確認

---

## 💻 実装ガイド

### ステップ1: ページ構造の調査

実際のロジックを実装する前に、対象ページの構造を調査してください。

1. **ブラウザのデベロッパーツールを開く**
   - Chrome: `F12` または `Ctrl+Shift+I`
   - 「Elements」タブで要素を検査

2. **要素のセレクターを特定**
   ```python
   # 例: ログインフォームの要素
   # <input id="userId" name="username" type="text">
   # <input id="password" name="password" type="password">
   # <button id="loginBtn" type="submit">ログイン</button>

   # セレクターの特定方法:
   # - ID: By.ID, "userId"
   # - NAME: By.NAME, "username"
   # - CSS: By.CSS_SELECTOR, "#loginBtn"
   # - XPATH: By.XPATH, "//button[@type='submit']"
   ```

3. **実際のページでテスト**
   ```python
   from selenium.webdriver.common.by import By

   # 要素が存在するか確認
   element = rpa.find_element_safe(By.ID, "userId")
   if element:
       print("要素が見つかりました")
   else:
       print("要素が見つかりませんでした - セレクターを確認してください")
   ```

### ステップ2: ログイン機能の実装例

```python
def login(self, username: str, password: str) -> bool:
    """ログイン処理の実装例"""
    try:
        # 1. ログインページに移動
        self.navigate_to(self.LOGIN_URL)
        self.wait_for_page_load()

        # 2. ユーザー名入力（実際のセレクターに更新すること）
        if not self.input_text_safe(By.ID, "userId", username):
            self.logger.error("ユーザー名入力失敗")
            return False

        # 3. パスワード入力
        if not self.input_text_safe(By.ID, "password", password):
            self.logger.error("パスワード入力失敗")
            return False

        # 4. ログインボタンをクリック
        if not self.click_element_safe(By.ID, "loginBtn"):
            self.logger.error("ログインボタンクリック失敗")
            return False

        # 5. ログイン成功を確認（ログイン後のページに特有の要素で確認）
        self.wait_for_page_load()
        profile_element = self.find_element_safe(By.CLASS_NAME, "user-profile", timeout=10)

        if profile_element:
            self.logger.info("ログイン成功")
            self.is_logged_in = True
            return True
        else:
            self.logger.error("ログイン確認失敗")
            return False

    except Exception as e:
        self.handle_error(e, "login")
        return False
```

### ステップ3: レース情報取得の実装例

```python
def get_race_information(self) -> Optional[Dict]:
    """レース情報取得の実装例"""
    try:
        race_info = {
            'venue': None,
            'race_number': None,
            'race_time': None,
            'boats': []
        }

        # 会場名を取得（実際のセレクターに更新すること）
        venue_element = self.find_element_safe(By.CLASS_NAME, "venue-name")
        if venue_element:
            race_info['venue'] = venue_element.text

        # レース番号を取得
        race_num_element = self.find_element_safe(By.CLASS_NAME, "race-number")
        if race_num_element:
            race_info['race_number'] = int(race_num_element.text)

        # レース時刻を取得
        time_element = self.find_element_safe(By.CLASS_NAME, "race-time")
        if time_element:
            race_info['race_time'] = time_element.text

        # 各艇の情報を取得
        boat_elements = self.driver.find_elements(By.CLASS_NAME, "boat-info")
        for boat_elem in boat_elements:
            boat_data = {
                'boat_number': None,
                'player_name': None,
                'motor_number': None,
                # ... その他の情報
            }

            # 艇番
            num_elem = boat_elem.find_element(By.CLASS_NAME, "boat-number")
            if num_elem:
                boat_data['boat_number'] = int(num_elem.text)

            # 選手名
            player_elem = boat_elem.find_element(By.CLASS_NAME, "player-name")
            if player_elem:
                boat_data['player_name'] = player_elem.text

            race_info['boats'].append(boat_data)

        self.logger.info(f"レース情報取得成功: {race_info}")
        return race_info

    except Exception as e:
        self.handle_error(e, "get_race_information")
        return None
```

---

## 🛡️ セキュリティとベストプラクティス

### 1. 認証情報の管理

```python
# ❌ 悪い例: コードに直接記述
rpa.login("my_username", "my_password")

# ✅ 良い例: 環境変数から読み込み
import os
username = os.getenv("BOATRACE_USERNAME")
password = os.getenv("BOATRACE_PASSWORD")
rpa.login(username, password)
```

### 2. レート制限の遵守

```python
# 自動遅延機能を活用
config = RPAConfig(
    min_action_delay=1.0,  # アクション間に1-3秒の遅延
    max_action_delay=3.0,
)
```

### 3. エラーハンドリング

```python
try:
    # RPA処理
    with create_experiment_instance() as rpa:
        # 処理...
        pass
except Exception as e:
    # エラーログ出力
    logging.error(f"RPA処理中にエラー: {e}")
    # スクリーンショットは自動保存される
```

### 4. リソースのクリーンアップ

```python
# コンテキストマネージャーを使用（推奨）
with create_experiment_instance() as rpa:
    # 処理...
    pass
# 自動的に rpa.stop() が呼ばれる

# または明示的にクリーンアップ
rpa = create_experiment_instance()
try:
    rpa.start()
    # 処理...
finally:
    rpa.stop()  # 必ず実行
```

---

## 🔍 デバッグとトラブルシューティング

### 1. ログの確認

```bash
# ログファイルを確認
tail -f web_rpa/logs/rpa.log
```

### 2. スクリーンショットの確認

エラー発生時、自動的にスクリーンショットが保存されます：

```bash
ls -lt web_rpa/screenshots/
```

### 3. ヘッドレスモードを無効化

問題を視覚的に確認するため、ヘッドレスモードを無効化：

```python
config = RPAConfig(headless=False)
rpa = BoatraceRPAExperiment(config)
```

### 4. タイムアウトの調整

要素が見つからない場合、タイムアウトを延長：

```python
config = RPAConfig(
    page_load_timeout=60,    # ページ読み込み: 60秒
    explicit_wait=30,         # 要素待機: 30秒
)
```

### 5. よくある問題

#### 問題: 要素が見つからない

```python
# 解決策1: セレクターを確認
element = rpa.find_element_safe(By.ID, "correct_id")

# 解決策2: 待機時間を増やす
element = rpa.find_element_safe(By.ID, "element_id", timeout=20)

# 解決策3: ページ読み込みを待つ
rpa.wait_for_page_load()
element = rpa.find_element_safe(By.ID, "element_id")
```

#### 問題: クリックできない

```python
# 解決策1: スクロールして表示
element = rpa.driver.find_element(By.ID, "element_id")
rpa.driver.execute_script("arguments[0].scrollIntoView();", element)
rpa._random_delay()
element.click()

# 解決策2: JavaScriptでクリック
element = rpa.driver.find_element(By.ID, "element_id")
rpa.driver.execute_script("arguments[0].click();", element)
```

#### 問題: 認証エラー

```python
# 環境変数が設定されているか確認
import os
print(os.getenv("BOATRACE_USERNAME"))  # None なら未設定

# .envファイルを使用する場合
from dotenv import load_dotenv
load_dotenv()
```

---

## 📝 実装チェックリスト

RPAを実装する前に、以下を確認してください：

- [ ] 利用規約を読み、理解した
- [ ] 自動化が許可されていることを確認した
- [ ] テスト環境が用意されている
- [ ] 認証情報を安全に管理する方法を確立した
- [ ] エラーハンドリングを実装した
- [ ] ログ記録を設定した
- [ ] レート制限を設定した
- [ ] クリーンアップ処理を実装した
- [ ] 法的リスクを理解した
- [ ] セキュリティリスクを理解した

---

## 📚 参考リソース

### Selenium公式ドキュメント
- [Selenium with Python](https://selenium-python.readthedocs.io/)
- [WebDriver API](https://www.selenium.dev/documentation/webdriver/)

### セレクター関連
- [CSS Selector Reference](https://www.w3schools.com/cssref/css_selectors.asp)
- [XPath Tutorial](https://www.w3schools.com/xml/xpath_intro.asp)

### ベストプラクティス
- [Web Scraping Best Practices](https://www.scraperapi.com/blog/web-scraping-best-practices/)
- [Responsible Web Scraping](https://www.scrapingbee.com/blog/web-scraping-best-practices/)

---

## ⚖️ 法的および倫理的考慮事項

### 必ず確認すること

1. **利用規約の遵守**
   - ボートレース公式サイトの利用規約を熟読
   - 自動化が明示的に禁止されていないか確認
   - 禁止されている場合は使用しない

2. **法令遵守**
   - 不正アクセス禁止法の理解
   - ギャンブル関連法規の理解
   - データ保護法の理解

3. **倫理的配慮**
   - サーバーに過度な負荷をかけない
   - 他のユーザーの利用を妨げない
   - 公正性を損なわない

### 責任

- このコードの使用によるすべての結果について、使用者が全責任を負います
- 作成者は一切の責任を負いません
- 自己責任で使用してください

---

## 🤝 サポート

このフレームワークは教育目的のテンプレートです。実装に関する質問は、以下を確認してください：

1. このガイドドキュメント
2. Selenium公式ドキュメント
3. Python公式ドキュメント

---

## 📄 ライセンスと免責事項

このコードは「現状のまま」提供され、いかなる保証もありません。

**使用前に必ず**：
- 利用規約を確認
- 法的アドバイスを求める（必要に応じて）
- 自己責任で使用する

---

**最終更新**: 2024年1月
**バージョン**: 0.1.0
