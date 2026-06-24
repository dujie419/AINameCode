import json
from uuid import uuid4

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import AuthHandler
from core.workflow import feedback_names, generate_naming_graph, generate_naming_graph_v2
from dependencies import get_session
from models.name_record import NameCandidate, NameRecord
from schemas.name_schemas import FeedbackSchema, NameIn, NameOutSchema, NameOutSchemaWithThreadOut
from services.quota_service import ensure_quota_available, record_usage

auth_handler = AuthHandler()
router = APIRouter(prefix="/name", tags=["name"])


def record_keyword(name_info: NameIn) -> str:
    parts = [name_info.surname, name_info.other]
    return " ".join([str(item) for item in parts if item]).strip()


async def save_name_record(
        session: AsyncSession,
        user_id: int,
        thread_id: str,
        name_info: NameIn,
        result: dict,
        source_type: str = "generate",
        feedback: str | None = None,
        parent_record_id: int | None = None,
) -> NameRecord:
    names = result.get("names") or []
    record = NameRecord(
        user_id=int(user_id),
        thread_id=thread_id,
        naming_type=name_info.category,
        source_type=source_type,
        keyword=record_keyword(name_info),
        surname=name_info.surname or "",
        gender=name_info.gender or "",
        length=name_info.length or "",
        exclude_words=",".join(name_info.exclude or []),
        feedback=feedback,
        request_json=name_info.model_dump_json(),
        result_json=json.dumps(result, ensure_ascii=False),
        status="success",
        parent_record_id=parent_record_id,
    )
    session.add(record)
    await session.flush()

    for item in names:
        if hasattr(item, "model_dump"):
            item = item.model_dump()
        session.add(NameCandidate(
            record_id=record.id,
            user_id=int(user_id),
            name=item.get("name", ""),
            reference=item.get("reference", ""),
            moral=item.get("moral", ""),
            domain=item.get("domain", ""),
            domain_status=item.get("domain_status", ""),
        ))

    await session.commit()
    await session.refresh(record)
    return record


@router.post("/get_names", response_model=NameOutSchema)
async def get_names(
        name_info: NameIn,
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session),
):
    await ensure_quota_available(user_id, "name_generate", session)
    result = await generate_naming_graph(name_info, user_id)
    record = await save_name_record(
        session=session,
        user_id=user_id,
        thread_id=str(uuid4()),
        name_info=name_info,
        result=result,
        source_type="generate",
    )
    await record_usage(user_id, "name_generate", session, reason="AI 起名", related_id=record.id)
    return NameOutSchema(names=result["names"])


@router.post("/generate", response_model=NameOutSchemaWithThreadOut)
async def generate_names(
        name_info: NameIn,
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session),
):
    await ensure_quota_available(user_id, "name_generate", session)
    result = await generate_naming_graph_v2(name_info, user_id)
    record = await save_name_record(
        session=session,
        user_id=user_id,
        thread_id=result["thread_id"],
        name_info=name_info,
        result=result["names"],
        source_type="generate",
    )
    await record_usage(user_id, "name_generate", session, reason="AI 起名", related_id=record.id)
    return NameOutSchemaWithThreadOut(
        thread_id=result["thread_id"],
        name_record_id=record.id,
        names=result["names"]["names"],
    )


@router.post("/feedback", response_model=NameOutSchemaWithThreadOut)
async def feedback(
        data: FeedbackSchema,
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session),
):
    await ensure_quota_available(user_id, "name_generate", session)
    result = await feedback_names(data, user_id)
    parent_record = await session.scalar(
        select(NameRecord)
        .where(NameRecord.user_id == int(user_id), NameRecord.thread_id == data.thread_id)
        .order_by(NameRecord.id.desc())
    )
    name_info = NameIn.model_construct(
        category=data.category,
        surname=parent_record.surname if parent_record else "",
        gender=parent_record.gender if parent_record else "",
        length=parent_record.length if parent_record else "",
        other=parent_record.keyword if parent_record else "",
        exclude=(parent_record.exclude_words.split(",") if parent_record and parent_record.exclude_words else []),
    )
    record = await save_name_record(
        session=session,
        user_id=user_id,
        thread_id=data.thread_id,
        name_info=name_info,
        result=result["names"],
        source_type="feedback",
        feedback=data.feedback,
        parent_record_id=parent_record.id if parent_record else None,
    )
    await record_usage(user_id, "name_generate", session, reason="AI 起名反馈重生成", related_id=record.id)
    return NameOutSchemaWithThreadOut(
        thread_id=result["thread_id"],
        name_record_id=record.id,
        names=result["names"]["names"],
    )
