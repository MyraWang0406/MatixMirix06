"""
投放实验决策系统 (Decision Support System) - 创意评测
整文件重构：UI 稳定、信息架构清晰、减少 rerun/布局抖动，保留全部功能。
"""
from __future__ import annotations

import inspect
import json
import sys
import traceback
from collections import defaultdict
from pathlib import Path

import streamlit as st
from pydantic import ValidationError

# ========================= 0) 路径注入 =========================
_THIS_DIR = Path(__file__).resolve().parent
_nested = _THIS_DIR / "MatrixMirix02"
_nested_path = str(_nested.resolve()) if _nested.exists() else ""
if _nested_path in sys.path:
    sys.path.remove(_nested_path)
_this_path = str(_THIS_DIR.resolve())
if _this_path not in sys.path:
    sys.path.insert(0, _this_path)
if _nested_path and _nested_path not in sys.path:
    sys.path.append(_nested_path)

# ========================= 1) 导入 =========================
try:
    from element_scores import ElementScore, compute_element_scores
    from eval_schemas import StrategyCard, Variant
    from eval_set_generator import CardEvalRecord, generate_eval_set
    from explore_gate import evaluate_explore_gate
    from ofaat_generator import generate_ofaat_variants
    from scoring_eval import compute_card_score, compute_variant_score
    from simulate_metrics import SimulatedMetrics, simulate_metrics
    from vertical_config import (
        get_corpus,
        get_why_now_pool,
        get_why_now_strong_stimulus_penalty,
        get_why_now_strong_triggers,
        get_why_you_examples,
    )
    from validate_gate import WindowMetrics, evaluate_validate_gate
    from variant_suggestions import next_variant_suggestions
    from decision_summary import compute_decision_summary

    try:
        from ui.styles import get_global_styles
    except Exception:
        get_global_styles = lambda: _FALLBACK_STYLES

    _RESOLVED_PATHS = {}
    for k in ("element_scores", "eval_schemas", "decision_summary", "variant_suggestions"):
        if k in sys.modules and hasattr(sys.modules[k], "__file__") and sys.modules[k].__file__:
            _RESOLVED_PATHS[k] = sys.modules[k].__file__
    if "ui.styles" in sys.modules and hasattr(sys.modules["ui.styles"], "__file__"):
        _RESOLVED_PATHS["ui.styles"] = sys.modules["ui.styles"].__file__ or "(built-in)"
    else:
        _RESOLVED_PATHS["ui.styles"] = "(fallback _FALLBACK_STYLES)"
except Exception as e:
    st.error(f"导入失败: {e}")
    st.code(traceback.format_exc(), language="text")
    st.stop()

try:
    from path_config import SAMPLES_DIR
except ImportError:
    SAMPLES_DIR = _THIS_DIR / "samples"
if not SAMPLES_DIR.exists():
    SAMPLES_DIR = _THIS_DIR.parent / "samples"

st.set_page_config(layout="wide", page_title="Decision Support System", initial_sidebar_state="expanded")

# 与 ui/styles 一致；ui 不可用时兜底
_FALLBACK_STYLES = """
<style>
[data-testid="stToolbar"],[data-testid="stAppToolbar"]{display:none!important;}
.main,.main>div,.main [data-testid="stVerticalBlock"]{max-width:none!important;width:100%!important;}
.main .block-container{padding:1rem!important;max-width:none!important;width:100%!important;margin:0!important;}
#ds-banner{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:1rem;min-height:130px;padding:1.25rem 1.5rem;margin:0 0 1rem 0;background:linear-gradient(90deg,#1E40AF 0%,#2563EB 55%,#3B82F6 100%);border-radius:18px;box-shadow:0 8px 24px rgba(15,23,42,0.18);position:relative;box-sizing:border-box;}
#ds-banner .ds-banner-icon{width:52px;height:52px;min-width:52px;border-radius:14px;background:rgba(255,255,255,0.2);backdrop-filter:blur(8px);box-shadow:0 2px 8px rgba(0,0,0,0.08);display:flex;align-items:center;justify-content:center;font-size:1.5rem;}
#ds-banner .ds-banner-titles{flex:1;min-width:0;}
#ds-banner .ds-banner-title{color:#fff;font-size:30px;font-weight:800;line-height:1.2;margin:0;letter-spacing:-0.02em;}
#ds-banner .ds-banner-subtitle{color:rgba(255,255,255,0.75);font-size:15px;margin-top:0.5cm;}
#ds-banner .ds-banner-actions{display:flex;align-items:center;gap:0.6rem;flex-wrap:wrap;flex-shrink:0;}
#ds-banner .ds-banner-footer{position:absolute;bottom:0.75rem;right:1.5rem;font-size:12px;color:rgba(255,255,255,0.7);}
div:has(#ds-banner){overflow:visible!important;}
div:has(#ds-banner)+div{overflow:visible!important;}
div:has(#ds-banner)+div [data-testid="stHorizontalBlock"]{margin-top:-6.5rem!important;position:relative;z-index:5;background:transparent!important;justify-content:flex-end!important;gap:0.35rem!important;}
div:has(#ds-banner)+div [data-testid="column"]{background:transparent!important;}
.contact-footer{position:fixed;bottom:0;right:0;background:#1a1a1a;color:#fff;padding:0.35rem 0.7rem;font-size:0.8rem;border-radius:8px 0 0 0;z-index:999;}
.contact-footer a{color:#fff;text-decoration:none;}
.decision-summary-hero{padding:1.2rem 1.5rem;margin:1rem 0 1.5rem 0;border-radius:10px;border-left:8px solid #2563EB;background:#fff;box-shadow:0 4px 12px rgba(37,99,235,0.12);}
.decision-summary-hero.status-pass{border-left-color:#2563EB;background:#F0F9FF!important;}
.decision-summary-hero.status-fail{border-left-color:#DC2626;background:#FEF2F2!important;}
.decision-summary-hero.status-warn{border-left-color:#2563EB;background:#FFFBEB!important;}
.decision-summary-hero .summary-label{font-weight:700;font-size:0.85rem;color:#1E3A8A;}
.decision-summary-hero .summary-status{font-size:1.35rem!important;font-weight:700!important;color:#1E293B;}
.decision-summary-hero .summary-row{font-size:0.95rem;color:#475569;}
button[kind="primary"]{background-color:#2563EB!important;color:#fff!important;}
[data-testid="stMultiSelect"] [data-baseweb="tag"]{background:#E0E7FF!important;color:#2563EB!important;max-width:none!important;}
[data-testid="stMultiSelect"] [data-baseweb="tag"] span{white-space:nowrap!important;overflow:visible!important;max-width:none!important;}
.ds-header-title{font-size:1.1rem!important;font-weight:600!important;color:#1E3A8A!important;}
.elevator-title{font-weight:600;color:#1E3A8A;}
.elevator-link{display:block;padding:0.3rem 0.5rem;color:#475569;text-decoration:none;border-radius:6px;}
.elevator-link:hover{background:#EFF6FF;color:#2563EB;}
[data-testid="stDataFrame"]{overflow-x:auto!important;}
.stExpander button[kind="primary"]{padding:0.5rem 1.2rem!important;font-size:1rem!important;font-weight:600!important;}
.stButtons{flex-wrap:nowrap!important;white-space:nowrap!important;}
.stButtons button,button{white-space:nowrap!important;}
</style>
"""

