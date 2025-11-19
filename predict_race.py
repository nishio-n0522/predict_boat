"""
ボートレース予測アプリケーション

会場とレース番号を指定して、レース結果を予測
"""

import argparse
import json
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Dict, Optional

from fetch_live_data import LiveRaceDataFetcher
from prediction.data_preprocessor import RaceDataPreprocessor
from prediction.inference_engine import PredictionEngine
from boatrace_venues import get_all_venues

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RacePredictor:
    """レース予測クラス"""

    def __init__(self, model_path: Optional[Path] = None, use_selenium: bool = False):
        """
        初期化

        Args:
            model_path: 学習済みモデルのパス
            use_selenium: Seleniumを使用するかどうか
        """
        self.preprocessor = RaceDataPreprocessor()
        self.engine = PredictionEngine(model_path)
        self.use_selenium = use_selenium

    def close(self):
        """リソースのクリーンアップ"""
        if self.preprocessor:
            self.preprocessor.close()

    def predict_race(self, venue, race_number: int, target_date: Optional[date] = None) -> Dict:
        """
        レース予測を実行

        Args:
            venue: 競艇場ID（1-24）または名前
            race_number: レース番号（1-12）
            target_date: 対象日（Noneの場合は今日）

        Returns:
            予測結果の辞書
        """
        if target_date is None:
            target_date = date.today()

        logger.info(f"予測開始: {venue} R{race_number} ({target_date})")

        # 出走表を取得
        fetcher = LiveRaceDataFetcher(venue, use_selenium=self.use_selenium)
        try:
            race_card = fetcher.fetch_race_card(race_number, target_date)
        finally:
            fetcher.close()

        # 前処理
        features_df = self.preprocessor.preprocess_race_card(race_card)

        if features_df.empty:
            logger.error("特徴量の抽出に失敗しました")
            return {
                'error': '特徴量の抽出に失敗しました',
                'venue': venue,
                'race_number': race_number,
                'date': target_date.isoformat()
            }

        # 予測
        prediction_result = self.engine.predict(features_df)

        # 2連単・3連単予測を追加
        if prediction_result.get('predictions'):
            prediction_result['quinella_top5'] = self.engine.predict_quinella(
                prediction_result['predictions']
            )[:5]
            prediction_result['trifecta_top5'] = self.engine.predict_trifecta(
                prediction_result['predictions']
            )[:5]

        # メタ情報を追加
        prediction_result['venue_name'] = race_card.get('venue_name', str(venue))
        prediction_result['race_number'] = race_number
        prediction_result['date'] = target_date.isoformat()
        prediction_result['race_name'] = race_card.get('race_name', '')

        logger.info("予測完了")
        return prediction_result

    def display_prediction(self, result: Dict):
        """
        予測結果を表示

        Args:
            result: 予測結果
        """
        if 'error' in result:
            print(f"\nエラー: {result['error']}")
            return

        print("\n" + "=" * 60)
        print(f"{result.get('venue_name', '')} R{result.get('race_number', '')} - {result.get('race_name', '')}")
        print(f"日付: {result.get('date', '')}")
        print(f"モデル: {result.get('model_type', '')}")
        print("=" * 60)

        # 単勝予測
        print("\n【単勝予測】")
        predictions = result.get('predictions', [])
        for pred in predictions:
            rank = pred.get('rank', 0)
            boat = pred.get('boat_number', 0)
            prob = pred.get('probability', 0.0)
            score = pred.get('score', 0.0)

            marker = "◎" if rank == 1 else ("○" if rank == 2 else ("▲" if rank == 3 else "  "))
            print(f"{marker} {rank}位: {boat}号艇 (確率: {prob:6.1%}, スコア: {score:.3f})")

        # 推奨
        top3 = result.get('top3', [])
        if top3:
            print(f"\n推奨: {'-'.join(map(str, top3))}")

        # 2連単予測
        quinella = result.get('quinella_top5', [])
        if quinella:
            print("\n【2連単予測（上位5通り）】")
            for i, (b1, b2, prob) in enumerate(quinella, 1):
                print(f"{i}. {b1}-{b2} (確率: {prob:.2%})")

        # 3連単予測
        trifecta = result.get('trifecta_top5', [])
        if trifecta:
            print("\n【3連単予測（上位5通り）】")
            for i, (b1, b2, b3, prob) in enumerate(trifecta, 1):
                print(f"{i}. {b1}-{b2}-{b3} (確率: {prob:.3%})")

        print("=" * 60 + "\n")


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description='ボートレース予測アプリケーション',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
使用例:
  # 徳山1Rを予測
  python predict_race.py 徳山 1

  # 会場IDで指定
  python predict_race.py 18 1

  # 特定の日付を指定
  python predict_race.py 徳山 1 -d 2024-01-15

  # JSON形式で出力
  python predict_race.py 徳山 1 --json

  # 会場一覧を表示
  python predict_race.py --list
        '''
    )

    parser.add_argument('venue', nargs='?', help='競艇場名またはID（1-24）')
    parser.add_argument('race', nargs='?', type=int, help='レース番号（1-12）')
    parser.add_argument('-d', '--date', help='対象日（YYYY-MM-DD形式）')
    parser.add_argument('-m', '--model', help='学習済みモデルのパス')
    parser.add_argument('-s', '--selenium', action='store_true', help='Seleniumを使用')
    parser.add_argument('--json', action='store_true', help='JSON形式で出力')
    parser.add_argument('--list', action='store_true', help='会場一覧を表示')
    parser.add_argument('-v', '--verbose', action='store_true', help='詳細ログを表示')

    args = parser.parse_args()

    # ログレベル設定
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # 会場一覧表示
    if args.list:
        print("\n=== 全ボートレース場一覧 ===")
        for venue in get_all_venues():
            print(f"{venue.venue_id:2d}. {venue.name:8s} - {venue.url}")
        print()
        return

    # 引数チェック
    if not args.venue or not args.race:
        parser.print_help()
        return

    # 対象日
    target_date = None
    if args.date:
        try:
            target_date = datetime.strptime(args.date, '%Y-%m-%d').date()
        except ValueError:
            print("エラー: 日付形式が正しくありません。YYYY-MM-DD形式で指定してください。")
            return

    # モデルパス
    model_path = Path(args.model) if args.model else None

    # 予測実行
    predictor = RacePredictor(model_path=model_path, use_selenium=args.selenium)
    try:
        result = predictor.predict_race(
            venue=args.venue,
            race_number=args.race,
            target_date=target_date
        )

        if args.json:
            # JSON出力
            print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        else:
            # テキスト表示
            predictor.display_prediction(result)

    except KeyboardInterrupt:
        print("\n\n中断されました")
    except Exception as e:
        logger.error(f"予測エラー: {e}", exc_info=args.verbose)
        print(f"\nエラーが発生しました: {e}")
    finally:
        predictor.close()


if __name__ == "__main__":
    main()
