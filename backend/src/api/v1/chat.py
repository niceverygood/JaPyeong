"""/v1/chat 라우터 — 룰베이스 사주 JSON + LLM 자문 + 가드레일.

Phase 4 핵심: 3층 책임 분리.
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from src.ai import consultation, guardrails
from src.ai.glossary import annotate_hanja
from src.ai.tone_down import tone_down
from src.api.v1.chat_schemas import ChatRequest, ChatResponse, CitationDTO
from src.engine.schema import BirthInfo
from src.middleware.rate_limit import get_limiter, resolve_user_id
from src.services import saju_service, teaser_service
from src.services.coin_catalog import get_spend_item
from src.services.user_service import get_user_tier

router = APIRouter(prefix="/v1/chat", tags=["chat"])


class TeaserRequest(BaseModel):
    birth: BirthInfo
    question: str | None = Field(default=None, max_length=2000)


@router.post("/teaser")
async def teaser(req: TeaserRequest, request: Request) -> dict:
    """무료 맛보기 — 결정론 명식에서 즉시 생성한 '내 한 줄' + 전체 풀이 잠금 안내.

    LLM 미사용(무료·즉시). 전환 퍼널의 1단계: 신뢰를 주고 전체 풀이를 결제로 잇는다.
    """
    await get_limiter().enforce_ip_only(request)
    try:
        natal = saju_service.analyze_natal(req.birth).model_dump()
    except NotImplementedError as e:
        raise HTTPException(422, str(e)) from e
    except ValueError as e:
        raise HTTPException(400, str(e)) from e

    result = teaser_service.build_teaser(natal, req.question, req.birth.year)
    item = get_spend_item("consult_one")
    # 결제 경로를 명확히: (1) 무료 일일 한도 내 AI 자문, (2) 코인 1회 심층, (3) 구독 무제한
    result["unlock"] = {
        "free": "무료 일일 한도 내 AI 자문",
        "coin_item": "consult_one",
        "coin_cost": item.cost if item else 4900,
        "coin_label": "심층 정밀 풀이 1회",
        "subscription_label": "구독 시 심층 무제한",
    }
    return result


def _post(text: str) -> str:
    """모든 LLM 응답 텍스트 필드에 적용할 후처리 파이프라인.

    1. 단정 표현 톤다운 (HIGH + MED)
    2. 한자 자동 병기 (한글(漢字))
    """
    return annotate_hanja(tone_down(text))


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest, request: Request) -> ChatResponse:
    # -1. Rate limit — 티어별 일일 한도(anon 5 / basic 20 / std 100 / prem·family 500)
    # 권한은 JWT 신원 → DB 활성구독에서 결정(클레임 미신뢰). 결제 즉시 상향, 해지 즉시 강등.
    tier = await get_user_tier(resolve_user_id(request))
    await get_limiter().enforce(request, user_tier=tier)
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
        result = consultation.consult(
            natal=natal, question=req.question, user_tier=tier
        )
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
