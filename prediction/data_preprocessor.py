"""
推論用データ前処理モジュール

出走表データを機械学習モデル用の特徴量に変換
"""

import logging
from datetime import date
from typing import Dict, List, Optional
import numpy as np
import pandas as pd

from db.db_setting import session_factory
from db.player import get as get_player
from db.motor import get as get_motor
from db.boat import get as get_boat
from db.stadium import get_or_create as get_stadium
from db.player_national_win_rate import PlayerNationalWinRate
from db.player_local_win_rate import PlayerLocalWinRate
from db.motor_top2finish_rate import MotorTop2FinishRate
from db.boat_top2finish_rate import BoatTop2FinishRate
from db.session_stats import SessionStats
from db.live_info import LiveInfo

logger = logging.getLogger(__name__)


class RaceDataPreprocessor:
    """レースデータの前処理クラス"""

    def __init__(self):
        """初期化"""
        self.session = session_factory()

    def close(self):
        """リソースのクリーンアップ"""
        if self.session:
            self.session.close()

    def preprocess_race_card(self, race_card: Dict) -> pd.DataFrame:
        """
        出走表データを特徴量に変換

        Args:
            race_card: 出走表データ

        Returns:
            特徴量DataFrame（6艇分）
        """
        venue_id = race_card['venue_id']
        race_date = date.fromisoformat(race_card['date'])
        boats = race_card.get('boats', [])

        if not boats:
            logger.warning("艇データが空です")
            return pd.DataFrame()

        # 各艇の特徴量を生成
        features_list = []
        for boat in boats:
            features = self._extract_boat_features(boat, venue_id, race_date)
            if features:
                features_list.append(features)

        if not features_list:
            logger.warning("特徴量の抽出に失敗しました")
            return pd.DataFrame()

        # DataFrameに変換
        df = pd.DataFrame(features_list)

        # 艇番順にソート
        if 'boat_number' in df.columns:
            df = df.sort_values('boat_number').reset_index(drop=True)

        return df

    def _extract_boat_features(self, boat: Dict, venue_id: int, race_date: date) -> Optional[Dict]:
        """
        1艇分の特徴量を抽出

        Args:
            boat: 艇データ
            venue_id: 会場ID
            race_date: レース日

        Returns:
            特徴量辞書
        """
        try:
            features = {}

            # 基本情報
            features['boat_number'] = int(boat.get('boat_number', 0))
            features['venue_id'] = venue_id

            # 選手情報を取得
            player_id = boat.get('player_id')
            if player_id:
                player_features = self._get_player_features(player_id, venue_id, race_date)
                features.update(player_features)

            # モーター情報を取得
            motor_number = boat.get('motor_number')
            if motor_number:
                motor_features = self._get_motor_features(motor_number, venue_id, race_date)
                features.update(motor_features)

            # ボート情報を取得
            boat_number = boat.get('boat_id')  # ボートIDの場合
            if boat_number:
                boat_features = self._get_boat_features(boat_number, venue_id, race_date)
                features.update(boat_features)

            # 直前情報
            features['exhibition_time'] = float(boat.get('exhibition_time', 0.0) or 0.0)
            features['tilt'] = float(boat.get('tilt', 0.0) or 0.0)
            features['approach_course'] = int(boat.get('approach_course', 0) or 0)
            features['body_weight'] = float(boat.get('body_weight', 0.0) or 0.0)
            features['win_odds'] = float(boat.get('win_odds', 0.0) or 0.0)

            # 節間成績
            session_features = self._get_session_stats(player_id, venue_id, race_date)
            features.update(session_features)

            return features

        except Exception as e:
            logger.error(f"特徴量抽出エラー: {e}")
            return None

    def _get_player_features(self, player_id: int, venue_id: int, race_date: date) -> Dict:
        """選手の特徴量を取得"""
        features = {
            'player_id': player_id,
            'player_national_win_rate': 0.0,
            'player_national_2nd_rate': 0.0,
            'player_national_3rd_rate': 0.0,
            'player_local_win_rate': 0.0,
            'player_local_2nd_rate': 0.0,
            'player_local_3rd_rate': 0.0,
        }

        try:
            # 全国勝率を取得（最新のデータ）
            national_rate = self.session.query(PlayerNationalWinRate).filter_by(
                player_id=player_id
            ).order_by(PlayerNationalWinRate.date.desc()).first()

            if national_rate:
                features['player_national_win_rate'] = float(national_rate.first_place_rate or 0.0)
                features['player_national_2nd_rate'] = float(national_rate.second_place_rate or 0.0)
                features['player_national_3rd_rate'] = float(national_rate.third_place_rate or 0.0)

            # 当地勝率を取得
            stadium = get_stadium(self.session, venue_id)
            local_rate = self.session.query(PlayerLocalWinRate).filter_by(
                player_id=player_id,
                stadium=stadium
            ).order_by(PlayerLocalWinRate.date.desc()).first()

            if local_rate:
                features['player_local_win_rate'] = float(local_rate.first_place_rate or 0.0)
                features['player_local_2nd_rate'] = float(local_rate.second_place_rate or 0.0)
                features['player_local_3rd_rate'] = float(local_rate.third_place_rate or 0.0)

        except Exception as e:
            logger.debug(f"選手情報取得エラー: {e}")

        return features

    def _get_motor_features(self, motor_number: int, venue_id: int, race_date: date) -> Dict:
        """モーターの特徴量を取得"""
        features = {
            'motor_number': motor_number,
            'motor_2nd_rate': 0.0,
        }

        try:
            stadium = get_stadium(self.session, venue_id)
            motor = get_motor(self.session, motor_number, stadium)

            if motor:
                # モーター2連対率を取得（最新のデータ）
                motor_rate = self.session.query(MotorTop2FinishRate).filter_by(
                    motor=motor
                ).order_by(MotorTop2FinishRate.date.desc()).first()

                if motor_rate:
                    features['motor_2nd_rate'] = float(motor_rate.top2finish_rate or 0.0)

        except Exception as e:
            logger.debug(f"モーター情報取得エラー: {e}")

        return features

    def _get_boat_features(self, boat_id: int, venue_id: int, race_date: date) -> Dict:
        """ボートの特徴量を取得"""
        features = {
            'boat_id': boat_id,
            'boat_2nd_rate': 0.0,
        }

        try:
            stadium = get_stadium(self.session, venue_id)
            boat = get_boat(self.session, boat_id, stadium)

            if boat:
                # ボート2連対率を取得（最新のデータ）
                boat_rate = self.session.query(BoatTop2FinishRate).filter_by(
                    boat=boat
                ).order_by(BoatTop2FinishRate.date.desc()).first()

                if boat_rate:
                    features['boat_2nd_rate'] = float(boat_rate.top2finish_rate or 0.0)

        except Exception as e:
            logger.debug(f"ボート情報取得エラー: {e}")

        return features

    def _get_session_stats(self, player_id: int, venue_id: int, race_date: date) -> Dict:
        """節間成績を取得"""
        features = {
            'session_1st_rate': 0.0,
            'session_2nd_rate': 0.0,
            'session_3rd_rate': 0.0,
            'session_win_rate': 0.0,
        }

        try:
            stadium = get_stadium(self.session, venue_id)
            session_stat = self.session.query(SessionStats).filter_by(
                player_id=player_id,
                stadium=stadium,
                date=race_date
            ).first()

            if session_stat:
                features['session_1st_rate'] = float(session_stat.session_1st_rate or 0.0)
                features['session_2nd_rate'] = float(session_stat.session_2nd_rate or 0.0)
                features['session_3rd_rate'] = float(session_stat.session_3rd_rate or 0.0)
                features['session_win_rate'] = float(session_stat.session_win_rate or 0.0)

        except Exception as e:
            logger.debug(f"節間成績取得エラー: {e}")

        return features

    def get_feature_columns(self) -> List[str]:
        """
        特徴量カラム名のリストを取得

        Returns:
            カラム名のリスト
        """
        return [
            'boat_number',
            'venue_id',
            'player_id',
            'player_national_win_rate',
            'player_national_2nd_rate',
            'player_national_3rd_rate',
            'player_local_win_rate',
            'player_local_2nd_rate',
            'player_local_3rd_rate',
            'motor_number',
            'motor_2nd_rate',
            'boat_id',
            'boat_2nd_rate',
            'exhibition_time',
            'tilt',
            'approach_course',
            'body_weight',
            'win_odds',
            'session_1st_rate',
            'session_2nd_rate',
            'session_3rd_rate',
            'session_win_rate',
        ]


if __name__ == "__main__":
    # テスト用
    import sys
    import json
    from fetch_live_data import fetch_race_card_simple

    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) < 3:
        print("Usage: python data_preprocessor.py <venue> <race_number>")
        sys.exit(1)

    venue = sys.argv[1]
    race_number = int(sys.argv[2])

    # 出走表を取得
    card = fetch_race_card_simple(venue, race_number)

    # 前処理
    preprocessor = RaceDataPreprocessor()
    try:
        features_df = preprocessor.preprocess_race_card(card)
        print("\n=== 特徴量 ===")
        print(features_df)
        print(f"\nShape: {features_df.shape}")
        print(f"Columns: {list(features_df.columns)}")
    finally:
        preprocessor.close()
