# deTACTer

**K리그 이벤트 데이터에서 반복되는 공격 패턴을 추출하고, 행동의 가치와 함께 해석하는 전술 분석 프로젝트.**

`Football Analytics` · `Sequence Representation Learning` · `VAEP` · `Team-wise Clustering`

**[웹사이트 바로가기](https://de-tac-ter.vercel.app/)** · **[▶ 데모 영상 보기](docs/media/demo.mp4)**

https://github.com/user-attachments/assets/b42762e2-34f7-4d5b-82dd-311a3e4aa445

- **연구 질문** — 슈팅과 득점에 앞선 공격 전개를 어떻게 비교 가능한 시퀀스로 표현하고, 반복되는 패턴과 개별 행동의 가치를 함께 설명할 수 있는가?
- **접근** — 이벤트 정제 → 성과 기반 시퀀스 추출 → Transformer Autoencoder → 팀별 OPTICS로 패턴을 구성하고, 별도 VAEP 모델의 행동 가치를 애니메이션과 대시보드에 연결.
- **데이터** — K리그 **198경기 · 12개 팀 · 579,306개 이벤트**를 분석하고, **205개 공격 시퀀스**를 대시보드에서 탐색.
- **프로젝트** — DACON K리그 경기 데이터 기반 AI 서비스 개발 · 팀 deTACTer · 김태현.
- **연구 범위** — 이벤트 좌표로 공격 전개의 반복성을 학습하고 행동 가치를 해석하는 연구 프로토타입(v5.9).

[실행·재현 안내](docs/reproduction.md) · [문제 해결 기록](docs/research/engineering-log.md) · [버전 기록](docs/versions/v5.9.md) · [참고 문헌](docs/references/README.md)

## Research contributions

- **분석 단위 설계** — 슈팅 및 상대 박스 내 행동을 기준으로 역추적하여 공격 시퀀스를 구성. 단절점, 세트피스, 경기·피리어드 경계, 액션 중복 조건을 적용해 비교 대상의 범위를 명시.
- **표현 학습과 가치 평가의 결합** — 좌표 시퀀스의 재구성으로 공간 패턴을 학습하고, VAEP로 각 행동의 득점·실점 확률 변화량을 설명. VAEP는 임베딩과 독립적으로 계산하는 행동 가치 지표.
- **팀별 패턴 발견** — 임베딩을 팀 단위로 분리한 뒤 OPTICS를 적용하여 반복 패턴과 밀도가 낮은 사례를 구분. 군집 수를 사전에 지정하지 않는 분석 흐름 구현.
- **분석 결과의 전달** — 팀·시퀀스 탐색, 행동별 VAEP 차트, 선수·공 이동 애니메이션을 React 대시보드에 연결. 영상은 이벤트 사이를 보간한 시각화이며 실제 트래킹 궤적은 아님.

## Pipeline

```mermaid
flowchart TD
    A["K리그 이벤트 / 경기 메타데이터"] --> B["이벤트 정제 · 좌표 정규화"]
    A --> C["경기별 SPADL 변환"]
    B --> D["성과 탐지 · 시퀀스 역추적"]
    D --> E["Transformer Autoencoder · TPE"]
    E --> F["Masked mean pooling · 임베딩"]
    F --> G["팀별 OPTICS"]
    C --> H["CatBoost 득점 / 실점 확률"]
    H --> I["VAEP 행동 가치"]
    D --> J["전술 애니메이션 · 웹 데이터"]
    G --> J
    I --> J
    J --> K["React 분석 대시보드"]
```

- **분석 흐름** — 시퀀스 분기는 공격 전개의 공간적 유사성을 학습하고, VAEP 분기는 개별 행동의 가치를 추정. 두 결과를 시퀀스 단위의 시각화로 연결.

### 1. Event preprocessing

- **입력** — `data/raw_data.csv`, `data/match_info.csv`; 경기·피리어드·시간·액션 ID, 팀·선수, 이벤트 유형·결과, 시작·종료 좌표 활용.
- **좌표 처리** — 105 × 68 기준으로 범위를 클리핑하고 좌표를 `[0, 1]`로 정규화. 이 단계에서는 팀별 공격 방향을 반전하지 않음.
- **리시브 보정** — 다음 행동과 시작 좌표가 중복되는 리시브 제거; 이동 리시브는 Carry로 변환하거나 다음 Carry에 병합; 정적 리시브와 후속 행동 사이 간극 보정.
- **연속성 판별** — 보정 후 이전 종료점과 현재 시작점 간 정규화 거리 `> 1e-3`를 `is_dis`로 표시. 좌표 이동량과 시간 차이도 계산.
- **출력 / 코드** — `data/refined/v5.9/preprocessed_data.csv` · [preprocessing.py](scripts/preprocessing.py).

### 2. Action valuation — VAEP

- **행동 표준화** — 원시 이벤트의 유형·결과·좌표를 SPADL 형식으로 매핑하고 경기별 `data/spadl/game_*.csv`로 구성.
- **상태 표현** — 현재 행동을 포함한 최근 3개 행동을 상태로 구성. 액션 유형·결과·신체 부위, 시간, 시작·종료 위치, 이동 및 행동 간 공간 차이, 팀 정보를 피처로 사용.
- **확률 추정** — CatBoost 이진 분류기 두 개로 향후 `nr_actions` 이내 득점·실점 여부를 각각 예측. 예측 구간은 최적 파라미터 파일을 우선 사용하며 없으면 10개 행동.
- **평가 방식** — 행동 행 단위 shuffled 5-fold 예측을 모아 Brier score 계산. 경기 단위 분할은 아니므로 동일 경기의 인접 상태가 학습·평가에 함께 포함될 수 있음.
- **가치 산정** — 같은 팀 관점에서 행동 전후의 득점 확률 증가와 실점 확률 감소를 합산. 실제 계산은 소유권 전환 등을 처리하는 `socceraction.vaep.formula.value` 사용. [VAEP 원 논문](https://doi.org/10.1145/3292500.3330758), [공식 구현 설명](https://socceraction.readthedocs.io/en/latest/documentation/valuing_actions/vaep.html).
- **출력 / 코드** — `vaep_values.csv`, `vaep_summary_stats.csv` · [convert_to_spadl.py](scripts/convert_to_spadl.py), [compute_vaep.py](scripts/compute_vaep.py).

$$
V(a_i)=\bigl[P_{score}(S_i,t)-P_{score}(S_{i-1},t)\bigr]
      +\bigl[P_{concede}(S_{i-1},t)-P_{concede}(S_i,t)\bigr]
$$

### 3. Outcome-conditioned sequence extraction

- **성과 정의** — 슈팅 또는 상대 박스 영역에서 시작하는 유효 행동. 공격 방향은 경기·피리어드·팀별 GK 평균 위치로 추정하고, 수비 행동은 성과 후보에서 제외.
- **공간 조건** — L→R 기준 박스 판정은 `x > 0.84`, `0.36 < y < 0.635`. y 조건은 슈팅 후보에도 적용하므로 전체 슈팅을 포괄하는 정의는 아님.
- **역추적 경계** — 경기·피리어드 변경, 이미 사용한 `action_id`, 공격팀의 단절 이벤트, 세트피스 등을 기준으로 탐색 종료. 상대팀 행동도 시퀀스 후보에 포함.
- **v5.9 설정** — 목표 공격팀 액션 수 8, 성과가 아닌 이벤트 중 순수 `Pass` 최소 3개, 전체 이벤트 최소 5개. 경계에서 조기 종료되거나 상대팀 이벤트가 포함되므로 모든 원시 시퀀스가 정확히 8행인 것은 아님.
- **혼전 제외** — 성과가 아닌 이벤트가 지정 박스 내부에서 시작하는 시퀀스 제외. 이후 공격팀 기준으로 시퀀스 전체 좌표를 함께 반전하고 성과 y 범위를 재확인.
- **출력 / 코드** — `attack_sequences.csv`, `attack_sequences_stats.csv` · [sequence_extraction.py](scripts/sequence_extraction.py).

### 4. Representation learning

- **입력 표현** — 성과→과거 순서로 정렬한 `(start_x, start_y)` 좌표열. 성과 지점에서 앞선 공격 전개를 역순으로 표현.
- **모델** — 2차원 좌표 투영 → 학습 가능한 위치 인코딩 → Transformer Encoder → 좌표 재구성. 마스킹한 토큰 표현의 평균으로 시퀀스 임베딩 생성; GRU Autoencoder도 비교 모델로 구현.
- **학습** — 길이 8에 맞춘 패딩·절단과 학습 시 y-flip 증강 적용. 손실은 패딩 좌표를 0으로 마스킹한 텐서의 MSE이며, 평균 분모에는 패딩 위치도 포함됨.
- **TPE 탐색** — 기본 통합 실행 50 trials, trial당 15 epochs. hidden dimension `{32,64,128,256,512}`, layer 수 `1–8`, dropout `0.1–0.3`, learning rate `1e-4–1e-2`, batch size `{16,32,64}`, head 수 `{2,4,8,16}` 탐색.
- **최적화 목표** — v5.9는 재구성 MSE 최소화. 탐색 코드의 학습·평가 시퀀스는 동일하며 증강 여부만 다름; 따라서 탐색 점수를 독립 검증 성능으로 해석하지 않음.
- **최종 학습** — 시퀀스 순서 기준 90:10 분할, 최대 100 epochs, patience 10. 탐색 DB·학습 로그·체크포인트 저장.
- **출력 / 코드** — `results/models/v5.9/transformer_best.pth`, `results/embeddings/v5.9/transformer_embeddings.npy`, `transformer_metadata.csv` · [학습](scripts/train_embedding_model.py), [임베딩 추출](scripts/extract_embeddings.py).

### 5. Team-wise pattern discovery

- **입력 정렬** — `sequence_id`로 임베딩 메타데이터와 팀 정보를 결합하고 팀별로 분리.
- **군집화** — Euclidean 거리 기반 OPTICS; 기본 `min_samples=3`, `xi=0.01`. 팀별 표본 수에 따라 최소 샘플 수를 조정하고, 5개 미만 팀은 건너뜀.
- **결과 해석** — 군집은 좌표 패턴의 반복성을 나타내며 노이즈 라벨은 `-1`. 군집 품질이 전술적 우수성이나 승리 기여를 직접 입증하지는 않음.
- **출력 / 코드** — `results/clustering/v5.9/transformer/<팀명>/team_clusters.csv` · [team_based_clustering.py](scripts/team_based_clustering.py).

### 6. Visualization & delivery

- **애니메이션** — 팀·군집·시퀀스 ID를 파일명에 반영하고 선수·공 이동을 보간하여 MP4 생성.
- **웹 데이터** — 시퀀스 통계, 행동 좌표, VAEP, 군집 및 영상 경로를 JSON으로 구성하여 분석 화면에 제공.
- **화면** — React 19 · Vite 7 · Tailwind CSS · Recharts · Framer Motion으로 팀 필터, 시퀀스 탐색, 행동별 가치 차트 제공.
- **출력 / 코드** — `results/animations/v5.9/transformer/`, `web/src/data/sequences.json` · [영상 생성](scripts/team_animations.py), [웹 데이터 변환](scripts/prepare_web_data.py), [분석 화면](web/src/pages/Analysis.jsx).

## Engineering decisions

- **상대팀 이벤트가 섞일 때 궤적이 반전됨 → 반전 단위를 시퀀스로 변경.** 전처리 단계의 팀별 좌표 반전을 제거하고, 공격팀 기준으로 상대팀 이벤트까지 함께 반전하여 좌표계 일관성을 확보. [구현](scripts/sequence_extraction.py)
- **리시브 중복과 Carry 누락으로 궤적이 파편화됨 → 중복 제거·이동 보정 분리.** 제자리 중복 리시브는 삭제하고 이동 정보는 Carry 변환·병합으로 유지. [구현](scripts/preprocessing.py)
- **동일 공격이 여러 시퀀스로 집계됨 → 액션 재사용 경계 도입.** 사용된 액션을 만나면 역추적을 종료하고 박스 내부 혼전 필터를 적용. [기록](docs/research/engineering-log.md), [구현](scripts/sequence_extraction.py)
- **좌표 불연속을 공격 전개로 학습함 → 정제 후 단절점을 계산.** `is_dis`를 추출 종료 조건으로 사용해 끊긴 궤적이 하나의 패턴으로 이어지는 것을 제한. [v5.5 기록](docs/versions/v5.5.md)
- **군집 점수 중심 탐색에서 시퀀스 정의까지 변함 → 추출 조건 고정·재구성 목표로 전환.** v5.9에서 길이 8·최소 패스 3을 고정하고 MSE를 최적화하여 표현 학습의 목적을 명시. 전술 품질 개선을 입증하려면 별도 평가가 필요. [v5.8](docs/versions/v5.8.md), [v5.9](docs/versions/v5.9.md)
- **영상 파일 탐색·인코딩 문제가 발생함 → 명명 규칙·재귀 탐색·대체 인코딩 적용.** 시퀀스 ID를 파일명에서 복원하고 하위 폴더를 검색하며 ImageIO 대체 경로를 마련. [웹 변환](scripts/prepare_web_data.py), [인코딩](scripts/animate_tactics.py)

## Results & limitations

| 분석 항목 | 결과 | 해석 |
| --- | --- | --- |
| 데이터 규모 | 198경기 · 12팀 · 579,306개 이벤트 | 경기 내 행동의 위치·유형·결과를 활용 |
| 시퀀스 탐색 | 12개 팀의 공격 시퀀스 205개 | 공격 전개와 행동별 VAEP를 대시보드에서 비교 |
| 표현 학습 | TPE 50 trials, 최소 재구성 MSE 0.000360 | [v5.9 실험](docs/versions/v5.9.md)의 탐색 목적함수 값; 독립 테스트 성능과 구분 |

- **평가 한계** — TPE의 학습·평가 시퀀스 중복, VAEP의 행동 단위 분할, 최종 모델의 단일 순서 분할로 인해 독립 경기 일반화 성능은 미확인.
- **해석 한계** — 이벤트 데이터만으로 오프더볼 움직임·수비 대형·의도를 복원할 수 없음. 성과 조건을 만족한 공격만 추출하므로 실패한 공격 전체로 결론을 확장하지 않음.
- **후속 검증** — 경기 단위 holdout과 seed 반복 실험으로 일반화 성능을 평가하고, 확률 calibration·좌표 및 DTW 기반 방법과의 비교·GRU 비교·전문가 군집 해석 평가로 유효성을 검증할 계획.

## Repository structure

```text
deTACTer/
├── README.md                 # 연구 질문·방법·근거·한계
├── config.yaml               # v5.9 설정
├── requirements.txt          # Python 의존성 목록
├── scripts/                  # 전처리·VAEP·학습·군집화·시각화
├── notebooks/                # 탐색·오류 분석·실험 노트북
├── web/                      # 팀별 전술 분석 대시보드
├── data/                     # 입력 데이터·SPADL·정제 데이터
├── results/                  # 모델·임베딩·군집·애니메이션
├── docs/
│   ├── reproduction.md       # 실행 조건·연결 지점·검증 범위
│   ├── research/             # 기획·선행연구·문제 해결 기록
│   ├── versions/             # 버전별 실험
│   ├── references/           # 참고 문헌·BibTeX
│   └── media/                # 시연 영상
└── archive/                  # 이전 실험과 실행 도구
```

## Quick start

- **대시보드** — `web/src/data/sequences.json`을 준비한 뒤 실행. 영상 재생에는 대응하는 MP4 파일이 필요하며 데이터·모델·영상은 저장소에 포함하지 않음.

```powershell
cd web
npm ci
npm run dev
```

- **분석 파이프라인** — 데이터 준비, SPADL 변환, 모델 학습 및 웹 내보내기의 실행 순서와 구현 제약은 [재현 안내](docs/reproduction.md) 참조.
- **기술 스택** — Python · pandas · NumPy · PyTorch · CatBoost · socceraction · scikit-learn · Optuna · Matplotlib / ImageIO · React / Vite.

## References

- **[1]** Decroos, T., Bransen, L., Van Haaren, J., & Davis, J. (2019). *Actions Speak Louder than Goals: Valuing Player Actions in Soccer*. Proceedings of the 25th ACM SIGKDD International Conference on Knowledge Discovery & Data Mining, 1851–1861. [DOI: 10.1145/3292500.3330758](https://doi.org/10.1145/3292500.3330758). — SPADL 및 VAEP의 원 논문.
- **[2]** Decroos, T., Bransen, L., Van Haaren, J., & Davis, J. (2020). *VAEP: An Objective Approach to Valuing On-the-Ball Actions in Soccer (Extended Abstract)*. IJCAI-20, 4696–4700. [DOI: 10.24963/ijcai.2020/648](https://doi.org/10.24963/ijcai.2020/648). — 원 연구의 확장 초록.
- **[3]** ML-KULeuven. *socceraction*: SPADL and action valuation implementation. [소스 코드](https://github.com/ML-KULeuven/socceraction) · [VAEP 문서](https://socceraction.readthedocs.io/en/latest/documentation/valuing_actions/vaep.html).
- **인용 파일** — [references.bib](docs/references/references.bib).
