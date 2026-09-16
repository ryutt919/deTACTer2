from pathlib import Path as _RepoPath
_REPO_ROOT = _RepoPath(__file__).resolve().parents[1].as_posix()

# =========================================================
# team_based_clustering.py
# v5.6 Transformer 임베딩 기반 팀별 독립 클러스터링
# =========================================================
# 주요 기능:
# 1. Transformer 임베딩을 팀별로 분할
# 2. 각 팀에 대해 독립적으로 OPTICS 클러스터링 수행
# 3. 팀별 클러스터 결과를 개별 파일로 저장
# =========================================================

import pandas as pd
import numpy as np
import os
import sys
import yaml
from sklearn.cluster import OPTICS

# 한글 출력 설정
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

# =========================================================
# 설정 로드
# =========================================================
BASE_DIR = _REPO_ROOT
CONFIG_PATH = os.path.join(BASE_DIR, 'config.yaml')

with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

VERSION = config['version']
REFINED_DIR = os.path.join(BASE_DIR, 'data', 'refined', VERSION)
EMBEDDINGS_DIR = os.path.join(BASE_DIR, 'results', 'embeddings', VERSION)
OUTPUT_DIR = os.path.join(BASE_DIR, 'results', 'clustering', VERSION, 'transformer')

os.makedirs(OUTPUT_DIR, exist_ok=True)

# =========================================================
# 팀별 클러스터링 함수
# =========================================================
def perform_team_clustering(version='v5.6'):
    """
    v5.6 Transformer 임베딩을 팀별로 분할하여 클러스터링을 수행합니다.
    """
    print(f"=" * 60)
    print(f"팀별 Transformer 클러스터링 시작 (버전: {version})")
    print(f"=" * 60)
    
    # 1. 임베딩 및 메타데이터 로드
    embeddings_path = os.path.join(EMBEDDINGS_DIR, 'transformer_embeddings.npy')
    metadata_path = os.path.join(EMBEDDINGS_DIR, 'transformer_metadata.csv')
    sequences_path = os.path.join(REFINED_DIR, 'attack_sequences.csv')
    
    if not os.path.exists(embeddings_path):
        print(f"[오류] 임베딩 파일을 찾을 수 없습니다: {embeddings_path}")
        return
    
    print(f"\n[1/4] 데이터 로드 중...")
    embeddings = np.load(embeddings_path)
    metadata_df = pd.read_csv(metadata_path, encoding='utf-8-sig')
    sequences_df = pd.read_csv(sequences_path, encoding='utf-8-sig')
    
    # [Fix] 메타데이터 중복 제거 (정합성 강화)
    initial_meta_count = len(metadata_df)
    metadata_df = metadata_df.drop_duplicates(subset=['sequence_id']).reset_index(drop=True)
    if len(metadata_df) < initial_meta_count:
        print(f"  ⚠️ 메타데이터 중복 발견: {initial_meta_count} -> {len(metadata_df)}")
    
    # 메타데이터에 원본 임베딩 인덱스 추가 (조인 후에 올바른 임베딩을 가져오기 위해 필수)
    metadata_df['embedding_idx'] = range(len(metadata_df))
    
    # 2. 메타데이터와 시퀀스 데이터 조인 (팀명 정보 획득)
    print(f"[2/4] 팀 정보 매칭 중...")
    # [Fix] 시퀀스 데이터에서 ID별 팀명 고유성 확보
    sequences_unique = sequences_df.groupby('sequence_id').first().reset_index()
    
    merged_df = metadata_df.merge(
        sequences_unique[['sequence_id', 'team_name_ko']],
        on='sequence_id',
        how='left'
    )
    
    # [Fix] 최종 조인 후에도 중복 발생 여부 재확인 (방어적 코딩)
    merged_df = merged_df.drop_duplicates(subset=['sequence_id'])
    
    # 팀명이 없는 경우 제외
    merged_df = merged_df.dropna(subset=['team_name_ko'])
    
    # 3. 팀별로 그룹화하여 클러스터링 수행
    teams = merged_df['team_name_ko'].unique()
    print(f"[3/4] 총 {len(teams)}개 팀 발견")
    
    for team_name in teams:
        print(f"\n▶️ [{team_name}] 클러스터링 시작...")
        
        # 해당 팀의 데이터만 필터링
        team_data = merged_df[merged_df['team_name_ko'] == team_name].copy()
        
        # embedding_idx를 사용하여 올바른 임베딩 추출
        emb_indices = team_data['embedding_idx'].tolist()
        team_embeddings = embeddings[emb_indices]
        
        if len(team_embeddings) < 5:
            print(f"  ⚠️ 데이터 부족 (샘플 수: {len(team_embeddings)}), 스킵")
            continue
        
        # OPTICS 클러스터링
        # 팀별 데이터가 적을 수 있으므로 min_samples는 데이터 크기에 맞춰 조정하되 config 값을 상한으로 사용
        current_min_samples = min(config['clustering'].get('min_samples', 3), len(team_embeddings) // 2)
        current_min_samples = max(2, current_min_samples) # 최소 2개는 되어야 함
        
        optics = OPTICS(min_samples=current_min_samples, xi=config['clustering'].get('xi', 0.01), metric='euclidean')
        cluster_labels = optics.fit_predict(team_embeddings)
        
        # 클러스터 레이블 추가
        team_data['cluster'] = cluster_labels
        
        # 클러스터 통계
        n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
        n_noise = list(cluster_labels).count(-1)
        print(f"  ✅ 클러스터 수: {n_clusters}, 노이즈: {n_noise}")
        
        # 팀별 디렉토리 생성 및 저장
        team_output_dir = os.path.join(OUTPUT_DIR, team_name)
        os.makedirs(team_output_dir, exist_ok=True)
        
        output_path = os.path.join(team_output_dir, 'team_clusters.csv')
        team_data[['sequence_id', 'cluster']].to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"  💾 저장 완료: {output_path}")
    
    print(f"\n{'='*60}")
    print(f"모든 팀별 클러스터링 완료!")
    print(f"{'='*60}")

# =========================================================
# 메인 실행
# =========================================================
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="팀별 Transformer 클러스터링")
    parser.add_argument("--version", type=str, default="v5.6", help="데이터 버전")
    args = parser.parse_args()
    
    perform_team_clustering(version=args.version)
