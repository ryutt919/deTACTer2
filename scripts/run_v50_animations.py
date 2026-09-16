from pathlib import Path as _RepoPath
_REPO_ROOT = _RepoPath(__file__).resolve().parents[1].as_posix()

# =========================================================
# run_v50_animations.py
# deTACTer v5.0 전술 애니메이션 생성 자동화
# =========================================================
# 주요 기능:
# 1. v5.0에서 추출된 시퀀스 중 각 클러스터의 대표 샘플 선정
# 2. animate_tactics.py의 기능을 활용하여 MP4 애니메이션 생성
# 3. 모든 경로는 config.yaml을 참조하는 소프트 코딩 방식
# =========================================================

import pandas as pd
import yaml
import os
import subprocess
import sys

# 터미널 한글 출력 인코딩 설정 (Windows)
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

# =========================================================
# 설정 정의
# =========================================================
BASE_DIR = _REPO_ROOT
CONFIG_PATH = os.path.join(BASE_DIR, 'config.yaml')

def get_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def setup_paths():
    config = get_config()
    version = config['version']
    refined_dir = os.path.join(BASE_DIR, "data", "refined", version)
    anim_output_dir = os.path.join(BASE_DIR, "results", "animations", version)
    os.makedirs(anim_output_dir, exist_ok=True)
    return version, refined_dir, anim_output_dir

# =========================================================
# 애니메이션 생성 대상 선정
# =========================================================
def select_animation_targets(refined_dir):
    """각 클러스터별로 대표적인 시퀀스들을 선정합니다."""
    # Transformer -> GRU -> Coord 순으로 우선순위 탐색
    cluster_results = ["transformer_clusters.csv", "gru_clusters.csv", "coord_clusters.csv", "cluster_labels.csv"]
    cluster_path = None
    
    for filename in cluster_results:
        pth = os.path.join(refined_dir, filename)
        if os.path.exists(pth):
            cluster_path = pth
            print(f"[정보] {filename}을 기반으로 애니메이션 대상 선정")
            break
            
    if not cluster_path:
        print(f"[오류] 클러스터 결과 파일(coord/gru/transformer)을 찾을 수 없습니다.")
        return []
        
    cluster_df = pd.read_csv(cluster_path, encoding='utf-8-sig')
    
    # 각 클러스터에서 상위 2개씩 선정 (너무 많으면 오래 걸림)
    clusters = sorted([c for c in cluster_df['cluster'].unique() if c != -1])
    targets = []
    
    for c_id in clusters:
        sample_ids = cluster_df[cluster_df['cluster'] == c_id]['sequence_id'].head(2).tolist()
        targets.extend(sample_ids)
        
    print(f"[선정 완료] 총 {len(targets)}개의 시퀀스 애니메이션 생성 예정 (클러스터당 2개)")
    return targets

# =========================================================
# 애니메이션 생성 실행 (v4.6: 모델별 분리 생성)
# =========================================================
def run_model_animations(model_type, version, refined_dir, anim_output_dir):
    """특정 모델의 클러스터 결과에 대해 애니메이션을 생성합니다."""
    cluster_filename = f"{model_type}_clusters.csv" if model_type != 'coord' else "coord_clusters.csv"
    # 기존 코드 호환성용
    if model_type == 'legacy': cluster_filename = "cluster_labels.csv"
    
    cluster_path = os.path.join(refined_dir, cluster_filename)
    if not os.path.exists(cluster_path):
        return False
        
    print(f"\n▶️ [{model_type.upper()}] 기반 애니메이션 생성 시작...")
    
    # 모델별 출력 디렉토리 생성
    model_output_dir = os.path.join(anim_output_dir, model_type)
    os.makedirs(model_output_dir, exist_ok=True)
    
    cluster_df = pd.read_csv(cluster_path, encoding='utf-8-sig')
    
    # 각 클러스터별 대표 1개씩만 선정 (전체 양이 많으므로)
    clusters = sorted([c for c in cluster_df['cluster'].unique() if c != -1])
    
    script_path = os.path.join(BASE_DIR, "scripts", "animate_tactics.py")

    for c_id in clusters:
        # 클러스터당 첫 번째 샘플 선택
        sid = cluster_df[cluster_df['cluster'] == c_id]['sequence_id'].iloc[0]
        
        # [v4.7] 파일명 명명 규칙: {version}_{model}_c{cluster}_s{sid}.mp4
        output_filename = f"{version}_{model_type}_c{c_id}_s{sid}.mp4"
        output_path = os.path.join(model_output_dir, output_filename)
        
        print(f"  - {output_filename} 생성 중...")
        
        cmd = ["python", script_path, "--sequence_id", str(sid), "--model", model_type]
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            # 생성된 파일 이동 및 이름 변경
            default_path = os.path.join(anim_output_dir, f"sequence_{sid}.mp4")
            if os.path.exists(default_path):
                if os.path.exists(output_path): os.remove(output_path)
                os.rename(default_path, output_path)
        except Exception as e:
            print(f"  - [오류] {sid} 생성 실패: {e}")
            
    return True

if __name__ == "__main__":
    version, refined_dir, anim_output_dir = setup_paths()
    
    print("=" * 60)
    print(f"deTACTer v5.0 전술 애니메이션 모델별 분리 생성 시작")
    print(f"  - 버전: {version}")
    print("=" * 60)
    
    # 각 모델별로 순차 실행
    found_any = False
    for m in ['coord', 'gru', 'transformer']:
        if run_model_animations(m, version, refined_dir, anim_output_dir):
            found_any = True
    
    print("\n" + "=" * 60)
    if found_any:
        print("모든 모델별 애니메이션 생성 작업 완료!")
    else:
        print("❌ 애니메이션 생성 실패: 생성할 대상 클러스터 파일을 찾지 못했습니다.")
        print("   (확인 필요: refined 폴더 내 *_clusters.csv 파일)")
    print("=" * 60)
