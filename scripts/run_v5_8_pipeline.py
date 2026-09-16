import yaml
import subprocess
import time
import os
import sys

# 강제 utf-8 설정
sys.stdout.reconfigure(encoding='utf-8')

VERSION = 'v5.8'

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
    print(f"🚀 Starting deTACTer {VERSION} Complete Pipeline (Final Optimized)")
    print(f"Target Parameters: SeqLen 6, MinPass 2, OPTICS 6")
    print("="*60)
    
    # 1. Preprocessing (v5.8 데이터 생성)
    # if not run_script('scripts/preprocessing.py'): return

    # 2. VAEP 계산 (전처리 데이터 기반)
    if not run_script('scripts/compute_vaep.py'): return
    
    # 3. Sequence Extraction (v5.8 최종 설정 기반)
    if not run_script('scripts/sequence_extraction.py'): return

    # 4. Final Embedding Model Training (100 Epochs + EarlyStopping)
    # TPE 써치는 이미 끝났으므로, main() 내의 최종 재학습 로직이 실행되도록 유도
    # --trials 0 혹은 기존 trials 수와 동일하게 설정하면 남은 trial이 0이 되어 재학습 단계로 진입함
    print("\n[STEP 4] 최종 임베딩 모델 재학습 (Transformer, 100 epochs)...")
    if not run_script('scripts/train_embedding_model.py --model transformer --trials 200'): return

    # 5. Extract Embeddings (Final Model 기반)
    print("\n[STEP 5] Transformer 임베딩 추출...")
    if not run_script(f'scripts/extract_embeddings.py --model transformer --version {VERSION}'): return
    
    # 6. Tactical Clustering (Embedding 기반 + 팀별 클러스터링)
    print("\n[STEP 6] Transformer 임베딩 기반 팀별 클러스터링 (OPTICS)...")
    if not run_script('scripts/tactical_clustering.py --mode embedding --team true'): return
    
    # 7. Animations (최종 결과물 가시화)
    print("\n[STEP 7] 최종 전술 애니메이션 생성...")
    if not run_script('scripts/run_v50_animations.py'): return
            
    print("\n" + "="*60)
    print(f"🎉 deTACTer {VERSION} Pipeline finished successfully!")
    print("="*60)

if __name__ == "__main__":
    main()
