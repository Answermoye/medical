"""
医疗导诊与报告解读助手 - 评估指标模块

计算各类评估指标：
1. 意图路由准确率
2. 科室Top-3命中率
3. 安全拦截命中率
4. 异常指标识别Recall
"""

import json
from pathlib import Path
from typing import Any

from backend.core.logger import setup_logger

logger = setup_logger(__name__)

# 测试集路径
TEST_SETS_DIR = Path(__file__).parent.parent.parent / "data" / "test_sets"


class MetricsCalculator:
    """评估指标计算器"""

    def __init__(self):
        logger.info("初始化MetricsCalculator")

    def load_test_set(self, filename: str) -> list[dict]:
        """加载测试集"""
        filepath = TEST_SETS_DIR / filename
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def calculate_intent_accuracy(self, predictions: list[dict]) -> dict:
        """
        计算意图路由准确率

        Args:
            predictions: 预测结果列表，格式: [{"input": "...", "predicted_intent": "...", "expected_intent": "..."}]

        Returns:
            准确率指标
        """
        total = len(predictions)
        correct = 0
        by_intent = {}

        for pred in predictions:
            expected = pred.get("expected_intent")
            predicted = pred.get("predicted_intent")

            if expected and predicted:
                if expected not in by_intent:
                    by_intent[expected] = {"total": 0, "correct": 0}
                by_intent[expected]["total"] += 1

                if expected == predicted:
                    correct += 1
                    by_intent[expected]["correct"] += 1

        accuracy = correct / total if total > 0 else 0

        # 计算每个意图的准确率
        intent_metrics = {}
        for intent, counts in by_intent.items():
            intent_metrics[intent] = {
                "total": counts["total"],
                "correct": counts["correct"],
                "accuracy": counts["correct"] / counts["total"] if counts["total"] > 0 else 0,
            }

        return {
            "total": total,
            "correct": correct,
            "accuracy": accuracy,
            "by_intent": intent_metrics,
        }

    def calculate_safety_metrics(self, predictions: list[dict]) -> dict:
        """
        计算安全拦截指标

        Args:
            predictions: 预测结果列表

        Returns:
            安全指标
        """
        total = len(predictions)
        true_positive = 0  # 应该拦截且被拦截
        false_positive = 0  # 不应该拦截但被拦截
        true_negative = 0  # 不应该拦截且未被拦截
        false_negative = 0  # 应该拦截但未被拦截

        for pred in predictions:
            expected_blocked = pred.get("expected_blocked", False)
            predicted_blocked = pred.get("predicted_blocked", False)

            if expected_blocked and predicted_blocked:
                true_positive += 1
            elif not expected_blocked and predicted_blocked:
                false_positive += 1
            elif not expected_blocked and not predicted_blocked:
                true_negative += 1
            elif expected_blocked and not predicted_blocked:
                false_negative += 1

        precision = true_positive / (true_positive + false_positive) if (true_positive + false_positive) > 0 else 0
        recall = true_positive / (true_positive + false_negative) if (true_positive + false_negative) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

        return {
            "total": total,
            "true_positive": true_positive,
            "false_positive": false_positive,
            "true_negative": true_negative,
            "false_negative": false_negative,
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
        }

    def calculate_department_hit_rate(
        self,
        predictions: list[dict],
        top_k: int = 3,
    ) -> dict:
        """
        计算科室Top-K命中率

        Args:
            predictions: 预测结果列表
            top_k: Top-K

        Returns:
            命中率指标
        """
        total = len(predictions)
        hits = 0

        for pred in predictions:
            expected = pred.get("expected_departments", [])
            recommended = [d.get("department", "") for d in pred.get("recommended_departments", [])][:top_k]

            # 检查是否有交集
            if any(dept in recommended for dept in expected):
                hits += 1

        hit_rate = hits / total if total > 0 else 0

        return {
            "total": total,
            "hits": hits,
            "hit_rate": hit_rate,
            "top_k": top_k,
        }

    def calculate_abnormal_recall(self, predictions: list[dict]) -> dict:
        """
        计算异常指标识别Recall

        Args:
            predictions: 预测结果列表

        Returns:
            Recall指标
        """
        total_expected = 0
        total_predicted = 0
        true_positive = 0

        for pred in predictions:
            expected_abnormal = pred.get("expected_abnormal_types", [])
            predicted_abnormal = pred.get("predicted_abnormal_types", [])

            total_expected += len(expected_abnormal)
            total_predicted += len(predicted_abnormal)

            # 计算匹配数
            for exp in expected_abnormal:
                if exp in predicted_abnormal:
                    true_positive += 1

        recall = true_positive / total_expected if total_expected > 0 else 0
        precision = true_positive / total_predicted if total_predicted > 0 else 0

        return {
            "total_expected": total_expected,
            "total_predicted": total_predicted,
            "true_positive": true_positive,
            "recall": recall,
            "precision": precision,
        }

    def generate_report(self, results: dict) -> str:
        """
        生成评估报告

        Args:
            results: 评估结果

        Returns:
            格式化的报告文本
        """
        lines = []
        lines.append("# 评估报告\n")
        lines.append("**证据等级**: D级（Demo实测）\n")

        if "intent" in results:
            intent = results["intent"]
            lines.append("## 意图路由准确率\n")
            lines.append(f"- 总样本数: {intent['total']}")
            lines.append(f"- 正确数: {intent['correct']}")
            lines.append(f"- **准确率: {intent['accuracy']:.1%}**\n")

            if "by_intent" in intent:
                lines.append("### 各意图准确率\n")
                for intent_name, metrics in intent["by_intent"].items():
                    lines.append(f"- {intent_name}: {metrics['accuracy']:.1%} ({metrics['correct']}/{metrics['total']})")
                lines.append("")

        if "safety" in results:
            safety = results["safety"]
            lines.append("## 安全拦截指标\n")
            lines.append(f"- 总样本数: {safety['total']}")
            lines.append(f"- 精确率: {safety['precision']:.1%}")
            lines.append(f"- 召回率: {safety['recall']:.1%}")
            lines.append(f"- **F1分数: {safety['f1_score']:.1%}**\n")

        if "department" in results:
            dept = results["department"]
            lines.append("## 科室推荐命中率\n")
            lines.append(f"- 总样本数: {dept['total']}")
            lines.append(f"- Top-{dept['top_k']}命中数: {dept['hits']}")
            lines.append(f"- **命中率: {dept['hit_rate']:.1%}**\n")

        if "abnormal" in results:
            abnorm = results["abnormal"]
            lines.append("## 异常指标识别\n")
            lines.append(f"- 期望异常数: {abnorm['total_expected']}")
            lines.append(f"- 预测异常数: {abnorm['total_predicted']}")
            lines.append(f"- 正确识别数: {abnorm['true_positive']}")
            lines.append(f"- **Recall: {abnorm['recall']:.1%}**")
            lines.append(f"- Precision: {abnorm['precision']:.1%}\n")

        return "\n".join(lines)


# 全局MetricsCalculator实例
metrics_calculator = MetricsCalculator()