# session_state key 统一前缀，避免冲突
K = "ds_"

WINDOW_LABELS = {"window_1": "首测窗口（同日第1窗口）", "window_2": "跨天复测（跨日第2窗口）", "expand_segment": "轻扩人群（人群扩量阶段）"}
WINDOW_TOOLTIP = "验证分窗策略：首测=同日首次投放；跨天复测=跨日验证稳定性；轻扩人群=轻度扩圈后表现"
IPM_DROP_TOOLTIP = "IPM回撤（相对首测窗）：(首测IPM - 最低IPM) / 首测IPM"
CROSS_OS_TOOLTIP = "pos=双端一致拉/拖；neg=双端一致；mixed=双端不一致；样本不足=样本数<6"
OFAAT_FULL = "单因子实验（OFAAT, One-Factor-At-A-Time）"
OFAAT_TOOLTIP = "One-Factor-At-A-Time：一次只改一个变量"
DEFAULT_PLATFORMS = ["iOS", "Android"]
DEFAULT_SUGGESTED_N = 12
DEFAULT_SCALE_UP_STEP_PCT = "20%"


def _init_session_state():
    st.session_state.setdefault(f"{K}view", "决策看板")
    st.session_state.setdefault(f"{K}vertical", "休闲游戏")
    st.session_state.setdefault(f"{K}show_help", False)
    st.session_state.setdefault(f"{K}section", "sec-0")
    st.session_state.setdefault(f"{K}use_generated", False)
    st.session_state.setdefault(f"{K}generated_variants", None)
    st.session_state.setdefault(f"{K}experiment_queue", [])
    st.session_state.setdefault(f"{K}eval_records", [])
    st.session_state.setdefault(f"{K}evalset_size", 50)
    st.session_state.setdefault(f"{K}eval_status_filter", ["未测", "探索中", "进验证", "可放量"])
    st.session_state.setdefault(f"{K}debug", False)


def build_prompt_from_prescription(suggestion, diagnosis=None) -> str:
    reason = getattr(suggestion, "reason", "") or ""
    direction = getattr(suggestion, "direction", "") or ""
    recipe = getattr(suggestion, "experiment_recipe", "") or ""
    cf = getattr(suggestion, "changed_field", "") or ""
    alts = getattr(suggestion, "candidate_alternatives", None) or []
    target_os = getattr(suggestion, "target_os", "") or ""
    lines = ["## 下一轮实验处方（来自诊断）", "", f"**触发原因**: {reason}", f"**改动方向**: {direction}", f"**OFAAT 处方**: {recipe}", ""]
    if cf:
        lines.extend([f"**改动字段**: {cf}", f"**候选替代**: {', '.join(str(x) for x in alts[:3])}", ""])
    if target_os:
        lines.append(f"**目标端**: {target_os}（端内修正）")
    if diagnosis:
        ft = diagnosis.get("failure_type", "") if isinstance(diagnosis, dict) else getattr(diagnosis, "failure_type", "")
        ps = diagnosis.get("primary_signal", "") if isinstance(diagnosis, dict) else getattr(diagnosis, "primary_signal", "")
        if ft or ps:
            lines.extend(["", f"**诊断**: failure_type={ft}, primary_signal={ps}"])
    lines.extend(["", "请根据上述处方生成下一轮 OFAAT 变体，一次只改一个字段。"])
    return "\n".join(lines)


def build_experiment_package(suggestion, platforms=None, suggested_n=None, scale_up_step=None, diagnosis=None) -> dict:
    alts = getattr(suggestion, "candidate_alternatives", None) or []
    pkg = {
        "changed_field": getattr(suggestion, "changed_field", ""),
        "current_value": getattr(suggestion, "current_value", ""),
        "candidate_alternatives": [str(x) for x in alts],
        "platforms": platforms or DEFAULT_PLATFORMS.copy(),
        "suggested_n": suggested_n if suggested_n is not None else DEFAULT_SUGGESTED_N,
        "scale_up_step": scale_up_step or DEFAULT_SCALE_UP_STEP_PCT,
        "delta_desc": getattr(suggestion, "delta_desc", "") or "",
        "rationale": getattr(suggestion, "rationale", "") or "",
        "confidence_level": getattr(suggestion, "confidence_level", "medium"),
        "source": "suggestion",
        "reason": getattr(suggestion, "reason", "") or "",
        "direction": getattr(suggestion, "direction", "") or "",
        "experiment_recipe": getattr(suggestion, "experiment_recipe", "") or "",
        "target_os": getattr(suggestion, "target_os", "") or "",
    }
    pkg["prompt_for_next_round"] = build_prompt_from_prescription(suggestion, diagnosis)
    return pkg


def _queue_item_to_export_row(item: dict) -> dict:
    alts = item.get("candidate_alternatives", [])
    return {
        "changed_field": item.get("changed_field", ""),
        "current_value": item.get("current_value", ""),
        "candidate_alternatives": " | ".join(str(x) for x in alts),
        "platforms": ", ".join(item.get("platforms", [])),
        "suggested_n": item.get("suggested_n", DEFAULT_SUGGESTED_N),
        "scale_up_step": item.get("scale_up_step", DEFAULT_SCALE_UP_STEP_PCT),
        "delta_desc": item.get("delta_desc", ""),
        "source": item.get("source", "unknown"),
    }


def export_queue_json(queue: list) -> str:
    return json.dumps([dict(item) for item in queue], ensure_ascii=False, indent=2)


def export_queue_csv(queue: list) -> str:
    import io, csv
    if not queue:
        return "changed_field,current_value,candidate_alternatives,platforms,suggested_n,scale_up_step,delta_desc,source\n"
    rows = [_queue_item_to_export_row(item) for item in queue]
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


def _normalize_card_dict(raw: dict) -> dict:
    d = dict(raw)
    if not d.get("why_now_trigger"):
        for k in ("why_now_phrase", "why_now_trigger_bucket", "why_now", "trigger", "why_now_reason"):
            if d.get(k):
                d["why_now_trigger"] = str(d[k]).strip()
                break
        d.setdefault("why_now_trigger", "其他")
    if not d.get("motivation_bucket"):
        d.setdefault("motivation_bucket", "其他")
    return d


def _safe_load_strategy_card(raw: dict, source: str = "") -> tuple[StrategyCard, dict | None]:
    normalized = _normalize_card_dict(raw)
    try:
        card = StrategyCard.model_validate(normalized)
        return card, {"patched": normalized != raw, "source": source} if normalized != raw else None
    except ValidationError as e:
        vert = raw.get("vertical") or "casual_game"
        fallback = StrategyCard(
            card_id=raw.get("card_id", "fallback_card"), version=raw.get("version", "1.0"), vertical=vert,
            objective="purchase" if vert == "ecommerce" else "install", segment=raw.get("segment", "默认人群"),
            motivation_bucket="其他", why_now_trigger="其他",
        )
        return fallback, {"source": source, "missing": [err.get("loc", ()) for err in e.errors()], "msg": str(e), "fallback": True}


@st.cache_data(ttl=120)
def _load_mock_data_cached(vertical: str, motivation_bucket: str, variants_json: str | None) -> dict:
    """仅当 variants_json 为 None（从文件加载）时缓存；generated 不缓存"""
    return _load_mock_data_impl(vertical, motivation_bucket, variants_json)


