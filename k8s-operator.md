```
사람이 하던 운영 작업을 코드로 자동화한 컨트롤러"

일반 K8s:
  Deployment, Service, Pod → K8s가 기본 제공
  → "Pod 3개 유지해줘" 정도의 단순한 관리

Operator:
  CRD + Custom Controller
  → "Prometheus 클러스터를 이 설정대로 운영해줘" 같은 복잡한 관리
예를 들어 Prometheus를 수동으로 운영하면:

수동 운영 (사람이 할 일):
  1. Prometheus 설치
  2. 설정 파일 관리
  3. 스크래핑 대상 추가/삭제
  4. 스토리지 관리
  5. 버전 업그레이드
  6. 장애 시 재시작

Prometheus Operator (코드가 할 일):
  → 위의 1~6을 전부 자동으로
  → 사용자는 CRD(ServiceMonitor 등)만 선언하면 됨
# 사용자가 하는 건 이것뿐
apiVersion: monitoring.coreos.com/v1
kind: Prometheus
spec:
  replicas: 2
  retention: 30d
  serviceMonitorSelector:
    matchLabels:
      team: gpu-infra
# → Operator가 알아서 Prometheus 2대 띄우고, 설정하고, 모니터링
GPU 클러스터에서 쓰는 Operator들:

Operator	하는 일
Prometheus Operator	Prometheus + AlertManager 자동 관리
GPU Operator	NVIDIA 드라이버 + DCGM + Device Plugin 자동 설치
Network Operator	Mellanox 드라이버 + SR-IOV 자동 설치
Training Operator	PyTorchJob 등 학습 잡 관리
Operator 패턴 = "운영자(Operator)의 지식을 코드로 만든 것"이에요. 그래서 이름이 Operator 이다.
```
