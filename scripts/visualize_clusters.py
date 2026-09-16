from pathlib import Path as _RepoPath
_REPO_ROOT = _RepoPath(__file__).resolve().parents[1].as_posix()

# =========================================================
# visualize_clusters.py
# deTACTer v5.0 클러스터별 상세 분석 및 VAEP 시각화
# =========================================================
# 주요 기능:
# 1. 클러스터별 대표 시퀀스 시각화 (피치 위에 경로)
# 2. 클러스터별 VAEP 위협도 히트맵
# 3. 클러스터 통계 대시보드
# =========================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import seaborn as sns
import yaml
import os
import sys

# 터미널 한글 출력 인코딩 설정 (Windows)
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# =========================================================
# 설정 로드
# =========================================================
CONFIG_PATH = (_REPO_ROOT + '/config.yaml')
with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

VERSION = config['version']
BASE_DIR = _REPO_ROOT
REFINED_DIR = f"{BASE_DIR}/data/refined/{VERSION}/"
OUTPUT_DIR = f"{BASE_DIR}/results/visualizations/{VERSION}/"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# =========================================================
# 축구장 그리기
# =========================================================
def draw_pitch(ax, pitch_color='#1a472a', line_color='white'):
    """정규화된 좌표(0~1)에 맞춘 축구장을 그립니다."""
    ax.set_facecolor(pitch_color)
    
    # 외곽선
    ax.plot([0, 1], [0, 0], color=line_color, linewidth=2)
    ax.plot([0, 1], [1, 1], color=line_color, linewidth=2)
    ax.plot([0, 0], [0, 1], color=line_color, linewidth=2)
    ax.plot([1, 1], [0, 1], color=line_color, linewidth=2)
    
    # 중앙선
    ax.plot([0.5, 0.5], [0, 1], color=line_color, linewidth=1.5)
    
    # 센터 서클
    center_circle = plt.Circle((0.5, 0.5), 0.087, fill=False, color=line_color, linewidth=1.5)
    ax.add_patch(center_circle)
    
    # 패널티 박스
    ax.add_patch(patches.Rectangle((0, 0.211), 0.157, 0.578, fill=False, color=line_color, linewidth=1.5))
    ax.add_patch(patches.Rectangle((0.843, 0.211), 0.157, 0.578, fill=False, color=line_color, linewidth=1.5))
    
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.02)
    ax.set_aspect('equal')
    ax.axis('off')
    return ax