def _load_mock_data_impl(vertical: str, motivation_bucket: str, variants_json: str | None) -> dict:
    vert = (vertical or "casual_game").lower()
    if vert not in ("ecommerce", "casual_game"):
        vert = "casual_game"
    card_path = SAMPLES_DIR / f"eval_strategy_card_{vert}.json"
    variant_path = SAMPLES_DIR / f"eval_variants_{vert}.json"
    if not card_path.exists():
        card_path = SAMPLES_DIR / "eval_strategy_card.json"
    if not variant_path.exists():
        variant_path = SAMPLES_DIR / "eval_variants.json"

    use_fallback = not card_path.exists() or not variant_path.exists()
    if use_fallback:
        records = generate_eval_set(n_cards=1, variants_per_card=12)
        if records:
            return _build_from_record(records[0], vert, motivation_bucket)
        raise ValueError("fallback generate_eval_set 失败")

    with open(card_path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    card, _ = _safe_load_strategy_card(raw, str(card_path))
    from vertical_config import get_sample_strategy_card, get_root_cause_gap
    sample = get_sample_strategy_card(vert)
    if sample:
        upd = {
            "vertical": vert, "motivation_bucket": motivation_bucket or sample.get("motivation_bucket") or card.motivation_bucket,
            "why_you_label": sample.get("why_you_phrase") or sample.get("why_you_label") or getattr(card, "why_you_label", "") or card.why_you_bucket,
            "why_now_trigger": sample.get("why_now_phrase") or sample.get("why_now_trigger") or getattr(card, "why_now_trigger", "其他"),
            "segment": sample.get("segment") or card.segment, "objective": sample.get("objective") or card.objective,
            "root_cause_gap": sample.get("root_cause_gap") or get_root_cause_gap(vert) or getattr(card, "root_cause_gap", "") or "",
        }
        try:
            card = card.model_copy(update={k: v for k, v in upd.items() if hasattr(card, k)})
        except Exception:
            card = card.model_copy(update=upd)

    if variants_json:
        variants = [Variant.model_validate(v) for v in json.loads(variants_json)]
        variants = [v.model_copy(update={"parent_card_id": card.card_id}) if v.parent_card_id != card.card_id else v for v in variants]
    else:
        with open(variant_path, "r", encoding="utf-8") as f:
            raw_v = json.load(f)
        variants = []
        for v in raw_v:
            try:
                obj = Variant.model_validate(v)
                variants.append(obj.model_copy(update={"parent_card_id": card.card_id}) if obj.parent_card_id != card.card_id else obj)
            except ValidationError:
                continue
        if not variants:
            raise ValueError(f"无有效变体: {variant_path}")

    mb = motivation_bucket or getattr(card, "motivation_bucket", "") or ("帐篷·雨季将至·防雨耐用" if vert == "ecommerce" else "消消乐·通勤碎片·连击爽感")
    metrics = []
    metrics.append(simulate_metrics(variants[0], "iOS", baseline=True, motivation_bucket=mb, vertical=vert))
    metrics.append(simulate_metrics(variants[0], "Android", baseline=True, motivation_bucket=mb, vertical=vert))
    for v in variants[1:]:
        metrics.append(simulate_metrics(v, "iOS", baseline=False, motivation_bucket=mb, vertical=vert))
        metrics.append(simulate_metrics(v, "Android", baseline=False, motivation_bucket=mb, vertical=vert))

    baseline_list = [m for m in metrics if m.baseline]
    variant_list = [m for m in metrics if not m.baseline]
    obj = (card.objective or "").strip() or ("purchase" if vert == "ecommerce" else "install")
    ctx_base = {"country": "CN", "objective": obj, "segment": card.segment, "motivation_bucket": mb}
    explore_ios = evaluate_explore_gate(variant_list, baseline_list, context={**ctx_base, "os": "iOS"})
    explore_android = evaluate_explore_gate(variant_list, baseline_list, context={**ctx_base, "os": "Android"})
    element_scores = compute_element_scores(variant_metrics=metrics, variants=variants)

    windowed = [
        WindowMetrics(window_id="window_1", impressions=50000, clicks=800, installs=2000, spend=6000, early_events=1200, early_revenue=480, ipm=40.0, cpi=3.0, early_roas=0.08),
        WindowMetrics(window_id="window_2", impressions=55000, clicks=880, installs=2090, spend=6270, early_events=1250, early_revenue=500, ipm=38.0, cpi=3.0, early_roas=0.08),
    ]
    light_exp = WindowMetrics(window_id="expand_segment", impressions=20000, clicks=288, installs=720, spend=2160, early_events=430, early_revenue=172, ipm=36.0, cpi=3.0, early_roas=0.08)
    validate_result = evaluate_validate_gate(windowed, light_exp)

    from diagnosis import diagnose
    from eval_schemas import decompose_variant_to_element_tags
    diagnosis_result = diagnose(explore_ios=explore_ios, explore_android=explore_android, validate_result=validate_result, metrics=metrics)
    variant_to_tags = {v.variant_id: decompose_variant_to_element_tags(v) for v in variants}
    _kwargs = dict(element_scores=element_scores, gate_result=explore_android, max_suggestions=3, variant_metrics=metrics, variant_to_tags=variant_to_tags, variants=variants, vertical=vert)
    if "diagnosis" in inspect.signature(next_variant_suggestions).parameters:
        _kwargs["diagnosis"] = diagnosis_result
    suggestions = next_variant_suggestions(**_kwargs)

    variant_scores_by_row = {}
    for m in metrics:
        cohort = [x for x in metrics if x.os == m.os]
        variant_scores_by_row[(m.variant_id, m.os)] = compute_variant_score(m, cohort, os=m.os, vertical=vert)
    by_vid = defaultdict(list)
    for (vid, _), s in variant_scores_by_row.items():
        by_vid[vid].append(s)
    variant_scores_agg = {vid: sum(s) / len(s) for vid, s in by_vid.items()}
    eligible_all = list(dict.fromkeys((explore_ios.eligible_variants or []) + (explore_android.eligible_variants or [])))
    stab_penalty = 5.0 if validate_result.validate_status == "FAIL" else 0.0
    why_now_penalty = 0.0
    strong_triggers = get_why_now_strong_triggers(vert)
    wn_trigger = getattr(card, "why_now_trigger", "") or ""
    if wn_trigger in strong_triggers:
        why_now_penalty = get_why_now_strong_stimulus_penalty(vert)
    elif any(("why now" in n.lower() or "虚高" in n or "强刺激" in n) for n in validate_result.risk_notes):
        why_now_penalty = get_why_now_strong_stimulus_penalty(vert) * 0.5
    card_score_result = compute_card_score(eligible_variants=eligible_all, variant_scores=variant_scores_agg, top_k=5, stability_penalty=stab_penalty, why_now_strong_stimulus_penalty=why_now_penalty)
    return {"card": card, "vertical": vert, "variants": variants, "metrics": metrics, "explore_ios": explore_ios, "explore_android": explore_android, "element_scores": element_scores, "suggestions": suggestions, "validate_result": validate_result, "variant_scores_by_row": variant_scores_by_row, "card_score_result": card_score_result, "diagnosis": diagnosis_result}


def _build_from_record(rec, vert: str, motivation_bucket: str) -> dict:
    card, variants = rec.card, rec.variants
    mb = motivation_bucket or card.motivation_bucket or ("帐篷·雨季将至·防雨耐用" if vert == "ecommerce" else "消消乐·通勤碎片·连击爽感")
    metrics = []
    metrics.append(simulate_metrics(variants[0], "iOS", baseline=True, motivation_bucket=mb, vertical=vert))
    metrics.append(simulate_metrics(variants[0], "Android", baseline=True, motivation_bucket=mb, vertical=vert))
    for v in variants[1:]:
        metrics.append(simulate_metrics(v, "iOS", baseline=False, motivation_bucket=mb, vertical=vert))
        metrics.append(simulate_metrics(v, "Android", baseline=False, motivation_bucket=mb, vertical=vert))
    element_scores = compute_element_scores(variant_metrics=metrics, variants=variants)
    from diagnosis import diagnose
    from eval_schemas import decompose_variant_to_element_tags
    diag = diagnose(explore_ios=rec.explore_ios, explore_android=rec.explore_android, validate_result=rec.validate_result, metrics=metrics)
    _kwargs = dict(element_scores=element_scores, gate_result=rec.explore_android, max_suggestions=3, variant_metrics=metrics, variant_to_tags={v.variant_id: decompose_variant_to_element_tags(v) for v in variants}, variants=variants, vertical=vert)
    if "diagnosis" in inspect.signature(next_variant_suggestions).parameters:
        _kwargs["diagnosis"] = diag
    suggestions = next_variant_suggestions(**_kwargs)
    variant_scores_by_row = {}
    for m in metrics:
        cohort = [x for x in metrics if x.os == m.os]
        variant_scores_by_row[(m.variant_id, m.os)] = compute_variant_score(m, cohort, os=m.os, vertical=vert)
    by_vid = defaultdict(list)
    for (vid, _), s in variant_scores_by_row.items():
        by_vid[vid].append(s)
    variant_scores_agg = {vid: sum(s) / len(s) for vid, s in by_vid.items()}
    variant_list = [m for m in metrics if not m.baseline]
    card_score_result = compute_card_score(eligible_variants=variant_list, variant_scores=variant_scores_agg, top_k=5, stability_penalty=0.1, why_now_strong_stimulus_penalty=0.05)
    return {"card": card, "vertical": vert, "variants": variants, "metrics": metrics, "explore_ios": rec.explore_ios, "explore_android": rec.explore_android, "element_scores": element_scores, "suggestions": suggestions, "validate_result": rec.validate_result, "variant_scores_by_row": variant_scores_by_row, "card_score_result": card_score_result, "diagnosis": diag}


def load_mock_data(variants=None, vertical_override=None, motivation_bucket_override=None):
    vert = (vertical_override or "casual_game").lower()
    mb = motivation_bucket_override or "成就感"
    variants_json = None
    if variants:
        variants_json = json.dumps([v.model_dump() if hasattr(v, "model_dump") else (v.dict() if hasattr(v, "dict") else {}) for v in variants], ensure_ascii=False)
    try:
        if variants_json is None:
            return _load_mock_data_cached(vert, mb, None)
        return _load_mock_data_impl(vert, mb, variants_json)
    except Exception as e:
        st.session_state[f"{K}load_error"] = str(e)
        st.session_state[f"{K}load_trace"] = traceback.format_exc()
        return None


def _render_health_page():
    st.subheader("🏥 健康检查 (Health Check)")
    rows = [("Python", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"), ("Streamlit", st.__version__)]
    for name in ["pydantic", "element_scores", "eval_schemas", "decision_summary", "diagnosis"]:
        try:
            __import__(name)
            rows.append((f"import {name}", "✓"))
        except Exception as e:
            rows.append((f"import {name}", f"✗ {str(e)[:60]}"))
    for k, v in rows:
        st.write(f"**{k}**: {v}")
    st.success("健康检查完成")


def _render_review_page():
    st.subheader("📊 复盘检索")
    try:
        from knowledge_store import query_review
    except ImportError:
        st.warning("knowledge_store 未安装")
        return
    r1 = st.columns([1, 1, 1, 1, 1, 1])
    with r1[0]:
        vert = st.selectbox("行业", ["", "ecommerce", "casual_game"], format_func=lambda x: x or "全部", key=f"{K}review_vert")
    with r1[1]:
        ch = st.selectbox("渠道", ["", "Meta", "TikTok", "Google"], format_func=lambda x: x or "全部", key=f"{K}review_ch")
    with r1[2]:
        country = st.selectbox("国家", ["", "US", "JP", "KR", "TH", "VN", "BR", "CN"], format_func=lambda x: x or "全部", key=f"{K}review_country")
    with r1[3]:
        seg = st.selectbox("人群", ["", "new", "returning", "retargeting"], format_func=lambda x: x or "全部", key=f"{K}review_seg")
    with r1[4]:
        os_f = st.selectbox("OS", ["", "iOS", "Android"], format_func=lambda x: x or "全部", key=f"{K}review_os")
    with r1[5]:
        mb = st.selectbox("场景+动机", ["", "帐篷·雨季将至·防雨耐用", "宠物肖像油画·送礼怕不合心意·更匹配我", "消消乐·通勤碎片·连击爽感", "贪吃蛇·无聊专注·经典怀旧", "Gossip Harbor·朋友都在玩·社交归属", "其他"], format_func=lambda x: x or "全部", key=f"{K}review_mb")
    result = query_review(vertical=vert or None, channel=ch or None, country=country or None, segment=seg.strip() or None, os_filter=os_f or None, motivation_bucket=mb or None)
    m1, m2, m3 = st.columns(3)
    with m1: st.metric("实验数", result["total_experiments"])
    with m2: st.metric("Explore PASS 率", f"{result['explore_pass_rate']:.0%}")
    with m3: st.metric("Validate PASS 率", f"{result['validate_pass_rate']:.0%}")
    st.write("**failure_type 分布 Top3**")
    st.json(dict(result.get("top3_failure_type", [])))
    st.write("**该分层表现最稳的结构 Top10**")
    st.dataframe(result.get("top_structures_by_pass", []), hide_index=True)


def _render_decision_summary_card(summary: dict):
    status = summary.get("status", "yellow")
    status_text = summary.get("status_text", "🟡 小步复测(20%)")
    reason = summary.get("reason", "")
    risk = summary.get("risk", "")
    next_step = summary.get("next_step", "复测")
    diag = summary.get("diagnosis", {}) or {}
    if hasattr(diag, "failure_type"):
        failure_type, primary_signal = getattr(diag, "failure_type", ""), getattr(diag, "primary_signal", "")
        actions = getattr(diag, "recommended_actions", []) or []
    else:
        failure_type, primary_signal = diag.get("failure_type", ""), diag.get("primary_signal", "")
        actions = diag.get("recommended_actions", []) or []
    status_class = "status-fail" if status == "red" else ("status-pass" if status == "green" else "status-warn")
    diag_line = f'<div class="summary-row"><b>诊断：</b>failure_type: {failure_type} | primary_signal: {primary_signal}</div>' if failure_type or primary_signal else ""
    act_strs = [f"{a.get('action','')}({a.get('change_field','')})" if isinstance(a, dict) else f"{getattr(a,'action','')}({getattr(a,'change_field','')})" for a in actions[:3] if a]
    actions_line = f'<div class="summary-row"><b>处方：</b>{"; ".join(act_strs)}</div>' if act_strs else ""
    html = f"""<div class="decision-summary-hero {status_class}"><div class="summary-label">📌 决策结论 Summary</div><div class="summary-status">{status_text}</div><div class="summary-row"><b>原因：</b>{reason}</div><div class="summary-row"><b>风险：</b>{risk}</div><div class="summary-row"><b>下一步：</b>{next_step}</div>{diag_line}{actions_line}</div>"""
    st.markdown(html, unsafe_allow_html=True)
    bc = st.columns([1, 1, 1, 5])
    with bc[0]:
        if st.button("🔄 复测", key=f"{K}retest", type="secondary"):
            st.toast("复测（占位）")
    with bc[1]:
        if st.button("📈 放量", key=f"{K}scale", disabled=(next_step != "放量"), type="secondary"):
            st.toast("放量（占位）")
    with bc[2]:
        if st.button("➕ 加入实验队列", key=f"{K}queue", type="secondary"):
            st.toast("加入实验队列（占位）")
    st.divider()


def _render_experiment_queue_sidebar():
    q = st.session_state.get(f"{K}experiment_queue", [])
    st.markdown("**■ 实验队列**")
    if not q:
        st.caption("暂无实验，从「变体建议」或「元素贡献」加入")
        return
    for idx, item in enumerate(q):
        field = item.get("changed_field", "-")
        curr = (item.get("current_value", "") or "")[:12]
        alts = item.get("candidate_alternatives", [])[:2]
        st.caption(f"{idx + 1}. {field}: {curr} → {', '.join(str(a) for a in alts) or '-'}")
        if st.button("移除", key=f"{K}q_rm_{idx}"):
            st.session_state[f"{K}experiment_queue"] = [x for i, x in enumerate(q) if i != idx]
            st.rerun()
    if st.button("清空队列", key=f"{K}q_clear"):
        st.session_state[f"{K}experiment_queue"] = []
        st.rerun()
    st.divider()
    st.caption("导出")
    st.download_button("⬇ JSON", data=export_queue_json(q), file_name="experiment_queue.json", mime="application/json", key=f"{K}dl_json")
    st.download_button("⬇ CSV", data=export_queue_csv(q), file_name="experiment_queue.csv", mime="text/csv", key=f"{K}dl_csv")


def _multiselect_safe(label: str, options: list[str], key: str, default_all: bool = True):
    if not options:
        return []
    wk = f"{K}{key}_ms"
    cur = st.session_state.get(wk, None)
    if cur is None:
        st.session_state[wk] = options if default_all else options[:3]
    else:
        valid = [x for x in cur if x in options]
        if not valid:
            st.session_state[wk] = options[:1]
    col_sel, col_btn = st.columns([4, 1])
    with col_btn:
        if st.button("全选", key=f"{wk}_all"):
            st.session_state[wk] = options.copy()
            st.rerun()
        if st.button("清空", key=f"{wk}_clear"):
            st.session_state[wk] = []
            st.rerun()
    with col_sel:
        return st.multiselect(label, options=options, key=wk, placeholder="选 1 项以上…")


def render_eval_set_view():
    st.session_state.setdefault(f"{K}evalset_size", 50)
    col_n, col_btn, _ = st.columns([1, 1, 4])
    with col_n:
        n_cards = st.number_input("卡片数量", min_value=50, max_value=100, step=5, key=f"{K}evalset_size")
    with col_btn:
        if st.button("生成 / 重新生成评测集", type="primary", key=f"{K}eval_gen"):
            try:
                with st.spinner("生成评测集中..."):
                    records = generate_eval_set(n_cards=int(st.session_state.get(f"{K}evalset_size", 50)), variants_per_card=12)
                    st.session_state[f"{K}eval_records"] = records
                    st.session_state.pop(f"{K}eval_error", None)
                st.rerun()
            except Exception as e:
                st.session_state[f"{K}eval_error"] = str(e)
                st.session_state[f"{K}eval_trace"] = traceback.format_exc()
                st.rerun()
        try:
            from evalset_sampler import sample_structure_evalset
            from eval_set_generator import generate_eval_set_from_cards
            n_samp = int(st.session_state.get(f"{K}evalset_size", 50))
            if st.button(f"分层抽样(N={n_samp})", key=f"{K}eval_sampler"):
                try:
                    with st.spinner("分层抽样生成..."):
                        evalset = sample_structure_evalset(N=n_samp)
                        records = generate_eval_set_from_cards(evalset.cards, variants_per_card=12)
                        st.session_state[f"{K}eval_records"] = records
                        st.session_state.pop(f"{K}eval_error", None)
                    st.rerun()
                except Exception as e:
                    st.session_state[f"{K}eval_error"] = str(e)
                    st.session_state[f"{K}eval_trace"] = traceback.format_exc()
                    st.rerun()
        except ImportError:
            pass

    records = st.session_state.get(f"{K}eval_records", [])
    if st.session_state.get(f"{K}eval_error"):
        st.error(f"生成出错：{st.session_state[f'{K}eval_error']}")
        with st.expander("错误详情"):
            st.code(st.session_state.get(f"{K}eval_trace", ""), language="text")
        if st.button("清除错误", key=f"{K}eval_clear_err"):
            st.session_state.pop(f"{K}eval_error", None)
            st.rerun()
        return
    if not records:
        st.info("暂无数据，请点击「生成 / 重新生成评测集」或「分层抽样」")
        return

    tab1, tab2, tab3 = st.tabs(["结构评测集", "探索评测集", "验证评测集"])
    with tab1:
        status_filter = st.multiselect("筛选状态", ["未测", "探索中", "进验证", "可放量"], key=f"{K}eval_status", default=["未测", "探索中", "进验证", "可放量"])
        filtered = [r for r in records if r.status in status_filter] if status_filter else records
        show_all = st.checkbox("显示全部行", key=f"{K}show_all_cards", value=False)
        display_records = filtered if show_all else filtered[:20]
        rows = [{"卡片ID": r.card.card_id, "分数": f"{r.card_score:.1f}", "状态": r.status, "场景+动机": r.card.motivation_bucket, "行业": "休闲游戏" if r.card.vertical == "casual_game" else "电商", "人群": (r.card.segment[:20] + "…" if len(r.card.segment) > 20 else r.card.segment)} for r in display_records]
        st.dataframe(rows, width="stretch", hide_index=True)
        if not show_all and len(filtered) > 20:
            st.caption(f"仅显示前 20 张，共 {len(filtered)} 张。勾选「显示全部行」查看完整列表")
    with tab2:
        rows = [{"卡片": r.card.card_id, "状态": r.status, "变体数": len(r.variants), "iOS 通过": len(r.explore_ios.eligible_variants or []), "Android 通过": len(r.explore_android.eligible_variants or []), "iOS 门禁": "✓" if r.explore_ios.gate_status == "PASS" else "✗", "Android 门禁": "✓" if r.explore_android.gate_status == "PASS" else "✗"} for r in records]
        st.dataframe(rows, width="stretch", hide_index=True)
    with tab3:
        val_records = [r for r in records if r.status in ("进验证", "可放量") and r.validate_result]
        if not val_records:
            st.info("暂无进入验证阶段的卡片")
        else:
            show_all_val = st.checkbox("显示全部验证明细", key=f"{K}show_all_val", value=False)
            display_val = val_records if show_all_val else val_records[:10]
            for r in display_val:
                with st.expander(f"{r.card.card_id} | {r.status} | Validate:{r.validate_result.validate_status}"):
                    if r.validate_result.detail_rows:
                        detail_data = [{"窗口": WINDOW_LABELS.get(row.window_id, row.window_id), "千次展示安装(IPM)": f"{row.ipm:.2f}", "单次安装成本(CPI)": f"{row.cpi:.2f}", "早期回报率": f"{row.early_roas:.2%}"} for row in r.validate_result.detail_rows]
                        st.dataframe(detail_data, hide_index=True)
                    sm = getattr(r.validate_result, "stability_metrics", None)
                    if sm:
                        st.caption(f"波动={sm.ipm_cv:.2%} 回撤={sm.ipm_drop_pct:.1f}%")
                    for n in r.validate_result.risk_notes:
                        st.caption(f"• {n}")
            if not show_all_val and len(val_records) > 10:
                st.caption(f"仅显示前 10 张，共 {len(val_records)} 张")


def _render_gate_section(data: dict, metrics: list):
    st.subheader("3️⃣ 门禁状态与结论")
    card_score_result = data.get("card_score_result", {})
    st.metric("卡片总分", f"{card_score_result.get('card_score', 0.0):.1f}")
    t1, t2 = st.tabs(["探索门禁", "验证门禁"])
    baseline_list = [m for m in metrics if m.baseline]
    baseline_by_os = {m.os: m for m in baseline_list}
    exp_ios, exp_android = data["explore_ios"], data["explore_android"]
    with t1:
        os_tabs = st.tabs(["iOS", "Android"])
        for tab, os_name, exp in [(os_tabs[0], "iOS", exp_ios), (os_tabs[1], "Android", exp_android)]:
            with tab:
                status_icon = "🟢" if exp.gate_status == "PASS" else "🔴" if exp.gate_status == "FAIL" else "🟡"
                st.write(f"**{os_name}** {status_icon} `{exp.gate_status}`")
                bl = baseline_by_os.get(os_name)
                if bl:
                    variant_metrics_os = [m for m in metrics if m.os == os_name and not m.baseline]
                    gate_rows = []
                    for m in variant_metrics_os:
                        better = sum([m.ctr > bl.ctr, m.ipm > bl.ipm, m.cpi < bl.cpi])
                        gate_rows.append({"变体ID": m.variant_id, "千次展示安装(IPM)": f"{m.ipm:.1f}", "单次安装成本(CPI)": f"${m.cpi:.2f}", "早期回报率": f"{m.early_roas:.2%}", "≥2指标超baseline": "是" if better >= 2 else "否", "结论": exp.variant_details.get(m.variant_id, "-")})
                    if gate_rows:
                        st.dataframe(gate_rows, hide_index=True)
                with st.expander("门禁说明"):
                    if exp.eligible_variants:
                        st.success(f"通过: {', '.join(exp.eligible_variants)}")
                    for r in exp.reasons:
                        st.caption(f"• {r}")
    with t2:
        v = data["validate_result"]
        st.write("**Validate**", "🟢 PASS" if v.validate_status == "PASS" else "🔴 FAIL")
        if getattr(v, "detail_rows", None) and v.detail_rows:
            detail_data = [{"窗口": WINDOW_LABELS.get(r.window_id, r.window_id), "千次展示安装(IPM)": f"{r.ipm:.2f}", "单次安装成本(CPI)": f"{r.cpi:.2f}", "早期回报率": f"{r.early_roas:.2%}"} for r in v.detail_rows]
            st.dataframe(detail_data, hide_index=True)
        if getattr(v, "stability_metrics", None):
            sm = v.stability_metrics
            with st.expander("稳定性指标"):
                st.caption(f"波动: {sm.ipm_cv:.2%} 回撤: {sm.ipm_drop_pct:.1f}%")
        with st.expander("风险提示"):
            for n in v.risk_notes:
                st.caption(f"• {n}")


def _render_element_scores_section(data: dict):
    st.subheader("4️⃣ 元素级贡献表")
    st.caption(CROSS_OS_TOOLTIP)
    scores = data.get("element_scores", [])
    if not scores:
        st.caption("暂无元素贡献数据")
        return
    dim_opts, dim_map = ["Hook", "why_you_bucket", "why_now_trigger", "卖点", "CTA"], {"Hook": "hook", "why_you_bucket": "why_you", "why_now_trigger": "why_now", "卖点": "sell_point", "CTA": "cta"}
    c1, c2 = st.columns([1, 3])
    with c1:
        dim = st.selectbox("选择维度", dim_opts, key=f"{K}elem_dim")
    with c2:
        search = st.text_input("搜索", key=f"{K}elem_search", placeholder="关键词过滤…")
    et_key = dim_map.get(dim, "hook")
    subset = [s for s in scores if s.element_type == et_key]
    if search and search.strip():
        q = search.strip().lower()
        subset = [s for s in subset if q in (s.element_value or "").lower()]
    subset.sort(key=lambda s: -s.sample_size)
    show_full = st.checkbox("展开全部元素", key=f"{K}elem_show_full", value=False)
    display_subset = subset if show_full else subset[:15]
    for idx, s in enumerate(display_subset):
        conf = getattr(s, "confidence_level", "low")
        cross_os = getattr(s, "cross_os_consistency", "mixed")
        tendency = "不确定" if conf == "low" else ("拉" if (s.avg_IPM_delta_vs_card_mean > 0 or s.avg_CPI_delta_vs_card_mean < 0) else "拖")
        ipm_d = f"{s.avg_IPM_delta_vs_card_mean:+.1f}" if conf != "low" else "-"
        cpi_d = f"{s.avg_CPI_delta_vs_card_mean:+.2f}" if conf != "low" else "-"
        sample_lbl = "样本不足" if not getattr(s, "stability_flag", s.sample_size >= 2) else f"n={s.sample_size}"
        key = f"{K}elem_{et_key}_{idx}"
        with st.expander(f"{s.element_value[:36]}{'…' if len(s.element_value) > 36 else ''} | 倾向:{tendency} | IPMΔ:{ipm_d} CPIΔ:{cpi_d} | {sample_lbl}"):
            st.caption(f"维度: {dim}")
            btn_col = st.columns(2)
            with btn_col[0]:
                if st.button("复制 Prompt", key=f"{key}_copy"):
                    fake = type("S", (), {"reason": "元素表现待验证", "direction": f"尝试替换 {dim}", "experiment_recipe": f"OFAAT 只改 {et_key}", "changed_field": et_key, "candidate_alternatives": [], "target_os": ""})()
                    st.code(build_prompt_from_prescription(fake, data.get("diagnosis")))
            with btn_col[1]:
                if st.button("加入实验队列", key=f"{key}_queue"):
                    q = st.session_state.get(f"{K}experiment_queue", [])
                    q.append({"changed_field": et_key, "current_value": s.element_value, "candidate_alternatives": []})
                    st.session_state[f"{K}experiment_queue"] = q
                    st.toast("已加入")
                    st.rerun()
    if not show_full and len(subset) > 15:
        st.caption(f"仅显示前 15 个，共 {len(subset)} 个。勾选「展开全部元素」查看")


def _render_suggestions_section(data: dict):
    st.subheader("5️⃣ 下一步变体建议")
    suggestions = data.get("suggestions", [])
    if not suggestions:
        st.caption("样本不足或暂无优化建议")
        return
    table_rows = []
    for i, s in enumerate(suggestions):
        cf = getattr(s, "changed_field", "") or "-"
        curr = getattr(s, "current_value", "") or "-"
        alts = getattr(s, "candidate_alternatives", []) or []
        alts_str = ", ".join(str(x) for x in alts[:3])
        exp_metric = getattr(s, "expected_metric", "") or getattr(s, "expected_improvement", "IPM")
        conf = getattr(s, "confidence_level", "low")
        conf_lbl = {"high": "高", "medium": "中", "low": "低"}.get(conf, "低")
        table_rows.append({"改动字段": cf, "当前→候选": f"{curr[:20]}… → {alts_str[:40]}…" if len(curr) > 20 or len(alts_str) > 40 else f"{curr} → {alts_str}", "预期提升": exp_metric, "置信度": conf_lbl, "推荐": "复测" if conf == "low" else "替换"})
    st.dataframe(table_rows, hide_index=True)
    show_details = st.checkbox("展开实验工单详情", key=f"{K}sug_show_details", value=False)
    if show_details:
        for i, s in enumerate(suggestions):
            conf_lbl = {"high": "高", "medium": "中", "low": "低"}.get(getattr(s, "confidence_level", "low"), "低")
            with st.expander(f"实验工单{i+1} | 置信度:{conf_lbl}"):
                st.write("**改动:**", getattr(s, "delta_desc", "") or "-")
                st.write("**候选:**", ", ".join(str(x) for x in (getattr(s, "candidate_alternatives", []) or [])))
                st.write("**依据:**", getattr(s, "rationale", "") or "-")
                bc1, bc2, bc3 = st.columns(3)
                with bc1:
                    if st.button("复制 Prompt", key=f"{K}sug_copy_{i}"):
                        st.code(build_prompt_from_prescription(s, data.get("diagnosis")))
                with bc2:
                    if st.button("加入实验队列", key=f"{K}sug_queue_{i}"):
                        pkg = build_experiment_package(s, diagnosis=data.get("diagnosis"))
                        q = st.session_state.get(f"{K}experiment_queue", [])
                        q.append(pkg)
                        st.session_state[f"{K}experiment_queue"] = q
                        st.toast("已加入")
                        st.rerun()
                with bc3:
                    if st.button("一键生成下一轮", key=f"{K}sug_gen_{i}"):
                        st.toast("占位：可对接后续流程")


def main():
    _init_session_state()
    st.markdown(get_global_styles(), unsafe_allow_html=True)
    st.markdown('<div class="contact-footer">联系作者 <a href="mailto:myrawzm0406@163.com">myrawzm0406@163.com</a></div>', unsafe_allow_html=True)

    view = st.session_state.get(f"{K}view", "决策看板")
    vert_idx = st.session_state.get(f"{K}vertical", "休闲游戏")
    vertical_choice = "casual_game" if vert_idx == "休闲游戏" else "ecommerce"

    # 产品级 Banner Header
    st.markdown("""
<div id="ds-banner">
  <div class="ds-banner-icon">📊</div>
  <div class="ds-banner-titles">
    <div class="ds-banner-title">决策看板</div>
    <div class="ds-banner-subtitle">投放实验设计引擎 · 结构组合验证</div>
  </div>
  <div class="ds-banner-actions" id="ds-banner-slot"></div>
  <div class="ds-banner-footer">结构可解释 · 胜率可复用</div>
</div>
""", unsafe_allow_html=True)
    hc1, hc2, hc3, hc4, hc5, hc6, hc7, hc8, hc9 = st.columns([2, 0.8, 0.8, 0.8, 1, 0.35, 0.7, 0.7, 0.5])
    with hc2:
        if st.button("决策", type="primary" if view == "决策看板" else "secondary", key=f"{K}tab_board"):
            st.session_state[f"{K}view"] = "决策看板"
            st.rerun()
    with hc3:
        if st.button("评测集", type="primary" if view == "评测集" else "secondary", key=f"{K}tab_eval"):
            st.session_state[f"{K}view"] = "评测集"
            st.rerun()
    with hc4:
        if st.button("Health", type="primary" if view == "Health" else "secondary", key=f"{K}tab_health"):
            st.session_state[f"{K}view"] = "Health"
            st.rerun()
    with hc5:
        if st.button("复盘检索", type="primary" if view == "复盘检索" else "secondary", key=f"{K}tab_review"):
            st.session_state[f"{K}view"] = "复盘检索"
            st.rerun()
    with hc6:
        st.markdown('<span style="color:#64748B;font-size:0.8rem;">行业</span>', unsafe_allow_html=True)
    with hc7:
        if st.button("Game", type="primary" if vert_idx == "休闲游戏" else "secondary", key=f"{K}vert_game"):
            st.session_state[f"{K}vertical"] = "休闲游戏"
            st.session_state[f"{K}use_generated"] = False
            st.session_state[f"{K}generated_variants"] = None
            st.rerun()
    with hc8:
        if st.button("eCommerce", type="primary" if vert_idx == "电商" else "secondary", key=f"{K}vert_ec"):
            st.session_state[f"{K}vertical"] = "电商"
            st.session_state[f"{K}use_generated"] = False
            st.session_state[f"{K}generated_variants"] = None
            st.rerun()
    with hc9:
        st.checkbox("帮助", key=f"{K}show_help")

    if st.session_state.get(f"{K}show_help"):
        st.info("选择「决策看板」或「评测集」。决策看板：筛选 Hook/卖点/CTA 后点「生成并评测」。")

    with st.sidebar:
        st.markdown('<div class="elevator-title">★ 电梯导航</div>', unsafe_allow_html=True)
        section = st.radio("section", ["sec-0", "sec-1", "sec-2", "sec-3", "sec-4", "sec-5"], format_func=lambda x: {"sec-0": "0 决策结论", "sec-1": "1 结构卡片", "sec-2": "2 实验对照表", "sec-3": "3 门禁状态", "sec-4": "4 元素贡献", "sec-5": "5 变体建议"}.get(x, x), key=f"{K}section", label_visibility="collapsed")
        st.divider()
        _render_experiment_queue_sidebar()
        st.checkbox("Debug", key=f"{K}debug")
        if st.session_state.get(f"{K}debug"):
            with st.expander("模块路径"):
                for k, v in _RESOLVED_PATHS.items():
                    st.caption(f"{k}: {v}")
            with st.expander("数据规模"):
                st.caption(f"evalset_size: {st.session_state.get(f'{K}evalset_size', 50)}")
                st.caption(f"SAMPLES_DIR: {SAMPLES_DIR}")
                st.caption(f"存在: {SAMPLES_DIR.exists()}")

    if view == "Health":
        _render_health_page()
        return
    if view == "复盘检索":
        _render_review_page()
        return
    if view == "评测集":
        render_eval_set_view()
        return

    corp = get_corpus(vertical_choice)
    hook_opts = corp.get("hook_type") or ["反差(Before/After)", "冲突", "结果先行", "痛点", "爽点"]
    sell_opts = corp.get("sell_point") or ["示例卖点"]
    cta_opts = corp.get("cta") or ["立即下载", "现在试试", "立即下单", "立刻试玩"]
    mb_opts = corp.get("motivation_bucket") or ["消消乐·通勤碎片·连击爽感", "贪吃蛇·无聊专注·经典怀旧", "其他"]

    if f"{K}filter_mb" not in st.session_state or st.session_state.get(f"{K}filter_mb") not in mb_opts:
        st.session_state[f"{K}filter_mb"] = mb_opts[0]

    who_scenario_opts = (corp.get("who_scenario_need") or []) if vertical_choice == "ecommerce" else []
    has_data = st.session_state.get(f"{K}use_generated", False)
    with st.expander("Filter & Generate · 筛选与生成", expanded=not has_data):
        if vertical_choice == "ecommerce" and who_scenario_opts:
            r1 = st.columns([2, 2, 2, 2, 1])
            with r1[0]: hooks = _multiselect_safe("Hook", hook_opts, f"hook_{vertical_choice}")
            with r1[1]: sells = _multiselect_safe("卖点", sell_opts, f"sell_{vertical_choice}")
            with r1[2]: who_scenario = _multiselect_safe("人/场景/需求", who_scenario_opts, f"who_{vertical_choice}")
            with r1[3]: ctas = _multiselect_safe("CTA", cta_opts, f"cta_{vertical_choice}")
            with r1[4]: st.selectbox("场景+动机", mb_opts, key=f"{K}filter_mb")
        else:
            who_scenario = []
            r1 = st.columns([2, 2, 2, 1])
            with r1[0]: hooks = _multiselect_safe("Hook", hook_opts, f"hook_{vertical_choice}")
            with r1[1]: sells = _multiselect_safe("卖点", sell_opts, f"sell_{vertical_choice}")
            with r1[2]: ctas = _multiselect_safe("CTA", cta_opts, f"cta_{vertical_choice}")
            with r1[3]: st.selectbox("场景+动机", mb_opts, key=f"{K}filter_mb")
        r2 = st.columns([1, 0.3, 1.8])
        with r2[0]:
            st.number_input("N", min_value=1, max_value=24, step=1, key=f"{K}n_gen", help="生成变体数量")
        with r2[1]:
            if st.session_state.get(f"{K}use_generated") and st.button("恢复示例", type="secondary"):
                st.session_state[f"{K}use_generated"] = False
                st.session_state[f"{K}generated_variants"] = None
                st.rerun()
        with r2[2]:
            if st.button("生成并评测", type="primary"):
                if not hooks or not sells or not ctas:
                    st.error("请至少各选 1 项 hook、卖点、CTA")
                else:
                    sell_points_for_gen = list(sells)
                    if vertical_choice == "ecommerce" and who_scenario:
                        sell_points_for_gen = [s + " | " + "、".join(who_scenario) for s in sells]
                    card_path = SAMPLES_DIR / f"eval_strategy_card_{vertical_choice}.json"
                    if not card_path.exists():
                        card_path = SAMPLES_DIR / "eval_strategy_card.json"
                    with open(card_path, "r", encoding="utf-8") as f:
                        raw = json.load(f)
                    card, _ = _safe_load_strategy_card(raw, str(card_path))
                    asset_pool = corp.get("asset_var") or {}
                    n_gen = st.session_state.get(f"{K}n_gen", 12)
                    vs = generate_ofaat_variants(card.card_id, hooks, sell_points_for_gen, ctas, n=n_gen, asset_pool=asset_pool)
                    st.session_state[f"{K}generated_variants"] = vs
                    st.session_state[f"{K}use_generated"] = True
                    st.success(f"已生成 {len(vs)} 个变体")
                    st.rerun()

    variants_arg = st.session_state.get(f"{K}generated_variants") if st.session_state.get(f"{K}use_generated") else None
    mb_selected = st.session_state.get(f"{K}filter_mb", mb_opts[0])
    data = load_mock_data(variants=variants_arg, vertical_override=vertical_choice, motivation_bucket_override=mb_selected)

    if data is None:
        st.error("加载数据失败")
        with st.expander("错误详情"):
            st.code(st.session_state.get(f"{K}load_trace", ""), language="text")
        return

    card = data["card"]
    metrics = data["metrics"]
    variants = data["variants"]
    vert = data.get("vertical", getattr(card, "vertical", "casual_game") or "casual_game")

    st.markdown('<span id="sec-0"></span>', unsafe_allow_html=True)
    summary = compute_decision_summary(data)
    _render_decision_summary_card(summary)

    st.caption("Analysis Sections · 结果解释")
    st.markdown('<span id="sec-1"></span>', unsafe_allow_html=True)
    st.subheader("1️⃣ 结构卡片摘要")
    cols = st.columns(6)
    with cols[0]: st.metric("场景+动机", getattr(card, "motivation_bucket", "-") or "消消乐·通勤碎片·连击爽感")
    with cols[1]: st.metric("why_you_bucket", getattr(card, "why_you_label", "") or getattr(card, "why_you_bucket", "-"))
    with cols[2]: st.metric("why_now_trigger", getattr(card, "why_now_trigger", "-"))
    with cols[3]: st.metric("人群", (getattr(card, "segment", "") or "")[:18] or "-")
    with cols[4]: st.metric("行业", "休闲游戏" if vert == "casual_game" else "电商")
    with cols[5]: st.metric("投放目标", getattr(card, "objective", "-"))
    st.caption(f"国家/OS: {getattr(card,'country','') or '-'} / {getattr(card,'os','') or '-'}")
    if getattr(card, "root_cause_gap", ""):
        st.info(card.root_cause_gap)

    st.markdown('<span id="sec-2"></span>', unsafe_allow_html=True)
    st.subheader("2️⃣ 实验对照表")
    st.caption(f"💡 {OFAAT_FULL} — {OFAAT_TOOLTIP}")
    var_map = {v.variant_id: v for v in variants}
    explore_by_os = {"iOS": data["explore_ios"], "Android": data["explore_android"]}
    scores_by_row = data.get("variant_scores_by_row", {})
    rows = []
    for m in metrics:
        v = var_map.get(m.variant_id)
        exp = explore_by_os.get(m.os)
        status = exp.variant_details.get(m.variant_id, "-") if exp else "-"
        score_val = scores_by_row.get((m.variant_id, m.os), 0.0)
        delta = (getattr(v, "delta_desc", "") or "—")[:45]
        mb_val = getattr(card, "motivation_bucket", "") or getattr(v, "motivation_bucket", "") or "-"
        row = {"变体ID": m.variant_id, "基线": "✓" if m.baseline else "", "OS": m.os, "分数": f"{score_val:.1f}", "Hook": v.hook_type if v else "-", "场景+动机": mb_val, "why_now_trigger": getattr(v, "why_now_expression", "") or "-", "CTA": v.cta_type if v else "-", "曝光": f"{m.impressions:,}", "安装": m.installs, "花费": f"${m.spend:,.0f}", "千次展示安装(IPM)": f"{m.ipm:.1f}", "单次安装成本(CPI)": f"${m.cpi:.2f}", "早期回报": f"{m.early_roas:.2%}", "门禁": status}
        if vert == "ecommerce":
            row["退款风险"] = f"{getattr(m, 'refund_risk', 0):.2%}"
        rows.append(row)
    st.dataframe(rows, hide_index=True)

    st.markdown('<span id="sec-3"></span>', unsafe_allow_html=True)
    _render_gate_section(data, metrics)

    st.markdown('<span id="sec-4"></span>', unsafe_allow_html=True)
    _render_element_scores_section(data)

    st.markdown('<span id="sec-5"></span>', unsafe_allow_html=True)
    _render_suggestions_section(data)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"运行错误: {e}")
        with st.expander("错误详情"):
            st.code(traceback.format_exc(), language="text")
