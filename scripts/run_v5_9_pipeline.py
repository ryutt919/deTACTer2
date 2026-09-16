import yaml
import subprocess
import time
import os
import sys

# 강제 utf-8 설정
sys.stdout.reconfigure(encoding='utf-8')

VERSION = 'v5.9'

def run_script(script_path):
    print(f"\n▶️ Running {script_path}...")
    start_time = time.time()
    try:
        env = os.environ.copy()
        env['PYTHONUTF8'] = '1'
        
        process = subprocess.Popen(
            ['python'] + script_path.split(' '),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            env=env,
            bufsize=1
        )
        
        for line in process.stdout:
            print(f"  {line}", end='')
        
        process.wait()
        duration = time.time() - start_time
        
        if process.returncode != 0:
            print(f"❌ Error executing {script_path} (Exit Code: {process.returncode})")
            return False
        else:
            print(f"✅ Completed {script_path} ({duration:.1f}s)")
            return True
            
    except Exception as e:
        print(f"❌ Exception executing {script_path}: {e}")
        return False

def main():
    print(f"🚀 Starting deTACTer {VERSION} Complete Pipeline")
    print(f"Target Parameters: SeqLen 8 (Fixed), MinPass 3 (Fixed)")
    print("="*60)
    
    # 1. Preprocessing (v5.9 데이터 생성)
    if not run_script('scripts/preprocessing.py'): return

    # 2. VAEP 계산
    if not run_script('scripts/compute_vaep.py'): return
    
    # 3. Sequence Extraction (config v5.9 값 사용 -> attack/buildup len 반영)
    if not run_script('scripts/sequence_extraction.py'): return

    # 4. Model Training & TPE
    # 데이터는 고정되어 있으나, 모델 구조(Layer, Head 등) 최적화를 위해 TPE 수행
    # 50회 정도면 충분할 것으로 예상 (데이터 파라미터가 고정되어서 탐색 공간이 줄어듦)
    print("\n[STEP 4] Transformer 모델 구조 최적화 (TPE 50 trials)...")
    if not run_script('scripts/train_embedding_model.py --model transformer --trials 50'): return

    # 5. Extract Embeddings (Final Model 기반)
    print("\n[STEP 5] Transformer 임베딩 추출...")
    if not run_script(f'scripts/extract_embeddings.py --model transformer --version {VERSION}'): return
    
    # 6. Tactical Clustering (Embedding 기반 + 팀별 클러스터링)
    print("\n[STEP 6] Transformer 임베딩 기반 팀별 클러스터링 (OPTICS)...")
    if not run_script('scripts/tactical_clustering.py --mode embedding --team true'): return
    
    # [Fix] 애니메이션 생성을 위해 파일명 변경 (cluster_labels.csv -> transformer_clusters.csv)
    try:
        data_dir = f"data/refined/{VERSION}"
        src = f"{data_dir}/cluster_labels.csv"
        dst = f"{data_dir}/transformer_clusters.csv"
        if os.path.exists(src):
            if os.path.exists(dst): os.remove(dst)
            os.rename(src, dst)
            print(f"✅ 파일명 변경 완료: cluster_labels.csv -> transformer_clusters.csv")
    except Exception as e:
        print(f"❌ 파일명 변경 실패: {e}")
    
    # 7. Animations
    print("\n[STEP 7] 최종 전술 애니메이션 생성...")
    if not run_script('scripts/run_v50_animations.py'): return
            
    print("\n" + "="*60)
    print(f"🎉 deTACTer {VERSION} Pipeline finished successfully!")
    print("="*60)

if __name__ == "__main__":
    main()
