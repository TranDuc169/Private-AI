"""Read-only workspace learning activity, never a mastery estimate."""
from fastapi import APIRouter, Depends, Response
from sqlalchemy import select, func, case
from sqlalchemy.orm import Session
from app.models import Workspace, Document, StudyPlan, StudyStep, Quiz, QuizAttempt
from app.routes import owned_workspace
from app.security import get_session
from app.planning import CURRICULUM

router=APIRouter(prefix='/workspaces/{workspace_id}',tags=['Learning progress'])


@router.get('/progress')
def progress(response: Response, workspace: Workspace=Depends(owned_workspace), session: Session=Depends(get_session)):
    response.headers['Cache-Control']='no-store'
    wid=workspace.id
    document_counts=dict(session.execute(select(Document.index_status,func.count()).where(Document.workspace_id==wid).group_by(Document.index_status)).all())
    plan_counts=dict(session.execute(select(StudyPlan.status,func.count()).where(StudyPlan.workspace_id==wid).group_by(StudyPlan.status)).all())
    steps=session.execute(select(func.count(StudyStep.id),func.coalesce(func.sum(case((StudyStep.done.is_(True),1),else_=0)),0)).join(StudyPlan).where(StudyPlan.workspace_id==wid,StudyPlan.status=='confirmed')).one()
    topic_key=Quiz.spec['topic_key'].as_string()
    question_count=func.json_array_length(Quiz.spec['questions'])
    grouped=session.execute(select(topic_key,func.count(QuizAttempt.id),func.sum(QuizAttempt.score),func.sum(question_count)).select_from(QuizAttempt).join(Quiz,QuizAttempt.quiz_id==Quiz.id).where(Quiz.workspace_id==wid,Quiz.status=='approved').group_by(topic_key)).all()
    stats={key:dict(attempts=n,correct=correct,total=total) for key,n,correct,total in grouped}
    # Limit lists, not aggregate totals. Full records remain accessible in History.
    plan_rows=session.execute(select(StudyPlan.id,StudyPlan.conversation_id,StudyPlan.status,StudyPlan.spec['request']['goal'].as_string(),StudyPlan.created_at).where(StudyPlan.workspace_id==wid).order_by(StudyPlan.created_at.desc(),StudyPlan.id.desc()).limit(20)).all()
    recent=session.execute(select(Quiz.id,Quiz.conversation_id,topic_key,QuizAttempt.score,question_count,QuizAttempt.created_at).select_from(Quiz).join(QuizAttempt,QuizAttempt.quiz_id==Quiz.id).where(Quiz.workspace_id==wid,Quiz.status=='approved').order_by(QuizAttempt.created_at.desc(),QuizAttempt.id.desc()).limit(20)).all()
    return dict(workspace_id=wid,documents=document_counts,plans=plan_counts,
        checklist=dict(completed=steps[1],total=steps[0]),
        topics=[dict(key=key,title=title,**stats.get(key,dict(attempts=0,correct=0,total=0))) for key,(title,_) in CURRICULUM.items()],
        recent_plans=[dict(id=p,conversation_id=c,status=status,goal=goal,created_at=created) for p,c,status,goal,created in plan_rows],
        recent_results=[dict(quiz_id=q,conversation_id=c,topic_key=k,score=score,total=total,submitted_at=created) for q,c,k,score,total,created in recent],
        recent_limit=20,limitation='Checklist là tự đánh dấu trên kế hoạch đã xác nhận. Điểm quiz là số câu đúng cộng dồn qua các lần nộp, có thể lặp câu; không chứng nhận thành thạo.')
