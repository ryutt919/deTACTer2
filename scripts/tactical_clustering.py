from pathlib import Path as _RepoPath
_REPO_ROOT = _RepoPath(__file__).resolve().parents[1].as_posix()

# =========================================================
# tactical_clustering.py
# deTACTer 프로젝트용 전술 클러스터링 모듈 (v5.9 Refactored)
# =========================================================
# 주요 기능:
# 1. 좌표 기반 또는 Transformer 임베딩 기반 클러스터링 지원
# 2. 팀별 독립적 클러스터링 (Team-aware Analysis)
# 3. OPTICS 알고리즘을 통한 가변 밀도 클러스터링
# =========================================================

import pandas as pd
import numpy as np
from sklearn.cluster import OPTICS
from sklearn.preprocessing import StandardScaler
import sys
import warnings
import yaml
import os
import argparse
from pathlib import Path

warnings.filterwarnings('ignore')

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# =========================================================
# 설정 및 경로 로드
# =========================================================
CONFIG_PATH = (_REPO_ROOT + '/config.yaml')
with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

VERSION = config['version']
BASE_DIR = _REPO_ROOT
REFINED_DIR = f"{BASE_DIR}/data/refined/{VERSION}"
OUTPUT_DIR = f"{REFINED_DIR}/"

def run_clustering(mode='coordinate', team_aware=False):
    print("=" * 60)
    print(f"deTACTer {VERSION} 전술 클러스터링")
    print(f" - 모드: {mode.upper()}")
    print(f" - 팀별 분석: {'활성화' if team_aware else '비활성화'}")
    print("=" * 60)

    # 1. 데이터 로드
    seq_df = pd.read_csv(f"{REFINED_DIR}/attack_sequences.csv", encoding='utf-8-sig')
    stats_df = pd.read_csv(f"{REFINED_DIR}/attack_sequences_stats.csv", encoding='utf-8-sig')
    
    # 2. 특징 행렬 준비
    if mode == 'embedding':
        emb_path = f"{BASE_DIR}/results/embeddings/{VERSION}/transformer_embeddings.npy"
        meta_path = f"{BASE_DIR}/results/embeddings/{VERSION}/transformer_metadata.csv"
        
        if not os.path.exists(emb_path):
            print(f"❌ 임베딩 파일을 찾을 수 없습니다: {emb_path}")
            return
            
        features = np.load(emb_path)
        meta_df = pd.read_csv(meta_path)
        features_df = pd.DataFrame(features)
        features_df['sequence_id'] = meta_df['sequence_id']
    else:
        # 기존 좌표 기반 로직 (생략 가능하나 유지)
        from tactical_clustering import prepare_coordinate_features
        features, valid_seq_ids = prepare_coordinate_features(seq_df, stats_df)
        features_df = pd.DataFrame(features)
        features_df['sequence_id'] = valid_seq_ids

    # 3. 클러스터링 수행
    merged_data = stats_df.merge(features_df, on='sequence_id', how='inner')
    
    final_labels = []
    
    if team_aware:
        teams = merged_data['team_name'].unique()
        print(f"팀별 클러스터링 시작 ({len(teams)}개 팀)...")
        
        global_cluster_offset = 0
        for team in teams:
            team_data = merged_data[merged_data['team_name'] == team].copy()
            if len(team_data) < 5: 
                print(f"  - {team}: 데이터 부족으로 스킵")
                continue
            
            X = team_data.drop(columns=['sequence_id', 'game_id', 'team_name', 'outcome_result', 'speed', 'distance', 'dt', 'period_id'])
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            optics = OPTICS(min_samples=3, xi=0.05)
            labels = optics.fit_predict(X_scaled)
            
            # 전역 ID 부여 (노이즈 -1 제외)
            team_data['cluster'] = np.where(labels >= 0, labels + global_cluster_offset, -1)
            if labels.max() >= 0:
                global_cluster_offset += (labels.max() + 1)
            
            final_labels.append(team_data[['sequence_id', 'cluster', 'team_name']])
            print(f"  - {team}: {len(set(labels[labels>=0]))}개 클러스터 식별")
    else:
        X = merged_data.drop(columns=['sequence_id', 'game_id', 'team_name', 'outcome_result', 'speed', 'distance', 'dt', 'period_id'])
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        optics = OPTICS(min_samples=5, xi=0.05)
        merged_data['cluster'] = optics.fit_predict(X_scaled)
        final_labels.append(merged_data[['sequence_id', 'cluster', 'team_name']])

    result_df = pd.concat(final_labels)
    
    # 4. 결과 저장
    result_df.to_csv(f"{REFINED_DIR}/cluster_labels.csv", index=False, encoding='utf-8-sig')
    
    # 통계 생성
    stats = merged_data.merge(result_df[['sequence_id', 'cluster']], on='sequence_id').groupby(['team_name', 'cluster']).agg({
        'sequence_id': 'count',
        'speed': 'mean',
        'outcome_result': lambda x: (x == 'success').mean()
    }).rename(columns={'sequence_id': 'count', 'speed': 'avg_tempo', 'outcome_result': 'success_rate'})
    
    stats.to_csv(f"{REFINED_DIR}/cluster_stats.csv", encoding='utf-8-sig')
    print(f"✅ 클러스터링 완료. 결과 저장: {REFINED_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', type=str, default='coordinate', choices=['coordinate', 'embedding'])
    parser.add_argument('--team', type=str, default='false')
    args = parser.parse_args()
    
    run_clustering(mode=args.mode, team_aware=(args.team.lower() == 'true'))
