"""
リアルタイム出走表取得モジュール

指定した会場・レース番号の出走表データをリアルタイムで取得
"""

import logging
from datetime import date, datetime
from typing import Dict, List, Optional, Union
import re

from bs4 import BeautifulSoup

from boatrace_venues import VenueInfo, get_venue_by_id, get_venue_by_name
from scrape_boatrace import BoatRaceScraper

logger = logging.getLogger(__name__)


class LiveRaceDataFetcher:
    """当日のレースデータをリアルタイムで取得するクラス"""

    def __init__(self, venue: Union[int, str, VenueInfo], use_selenium: bool = False):
        """
        初期化

        Args:
            venue: 競艇場ID、名前、またはVenueInfoオブジェクト
            use_selenium: Seleniumを使用するかどうか
        """
        self.scraper = BoatRaceScraper(venue, use_selenium=use_selenium)
        self.venue = self.scraper.venue

    def close(self):
        """リソースのクリーンアップ"""
        self.scraper.close()

    def fetch_race_card(self, race_number: int, target_date: Optional[date] = None) -> Dict:
        """
        出走表（番組表）を取得

        Args:
            race_number: レース番号（1-12）
            target_date: 対象日（Noneの場合は今日）

        Returns:
            出走表データの辞書
        """
        if target_date is None:
            target_date = date.today()

        if not 1 <= race_number <= 12:
            raise ValueError(f"Invalid race number: {race_number}. Must be 1-12.")

        logger.info(f"出走表取得: {self.venue.name} R{race_number} ({target_date})")

        # レース詳細を取得
        race_detail = self.scraper.scrape_race_detail(target_date, race_number)

        # 直前情報を取得
        live_info = self.scraper.scrape_live_info(target_date, race_number)

        # データを統合
        race_card = {
            'venue_id': self.venue.venue_id,
            'venue_name': self.venue.name,
            'date': target_date.isoformat(),
            'race_number': race_number,
            'race_name': race_detail.get('race_name', ''),
            'weather': race_detail.get('weather', ''),
            'boats': self._merge_boat_data(race_detail.get('boats', []), live_info.get('boats', []))
        }

        logger.info(f"出走表取得完了: {len(race_card['boats'])}艇")
        return race_card

    def _merge_boat_data(self, detail_boats: List[Dict], live_boats: List[Dict]) -> List[Dict]:
        """
        レース詳細と直前情報のデータをマージ

        Args:
            detail_boats: レース詳細の艇情報リスト
            live_boats: 直前情報の艇情報リスト

        Returns:
            マージされた艇情報リスト
        """
        merged = []

        # 艇番をキーにしてデータをマージ
        boat_dict = {}

        # レース詳細データを追加
        for boat in detail_boats:
            boat_num = boat.get('boat_number')
            if boat_num:
                boat_dict[boat_num] = boat.copy()

        # 直前情報をマージ
        for boat in live_boats:
            boat_num = boat.get('boat_number')
            if boat_num:
                if boat_num in boat_dict:
                    boat_dict[boat_num].update(boat)
                else:
                    boat_dict[boat_num] = boat.copy()

        # 艇番順にソート
        for boat_num in sorted(boat_dict.keys()):
            merged.append(boat_dict[boat_num])

        return merged

    def fetch_all_races_today(self) -> List[Dict]:
        """
        当日の全レース（1-12R）の出走表を取得

        Returns:
            全レースの出走表リスト
        """
        today = date.today()
        all_races = []

        for race_number in range(1, 13):
            try:
                race_card = self.fetch_race_card(race_number, today)
                all_races.append(race_card)
            except Exception as e:
                logger.error(f"R{race_number}の取得失敗: {e}")
                continue

        return all_races


def fetch_race_card_simple(venue: Union[int, str], race_number: int,
                           target_date: Optional[date] = None,
                           use_selenium: bool = False) -> Dict:
    """
    出走表を取得する簡易関数

    Args:
        venue: 競艇場ID（1-24）または名前
        race_number: レース番号（1-12）
        target_date: 対象日（Noneの場合は今日）
        use_selenium: Seleniumを使用するかどうか

    Returns:
        出走表データ

    Example:
        >>> card = fetch_race_card_simple(18, 1)  # 徳山1R
        >>> card = fetch_race_card_simple("徳山", 1)  # 同上
    """
    fetcher = LiveRaceDataFetcher(venue, use_selenium=use_selenium)
    try:
        return fetcher.fetch_race_card(race_number, target_date)
    finally:
        fetcher.close()


if __name__ == "__main__":
    # テスト用
    import sys
    import json
    from argparse import ArgumentParser

    logging.basicConfig(level=logging.INFO)

    parser = ArgumentParser(description='出走表取得テスト')
    parser.add_argument('venue', help='競艇場名またはID')
    parser.add_argument('race', type=int, help='レース番号（1-12）')
    parser.add_argument('-d', '--date', help='対象日（YYYY-MM-DD）')
    parser.add_argument('-s', '--selenium', action='store_true', help='Seleniumを使用')

    args = parser.parse_args()

    # 対象日
    target_date = None
    if args.date:
        target_date = datetime.strptime(args.date, '%Y-%m-%d').date()

    # 出走表を取得
    try:
        card = fetch_race_card_simple(
            args.venue,
            args.race,
            target_date=target_date,
            use_selenium=args.selenium
        )

        print(json.dumps(card, ensure_ascii=False, indent=2, default=str))

    except Exception as e:
        logger.error(f"エラー: {e}")
        sys.exit(1)
