"""
モデル管理APIのスキーマ定義
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class ModelInfo(BaseModel):
    """モデル情報"""
    name: str = Field(..., description="モデル名")
    model_type: str = Field(..., description="モデルタイプ")
    path: str = Field(..., description="モデルパス")
    created_at: Optional[datetime] = Field(None, description="作成日時")
    file_size: Optional[int] = Field(None, description="ファイルサイズ（バイト）")
    metadata: Optional[Dict[str, Any]] = Field(None, description="メタデータ")


class ModelListResponse(BaseModel):
    """モデル一覧レスポンス"""
    models: list[ModelInfo] = Field(..., description="モデル一覧")
    total: int = Field(..., description="総数")
