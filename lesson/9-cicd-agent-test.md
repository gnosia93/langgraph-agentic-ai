## 에이전트 로직 테스트 자동화 ##
에이전트 로직 테스트의 핵심은 "에이전트가 뭘 했는지(trajectory)"와 "결과가 좋은지(llm-rubric)"를 분리해서 테스트하는 것이다. 도구를 제대로 골랐는데 답변이 구리면 프롬프트 문제이고, 도구를 잘못 골랐으면 라우팅 로직 문제인 것이다.

### 1. 단위 테스트: 개별 도구/노드 테스트 ###
에이전트의 각 구성 요소를 독립적으로 테스트 하는것으로 일반 소프트웨어 단위 테스트와 동일하다.

[단위 테스트 샘플]
```
# pytest로 LangGraph 노드 개별 테스트
import pytest

def test_search_tool():
    result = search_tool.invoke({"query": "EKS 버전"})
    assert result is not None
    assert len(result) > 0

def test_retriever_node():
    state = {"question": "쿠버네티스란?"}
    result = retriever_node(state)
    assert "documents" in result
    assert len(result["documents"]) > 0
```
* 각 도구가 정상 동작하는가
* 각 노드가 올바른 출력을 내는가


### 2. 통합 테스트: 에이전트 전체 흐름 테스트 ###
에이전트가 올바른 도구를 올바른 순서로 호출하는지 검증하는 것으로 promptfoo의 trajectory assert 를 활용한다.
```
# promptfooconfig.yaml
providers:
  - id: http://localhost:8000/agent  # 에이전트 API 엔드포인트

tests:
  - vars:
      input: "서울 날씨 알려줘"
    assert:
      # 올바른 도구를 호출했는가
      - type: trajectory:tool-used
        value: weather_search

      # 도구 호출 순서가 맞는가
      - type: trajectory:tool-sequence
        value:
          - weather_search
          - format_response

      # 도구에 올바른 인자를 넘겼는가
      - type: trajectory:tool-args-match
        value:
          tool: weather_search
          args:
            location: "서울"

      # 최종 응답 품질
      - type: llm-rubric
        value: "서울의 현재 날씨 정보가 포함되어 있는가?"

  - vars:
      input: "이 PDF 요약해줘"
    assert:
      - type: trajectory:tool-used
        value: document_reader
      - type: trajectory:goal-success
        value: "사용자가 요청한 문서를 요약했는가?"
```
* 에이전트가 올바른 도구를 호출하는가 (trajectory:tool-used)
* 호출 순서가 맞는가 (trajectory:tool-sequence)
* 최종 응답 품질이 기준을 충족하는가 (llm-rubric)
* 보안 취약점은 없는가 (red-team)

### 3. CI/CD 파이프라인에 통합 ###

[github action 샘플]
```
# .github/workflows/agent-test.yml
name: Agent Test

on:
  pull_request:
    paths:
      - 'agent/**'
      - 'prompts/**'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # 단위 테스트
      - name: Unit Tests
        run: pytest tests/unit/

      # 에이전트 서버 띄우기
      - name: Start Agent
        run: docker compose up -d agent

      # promptfoo로 에이전트 통합 테스트
      - name: Agent Eval
        run: npx promptfoo@latest eval --ci
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}

      # 결과 확인 (실패 시 PR 블록)
      - name: Check Results
        run: npx promptfoo@latest eval --ci --fail-on-error
```

## 추가 정보 ##

1. 단위 테스트: "결정론적(Deterministic)" 검증작성하신 코드처럼 도구가 '살아있는지' 보는 것도 중요하지만, Edge case 대응 여부를 단위 테스트에 포함하면 더 탄탄해집니다.팁: search_tool이 아무 결과도 못 찾았을 때 에이전트가 죽지 않고 빈 리스트를 잘 반환하는지, 혹은 에러를 던지는지 확인하는 테스트를 추가해 보세요.

2. 통합 테스트: promptfoo 활용의 묘미trajectory 어설션(Assertion)을 사용하신 건 정말 좋은 선택입니다. 에이전트 개발에서 가장 골치 아픈 게 "답변은 그럴싸한데, 사실 엉뚱한 도구를 써서 만든 가짜 정보(Hallucination)"일 때가 많거든요.팁: llm-rubric을 사용할 때, 가끔 검사역(LLM)이 너무 너그러울 수 있습니다. threshold 값을 조절하거나, 중요한 비즈니스 로직은 javascript 기반 커스텀 단언문을 섞어 쓰면 더 정교해집니다.

3. CI/CD 파이프라인: 비용과 시간 관리에이전트 테스트는 일반 코드 테스트보다 비싸고 느립니다. (LLM 호출 비용 + 지연 시간)팁: 모든 PR마다 전체 통합 테스트를 돌리기 부담스럽다면, promptfoo의 cache 기능을 활성화하여 동일한 입력에 대한 중복 호출을 막으세요.중요: red-team 테스트는 시간이 꽤 걸리므로, 매 PR 보다는 Daily Cron Job이나 배포 직전 단계로 분리하는 것도 방법입니다.

4. 추가 제언: 골든 데이터셋(Golden Dataset)테스트 케이스가 늘어나면 관리가 힘들어집니다. "이 질문에는 반드시 A 도구를 써야 한다"는 기준이 명확한 골든 데이터셋을 만들어 관리하시면, 프롬프트를 수정했을 때 발생하는 Regression(성능 퇴화)을 잡는 데 매우 효과적입니다.
