"""Pydantic 请求/响应模型"""
from pydantic import BaseModel, Field
from typing import Optional, Literal


# ============ 请求模型 ============

class RecommendRequest(BaseModel):
    score: int = Field(..., ge=0, le=750, description="高考总分")
    subject_selection: list[str] = Field(
        default=["物理", "化学", "生物"],
        description="选考科目 (山东3+3: 从物理/化学/生物/政治/历史/地理中选3门)"
    )
    year: int = Field(default=2025, description="参考年份")

    # 可选偏好筛选
    preferred_cities: list[str] = Field(default=[], description="偏好城市")
    avoided_cities: list[str] = Field(default=[], description="排除城市")
    preferred_major_categories: list[str] = Field(default=[], description="偏好专业大类")
    min_school_level: Optional[str] = Field(default=None, description="最低院校层次: 985/211/双一流/普通")
    max_tuition: Optional[int] = Field(default=None, description="最高学费")
    preferred_provinces: list[str] = Field(default=[], description="偏好省份（不出省填['山东']）")


class VolunteerItem(BaseModel):
    """志愿表中的一项"""
    admission_line_id: int
    school_name: str
    major_name: str
    strategy: Literal["冲", "稳", "保"]
    probability: float
    order: int  # 志愿序号 (1-96)


class SaveVolunteerRequest(BaseModel):
    user_identifier: str = Field(default="default_user")
    batch: str = Field(default="常规批第1次")
    volunteers: list[VolunteerItem]


class StrategyWeightRequest(BaseModel):
    """个性化权重调整"""
    weight_school_rank: float = Field(default=0.25, ge=0, le=1, description="院校排名权重")
    weight_major_match: float = Field(default=0.25, ge=0, le=1, description="专业匹配权重")
    weight_city: float = Field(default=0.15, ge=0, le=1, description="城市偏好权重")
    weight_probability: float = Field(default=0.35, ge=0, le=1, description="录取概率权重")


# ============ 响应模型 ============

class RankInfo(BaseModel):
    score: int
    cumulative_rank: int
    segment_count: int
    year: int
    percentile: float = 0.0
    note: str = ""


class RecommendationItem(BaseModel):
    id: int
    school_name: str
    major_name: str
    major_code: Optional[str]
    subject_requirement: str
    predicted_rank: float
    sigma: float
    min_rank_history: list[int]  # 近3年位次
    probability: float
    strategy: str  # '冲' / '稳' / '保'
    quota: int
    tuition: Optional[int]
    school_level: str
    school_city: str
    school_province: str
    meets_subject_requirement: bool  # 选科是否满足要求


class RecommendResponse(BaseModel):
    my_rank: RankInfo
    total_count: int
    filtered_count: int
    risk_zone: str  # '冲刺区' / '主战场' / '安全区' 对应分数段
    reach: list[RecommendationItem]   # 冲
    match: list[RecommendationItem]   # 稳
    safety: list[RecommendationItem]  # 保


class SimulationResult(BaseModel):
    slip_risk: float           # 滑档概率
    safety_score: float         # 安全指数 (0-100)
    first_choice_rate: float    # 第一志愿命中概率
    admission_by_position: dict[int, float]  # {志愿序号: 录取概率}
    warnings: list[str]         # 风险预警


class VolunteerAnalysis(BaseModel):
    strategy_score: int
    risk_level: str
    slip_risk: float
    count_reach: int
    count_match: int
    count_safety: int
    warnings: list[str]
    suggestions: list[str]
