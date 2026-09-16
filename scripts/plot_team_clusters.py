import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os
import yaml
from tqdm import tqdm

# [소프트 코딩] 설정 로드
CONFIG_PATH = 'config.yaml'
with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

VERSION = config['version'] # v5.6
BASE_DIR = '.'
REFINED_DIR = f"{BASE_DIR}/data/refined/{VERSION}/"
CLUSTERING_RESULT_DIR = f"{BASE_DIR}/results/clustering/{VERSION}/transformer/"
OUTPUT_BASE_DIR = f"{BASE_DIR}/results/temp/{VERSION}/"

def draw_pitch(ax):
    """축구장 피치를 그리는 함수 (0-1 정문화 좌표계 기준)"""
    # 피치 외곽선
    rect = patches.Rectangle((0, 0), 1, 1, linewidth=2, edgecolor='black', facecolor='white', zorder=0)
    ax.add_patch(rect)
    
    # 하프라인
    ax.plot([0.5, 0.5], [0, 1], color="black", linewidth=1)
    
    # 중앙 원
    center_circle = patches.Circle((0.5, 0.5), 0.09, color="black", fill=False, linewidth=1)
    ax.add_patch(center_circle)
    ax.scatter(0.5, 0.5, color="black", s=10)
    
    # 페널티 박스 (왼쪽)
    left_box = patches.Rectangle((0, 0.2), 0.165, 0.6, linewidth=1, edgecolor='black', facecolor='none')
    ax.add_patch(left_box)
    left_goal = patches.Rectangle((0, 0.4), 0.055, 0.2, linewidth=1, edgecolor='black', facecolor='none')
    ax.add_patch(left_goal)
    
    # 페널티 박스 (오른쪽)
    right_box = patches.Rectangle((1-0.165, 0.2), 0.165, 0.6, linewidth=1, edgecolor='black', facecolor='none')
    ax.add_patch(right_box)
    right_goal = patches.Rectangle((1-0.055, 0.4), 0.055, 0.2, linewidth=1, edgecolor='black', facecolor='none')
    ax.add_patch(right_goal)

def plot_cluster_trajectories(seq_df, team_name, cluster_id, sequence_ids, output_path):
    """특정 클러스터의 시퀀스 궤적을 플로팅하여 저장"""
    fig, ax = plt.subplots(figsize=(12, 8))
    draw_pitch(ax)
    
    cluster_seqs = seq_df[seq_df['sequence_id'].isin(sequence_ids)].sort_values(['sequence_id', 'action_id'])
    
    # 클러스터 내의 각 시퀀스별로 그리기
    for seq_id in sequence_ids:
        one_seq = cluster_seqs[cluster_seqs['sequence_id'] == seq_id]
        if len(one_seq) < 2:
            continue
            
        # 궤적 그리기 (이벤트 연결)
        ax.plot(one_seq['start_x'], one_seq['start_y'], color='blue', alpha=0.3, linewidth=1)
        
        # 마지막 성과 지점 표시
        last_event = one_seq.iloc[-1]
        ax.scatter(last_event['end_x'], last_event['end_y'], color='red', s=30, alpha=0.6, marker='x' if not last_event['is_outcome'] else 'o')
        
        # 시작 지점 표시
        first_event = one_seq.iloc[0]
        ax.scatter(first_event['start_x'], first_event['start_y'], color='green', s=10, alpha=0.4)

    plt.title(f"Team: {team_name} | Cluster: {cluster_id} (n={len(sequence_ids)})", fontsize=15)
    plt.xlim(-0.05, 1.05)
    plt.ylim(-0.05, 1.05)
    plt.axis('off')
    
    # 디렉토리 생성 및 저장
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, bbox_inches='tight', dpi=150)
    plt.close()

def main():
    print(f"v5.6 팀별 클러스터 시각화 시작...")
    
    # 1. 공격 시퀀스 데이터 로드
    seq_path = os.path.join(REFINED_DIR, 'attack_sequences.csv')
    if not os.path.exists(seq_path):
        print(f"Error: {seq_path} 파일을 찾을 수 없습니다.")
        return
    
    print(f"시퀀스 데이터 로딩 중: {seq_path}")
    seq_df = pd.read_csv(seq_path, encoding='utf-8-sig')
    
    # 2. 팀별 클러스터 결과 폴더 조회
    if not os.path.exists(CLUSTERING_RESULT_DIR):
        print(f"Error: {CLUSTERING_RESULT_DIR} 경로가 존재하지 않습니다.")
        return
        
    teams = [d for d in os.listdir(CLUSTERING_RESULT_DIR) if os.path.isdir(os.path.join(CLUSTERING_RESULT_DIR, d))]
    print(f"발견된 팀: {len(teams)}개")
    
    # 3. 팀별 처리
    for team in tqdm(teams, desc="Processing Teams"):
        team_cluster_file = os.path.join(CLUSTERING_RESULT_DIR, team, 'team_clusters.csv')
        if not os.path.exists(team_cluster_file):
            continue
            
        team_cluster_df = pd.read_csv(team_cluster_file, encoding='utf-8-sig')
        
        # 클러스터별로 그룹화
        clusters = team_cluster_df.groupby('cluster')
        
        for cluster_id, group in clusters:
            seq_ids = group['sequence_id'].tolist()
            output_file = os.path.join(OUTPUT_BASE_DIR, team, f"cluster_{cluster_id}.png")
            
            # 시각화 실행
            plot_cluster_trajectories(seq_df, team, cluster_id, seq_ids, output_file)

    print(f"\n시각화 완료! 결과 저장 경로: {OUTPUT_BASE_DIR}")

if __name__ == "__main__":
    main()
