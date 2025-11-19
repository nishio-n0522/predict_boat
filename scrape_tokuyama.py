"""
ボートレース徳山の公式サイトからレースデータをスクレイピングするスクリプト

主な機能:
1. レース開催日の1~12Rのデータを取得
2. 節間成績の取得
3. 直前情報の取得
4. データベースへの保存
"""

from datetime import datetime, date
from pathlib import Path
from time import sleep
from typing import Dict, List, Optional
import json
import logging

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TokuyamaRaceScraper:
    """ボートレース徳山のレースデータをスクレイピングするクラス"""

    BASE_URL = "https://www.boatrace-tokuyama.jp"
    STADIUM_ID = 18  # 徳山競艇場のID

    def __init__(self, use_selenium: bool = False, headless: bool = True):
        """
        初期化

        Args:
            use_selenium: Seleniumを使用するかどうか（動的コンテンツの場合はTrue）
            headless: ヘッドレスモードで実行するかどうか
        """
        self.use_selenium = use_selenium
        self.headless = headless
        self.driver = None
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

        if use_selenium:
            self._init_selenium()

    def _init_selenium(self):
        """Seleniumドライバーの初期化"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        logger.info("Seleniumドライバーを初期化しました")

    def close(self):
        """リソースのクリーンアップ"""
        if self.driver:
            self.driver.quit()
            logger.info("Seleniumドライバーを終了しました")

    def get_page_content(self, url: str, wait_selector: Optional[str] = None) -> str:
        """
        ページコンテンツを取得

        Args:
            url: 取得するURL
            wait_selector: Selenium使用時に待機するCSSセレクタ

        Returns:
            HTMLコンテンツ
        """
        try:
            if self.use_selenium:
                self.driver.get(url)
                if wait_selector:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, wait_selector))
                    )
                sleep(1)  # ページの完全な読み込みを待つ
                return self.driver.page_source
            else:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                response.encoding = response.apparent_encoding  # 文字化け対策
                return response.text
        except Exception as e:
            logger.error(f"ページ取得エラー: {url} - {e}")
            raise

    def scrape_race_list(self, target_date: date) -> List[Dict]:
        """
        指定日のレース一覧を取得

        Args:
            target_date: 対象日

        Returns:
            レース一覧のリスト
        """
        date_str = target_date.strftime("%Y%m%d")
        # ボートレース場の公式サイトの一般的なURL構造に対応
        # 実際のサイト構造に応じて調整が必要
        possible_urls = [
            f"{self.BASE_URL}/race/{date_str}/",
            f"{self.BASE_URL}/races/{date_str}/",
            f"{self.BASE_URL}/schedule/{date_str}/",
            f"{self.BASE_URL}/race?date={date_str}",
        ]

        for url in possible_urls:
            try:
                logger.info(f"レース一覧取得を試行: {url}")
                html = self.get_page_content(url)
                soup = BeautifulSoup(html, 'lxml')

                # レース情報を抽出（サイト構造に応じて調整）
                races = self._parse_race_list(soup, target_date)
                if races:
                    logger.info(f"{len(races)}件のレース情報を取得しました")
                    return races
            except Exception as e:
                logger.warning(f"URL {url} からの取得失敗: {e}")
                continue

        logger.warning(f"{target_date}のレース情報が取得できませんでした")
        return []

    def _parse_race_list(self, soup: BeautifulSoup, target_date: date) -> List[Dict]:
        """
        レース一覧ページをパース

        Args:
            soup: BeautifulSoupオブジェクト
            target_date: 対象日

        Returns:
            レース情報のリスト
        """
        races = []

        # 一般的なレース一覧の構造を想定してパース
        # 実際のサイト構造に応じて調整が必要
        race_elements = soup.select('.race-item, .race-list-item, .race')

        if not race_elements:
            # 別のセレクタを試す
            race_elements = soup.select('table.race-table tr, div[class*="race"]')

        for idx, element in enumerate(race_elements, 1):
            try:
                race_info = {
                    'date': target_date,
                    'race_number': idx,
                    'stadium_id': self.STADIUM_ID
                }
                races.append(race_info)
            except Exception as e:
                logger.warning(f"レース{idx}のパースエラー: {e}")

        # レースが見つからない場合は、1~12Rを仮定
        if not races:
            races = [
                {
                    'date': target_date,
                    'race_number': i,
                    'stadium_id': self.STADIUM_ID
                }
                for i in range(1, 13)
            ]

        return races

    def scrape_race_detail(self, target_date: date, race_number: int) -> Dict:
        """
        レース詳細情報を取得

        Args:
            target_date: 対象日
            race_number: レース番号(1~12)

        Returns:
            レース詳細情報の辞書
        """
        date_str = target_date.strftime("%Y%m%d")

        # レース詳細ページの一般的なURL構造
        possible_urls = [
            f"{self.BASE_URL}/race/{date_str}/{race_number:02d}/",
            f"{self.BASE_URL}/race/{date_str}/race{race_number}/",
            f"{self.BASE_URL}/races/{date_str}/{race_number}/",
            f"{self.BASE_URL}/race?date={date_str}&race={race_number}",
        ]

        for url in possible_urls:
            try:
                logger.info(f"レース詳細取得を試行: {url}")
                html = self.get_page_content(url)
                soup = BeautifulSoup(html, 'lxml')

                detail = self._parse_race_detail(soup, target_date, race_number)
                if detail:
                    logger.info(f"R{race_number}の詳細情報を取得しました")
                    return detail
            except Exception as e:
                logger.warning(f"URL {url} からの取得失敗: {e}")
                continue

        logger.warning(f"R{race_number}の詳細情報が取得できませんでした")
        return {
            'date': target_date,
            'race_number': race_number,
            'stadium_id': self.STADIUM_ID
        }

    def _parse_race_detail(self, soup: BeautifulSoup, target_date: date, race_number: int) -> Dict:
        """
        レース詳細ページをパース

        Args:
            soup: BeautifulSoupオブジェクト
            target_date: 対象日
            race_number: レース番号

        Returns:
            レース詳細情報
        """
        detail = {
            'date': target_date,
            'race_number': race_number,
            'stadium_id': self.STADIUM_ID,
            'boats': []
        }

        # レース名を取得
        race_name_elem = soup.select_one('h1, .race-title, .race-name, h2.title')
        if race_name_elem:
            detail['race_name'] = race_name_elem.get_text(strip=True)

        # 天候情報を取得
        weather_elem = soup.select_one('.weather, .weather-info, [class*="weather"]')
        if weather_elem:
            detail['weather'] = weather_elem.get_text(strip=True)

        # 出走表から各艇の情報を取得
        boat_rows = soup.select('table.lineup tr, .boat-item, .racer-item')
        for boat_row in boat_rows:
            try:
                boat_info = self._parse_boat_info(boat_row)
                if boat_info:
                    detail['boats'].append(boat_info)
            except Exception as e:
                logger.warning(f"艇情報のパースエラー: {e}")

        return detail

    def _parse_boat_info(self, element) -> Optional[Dict]:
        """
        艇情報をパース

        Args:
            element: BeautifulSoupの要素

        Returns:
            艇情報の辞書
        """
        # サイト構造に応じて実装
        # ここではプレースホルダー
        return None

    def scrape_session_stats(self, target_date: date) -> List[Dict]:
        """
        節間成績を取得

        Args:
            target_date: 対象日

        Returns:
            節間成績のリスト
        """
        date_str = target_date.strftime("%Y%m%d")

        possible_urls = [
            f"{self.BASE_URL}/race/{date_str}/racer/",
            f"{self.BASE_URL}/race/{date_str}/stats/",
            f"{self.BASE_URL}/races/{date_str}/racer/",
            f"{self.BASE_URL}/racer/{date_str}/",
        ]

        for url in possible_urls:
            try:
                logger.info(f"節間成績取得を試行: {url}")
                html = self.get_page_content(url)
                soup = BeautifulSoup(html, 'lxml')

                stats = self._parse_session_stats(soup, target_date)
                if stats:
                    logger.info(f"{len(stats)}件の節間成績を取得しました")
                    return stats
            except Exception as e:
                logger.warning(f"URL {url} からの取得失敗: {e}")
                continue

        logger.warning(f"{target_date}の節間成績が取得できませんでした")
        return []

    def _parse_session_stats(self, soup: BeautifulSoup, target_date: date) -> List[Dict]:
        """
        節間成績ページをパース

        Args:
            soup: BeautifulSoupオブジェクト
            target_date: 対象日

        Returns:
            節間成績のリスト
        """
        stats = []

        # 節間成績テーブルを取得
        stat_rows = soup.select('table.stats tr, .stats-item, .racer-stats')

        for row in stat_rows:
            try:
                stat_info = {
                    'date': target_date,
                    'stadium_id': self.STADIUM_ID
                }
                # 選手番号、名前、成績などを抽出
                # サイト構造に応じて実装
                stats.append(stat_info)
            except Exception as e:
                logger.warning(f"節間成績のパースエラー: {e}")

        return stats

    def scrape_live_info(self, target_date: date, race_number: int) -> Dict:
        """
        直前情報を取得

        Args:
            target_date: 対象日
            race_number: レース番号

        Returns:
            直前情報の辞書
        """
        date_str = target_date.strftime("%Y%m%d")

        possible_urls = [
            f"{self.BASE_URL}/race/{date_str}/{race_number:02d}/live/",
            f"{self.BASE_URL}/race/{date_str}/{race_number}/info/",
            f"{self.BASE_URL}/races/{date_str}/{race_number}/live/",
            f"{self.BASE_URL}/live/{date_str}/{race_number}/",
        ]

        for url in possible_urls:
            try:
                logger.info(f"直前情報取得を試行: {url}")
                html = self.get_page_content(url)
                soup = BeautifulSoup(html, 'lxml')

                live_info = self._parse_live_info(soup, target_date, race_number)
                if live_info:
                    logger.info(f"R{race_number}の直前情報を取得しました")
                    return live_info
            except Exception as e:
                logger.warning(f"URL {url} からの取得失敗: {e}")
                continue

        logger.warning(f"R{race_number}の直前情報が取得できませんでした")
        return {
            'date': target_date,
            'race_number': race_number,
            'stadium_id': self.STADIUM_ID
        }

    def _parse_live_info(self, soup: BeautifulSoup, target_date: date, race_number: int) -> Dict:
        """
        直前情報ページをパース

        Args:
            soup: BeautifulSoupオブジェクト
            target_date: 対象日
            race_number: レース番号

        Returns:
            直前情報
        """
        info = {
            'date': target_date,
            'race_number': race_number,
            'stadium_id': self.STADIUM_ID
        }

        # 展示タイム、スタート展示などを取得
        # サイト構造に応じて実装

        return info

    def scrape_all_races(self, target_date: date, save_dir: Optional[Path] = None) -> Dict:
        """
        指定日の全レース(1~12R)のデータを取得

        Args:
            target_date: 対象日
            save_dir: 保存先ディレクトリ（Noneの場合は保存しない）

        Returns:
            全レースのデータを含む辞書
        """
        logger.info(f"=== {target_date} の全レースデータ取得開始 ===")

        all_data = {
            'date': target_date.isoformat(),
            'stadium_id': self.STADIUM_ID,
            'stadium_name': '徳山',
            'races': [],
            'session_stats': []
        }

        # 節間成績を取得
        try:
            session_stats = self.scrape_session_stats(target_date)
            all_data['session_stats'] = session_stats
        except Exception as e:
            logger.error(f"節間成績取得エラー: {e}")

        # 各レースの情報を取得
        for race_number in range(1, 13):
            try:
                logger.info(f"--- R{race_number} データ取得中 ---")

                # レース詳細
                race_detail = self.scrape_race_detail(target_date, race_number)

                # 直前情報
                live_info = self.scrape_live_info(target_date, race_number)

                # データを統合
                race_data = {
                    **race_detail,
                    'live_info': live_info
                }

                all_data['races'].append(race_data)

                # サーバーに負荷をかけないよう待機
                sleep(2)

            except Exception as e:
                logger.error(f"R{race_number} データ取得エラー: {e}")
                # エラーがあっても続行
                all_data['races'].append({
                    'date': target_date,
                    'race_number': race_number,
                    'error': str(e)
                })

        logger.info(f"=== データ取得完了 ===")

        # JSONファイルに保存
        if save_dir:
            save_dir = Path(save_dir)
            save_dir.mkdir(parents=True, exist_ok=True)

            filename = f"tokuyama_{target_date.strftime('%Y%m%d')}.json"
            filepath = save_dir / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(all_data, f, ensure_ascii=False, indent=2, default=str)

            logger.info(f"データを保存しました: {filepath}")

        return all_data


def main():
    """メイン処理"""
    # 今日の日付を取得
    target_date = date.today()

    # 引数で日付を指定可能にする場合
    import sys
    if len(sys.argv) > 1:
        try:
            target_date = datetime.strptime(sys.argv[1], '%Y-%m-%d').date()
        except ValueError:
            print("日付形式が正しくありません。YYYY-MM-DD形式で指定してください。")
            return

    # スクレイパーを初期化
    # 動的コンテンツがある場合はuse_selenium=Trueに変更
    scraper = TokuyamaRaceScraper(use_selenium=False)

    try:
        # データ保存ディレクトリ
        save_dir = Path("./data/tokuyama_scraped")

        # 全レースデータを取得
        data = scraper.scrape_all_races(target_date, save_dir=save_dir)

        print(f"\n=== 取得結果 ===")
        print(f"対象日: {target_date}")
        print(f"レース数: {len(data['races'])}")
        print(f"節間成績: {len(data['session_stats'])}件")

    finally:
        # リソースのクリーンアップ
        scraper.close()


if __name__ == "__main__":
    main()
