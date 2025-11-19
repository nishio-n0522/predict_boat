"""
バックテストエンジン

過去のデータを使用して、モデルの予測性能と舟券購入シミュレーションを実行
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import datetime as dt

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent.parent))

from db.db_setting import session_factory
import db
from ml_models.predict import LightGBMRacePredictor
from ml_models.predict_transformer import TransformerRacePredictor
from ml_models.predict_bayesian import BayesianRacePredictor
from ml_models.race_grade_classifier import classify_race_grade, is_target_race


class Backtester:
    """バックテストエンジン"""

    def __init__(self):
        """初期化"""
        self.session = session_factory()
        self.predictors: Dict[str, Any] = {}

    def load_model(self, model_name: str, model_path: str, model_type: str):
        """
        モデルをロード

        Args:
            model_name: モデル名
            model_path: モデルファイルパス
            model_type: モデルタイプ (lightgbm, transformer, bayesian)
        """
        if model_type == "lightgbm":
            predictor = LightGBMRacePredictor(model_path)
        elif model_type == "transformer":
            predictor = TransformerRacePredictor(model_path)
        elif model_type == "bayesian":
            predictor = BayesianRacePredictor(model_path)
        else:
            raise ValueError(f"Unknown model type: {model_type}")

        self.predictors[model_name] = predictor

    def run_simulation(
        self,
        model_name: str,
        start_date: dt.date,
        end_date: dt.date,
        bet_type: str = "boxed_trifecta",
        bet_amount: int = 100,
        stadium_ids: Optional[List[int]] = None,
        target_grades_only: bool = True
    ) -> Dict[str, Any]:
        """
        シミュレーション実行

        Args:
            model_name: モデル名
            start_date: 開始日
            end_date: 終了日
            bet_type: 舟券種類 (boxed_trifecta, trifecta)
            bet_amount: 1点あたりの賭け金（円）
            stadium_ids: 対象競艇場ID（未指定の場合は全場）
            target_grades_only: True=一般戦・G3のみ

        Returns:
            dict: シミュレーション結果
        """
        if model_name not in self.predictors:
            raise ValueError(f"Model not loaded: {model_name}")

        predictor = self.predictors[model_name]

        # 対象レースを取得
        query = self.session.query(db.each_race_results.EachRaceResult).filter(
            db.each_race_results.EachRaceResult.date >= start_date,
            db.each_race_results.EachRaceResult.date <= end_date
        )

        if stadium_ids:
            query = query.filter(
                db.each_race_results.EachRaceResult.stadium_id.in_(stadium_ids)
            )

        races = query.order_by(
            db.each_race_results.EachRaceResult.date,
            db.each_race_results.EachRaceResult.stadium_id,
            db.each_race_results.EachRaceResult.race_index
        ).all()

        race_results = []
        skipped = 0

        for race in races:
            # グレード判定
            if target_grades_only:
                grade = classify_race_grade(race.race_name)
                if not is_target_race(grade):
                    skipped += 1
                    continue

            try:
                # 予測実行
                prediction = predictor.predict_race(
                    race.date,
                    race.stadium_id,
                    race.race_index
                )

                # 実際の結果を取得
                actual_results = self._get_actual_results(race)

                if not actual_results:
                    skipped += 1
                    continue

                # シミュレーション結果を計算
                sim_result = self._simulate_bet(
                    prediction,
                    actual_results,
                    race,
                    bet_type,
                    bet_amount
                )
                race_results.append(sim_result)

            except Exception as e:
                skipped += 1
                continue

        return {
            "race_results": race_results,
            "skipped": skipped
        }

    def _get_actual_results(
        self, race: db.each_race_results.EachRaceResult
    ) -> Optional[Dict[str, Any]]:
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
            return None

        results = {}
        for boat_data in boat_data_list:
            if not boat_data.order_of_arrival:
                return None

            results[boat_data.boat_number] = {
                'arrival': boat_data.order_of_arrival,
                'is_top3': boat_data.order_of_arrival <= 3
            }

        # 着順リスト（1着、2着、3着の艇番）
        sorted_boats = sorted(
            [boat_data.boat_number for boat_data in boat_data_list],
            key=lambda x: results[x]['arrival']
        )
        results['actual_order'] = sorted_boats

        # 払戻金
        results['trifecta_refund'] = race.trifecta_refund or 0
        results['boxed_trifecta_refund'] = race.boxed_trifecta_refund or 0

        return results

    def _simulate_bet(
        self,
        prediction,
        actual_results: Dict[str, Any],
        race: db.each_race_results.EachRaceResult,
        bet_type: str,
        bet_amount: int
    ) -> Dict[str, Any]:
        """
        舟券購入シミュレーション

        Args:
            prediction: 予測結果
            actual_results: 実際の結果
            race: レースデータ
            bet_type: 舟券種類
            bet_amount: 1点あたりの賭け金

        Returns:
            dict: シミュレーション結果
        """
        recommended_boats = prediction.get_recommended_boats()

        # 実際の3着以内
        actual_top3 = sorted([
            boat_num for boat_num, data in actual_results.items()
            if isinstance(boat_num, int) and data['is_top3']
        ], key=lambda x: actual_results[x]['arrival'])

        # 的中判定と払戻金計算
        if bet_type == "boxed_trifecta":
            # 3連複ボックス（6点買い）
            total_bet = bet_amount * 6
            hit = set(recommended_boats) == set(actual_top3)
            refund = actual_results['boxed_trifecta_refund'] if hit else 0
        elif bet_type == "trifecta":
            # 3連単ボックス（6点買い）
            total_bet = bet_amount * 6
            hit = set(recommended_boats) == set(actual_top3)
            refund = actual_results['trifecta_refund'] if hit else 0
        else:
            raise ValueError(f"Unknown bet type: {bet_type}")

        profit = refund - total_bet

        # 競艇場名を取得
        stadium = self.session.query(db.stadium.Stadium).filter(
            db.stadium.Stadium.id == race.stadium_id
        ).first()
        stadium_name = stadium.name if stadium else f"場{race.stadium_id}"

        return {
            "race_date": race.date,
            "stadium_id": race.stadium_id,
            "stadium_name": stadium_name,
            "race_index": race.race_index,
            "predicted_boats": recommended_boats,
            "actual_order": actual_results['actual_order'],
            "bet_amount": total_bet,
            "refund_amount": refund,
            "profit": profit,
            "hit": hit
        }

    def close(self):
        """リソースをクローズ"""
        for predictor in self.predictors.values():
            predictor.close()
        self.session.close()
