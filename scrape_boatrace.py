"""
全ボートレース場対応の汎用スクレイピングスクリプト

全24場の競艇場からレースデータをスクレイピング
- レース開催日の1~12Rのデータを取得
- 節間成績の取得
- 直前情報の取得
- データベースへの保存
"""

from datetime import datetime, date
from pathlib import Path
from time import sleep
from typing import Dict, List, Optional, Union
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

from boatrace_venues import VenueInfo, get_venue_by_id, get_venue_by_name, get_all_venues

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BoatRaceScraper:
    """全ボートレース場対応の汎用スクレイパークラス"""

    def __init__(self, venue: Union[int, str, VenueInfo], use_selenium: bool = False, headless: bool = True):
        """
        初期化

        Args:
            venue: 競艇場ID、名前、またはVenueInfoオブジェクト
            use_selenium: Seleniumを使用するかどうか（動的コンテンツの場合はTrue）
            headless: ヘッドレスモードで実行するかどうか
        """
        # 会場情報を取得
        if isinstance(venue, VenueInfo):
            self.venue = venue
        elif isinstance(venue, int):
            self.venue = get_venue_by_id(venue)
            if not self.venue:
                raise ValueError(f"Invalid venue ID: {venue}")
        elif isinstance(venue, str):
            self.venue = get_venue_by_name(venue)
            if not self.venue:
                raise ValueError(f"Invalid venue name: {venue}")
        else:
            raise TypeError(f"Invalid venue type: {type(venue)}")

        self.use_selenium = use_selenium
        self.headless = headless
        self.driver = None
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

        if use_selenium:
            self._init_selenium()

        logger.info(f"スクレイパー初期化: {self.venue.name} ({self.venue.url})")

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

    def _build_urls(self, target_date: date, race_number: Optional[int] = None, page_type: str = "race") -> List[str]:
        """
        URLのパターンリストを構築

        Args:
            target_date: 対象日
            race_number: レース番号（Noneの場合はレース一覧）
            page_type: ページタイプ（"race", "racer", "live"）

        Returns:
            試行するURLのリスト
        """
        date_str = target_date.strftime("%Y%m%d")
        base_url = self.venue.url.rstrip('/')

        urls = []

        if page_type == "race":
            if race_number is None:
                # レース一覧ページ
                urls = [
                    f"{base_url}/race/{date_str}/",
                    f"{base_url}/races/{date_str}/",
                    f"{base_url}/schedule/{date_str}/",
                    f"{base_url}/race?date={date_str}",
                    f"{base_url}/today/",
                    f"{base_url}/",
                ]
            else:
                # レース詳細ページ
                urls = [
                    f"{base_url}/race/{date_str}/{race_number:02d}/",
                    f"{base_url}/race/{date_str}/race{race_number}/",
                    f"{base_url}/races/{date_str}/{race_number}/",
                    f"{base_url}/race?date={date_str}&race={race_number}",
                    f"{base_url}/today/race{race_number}/",
                ]
        elif page_type == "racer":
            # 節間成績ページ
            urls = [
                f"{base_url}/race/{date_str}/racer/",
                f"{base_url}/race/{date_str}/stats/",
                f"{base_url}/races/{date_str}/racer/",
                f"{base_url}/racer/{date_str}/",
                f"{base_url}/racer?date={date_str}",
                f"{base_url}/today/racer/",
            ]
        elif page_type == "live":
            # 直前情報ページ
            if race_number:
                urls = [
                    f"{base_url}/race/{date_str}/{race_number:02d}/live/",
                    f"{base_url}/race/{date_str}/{race_number}/info/",
                    f"{base_url}/races/{date_str}/{race_number}/live/",
                    f"{base_url}/live/{date_str}/{race_number}/",
                    f"{base_url}/live?date={date_str}&race={race_number}",
                    f"{base_url}/today/race{race_number}/live/",
                ]

        return urls

    def scrape_race_list(self, target_date: date) -> List[Dict]:
        """
        指定日のレース一覧を取得

        Args:
            target_date: 対象日

        Returns:
            レース一覧のリスト
        """
        urls = self._build_urls(target_date, page_type="race")

        for url in urls:
            try:
                logger.info(f"レース一覧取得を試行: {url}")
                html = self.get_page_content(url)
                soup = BeautifulSoup(html, 'lxml')

                races = self._parse_race_list(soup, target_date)
                if races:
                    logger.info(f"{len(races)}件のレース情報を取得しました")
                    return races
            except Exception as e:
                logger.debug(f"URL {url} からの取得失敗: {e}")
                continue

        logger.warning(f"{target_date}のレース情報が取得できませんでした（デフォルト1~12Rを返します）")
        # レースが見つからない場合は、1~12Rを仮定
        return [
            {
                'date': target_date,
                'race_number': i,
                'stadium_id': self.venue.venue_id
            }
            for i in range(1, 13)
        ]

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
        race_elements = soup.select('.race-item, .race-list-item, .race, table.race-table tr, div[class*="race"]')

        for idx, element in enumerate(race_elements[:12], 1):  # 最大12R
            try:
                race_info = {
                    'date': target_date,
                    'race_number': idx,
                    'stadium_id': self.venue.venue_id
                }
                races.append(race_info)
            except Exception as e:
                logger.debug(f"レース{idx}のパースエラー: {e}")

        return races if races else None

    def scrape_race_detail(self, target_date: date, race_number: int) -> Dict:
        """
        レース詳細情報を取得

        Args:
            target_date: 対象日
            race_number: レース番号(1~12)

        Returns:
            レース詳細情報の辞書
        """
        urls = self._build_urls(target_date, race_number, page_type="race")

        for url in urls:
            try:
                logger.debug(f"レース詳細取得を試行: {url}")
                html = self.get_page_content(url)
                soup = BeautifulSoup(html, 'lxml')

                detail = self._parse_race_detail(soup, target_date, race_number)
                if detail and detail.get('boats'):  # データが取得できた場合のみ
                    logger.info(f"R{race_number}の詳細情報を取得しました")
                    return detail
            except Exception as e:
                logger.debug(f"URL {url} からの取得失敗: {e}")
                continue

        logger.warning(f"R{race_number}の詳細情報が取得できませんでした")
        return {
            'date': target_date,
            'race_number': race_number,
            'stadium_id': self.venue.venue_id,
            'boats': []
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
            'stadium_id': self.venue.venue_id,
            'boats': []
        }

        # レース名を取得
        race_name_selectors = ['h1', 'h2', '.race-title', '.race-name', 'h2.title', '.ttl1', '.race_title']
        for selector in race_name_selectors:
            race_name_elem = soup.select_one(selector)
            if race_name_elem and race_name_elem.get_text(strip=True):
                detail['race_name'] = race_name_elem.get_text(strip=True)
                break

        # 天候情報を取得
        weather_selectors = ['.weather', '.weather-info', '[class*="weather"]', '.weather_data']
        for selector in weather_selectors:
            weather_elem = soup.select_one(selector)
            if weather_elem and weather_elem.get_text(strip=True):
                detail['weather'] = weather_elem.get_text(strip=True)
                break

        # 出走表から各艇の情報を取得
        boat_selectors = [
            'table.lineup tr',
            '.boat-item',
            '.racer-item',
            'table.table1 tr',
            '.player_data tr',
            'table[class*="lineup"] tr',
            'table[class*="race"] tbody tr'
        ]

        for selector in boat_selectors:
            boat_rows = soup.select(selector)
            if boat_rows and len(boat_rows) > 1:  # ヘッダー行を除く
                for boat_row in boat_rows[1:7]:  # 最大6艇
                    try:
                        boat_info = self._parse_boat_info(boat_row)
                        if boat_info:
                            detail['boats'].append(boat_info)
                    except Exception as e:
                        logger.debug(f"艇情報のパースエラー: {e}")
                if detail['boats']:
                    break

        return detail

    def _parse_boat_info(self, element) -> Optional[Dict]:
        """
        艇情報をパース

        Args:
            element: BeautifulSoupの要素

        Returns:
            艇情報の辞書
        """
        try:
            # tdタグからデータを抽出
            cells = element.select('td')
            if not cells or len(cells) < 3:
                return None

            boat_info = {}

            # 一般的な出走表の構造を想定
            # [艇番, 選手名, 級別, 全国勝率, 当地勝率, モーター, ボート, ...]
            # サイト構造に応じて調整が必要

            # 艇番
            boat_num_elem = cells[0] if len(cells) > 0 else None
            if boat_num_elem:
                boat_info['boat_number'] = boat_num_elem.get_text(strip=True)

            # 選手名
            player_elem = cells[1] if len(cells) > 1 else None
            if player_elem:
                boat_info['player_name'] = player_elem.get_text(strip=True)

            return boat_info if boat_info else None

        except Exception as e:
            logger.debug(f"艇情報パースエラー: {e}")
            return None

    def scrape_session_stats(self, target_date: date) -> List[Dict]:
        """
        節間成績を取得

        Args:
            target_date: 対象日

        Returns:
            節間成績のリスト
        """
        urls = self._build_urls(target_date, page_type="racer")

        for url in urls:
            try:
                logger.info(f"節間成績取得を試行: {url}")
                html = self.get_page_content(url)
                soup = BeautifulSoup(html, 'lxml')

                stats = self._parse_session_stats(soup, target_date)
                if stats:
                    logger.info(f"{len(stats)}件の節間成績を取得しました")
                    return stats
            except Exception as e:
                logger.debug(f"URL {url} からの取得失敗: {e}")
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
        stat_selectors = [
            'table.stats tr',
            '.stats-item',
            '.racer-stats',
            'table.table1 tr',
            'table[class*="stats"] tr'
        ]

        for selector in stat_selectors:
            stat_rows = soup.select(selector)
            if stat_rows and len(stat_rows) > 1:  # ヘッダー行を除く
                for row in stat_rows[1:]:
                    try:
                        stat_info = {
                            'date': target_date,
                            'stadium_id': self.venue.venue_id
                        }
                        # サイト構造に応じて実装
                        stats.append(stat_info)
                    except Exception as e:
                        logger.debug(f"節間成績のパースエラー: {e}")
                if stats:
                    break

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
        urls = self._build_urls(target_date, race_number, page_type="live")

        for url in urls:
            try:
                logger.debug(f"直前情報取得を試行: {url}")
                html = self.get_page_content(url)
                soup = BeautifulSoup(html, 'lxml')

                live_info = self._parse_live_info(soup, target_date, race_number)
                if live_info and live_info.get('boats'):  # データが取得できた場合のみ
                    logger.info(f"R{race_number}の直前情報を取得しました")
                    return live_info
            except Exception as e:
                logger.debug(f"URL {url} からの取得失敗: {e}")
                continue

        logger.warning(f"R{race_number}の直前情報が取得できませんでした")
        return {
            'date': target_date,
            'race_number': race_number,
            'stadium_id': self.venue.venue_id,
            'boats': []
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
            'stadium_id': self.venue.venue_id,
            'boats': []
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
        logger.info(f"=== {self.venue.name} {target_date} の全レースデータ取得開始 ===")

        all_data = {
            'date': target_date.isoformat(),
            'stadium_id': self.venue.venue_id,
            'stadium_name': self.venue.name,
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
                logger.info(f"--- {self.venue.name} R{race_number} データ取得中 ---")

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
                logger.error(f"{self.venue.name} R{race_number} データ取得エラー: {e}")
                all_data['races'].append({
                    'date': target_date,
                    'race_number': race_number,
                    'error': str(e)
                })

        logger.info(f"=== {self.venue.name} データ取得完了 ===")

        # JSONファイルに保存
        if save_dir:
            save_dir = Path(save_dir)
            save_dir.mkdir(parents=True, exist_ok=True)

            filename = f"{self.venue.name_en}_{target_date.strftime('%Y%m%d')}.json"
            filepath = save_dir / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(all_data, f, ensure_ascii=False, indent=2, default=str)

            logger.info(f"データを保存しました: {filepath}")

        return all_data


def main():
    """メイン処理"""
    import sys
    import argparse

    parser = argparse.ArgumentParser(description='ボートレース場のレースデータをスクレイピング')
    parser.add_argument('venue', nargs='?', help='競艇場名またはID（指定しない場合は全会場）')
    parser.add_argument('-d', '--date', help='対象日（YYYY-MM-DD形式、デフォルトは今日）')
    parser.add_argument('-s', '--selenium', action='store_true', help='Seleniumを使用')
    parser.add_argument('--all', action='store_true', help='全会場を処理')

    args = parser.parse_args()

    # 対象日を決定
    if args.date:
        try:
            target_date = datetime.strptime(args.date, '%Y-%m-%d').date()
        except ValueError:
            print("日付形式が正しくありません。YYYY-MM-DD形式で指定してください。")
            return
    else:
        target_date = date.today()

    # 対象会場を決定
    venues = []
    if args.all:
        venues = get_all_venues()
    elif args.venue:
        # IDまたは名前で指定
        try:
            venue_id = int(args.venue)
            venue = get_venue_by_id(venue_id)
        except ValueError:
            venue = get_venue_by_name(args.venue)

        if not venue:
            print(f"会場が見つかりません: {args.venue}")
            return
        venues = [venue]
    else:
        print("会場を指定してください。--all オプションで全会場を処理できます。")
        print("\n利用可能な会場:")
        for v in get_all_venues():
            print(f"  {v.venue_id:2d}. {v.name}")
        return

    # データ保存ディレクトリ
    save_dir = Path("./data/boatrace_scraped")

    # 各会場のデータを取得
    for venue in venues:
        scraper = BoatRaceScraper(venue, use_selenium=args.selenium)
        try:
            data = scraper.scrape_all_races(target_date, save_dir=save_dir)
            print(f"\n{venue.name} - 取得結果:")
            print(f"  レース数: {len(data['races'])}")
            print(f"  節間成績: {len(data['session_stats'])}件")
        except Exception as e:
            logger.error(f"{venue.name} のスクレイピング失敗: {e}")
        finally:
            scraper.close()

        # 会場間で待機
        if len(venues) > 1:
            sleep(5)


if __name__ == "__main__":
    main()
