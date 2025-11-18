"""
階層ベイズモデル訓練スクリプト

選手・モーター・競艇場の階層構造を持つベイズモデルを訓練
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import pickle

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from ml_models.hierarchical_bayesian_model import HierarchicalBayesianModel


def prepare_bayesian_data(dataset_path: str):
    """
    階層ベイズモデル用にデータを準備

    Args:
        dataset_path: データセットパス

    Returns:
        tuple: (X, y, player_ids, motor_ids, stadium_ids, mappings, feature_names)
    """
    print("データ読み込み中...")
    df = pd.read_csv(dataset_path)

    print(f"データサイズ: {len(df)} 行")

    # 目的変数がないデータを除外
    df = df[df['target_top3'].notna()].copy()

    print(f"有効データ: {len(df)} 行")

    # ============================================
    # 1. 特徴量と目的変数を分離
    # ============================================
    exclude_cols = [
        'target_top3', 'order_of_arrival',
        'race_date', 'stadium_id', 'race_index', 'race_name',
        'boat_number'  # 艇番は階層には含めない
    ]

    # プレイヤーID、モーターID、競艇場IDを取得するための列を追加で除外
    id_cols = []

    feature_cols = [col for col in df.columns if col not in exclude_cols + id_cols]

    X = df[feature_cols].copy()
    y = df['target_top3'].copy().values

    # ============================================
    # 2. 選手ID・モーターID・競艇場IDの作成
    # ============================================
    # ※ 既存データセットには直接の選手IDなどがないため、
    # 選手勝率などから推定するか、元のDBから取得する必要がある

    # 簡易版: 競艇場IDは既にあるのでそれを使用
    # 選手・モーターは一意なIDに変換する必要がある

    # ここでは簡易的に、レース単位でグループ化してID化する
    # （実際のシステムでは、元のDBから選手登番、モーター番号を取得すべき）

    # レースごとにグループ化
    df['race_group'] = df['race_date'].astype(str) + '_' + df['stadium_id'].astype(str) + '_' + df['race_index'].astype(str)

    # 仮想的な選手IDを作成（同じ選手勝率なら同じ選手と仮定）
    # 注: これは簡易版の実装。実際は選手登番を使用すべき
    df['player_virtual_id'] = pd.factorize(df['player_national_win_rate'].round(2))[0]

    # モーターIDも同様（モーター連対率から推定）
    df['motor_virtual_id'] = pd.factorize(df['motor_top2_rate'].round(2))[0]

    # 競艇場IDはそのまま使用
    stadium_ids = df['stadium_id'].values

    # マッピング作成
    player_mapping = {i: i for i in range(df['player_virtual_id'].max() + 1)}
    motor_mapping = {i: i for i in range(df['motor_virtual_id'].max() + 1)}
    stadium_mapping = {i: i for i in range(int(stadium_ids.max()) + 1)}

    n_players = len(player_mapping)
    n_motors = len(motor_mapping)
    n_stadiums = len(stadium_mapping)

    player_ids = df['player_virtual_id'].values
    motor_ids = df['motor_virtual_id'].values

    print()
    print("ID統計:")
    print(f"  ユニーク選手数: {n_players}")
    print(f"  ユニークモーター数: {n_motors}")
    print(f"  ユニーク競艇場数: {n_stadiums}")
    print()

    # ============================================
    # 3. 特徴量の標準化
    # ============================================
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X.fillna(0))

    # ============================================
    # 4. メタデータ
    # ============================================
    mappings = {
        'player_mapping': player_mapping,
        'motor_mapping': motor_mapping,
        'stadium_mapping': stadium_mapping,
        'scaler': scaler
    }

    return X_scaled, y, player_ids, motor_ids, stadium_ids, mappings, feature_cols


def main():
    import argparse

    parser = argparse.ArgumentParser(description="階層ベイズモデル訓練")
    parser.add_argument("--dataset", type=str, default="data/processed/training_dataset.csv")
    parser.add_argument("--output", type=str, default="models_trained/bayesian_model.pkl")
    parser.add_argument("--draws", type=int, default=2000, help="MCMCサンプル数")
    parser.add_argument("--tune", type=int, default=2000, help="チューニング数")
    parser.add_argument("--chains", type=int, default=4, help="チェーン数")
    parser.add_argument("--cores", type=int, default=4, help="並列コア数")
    parser.add_argument("--sample-size", type=int, default=10000, help="訓練に使用するサンプル数（全データは重いため）")

    args = parser.parse_args()

    # データ準備
    X, y, player_ids, motor_ids, stadium_ids, mappings, feature_names = prepare_bayesian_data(
        args.dataset
    )

    # サンプリング（計算時間短縮のため一部のみ使用）
    if args.sample_size and args.sample_size < len(X):
        print(f"\n訓練データを {args.sample_size} サンプルに制限します")
        indices = np.random.choice(len(X), args.sample_size, replace=False)
        X = X[indices]
        y = y[indices]
        player_ids = player_ids[indices]
        motor_ids = motor_ids[indices]
        stadium_ids = stadium_ids[indices]

    n_players = len(mappings['player_mapping'])
    n_motors = len(mappings['motor_mapping'])
    n_stadiums = len(mappings['stadium_mapping'])
    n_features = X.shape[1]

    print("\n" + "=" * 80)
    print("モデル訓練開始")
    print("=" * 80)
    print(f"訓練サンプル数: {len(X)}")
    print(f"正例率: {y.mean():.3f}")
    print()

    # モデル作成
    model = HierarchicalBayesianModel(
        n_players=n_players,
        n_motors=n_motors,
        n_stadiums=n_stadiums,
        n_features=n_features,
        feature_names=feature_names
    )

    model.player_id_map = mappings['player_mapping']
    model.motor_id_map = mappings['motor_mapping']
    model.stadium_id_map = mappings['stadium_mapping']

    # 訓練
    try:
        model.fit(
            X, y,
            player_ids, motor_ids, stadium_ids,
            draws=args.draws,
            tune=args.tune,
            chains=args.chains,
            cores=args.cores
        )
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        print("\nヒント: サンプル数やチェーン数を減らしてみてください")
        return

    # ランダム効果の確認
    print("\n" + "=" * 80)
    print("ランダム効果の分析")
    print("=" * 80)

    effects = model.get_random_effects()

    print("\n【選手効果】")
    print(f"  平均: {effects['player_effect'].mean():.3f}")
    print(f"  標準偏差: {effects['player_effect'].std():.3f}")
    print(f"  最大: {effects['player_effect'].max():.3f}")
    print(f"  最小: {effects['player_effect'].min():.3f}")

    print("\n【モーター効果】")
    print(f"  平均: {effects['motor_effect'].mean():.3f}")
    print(f"  標準偏差: {effects['motor_effect'].std():.3f}")
    print(f"  最大: {effects['motor_effect'].max():.3f}")
    print(f"  最小: {effects['motor_effect'].min():.3f}")

    print("\n【競艇場効果】")
    print(f"  平均: {effects['stadium_effect'].mean():.3f}")
    print(f"  標準偏差: {effects['stadium_effect'].std():.3f}")

    # ハイパーパラメータの確認
    print("\n【階層のばらつき（σ）】")
    hyper = model.get_hyperparameters()
    print(f"  選手間のばらつき (σ_player): {hyper['sigma_player']:.3f}")
    print(f"  モーター間のばらつき (σ_motor): {hyper['sigma_motor']:.3f}")
    print(f"  競艇場間のばらつき (σ_stadium): {hyper['sigma_stadium']:.3f}")

    # モデル保存
    model.save(args.output)

    # Scalerも保存
    scaler_path = Path(args.output).parent / "bayesian_scaler.pkl"
    with open(scaler_path, 'wb') as f:
        pickle.dump(mappings['scaler'], f)
    print(f"Scalerを保存しました: {scaler_path}")

    print("\n✅ 訓練完了")


if __name__ == "__main__":
    main()
