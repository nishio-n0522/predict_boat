"""
階層ベイズモデル（Hierarchical Bayesian Model）

ボートレース予測用の階層構造を持つベイズモデル:
- 選手ランダム効果（individual difference）
- モーターランダム効果（motor performance）
- 競艇場ランダム効果（water characteristics）
- 固定効果（feature coefficients）
"""

import numpy as np
import pandas as pd
import pymc as pm
import arviz as az
import pickle
from typing import Dict, Optional, Tuple
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')


class HierarchicalBayesianModel:
    """
    階層ベイズモデル

    構造:
    logit(P(top3)) = α + θ_player + θ_motor + θ_stadium + X*β

    - θ_player ~ Normal(0, σ_player)  # 選手ランダム効果
    - θ_motor ~ Normal(0, σ_motor)    # モーターランダム効果
    - θ_stadium ~ Normal(0, σ_stadium) # 競艇場ランダム効果
    - β: 固定効果（特徴量の係数）
    """

    def __init__(
        self,
        n_players: int,
        n_motors: int,
        n_stadiums: int,
        n_features: int,
        feature_names: Optional[list] = None
    ):
        """
        初期化

        Args:
            n_players: 選手数
            n_motors: モーター数
            n_stadiums: 競艇場数
            n_features: 特徴量数
            feature_names: 特徴量名リスト
        """
        self.n_players = n_players
        self.n_motors = n_motors
        self.n_stadiums = n_stadiums
        self.n_features = n_features
        self.feature_names = feature_names or [f'feature_{i}' for i in range(n_features)]

        self.model = None
        self.trace = None
        self.player_id_map = {}
        self.motor_id_map = {}
        self.stadium_id_map = {}

    def build_model(
        self,
        X: np.ndarray,
        y: np.ndarray,
        player_ids: np.ndarray,
        motor_ids: np.ndarray,
        stadium_ids: np.ndarray
    ):
        """
        階層ベイズモデルを構築

        Args:
            X: 特徴量 (n_samples, n_features)
            y: 目的変数 (n_samples,) - 3着以内なら1, それ以外は0
            player_ids: 選手ID (n_samples,)
            motor_ids: モーターID (n_samples,)
            stadium_ids: 競艇場ID (n_samples,)
        """
        print("=" * 80)
        print("階層ベイズモデル構築")
        print("=" * 80)
        print(f"サンプル数: {len(y)}")
        print(f"選手数: {self.n_players}")
        print(f"モーター数: {self.n_motors}")
        print(f"競艇場数: {self.n_stadiums}")
        print(f"特徴量数: {self.n_features}")
        print()

        with pm.Model() as self.model:
            # ============================================
            # 1. Hyperpriors（階層の分散パラメータ）
            # ============================================
            sigma_player = pm.HalfCauchy('sigma_player', beta=2)
            sigma_motor = pm.HalfCauchy('sigma_motor', beta=2)
            sigma_stadium = pm.HalfCauchy('sigma_stadium', beta=1)

            # ============================================
            # 2. ランダム効果（階層構造）
            # ============================================
            # 選手ごとの本来の実力差
            player_effect = pm.Normal(
                'player_effect',
                mu=0,
                sigma=sigma_player,
                shape=self.n_players
            )

            # モーターごとの性能差
            motor_effect = pm.Normal(
                'motor_effect',
                mu=0,
                sigma=sigma_motor,
                shape=self.n_motors
            )

            # 競艇場ごとの特性差
            stadium_effect = pm.Normal(
                'stadium_effect',
                mu=0,
                sigma=sigma_stadium,
                shape=self.n_stadiums
            )

            # ============================================
            # 3. 固定効果（特徴量の係数）
            # ============================================
            beta = pm.Normal('beta', mu=0, sigma=1, shape=self.n_features)
            intercept = pm.Normal('intercept', mu=0, sigma=5)

            # ============================================
            # 4. 線形予測子
            # ============================================
            eta = (
                intercept
                + player_effect[player_ids]
                + motor_effect[motor_ids]
                + stadium_effect[stadium_ids]
                + pm.math.dot(X, beta)
            )

            # 3着以内に入る確率
            p = pm.math.sigmoid(eta)

            # ============================================
            # 5. 観測モデル
            # ============================================
            y_obs = pm.Bernoulli('y_obs', p=p, observed=y)

        print("✓ モデル構築完了")
        return self.model

    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        player_ids: np.ndarray,
        motor_ids: np.ndarray,
        stadium_ids: np.ndarray,
        draws: int = 2000,
        tune: int = 2000,
        chains: int = 4,
        cores: int = 4,
        target_accept: float = 0.9
    ):
        """
        モデルをサンプリング（訓練）

        Args:
            X: 特徴量
            y: 目的変数
            player_ids: 選手ID
            motor_ids: モーターID
            stadium_ids: 競艇場ID
            draws: サンプリング数
            tune: チューニング数
            chains: チェーン数
            cores: 並列コア数
            target_accept: 受容率目標
        """
        # モデル構築
        if self.model is None:
            self.build_model(X, y, player_ids, motor_ids, stadium_ids)

        print("\n" + "=" * 80)
        print("MCMC サンプリング開始")
        print("=" * 80)
        print(f"Draws: {draws}")
        print(f"Tune: {tune}")
        print(f"Chains: {chains}")
        print(f"Cores: {cores}")
        print()

        # サンプリング
        with self.model:
            self.trace = pm.sample(
                draws=draws,
                tune=tune,
                chains=chains,
                cores=cores,
                target_accept=target_accept,
                return_inferencedata=True,
                random_seed=42
            )

        print("\n" + "=" * 80)
        print("サンプリング完了")
        print("=" * 80)

        # 収束診断
        self._print_diagnostics()

        return self.trace

    def _print_diagnostics(self):
        """収束診断を表示"""
        if self.trace is None:
            print("トレースが存在しません")
            return

        print("\n【収束診断】")
        print("-" * 80)

        # R-hat（1.01以下が理想）
        summary = az.summary(self.trace, var_names=['intercept', 'beta', 'sigma_player', 'sigma_motor', 'sigma_stadium'])
        print(summary[['mean', 'sd', 'hdi_3%', 'hdi_97%', 'r_hat', 'ess_bulk']])

        # 警告
        rhat_max = summary['r_hat'].max()
        if rhat_max > 1.05:
            print(f"\n⚠ 警告: R-hat が高い変数があります（最大: {rhat_max:.3f}）")
            print("  → サンプリング数を増やすことを推奨します")
        else:
            print(f"\n✓ 収束良好（R-hat最大値: {rhat_max:.3f}）")

    def predict_proba(
        self,
        X: np.ndarray,
        player_ids: np.ndarray,
        motor_ids: np.ndarray,
        stadium_ids: np.ndarray,
        return_samples: bool = False
    ) -> np.ndarray:
        """
        3着以内に入る確率を予測

        Args:
            X: 特徴量
            player_ids: 選手ID
            motor_ids: モーターID
            stadium_ids: 競艇場ID
            return_samples: サンプル全体を返すか（True）、平均のみ返すか（False）

        Returns:
            np.ndarray: 予測確率
                - return_samples=False: (n_samples,)
                - return_samples=True: (n_mcmc_samples, n_samples)
        """
        if self.trace is None:
            raise ValueError("モデルが訓練されていません")

        # 事後分布からパラメータを取得
        posterior = self.trace.posterior

        intercept_samples = posterior['intercept'].values.flatten()  # (n_samples,)
        beta_samples = posterior['beta'].values.reshape(-1, self.n_features)  # (n_samples, n_features)
        player_effect_samples = posterior['player_effect'].values.reshape(-1, self.n_players)
        motor_effect_samples = posterior['motor_effect'].values.reshape(-1, self.n_motors)
        stadium_effect_samples = posterior['stadium_effect'].values.reshape(-1, self.n_stadiums)

        n_samples = len(intercept_samples)
        n_data = len(X)

        # 全サンプルでの予測
        all_predictions = np.zeros((n_samples, n_data))

        for i in range(n_samples):
            eta = (
                intercept_samples[i]
                + player_effect_samples[i, player_ids]
                + motor_effect_samples[i, motor_ids]
                + stadium_effect_samples[i, stadium_ids]
                + X @ beta_samples[i]
            )
            all_predictions[i] = 1 / (1 + np.exp(-eta))  # sigmoid

        if return_samples:
            return all_predictions  # (n_mcmc_samples, n_data)
        else:
            return all_predictions.mean(axis=0)  # (n_data,)

    def get_random_effects(self) -> Dict[str, np.ndarray]:
        """
        ランダム効果の事後平均を取得

        Returns:
            Dict: {'player_effect': array, 'motor_effect': array, 'stadium_effect': array}
        """
        if self.trace is None:
            raise ValueError("モデルが訓練されていません")

        posterior = self.trace.posterior

        return {
            'player_effect': posterior['player_effect'].mean(dim=['chain', 'draw']).values,
            'motor_effect': posterior['motor_effect'].mean(dim=['chain', 'draw']).values,
            'stadium_effect': posterior['stadium_effect'].mean(dim=['chain', 'draw']).values
        }

    def get_hyperparameters(self) -> Dict[str, float]:
        """
        階層のばらつき（σ）を取得

        Returns:
            Dict: {'sigma_player': float, 'sigma_motor': float, 'sigma_stadium': float}
        """
        if self.trace is None:
            raise ValueError("モデルが訓練されていません")

        posterior = self.trace.posterior

        return {
            'sigma_player': float(posterior['sigma_player'].mean()),
            'sigma_motor': float(posterior['sigma_motor'].mean()),
            'sigma_stadium': float(posterior['sigma_stadium'].mean())
        }

    def save(self, path: str):
        """
        モデルを保存

        Args:
            path: 保存先パス
        """
        if self.trace is None:
            raise ValueError("モデルが訓練されていません")

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        # トレースを保存
        trace_path = path.parent / f"{path.stem}_trace.nc"
        self.trace.to_netcdf(trace_path)

        # メタデータを保存
        metadata = {
            'n_players': self.n_players,
            'n_motors': self.n_motors,
            'n_stadiums': self.n_stadiums,
            'n_features': self.n_features,
            'feature_names': self.feature_names,
            'player_id_map': self.player_id_map,
            'motor_id_map': self.motor_id_map,
            'stadium_id_map': self.stadium_id_map
        }

        with open(path, 'wb') as f:
            pickle.dump(metadata, f)

        print(f"モデルを保存しました: {path}")
        print(f"トレースを保存しました: {trace_path}")

    def load(self, path: str):
        """
        モデルを読み込み

        Args:
            path: モデルパス
        """
        path = Path(path)

        # メタデータを読み込み
        with open(path, 'rb') as f:
            metadata = pickle.load(f)

        self.n_players = metadata['n_players']
        self.n_motors = metadata['n_motors']
        self.n_stadiums = metadata['n_stadiums']
        self.n_features = metadata['n_features']
        self.feature_names = metadata['feature_names']
        self.player_id_map = metadata['player_id_map']
        self.motor_id_map = metadata['motor_id_map']
        self.stadium_id_map = metadata['stadium_id_map']

        # トレースを読み込み
        trace_path = path.parent / f"{path.stem}_trace.nc"
        self.trace = az.from_netcdf(trace_path)

        print(f"モデルを読み込みました: {path}")
        print(f"トレースを読み込みました: {trace_path}")


