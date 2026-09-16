from pathlib import Path as _RepoPath
_REPO_ROOT = _RepoPath(__file__).resolve().parents[1].as_posix()

# =========================================================
# verify_animation_outputs.py
# 전술 애니메이션 출력 결과 검증 스크립트
# =========================================================

import os
import re
import pandas as pd

BASE_DIR = _REPO_ROOT
VERSION = 'v5.6'
ANIM_DIR = os.path.join(BASE_DIR, 'results', 'animations', VERSION, 'transformer')

def verify_files():
    print(f"=" * 60)
    print(f"애니메이션 출력물 검증 시작 (버전: {VERSION})")
    print(f"=" * 60)
    
    if not os.path.exists(ANIM_DIR):
        print(f"[오류] 디렉토리가 존재하지 않습니다: {ANIM_DIR}")
        return

    # 파일명 패턴: {팀명}_c{숫자}_s{숫자}.mp4
    # 팀명에 다양한 문자가 올 수 있으므로 유연하게 매칭
    pattern = re.compile(r'^.+_c\d+_s\d+\.mp4$')
    
    total_files = 0
    invalid_name_files = []
    zero_byte_files = []
    team_stats = {}
    
    for root, dirs, files in os.walk(ANIM_DIR):
        team_name = os.path.basename(root)
        if team_name == 'transformer': continue
        
        mp4_files = [f for f in files if f.endswith('.mp4')]
        if not mp4_files and not dirs: continue
        
        team_stats[team_name] = len(mp4_files)
        
        for f in mp4_files:
            total_files += 1
            file_path = os.path.join(root, f)
            
            # 1. 파일명 검증
            if not pattern.match(f):
                invalid_name_files.append(file_path)
            
            # 2. 파일 크기 검증
            if os.path.getsize(file_path) == 0:
                zero_byte_files.append(file_path)
                
    # 결과 출력
    print(f"\n[1] 기본 통계")
    print(f"  - 총 생성된 파일 수: {total_files}")
    for team, count in team_stats.items():
        print(f"  - {team}: {count}개")
        
    print(f"\n[2] 무결성 검사")
    
    if invalid_name_files:
        print(f"  ❌ [파일명 형식 불일치] {len(invalid_name_files)}개")
        for f in invalid_name_files[:5]:
            print(f"    - {f}")
    else:
        print(f"  ✅ 모든 파일명이 규칙(c{{cluster}}_s{{sid}}.mp4)을 준수합니다.")
        
    if zero_byte_files:
        print(f"  ❌ [빈 파일 발견] {len(zero_byte_files)}개")
        for f in zero_byte_files[:5]:
            print(f"    - {f}")
    else:
        print(f"  ✅ 모든 영상 파일이 정상적인 크기를 가집니다.")
        
    print(f"\n{'='*60}")
    if not invalid_name_files and not zero_byte_files and total_files > 0:
        print("🎉 모든 검증을 통과했습니다!")
    else:
        print("⚠️ 일부 검증 항목에 주의가 필요합니다.")
    print(f"{'='*60}")

if __name__ == "__main__":
    verify_files()