# =========================================================
# 클러스터별 대표 시퀀스 플롯
# =========================================================
def plot_cluster_sequences(seq_df, cluster_df, cluster_col, n_samples=5):
    """각 클러스터의 대표 시퀀스들을 피치 위에 시각화합니다."""
    print(f"[시각화] {cluster_col} 클러스터별 대표 시퀀스 플롯 중...")
    
    clusters = cluster_df[cluster_col].unique()
    clusters = sorted([c for c in clusters if c != -1])[:10]  # 상위 10개
    
    for cluster_id in clusters:
        fig, ax = plt.subplots(figsize=(12, 8))
        draw_pitch(ax)
        
        seq_ids = cluster_df[cluster_df[cluster_col] == cluster_id]['sequence_id'].values[:n_samples]
        colors = plt.cm.plasma(np.linspace(0.2, 0.8, len(seq_ids)))
        
        for i, seq_id in enumerate(seq_ids):
            seq = seq_df[seq_df['sequence_id'] == seq_id].sort_values('seq_position', ascending=False)
            x = seq['start_x'].values
            y = seq['start_y'].values
            
            ax.plot(x, y, color=colors[i], alpha=0.7, linewidth=2, marker='o', markersize=4)
            ax.scatter([x[0]], [y[0]], color='lime', s=80, zorder=5, edgecolor='white')
            ax.scatter([x[-1]], [y[-1]], color='red', s=80, zorder=5, marker='*', edgecolor='white')
        
        ax.set_title(f'{cluster_col} 클러스터 {cluster_id} (샘플 {len(seq_ids)}개)', fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(f'{OUTPUT_DIR}{cluster_col}_cluster_{cluster_id}_sequences.png', dpi=150, bbox_inches='tight')
        plt.close()
    
    print(f"    -> 저장 완료: {OUTPUT_DIR}")

# =========================================================
# 클러스터별 VAEP 위협도 대시보드
# =========================================================
def plot_cluster_vaep_dashboard(stats_df, cluster_df, cluster_col):
    """클러스터별 VAEP 위협도를 대시보드로 시각화합니다."""
    print(f"[시각화] {cluster_col} VAEP 위협도 대시보드 생성 중...")
    
    # VAEP 데이터 로드
    vaep_path = os.path.join(REFINED_DIR, "vaep_values.csv")
    if not os.path.exists(vaep_path):
        print("    [경고] VAEP 데이터가 없습니다. 스킵합니다.")
        return
    
    vaep_df = pd.read_csv(vaep_path, encoding='utf-8-sig')
    
    # 클러스터 정보 병합
    merged = stats_df.merge(cluster_df, on='sequence_id', how='inner')
    
    # 시퀀스별 VAEP 합계 계산 (sequence_id가 있는 경우만)
    if 'sequence_id' in vaep_df.columns:
        seq_vaep = vaep_df.groupby('sequence_id')['vaep_value'].sum().reset_index()
        merged = merged.merge(seq_vaep, on='sequence_id', how='left')
    else:
        print("    [경고] VAEP 데이터에 sequence_id가 없습니다.")
        return
    
    # 클러스터별 VAEP 통계
    cluster_vaep = merged.groupby(cluster_col)['vaep_value'].agg(['mean', 'sum', 'count']).reset_index()
    cluster_vaep.columns = [cluster_col, 'avg_vaep', 'sum_vaep', 'count']
    cluster_vaep = cluster_vaep[cluster_vaep[cluster_col] != -1].sort_values('avg_vaep', ascending=False)
    
    # 대시보드 생성
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # 평균 VAEP
    sns.barplot(data=cluster_vaep.head(10), x=cluster_col, y='avg_vaep', ax=axes[0], palette='Reds_r')
    axes[0].set_title(f'{cluster_col} 클러스터별 평균 VAEP (위협도)', fontsize=12)
    axes[0].set_xlabel('클러스터 ID')
    axes[0].set_ylabel('평균 VAEP')
    
    # 시퀀스 수
    sns.barplot(data=cluster_vaep.head(10), x=cluster_col, y='count', ax=axes[1], palette='Blues_r')
    axes[1].set_title(f'{cluster_col} 클러스터별 시퀀스 수', fontsize=12)
    axes[1].set_xlabel('클러스터 ID')
    axes[1].set_ylabel('시퀀스 수')
    
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}{cluster_col}_vaep_dashboard.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    # CSV 저장
    cluster_vaep.to_csv(f'{OUTPUT_DIR}{cluster_col}_vaep_stats.csv', index=False, encoding='utf-8-sig')
    print(f"    -> 저장 완료: {OUTPUT_DIR}{cluster_col}_vaep_dashboard.png")

# =========================================================
# 메인 실행
# =========================================================
def run_cluster_visualization():
    """클러스터 시각화 파이프라인을 실행합니다."""
    print("=" * 60)
    print(f"deTACTer v5.0 클러스터 시각화 시작")
    print(f"  - 버전: {VERSION}")
    print("=" * 60)
    
    # 데이터 로드
    seq_df = pd.read_csv(REFINED_DIR + 'attack_sequences.csv', encoding='utf-8-sig')
    stats_df = pd.read_csv(REFINED_DIR + 'attack_sequences_stats.csv', encoding='utf-8-sig')
    
    try:
        cluster_df = pd.read_csv(REFINED_DIR + 'cluster_labels.csv', encoding='utf-8-sig')
    except FileNotFoundError:
        print("[오류] 클러스터링 결과가 없습니다. 클러스터링을 먼저 실행하세요.")
        return
    
    # 클러스터별 시퀀스 시각화
    plot_cluster_sequences(seq_df, cluster_df, 'optics_cluster')
    plot_cluster_sequences(seq_df, cluster_df, 'agglom_cluster')
    
    # VAEP 위협도 대시보드
    plot_cluster_vaep_dashboard(stats_df, cluster_df, 'optics_cluster')
    plot_cluster_vaep_dashboard(stats_df, cluster_df, 'agglom_cluster')
    
    print("\n" + "=" * 60)
    print("클러스터 시각화 완료!")
    print(f"결과 폴더: {OUTPUT_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    run_cluster_visualization()
