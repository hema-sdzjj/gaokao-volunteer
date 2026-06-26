"""位次换算服务 — 山东3+3新高考（数据库版）"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from models import ScoreSegment


class RankService:
    """分数 ↔ 省排名换算"""

    def __init__(self, db: Session):
        self.db = db

    def score_to_rank(self, score: int, year: int = 2025) -> dict:
        """
        分数 → 省排名
        山东不分文理，统一排名
        """
        row = self.db.query(ScoreSegment).filter(
            and_(ScoreSegment.year == year, ScoreSegment.score == score)
        ).first()

        if not row:
            # 找最接近的分数
            all_rows = self.db.query(ScoreSegment).filter(
                ScoreSegment.year == year
            ).all()
            if not all_rows:
                raise ValueError(f"没有{year}年的一分一段数据，请先运行 scripts/load_data.py")

            closest = min(all_rows, key=lambda r: abs(r.score - score))
            total = max(r.cumulative_rank for r in all_rows)
            return {
                "score": score,
                "cumulative_rank": closest.cumulative_rank,
                "segment_count": closest.segment_count or 0,
                "year": year,
                "percentile": round(closest.cumulative_rank / total * 100, 2) if total > 0 else 0,
                "note": f"精确分数{score}不在表中，使用最接近的{closest.score}分"
            }

        total = max(r.cumulative_rank for r in self.db.query(ScoreSegment).filter(
            ScoreSegment.year == year
        ).all())
        return {
            "score": score,
            "cumulative_rank": row.cumulative_rank,
            "segment_count": row.segment_count or 0,
            "year": year,
            "percentile": round(row.cumulative_rank / total * 100, 2) if total > 0 else 0,
        }

    def rank_to_score(self, rank: int, year: int = 2025) -> dict:
        """省排名 → 大致分数（反向查询）"""
        rows = self.db.query(ScoreSegment).filter(
            ScoreSegment.year == year
        ).order_by(ScoreSegment.cumulative_rank.asc()).all()

        if not rows:
            raise ValueError(f"没有{year}年的一分一段数据")

        # 找累计人数 >= rank 的第一个分数段（即该排名对应的最高分）
        for row in rows:
            if row.cumulative_rank >= rank:
                return {
                    "rank": rank,
                    "equivalent_score": row.score,
                    "year": year,
                }
        # 如果排名超出所有 → 返回最低分
        return {
            "rank": rank,
            "equivalent_score": rows[-1].score,
            "year": year,
        }

    def equivalent_rank(self, score: int, from_year: int, to_year: int) -> dict:
        """跨年份位次等价换算"""
        rank_info = self.score_to_rank(score, from_year)
        my_rank = rank_info["cumulative_rank"]

        # 计算该位次占当年考生总数的比例
        rows_from = self.db.query(ScoreSegment).filter(
            ScoreSegment.year == from_year
        ).all()
        total_from = max(r.cumulative_rank for r in rows_from) if rows_from else 600000

        rows_to = self.db.query(ScoreSegment).filter(
            ScoreSegment.year == to_year
        ).all()
        total_to = max(r.cumulative_rank for r in rows_to) if rows_to else 600000

        equivalent_rank_to = int(my_rank / total_from * total_to)
        score_in_to = self.rank_to_score(equivalent_rank_to, to_year)

        return {
            "original_score": score,
            "original_rank": my_rank,
            "from_year": from_year,
            "equivalent_rank_in_target_year": equivalent_rank_to,
            "equivalent_score_in_target_year": score_in_to["equivalent_score"],
            "to_year": to_year,
        }
