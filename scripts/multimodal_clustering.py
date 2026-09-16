from pathlib import Path as _RepoPath
_REPO_ROOT = _RepoPath(__file__).resolve().parents[1].as_posix()

# =========================================================
# multimodal_clustering.py
# Coordinates, GRU, Transformer 임베딩 기반 각각의 클러스터링 수행
# =========================================================

import pandas as pd
import numpy as np
from sklearn.cluster import OPTICS
from sklearn.preprocessing import StandardScaler
import yaml
import os
import argparse
from pathlib import Path
import sys

# 터미널 한글 출력 인코딩 설정
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

# =========================================================
# 설정
# =========================================================
CONFIG_PATH = (_REPO_ROOT + '/config.yaml')
with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

BASE_DIR = _REPO_ROOT

# =========================================================
# 1. Coordinate-based Clustering (기존 logic 유지)
# =========================================================
def extract_trajectory_features(path):
    if path is None or len(path) < 2:
        return None
    features = []
    features.extend([path[0][0], path[0][1]])  # start_x, start_y
    features.extend([path[-1][0], path[-1][1]])  # end_x, end_y
    features.extend([np.mean(path[:, 0]), np.mean(path[:, 1])])
    features.extend([np.std(path[:, 0]), np.std(path[:, 1])])
    distances = np.sqrt(np.sum(np.diff(path, axis=0)**2, axis=1))
    features.append(np.sum(distances))
    direct_dist = np.sqrt((path[-1][0] - path[0][0])**2 + (path[-1][1] - path[0][1])**2)
    features.append(direct_dist)
    features.append(direct_dist / (np.sum(distances) + 1e-8))
    return np.array(features)

def run_coord_clustering(version, seq_df, stats_df):
    print(f"[{version}] Coordinate-based 클러스터링 실행 중...")
    
    unique_seqs = stats_df['sequence_id'].unique()
    features_list = []
    valid_seq_ids = []
    
    for seq_id in unique_seqs:
        seq = seq_df[seq_df['sequence_id'] == seq_id].sort_values('seq_position', ascending=False)
        if len(seq) >= 3:
            coords = [(seq.iloc[0]['start_x'], seq.iloc[0]['start_y']),
                      (seq.iloc[0]['end_x'], seq.iloc[0]['end_y'])]
            for i in range(1, len(seq)):
                coords.append((seq.iloc[i]['end_x'], seq.iloc[i]['end_y']))
            
            features = extract_trajectory_features(np.array(coords))
            if features is not None:
                features_list.append(features)
                valid_seq_ids.append(seq_id)
    
    X = np.array(features_list)
    X_scaled = StandardScaler().fit_transform(X)
    
    # Grid logic (optional, but keeping it simple for verification)
    optics = OPTICS(min_samples=5, xi=0.03, metric='euclidean', n_jobs=-1)
    labels = optics.fit_predict(X_scaled)
    
    res_df = pd.DataFrame({'sequence_id': valid_seq_ids, 'cluster': labels})
    output_path = f"{BASE_DIR}/data/refined/{version}/coord_clusters.csv"
    res_df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"✅ 저장 완료: {output_path}")

# =========================================================
# 2. Embedding-based Clustering (GRU / Transformer)
# =========================================================
def run_embedding_clustering(version, model_type):
    print(f"[{version}] {model_type.upper()} 임베딩 클러스터링 실행 중...")
    
    emb_path = f"{BASE_DIR}/results/embeddings/{version}/{model_type}_embeddings.npy"
    meta_path = f"{BASE_DIR}/results/embeddings/{version}/{model_type}_metadata.csv"
    
    if not os.path.exists(emb_path) or not os.path.exists(meta_path):
        print(f"⚠️ {model_type.upper()} 임베딩 파일이 없습니다. 스킵합니다.")
        return
        
    X = np.load(emb_path)
    meta = pd.read_csv(meta_path)
    
    # OPTICS 클러스터링
    optics = OPTICS(min_samples=5, xi=0.03, metric='euclidean', n_jobs=-1)
    labels = optics.fit_predict(X)
    
    res_df = pd.DataFrame({'sequence_id': meta['sequence_id'], 'cluster': labels})
    output_path = f"{BASE_DIR}/data/refined/{version}/{model_type}_clusters.csv"
    res_df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"✅ 저장 완료: {output_path}")

# =========================================================
# 메인
# =========================================================
def main(version):
    # 데이터 로드
    data_dir = f"{BASE_DIR}/data/refined/{version}/"
    seq_df = pd.read_csv(f"{data_dir}attack_sequences.csv", encoding='utf-8-sig')
    stats_df = pd.read_csv(f"{data_dir}attack_sequences_stats.csv", encoding='utf-8-sig')
    
    # 1. Coordinates
    run_coord_clustering(version, seq_df, stats_df)
    
    # 2. GRU
    run_embedding_clustering(version, 'gru')
    
    # 3. Transformer
    run_embedding_clustering(version, 'transformer')

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', type=str, required=True)
    args = parser.parse_args()
    
    main(args.version)
