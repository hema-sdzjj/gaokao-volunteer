"""风险评估服务 — 蒙特卡洛模拟 + 志愿表分析"""
import math
import random
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from models import AdmissionLine
from schemas import SimulationResult, VolunteerAnalysis, VolunteerItem


class RiskService:
    """志愿表风险评估"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== 蒙特卡洛模拟 ====================

    def monte_carlo_simulate(self, volunteers: list[VolunteerItem],
                              my_rank: int, n_simulations: int = 10000) -> SimulationResult:
        """
        模拟平行志愿录取过程 N 次
        """
        if not volunteers:
            return SimulationResult(
                slip_risk=1.0,
                safety_score=0,
                first_choice_rate=0,
                admission_by_position={},
                warnings=["志愿表为空，请先添加志愿"],
            )

        # 为每个志愿获取历史数据（或使用概率作为fallback）
        enriched = []
        for v in volunteers:
            history = self._get_rank_history(v.admission_line_id)
            if history:
                pred_rank, sigma = self._predict_rank(history)
                quota = history[-1][2] if history else 10
                enriched.append({
                    "volunteer": v,
                    "pred_rank": pred_rank,
                    "sigma": max(sigma, pred_rank * 0.03),
                    "quota": quota,
                    "use_probability_fallback": False,
                })
            elif v.probability and v.probability > 0:
                # Fallback: use the probability directly
                enriched.append({
                    "volunteer": v,
                    "pred_rank": 0,
                    "sigma": 0,
                    "quota": 10,
                    "use_probability_fallback": True,
                })

        if not enriched:
            return SimulationResult(
                slip_risk=1.0,
                safety_score=0,
                first_choice_rate=0,
                admission_by_position={},
                warnings=["无法获取志愿的历史数据"],
            )

        # 模拟
        all_fail = 0
        admitted_count = {i: 0 for i in range(len(enriched))}
        first_choice_hit = 0

        for _ in range(n_simulations):
            admitted_this_run = False
            for i, item in enumerate(enriched):
                if item["use_probability_fallback"]:
                    # Probability-based fallback
                    if random.random() < item["volunteer"].probability:
                        admitted_count[i] += 1
                        admitted_this_run = True
                        if i == 0:
                            first_choice_hit += 1
                        break
                else:
                    # 实际录取位次是一个随机变量
                    actual_cutoff = random.gauss(item["pred_rank"], item["sigma"])

                    # 小计划数的额外随机性
                    if item["quota"] < 10:
                        actual_cutoff += random.uniform(-item["sigma"] * 0.5, item["sigma"] * 0.5)

                    if my_rank <= actual_cutoff:
                        admitted_count[i] += 1
                        admitted_this_run = True
                        if i == 0:
                            first_choice_hit += 1
                        break  # 平行志愿，投档后不再检索后续

            if not admitted_this_run:
                all_fail += 1

        # 计算概率
        slip_risk = all_fail / n_simulations
        admission_by_position = {
            item["volunteer"].order: admitted_count[i] / n_simulations
            for i, item in enumerate(enriched)
        }

        # 生成警告
        warnings = self._generate_warnings(slip_risk, enriched, admission_by_position)

        return SimulationResult(
            slip_risk=round(slip_risk, 4),
            safety_score=round((1 - slip_risk) * 100, 1),
            first_choice_rate=round(first_choice_hit / n_simulations, 4),
            admission_by_position=admission_by_position,
            warnings=warnings,
        )

    # ==================== 志愿表策略分析 ====================

    def analyze_strategy(self, volunteers: list[VolunteerItem],
                          my_rank: int) -> VolunteerAnalysis:
        """分析志愿表的冲稳保结构"""
        if not volunteers:
            return VolunteerAnalysis(
                strategy_score=0,
                risk_level="高",
                slip_risk=1.0,
                count_reach=0,
                count_match=0,
                count_safety=0,
                warnings=["志愿表为空"],
                suggestions=["请先添加志愿"],
            )

        reach = [v for v in volunteers if v.strategy == "冲"]
        match = [v for v in volunteers if v.strategy == "稳"]
        safety = [v for v in volunteers if v.strategy == "保"]

        total = len(volunteers)
        n_reach = len(reach)
        n_match = len(match)
        n_safety = len(safety)

        ratio_reach = n_reach / total
        ratio_match = n_match / total
        ratio_safety = n_safety / total

        warnings = []
        suggestions = []
        score = 100

        # 山东96个志愿，这是一个非常大的空间
        # 理想的配比：冲 15-25%，稳 40-50%，保 25-35%

        # 检查冲的比例
        if ratio_reach > 0.30:
            warnings.append(f"冲的比例过高（{ratio_reach:.0%}），建议控制在30%以内")
            score -= 15
        elif ratio_reach < 0.10 and n_safety < 20:
            suggestions.append("可以适当增加几个冲刺志愿，96个志愿空间足够尝试梦想院校")

        # 检查保的数量
        if n_safety < 15:
            warnings.append(f"保底志愿不足（仅{n_safety}个），滑档风险较大")
            score -= 25
        elif n_safety < 25:
            suggestions.append(f"保底志愿{n_safety}个，考虑到96个志愿，建议增加到25个以上")
            score -= 5

        # 检查稳的数量
        if n_match < 20:
            warnings.append(f"稳妥志愿不足（仅{n_match}个），缺少主战场")
            score -= 15

        # 检查概率梯度
        probs = [v.probability for v in volunteers]
        if probs and max(probs) - min(probs) < 0.3:
            warnings.append("各志愿录取概率过于集中，缺少梯度")
            score -= 10
        elif probs and max(probs) < 0.5:
            warnings.append("所有志愿录取概率都低于50%，风险极高！请务必增加保底")
            score -= 40

        # 检查是否所有保底的概率都够高
        low_safety = [v for v in safety if v.probability < 0.75]
        if low_safety:
            warnings.append(f"有{len(low_safety)}个'保底'志愿的实际录取概率低于75%，建议替换为更稳妥的选择")
            score -= 10

        # 检查是否按概率降序排列
        is_descending = all(probs[i] >= probs[i + 1] for i in range(len(probs) - 1))
        if not is_descending:
            suggestions.append("建议将录取概率更高的志愿排在前面（或自行调整以反映真实偏好）")

        # 蒙特卡洛补充验证
        sim = self.monte_carlo_simulate(volunteers, my_rank, n_simulations=5000)
        slip_risk = sim.slip_risk

        if slip_risk > 0.20:
            risk_level = "高"
            score = max(0, score - 30)
        elif slip_risk > 0.08:
            risk_level = "中"
            score = max(0, score - 10)
        else:
            risk_level = "低"

        # 生成综合建议
        if not suggestions:
            if risk_level == "低":
                suggestions.append("志愿表结构合理，梯度清晰，兜底充分 ✓")
            if n_safety >= 30:
                suggestions.append("保底志愿非常充足，可以考虑将末尾几个保底换成更心仪的稳妥志愿")

        return VolunteerAnalysis(
            strategy_score=max(0, min(100, score)),
            risk_level=risk_level,
            slip_risk=round(slip_risk, 4),
            count_reach=n_reach,
            count_match=n_match,
            count_safety=n_safety,
            warnings=warnings,
            suggestions=suggestions,
        )

    # ==================== 辅助方法 ====================

    def _get_rank_history(self, line_id: int) -> list[tuple[int, int, int]]:
        """获取该投档线近3年的 (位次, 分数, 计划数)"""
        line = self.db.query(AdmissionLine).filter(AdmissionLine.id == line_id).first()
        if not line:
            return []

        rows = self.db.query(AdmissionLine).filter(
            and_(
                AdmissionLine.school_name == line.school_name,
                AdmissionLine.major_name == line.major_name,
                AdmissionLine.year.in_([2023, 2024, 2025]),
            )
        ).order_by(AdmissionLine.year.desc()).all()

        return [(r.min_rank, r.min_score, r.quota or 10) for r in rows]

    def _predict_rank(self, history: list[tuple[int, int, int]]) -> tuple[float, float]:
        """加权预测"""
        weights = {2025: 0.50, 2024: 0.30, 2023: 0.20}
        ranks = [h[0] for h in history]
        if not ranks:
            return 999999, 10000

        predicted = sum(w * r for w, r in zip(
            [weights.get(2025 - i, 0.2) for i in range(len(ranks))], ranks
        )) / sum([weights.get(2025 - i, 0.2) for i in range(len(ranks))])

        residuals = [r - predicted for r in ranks]
        sigma = math.sqrt(sum(e**2 for e in residuals) / len(residuals)) if len(residuals) > 1 else predicted * 0.05
        sigma = max(sigma, predicted * 0.03)

        return predicted, sigma

    def _generate_warnings(self, slip_risk: float, enriched: list,
                            admission_by_position: dict) -> list[str]:
        """生成风险警告"""
        warnings = []
        if slip_risk > 0.20:
            warnings.append(f"⚠️ 滑档风险 {slip_risk:.1%}，强烈建议增加保底志愿")
        elif slip_risk > 0.08:
            warnings.append(f"⚠️ 滑档风险 {slip_risk:.1%}，建议再增加几个保底志愿")
        elif slip_risk > 0.03:
            warnings.append(f"滑档风险 {slip_risk:.1%}，在可接受范围内")

        # 检查前几个志愿的命中率
        if admission_by_position:
            top3_prob = sum(
                prob for order, prob in admission_by_position.items()
                if order <= 3
            )
            if top3_prob < 0.15:
                warnings.append("前3个志愿综合命中率偏低，如果它们是你的首选，建议调整")

        return warnings
