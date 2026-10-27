"""Owner-scoped plan reads and optimistic, explicit checklist writes."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from app.models import StudyPlan, StudyStep, Workspace
from app.routes import owned_workspace
from app.security import get_session

router = APIRouter(prefix='/workspaces/{workspace_id}/plans', tags=['Study plans'])


class RevisionInput(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    revision: int = Field(ge=0)


class StepInput(RevisionInput):
    done: bool


def owned_plan(session, workspace_id, plan_id):
    plan = session.scalar(select(StudyPlan).where(StudyPlan.id == plan_id, StudyPlan.workspace_id == workspace_id))
    if plan is None: raise HTTPException(404, 'Không tìm thấy kế hoạch.')
    return plan


def plan_out(session, plan):
    steps = session.scalars(select(StudyStep).where(StudyStep.plan_id == plan.id)).all()
    return dict(id=plan.id, workspace_id=plan.workspace_id, status=plan.status, revision=plan.revision,
                spec=plan.spec, progress={s.step_key: s.done for s in steps})


@router.get('/{plan_id}')
def read_plan(plan_id: UUID, response: Response, workspace: Workspace = Depends(owned_workspace), session: Session = Depends(get_session)):
    response.headers['Cache-Control'] = 'no-store'
    return plan_out(session, owned_plan(session, workspace.id, plan_id))


def change_revision(session, plan, expected, **values):
    changed = session.execute(update(StudyPlan).where(StudyPlan.id == plan.id, StudyPlan.revision == expected)
        .values(revision=expected+1, **values))
    if changed.rowcount != 1:
        session.rollback()
        raise HTTPException(409, 'Kế hoạch đã thay đổi ở nơi khác. Tải lại thẻ kế hoạch.')


@router.post('/{plan_id}/confirm')
def confirm_plan(plan_id: UUID, data: RevisionInput, response: Response,
                 workspace: Workspace = Depends(owned_workspace), session: Session = Depends(get_session)):
    response.headers['Cache-Control'] = 'no-store'
    plan = owned_plan(session, workspace.id, plan_id)
    if plan.status != 'draft': raise HTTPException(409, 'Kế hoạch đã được xác nhận. Tải lại thẻ kế hoạch.')
    change_revision(session, plan, data.revision, status='confirmed')
    session.commit(); session.refresh(plan)
    return plan_out(session, plan)


@router.patch('/{plan_id}/steps/{step_key}')
def mark_step(plan_id: UUID, step_key: str, data: StepInput, response: Response,
              workspace: Workspace = Depends(owned_workspace), session: Session = Depends(get_session)):
    response.headers['Cache-Control'] = 'no-store'
    plan = owned_plan(session, workspace.id, plan_id)
    if plan.status != 'confirmed': raise HTTPException(409, 'Xác nhận kế hoạch trước khi đánh dấu tiến độ.')
    step = session.scalar(select(StudyStep).where(StudyStep.plan_id == plan.id, StudyStep.step_key == step_key))
    if step is None: raise HTTPException(404, 'Không tìm thấy bước học.')
    change_revision(session, plan, data.revision)
    step.done = data.done
    session.commit(); session.refresh(plan)
    return plan_out(session, plan)
