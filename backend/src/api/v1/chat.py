"""/v1/chat 라우터 — 룰베이스 사주 JSON + LLM 자문 + 가드레일.

Phase 4 핵심: 3층 책임 분리.
"""

from fastapi import APIRouter, HTTPException, Request

from src.ai import consultation, guardrails
from src.ai.glossary import annotate_hanja
from src.ai.tone_down import tone_down
from src.api.v1.chat_schemas import ChatRequest, ChatResponse, CitationDTO
from src.middleware.rate_limit import get_limiter
from src.services import saju_service

router = APIRouter(prefix="/v1/chat", tags=["chat"])


def _post(text: str) -> str:
    """모든 LLM 응답 텍스트 필드에 적용할 후처리 파이프라인.

    1. 단정 표현 톤다운 (HIGH + MED)
    2. 한자 자동 병기 (한글(漢字))
    """
    return annotate_hanja(tone_down(text))


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest, request: Request) -> ChatResponse:
    # -1. Rate limit — 비회원 일일 5회 / IP 분당 60 / IP 일일 1000
    # TODO Sprint 1-2: user_tier 를 JWT 에서 추출
    await get_limiter().enforce(request, user_tier="anon")
    # 0. 입력 위기 키워드 검사 — 즉시 상담 안내로 단축
    pre = guardrails.check_question(req.question)
    if not pre.safe:
        return ChatResponse(
            answer=pre.answer,
            basis="안전 안내",
            confidence="high",
            flags=list(pre.flags),
            model="(guardrail)",
        )

    # 1. 룰베이스 원국 JSON
    try:
        natal = saju_service.analyze_natal(req.birth).model_dump()
    except NotImplementedError as e:
        raise HTTPException(422, str(e)) from e
    except ValueError as e:
        raise HTTPException(400, str(e)) from e

    # 2. LLM 자문
    try:
        result = consultation.consult(natal=natal, question=req.question)
    except RuntimeError as e:
        # ANTHROPIC_API_KEY 미설정
        raise HTTPException(503, str(e)) from e
    except Exception as e:
        # 네트워크·파싱 실패 등
        raise HTTPException(502, f"자문 호출 실패: {e}") from e

    # 3. 후처리 가드레일
    post = guardrails.filter_answer(result.answer)

    # 4. 후처리 — 톤다운 + 한자 자동 병기 (모든 텍스트 필드)
    return ChatResponse(
        answer=_post(post.answer),
        basis=_post(result.basis),
        perspective=_post(result.perspective),
        timing=_post(result.timing),
        cautions=[_post(c) for c in result.cautions],
        citations=[
            CitationDTO(
                source=_post(c.source),
                volume=_post(c.volume) if c.volume else None,
            )
            for c in result.citations
        ],
        contested=[_post(c) for c in result.contested],
        confidence=result.confidence,
        follow_up_suggestions=[_post(s) for s in result.follow_up_suggestions],
        flags=list(post.flags),
        model=result.model,
    )
