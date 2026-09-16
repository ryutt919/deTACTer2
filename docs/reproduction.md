# 실행 및 재현 범위

- **작업 기준** — 저장소 루트를 현재 작업 디렉터리로 사용. `scripts/`의 이전 PC 절대 경로는 파일 위치에서 저장소 루트를 구하도록 변경했으며, 알고리즘은 그대로 보존.
- **설정 기준** — `config.yaml`의 `version: v5.9`, `attack_len: 4`, `buildup_len: 4`, `min_pass_count: 3`, OPTICS `min_samples: 3`, `xi: 0.01`.
- **아카이브** — `archive/`의 코드·노트북·실행기는 과거 기록이며 현재 재현 진입점이 아님. 당시 절대 경로와 상대 링크가 남아 있을 수 있음.

## 1. 웹 대시보드

```powershell
cd web
npm ci
npm run build
npm run dev
```

- **환경** — lockfile의 Vite 7 요구에 맞는 Node.js 사용. 정리 작업 환경은 Node.js 24.12.0 / npm 11.6.2.
- **입력** — `web/src/data/sequences.json`은 기존 `deTACTer5.9` 제출 폴더에서 복사한 205개 시퀀스 스냅샷. 내용 변경 없이 로컬에만 보관하며 Git에서는 제외. 새 클론에서는 이 파일을 별도로 복사하거나 웹 데이터 변환으로 생성한 뒤 위 명령을 실행해야 함. `.gitkeep`만 있는 상태에서는 JSON import를 해석할 수 없어 빌드가 실패함.
- **영상** — JSON에 107개 영상 URL이 있지만 해당 개별 MP4는 제출 폴더에 없었음. `docs/media/`의 기존 전체 데모 영상 2개는 개별 영상의 대체 파일이 아니며 로컬에만 보관.

## 2. Python 의존성

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

- **목록 출처** — 제출본의 `requirements.txt`를 바탕으로 표준 라이브러리 `sqlite3`와 인터프리터 `python` 항목을 제외하고 시각화 의존성을 보완.
- **환경 한계** — 당시 환경 lockfile은 없음. 이 목록은 의존성 목록이며 Python·PyTorch·socceraction 조합의 설치 및 학습 재현을 보증하는 고정 환경이 아님. 이번 작업에서는 전체 Python 환경 설치·학습을 수행하지 않음.

## 3. 입력 데이터

```text
data/
├── raw_data.csv
├── match_info.csv
├── data_description.xlsx
└── spadl/
    └── game_<game_id>.csv
```

- **로컬 입력** — 원본 폴더의 CSV 2개와 데이터 설명 파일을 복사해 보존. 원시 데이터는 Git 추적 대상에서 제외.
- **원시 스키마** — `game_id`, `action_id`, `period_id`, `time_seconds`, `team_id`, `player_id`, `result_name`, `start_x`, `start_y`, `end_x`, `end_y`, `dx`, `dy`, `type_name`, `player_name_ko`, `team_name_ko`, `position_name`, `main_position`.
- **식별자 조건** — 추출 코드는 `action_id` 단독으로 사용 여부를 관리하므로 전체 입력에서 ID 고유성을 확인해야 함. 경기 내부에서만 고유하면 `(game_id, action_id)` 기준으로 수정하는 별도 작업 필요.

## 4. 단계별 실행 순서

- **현재 상태** — 아래는 스크립트의 의존 순서이며 원클릭 재현 보장 명령이 아님. 특히 SPADL 변환의 입력 스키마 불일치는 먼저 해결해야 함.

```powershell
# 1. 시퀀스 분석용 전처리
python scripts/preprocessing.py

# 2. VAEP용 경기별 SPADL 생성: 아래 '미해결 연결 지점' 먼저 확인
python scripts/convert_to_spadl.py
python scripts/compute_vaep.py

# 3. 시퀀스 추출 및 표현 학습
python scripts/sequence_extraction.py
python scripts/train_embedding_model.py --model transformer --trials 50 --version v5.9
python scripts/extract_embeddings.py --model transformer --version v5.9

# 4. 팀별 분석과 영상
python scripts/team_based_clustering.py --version v5.9
python scripts/team_animations.py --version v5.9

# 5. 웹 내보내기: 팀별 군집 결과 연결 확인 후 실행
python scripts/prepare_web_data.py
```

