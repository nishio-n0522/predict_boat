"""
全ボートレース場のデータを一括でスクレイピングするスクリプト

レース開催日に、開催されている全会場のデータを自動的に取得
"""

import argparse
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime
from pathlib import Path
from time import sleep
from typing import Dict, List, Set

import requests
from bs4 import BeautifulSoup

from boatrace_venues import get_all_venues, VenueInfo
from scrape_boatrace import BoatRaceScraper

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AllVenuesScraper:
    """全会場のスクレイピングを管理するクラス"""

    # ボートレース公式の開催情報API（存在する場合）
    OFFICIAL_SCHEDULE_URL = "https://www.boatrace.jp/owpc/pc/race/index"

    def __init__(self, use_selenium: bool = False, max_workers: int = 3):
        """
        初期化

        Args:
            use_selenium: Seleniumを使用するかどうか
            max_workers: 並列処理の最大ワーカー数
        """
        self.use_selenium = use_selenium
        self.max_workers = max_workers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def get_racing_venues(self, target_date: date) -> Set[int]:
        """
        指定日に開催されている会場IDを取得

        Args:
            target_date: 対象日

        Returns:
            開催中の会場IDのセット
        """
        # ボートレース公式サイトから開催情報を取得
        # 実装例：公式サイトのスケジュールページをパース
        # ここでは簡易的に全会場を返す

        logger.info(f"{target_date}の開催会場を取得中...")

        try:
            # 公式サイトのスケジュールページから取得を試みる
            date_str = target_date.strftime('%Y%m%d')
            schedule_urls = [
                f"https://www.boatrace.jp/owpc/pc/race/index?hd={date_str}",
                f"https://www.boatrace.jp/owpc/pc/race/raceindex?hd={date_str}",
            ]

            for url in schedule_urls:
                try:
                    response = self.session.get(url, timeout=10)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.content, 'lxml')

                    # 開催場を示す要素を探す
                    # サイト構造に応じて調整が必要
                    venue_elements = soup.select('[data-jcd], .is-active[class*="jcd"]')
                    if venue_elements:
                        venue_ids = set()
                        for elem in venue_elements:
                            jcd = elem.get('data-jcd') or elem.get('class', [''])[0].replace('jcd', '')
                            try:
                                venue_ids.add(int(jcd))
                            except (ValueError, TypeError):
                                pass
                        if venue_ids:
                            logger.info(f"開催会場: {sorted(venue_ids)}")
                            return venue_ids
                except Exception as e:
                    logger.debug(f"URL {url} からの取得失敗: {e}")
                    continue

        except Exception as e:
            logger.warning(f"開催情報の取得失敗: {e}")

        # 取得できない場合は全会場を対象とする
        logger.info("開催情報を取得できませんでした。全会場を対象とします。")
        all_venue_ids = {v.venue_id for v in get_all_venues()}
        return all_venue_ids

    def scrape_venue(self, venue: VenueInfo, target_date: date, save_dir: Path) -> Dict:
        """
        単一会場のスクレイピングを実行

        Args:
            venue: 会場情報
            target_date: 対象日
            save_dir: 保存先ディレクトリ

        Returns:
            スクレイピング結果
        """
        result = {
            'venue_id': venue.venue_id,
            'venue_name': venue.name,
            'success': False,
            'error': None,
            'race_count': 0,
            'stats_count': 0
        }

        scraper = None
        try:
            logger.info(f"[{venue.name}] スクレイピング開始")
            scraper = BoatRaceScraper(venue, use_selenium=self.use_selenium)

            data = scraper.scrape_all_races(target_date, save_dir=save_dir)

            result['success'] = True
            result['race_count'] = len(data.get('races', []))
            result['stats_count'] = len(data.get('session_stats', []))

            logger.info(f"[{venue.name}] スクレイピング完了 - レース:{result['race_count']}, 成績:{result['stats_count']}")

        except Exception as e:
            result['error'] = str(e)
            logger.error(f"[{venue.name}] スクレイピング失敗: {e}")

        finally:
            if scraper:
                scraper.close()

        return result

    def scrape_all_venues(self, target_date: date, save_dir: Path,
                         venue_ids: Set[int] = None, parallel: bool = False) -> List[Dict]:
        """
        複数会場のスクレイピングを実行

        Args:
            target_date: 対象日
            save_dir: 保存先ディレクトリ
            venue_ids: 対象会場IDのセット（Noneの場合は開催中の全会場）
            parallel: 並列処理を行うかどうか

        Returns:
            各会場のスクレイピング結果のリスト
        """
        # 対象会場を決定
        if venue_ids is None:
            venue_ids = self.get_racing_venues(target_date)

        venues = [v for v in get_all_venues() if v.venue_id in venue_ids]

        if not venues:
            logger.warning("対象会場が見つかりません")
            return []

        logger.info(f"対象会場数: {len(venues)}")

        # 保存ディレクトリを作成
        save_dir = Path(save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)

        results = []

        if parallel and len(venues) > 1:
            # 並列処理
            logger.info(f"並列処理開始（最大{self.max_workers}ワーカー）")
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_venue = {
                    executor.submit(self.scrape_venue, venue, target_date, save_dir): venue
                    for venue in venues
                }

                for future in as_completed(future_to_venue):
                    venue = future_to_venue[future]
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        logger.error(f"[{venue.name}] 予期しないエラー: {e}")
                        results.append({
                            'venue_id': venue.venue_id,
                            'venue_name': venue.name,
                            'success': False,
                            'error': str(e)
                        })
        else:
            # 順次処理
            logger.info("順次処理開始")
            for venue in venues:
                result = self.scrape_venue(venue, target_date, save_dir)
                results.append(result)

                # 会場間で待機（サーバー負荷軽減）
                if len(venues) > 1:
                    sleep(3)

        return results

    def save_summary(self, results: List[Dict], target_date: date, save_dir: Path):
        """
        スクレイピング結果のサマリーを保存

        Args:
            results: スクレイピング結果のリスト
            target_date: 対象日
            save_dir: 保存先ディレクトリ
        """
        summary = {
            'date': target_date.isoformat(),
            'total_venues': len(results),
            'successful': sum(1 for r in results if r['success']),
            'failed': sum(1 for r in results if not r['success']),
            'results': results
        }

        summary_file = save_dir / f"summary_{target_date.strftime('%Y%m%d')}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        logger.info(f"サマリーを保存: {summary_file}")

        # コンソールにサマリーを表示
        print("\n" + "=" * 60)
        print(f"スクレイピング結果サマリー - {target_date}")
        print("=" * 60)
        print(f"対象会場数: {summary['total_venues']}")
        print(f"成功: {summary['successful']}")
        print(f"失敗: {summary['failed']}")
        print("\n各会場の結果:")
        for r in results:
            status = "✓" if r['success'] else "✗"
            print(f"  {status} {r['venue_name']:8s} - レース:{r.get('race_count', 0):2d}, 成績:{r.get('stats_count', 0):3d}")
            if r.get('error'):
                print(f"      エラー: {r['error']}")
        print("=" * 60)


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(description='全ボートレース場のデータを一括スクレイピング')
    parser.add_argument('-d', '--date', help='対象日（YYYY-MM-DD形式、デフォルトは今日）')
    parser.add_argument('-v', '--venues', help='対象会場ID（カンマ区切り、例: 1,2,18）')
    parser.add_argument('-s', '--selenium', action='store_true', help='Seleniumを使用')
    parser.add_argument('-p', '--parallel', action='store_true', help='並列処理を有効化')
    parser.add_argument('-w', '--workers', type=int, default=3, help='並列処理のワーカー数（デフォルト:3）')
    parser.add_argument('-o', '--output', default='./data/boatrace_scraped', help='保存先ディレクトリ')

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
    venue_ids = None
    if args.venues:
        try:
            venue_ids = {int(v.strip()) for v in args.venues.split(',')}
        except ValueError:
            print("会場IDの形式が正しくありません。")
            return

    # スクレイパーを実行
    scraper = AllVenuesScraper(use_selenium=args.selenium, max_workers=args.workers)

    save_dir = Path(args.output)
    results = scraper.scrape_all_venues(
        target_date=target_date,
        save_dir=save_dir,
        venue_ids=venue_ids,
        parallel=args.parallel
    )

    # サマリーを保存
    scraper.save_summary(results, target_date, save_dir)


if __name__ == "__main__":
    main()
