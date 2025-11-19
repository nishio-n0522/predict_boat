"""
シミュレーションAPIルーター
"""

from fastapi import APIRouter, HTTPException

from backend.schemas.simulation import (
    SimulationRequest,
    SimulationResponse,
    DashboardRequest,
    DashboardResponse,
)
from backend.services.simulation_service import SimulationService

router = APIRouter(prefix="/api/simulation", tags=["simulation"])
simulation_service = SimulationService()


@router.post("/run", response_model=SimulationResponse)
async def run_simulation(request: SimulationRequest):
    """
    シミュレーション実行

    指定された期間とモデルで舟券購入シミュレーションを実行します。
    """
    try:
        result = simulation_service.run_simulation(
            model_paths=request.model_paths,
            start_date=request.start_date,
            end_date=request.end_date,
            bet_type=request.bet_type,
            bet_amount=request.bet_amount,
            stadium_ids=request.stadium_ids
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dashboard", response_model=DashboardResponse)
async def get_dashboard(request: DashboardRequest):
    """
    ダッシュボードデータ取得

    指定された日付のレース予測と結果を取得します。
    """
    try:
        result = simulation_service.get_dashboard_data(
            target_date=request.target_date,
            model_paths=request.model_paths,
            stadium_ids=request.stadium_ids
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
