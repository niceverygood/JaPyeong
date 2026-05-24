"""/v1/chat 라우터 — 룰베이스 사주 JSON + LLM 자문 + 가드레일.

Phase 4 핵심: 3층 책임 분리.
"""

from fastapi import APIRouter, HTTPException

from src.ai import consultation, guardrails
from src.ai.glossary import annotate_hanja
from src.api.v1.chat_schemas import ChatRequest, ChatResponse, CitationDTO
from src.services import saju_service

router = APIRouter(prefix="/v1/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
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

    # 4. 한자 → '한글(한자)' 자동 병기 (모든 텍스트 필드)
    return ChatResponse(
        answer=annotate_hanja(post.answer),
        basis=annotate_hanja(result.basis),
        perspective=annotate_hanja(result.perspective),
        timing=annotate_hanja(result.timing),
        cautions=[annotate_hanja(c) for c in result.cautions],
        citations=[
            CitationDTO(
                source=annotate_hanja(c.source),
                volume=annotate_hanja(c.volume) if c.volume else None,
            )
            for c in result.citations
        ],
        contested=[annotate_hanja(c) for c in result.contested],
        confidence=result.confidence,
        follow_up_suggestions=[annotate_hanja(s) for s in result.follow_up_suggestions],
        flags=list(post.flags),
        model=result.model,
    )
