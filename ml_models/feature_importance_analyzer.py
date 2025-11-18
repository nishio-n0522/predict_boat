"""
特徴量重要度分析モジュール

Transformerモデルの特徴量重要度を様々な手法で分析：
- Attention Weights
- SHAP (Shapley Additive Explanations)
- Integrated Gradients
"""

import torch
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Optional, Dict
from pathlib import Path


class FeatureImportanceAnalyzer:
    """
    特徴量重要度分析器

    複数の手法で特徴量の重要度を分析
    """

    def __init__(
        self,
        model,
        feature_names: List[str],
        device: str = None
    ):
        """
        初期化

        Args:
            model: Transformerモデル
            feature_names: 特徴量名のリスト
            device: デバイス
        """
        self.model = model
        self.feature_names = feature_names
        self.n_features = len(feature_names)

        if device is None:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = torch.device(device)

    def analyze_attention_weights(
        self,
        X: np.ndarray,
        boat_idx: int = 0
    ) -> Dict[str, np.ndarray]:
        """
        Attention Weightsを分析

        Args:
            X: 入力特徴量 (n_races, 6, n_features)
            boat_idx: 分析対象の艇番（0-5）

        Returns:
            Dict: 分析結果
        """
        self.model.eval()

        with torch.no_grad():
            X_tensor = torch.tensor(X, dtype=torch.float32).to(self.device)
            _, attention_info = self.model(X_tensor, return_attention=True)

        results = {}

        # Feature Gate Weightsを取得
        if attention_info and 'feature_gates' is not None and attention_info['feature_gates'] is not None:
            feature_gates = attention_info['feature_gates'].cpu().numpy()

            # 指定艇の平均ゲート重み
            boat_gates = feature_gates[:, boat_idx, :]  # (n_races, n_features)
            avg_gates = np.mean(boat_gates, axis=0)  # (n_features,)

            results['feature_gate_weights'] = avg_gates

        return results

    def analyze_integrated_gradients(
        self,
        X: np.ndarray,
        n_steps: int = 50
    ) -> np.ndarray:
        """
        Integrated Gradientsで重要度を計算

        Args:
            X: 入力特徴量 (n_races, 6, n_features)
            n_steps: 積分ステップ数

        Returns:
            np.ndarray: 各特徴量の重要度 (n_features,)
        """
        self.model.eval()

        X_tensor = torch.tensor(X, dtype=torch.float32).to(self.device)
        X_tensor.requires_grad = True

        # ベースライン（ゼロベクトル）
        baseline = torch.zeros_like(X_tensor)

        # 積分パスを作成
        alphas = torch.linspace(0, 1, n_steps).to(self.device)

        gradients_list = []

        for alpha in alphas:
            # 補間
            interpolated = baseline + alpha * (X_tensor - baseline)
            interpolated.requires_grad = True

            # 順伝播
            probs, _ = self.model(interpolated, return_attention=False)

            # 全艇の平均確率を目的関数とする
            target = probs.mean()

            # 逆伝播
            target.backward()

            # 勾配を保存
            gradients_list.append(interpolated.grad.detach().clone())

            # 勾配をクリア
            interpolated.grad.zero_()

        # 勾配の平均
        avg_gradients = torch.stack(gradients_list).mean(dim=0)

        # Integrated Gradients
        integrated_grads = (X_tensor - baseline) * avg_gradients

        # 全レース・全艇での平均重要度を計算
        importance = integrated_grads.abs().mean(dim=(0, 1)).cpu().numpy()

        return importance

    def analyze_shap_approximation(
        self,
        X: np.ndarray,
        n_samples: int = 100
    ) -> np.ndarray:
        """
        SHAP風の近似的重要度を計算（簡易版）

        注意: 完全なSHAPではなく、計算コストを抑えた近似

        Args:
            X: 入力特徴量 (n_races, 6, n_features)
            n_samples: サンプル数

        Returns:
            np.ndarray: 各特徴量の重要度 (n_features,)
        """
        self.model.eval()

        # ベースライン予測（全特徴量をゼロにした場合）
        X_baseline = np.zeros_like(X)

        with torch.no_grad():
            X_baseline_tensor = torch.tensor(X_baseline, dtype=torch.float32).to(self.device)
            baseline_probs, _ = self.model(X_baseline_tensor, return_attention=False)
            baseline_probs = baseline_probs.cpu().numpy()

        # 元の予測
        with torch.no_grad():
            X_tensor = torch.tensor(X, dtype=torch.float32).to(self.device)
            original_probs, _ = self.model(X_tensor, return_attention=False)
            original_probs = original_probs.cpu().numpy()

        # 各特徴量を個別にマスクして影響を測定
        feature_importance = np.zeros(self.n_features)

        for feat_idx in range(self.n_features):
            # 特徴量をマスク
            X_masked = X.copy()
            X_masked[:, :, feat_idx] = 0

            with torch.no_grad():
                X_masked_tensor = torch.tensor(X_masked, dtype=torch.float32).to(self.device)
                masked_probs, _ = self.model(X_masked_tensor, return_attention=False)
                masked_probs = masked_probs.cpu().numpy()

            # 予測の変化量を重要度とする
            importance = np.abs(original_probs - masked_probs).mean()
            feature_importance[feat_idx] = importance

        return feature_importance

    def plot_feature_importance(
        self,
        importance_dict: Dict[str, np.ndarray],
        top_n: int = 20,
        save_path: Optional[str] = None
    ):
        """
        特徴量重要度をプロット

        Args:
            importance_dict: {'手法名': 重要度配列} の辞書
            top_n: 表示する上位N個
            save_path: 保存先パス
        """
        n_methods = len(importance_dict)

        fig, axes = plt.subplots(1, n_methods, figsize=(8 * n_methods, 8))

        if n_methods == 1:
            axes = [axes]

        for ax, (method_name, importance) in zip(axes, importance_dict.items()):
            # DataFrameを作成
            df = pd.DataFrame({
                'feature': self.feature_names,
                'importance': importance
            }).sort_values('importance', ascending=False).head(top_n)

            # プロット
            sns.barplot(data=df, x='importance', y='feature', ax=ax)
            ax.set_title(f'{method_name} (Top {top_n})', fontsize=14)
            ax.set_xlabel('Importance', fontsize=12)
            ax.set_ylabel('Feature', fontsize=12)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"特徴量重要度を保存しました: {save_path}")
        else:
            plt.show()

    def analyze_all_methods(
        self,
        X: np.ndarray,
        save_dir: Optional[str] = None
    ) -> Dict[str, np.ndarray]:
        """
        全ての手法で特徴量重要度を分析

        Args:
            X: 入力特徴量 (n_races, 6, n_features)
            save_dir: 結果保存ディレクトリ

        Returns:
            Dict: {'手法名': 重要度配列} の辞書
        """
        print("=" * 80)
        print("特徴量重要度分析開始")
        print("=" * 80)

        results = {}

        # 1. Attention Weights
        print("\n1. Attention Weights分析中...")
        try:
            attention_results = self.analyze_attention_weights(X, boat_idx=0)
            if 'feature_gate_weights' in attention_results:
                results['Feature Gate Weights'] = attention_results['feature_gate_weights']
                print(f"  ✓ 完了")
        except Exception as e:
            print(f"  ✗ エラー: {e}")

        # 2. Integrated Gradients
        print("\n2. Integrated Gradients分析中...")
        try:
            ig_importance = self.analyze_integrated_gradients(X, n_steps=50)
            results['Integrated Gradients'] = ig_importance
            print(f"  ✓ 完了")
        except Exception as e:
            print(f"  ✗ エラー: {e}")

        # 3. SHAP Approximation
        print("\n3. SHAP Approximation分析中...")
        try:
            shap_importance = self.analyze_shap_approximation(X, n_samples=100)
            results['SHAP Approximation'] = shap_importance
            print(f"  ✓ 完了")
        except Exception as e:
            print(f"  ✗ エラー: {e}")

        print("\n" + "=" * 80)
        print("分析完了")
        print("=" * 80)

        # 結果を表示
        print("\n【特徴量重要度トップ10】")
        for method_name, importance in results.items():
            print(f"\n{method_name}:")
            top_indices = np.argsort(importance)[::-1][:10]
            for rank, idx in enumerate(top_indices, 1):
                print(f"  {rank}. {self.feature_names[idx]}: {importance[idx]:.4f}")

        # プロット保存
        if save_dir and results:
            save_dir = Path(save_dir)
            save_dir.mkdir(parents=True, exist_ok=True)
            save_path = save_dir / "feature_importance_comparison.png"
            self.plot_feature_importance(results, top_n=20, save_path=str(save_path))

        return results


if __name__ == "__main__":
    from ml_models.transformer_model import BoatRaceTransformer

    # テスト
    print("=" * 80)
    print("特徴量重要度分析 テスト")
    print("=" * 80)

    # パラメータ
    batch_size = 10
    n_features = 20

    # ダミーデータ
    X = np.random.randn(batch_size, 6, n_features).astype(np.float32)

    # 特徴量名
    feature_names = [f'feature_{i}' for i in range(n_features)]

    # モデル作成
    model = BoatRaceTransformer(
        n_features=n_features,
        d_model=64,
        nhead=4,
        num_layers=2,
        use_feature_gating=True
    )

    # 分析器作成
    analyzer = FeatureImportanceAnalyzer(
        model=model,
        feature_names=feature_names
    )

    # 全手法で分析
    results = analyzer.analyze_all_methods(X)

    print("\n✅ テスト成功")
