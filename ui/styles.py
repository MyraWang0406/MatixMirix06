"""全局样式：产品级蓝色主题、顶栏、决策结论、筛选区 Tag"""


def get_global_styles() -> str:
    return """
<style>
/* ===== 隐藏 Streamlit 工具条 ===== */
[data-testid="stToolbar"], [data-testid="stAppToolbar"],
[data-testid="stDeployButton"], [data-testid="stHeaderToolbar"],
header[data-testid="stHeader"], .stDeployButton { display: none !important; }
div[data-testid="stToolbar"] { display: none !important; }

/* ===== 留白与布局：蓝色模块铺满主内容区全宽 ===== */
.main, .main > div, .main [data-testid="stVerticalBlock"] { max-width: none !important; width: 100% !important; }
.main .block-container { padding: 1rem !important; max-width: none !important; width: 100% !important; margin: 0 !important; overflow: visible !important; }
.stApp > header { padding-top: 0 !important; }
[data-testid="stVerticalBlock"] > div { gap: 0.5rem !important; }
.main .block-container > div:first-of-type [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; }
/* ===== 按钮不换行，铺开，右边留白 ===== */
.stButtons { flex-wrap: nowrap !important; white-space: nowrap !important; }
.stButtons button, button { white-space: nowrap !important; }
.stButton { flex-shrink: 0 !important; }

/* ===== 产品级 Banner Header ===== */
#ds-banner {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 1rem;
    min-height: 130px;
    padding: 1.25rem 1.5rem;
    margin: 0 0 1rem 0;
    background: linear-gradient(90deg, #1E40AF 0%, #2563EB 55%, #3B82F6 100%);
    border-radius: 18px;
    box-shadow: 0 8px 24px rgba(15,23,42,0.18);
    position: relative;
    box-sizing: border-box;
}
#ds-banner .ds-banner-icon {
    width: 52px;
    height: 52px;
    min-width: 52px;
    border-radius: 14px;
    background: rgba(255,255,255,0.2);
    backdrop-filter: blur(8px);
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.5rem;
}
#ds-banner .ds-banner-titles {
    flex: 1;
    min-width: 0;
}
#ds-banner .ds-banner-title {
    color: #fff;
    font-size: 30px;
    font-weight: 800;
    line-height: 1.2;
    margin: 0;
    letter-spacing: -0.02em;
}
#ds-banner .ds-banner-subtitle {
    color: rgba(255,255,255,0.75);
    font-size: 15px;
    margin-top: 0.5cm;
}
#ds-banner .ds-banner-actions {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    flex-wrap: wrap;
    flex-shrink: 0;
}
#ds-banner .ds-banner-capsule {
    padding: 0.5rem 1rem;
    border-radius: 999px;
    background: rgba(255,255,255,0.15);
    border: 1px solid rgba(255,255,255,0.6);
    color: #fff;
    font-size: 0.9rem;
    font-weight: 500;
    cursor: pointer;
    white-space: nowrap;
    transition: background 0.2s, border-color 0.2s;
}
#ds-banner .ds-banner-capsule:hover {
    background: rgba(255,255,255,0.3);
    border-color: rgba(255,255,255,0.9);
}
#ds-banner .ds-banner-footer {
    position: absolute;
    bottom: 0.75rem;
    right: 1.5rem;
    font-size: 12px;
    color: rgba(255,255,255,0.7);
}
/* Streamlit 按钮叠加在 banner 右侧，确保帮助模块不被裁切 */
div:has(#ds-banner) { overflow: visible !important; }
div:has(#ds-banner) + div { overflow: visible !important; min-height: 0 !important; }
div:has(#ds-banner) + div [data-testid="stHorizontalBlock"] { margin-top: -6.5rem !important; position: relative; z-index: 5; background: transparent !important; justify-content: flex-end !important; gap: 0.35rem !important; }
div:has(#ds-banner) + div [data-testid="column"] { background: transparent !important; }

/* ===== 联系作者 ===== */
.contact-footer { position: fixed; bottom: 0; right: 0; background: #1a1a1a; color: #fff; padding: 0.35rem 0.7rem; font-size: 0.8rem; border-radius: 8px 0 0 0; z-index: 999; }
.contact-footer a { color: #fff; text-decoration: none; }

/* ===== 筛选区 multiselect tag：不截断，铺开显示 ===== */
[data-testid="stMultiSelect"] [data-baseweb="tag"],
.stMultiSelect [data-baseweb="tag"] {
  background: #E0E7FF !important; color: #2563EB !important; border-color: #93C5FD !important;
  max-width: none !important; min-width: fit-content !important; overflow: visible !important;
}
[data-testid="stMultiSelect"] [data-baseweb="tag"] span,
.stMultiSelect [data-baseweb="tag"] span {
  white-space: nowrap !important; overflow: visible !important; text-overflow: clip !important; max-width: none !important;
}
[data-testid="stMultiSelect"] [data-baseweb="tag"]:hover { background: #C7D2FE !important; }
[data-testid="stMultiSelect"] button[aria-label="Remove"] { color: #2563EB !important; }
[data-testid="stMultiSelect"] > div, [data-testid="stMultiSelect"] [data-baseweb="input"] { overflow: visible !important; }
/* 主 CTA（生成并评测）更大：位于筛选区 expander 内 */
.stExpander button[kind="primary"] { padding: 0.5rem 1.2rem !important; font-size: 1rem !important; font-weight: 600 !important; }

/* ===== Decision Summary：重（王）一眼看到结论/原因/下一步 ===== */
.decision-summary-hero {
    padding: 1.2rem 1.5rem;
    margin: 1rem 0 1.5rem 0;
    border-radius: 10px;
    border-left: 8px solid #2563EB;
    background: #fff !important;
    box-shadow: 0 4px 12px rgba(37,99,235,0.12);
}
.decision-summary-hero.status-pass { border-left-color: #2563EB; background: #F0F9FF !important; }
.decision-summary-hero.status-fail { border-left-color: #DC2626; background: #FEF2F2 !important; }
.decision-summary-hero.status-warn { border-left-color: #2563EB; background: #FFFBEB !important; }
.decision-summary-hero .summary-label { font-weight: 700; margin-bottom: 0.5rem; font-size: 0.85rem; color: #1E3A8A; letter-spacing: 0.03em; }
.decision-summary-hero .summary-status { font-size: 1.35rem !important; font-weight: 700 !important; margin: 0.6rem 0; color: #1E293B; line-height: 1.4; }
.decision-summary-hero .summary-row { margin: 0.35rem 0; font-size: 0.95rem; color: #475569; }
.summary-label { font-weight: 600; margin-bottom: 0.4rem; font-size: 0.9rem; color: #1E3A8A; }
.summary-status { font-size: 1.1rem; font-weight: 600; margin: 0.5rem 0; color: #1E293B; }
.summary-row { margin: 0.25rem 0; font-size: 0.9rem; color: #475569; }
.decision-summary-hero .ds-summary-btns button { background: #f1f5f9 !important; color: #475569 !important; border: 1px solid #e2e8f0 !important; }
.decision-summary-hero .ds-summary-btns button:hover { background: #e2e8f0 !important; }

/* ===== 主按钮 ===== */
button[kind="primary"] { background-color: #2563EB !important; color: #fff !important; border: none !important; }
button[kind="secondary"] { background: #f1f5f9 !important; color: #475569 !important; border: 1px solid #e2e8f0 !important; }

/* ===== 电梯导航 ===== */
.elevator-title { font-weight: 600; font-size: 0.9rem; color: #1E3A8A; }
.elevator-link { display: block; padding: 0.3rem 0.5rem; font-size: 0.85rem; color: #475569; text-decoration: none; border-radius: 6px; }
.elevator-link:hover { background: #EFF6FF; color: #2563EB; }

/* ===== 表格 ===== */
[data-testid="stDataFrame"], .stDataFrame { overflow-x: auto !important; max-width: 100%; }
[data-testid="stMetric"] { font-size: 1rem !important; }
[data-testid="stMetric"] label { font-size: 0.85rem !important; }

@media (max-width: 768px) {
    .main .block-container { padding: 0.5rem !important; max-width: 100% !important; }
    #ds-banner { flex-wrap: wrap !important; }
}
</style>
"""
