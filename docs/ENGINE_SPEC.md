# 投放实验设计引擎 · 引擎规范

## 核心定位

**你的任务不是「评素材好不好」，而是判断：这个【结构组合】是否值得进入下一轮验证。**

## 输入

| 输入 | 说明 |
|------|------|
| 1. 人群假设 | segment（country / os / user_type / context_scene） |
| 2. 动机桶 | motivation_bucket（场景+动机，如 帐篷·雨季将至·防雨耐用） |
| 3. 结构组合 | Hook / Sell point / Why now / CTA |
| 4. 早期代理指标 | iOS / Android 的 CTR、IPM、CPI（Explore 阶段） |

## 输出

| 输出 | 说明 |
|------|------|
| **当前假设状态** | PASS / FAIL / UNCERTAIN |
| **失败原因类型** | 假设问题（非素材问题）：INCONCLUSIVE / EFFICIENCY_FAIL / QUALITY_FAIL / HANDOFF_MISMATCH / OS_DIVERGENCE / MIXED_SIGNALS |
| **下一步** | 只允许改 1 个变量（OFAAT） |
| **样本不足** | 若样本不足，明确标注：**需要补样**（不下结论，禁止输出「结构不行」） |

## 与现有模块对应

| 引擎输出 | 对应模块 |
|----------|----------|
| 假设状态 PASS/FAIL/UNCERTAIN | `decision_summary.status` → status_text |
| 失败原因类型 | `diagnosis.failure_type` |
| 下一步（单变量） | `diagnosis.recommended_actions` → change_field |
| 需要补样 | `failure_type=INCONCLUSIVE`，`primary_signal=SAMPLE_TOO_LOW` |

## 规则摘要

- 样本不足 → **UNCERTAIN**，输出「需要补样」，不改结构
- 门禁失败 → **FAIL**，输出假设问题类型
- 跨窗稳定 + OS 不冲突 + 指标达线 → **PASS**
- 下一步处方：一次只改 1 个变量（OFAAT）
