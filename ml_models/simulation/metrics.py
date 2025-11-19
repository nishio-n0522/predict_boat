"""
シミュレーションメトリクス計算

シミュレーション結果から各種統計情報を計算
"""

from typing import List, Dict, Any
import datetime as dt


class SimulationMetricsCalculator:
    """シミュレーションメトリクス計算機"""

    @staticmethod
    def calculate_metrics(race_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        シミュレーション結果からメトリクスを計算

        Args:
            race_results: レースごとのシミュレーション結果

        Returns:
            dict: 計算されたメトリクス
        """
        if not race_results:
            return {
                "total_races": 0,
                "hit_count": 0,
                "hit_rate": 0.0,
                "total_bet": 0,
                "total_refund": 0,
                "total_profit": 0,
                "recovery_rate": 0.0,
                "max_profit": 0,
                "max_loss": 0,
                "consecutive_wins": 0,
                "consecutive_losses": 0
            }

        total_races = len(race_results)
        hit_count = sum(1 for r in race_results if r["hit"])
        total_bet = sum(r["bet_amount"] for r in race_results)
        total_refund = sum(r["refund_amount"] for r in race_results)
        total_profit = total_refund - total_bet

        hit_rate = hit_count / total_races if total_races > 0 else 0.0
        recovery_rate = (total_refund / total_bet * 100) if total_bet > 0 else 0.0

        # 最大利益と最大損失
        profits = [r["profit"] for r in race_results]
        max_profit = max(profits) if profits else 0
        max_loss = min(profits) if profits else 0

        # 連勝・連敗数
        consecutive_wins = SimulationMetricsCalculator._calculate_max_consecutive(
            race_results, True
        )
        consecutive_losses = SimulationMetricsCalculator._calculate_max_consecutive(
            race_results, False
        )

        return {
            "total_races": total_races,
            "hit_count": hit_count,
            "hit_rate": hit_rate,
            "total_bet": total_bet,
            "total_refund": total_refund,
            "total_profit": total_profit,
            "recovery_rate": recovery_rate,
            "max_profit": max_profit,
            "max_loss": max_loss,
            "consecutive_wins": consecutive_wins,
            "consecutive_losses": consecutive_losses
        }

    @staticmethod
    def _calculate_max_consecutive(
        race_results: List[Dict[str, Any]], target_hit: bool
    ) -> int:
        """
        最大連勝数または最大連敗数を計算

        Args:
            race_results: レースごとのシミュレーション結果
            target_hit: True=連勝, False=連敗

        Returns:
            int: 最大連勝数または最大連敗数
        """
        max_consecutive = 0
        current_consecutive = 0

        for result in race_results:
            if result["hit"] == target_hit:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0

        return max_consecutive

    @staticmethod
    def calculate_time_series(race_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        時系列データを計算

        Args:
            race_results: レースごとのシミュレーション結果

        Returns:
            list: 日ごとの時系列データ
        """
        if not race_results:
            return []

        # 日付ごとにグループ化
        daily_data: Dict[dt.date, List[Dict[str, Any]]] = {}
        for result in race_results:
            race_date = result["race_date"]
            if race_date not in daily_data:
                daily_data[race_date] = []
            daily_data[race_date].append(result)

        # 時系列データを生成
        sorted_dates = sorted(daily_data.keys())
        time_series = []
        cumulative_bet = 0
        cumulative_refund = 0
        cumulative_profit = 0
        cumulative_races = 0

        for date in sorted_dates:
            day_results = daily_data[date]
            day_bet = sum(r["bet_amount"] for r in day_results)
            day_refund = sum(r["refund_amount"] for r in day_results)
            day_profit = day_refund - day_bet

            cumulative_bet += day_bet
            cumulative_refund += day_refund
            cumulative_profit += day_profit
            cumulative_races += len(day_results)

            recovery_rate = (
                (cumulative_refund / cumulative_bet * 100)
                if cumulative_bet > 0
                else 0.0
            )

            time_series.append({
                "date": date,
                "cumulative_profit": cumulative_profit,
                "cumulative_bet": cumulative_bet,
                "cumulative_refund": cumulative_refund,
                "recovery_rate": recovery_rate,
                "race_count": cumulative_races
            })

        return time_series

    @staticmethod
    def compare_models(
        model_results: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        複数モデルの結果を比較

        Args:
            model_results: モデル名: メトリクスのマッピング

        Returns:
            dict: 比較結果
        """
        if not model_results:
            return {}

        # 各指標でランキング
        rankings = {
            "hit_rate": [],
            "recovery_rate": [],
            "total_profit": []
        }

        for model_name, metrics in model_results.items():
            rankings["hit_rate"].append({
                "model": model_name,
                "value": metrics["hit_rate"]
            })
            rankings["recovery_rate"].append({
                "model": model_name,
                "value": metrics["recovery_rate"]
            })
            rankings["total_profit"].append({
                "model": model_name,
                "value": metrics["total_profit"]
            })

        # ソート
        for key in rankings:
            rankings[key] = sorted(
                rankings[key], key=lambda x: x["value"], reverse=True
            )

        # 最高値・最低値
        best_hit_rate = max(
            model_results.values(), key=lambda x: x["hit_rate"]
        ) if model_results else None

        best_recovery_rate = max(
            model_results.values(), key=lambda x: x["recovery_rate"]
        ) if model_results else None

        best_profit = max(
            model_results.values(), key=lambda x: x["total_profit"]
        ) if model_results else None

        return {
            "rankings": rankings,
            "best_hit_rate_model": [
                name for name, m in model_results.items()
                if m == best_hit_rate
            ][0] if best_hit_rate else None,
            "best_recovery_rate_model": [
                name for name, m in model_results.items()
                if m == best_recovery_rate
            ][0] if best_recovery_rate else None,
            "best_profit_model": [
                name for name, m in model_results.items()
                if m == best_profit
            ][0] if best_profit else None
        }
