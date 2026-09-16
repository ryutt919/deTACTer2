# 포트폴리오 정리 기록

- **기준 저장소** — 로컬 `DACON_K_League`, commit `5324a26` (`5.9 완성`). `git clone --no-hardlinks`로 형제 폴더 `deTACTer`에 이력 포함 복제.
- **브랜치** — `portfolio/research-readme`. 원본 저장소는 수정하지 않음. 원격 주소는 기존 `https://github.com/ryutt919/deTACTer.git`를 유지하며 push는 수행하지 않음.
- **실행 코드** — `scripts/`, `web/`, `notebooks/`의 기존 위치 유지. 스크립트 상호 import와 실행 경로를 보존하기 위해 분석 단계를 문서에서 구분.

| 이전 위치 | 정리 후 위치 | 이유 |
| --- | --- | --- |
| 루트의 BAT / PowerShell / 보조 Python 실행기 | `archive/runners/` | 과거 실행 도구와 현재 분석 코드 구분 |
| `프로젝트 기획서.md` | `docs/research/proposal.md` | 기획 자료 모음 |
| `todo.md` | `docs/research/engineering-log.md` | 원문 문제 해결 이력 보존 |
| 선행연구·클러스터링 문서 | `docs/research/` | 연구 문서 모음 |
| `VAEP 논문.pdf` | `docs/references/vaep-original.pdf` | 참고 문헌 및 BibTeX와 함께 관리 |
| 루트 최종 산출물·인증서 PDF | `docs/reports/` | 원본의 미추적 자료까지 복사 |
| 루트 데모 영상 2개 | `docs/media/` | 로컬 시연 자료 보관 |
| 버전 미지정 `results/*` | `archive/results/` | 과거 결과를 v5.9 재현 결과와 구분 |
| 미추적 `deTACTer5.9/` | `archive/releases/v5.9/` | 제출 폴더 전체를 로컬에 보존 |
| 제출본 `web/src/data/sequences.json` | 현재 `web/src/data/sequences.json`에도 복사 | 기존 웹 코드의 누락된 정적 입력 복구 |

- **경로 수정** — 19개 분석 스크립트의 `c:/Users/Public/Documents/DIK/deTACTer` 리터럴을 파일 위치 기반 루트로 치환. 로직 변경 없음.
- **의존성 문서** — 제출본의 pip 목록에서 `python`, `sqlite3`를 제외하고 영상·그림 의존성을 추가. 환경 고정 또는 학습 재검증으로 간주하지 않음.
- **보존 원칙** — 연구 기록·아카이브 문서의 과거 수치는 원문 유지. 현재 코드와 다르면 새 README 및 재현 문서에서 구분.
- **Git 제외** — 원시·가공 데이터, 웹 JSON, 모델·임베딩·실험 DB·영상, `archive/` 전체 내용, 사용하지 않는 React 기본 이미지와 실행 결과 포함 중복 노트북, 가상환경·캐시·로그·빌드 결과.
- **폴더 보존** — 데이터·결과·웹 데이터·영상·아카이브 폴더는 디렉터리와 `.gitkeep` 예외 규칙으로 구조만 추적. 처음 실행할 때 필요한 SPADL·refined·models·embeddings·clustering·animations 폴더도 준비.
- **기존 추적 정리** — ignore 대상은 `git rm --cached`로 인덱스에서만 제거. 실제 로컬 파일은 삭제하지 않고 해시로 보존 확인. 기존 Git 커밋 이력의 파일은 소급 제거하지 않음.

## 검증 결과

- **Python 구문** — `scripts/`의 24개 파일 AST 파싱 통과.
- **알고리즘 보존** — 경로 치환을 역변환한 AST와 원본 AST를 비교하여 24개 파일의 로직 동일성 확인.
- **파일 보존** — 입력 데이터, 제출 폴더 전체, 웹 JSON의 SHA-256 일치 확인.
- **문서 연결** — 새 README·재현 안내·정리 기록·참고 문헌의 로컬 파일 링크 검사 통과.
- **웹 빌드** — `npm ci --no-audit --no-fund` 및 `npm run build` 성공; Node.js 24.12.0 / npm 11.6.2 / lockfile 기준 Vite 7.3.1.
- **기존 경고** — CSS의 `@import` 순서, 오래된 Browserslist 데이터, 500 kB 초과 번들 경고가 출력됨. 빌드는 성공했으며 UI 코드 수정·번들 최적화는 수행하지 않음.
- **검증 범위** — production build까지만 확인; 브라우저 상호작용·전술 영상 재생·전체 학습 및 인코딩은 검증하지 않음.
- **원본 상태** — 원본 Git working tree는 작업 전과 동일한 미추적 PDF 2개와 제출 폴더만 존재.
