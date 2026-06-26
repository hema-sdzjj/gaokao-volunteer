"""推荐引擎 — 山东3+3  '专业+学校' 平行志愿"""
import math
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from models import AdmissionLine, ScoreSegment
from schemas import RecommendRequest, RecommendationItem, RankInfo


class RecommendService:
    """志愿推荐引擎"""

    # 冲/稳/保——基于概率的分类（而非纯位次比）
    # 概率 > 65% → 保（大概率能进）
    # 概率 25%-65% → 稳（有机会，但不稳）
    # 概率 10%-25% → 冲（需要运气）
    # 概率 < 10% → 不显示（不现实）
    MIN_PROBABILITY = 0.10      # 最低显示概率
    REACH_PROB_MAX = 0.25       # 冲的上界
    MATCH_PROB_MAX = 0.65       # 稳的上界

    # 加权平均的年份权重
    YEAR_WEIGHTS = {2025: 0.50, 2024: 0.30, 2023: 0.20}

    def __init__(self, db: Session):
        self.db = db

    # ==================== 主入口 ====================

    def recommend(self, request: RecommendRequest) -> dict:
        # Step 1: 分数 → 位次
        rank_info = self._get_rank(request.score, request.year)

        # Step 2: 加载所有投档数据 (近3年)
        all_lines = self._load_admission_lines()

        # Step 3: 选科过滤（只保留满足选科要求的）
        eligible = self._filter_by_subject(all_lines, request.subject_selection)

        # Step 4: 计算每项的预测位次 + 录取概率
        recommendations = []
        for line in eligible:
            rec = self._compute_single(line, rank_info, request)
            if rec:
                recommendations.append(rec)

        # Step 5: 按录取概率排序
        recommendations.sort(key=lambda r: r.probability, reverse=True)

        # Step 6: 分类冲稳保
        reach = [r for r in recommendations if r.strategy == "冲"]
        match = [r for r in recommendations if r.strategy == "稳"]
        safety = [r for r in recommendations if r.strategy == "保"]

        # Step 7: 应用偏好过滤和排序（在每组内重新排序）
        if request.preferred_cities or request.preferred_major_categories or request.min_school_level or request.preferred_provinces:
            reach = self._apply_preference_sort(reach, request)
            match = self._apply_preference_sort(match, request)
            safety = self._apply_preference_sort(safety, request)

        # 用户的风险区间
        risk_zone = self._describe_risk_zone(rank_info, all_lines)

        return {
            "my_rank": rank_info,
            "total_count": len(all_lines),
            "filtered_count": len(eligible),
            "risk_zone": risk_zone,
            "reach": [r.model_dump() for r in reach],
            "match": [r.model_dump() for r in match],
            "safety": [r.model_dump() for r in safety],
        }

    # ==================== 核心计算 ====================

    def _get_rank(self, score: int, year: int) -> RankInfo:
        """分数→位次"""
        row = self.db.query(ScoreSegment).filter(
            and_(ScoreSegment.year == year, ScoreSegment.score == score)
        ).first()

        # 总考生数
        total_row = self.db.query(ScoreSegment).filter(
            ScoreSegment.year == year
        ).order_by(ScoreSegment.cumulative_rank.desc()).first()
        total = total_row.cumulative_rank if total_row else 600000

        if not row:
            # 找最接近的
            rows = self.db.query(ScoreSegment).filter(
                ScoreSegment.year == year
            ).order_by(ScoreSegment.score.desc()).all()
            if not rows:
                raise ValueError(f"没有{year}年的一分一段数据")
            closest = min(rows, key=lambda r: abs(r.score - score))
            return RankInfo(
                score=score,
                cumulative_rank=closest.cumulative_rank,
                segment_count=closest.segment_count,
                year=year,
                percentile=round(closest.cumulative_rank / total * 100, 2),
                note=f"精确分数{score}不在表中，使用最接近的{closest.score}分"
            )
        return RankInfo(
            score=score,
            cumulative_rank=row.cumulative_rank,
            segment_count=row.segment_count or 0,
            year=year,
            percentile=round(row.cumulative_rank / total * 100, 2),
        )

    def _load_admission_lines(self) -> list[AdmissionLine]:
        """加载投档数据 — 仅最新年份，去重"""
        return self.db.query(AdmissionLine).filter(
            AdmissionLine.year == 2025
        ).all()

    def _filter_by_subject(self, lines: list[AdmissionLine], my_subjects: list[str]) -> list[AdmissionLine]:
        """选科过滤"""
        eligible = []
        for line in lines:
            if self._meets_subject_requirement(line.subject_requirement, my_subjects):
                eligible.append(line)
        return eligible

    def _compute_single(self, line: AdmissionLine, my_rank: RankInfo, request: RecommendRequest) -> Optional[RecommendationItem]:
        """计算单个专业+学校的推荐"""
        # 收集该专业近3年位次（去重：AdmissionLine 已包含每年数据）
        history = self._get_history_for_line(line)

        if len(history) < 2:
            return None  # 数据不足，跳过

        # 预测位次 + 标准差
        pred_rank, sigma = self._predict_rank(history)

        # 录取概率
        quota = history.get(2025, {}).get("quota", 10) or 10
        prob = self._admission_probability(my_rank.cumulative_rank, pred_rank, sigma, quota)

        # 硬性过滤：预测位次比我好20倍以上的学校，不可能考上，不显示
        if my_rank.cumulative_rank > 0 and pred_rank > 0:
            if my_rank.cumulative_rank / pred_rank > 20:
                return None  # 差距过大，不现实

        # 策略分类——基于概率
        if prob < self.MIN_PROBABILITY:
            return None  # 不现实，不显示
        elif prob < self.REACH_PROB_MAX:
            strategy = "冲"
        elif prob < self.MATCH_PROB_MAX:
            strategy = "稳"
        else:
            strategy = "保"

        # 选科检查
        meets = self._meets_subject_requirement(
            line.subject_requirement, request.subject_selection
        )

        # 硬性过滤
        if request.max_tuition and line.tuition and line.tuition > request.max_tuition:
            return None
        if request.min_school_level:
            level_order = {"985": 1, "211": 2, "双一流": 3, "普通": 4}
            req_min = level_order.get(request.min_school_level, 4)
            line_level = level_order.get(line.school_level, 4)
            if line_level > req_min:
                return None
        if request.preferred_cities and line.school_city not in request.preferred_cities:
            return None
        if request.preferred_provinces and line.school_province not in request.preferred_provinces:
            return None

        return RecommendationItem(
            id=line.id,
            school_name=line.school_name,
            major_name=line.major_name,
            major_code=line.major_code,
            subject_requirement=line.subject_requirement or "不限",
            predicted_rank=round(pred_rank, 0),
            sigma=round(sigma, 0),
            min_rank_history=[history[y]["min_rank"] for y in sorted(history.keys()) if y in history],
            probability=round(prob, 4),
            strategy=strategy,
            quota=line.quota or 0,
            tuition=line.tuition,
            school_level=line.school_level or "普通",
            school_city=line.school_city or "",
            school_province=line.school_province or "",
            meets_subject_requirement=meets,
        )

    def _get_history_for_line(self, line: AdmissionLine) -> dict:
        """获取同一专业+学校的历史位次数据"""
        history = {}
        all_rows = self.db.query(AdmissionLine).filter(
            and_(
                AdmissionLine.school_name == line.school_name,
                AdmissionLine.major_name == line.major_name,
                AdmissionLine.year.in_([2023, 2024, 2025]),
            )
        ).all()

        for row in all_rows:
            history[row.year] = {
                "min_rank": row.min_rank,
                "min_score": row.min_score,
                "quota": row.quota,
            }
        return history

    def _predict_rank(self, history: dict) -> tuple[float, float]:
        """加权预测位次 + 标准差"""
        total_weight = 0
        weighted_sum = 0

        for year, weight in self.YEAR_WEIGHTS.items():
            if year in history:
                weighted_sum += weight * history[year]["min_rank"]
                total_weight += weight

        if total_weight == 0:
            return 999999, 10000

        predicted = weighted_sum / total_weight

        # 计算加权标准差
        var_sum = 0
        for year, weight in self.YEAR_WEIGHTS.items():
            if year in history:
                residual = history[year]["min_rank"] - predicted
                var_sum += weight * residual ** 2

        sigma = math.sqrt(var_sum / total_weight) if total_weight > 0 else predicted * 0.05
        sigma = max(sigma, predicted * 0.03)  # 最小3%波动

        return predicted, sigma

    def _admission_probability(self, my_rank: int, pred_rank: float,
                                sigma: float, quota: int) -> float:
        """
        Sigmoid 概率模型——比正态CDF更宽容，更符合真实认知

        概率 = 1 / (1 + exp(-steepness * (pred_rank - my_rank) / pred_rank))

        当我的位次 = 预测位次时，概率 = 50%
        当我的位次比预测线好很多(my_rank << pred_rank)，概率 → 100%
        当我的位次比预测线差很多(my_rank >> pred_rank)，概率 → 0%

        sigma 用于调节陡峭度：sigma 小(稳定) → 更陡峭；sigma 大(波动) → 更平缓
        """
        if pred_rank <= 0:
            return 0.5

        # 基础 steepness：用 sigma/pred_rank 调节
        # 历史波动大(sigma大) → steepness小 → 概率函数平缓 → 更宽容
        # 历史波动小(sigma小) → steepness大 → 概率函数陡峭 → 更严格
        volatility = sigma / pred_rank  # 波动率，通常在 0.03-0.20
        # steepness 在 5-20 之间
        steepness = max(5, min(20, 8 / max(volatility, 0.03)))

        # sigmoid
        relative_diff = (pred_rank - my_rank) / pred_rank

        # 防止 math.exp 溢出：relative_diff 可能很大（如 -1000）
        # 当 exponent > 50 时概率已基本为0或1，直接截断
        exponent = steepness * relative_diff
        if exponent > 50:
            prob = 0.99  # 远远优于录取线
        elif exponent < -50:
            prob = 0.01  # 远远低于录取线
        else:
            prob = 1.0 / (1.0 + math.exp(-exponent))

        # 小计划数的不确定性修正（适度，不超过10个百分点）
        if quota < 15 and prob > 0.05:
            uncertainty = min(0.20, (15 - quota) / 15 * 0.25)
            prob = (1 - uncertainty) * prob + uncertainty * 0.5

        return max(0.01, min(0.99, prob))

    # ==================== 辅助方法 ====================

    def _meets_subject_requirement(self, requirement: str, my_subjects: list[str]) -> bool:
        """检查选科是否满足要求"""
        if not requirement or requirement == "不限":
            return True

        req = requirement.strip()
        my_set = set(s.strip() for s in my_subjects)

        if "和" in req:
            # "物理和化学" → 两门都必须有
            parts = [p.strip() for p in req.split("和")]
            return all(p in my_set for p in parts)
        elif "或" in req:
            # "物理或化学" → 有一门即可
            parts = [p.strip() for p in req.split("或")]
            return any(p in my_set for p in parts)
        else:
            # "物理" → 单科要求
            return req in my_set

    def _apply_preference_sort(self, items: list[RecommendationItem],
                                request: RecommendRequest) -> list[RecommendationItem]:
        """根据偏好重新排序"""
        def score(item: RecommendationItem):
            s = item.probability
            if request.preferred_cities and item.school_city in request.preferred_cities:
                s += 0.1
            if request.preferred_provinces and item.school_province in request.preferred_provinces:
                s += 0.08
            if request.preferred_major_categories:
                # 简单匹配（后续可扩展专业大类匹配）
                major_cat = self._get_major_category(item.major_code)
                if major_cat in request.preferred_major_categories:
                    s += 0.12
            return s

        return sorted(items, key=score, reverse=True)

    def _get_major_category(self, major_code: Optional[str]) -> str:
        """通过专业代码推断大类"""
        if not major_code:
            return ""
        mapping = {
            "0809": "计算机类", "080901": "计算机类", "080902": "计算机类",
            "0807": "电子信息类", "080701": "电子信息类", "080702": "电子信息类",
            "1002": "临床医学类", "100201": "临床医学类",
            "0301": "法学类", "030101": "法学类",
            "1202": "工商管理类", "120203": "工商管理类",
            "0502": "外国语言文学类", "050201": "外国语言文学类",
            "0701": "数学类", "070101": "数学类",
            "0802": "机械类", "080201": "机械类",
            "0810": "土木类", "081001": "土木类",
            "0201": "经济学类", "020101": "经济学类",
        }
        for prefix, cat in mapping.items():
            if major_code.startswith(prefix):
                return cat
        return ""

    def _describe_risk_zone(self, my_rank: RankInfo, all_lines: list[AdmissionLine]) -> str:
        """描述用户的风险区间"""
        # 获取2025年所有投档线位次分布
        ranks_2025 = [line.min_rank for line in all_lines
                      if line.year == 2025 and line.min_rank]

        if not ranks_2025:
            return "未知"

        ranks_2025.sort()

        my = my_rank.cumulative_rank

        if my <= ranks_2025[int(len(ranks_2025) * 0.05)]:
            return "顶级竞争区（前5%）—— 可冲击清北复交等顶尖院校"
        elif my <= ranks_2025[int(len(ranks_2025) * 0.15)]:
            return "高分段（前15%）—— 985院校主战场"
        elif my <= ranks_2025[int(len(ranks_2025) * 0.35)]:
            return "中高分段（前35%）—— 211及省重点院校"
        elif my <= ranks_2025[int(len(ranks_2025) * 0.60)]:
            return "中分段（前60%）—— 省属重点院校"
        elif my <= ranks_2025[int(len(ranks_2025) * 0.85)]:
            return "中低分段 —— 普通本科院校"
        else:
            return "本科线边缘 —— 重点关注保底院校和民办/独立学院"
