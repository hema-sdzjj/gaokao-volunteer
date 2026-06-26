"""志愿表CRUD服务"""
from datetime import datetime
from sqlalchemy.orm import Session
from models import VolunteerTable
from schemas import SaveVolunteerRequest, VolunteerItem


class VolunteerService:
    """志愿表管理"""

    def __init__(self, db: Session):
        self.db = db

    def save(self, request: SaveVolunteerRequest) -> VolunteerTable:
        """保存或更新志愿表"""
        existing = self.db.query(VolunteerTable).filter(
            VolunteerTable.user_identifier == request.user_identifier,
            VolunteerTable.batch == request.batch,
        ).first()

        volunteers_json = [v.model_dump() for v in request.volunteers]

        if existing:
            existing.volunteers = volunteers_json
            existing.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            new_table = VolunteerTable(
                user_identifier=request.user_identifier,
                batch=request.batch,
                volunteers=volunteers_json,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            self.db.add(new_table)
            self.db.commit()
            self.db.refresh(new_table)
            return new_table

    def load(self, user_identifier: str = "default_user",
             batch: str = "常规批第1次") -> VolunteerTable | None:
        """加载志愿表"""
        return self.db.query(VolunteerTable).filter(
            VolunteerTable.user_identifier == user_identifier,
            VolunteerTable.batch == batch,
        ).first()

    def clear(self, user_identifier: str = "default_user",
              batch: str = "常规批第1次") -> None:
        """清空志愿表"""
        self.db.query(VolunteerTable).filter(
            VolunteerTable.user_identifier == user_identifier,
            VolunteerTable.batch == batch,
        ).delete()
        self.db.commit()
