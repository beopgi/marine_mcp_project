# MCP 기반 LLM Agent 해양 레저 추천 프레임워크 (Prototype MVP)

## 1) 시스템 개요
이 프로젝트는 **"MCP 기반 LLM Agent를 활용한 해양 레저 추천 프레임워크"**의 구조 검증용 프로토타입입니다.
핵심 목표는 단순 챗봇이 아니라 아래 파이프라인을 **코드 계층으로 분리**해 보여주는 것입니다.

- 자연어 입력 → Query Structuring
- Structured Query → MCP Client
- MCP Server → Adapter 조회/정규화/필터링
- Candidate Pool 생성
- 후보군 내부 제한형 최종 추천(Top-1)

---

## 2) 아키텍처 설명

### 계층 및 역할

1. **LLM Agent 계층 (`app/agents`)**
   - `query_structurer.py`: 자연어를 구조화된 질의(JSON)로 변환
   - `prompt_builder.py`: Recommendation Prompt(Role/Task/Format) 구성
   - `recommender.py`: 후보군 제한형 추천 로직(후보군 외 생성 금지)
   - `llm_agent.py`: 전체 흐름 오케스트레이션

2. **MCP Client 계층 (`app/mcp`)**
   - `tool_handler.py`: Tool Request Handling
   - `formatter.py`: Request Formatting
   - `session.py`: Session/Trace ID 관리
   - `client.py`: MCP 요청 orchestration

3. **MCP Server 계층 (`app/mcp/server.py`, `app/tools`, `app/adapters`, `app/services`, `app/repositories`)**
   - `MarineContentQueryTool`: 도구 실행 진입점
   - `MarineContentAPIAdapter`: 외부 API 인터페이스
   - `FilteringService`: 명시 조건 기반 1차 필터링
   - `MarineContentRepository`: 후보군 저장소(in-memory)

4. **API 계층 (`app/api/routes.py`)**
   - 단계별 endpoint와 end-to-end endpoint 제공

---

## 3) 논문 구조 ↔ 코드 구현 대응 관계

- **Query Structuring** → `app/agents/query_structurer.py`
- **Tool Request Handling** → `app/mcp/tool_handler.py`
- **Request Formatting** → `app/mcp/formatter.py`
- **Session Management** → `app/mcp/session.py`
- **Marine Content Query Tool** → `app/tools/marine_content_query_tool.py`
- **External API Adapter** → `app/adapters/base.py`, `mock_adapter.py`, `naver_adapter.py`
- **Filtering** → `app/services/filtering.py`
- **Marine Content DB / Candidate Pool** → `app/repositories/marine_content_repo.py`
- **Recommendation Prompt 기반 통제 추천** → `app/agents/prompt_builder.py`, `app/agents/recommender.py`

---

## 4) 전체 파이프라인 동작

`POST /pipeline/run` 기준:

1. 사용자 자연어 입력 수신
2. `QueryStructurer`가 구조화된 질의 생성
3. `MCPClient`가 세션 생성 + tool 선택 + payload 포맷팅
4. `MCPServer`가 `MarineContentQueryTool` 실행
5. Adapter가 데이터 수집(mock/real)
6. Normalization + Filtering 수행
7. Repository에 후보군 저장
8. 후보군만 LLM Agent에 전달
9. Recommender가 후보군 내부 Top-1 선택 및 이유 반환

---

## 5) 프로젝트 구조

```text
project/
  app/
    main.py
    api/
      routes.py
    core/
      config.py
      logging.py
    schemas/
      query.py
      content.py
      recommendation.py
    agents/
      llm_agent.py
      prompt_builder.py
      query_structurer.py
      recommender.py
    mcp/
      client.py
      server.py
      session.py
      formatter.py
      tool_handler.py
    tools/
      marine_content_query_tool.py
    adapters/
      base.py
      mock_adapter.py
      naver_adapter.py
      weather_adapter.py
    services/
      filtering.py
      normalization.py
      pipeline.py
    repositories/
      marine_content_repo.py
    data/
      mock_marine_contents.json
  tests/
    test_pipeline.py
  .env.example
  requirements.txt
  README.md
```

---

## 6) 설치 및 실행

### 6-1. 의존성 설치
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 6-2. 환경 변수
```bash
cp .env.example .env
```
기본은 `ADAPTER_MODE=mock` 이며 API 키 없이 동작합니다.

### 6-3. 서버 실행
```bash
uvicorn app.main:app --reload --port 8000
```

---

## 7) API 엔드포인트

- `GET /health`
- `POST /query/structure`
- `POST /mcp/search`
- `POST /recommend`
- `POST /pipeline/run`

---

## 8) 샘플 요청/응답

### 8-1. Query Structuring
요청:
```bash
curl -X POST http://127.0.0.1:8000/query/structure \
  -H "Content-Type: application/json" \
  -d '{"user_input":"이번 주말에 부산에서 2명이서 10만원 이하로 낚시하고 싶어"}'
```

응답 예시:
```json
{
  "structured_query": {
    "location": "부산",
    "activity": "낚시",
    "time": {
      "start_datetime": "2026-04-04T00:00:00Z",
      "end_datetime": "2026-04-05T23:59:59.999999Z"
    },
    "price_min": null,
    "price_max": 100000,
    "people_count": 2,
    "duration": null,
    "transport": null,
    "purpose": null,
    "preference": null,
    "avoid": null
  }
}
```

### 8-2. End-to-End Pipeline
요청:
```bash
curl -X POST http://127.0.0.1:8000/pipeline/run \
  -H "Content-Type: application/json" \
  -d '{"user_input":"이번 주말에 부산에서 2명이서 10만원 이하로 낚시하고 싶어"}'
```

응답 예시(요약):
```json
{
  "structured_query": {"location":"부산","activity":"낚시","price_max":100000,"people_count":2},
  "filtered_candidates": [{"id":"mc_001","service_name":"부산 선상 낚시 체험", "price":80000}],
  "final_recommendation": {
    "selected_id": "mc_001",
    "reason": "'부산 선상 낚시 체험'가 위치/활동/예산/인원 조건 적합도가 가장 높습니다.",
    "matched_constraints": ["location","activity","budget","people_count"]
  },
  "trace_id": "trace_xxx"
}
```

---

## 9) mock mode 실행법
- `.env`에서 `ADAPTER_MODE=mock` 설정
- `app/data/mock_marine_contents.json` 기반으로 후보군 생성
- 외부 API 키가 없어도 전체 파이프라인 실행 가능

---

## 10) real adapter로 확장 방법

1. `app/adapters/base.py`의 `MarineContentAPIAdapter` 인터페이스 구현
2. 신규 adapter에서 외부 API 응답을 받아 raw dict 리스트 반환
3. `NormalizationService`에서 공통 스키마(`MarineContentItem`)로 정규화
4. `.env`의 `ADAPTER_MODE` 값과 `build_agent()` 분기 추가

`naver_adapter.py`는 현재 stub 형태로 제공되어 교체 포인트를 명확히 보여줍니다.

---

## 11) 테스트
```bash
pytest -q
```

포함 테스트:
- 질의 구조화 필드 추출 확인
- pipeline 실행 시 추천 ID가 후보군 내부인지 확인(후보군 제한형 추천 보장)

## 12) 포스터
<img width="480" height="801" alt="image" src="https://github.com/user-attachments/assets/13265f9b-8dfb-442b-b5ef-de03d577d322" />

