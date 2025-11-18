"""
学習APIのスキーマ定義
"""

from typing import Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import date


class TrainingRequest(BaseModel):
    """学習リクエスト"""
    model_type: Literal["lightgbm", "transformer", "bayesian"] = Field(
        ..., description="モデルタイプ"
    )
    dataset_path: str = Field(
        default="data/processed/training_dataset.csv",
        description="訓練データパス"
    )
    output_path: Optional[str] = Field(
        None, description="モデル保存パス（未指定の場合は自動生成）"
    )
    start_date: Optional[date] = Field(
        None, description="データ開始日（フィルタ用）"
    )
    end_date: Optional[date] = Field(
        None, description="データ終了日（フィルタ用）"
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="モデル固有のパラメータ"
    )


class TrainingProgress(BaseModel):
    """学習進捗"""
    status: Literal["starting", "running", "completed", "failed"] = Field(
        ..., description="ステータス"
    )
    progress: float = Field(
        default=0.0, ge=0.0, le=1.0, description="進捗率（0.0〜1.0）"
    )
    message: str = Field(
        default="", description="メッセージ"
    )
    current_step: Optional[str] = Field(
        None, description="現在のステップ"
    )
    metrics: Optional[Dict[str, float]] = Field(
        None, description="評価指標"
    )


class TrainingResponse(BaseModel):
    """学習レスポンス"""
    task_id: str = Field(..., description="タスクID")
    model_type: str = Field(..., description="モデルタイプ")
    status: str = Field(..., description="ステータス")
    message: str = Field(..., description="メッセージ")