if __name__ == "__main__":
    # テスト
    print("=" * 80)
    print("階層ベイズモデル テスト")
    print("=" * 80)

    # ダミーデータ
    np.random.seed(42)

    n_samples = 1000
    n_players = 50
    n_motors = 30
    n_stadiums = 5
    n_features = 10

    # 特徴量
    X = np.random.randn(n_samples, n_features).astype(np.float64)

    # ID
    player_ids = np.random.randint(0, n_players, n_samples)
    motor_ids = np.random.randint(0, n_motors, n_samples)
    stadium_ids = np.random.randint(0, n_stadiums, n_samples)

    # 目的変数（ダミー）
    y = np.random.binomial(1, 0.5, n_samples)

    # モデル作成
    model = HierarchicalBayesianModel(
        n_players=n_players,
        n_motors=n_motors,
        n_stadiums=n_stadiums,
        n_features=n_features
    )

    # 訓練（テストなので少ないサンプル数）
    model.fit(
        X, y,
        player_ids, motor_ids, stadium_ids,
        draws=100,
        tune=100,
        chains=2
    )

    # 予測
    probs = model.predict_proba(X[:10], player_ids[:10], motor_ids[:10], stadium_ids[:10])
    print(f"\n予測確率サンプル: {probs}")

    # ランダム効果
    effects = model.get_random_effects()
    print(f"\n選手効果（最初の5人）: {effects['player_effect'][:5]}")

    # ハイパーパラメータ
    hyper = model.get_hyperparameters()
    print(f"\nばらつき: {hyper}")

    print("\n✅ テスト成功")
