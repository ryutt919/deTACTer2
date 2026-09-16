# 스포츠 전술 및 궤적 클러스터링 관련 선행 연구 조사

축구 시퀀스 데이터와 공의 이동 궤적을 활용한 전술 추출 연구 사례를 조사하여 정리했습니다.

## 연구 1: DTW를 활용한 침투 스포츠(Invasion Sports) 궤적 분석

- **제목**: *A Framework for Clustering and Comparing Ball Trajectories in Basketball* (PLOS ONE, 2018)
- **주요 방법론**:
  - **DTW (Dynamic Time Warping)**: 시간적 흐름이 가변적인 농구의 슛 및 패스 궤적을 비교하기 위해 DTW를 사용.
  - **고정적 유클리디안 거리의 한계 극복**: 움직임의 속도가 달라도 위상학적으로 유사한 궤적을 동일한 패턴으로 인식.
- **결과**: 슛의 성공 여부나 공격 전술의 유형(예: Pick and Roll)을 궤적 형태만으로 자동 분류할 수 있음을 입증.

## 연구 2: TRACLUS 프레임워크를 이용한 부분 전술 패턴 추출

- **핵심 문헌**: *Trajectory Clustering: A Partition-and-Group Framework* (Lee et al., SIGMOD 2007)
- **주요 방법론**:
  - **Partition-and-Group**: 궤적 전체가 아닌 '유사한 선분'들의 군집을 찾음.
  - **MDL (Minimum Description Length)**: 데이터 압축 효율을 기준으로 궤적이 꺾이는 핵심 지점(Characteristic Points)을 자동 추출.
- **축구 적용 의의**: 축구 공격 시퀀스에서 빌드업 과정은 달라도 '최종 박스 침투'나 '측면 크로스'와 같은 특정 부분 전술이 반복되는 것을 포착하는 데 효과적임.

## 연구 3: 딥러닝 기반의 이동 패턴 인식 및 임베딩

- **제목**: *Learning Soccer Tactical Patterns using Deep Convolutional Neural Networks* (2017)
- **주요 방법론**:
  - **RNN/LSTM**: 시퀀스 데이터를 고정된 차원의 벡터(Embedding)로 변환.
  - **Autoencoder**: 비지도 학습을 통해 전술적 의도가 담긴 잠재 공간(Latent Space)을 구축하고 여기서 클러스터링 수행.
- **특징**: 단순히 기하학적 유사성을 넘어, 앞뒤 맥락(Context)을 고려한 전술적 유사성을 학습함.

---

## 시사점 및 우리 프로젝트의 방향

1. **가변 길이 대응**: 대부분의 선행 연구가 DTW나 Partitioning(TRACLUS)을 통해 시퀀스 길이의 불일치 문제를 해결함.
2. **부분 유사성의 중요성**: 축구는 90분 내내 불규칙하게 움직이므로, 전체를 보기보다는 의미 있는 '분할된 선분'의 조합을 보는 TRACLUS 방식이 실전 전술 추출에 가장 유리함.
3. **직선 조합의 특징 활용**: 사용자의 데이터가 "직선들의 조합"이라는 점은 TRACLUS의 선분 기반 접근과 완벽하게 일치함.
