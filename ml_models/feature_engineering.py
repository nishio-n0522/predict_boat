"""
特徴量エンジニアリングモジュール

データベースから特徴量を抽出し、機械学習モデル用のデータセットを構築します。
"""

import datetime as dt
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from db.db_setting import session_factory
import db


class FeatureExtractor:
    """特徴量抽出クラス"""

    def __init__(self, session: Session = None):
        """
        初期化

        Args:
            session: SQLAlchemyセッション（Noneの場合は新規作成）
        """
        self.session = session if session else session_factory()

    def extract_race_features(
        self,
        race_date: dt.date,
        stadium_id: int,
        race_index: int,
        lookback_days: int = 90
    ) -> pd.DataFrame:
        """
        1レース分の特徴量を抽出

        Args:
            race_date: レース日
            stadium_id: 競艇場ID
            race_index: レース番号
            lookback_days: 過去成績を参照する日数

        Returns:
            pd.DataFrame: 6艇分の特徴量（shape: (6, n_features)）
        """
        # レース基本情報を取得
        race = self.session.query(db.each_race_results.EachRaceResult).filter(
            db.each_race_results.EachRaceResult.date == race_date,
            db.each_race_results.EachRaceResult.stadium_id == stadium_id,
            db.each_race_results.EachRaceResult.race_index == race_index
        ).first()

        if not race:
            return pd.DataFrame()

        # 各艇のデータを取得
        boat_data_list = self.session.query(db.each_boat_data.EachBoatData).filter(
            db.each_boat_data.EachBoatData.each_race_result_id == race.id
        ).order_by(db.each_boat_data.EachBoatData.boat_number).all()

        features_list = []
        for boat_data in boat_data_list:
            features = self._extract_boat_features(
                boat_data, race, race_date, lookback_days
            )
            features_list.append(features)

        return pd.DataFrame(features_list)

    def _extract_boat_features(
        self,
        boat_data: db.each_boat_data.EachBoatData,
        race: db.each_race_results.EachRaceResult,
        race_date: dt.date,
        lookback_days: int
    ) -> Dict:
        """
        1艇分の特徴量を抽出

        Args:
            boat_data: 艇データ
            race: レースデータ
            race_date: レース日
            lookback_days: 過去成績を参照する日数

        Returns:
            Dict: 特徴量辞書
        """
        features = {}

        # 艇番
        features['boat_number'] = boat_data.boat_number

        # === 選手基本情報 ===
        player = boat_data.player

        # 選手の全国勝率・連対率（当日）
        player_national = self.session.query(db.player_national_win_rate.PlayerNationalWinRate).filter(
            db.player_national_win_rate.PlayerNationalWinRate.player_id == player.id,
            db.player_national_win_rate.PlayerNationalWinRate.race_date == race_date
        ).first()

        if player_national:
            features['player_national_win_rate'] = player_national.player_national_win_rate
            features['player_national_top2_rate'] = player_national.player_national_top2finish_rate
        else:
            features['player_national_win_rate'] = 0.0
            features['player_national_top2_rate'] = 0.0

        # 選手の地元勝率・連対率（当日）
        player_local = self.session.query(db.player_local_win_rate.PlayerLocalWinRate).filter(
            db.player_local_win_rate.PlayerLocalWinRate.player_id == player.id,
            db.player_local_win_rate.PlayerLocalWinRate.race_date == race_date
        ).first()

        if player_local:
            features['player_local_win_rate'] = player_local.player_local_win_rate
            features['player_local_top2_rate'] = player_local.player_local_top2finish_rate
        else:
            features['player_local_win_rate'] = 0.0
            features['player_local_top2_rate'] = 0.0

        # 選手の年齢・体重・級別
        player_data = self.session.query(db.player_data.PlayerData).filter(
            db.player_data.PlayerData.player_id == player.id,
            db.player_data.PlayerData.date == race_date
        ).first()

        if player_data:
            features['player_age'] = player_data.player_age
            features['player_weight'] = player_data.player_weight
            features['player_rank'] = self._encode_rank(player_data.rank.rank_name if player_data.rank else None)
        else:
            features['player_age'] = 30  # デフォルト値
            features['player_weight'] = 52  # デフォルト値
            features['player_rank'] = 2  # B1級

        # === モーター・ボート性能 ===
        motor = boat_data.motor
        motor_rate = self.session.query(db.motor_top2finish_rate.MotorTop2finishRate).filter(
            db.motor_top2finish_rate.MotorTop2finishRate.motor_id == motor.id,
            db.motor_top2finish_rate.MotorTop2finishRate.date == race_date
        ).first()

        features['motor_top2_rate'] = motor_rate.motor_top2finish_rate if motor_rate else 0.0

        boat = boat_data.boat
        boat_rate = self.session.query(db.boat_top2finish_rate.BoatTop2finishRate).filter(
            db.boat_top2finish_rate.BoatTop2finishRate.boat_id == boat.id,
            db.boat_top2finish_rate.BoatTop2finishRate.date == race_date
        ).first()

        features['boat_top2_rate'] = boat_rate.boat_top2finish_rate if boat_rate else 0.0

        # === レース条件 ===
        features['stadium_id'] = race.stadium_id
        features['weather_id'] = race.weather_id if race.weather_id else 0
        features['wind_direction_id'] = race.wind_direction_id if race.wind_direction_id else 0
        features['wind_speed'] = race.wind_speed if race.wind_speed else 0
        features['wave_height'] = race.wave_height if race.wave_height else 0

        # === 当日情報 ===
        features['sample_time'] = boat_data.sample_time if boat_data.sample_time else 0.0
        features['start_timing'] = boat_data.start_timing if boat_data.start_timing else 0.0
        features['starting_order'] = boat_data.starting_order if boat_data.starting_order else boat_data.boat_number

        # === 過去成績（直近lookback_days日間）===
        past_results = self._get_past_results(player.id, race_date, lookback_days)
        features.update(past_results)

        # === 目的変数（訓練時のみ）===
        if boat_data.order_of_arrival:
            features['target_top3'] = 1 if boat_data.order_of_arrival <= 3 else 0
            features['order_of_arrival'] = boat_data.order_of_arrival
        else:
            features['target_top3'] = None
            features['order_of_arrival'] = None

        return features

    def _get_past_results(
        self,
        player_id: int,
        race_date: dt.date,
        lookback_days: int
    ) -> Dict:
        """
        選手の過去成績を取得

        Args:
            player_id: 選手ID
            race_date: 基準日
            lookback_days: 遡る日数

        Returns:
            Dict: 過去成績特徴量
        """
        start_date = race_date - dt.timedelta(days=lookback_days)

        # 過去のレース結果を取得
        past_races = self.session.query(db.each_boat_data.EachBoatData).join(
            db.each_race_results.EachRaceResult,
            db.each_boat_data.EachBoatData.each_race_result_id == db.each_race_results.EachRaceResult.id
        ).filter(
            db.each_boat_data.EachBoatData.player_id == player_id,
            db.each_race_results.EachRaceResult.date >= start_date,
            db.each_race_results.EachRaceResult.date < race_date
        ).order_by(db.each_race_results.EachRaceResult.date.desc()).limit(20).all()

        if not past_races:
            return {
                'past_race_count': 0,
                'past_avg_arrival': 3.5,
                'past_win_rate': 0.0,
                'past_top2_rate': 0.0,
                'past_top3_rate': 0.0,
            }

        arrivals = [r.order_of_arrival for r in past_races if r.order_of_arrival and r.order_of_arrival <= 6]

        if not arrivals:
            return {
                'past_race_count': 0,
                'past_avg_arrival': 3.5,
                'past_win_rate': 0.0,
                'past_top2_rate': 0.0,
                'past_top3_rate': 0.0,
            }

        race_count = len(arrivals)
        return {
            'past_race_count': race_count,
            'past_avg_arrival': np.mean(arrivals),
            'past_win_rate': sum(1 for a in arrivals if a == 1) / race_count,
            'past_top2_rate': sum(1 for a in arrivals if a <= 2) / race_count,
            'past_top3_rate': sum(1 for a in arrivals if a <= 3) / race_count,
        }

    def _encode_rank(self, rank_name: Optional[str]) -> int:
        """
        級別を数値エンコード

        Args:
            rank_name: 級別名

        Returns:
            int: エンコード値（A1=0, A2=1, B1=2, B2=3）
        """
        rank_map = {
            'A1': 0,
            'A2': 1,
            'B1': 2,
            'B2': 3,
        }
        return rank_map.get(rank_name, 2)  # デフォルトB1

    def close(self):
        """セッションをクローズ"""
        if self.session:
            self.session.close()


if __name__ == "__main__":
    # テスト
    extractor = FeatureExtractor()

    # サンプルレースの特徴量を抽出
    print("特徴量抽出テスト")
    print("=" * 60)

    # 2020年4月1日の桐生競艇場(01)の第1レースを取得
    test_date = dt.date(2020, 4, 1)
    test_stadium = 1
    test_race_index = 1

    features_df = extractor.extract_race_features(
        race_date=test_date,
        stadium_id=test_stadium,
        race_index=test_race_index,
        lookback_days=90
    )

    if not features_df.empty:
        print(f"レース: {test_date} 場: {test_stadium} R{test_race_index}")
        print(f"特徴量数: {len(features_df.columns)}")
        print(f"艇数: {len(features_df)}")
        print("\n特徴量一覧:")
        for col in features_df.columns:
            print(f"  - {col}")
        print("\nデータサンプル:")
        print(features_df.head())
    else:
        print("データが見つかりませんでした")

    extractor.close()
