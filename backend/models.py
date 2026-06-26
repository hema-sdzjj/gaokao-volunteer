"""SQLAlchemy 数据模型"""
import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, JSON, UniqueConstraint, ForeignKey
from database import Base


class School(Base):
    __tablename__ = "schools"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, index=True)
    alias = Column(String(200))                # JSON数组: '["山大","山东大学"]'
    level = Column(String(20))                 # '985'/'211'/'双一流'/'普通'
    school_type = Column(String(20))            # '综合'/'理工'/'师范'/'医学'/'财经'...
    province = Column(String(20))               # 所在省份
    city = Column(String(50))                   # 所在城市
    is_public = Column(Boolean, default=True)   # 公办/民办
    website = Column(String(200))
    intro = Column(Text)
    logo_url = Column(String(300))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "alias": json.loads(self.alias) if self.alias else [],
            "level": self.level,
            "school_type": self.school_type,
            "province": self.province,
            "city": self.city,
            "is_public": self.is_public,
            "intro": self.intro,
        }


class Major(Base):
    __tablename__ = "majors"

    code = Column(String(6), primary_key=True)  # '080901' 计算机科学与技术
    name = Column(String(100), nullable=False)
    category = Column(String(50))                # '计算机类'
    discipline = Column(String(50))              # '工学'
    degree = Column(String(20))                  # '工学学士'
    study_years = Column(Integer, default=4)
    intro = Column(Text)
    courses = Column(JSON)                       # 主干课程列表
    career_directions = Column(JSON)             # 就业方向
    profile_vector = Column(JSON)                # [理论-实践, 人际-事物, 创造-执行, 稳定-变化]

    def to_dict(self):
        return {
            "code": self.code,
            "name": self.name,
            "category": self.category,
            "discipline": self.discipline,
            "degree": self.degree,
            "study_years": self.study_years,
            "intro": self.intro,
            "courses": json.loads(self.courses) if isinstance(self.courses, str) else self.courses,
            "career_directions": json.loads(self.career_directions) if isinstance(self.career_directions, str) else self.career_directions,
        }


class ScoreSegment(Base):
    """一分一段表 — 山东专用"""
    __tablename__ = "score_segment"

    id = Column(Integer, primary_key=True, autoincrement=True)
    year = Column(Integer, nullable=False, index=True)
    score = Column(Integer, nullable=False)
    cumulative_rank = Column(Integer, nullable=False)
    segment_count = Column(Integer)

    __table_args__ = (
        UniqueConstraint("year", "score", name="uq_year_score"),
    )


class AdmissionLine(Base):
    """投档线 — 山东 '专业+学校' 粒度"""
    __tablename__ = "admission_lines"

    id = Column(Integer, primary_key=True, autoincrement=True)
    year = Column(Integer, nullable=False, index=True)
    school_name = Column(String(100), nullable=False, index=True)
    major_name = Column(String(100), nullable=False)
    major_code = Column(String(6))
    subject_requirement = Column(String(50))     # '物理' / '物理或化学' / '不限'
    min_score = Column(Integer, nullable=False)
    min_rank = Column(Integer, nullable=False)
    avg_score = Column(Integer)
    quota = Column(Integer, default=0)           # 招生计划数
    tuition = Column(Integer)                     # 学费
    school_level = Column(String(20))             # 冗余存储，方便查询
    school_city = Column(String(50))
    school_province = Column(String(20))

    __table_args__ = (
        UniqueConstraint("year", "school_name", "major_name", name="uq_year_school_major"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "year": self.year,
            "school_name": self.school_name,
            "major_name": self.major_name,
            "major_code": self.major_code,
            "subject_requirement": self.subject_requirement,
            "min_score": self.min_score,
            "min_rank": self.min_rank,
            "avg_score": self.avg_score,
            "quota": self.quota,
            "tuition": self.tuition,
            "school_level": self.school_level,
            "school_city": self.school_city,
            "school_province": self.school_province,
        }


class VolunteerTable(Base):
    """用户志愿表"""
    __tablename__ = "volunteer_tables"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_identifier = Column(String(100), index=True)  # 简单标识（可扩展为用户系统）
    batch = Column(String(50), default="常规批第1次")
    volunteers = Column(JSON, default=list)            # 志愿列表
    strategy_score = Column(Integer)                    # 策略评分
    risk_level = Column(String(10))                     # '低'/'中'/'高'
    slip_risk = Column(Float)                           # 滑档概率
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
