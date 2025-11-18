"""
推論APIのスキーマ定義
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import date


class PredictionRequest(BaseModel):
    """推論リクエスト"""
    model_path: str = Field(..., description="モデルパス")
    model_type: str = Field(..., description="モデルタイプ")
    race_date: date = Field(..., description="レース日")
    stadium_id: int = Field(..., ge=1, le=24, description="競艇場ID")
    race_index: Optional[int] = Field(
        None, ge=1, le=12, description="レース番号（未指定の場合は全レース）"
    )


class BoatPrediction(BaseModel):
    """艇の予測結果"""
    boat_number: int = Field(..., description="艇番")
    probability: float = Field(..., description="3着以内確率")
    std: Optional[float] = Field(None, description="標準偏差（ベイズのみ）")
    ci_lower: Optional[float] = Field(None, description="信頼区間下限（ベイズのみ）")
    ci_upper: Optional[float] = Field(None, description="信頼区間上限（ベイズのみ）")


class RacePrediction(BaseModel):
    """レース予測結果"""
    race_date: date = Field(..., description="レース日")
    stadium_id: int = Field(..., description="競艇場ID")
    race_index: int = Field(..., description="レース番号")
    boats: List[BoatPrediction] = Field(..., description="各艇の予測")
    recommended_boats: List[int] = Field(..., description="推奨3艇")
    expected_hit_rate: float = Field(..., description="期待的中率")
    has_uncertainty: bool = Field(default=False, description="不確実性情報あり")


class MultiModelPredictionRequest(BaseModel):
    """複数モデル予測リクエスト"""
    model_paths: Dict[str, str] = Field(
        ..., description="モデル名: パスのマッピング"
    )
    race_date: date = Field(..., description="レース日")
    stadium_id: int = Field(..., description="競艇場ID")
    race_index: int = Field(..., description="レース番号")


class MultiModelPredictionResponse(BaseModel):
    """複数モデル予測レスポンス"""
    race_info: Dict[str, Any] = Field(..., description="レース情報")
    predictions: Dict[str, RacePrediction] = Field(..., description="各モデルの予測")
    comparison: Optional[Dict[str, Any]] = Field(None, description="比較情報")


class FeatureImportanceRequest(BaseModel):
    """特徴量重要度取得リクエスト"""
    model_path: str = Field(..., description="モデルパス")
    model_type: str = Field(..., description="モデルタイプ")
    top_n: int = Field(default=20, ge=1, le=100, description="上位N件")


class FeatureImportance(BaseModel):
    """特徴量重要度"""
    feature_name: str = Field(..., description="特徴量名")
    importance: float = Field(..., description="重要度")
    rank: int = Field(..., description="ランク")


class FeatureImportanceResponse(BaseModel):
    """特徴量重要度レスポンス"""
    model_type: str = Field(..., description="モデルタイプ")
    method: str = Field(..., description="重要度計算方法")
    features: List[FeatureImportance] = Field(..., description="特徴量重要度リスト")
