"""
シミュレーションサービス
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import date

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent.parent))

from ml_models.simulation.backtester import Backtester
from ml_models.simulation.metrics import SimulationMetricsCalculator
from backend.schemas.simulation import (
    RaceSimulationResult,
    SimulationMetrics,
    TimeSeriesDataPoint,
    ModelSimulationResult,
)
from db.db_setting import session_factory
import db


class SimulationService:
    """シミュレーションサービス"""

    def run_simulation(
        self,
        model_paths: Dict[str, str],
        start_date: date,
        end_date: date,
        bet_type: str = "boxed_trifecta",
        bet_amount: int = 100,
        stadium_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        シミュレーション実行

        Args:
            model_paths: モデル名: パスのマッピング
            start_date: 開始日
            end_date: 終了日
            bet_type: 舟券種類
            bet_amount: 1点あたりの賭け金
            stadium_ids: 対象競艇場ID

        Returns:
            dict: シミュレーション結果
        """
        backtester = Backtester()
        results = []

        try:
            # 各モデルでシミュレーション実行
            for model_name, model_path in model_paths.items():
                # モデルタイプを推定
                model_type = self._infer_model_type(model_path)
                if not model_type:
                    continue

                # モデルをロード
                backtester.load_model(model_name, model_path, model_type)

                # シミュレーション実行
                sim_result = backtester.run_simulation(
                    model_name=model_name,
                    start_date=start_date,
                    end_date=end_date,
                    bet_type=bet_type,
                    bet_amount=bet_amount,
                    stadium_ids=stadium_ids
                )

                # メトリクス計算
                metrics = SimulationMetricsCalculator.calculate_metrics(
                    sim_result["race_results"]
                )

                # 時系列データ計算
                time_series = SimulationMetricsCalculator.calculate_time_series(
                    sim_result["race_results"]
                )

                # レース結果をスキーマに変換
                race_results = [
                    RaceSimulationResult(**result)
                    for result in sim_result["race_results"]
                ]

                # 時系列データをスキーマに変換
                time_series_data = [
                    TimeSeriesDataPoint(**point)
                    for point in time_series
                ]

                # モデルシミュレーション結果を構築
                model_result = ModelSimulationResult(
                    model_name=model_name,
                    metrics=SimulationMetrics(**metrics),
                    time_series=time_series_data,
                    race_results=race_results
                )

                results.append(model_result)

        finally:
            backtester.close()

        # モデル間比較
        comparison = None
        if len(results) > 1:
            metrics_dict = {
                r.model_name: {
                    "hit_rate": r.metrics.hit_rate,
                    "recovery_rate": r.metrics.recovery_rate,
                    "total_profit": r.metrics.total_profit,
                    "total_races": r.metrics.total_races,
                    "hit_count": r.metrics.hit_count,
                    "total_bet": r.metrics.total_bet,
                    "total_refund": r.metrics.total_refund
                }
                for r in results
            }
            comparison = SimulationMetricsCalculator.compare_models(metrics_dict)

        return {
            "request_info": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "bet_type": bet_type,
                "bet_amount": bet_amount,
                "stadium_ids": stadium_ids
            },
            "models": results,
            "comparison": comparison
        }

    def get_dashboard_data(
        self,
        target_date: date,
        model_paths: Dict[str, str],
        stadium_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        ダッシュボードデータ取得

        Args:
            target_date: 対象日
            model_paths: モデル名: パスのマッピング
            stadium_ids: 対象競艇場ID

        Returns:
            dict: ダッシュボードデータ
        """
        session = session_factory()
        backtester = Backtester()

        try:
            # 対象日のレースを取得
            query = session.query(db.each_race_results.EachRaceResult).filter(
                db.each_race_results.EachRaceResult.date == target_date
            )

            if stadium_ids:
                query = query.filter(
                    db.each_race_results.EachRaceResult.stadium_id.in_(stadium_ids)
                )

            races = query.order_by(
                db.each_race_results.EachRaceResult.stadium_id,
                db.each_race_results.EachRaceResult.race_index
            ).all()

            # 各モデルをロード
            for model_name, model_path in model_paths.items():
                model_type = self._infer_model_type(model_path)
                if model_type:
                    backtester.load_model(model_name, model_path, model_type)

            # レースごとの予測と結果を取得
            race_data = []
            for race in races:
                # 競艇場名を取得
                stadium = session.query(db.stadium.Stadium).filter(
                    db.stadium.Stadium.id == race.stadium_id
                ).first()
                stadium_name = stadium.name if stadium else f"場{race.stadium_id}"

                # 各モデルで予測
                predicted_boats = {}
                for model_name in backtester.predictors.keys():
                    try:
                        predictor = backtester.predictors[model_name]
                        prediction = predictor.predict_race(
                            race.date,
                            race.stadium_id,
                            race.race_index
                        )
                        predicted_boats[model_name] = prediction.get_recommended_boats()
                    except:
                        predicted_boats[model_name] = []

                # 実際の結果を取得
                actual_results = backtester._get_actual_results(race)
                is_finished = actual_results is not None

                race_info = {
                    "race_date": race.date,
                    "stadium_id": race.stadium_id,
                    "stadium_name": stadium_name,
                    "race_index": race.race_index,
                    "predicted_boats": predicted_boats,
                    "actual_order": actual_results["actual_order"] if is_finished else None,
                    "is_finished": is_finished,
                    "results": None
                }

                # レースが終了している場合、各モデルの結果を計算
                if is_finished:
                    model_results = {}
                    for model_name, boats in predicted_boats.items():
                        actual_top3 = actual_results["actual_order"][:3]
                        hit = set(boats) == set(actual_top3)
                        refund = actual_results["boxed_trifecta_refund"] if hit else 0
                        bet = 600  # 3連複ボックス6点買い

                        model_results[model_name] = {
                            "hit": hit,
                            "bet_amount": bet,
                            "refund_amount": refund,
                            "profit": refund - bet
                        }

                    race_info["results"] = model_results

                race_data.append(race_info)

            # サマリー情報を計算
            summary = self._calculate_dashboard_summary(race_data)

            return {
                "target_date": target_date,
                "races": race_data,
                "summary": summary
            }

        finally:
            backtester.close()
            session.close()

    def _infer_model_type(self, model_path: str) -> Optional[str]:
        """モデルタイプを推定"""
        model_path_lower = model_path.lower()
        if "lightgbm" in model_path_lower:
            return "lightgbm"
        elif "transformer" in model_path_lower:
            return "transformer"
        elif "bayesian" in model_path_lower:
            return "bayesian"
        return None

    def _calculate_dashboard_summary(
        self, race_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """ダッシュボードサマリーを計算"""
        total_races = len(race_data)
        finished_races = sum(1 for r in race_data if r["is_finished"])
        pending_races = total_races - finished_races

        # モデルごとの集計
        model_summaries = {}
        if race_data and race_data[0]["predicted_boats"]:
            model_names = list(race_data[0]["predicted_boats"].keys())

            for model_name in model_names:
                hits = 0
                total_bet = 0
                total_refund = 0

                for race in race_data:
                    if race["is_finished"] and race["results"]:
                        result = race["results"].get(model_name, {})
                        if result.get("hit", False):
                            hits += 1
                        total_bet += result.get("bet_amount", 0)
                        total_refund += result.get("refund_amount", 0)

                hit_rate = hits / finished_races if finished_races > 0 else 0
                recovery_rate = (total_refund / total_bet * 100) if total_bet > 0 else 0

                model_summaries[model_name] = {
                    "hits": hits,
                    "hit_rate": hit_rate,
                    "total_bet": total_bet,
                    "total_refund": total_refund,
                    "profit": total_refund - total_bet,
                    "recovery_rate": recovery_rate
                }

        return {
            "total_races": total_races,
            "finished_races": finished_races,
            "pending_races": pending_races,
            "model_summaries": model_summaries
        }
