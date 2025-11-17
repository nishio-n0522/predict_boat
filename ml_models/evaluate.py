"""
評価スクリプト

モデルの予測性能を評価し、的中率や回収率を計算します。
"""

import sys
from pathlib import Path
import datetime as dt
import pandas as pd
import numpy as np
from tqdm import tqdm

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from db.db_setting import session_factory
import db
from ml_models.predict import RacePredictor
from ml_models.race_grade_classifier import classify_race_grade, is_target_race


class ModelEvaluator:
    """モデル評価器"""

    def __init__(self, model_path: str):
        """
        初期化

        Args:
            model_path: 訓練済みモデルのパス
        """
        self.predictor = RacePredictor(model_path)
        self.session = session_factory()

    def evaluate_period(
        self,
        start_date: dt.date,
        end_date: dt.date,
        target_grades_only: bool = True
    ) -> dict:
        """
        期間内の予測性能を評価

        Args:
            start_date: 開始日
            end_date: 終了日
            target_grades_only: True=一般戦・G3のみ

        Returns:
            dict: 評価結果
        """
        print("=" * 80)
        print("モデル評価開始")
        print("=" * 80)
        print(f"期間: {start_date} ~ {end_date}")
        print(f"対象: {'一般戦・G3のみ' if target_grades_only else '全グレード'}")
        print()

        # 対象レースを取得
        races = self.session.query(db.each_race_results.EachRaceResult).filter(
            db.each_race_results.EachRaceResult.date >= start_date,
            db.each_race_results.EachRaceResult.date <= end_date
        ).order_by(
            db.each_race_results.EachRaceResult.date,
            db.each_race_results.EachRaceResult.stadium_id,
            db.each_race_results.EachRaceResult.race_index
        ).all()

        results = []
        skipped = 0

        for race in tqdm(races, desc="評価中"):
            # グレード判定
            if target_grades_only:
                grade = classify_race_grade(race.race_name)
                if not is_target_race(grade):
                    skipped += 1
                    continue

            try:
                # 予測実行
                prediction = self.predictor.predict_race(
                    race.date,
                    race.stadium_id,
                    race.race_index
                )

                # 実際の結果を取得
                actual_results = self._get_actual_results(race)

                if not actual_results:
                    skipped += 1
                    continue

                # 評価指標を計算
                eval_result = self._evaluate_prediction(
                    prediction, actual_results, race
                )
                results.append(eval_result)

            except Exception as e:
                skipped += 1
                continue

        print()
        print("=" * 80)
        print(f"評価完了")
        print(f"  評価レース数: {len(results)}")
        print(f"  スキップ: {skipped}")
        print("=" * 80)

        if not results:
            print("警告: 評価可能なレースがありませんでした")
            return {}

        # 集計
        return self._aggregate_results(results)

    def _get_actual_results(self, race: db.each_race_results.EachRaceResult) -> dict:
        """
        実際のレース結果を取得

        Args:
            race: レースデータ

        Returns:
            dict: 結果データ
        """
        boat_data_list = self.session.query(db.each_boat_data.EachBoatData).filter(
            db.each_boat_data.EachBoatData.each_race_result_id == race.id
        ).order_by(db.each_boat_data.EachBoatData.boat_number).all()

        if len(boat_data_list) != 6:
            return {}

        results = {}
        for boat_data in boat_data_list:
            if not boat_data.order_of_arrival:
                return {}

            results[boat_data.boat_number] = {
                'arrival': boat_data.order_of_arrival,
                'is_top3': boat_data.order_of_arrival <= 3
            }

        # 3連単払戻金
        results['trifecta_refund'] = race.trifecta_refund

        return results

    def _evaluate_prediction(
        self,
        prediction,
        actual_results: dict,
        race: db.each_race_results.EachRaceResult
    ) -> dict:
        """
        予測を評価

        Args:
            prediction: 予測結果
            actual_results: 実際の結果
            race: レースデータ

        Returns:
            dict: 評価結果
        """
        recommended_boats = prediction.get_recommended_boats()

        # 推奨3艇が実際に3着以内に入ったか
        hit_count = sum(
            1 for boat in recommended_boats
            if actual_results[boat]['is_top3']
        )

        # 完全的中（推奨3艇が全て3着以内）
        perfect_hit = hit_count == 3

        # 2艇的中
        two_hit = hit_count == 2

        # 1艇的中
        one_hit = hit_count == 1

        # 3連単ボックスの的中判定（6点のうち1点でも的中すればOK）
        trifecta_hit = False
        actual_top3 = sorted([
            boat_num for boat_num, data in actual_results.items()
            if isinstance(boat_num, int) and data['is_top3']
        ], key=lambda x: actual_results[x]['arrival'])

        if len(actual_top3) == 3:
            # 推奨3艇が実際の3着以内と一致するか
            trifecta_hit = set(recommended_boats) == set(actual_top3)

        # 払戻金の取得
        trifecta_refund = actual_results.get('trifecta_refund', 0) or 0

        return {
            'race_date': race.date,
            'stadium_id': race.stadium_id,
            'race_index': race.race_index,
            'recommended_boats': recommended_boats,
            'actual_top3': actual_top3,
            'hit_count': hit_count,
            'perfect_hit': perfect_hit,
            'two_hit': two_hit,
            'one_hit': one_hit,
            'trifecta_hit': trifecta_hit,
            'trifecta_refund': trifecta_refund
        }

    def _aggregate_results(self, results: list) -> dict:
        """
        評価結果を集計

        Args:
            results: 評価結果リスト

        Returns:
            dict: 集計結果
        """
        total_races = len(results)

        perfect_hits = sum(1 for r in results if r['perfect_hit'])
        two_hits = sum(1 for r in results if r['two_hit'])
        one_hits = sum(1 for r in results if r['one_hit'])
        trifecta_hits = sum(1 for r in results if r['trifecta_hit'])

        # 3連単ボックス買いの収支計算（1点100円として）
        bet_per_race = 600  # 6点 x 100円
        total_bet = bet_per_race * total_races

        total_return = sum(
            r['trifecta_refund'] if r['trifecta_hit'] else 0
            for r in results
        )

        recovery_rate = (total_return / total_bet * 100) if total_bet > 0 else 0

        summary = {
            'total_races': total_races,
            'perfect_hit_rate': perfect_hits / total_races,
            'two_hit_rate': two_hits / total_races,
            'one_hit_rate': one_hits / total_races,
            'trifecta_hit_rate': trifecta_hits / total_races,
            'total_bet': total_bet,
            'total_return': total_return,
            'profit': total_return - total_bet,
            'recovery_rate': recovery_rate
        }

        # 結果を表示
        print("\n【評価結果サマリー】")
        print("=" * 80)
        print(f"総レース数: {total_races}")
        print()
        print("的中率:")
        print(f"  3艇完全的中: {perfect_hits} レース ({summary['perfect_hit_rate']*100:.2f}%)")
        print(f"  2艇的中: {two_hits} レース ({summary['two_hit_rate']*100:.2f}%)")
        print(f"  1艇的中: {one_hits} レース ({summary['one_hit_rate']*100:.2f}%)")
        print()
        print("3連単ボックス買い（6点 x 100円 = 600円/レース）:")
        print(f"  的中: {trifecta_hits} レース ({summary['trifecta_hit_rate']*100:.2f}%)")
        print(f"  総購入額: {summary['total_bet']:,}円")
        print(f"  総払戻額: {summary['total_return']:,}円")
        print(f"  収支: {summary['profit']:+,}円")
        print(f"  回収率: {summary['recovery_rate']:.2f}%")
        print("=" * 80)

        return summary

    def close(self):
        """リソースをクローズ"""
        self.predictor.close()
        self.session.close()


def main():
    """メイン処理"""
    import argparse

    parser = argparse.ArgumentParser(description="モデル評価")
    parser.add_argument(
        "--model",
        type=str,
        default="models_trained/lightgbm_model.pkl",
        help="訓練済みモデルのパス"
    )
    parser.add_argument(
        "--start-date",
        type=str,
        required=True,
        help="開始日 (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--end-date",
        type=str,
        required=True,
        help="終了日 (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--all-grades",
        action="store_true",
        help="全グレードを対象にする（デフォルトは一般戦・G3のみ）"
    )

    args = parser.parse_args()

    start_date = dt.datetime.strptime(args.start_date, "%Y-%m-%d").date()
    end_date = dt.datetime.strptime(args.end_date, "%Y-%m-%d").date()

    evaluator = ModelEvaluator(args.model)

    try:
        evaluator.evaluate_period(
            start_date=start_date,
            end_date=end_date,
            target_grades_only=not args.all_grades
        )
    finally:
        evaluator.close()


if __name__ == "__main__":
    main()
