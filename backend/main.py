"""FastAPI 主入口 — 高考志愿填报系统（山东）"""
import json
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from database import get_db, init_db
from schemas import (
    RecommendRequest, RecommendResponse,
    SaveVolunteerRequest, SimulationResult, VolunteerAnalysis,
    StrategyWeightRequest,
)
from services.rank_service import RankService
from services.recommend_service import RecommendService
from services.risk_service import RiskService
from services.volunteer_service import VolunteerService

app = FastAPI(
    title="高考志愿填报助手",
    description="山东省高考志愿填报辅助系统 — 3+3新高考 · 96个平行志愿",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()


# ==================== 位次换算 ====================

@app.get("/api/rank")
def score_to_rank(score: int, year: int = 2025, db: Session = Depends(get_db)):
    """分数 → 省排名"""
    try:
        service = RankService(db)
        return service.score_to_rank(score, year)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/rank/compare")
def compare_rank(score: int, from_year: int, to_year: int, db: Session = Depends(get_db)):
    """跨年份位次等价换算"""
    try:
        service = RankService(db)
        return service.equivalent_rank(score, from_year, to_year)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 推荐引擎 ====================

@app.post("/api/recommend")
def recommend(request: RecommendRequest, db: Session = Depends(get_db)):
    """获取志愿推荐"""
    service = RecommendService(db)
    result = service.recommend(request)
    return result


# ==================== 志愿表管理 ====================

@app.get("/api/volunteer")
def load_volunteer(user: str = Query(default="default_user"),
                   batch: str = Query(default="常规批第1次"),
                   db: Session = Depends(get_db)):
    """加载用户的志愿表"""
    service = VolunteerService(db)
    table = service.load(user_identifier=user, batch=batch)
    if not table:
        return {"volunteers": [], "strategy_score": None, "risk_level": None}
    return {
        "id": table.id,
        "volunteers": table.volunteers,
        "strategy_score": table.strategy_score,
        "risk_level": table.risk_level,
        "slip_risk": table.slip_risk,
        "created_at": str(table.created_at),
        "updated_at": str(table.updated_at),
    }


@app.post("/api/volunteer")
def save_volunteer(request: SaveVolunteerRequest, db: Session = Depends(get_db)):
    """保存志愿表"""
    service = VolunteerService(db)
    table = service.save(request)
    return {"id": table.id, "message": "保存成功", "count": len(request.volunteers)}


@app.delete("/api/volunteer")
def clear_volunteer(user: str = Query(default="default_user"),
                    batch: str = Query(default="常规批第1次"),
                    db: Session = Depends(get_db)):
    """清空志愿表"""
    service = VolunteerService(db)
    service.clear(user_identifier=user, batch=batch)
    return {"message": "已清空"}


# ==================== 风险分析 ====================

@app.post("/api/analyze")
def analyze_volunteer(request: SaveVolunteerRequest, db: Session = Depends(get_db)):
    """分析志愿表的策略和风险"""
    risk_service = RiskService(db)

    # 我们需要知道考生的位次——从志愿表中的 probability 反向推算
    # 简化方案：由前端传入，或者存到志愿表记录中
    # 这里我们需要一个位次参数
    # 暂时让前端传一个额外的 my_rank 字段
    # 请求复用 SaveVolunteerRequest（里面没有 my_rank），加个 query param
    raise HTTPException(status_code=400, detail="请使用 /api/analyze/{my_rank} 端点")


@app.post("/api/analyze/{my_rank}")
def analyze_with_rank(my_rank: int, request: SaveVolunteerRequest,
                       db: Session = Depends(get_db)):
    """分析志愿表（需要考生位次）"""
    from schemas import VolunteerItem
    risk_service = RiskService(db)

    volunteers = [
        VolunteerItem(**v) if isinstance(v, dict) else v
        for v in request.volunteers
    ]

    analysis = risk_service.analyze_strategy(volunteers, my_rank)
    sim = risk_service.monte_carlo_simulate(volunteers, my_rank, n_simulations=10000)

    return {
        "analysis": analysis.model_dump(),
        "simulation": sim.model_dump(),
    }


# ==================== 院校/专业查询 ====================

@app.get("/api/schools")
def list_schools(search: str = Query(default=""),
                 level: str = Query(default=""),
                 province: str = Query(default=""),
                 db: Session = Depends(get_db)):
    """查询院校列表"""
    from models import School
    query = db.query(School)
    if search:
        query = query.filter(School.name.contains(search))
    if level:
        query = query.filter(School.level == level)
    if province:
        query = query.filter(School.province == province)
    schools = query.limit(200).all()
    return [s.to_dict() for s in schools]


@app.get("/api/schools/{school_name}/majors")
def get_school_majors(school_name: str, year: int = Query(default=2025),
                       db: Session = Depends(get_db)):
    """获取某校在山东招生的专业列表"""
    from models import AdmissionLine
    lines = db.query(AdmissionLine).filter(
        AdmissionLine.school_name == school_name,
        AdmissionLine.year == year,
    ).all()
    return [line.to_dict() for line in lines]


# ==================== 静态文件（前端）====================

import os
frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