- **통합 실행기** — `scripts/run_v5_9_final_pipeline.py`는 전처리→VAEP→추출→학습→임베딩→팀별 군집→애니메이션 순서. SPADL 생성과 웹 내보내기는 별도 단계.
- **산출물 관리** — 통합 실행기는 기존 `results/animations/v5.9/transformer/`를 삭제하고 다시 생성하는 코드가 있으므로 결과 보존이 필요하면 버전별로 별도 복사.

## 5. 미해결 연결 지점과 평가 제약

- **SPADL 스키마** — `convert_to_spadl.py`는 `df['sequence_id']`를 요구하나 제공 원시 CSV에는 해당 열이 없음. 변환 결과에는 `action_id`도 명시적으로 보존되지 않음. 변환 단계의 식별자 설계·스키마 검증이 선행되어야 처음부터 VAEP를 재생성할 수 있음.
- **분리된 데이터 분기** — VAEP 변환은 원시 데이터를 읽고, 시퀀스 분기는 리시브 보정 데이터를 읽음. 생성된 Carry와 원시 행동 간 매칭, VAEP 미매칭 시 0 처리, 공격 방향 정규화 범위를 검증해야 함.
- **웹 군집 연결** — 팀별 군집화는 `results/clustering/v5.9/transformer/<팀>/team_clusters.csv`를 쓰지만 웹 준비 코드는 `data/refined/v5.9/transformer_clusters.csv`를 읽음. 통합 매핑을 만들거나 웹 로더를 수정해야 팀별 군집이 화면에 반영됨.
- **통계 동기화** — 학습기는 최종 `attack_sequences.csv`를 다시 저장하지만 통계 CSV는 재생성하지 않음. 최종 추출 결과의 ID·개수와 통계의 정합성 확인 필요.
- **TPE 평가** — 탐색 시 학습·평가에 같은 시퀀스 사용. 예외 분기에서 최소화 목적에 `-1.0`을 반환하여 실패 trial이 최적값으로 선택될 가능성도 있음. 독립 검증 분할 및 실패 trial 처리가 후속 수정 대상.
- **체크포인트** — 최적 모델 상태를 `state_dict()` 참조로 보관하므로 이후 학습으로 값이 바뀔 수 있음. 최적 epoch 복원 보장에는 deepcopy 또는 즉시 저장이 필요.
- **임베딩 매칭** — 메타데이터 중복 제거 후 인덱스를 다시 부여하므로 입력에 중복이 있다면 실제 임베딩 행과 일치하는지 검증해야 함.
- **측정 해석** — TPE 로그의 일부 `Silhouette` 문구는 과거 이름이며 실제 목적은 MSE. 탐색하는 `optics_min_samples`는 현재 MSE 계산에 사용되지 않고 최종 팀별 군집화는 YAML 설정을 사용.
- **변경 범위** — 위 항목은 코드·스키마 확인으로 발견한 현재 제약. 폴더·문서 정리 범위를 넘어서는 알고리즘 수정은 이번 작업에 포함하지 않았으며, 해결 완료로 기록하지 않음.

## 6. 이번 정리의 검증 범위

- Python 코드는 실행 없이 AST 구문 검사 및 경로 변경 전후 알고리즘 동일성 확인.
- 새 README와 안내 문서의 로컬 링크 확인, 원시 CSV·제출 JSON 규모 집계, 복사된 원본 자료의 해시 비교.
- 프런트엔드 의존성 설치와 production build 확인 결과는 `organization.md`에 기록.
- TPE 재탐색, CatBoost·Transformer 학습, 군집 재생성 및 영상 인코딩은 실행하지 않음. README의 과거 실험값은 새 벤치마크 결과가 아님.
