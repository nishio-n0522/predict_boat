"""
スクレイピングしたデータをデータベースに保存するモジュール
"""

import json
import logging
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

from db.db_setting import session_factory
from db.stadium import get_or_create as get_or_create_stadium
from db.player import get_or_create as get_or_create_player
from db.session_stats import get_or_create as get_or_create_session_stats
from db.live_info import get_or_create as get_or_create_live_info

logger = logging.getLogger(__name__)


class ScrapedDataSaver:
    """スクレイピングしたデータをデータベースに保存するクラス"""

    def __init__(self):
        """初期化"""
        self.session = session_factory()

    def save_session_stats(self, stats_data: List[Dict]) -> int:
        """
        節間成績をデータベースに保存

        Args:
            stats_data: 節間成績データのリスト

        Returns:
            保存したレコード数
        """
        saved_count = 0

        for stat in stats_data:
            try:
                # 競艇場を取得または作成
                stadium, _ = get_or_create_stadium(
                    self.session,
                    stadium_id=stat.get('stadium_id')
                )

                # 選手を取得または作成
                player, _ = get_or_create_player(
                    self.session,
                    player_id=stat.get('player_id')
                )

                # 節間成績を保存
                session_stat, created = get_or_create_session_stats(
                    self.session,
                    stadium=stadium,
                    date=stat.get('date'),
                    player=player,
                    session_1st_rate=stat.get('session_1st_rate'),
                    session_2nd_rate=stat.get('session_2nd_rate'),
                    session_3rd_rate=stat.get('session_3rd_rate'),
                    session_win_rate=stat.get('session_win_rate'),
                    session_race_count=stat.get('session_race_count'),
                    session_1st_count=stat.get('session_1st_count'),
                    session_2nd_count=stat.get('session_2nd_count'),
                    session_3rd_count=stat.get('session_3rd_count')
                )

                if created:
                    saved_count += 1
                    logger.info(f"節間成績を保存: 選手ID={stat.get('player_id')}")

            except Exception as e:
                logger.error(f"節間成績保存エラー: {e}, データ: {stat}")
                continue

        logger.info(f"節間成績を{saved_count}件保存しました")
        return saved_count

    def save_live_info(self, live_data: List[Dict]) -> int:
        """
        直前情報をデータベースに保存

        Args:
            live_data: 直前情報データのリスト

        Returns:
            保存したレコード数
        """
        saved_count = 0

        for info in live_data:
            try:
                # 競艇場を取得または作成
                stadium, _ = get_or_create_stadium(
                    self.session,
                    stadium_id=info.get('stadium_id')
                )

                # 選手を取得または作成
                player, _ = get_or_create_player(
                    self.session,
                    player_id=info.get('player_id')
                )

                # 直前情報を保存
                live_info, created = get_or_create_live_info(
                    self.session,
                    stadium=stadium,
                    date=info.get('date'),
                    race_index=info.get('race_number'),
                    boat_number=info.get('boat_number'),
                    player=player,
                    exhibition_time=info.get('exhibition_time'),
                    tilt=info.get('tilt'),
                    approach_course=info.get('approach_course'),
                    start_exhibition=info.get('start_exhibition'),
                    motor_adjustment=info.get('motor_adjustment'),
                    body_weight=info.get('body_weight'),
                    adjusted_weight=info.get('adjusted_weight'),
                    win_odds=info.get('win_odds'),
                    quinella_odds=info.get('quinella_odds')
                )

                if created:
                    saved_count += 1
                    logger.info(f"直前情報を保存: R{info.get('race_number')}-{info.get('boat_number')}号艇")

            except Exception as e:
                logger.error(f"直前情報保存エラー: {e}, データ: {info}")
                continue

        logger.info(f"直前情報を{saved_count}件保存しました")
        return saved_count

    def save_from_json(self, json_file: Path) -> Dict[str, int]:
        """
        JSONファイルからデータを読み込んでデータベースに保存

        Args:
            json_file: JSONファイルのパス

        Returns:
            保存したレコード数の辞書
        """
        logger.info(f"JSONファイルを読み込み: {json_file}")

        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        result = {
            'session_stats': 0,
            'live_info': 0
        }

        # 節間成績を保存
        if 'session_stats' in data and data['session_stats']:
            result['session_stats'] = self.save_session_stats(data['session_stats'])

        # 各レースの直前情報を保存
        if 'races' in data:
            live_info_list = []
            for race in data['races']:
                if 'live_info' in race and race['live_info']:
                    # live_infoがネストされている場合
                    if isinstance(race['live_info'], dict):
                        live_info_list.append(race['live_info'])
                    # boats情報から直前情報を抽出
                if 'boats' in race:
                    for boat in race['boats']:
                        if boat:
                            live_info_list.append(boat)

            if live_info_list:
                result['live_info'] = self.save_live_info(live_info_list)

        logger.info(f"保存完了: {result}")
        return result

    def close(self):
        """リソースのクリーンアップ"""
        if self.session:
            self.session.close()


def main():
    """メイン処理"""
    import sys

    if len(sys.argv) < 2:
        print("使用方法: python save_scraped_data.py <json_file_path>")
        return

    json_file = Path(sys.argv[1])

    if not json_file.exists():
        print(f"ファイルが見つかりません: {json_file}")
        return

    saver = ScrapedDataSaver()
    try:
        result = saver.save_from_json(json_file)
        print(f"\n保存結果:")
        print(f"  節間成績: {result['session_stats']}件")
        print(f"  直前情報: {result['live_info']}件")
    finally:
        saver.close()


if __name__ == "__main__":
    main()
