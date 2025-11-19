"""
シミュレーションAPIのスキーマ定義
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import date


class SimulationRequest(BaseModel):
    """シミュレーションリクエスト"""
    model_paths: Dict[str, str] = Field(
        ..., description="モデル名: パスのマッピング"
    )
    start_date: date = Field(..., description="開始日")
    end_date: date = Field(..., description="終了日")
    bet_type: str = Field(
        default="boxed_trifecta",
        description="舟券種類（boxed_trifecta, trifecta）"
    )
    bet_amount: int = Field(
        default=100,
        ge=100,
        description="1点あたりの賭け金（円）"
    )
    stadium_ids: Optional[List[int]] = Field(
        None,
        description="競艇場ID（未指定の場合は全場）"
    )


class RaceSimulationResult(BaseModel):
    """レースごとのシミュレーション結果"""
    race_date: date = Field(..., description="レース日")
    stadium_id: int = Field(..., description="競艇場ID")
    stadium_name: str = Field(..., description="競艇場名")
    race_index: int = Field(..., description="レース番号")
    predicted_boats: List[int] = Field(..., description="予測した3艇")
    actual_order: List[int] = Field(..., description="実際の着順")
    bet_amount: int = Field(..., description="賭け金")
    refund_amount: int = Field(..., description="払い戻し金額")
    profit: int = Field(..., description="収支")
    hit: bool = Field(..., description="的中フラグ")


class SimulationMetrics(BaseModel):
    """シミュレーション全体のメトリクス"""
    total_races: int = Field(..., description="総レース数")
    hit_count: int = Field(..., description="的中数")
    hit_rate: float = Field(..., description="的中率")
    total_bet: int = Field(..., description="総賭け金")
    total_refund: int = Field(..., description="総払い戻し")
    total_profit: int = Field(..., description="総収支")
    recovery_rate: float = Field(..., description="回収率（%）")
    max_profit: int = Field(..., description="最大利益")
    max_loss: int = Field(..., description="最大損失")
    consecutive_wins: int = Field(..., description="最大連勝数")
    consecutive_losses: int = Field(..., description="最大連敗数")


class TimeSeriesDataPoint(BaseModel):
    """時系列データポイント"""
    date: date = Field(..., description="日付")
    cumulative_profit: int = Field(..., description="累積収支")
    cumulative_bet: int = Field(..., description="累積賭け金")
    cumulative_refund: int = Field(..., description="累積払い戻し")
    recovery_rate: float = Field(..., description="その時点での回収率")
    race_count: int = Field(..., description="その時点でのレース数")


class ModelSimulationResult(BaseModel):
    """モデルごとのシミュレーション結果"""
    model_name: str = Field(..., description="モデル名")
    metrics: SimulationMetrics = Field(..., description="メトリクス")
    time_series: List[TimeSeriesDataPoint] = Field(
        ..., description="時系列データ"
    )
    race_results: List[RaceSimulationResult] = Field(
        ..., description="レースごとの結果"
    )


class SimulationResponse(BaseModel):
    """シミュレーションレスポンス"""
    request_info: Dict[str, Any] = Field(..., description="リクエスト情報")
    models: List[ModelSimulationResult] = Field(
        ..., description="各モデルのシミュレーション結果"
    )
    comparison: Optional[Dict[str, Any]] = Field(
        None, description="モデル間比較情報"
    )


class DashboardRequest(BaseModel):
    """ダッシュボードリクエスト"""
    target_date: date = Field(..., description="対象日")
    model_paths: Dict[str, str] = Field(
        ..., description="モデル名: パスのマッピング"
    )
    stadium_ids: Optional[List[int]] = Field(
        None,
        description="競艇場ID（未指定の場合は全場）"
    )


class RacePredictionWithResult(BaseModel):
    """予測と結果を含むレース情報"""
    race_date: date = Field(..., description="レース日")
    stadium_id: int = Field(..., description="競艇場ID")
    stadium_name: str = Field(..., description="競艇場名")
    race_index: int = Field(..., description="レース番号")
    predicted_boats: Dict[str, List[int]] = Field(
        ..., description="各モデルの予測3艇"
    )
    actual_order: Optional[List[int]] = Field(
        None, description="実際の着順（レース終了後のみ）"
    )
    is_finished: bool = Field(..., description="レース終了フラグ")
    results: Optional[Dict[str, Dict[str, Any]]] = Field(
        None, description="各モデルの結果（レース終了後のみ）"
    )


class DashboardResponse(BaseModel):
    """ダッシュボードレスポンス"""
    target_date: date = Field(..., description="対象日")
    races: List[RacePredictionWithResult] = Field(
        ..., description="レース一覧"
    )
    summary: Dict[str, Any] = Field(..., description="サマリー情報")
