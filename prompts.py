"""生成 prompt 与评审 prompt，支持 game / ecommerce 两种 vertical，强制执行五段式结构。"""
from __future__ import annotations

import json
from typing import Literal

from schemas import CreativeCard, CreativeVariant

# 枚举定义
HOOK_ENUM = [
    "BEFORE_AFTER", "RULES_VS_ME", "RESULT_FIRST", "CHALLENGE_DUEL", 
    "SATISFYING_LOOP", "SOCIAL_PROOF", "STORY_SHORT", "TUTORIAL_FAST", 
    "FAIL_TO_WIN", "VALUE_ANCHOR"
]
WHY_YOU_TRIGGER_ENUM = [
    "BORED_WAITING", "STRESS_RELEASE", "WANT_WIN", "WANT_COLLECT", 
    "WANT_SOCIAL", "WANT_IMPROVE", "NEED_SOLUTION", "NEED_DEAL"
]
MOTIVATION_BUCKET_ENUM = [
    "ACHIEVEMENT", "COMPETITION", "RELAXATION", "CURIOSITY", 
    "COLLECTING", "SOCIAL", "CONTROL", "SAVING_MONEY"
]
WHY_NOW_TRIGGER_ENUM = [
    "LIMITED_TIME", "NEW_VERSION", "NEW_CONTENT", "EVENT_TODAY", 
    "SCARCITY", "PRICE_DROP", "SOCIAL_TREND", "IMMEDIATE_RELIEF"
]
CTA_ENUM = [
    "INSTALL_NOW", "TRY_NOW", "JOIN_EVENT", "CLAIM_REWARD", 
    "WATCH_MORE", "BUY_NOW", "ADD_TO_CART"
]

def build_generation_prompt(card: CreativeCard, n: int = 5) -> str:
    """构建生成变体的 prompt（强制五段式结构）"""
    card_json = json.dumps(card.model_dump(), ensure_ascii=False, indent=2)
    
    return f"""你是广告投放创意生成引擎。你的任务：根据输入的 CreativeCard，生成 {n} 条 CreativeVariant。
【强约束：五段式结构】
你必须为每条变体严格执行以下五个维度的标签化输出，严禁使用任何营销废词（如：痛点共鸣、利益前置、口碑背书等）：

1. hook_type: 必须从以下枚举中选择 1 个：{HOOK_ENUM}
2. why_you_trigger: 必须从以下枚举中选择 1 个：{WHY_YOU_TRIGGER_ENUM}
3. motivation_bucket: 必须从以下枚举中选择 1 个：{MOTIVATION_BUCKET_ENUM}
4. why_now_trigger: 必须从以下枚举中选择 1 个：{WHY_NOW_TRIGGER_ENUM}
5. cta: 必须从以下枚举中选择 1 个（作为 CTA 类型）：{CTA_ENUM}

【字段映射要求】
- hook_type: 直接填入上述枚举值。
- who_why_now.who: 简短的一句话人群描述。
- who_why_now.why: 格式必须为：“场景:[why_you_trigger枚举] 动机:[motivation_bucket枚举] + 1句价值主张”。
- who_why_now.why_now: 格式必须为：“时机:[why_now_trigger枚举] + 1句现在为什么”。
- cta: 只允许输出上述 CTA_ENUM 中的值，不要输出长文案。
- script.shots: 必须 3-5 个镜头，字段齐全。
- risk_flags: 若出现营销废词，exaggeration_risk 必须设为 high。

【输出格式】
- 只允许输出一个 JSON 对象：{{"variants":[...]}}，不要 Markdown，不要解释。
- 数组长度必须等于 {n}。

【输入 CreativeCard】
{card_json}

现在开始输出 JSON：
"""

def build_review_prompt(card: CreativeCard, variants: list[CreativeVariant]) -> str:
    """构建评审变体的 prompt（增加五段式门禁检查）"""
    card_json = json.dumps(card.model_dump(), ensure_ascii=False, indent=2)
    variants_data = [v.model_dump() for v in variants]
    variants_json = json.dumps(variants_data, ensure_ascii=False, indent=2)

    return f"""你是投放素材评审官。你的任务：对变体进行评审，并严格执行“五段式结构”门禁检查。

【硬性门禁规则】
1. 结构检查：检查 hook_type, why_you_trigger, motivation_bucket, why_now_trigger, cta 是否全部存在且属于指定的枚举值。
   - HOOK: {HOOK_ENUM}
   - WHY_YOU: {WHY_YOU_TRIGGER_ENUM}
   - MOTIVATION: {MOTIVATION_BUCKET_ENUM}
   - WHY_NOW: {WHY_NOW_TRIGGER_ENUM}
   - CTA: {CTA_ENUM}
   - 若任一字段缺失或不在枚举内：decision 必须为 HARD_FAIL。
2. 废词检查：若发现“痛点共鸣/利益前置/口碑背书/真香/必买/干货/强烈推荐”等营销废词：
   - decision 必须为 HARD_FAIL。
   - fuse.fuse_reasons 必须包含 "LOW_SIGNAL_LABEL"。
3. 修复建议：required_fixes 必须包含 fix/why/how 三段式详细说明。

【输出格式】
- 只输出一个 JSON 对象：{{"overall_summary":"...","results":[...]}}
- decision 仅允许：PASS / SOFT_FAIL / HARD_FAIL。

【输入数据】
CreativeCard: {card_json}
CreativeVariants: {variants_json}

现在开始输出 JSON：
"""

def build_experiment_prompt(card_json: str, review_json: str) -> str:
    """构建投放实验建议的 prompt"""
    return f"""你是「最小可行投放实验设计器」。请根据评审结果给出实验建议。
只输出一个 JSON 对象，包含 should_test, suggested_segment, suggested_channel_type, budget_range, gate_metrics, stop_loss_condition, experiment_goal。
要求：gate_metrics 必须包含具体的 CTR/IPM/CPI 阈值，stop_loss_condition 必须包含时间窗口。
输入：{review_json}
"""
