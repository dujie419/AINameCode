from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import AuthHandler
from dependencies import get_session
from models.marketplace import CommunityCandidate, CommunityPost, CommunityVote
from models.name_record import NameCandidate, NameRecord
from schemas.marketplace import CommunityCandidateOut, CommunityPostCreateIn, CommunityPostOut, CommunityResultOut, CommunityVoteIn, PageOut
from services.quota_service import ensure_quota_available, record_usage

router = APIRouter(prefix="/community", tags=["community"])
auth_handler = AuthHandler()


def candidate_to_out(candidate: CommunityCandidate):
    return CommunityCandidateOut(
        id=candidate.id,
        post_id=candidate.post_id,
        name_candidate_id=candidate.name_candidate_id,
        name=candidate.name,
        description=candidate.description,
        reference=candidate.reference or "",
        moral=candidate.moral or "",
        domain=candidate.domain or "",
        vote_count=candidate.vote_count,
    )


async def post_to_out(session: AsyncSession, post: CommunityPost):
    result = await session.execute(select(CommunityCandidate).where(CommunityCandidate.post_id == post.id))
    return CommunityPostOut(
        id=post.id,
        user_id=post.user_id,
        naming_type=post.naming_type,
        name_record_id=post.name_record_id,
        title=post.title,
        description=post.description,
        status=post.status,
        created_at=post.created_at,
        candidates=[candidate_to_out(x) for x in result.scalars().all()],
    )


@router.post("/posts", response_model=CommunityPostOut)
async def create_post(
        data: CommunityPostCreateIn,
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session),
):
    await ensure_quota_available(user_id, "vote_publish", session)
    source_candidates = []
    naming_type = data.naming_type

    if data.name_record_id:
        record = await session.scalar(
            select(NameRecord).where(NameRecord.id == data.name_record_id, NameRecord.user_id == int(user_id))
        )
        if not record:
            raise HTTPException(status_code=404, detail="命名记录不存在或无权使用")
        if data.naming_type and data.naming_type != record.naming_type:
            raise HTTPException(status_code=400, detail="投票类型与命名记录类型不一致")
        naming_type = record.naming_type
        result = await session.execute(
            select(NameCandidate).where(NameCandidate.record_id == record.id).order_by(NameCandidate.id.asc())
        )
        source_candidates = result.scalars().all()
        if len(source_candidates) < 2:
            raise HTTPException(status_code=400, detail="命名记录至少需要两个候选名才能发起投票")
    else:
        names = [item.strip() for item in data.candidates if item and item.strip()]
        if len(names) < 2:
            raise HTTPException(status_code=400, detail="至少填写两个候选名称")
        source_candidates = names

    post = CommunityPost(
        user_id=int(user_id),
        naming_type=naming_type,
        name_record_id=data.name_record_id,
        title=data.title,
        description=data.description,
        status="active",
    )
    session.add(post)
    await session.flush()
    for item in source_candidates:
        if isinstance(item, NameCandidate):
            session.add(CommunityCandidate(
                post_id=post.id,
                name_candidate_id=item.id,
                name=item.name,
                reference=item.reference,
                moral=item.moral,
                domain=item.domain,
            ))
        else:
            session.add(CommunityCandidate(post_id=post.id, name=item))
    await session.commit()
    await session.refresh(post)
    await record_usage(user_id, "vote_publish", session, reason="发布投票", related_id=post.id)
    return await post_to_out(session, post)


@router.get("/posts", response_model=PageOut)
async def list_posts(
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100),
        sort: str = Query("latest"),
        session: AsyncSession = Depends(get_session),
):
    stmt = select(CommunityPost).where(CommunityPost.status == "active")
    if sort == "hot":
        stmt = stmt.outerjoin(CommunityCandidate, CommunityCandidate.post_id == CommunityPost.id).group_by(CommunityPost.id).order_by(desc(func.sum(CommunityCandidate.vote_count)))
    else:
        stmt = stmt.order_by(CommunityPost.id.desc())
    total = await session.scalar(select(func.count(CommunityPost.id)).where(CommunityPost.status == "active"))
    result = await session.execute(stmt.offset((page - 1) * page_size).limit(page_size))
    items = [await post_to_out(session, x) for x in result.scalars().all()]
    return {"total": total or 0, "page": page, "page_size": page_size, "items": items}


@router.get("/posts/{post_id}", response_model=CommunityPostOut)
async def post_detail(post_id: int, session: AsyncSession = Depends(get_session)):
    post = await session.scalar(select(CommunityPost).where(CommunityPost.id == post_id, CommunityPost.status == "active"))
    if not post:
        raise HTTPException(status_code=404, detail="投票不存在")
    return await post_to_out(session, post)


@router.post("/posts/{post_id}/vote")
async def vote_post(
        post_id: int,
        data: CommunityVoteIn,
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session),
):
    candidate = await session.scalar(
        select(CommunityCandidate)
        .where(CommunityCandidate.id == data.candidate_id, CommunityCandidate.post_id == post_id)
        .with_for_update()
    )
    if not candidate:
        raise HTTPException(status_code=404, detail="候选项不存在")
    exists_vote = await session.scalar(select(CommunityVote).where(CommunityVote.post_id == post_id, CommunityVote.user_id == int(user_id)))
    if exists_vote:
        raise HTTPException(status_code=400, detail="同一用户只能投一次")

    try:
        session.add(CommunityVote(post_id=post_id, candidate_id=data.candidate_id, user_id=int(user_id)))
        candidate.vote_count += 1
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=400, detail="同一用户只能投一次")

    return {"message": "投票成功"}


@router.get("/posts/{post_id}/result", response_model=CommunityResultOut)
async def post_result(post_id: int, session: AsyncSession = Depends(get_session)):
    candidate = await session.scalar(
        select(CommunityCandidate).where(CommunityCandidate.post_id == post_id).order_by(CommunityCandidate.vote_count.desc())
    )
    if not candidate:
        raise HTTPException(status_code=404, detail="暂无投票结果")
    return {"winner": candidate.name, "vote_count": candidate.vote_count}


@router.get("/rank")
async def community_rank(session: AsyncSession = Depends(get_session)):
    week_start = datetime.now() - timedelta(days=7)
    result = await session.execute(
        select(CommunityCandidate)
        .join(CommunityPost, CommunityPost.id == CommunityCandidate.post_id)
        .where(CommunityPost.created_at >= week_start, CommunityPost.status == "active")
        .order_by(CommunityCandidate.vote_count.desc())
        .limit(10)
    )
    return [candidate_to_out(x) for x in result.scalars().all()]
