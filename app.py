
def render_stage_popup_html(title: str, body: str, note: str = ""):
    """중앙 스테이지 클리어 팝업(HTML 오버레이)."""
    note_html = f'<div class="stage-popup-note">{html.escape(note)}</div>' if note else ""
    html_block = textwrap.dedent(f"""
    <div class="stage-popup-overlay">
      <div class="stage-popup-box">
        <div class="stage-popup-title">{html.escape(title)}</div>
        <div class="stage-popup-body">{html.escape(body)}</div>
        {note_html}
      </div>
    </div>
    """).strip()
    st.markdown(html_block, unsafe_allow_html=True)

import streamlit as st
from datetime import datetime
from pathlib import Path
import csv
import io
import time
import uuid
import base64
import pandas as pd
import numpy as np
import textwrap
try:
    from streamlit.errors import StreamlitInvalidHeightError
except Exception:
    StreamlitInvalidHeightError = Exception
import streamlit.components.v1 as components
import os
import re
import difflib
import html

# =========================================================
# 1) 페이지 설정 / 스타일
# =========================================================
st.set_page_config(page_title="2026 Compliance Adventure", layout="wide")

st.markdown("""
<style>
.stApp {
    background-color: #0E1117;
    color: #EAEAEA;
}
.block-container, [data-testid="stMainBlockContainer"] {
    max-width: 1280px;
    margin: 0 auto;
    padding-top: 6.8rem !important;
    padding-bottom: 2.4rem !important;
    padding-left: 2.1rem !important;
    padding-right: 2.1rem !important;
}
@media (max-width: 900px) {
    .block-container, [data-testid="stMainBlockContainer"] {
        padding-top: 3.2rem !important;
        padding-left: 0.9rem !important;
        padding-right: 0.9rem !important;
    }
}

/* 전체 가독성(다크 배경) */
html, body, [data-testid="stAppViewContainer"], [data-testid="stMainBlockContainer"] {
    color: #F4F7FF !important;
}
h1, h2, h3, h4, h5, h6, p, li {
    color: #F4F7FF !important;
}
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] span {
    color: #F4F7FF !important;
}
label, .stCaption, small {
    color: #DDE6F7 !important;
}

/* 퀴즈 선택지 / 입력창 가독성 */
div[role="radiogroup"] label,
div[role="radiogroup"] label * {
    color: #F7FAFF !important;
}
[data-testid="stRadio"] > label {
    color: #EAF1FF !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
}
div[role="radiogroup"] > label {
    background: #151D29;
    border: 1px solid #2D3A50;
    border-radius: 12px;
    padding: 10px 12px;
    margin: 0 0 8px 0;
    line-height: 1.45;
}
div[role="radiogroup"] > label:hover {
    border-color: #3F5C86;
    background: #182233;
}
[data-testid="stTextArea"] textarea,
[data-testid="stTextInput"] input {
    background: #161A22 !important;
    color: #F7FAFF !important;
    border: 1px solid #334158 !important;
}
[data-testid="stTextArea"] textarea::placeholder,
[data-testid="stTextInput"] input::placeholder {
    color: #AEBBD0 !important;
    opacity: 1 !important;
}

/* 버튼 */
div.stButton > button:first-child {
    background-color: #00C853 !important;
    color: white !important;
    border-radius: 12px !important;
    border: none !important;
    font-weight: 700 !important;
    min-height: 44px !important;
}
div.stButton > button:first-child:hover {
    filter: brightness(1.05);
}

/* 카드 */
.card {
    background: #161A22;
    border: 1px solid #2B3140;
    border-radius: 14px;
    padding: 14px 16px;
    margin-bottom: 10px;
}
.card-title {
    font-weight: 700;
    margin-bottom: 6px;
}

/* 미션 헤더 */
.mission-header {
    background: linear-gradient(135deg, #17202B, #11151C);
    border: 1px solid #2A3140;
    border-left: 6px solid #00C853;
    border-radius: 14px;
    padding: 14px 16px;
    margin-bottom: 10px;
}

/* 브리핑 카드 */
.brief-box {
    background: #151A23;
    border: 1px solid #2A3140;
    border-radius: 12px;
    padding: 12px 14px;
    min-height: 180px;
}
.brief-title {
    font-weight: 800;
    margin-bottom: 8px;
}
.brief-chip {
    display: inline-block;
    background: #243043;
    color: #D8E6FF;
    border-radius: 999px;
    padding: 4px 10px;
    font-size: 0.82rem;
    margin-right: 6px;
    margin-bottom: 6px;
}

/* 맵 전환 페이드 효과 */
@keyframes mapFadeIn {
    0%   { opacity: 0; transform: scale(0.995); }
    100% { opacity: 1; transform: scale(1); }
}
.map-fade-wrap {
    width: 100%;
    max-width: 1060px;
    margin: 0 auto 6px auto;
}
.map-fade-img {
    width: 100%;
    height: auto;
    border-radius: 12px;
    animation: mapFadeIn 0.28s ease-out;
    display: block;
}

/* 대시보드 카드 */
.dash-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0,1fr));
    gap: 10px;
    margin: 8px 0 12px 0;
}
.dash-card {
    background: linear-gradient(135deg, #141B24, #10151D);
    border: 1px solid #2B3140;
    border-radius: 14px;
    padding: 12px 14px;
}
.dash-card .label {
    font-size: 0.8rem;
    color: #B7C4D8;
    margin-bottom: 4px;
}
.dash-card .value {
    font-size: 1.15rem;
    font-weight: 800;
    color: #F5F7FA;
}
.rank-card {
    background: #131922;
    border: 1px solid #2B3140;
    border-radius: 12px;
    padding: 10px 12px;
    margin-bottom: 8px;
}
.rank-title {
    font-weight: 700;
    margin-bottom: 6px;
}
.rank-meta {
    color: #B7C4D8;
    font-size: 0.82rem;
    margin-top: 4px;
}
.rank-bar {
    width: 100%;
    height: 8px;
    border-radius: 999px;
    background: #202938;
    overflow: hidden;
}
.rank-fill {
    height: 100%;
    background: linear-gradient(90deg, #00C853, #55EFC4);
}
.admin-lock {
    background: linear-gradient(135deg, #1E1A10, #17120B);
    border: 1px solid #7A5C21;
    border-radius: 14px;
    padding: 14px;
    margin-bottom: 10px;
}

/* 퀴즈/브리핑 레이아웃 여백 */
.quiz-question-box {
    background: #111824;
    border: 1px solid #2A3344;
    border-radius: 14px;
    padding: 14px 16px;
    margin-bottom: 10px;
}
.quiz-question-kicker {
    color: #9FB2D4;
    font-size: 0.85rem;
    font-weight: 700;
    margin-bottom: 4px;
}
.quiz-question-title {
    color: #F8FBFF;
    font-size: 1.95rem;
    font-weight: 800;
    line-height: 1.22;
    letter-spacing: -0.01em;
}
.quiz-help-text {
    color: #C6D5EE;
    font-size: 0.95rem;
    margin-bottom: 8px;
}
.quiz-left-image-wrap {
    background: #121826;
    border: 1px solid #2A3344;
    border-radius: 14px;
    padding: 10px;
    margin-bottom: 10px;
}
.quiz-left-caption {
    color: #D7E4FB;
    text-align: center;
    margin-top: 6px;
    font-weight: 600;
}
.quiz-side-tip {
    line-height: 1.55;
}
.brief-actions-wrap {
    margin-top: 6px;
}
.stTextArea textarea {
    font-size: 0.98rem !important;
    line-height: 1.5 !important;
}
@media (max-width: 1200px) {
    .quiz-question-title {
        font-size: 1.65rem;
    }
}
@media (max-width: 900px) {
    .quiz-question-title {
        font-size: 1.25rem;
        line-height: 1.3;
    }
    div[role="radiogroup"] > label {
        padding: 8px 10px;
    }
}

/* 직원 확인 모달용 읽기 전용 정보 박스 (검은 disabled input 대체) */
.modal-readonly-field {
    margin-top: 2px;
}
.modal-readonly-label {
    font-size: 0.82rem;
    color: #95A4BF !important;
    font-weight: 700;
    margin: 0 0 6px 2px;
}
.modal-readonly-value {
    background: #F6F8FC;
    color: #1A2433 !important;
    border: 1px solid #D5DEEC;
    border-radius: 10px;
    padding: 10px 12px;
    min-height: 42px;
    display: flex;
    align-items: center;
    font-weight: 600;
    line-height: 1.25;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.7);
}



/* 기관별 누적 점수 미니 카드 (인트로) */
.org-mini-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 10px;
    margin: 8px 0 4px 0;
}
.org-mini-card {
    background: linear-gradient(135deg, #121A26, #0F1622);
    border: 1px solid #263348;
    border-radius: 12px;
    padding: 10px 12px;
}
.org-mini-title {
    color: #CFE0FF;
    font-size: 0.86rem;
    font-weight: 700;
    margin-bottom: 4px;
    line-height: 1.25;
}
.org-mini-score {
    color: #F7FBFF;
    font-size: 1.15rem;
    font-weight: 800;
}
.org-mini-meta {
    color: #AFC2E4;
    font-size: 0.78rem;
    margin-top: 2px;
}

/* 다이얼로그(직원 정보 확인) 가독성 보정 */
div[data-testid="stDialog"] [role="dialog"] {
    background: #FFFFFF !important;
    color: #172233 !important;
}
div[data-testid="stDialog"] h1,
div[data-testid="stDialog"] h2,
div[data-testid="stDialog"] h3,
div[data-testid="stDialog"] h4,
div[data-testid="stDialog"] label,
div[data-testid="stDialog"] p,
div[data-testid="stDialog"] span,
div[data-testid="stDialog"] div,
div[data-testid="stDialog"] small {
    color: #172233;
}
div[data-testid="stDialog"] [data-testid="stMarkdownContainer"] * {
    color: #172233 !important;
}
div[data-testid="stDialog"] [data-testid="stCaptionContainer"] * {
    color: #4A5A74 !important;
}
div[data-testid="stDialog"] [data-testid="stDataFrame"] * {
    color: #172233 !important;
}
div[data-testid="stDialog"] [data-testid="stSelectbox"] > label,
div[data-testid="stDialog"] [data-testid="stTextInput"] > label {
    color: #42526B !important;
    font-weight: 700 !important;
}
div[data-testid="stDialog"] [data-testid="stDialogHeader"] * {
    color: #172233 !important;
}
div[data-testid="stDialog"] button[kind="header"] svg {
    color: #172233 !important;
}

/* 인트로 참가자 확인(메인화면) 읽기 전용 정보 카드 */
.confirm-readonly-field {
    margin-top: 2px;
}
.confirm-readonly-label {
    font-size: 0.82rem;
    color: #B8C7E2 !important;
    font-weight: 700;
    margin: 0 0 6px 2px;
}
.confirm-readonly-value {
    background: #F6F8FC;
    color: #1A2433 !important;
    border: 1px solid #D5DEEC;
    border-radius: 10px;
    padding: 10px 12px;
    min-height: 42px;
    display: flex;
    align-items: center;
    font-weight: 700;
    line-height: 1.25;
}

/* 퀴즈 하단 네비게이션 */
.quiz-nav-wrap {
    margin-top: 14px;
    padding-top: 10px;
    border-top: 1px solid #243044;
}
.quiz-nav-hint {
    color: #AFC3E6;
    font-size: 0.84rem;
    margin-bottom: 8px;
}


/* 중앙 팝업 오버레이 (스테이지 클리어 안내) */
.stage-popup-overlay{
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.55);
    z-index: 9999;
    display: flex;
    align-items: center;
    justify-content: center;
}
.stage-popup-box{
    background: #F7F9FF;
    color: #172233;
    width: min(560px, 92vw);
    border-radius: 16px;
    padding: 18px 20px;
    border: 1px solid #D7E2FF;
    box-shadow: 0 18px 60px rgba(0,0,0,0.35);
}
.stage-popup-title{
    font-size: 1.05rem;
    font-weight: 900;
    margin-bottom: 6px;
}
.stage-popup-body{
    font-size: 0.98rem;
    line-height: 1.55;
    opacity: 0.95;
}
.stage-popup-note{
    margin-top: 10px;
    font-size: 0.88rem;
    opacity: 0.75;
}
</style>
""", unsafe_allow_html=True)



# =========================================================
# 공통 안전 UI 래퍼 (버전 차이/빈 데이터 방어)
# =========================================================
def safe_dataframe(data, **kwargs):
    """
    Streamlit 버전 차이(특히 height=None)로 인한 예외를 방지하는 래퍼.
    - height=None이면 height 인자를 아예 전달하지 않음
    - 잘못된 높이값이면 자동 보정
    - 데이터가 None이면 빈 안내 표시
    """
    if data is None:
        st.info("표시할 데이터가 없습니다.")
        return

    local_kwargs = dict(kwargs)
    height = local_kwargs.pop("height", "__MISSING__")

    # DataFrame 이외 입력도 허용 (list/dict 등)
    df_obj = data
    try:
        if isinstance(data, pd.DataFrame):
            df_obj = data
        else:
            df_obj = pd.DataFrame(data)
    except Exception:
        df_obj = data

    try:
        if height == "__MISSING__" or height is None:
            return st.dataframe(df_obj, **local_kwargs)
        # Streamlit 일부 버전은 int/"auto"만 허용
        if isinstance(height, (int, float)):
            height = int(height)
            if height < 1:
                height = 1
            return st.dataframe(df_obj, height=height, **local_kwargs)
        if isinstance(height, str) and height.lower() == "auto":
            return st.dataframe(df_obj, height="auto", **local_kwargs)
        # 그 외 값은 생략
        return st.dataframe(df_obj, **local_kwargs)
    except StreamlitInvalidHeightError:
        # height 문제면 height를 제거하고 재시도
        try:
            return st.dataframe(df_obj, **local_kwargs)
        except Exception:
            # 마지막 fallback
            if isinstance(df_obj, pd.DataFrame):
                st.write(df_obj)
            else:
                st.write(data)
    except Exception:
        if isinstance(df_obj, pd.DataFrame):
            st.write(df_obj)
        else:
            st.write(data)


def render_top_spacer():
    st.markdown("<div style='height:56px;'></div>", unsafe_allow_html=True)


def safe_bar_chart(data, **kwargs):
    """
    차트 데이터가 비어 있거나 숫자형 컬럼이 없을 때 앱이 죽지 않도록 방어.
    """
    if data is None:
        st.info("차트 데이터가 없습니다.")
        return
    try:
        chart_df = data.copy() if isinstance(data, pd.DataFrame) else pd.DataFrame(data)
    except Exception:
        st.info("차트 데이터를 불러오지 못했습니다.")
        return

    if chart_df is None or len(chart_df) == 0:
        st.info("차트 데이터가 없습니다.")
        return

    # 숫자형 컬럼만 사용
    try:
        numeric_cols = chart_df.select_dtypes(include="number").columns.tolist()
        if not numeric_cols:
            # 숫자형 변환 시도
            for c in chart_df.columns:
                chart_df[c] = pd.to_numeric(chart_df[c], errors="ignore")
            numeric_cols = chart_df.select_dtypes(include="number").columns.tolist()
        if not numeric_cols:
            st.info("차트로 표시할 숫자형 데이터가 없습니다.")
            return
        chart_df = chart_df[numeric_cols]
    except Exception:
        pass

    try:
        st.bar_chart(chart_df, **kwargs)
    except Exception:
        # 마지막 fallback: 원본 표로 표시
        st.info("차트를 표시하지 못해 표로 대신 보여드립니다.")
        safe_dataframe(chart_df, use_container_width=True)


# =========================================================
# 2) 파일 경로 / 에셋
#    (이미지/사운드 모두 app.py와 같은 폴더에 있다고 가정)
# =========================================================
BASE_DIR = Path(__file__).parent if "__file__" in globals() else Path.cwd()
ASSET_DIR = BASE_DIR
LOG_FILE = BASE_DIR / "compliance_training_log.csv"
LOG_FIELDNAMES = [
    "timestamp",
    "training_attempt_id",
    "attempt_round",
    "employee_no",
    "name",
    "organization",
    "department",
    "mission_key",
    "mission_title",
    "question_index",
    "question_code",
    "question_type",
    "question",
    "selected_or_text",
    "is_correct",
    "awarded_score",
    "max_score",
    "attempt_no_for_mission",
]

MAP_STAGE_IMAGES = {
    0: ASSET_DIR / "world_map_0.png",
    1: ASSET_DIR / "world_map_1.png",
    2: ASSET_DIR / "world_map_2.png",
    3: ASSET_DIR / "world_map_3.png",
}
DEFAULT_MAP_IMAGE = ASSET_DIR / "world_map.png"  # 선택 (fallback)
MASTER_IMAGE = ASSET_DIR / "master.png"
ENDING_IMAGE_CANDIDATE_NAMES = [
    "ending_final.png", "final_stage.png", "ending.png", "final.png",
    "completion_final.png", "guardian_final.png"
]

# --- 관리자 통계/채점 기준 ---
TEXT_CORRECT_THRESHOLD = 0.7  # 주관식 점수율 70% 이상이면 '정답'으로 집계

# --- 사운드 / 아이콘 자원 ---
SFX = {
    "correct": BASE_DIR / "sfx_correct.mp3",
    "wrong": BASE_DIR / "sfx_wrong.mp3",
    "conquer": BASE_DIR / "sfx_conquer.mp3",
    "final": BASE_DIR / "sfx_final.mp3",
}

THEME_ICONS = {
    "subcontracting": "🚜",
    "security": "🔐",
    "fairtrade": "🛡️",
}


# 스테이지 팝업에 사용할 표시명(요청: Valley/Fortress/Castle)
STAGE_DISPLAY_NAMES = {
    "subcontracting": "Valley of Subcontracting",
    "security": "Fortress of Information Security",
    "fairtrade": "Castle of Fair Trade",
}


EMPLOYEE_MASTER_CANDIDATE_NAMES = [
    "employee_master.xlsx", "employee_master.csv",
    "employee_list.xlsx", "employee_list.csv",
    "employees.xlsx", "employees.csv",
    "직원명단.xlsx", "직원명단.csv",
    "사번명단.xlsx", "사번명단.csv",
    "임직원명단.xlsx", "임직원명단.csv",
]

EMPLOYEE_COL_ALIASES = {
    "employee_no": ["employee_no", "emp_no", "empid", "employeeid", "employeenumber", "사번", "직원번호", "사원번호", "임직원번호", "직원코드", "사번코드"],
    "name": ["name", "employee_name", "fullname", "성명", "이름", "직원명", "사원명"],
    "organization": ["organization", "org", "department", "dept", "소속", "소속기관", "기관", "조직", "본부", "부서"],
}

# 전체 과정 공통 BGM (권장 파일명)
GLOBAL_BGM_CANDIDATE_NAMES = [
    "2026 Compliance Adventure_bgm.mp3",  # 사용자 지정 최종 파일명
    "2026_Compliance_Adventure_bgm.mp3",
    "bgm_main.mp3",
]

# 구버전 단계별 파일명도 fallback 지원 (기존 운영 호환)
BGM = {
    "intro": BASE_DIR / "bgm_intro.mp3",
    "map": BASE_DIR / "bgm_map.mp3",
    "subcontracting": BASE_DIR / "bgm_subcontracting.mp3",
    "security": BASE_DIR / "bgm_security.mp3",
    "fairtrade": BASE_DIR / "bgm_fairtrade.mp3",
    "ending": BASE_DIR / "bgm_final.mp3",
}

ADMIN_PASSWORD = os.environ.get("COMPLIANCE_ADMIN_PASSWORD", "admin2026")

# =========================================================
# 3) 콘텐츠 데이터 (브리핑 + 퀴즈)
#    테마당: 4지선다 2문항 + 주관식 1문항
# =========================================================
SCENARIO_ORDER = ["subcontracting", "security", "fairtrade"]

SCENARIOS = {'subcontracting': {'title': '🚜 하도급의 계곡',
                    'briefing': {'title': '하도급 실무 핵심 원칙 브리핑',
                                 'summary': '하도급 실무에서는 “착공 전 서면 발급”, “대금·범위 변경 시 근거 문서화”, “감액·지연 사유의 객관적 기록”이 핵심입니다. '
                                            '하도급법상 서면 미발급, 부당감액, 대금지연은 분쟁·제재로 이어질 수 있으므로, 급한 일정일수록 계약·변경·검수 기록을 먼저 남겨야 '
                                            '합니다.',
                                 'keywords': ['하도급법', '서면발급 의무', '변경계약 문서화', '부당감액 금지'],
                                 'red_flags': ['“먼저 작업부터, 계약서는 나중에”처럼 착공 전 서면을 미루는 지시',
                                               '구두로 범위/단가를 바꾸고 메일·변경합의서 없이 진행',
                                               '품질/납기 이슈 근거 없이 일괄 감액 또는 지급 보류'],
                                 'checklist': ['착공 전 발주서/계약서(범위·단가·납기) 발급 여부 확인',
                                               '변경 발생 시 변경사유·변경금액·승인권자 기록 남기기',
                                               '검수/납품/하자 근거자료를 지급 판단 문서와 연결하기',
                                               '감액 검토 시 정당한 사유·산정근거·협의내용을 서면으로 남기기']},
                    'quiz': [{'type': 'mcq',
                              'code': 'SC-1',
                              'score': 10,
                              'question': '하도급 업무에서 착공 전 가장 먼저 확인해야 할 항목은 무엇인가요?',
                              'options': ['서면 계약(발주서 포함) 발급 여부와 핵심 조건 명시 여부',
                                          '현장 인력 배치 완료 여부',
                                          '협력사 담당자 연락처 확보 여부',
                                          '작업 속도와 긴급성'],
                              'answer': 0,
                              'choice_feedback': ['정답입니다. 하도급법 분쟁의 출발점은 서면 미발급/조건 불명확인 경우가 많습니다.',
                                                  '인력 배치는 중요하지만, 계약 근거가 먼저 정리되어야 분쟁을 줄일 수 있습니다.',
                                                  '연락체계는 보조 요소이며, 계약 조건 확정이 우선입니다.',
                                                  '긴급한 일정이라도 법적 필수 절차(서면)는 생략할 수 없습니다.'],
                              'explain': '하도급 실무의 기본은 “서면 선행”입니다. 착공 전 발주서·계약서에 작업범위, 단가, 납기, 검수 기준 등이 명시되어야 이후 '
                                         '비용/품질/납기 분쟁을 예방할 수 있습니다.',
                              'wrong_extra': '실무에서는 “급해서 먼저”라는 말이 자주 나오지만, 서면 누락은 추후 부당감액·책임공방의 핵심 쟁점이 됩니다.'},
                             {'type': 'mcq',
                              'code': 'SC-2',
                              'score': 10,
                              'question': '작업 도중 발주 범위가 늘어나 단가 조정이 필요한 상황입니다. 가장 적절한 조치는 무엇인가요?',
                              'options': ['변경 내용을 메신저로만 남기고 기존 계약대로 정산한다',
                                          '변경 범위·단가·납기를 서면(변경합의/발주서)으로 확정 후 진행한다',
                                          '협력사에 먼저 진행시키고 월말에 내부 기준으로 감액 정산한다',
                                          '구두 합의만 되면 증빙 없이도 충분하다'],
                              'answer': 1,
                              'choice_feedback': ['메신저 기록은 보조자료일 뿐, 변경계약의 핵심 증빙으로는 부족할 수 있습니다.',
                                                  '정답입니다. 변경계약은 범위·금액·납기·책임을 서면으로 정리해야 분쟁을 줄일 수 있습니다.',
                                                  '사후 감액 정산은 부당감액 분쟁으로 이어질 가능성이 높습니다.',
                                                  '구두 합의는 해석이 갈리기 쉬워 분쟁 시 입증이 어렵습니다.'],
                              'explain': '하도급 변경관리에서는 “변경 전 합의·변경 후 집행” 원칙이 안전합니다. 변경 범위와 단가를 문서화해 승인권자까지 명확히 해야 지급·검수 '
                                         '단계에서 충돌을 줄일 수 있습니다.',
                              'wrong_extra': '분쟁사례에서는 “현장 구두지시”가 있었는지, 누가 승인했는지가 핵심 쟁점이 됩니다. 문서화가 가장 강력한 예방책입니다.'},
                             {'type': 'text',
                              'code': 'SC-3',
                              'score': 10,
                              'question': '나는 협력사 정산을 검토 중인데, 검수결과나 하자 근거 없이 대금을 일괄 감액하라는 요청을 받았습니다. 이 상황에서 내가 어떻게 처리할지 짧게 작성해보세요. (원칙 + 근거 확인 + 대안 포함)',
                              'sample_answer': '정당한 사유와 객관적 근거 없이 하도급대금을 바로 감액하지 않겠습니다. 먼저 검수결과·하자 여부·산정 근거를 확인하고, 조정이 필요하면 협의 내용과 정산 기준을 서면으로 남겨 처리하겠습니다.',
                              'model_answer': '예시 답변: “하도급대금은 정당한 사유와 객관적 산정 근거 없이 일괄 감액하면 분쟁과 법 위반 소지가 있으므로 바로 감액 처리하지 않겠습니다. 우선 검수결과와 하자 귀책, 감액 산정 근거를 확인하고, 조정이 필요하면 협의 내용과 정산 기준을 서면으로 남긴 뒤 처리하겠습니다.”',
                              'rubric_keywords': {'원칙 설명': {'keywords': ['하도급대금', '감액', '정당한 사유', '부당', '일괄 감액', '바로 감액하지'], 'weight': 3, 'min_hits': 2},
                                               '근거 확인': {'keywords': ['검수', '하자', '귀책', '산정', '근거', '증빙'], 'weight': 4, 'min_hits': 2},
                                               '처리/기록 조치': {'keywords': ['협의', '서면', '기록', '문서', '정산 기준', '확인 후'], 'weight': 3, 'min_hits': 2}}}]},
 'security': {'title': '🔐 정보보안의 요새',
              'briefing': {'title': '정보보안 기본 원칙 브리핑',
                           'summary': '정보보안은 “의심 메일/링크 식별”, “비밀번호·인증정보 보호”, “사고 징후 발견 즉시 보고”가 핵심입니다. 실제 사고는 클릭 한 번으로 '
                                      '시작되는 경우가 많고, 초기 보고가 늦어질수록 개인정보 유출·업무 중단 피해가 커집니다.',
                           'keywords': ['피싱 메일', '계정정보 보호', '사고 즉시보고', '개인정보'],
                           'red_flags': ['긴급결재·택배조회 등을 빙자한 링크 클릭 유도 메일',
                                         '비밀번호·OTP·인증코드를 메신저/메일로 요청하는 행위',
                                         '이상 로그인/파일 암호화 징후를 발견했는데 개인적으로만 처리'],
                           'checklist': ['발신자 도메인·링크 주소·첨부파일 확장자(exe, zip 등) 확인',
                                         '비밀번호/인증코드는 절대 공유하지 않고 공식 시스템에서만 입력',
                                         '의심 클릭/오발송/계정이상 발견 시 즉시 보안담당·헬프데스크 보고',
                                         '초동보고에는 사고상황·즉시조치·추가점검 요청을 함께 적기']},
              'quiz': [{'type': 'mcq',
                        'code': 'IS-1',
                        'score': 10,
                        'question': '다음 중 피싱 메일 가능성이 가장 높은 징후는 무엇인가요?',
                        'options': ['회사 공지 메일에 사내 포털 링크가 포함되어 있다',
                                    '발신자 주소가 유사하지만 다른 도메인이고, 압축파일 실행을 요구한다',
                                    '회의 일정 안내 메일에 회의실 정보가 포함되어 있다',
                                    '업무 메일에 결재 문서 PDF가 첨부되어 있다'],
                        'answer': 1,
                        'choice_feedback': ['링크 자체만으로는 피싱 여부를 단정할 수 없고, 도메인·URL 검증이 필요합니다.',
                                            '정답입니다. 유사 도메인 + 실행파일/압축파일 유도는 대표적인 피싱 징후입니다.',
                                            '일반적인 업무 안내 형태로, 추가 검증 요소가 더 필요합니다.',
                                            'PDF 첨부만으로는 판단하기 어렵고 발신자/맥락 확인이 먼저입니다.'],
                        'explain': '피싱 메일은 실제 조직명을 흉내 낸 유사 도메인, 긴급한 표현, 실행형 첨부파일 요구가 자주 나타납니다. 특히 압축파일/실행파일은 악성코드 감염의 '
                                   '주요 경로입니다.',
                        'wrong_extra': '“바빠서 일단 열어보자”가 사고의 출발점이 됩니다. 의심되면 클릭 전에 보안팀 확인이 우선입니다.'},
                       {'type': 'mcq',
                        'code': 'IS-2',
                        'score': 10,
                        'question': '직원이 피싱 페이지에 계정정보를 입력한 사실을 뒤늦게 알게 되었습니다. 가장 우선해야 할 조치는?',
                        'options': ['본인 PC만 재부팅하고 아무에게도 알리지 않는다',
                                    '다음날 출근 후 천천히 비밀번호를 바꾼다',
                                    '즉시 비밀번호 변경, 접속 차단 요청, 보안담당자/헬프데스크에 사고 보고',
                                    '메일을 삭제했으니 추가 조치는 필요 없다'],
                        'answer': 2,
                        'choice_feedback': ['재부팅만으로는 계정 탈취·추가 접근을 막을 수 없습니다.',
                                            '지연 대응은 피해를 키울 수 있습니다. 즉시 조치가 중요합니다.',
                                            '정답입니다. 계정보호 조치와 사고보고를 동시에 진행해야 확산을 줄일 수 있습니다.',
                                            '삭제는 흔적 제거가 아니며, 이미 입력한 정보는 유출됐을 수 있습니다.'],
                        'explain': '계정정보 입력 사고는 “즉시 비밀번호 변경 + 보안담당 통보 + 추가 인증 점검”이 기본입니다. 초기 10~30분 대응이 피해 규모를 크게 '
                                   '좌우합니다.',
                        'wrong_extra': '실제 사고 대응에서 보고 지연은 추가 접속·권한남용을 허용해 피해를 확대시키는 원인이 됩니다.'},
                       {'type': 'text',
                        'code': 'IS-3',
                        'score': 10,
                        'question': '나는 의심 메일 링크를 클릭한 뒤 계정정보 입력 가능성을 확인했습니다. 이 상황에서 내가 즉시 해야 할 조치와 보고 방향을 짧게 작성해보세요. (상황 + 즉시 조치 + 보고/요청 포함)',
                        'sample_answer': '의심 링크 클릭으로 계정정보 노출 가능성이 있어 즉시 비밀번호를 변경하고 추가 로그인 여부를 확인하겠습니다. 동시에 보안담당자와 헬프데스크에 사고 사실을 보고하고 접속기록 점검을 요청하겠습니다.',
                        'model_answer': '예시 답변: “의심 메일 링크 클릭으로 계정정보가 노출됐을 가능성이 있어 즉시 비밀번호를 변경하고 필요한 경우 로그아웃/차단 조치를 진행하겠습니다. 이후 보안담당자와 헬프데스크에 사고 사실을 바로 보고하고, 계정 접속기록 점검과 추가 대응 안내를 요청하겠습니다.”',
                        'rubric_keywords': {'사고 상황 인지': {'keywords': ['의심', '메일', '링크', '계정', '입력', '노출'], 'weight': 2, 'min_hits': 2},
                                            '즉시 보호 조치': {'keywords': ['비밀번호', '변경', '차단', '로그아웃', 'OTP', '인증'], 'weight': 4, 'min_hits': 2},
                                            '보고/점검 요청': {'keywords': ['보고', '보안담당', '헬프데스크', '접속기록', '점검', '요청'], 'weight': 4, 'min_hits': 2}}}]},
 'fairtrade': {'title': '🛡️ 공정거래의 성',
               'briefing': {'title': '공정거래·청렴 기본 원칙 브리핑',
                            'summary': '공정거래·청렴 실무에서는 “이해관계자와의 거리 유지”, “부당한 편의·청탁 거절”, “접촉·제안 발생 시 기록 및 보고”가 핵심입니다. '
                                       '청탁금지법, 공정거래 관련 내부규정, 윤리강령 위반은 개인 문제를 넘어 회사의 평판·입찰 리스크로 이어질 수 있습니다.',
                            'keywords': ['청탁금지법', '이해충돌 예방', '금품·편의 거절', '윤리보고'],
                            'red_flags': ['협력사/거래처가 식사·상품권·편의를 반복적으로 제공',
                                          '평가/입찰 담당자에게 결과를 미리 알려달라는 요청',
                                          '지인·퇴직자 네트워크를 통한 우회 청탁 제안'],
                            'checklist': ['거래처 접촉 시 목적·참석자·제공내역을 내부기준에 따라 기록',
                                          '금품/향응/편의 제공 제안은 즉시 거절하고 상급자·윤리채널 공유',
                                          '입찰·평가 정보는 권한자 외 비공개, 문의 시 공식 절차로 안내',
                                          '모든 업체에 동일 기준으로 답변되도록 공식 질의 채널로만 접수받기']},
               'quiz': [{'type': 'mcq',
                         'code': 'FT-1',
                         'score': 10,
                         'question': '평가를 앞둔 협력사가 “작은 감사 표시”라며 상품권을 전달하려고 합니다. 가장 적절한 대응은?',
                         'options': ['금액이 작으면 받고 넘어간다',
                                     '개인적으로 거절하고 기록은 남기지 않는다',
                                     '정중히 거절하고, 회사 기준에 따라 상급자/윤리채널에 공유한다',
                                     '평가가 끝난 뒤 받겠다고 안내한다'],
                         'answer': 2,
                         'choice_feedback': ['금액과 무관하게 이해관계 상황에서는 수수가 리스크가 됩니다.',
                                             '거절은 좋지만 기록·공유가 없으면 반복 제안이나 오해를 막기 어렵습니다.',
                                             '정답입니다. 거절 + 보고(기록)가 청렴 리스크 관리의 기본입니다.',
                                             '평가 이후라도 이해관계가 남아 있을 수 있어 부적절합니다.'],
                         'explain': '이해관계자 금품·편의 제공은 금액보다 상황과 직무 관련성이 중요합니다. 실무에서는 수수 자체를 피하고, 제안 사실을 기록/공유해 재발과 오해를 '
                                    '예방해야 합니다.',
                         'wrong_extra': '분쟁·감사 시에는 “받았는지”뿐 아니라 “제안이 있었을 때 회사가 어떻게 대응했는지”도 중요하게 확인됩니다.'},
                        {'type': 'mcq',
                         'code': 'FT-2',
                         'score': 10,
                         'question': '입찰 준비 중 거래처가 “평가 기준과 경쟁사 상황을 조금만 알려달라”고 요청했습니다. 가장 적절한 답변은?',
                         'options': ['관계 유지를 위해 구두로 일부 힌트만 준다',
                                     '공식 공지된 범위만 안내하고, 추가 문의는 공식 절차로 요청하도록 한다',
                                     '비공식 메신저로 평가 일정만 알려준다',
                                     '퇴근 후 사적으로 만나 설명한다'],
                         'answer': 1,
                         'choice_feedback': ['구두 힌트도 정보 비대칭/공정성 훼손 문제가 발생할 수 있습니다.',
                                             '정답입니다. 공개 가능한 정보만 동일하게 제공하고, 나머지는 공식 채널로 통제해야 합니다.',
                                             '비공식 전달은 기록이 남지 않아 감사 대응이 어렵습니다.',
                                             '사적 접촉은 오해와 청탁 리스크를 키웁니다.'],
                         'explain': '입찰·평가 정보는 공정성 확보가 핵심입니다. 모든 거래처에 동일한 기준으로 공개하고, 비공개 정보는 공유하지 않는 것이 원칙입니다.',
                         'wrong_extra': '공정거래·청렴 이슈는 실제 정보 유출뿐 아니라 “특정 업체만 더 알았는가”라는 절차적 공정성 문제로도 확산됩니다.'},
                        {'type': 'text',
                         'code': 'FT-3',
                         'score': 10,
                         'question': '나는 입찰 준비 중 거래처로부터 평가 기준 세부내용이나 경쟁사 관련 정보를 알려 달라는 요청을 받았습니다. 이 상황에서 내가 원칙을 지키며 어떻게 대응할지 짧게 작성해보세요. (공정성 원칙 + 거절 + 공식 채널 안내 포함)',
                         'sample_answer': '평가 관련 정보는 공정성을 위해 공개된 범위에서만 안내하겠습니다. 추가 문의는 공식 질의 채널로 접수하도록 안내하고 동일 기준으로 회신되도록 하겠습니다.',
                         'model_answer': '예시 답변: “입찰/평가 정보는 공정성과 동일기회 원칙에 따라 공개된 내용만 안내하겠습니다. 비공개 정보나 경쟁사 관련 내용은 제공하지 않고, 추가 문의는 공식 질의 채널로 접수하도록 안내해 모든 업체에 동일 기준으로 회신되도록 처리하겠습니다.”',
                         'rubric_keywords': {'공정성 원칙': {'keywords': ['공정', '동일', '공개', '원칙', '기준'], 'weight': 3, 'min_hits': 2},
                                             '비공개 정보 거절': {'keywords': ['비공개', '경쟁사', '제공하지', '어렵', '불가', '거절'], 'weight': 4, 'min_hits': 2},
                                             '공식 채널 안내': {'keywords': ['공식', '질의', '채널', '접수', '회신', '동일 기준'], 'weight': 3, 'min_hits': 2}}}]}}

MCQ_SCORE = 10
TEXT_SCORE = 10
PARTICIPATION_SCORE = 10

# 모든 테마에 동일 배점 적용 (객관식 10점 × 6문항, 주관식 10점 × 3문항)
for _m in SCENARIOS.values():
    for _q in _m.get("quiz", []):
        _q["score"] = MCQ_SCORE if _q.get("type") == "mcq" else TEXT_SCORE

THEME_TOTAL_SCORE = sum(q.get("score", 0) for q in SCENARIOS[SCENARIO_ORDER[0]]["quiz"]) if SCENARIO_ORDER else 0
TOTAL_SCORE = sum(sum(q.get("score", 0) for q in SCENARIOS[m]["quiz"]) for m in SCENARIO_ORDER) + PARTICIPATION_SCORE

# =========================================================
# 4) 상태 관리
# =========================================================
def init_state():
    defaults = {
        "stage": "intro",  # intro -> map -> briefing -> quiz -> ending
        "user_info": {},
        "current_mission": None,
        "completed": [],
        "mission_scores": {},
        "score": 0,
        "participation_awarded": False,
        "participation_score": 0,
        "quiz_progress": {},
        "attempt_counts": {},
        "attempt_history": [],
        "training_attempt_id": "",
        "training_attempt_round": 1,
        "show_conquer_fx": False,
        "map_fx_done": False,
        "map_celebrate_until": 0.0,
        "map_celebrate_theme": None,
        "last_cleared_mission": None,
        "log_write_error": None,
        "played_final_fanfare": False,
        "admin_authed": False,
        "pending_sfx": None,
        "bgm_enabled": True,
        "audio_debug": False,
        "employee_lookup_candidates": [],
        "employee_selected_record": None,
        "employee_lookup_modal_open": False,
        "retry_offer": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def recalc_total_score():
    theme_sum = int(sum(st.session_state.mission_scores.values()))
    st.session_state.score = theme_sum + int(st.session_state.get("participation_score", 0) or 0)


def theme_max_score(m_key: str) -> int:
    return int(sum(q.get("score", 0) for q in SCENARIOS.get(m_key, {}).get("quiz", [])))


def award_participation_points_if_needed():
    if not st.session_state.get("participation_awarded", False):
        st.session_state.participation_awarded = True
        st.session_state.participation_score = PARTICIPATION_SCORE
    recalc_total_score()


def ensure_quiz_progress(m_key: str):
    if m_key not in st.session_state.quiz_progress:
        st.session_state.quiz_progress[m_key] = {
            "current_idx": 0,
            "submissions": {}
        }


def _normalize_for_similarity(text: str) -> str:
    s = str(text or "").strip().lower()
    s = re.sub(r"\s+", "", s)
    s = re.sub(r"[^0-9a-zA-Z가-힣]", "", s)
    return s


def is_near_copy_answer(answer_text: str, *examples: str, threshold: float = 0.92) -> bool:
    user = _normalize_for_similarity(answer_text)
    if not user:
        return False
    for ex in examples:
        exn = _normalize_for_similarity(ex)
        if not exn:
            continue
        if user == exn:
            return True
        ratio = difflib.SequenceMatcher(None, user, exn).ratio()
        if ratio >= threshold:
            return True
    return False


def get_text_question_sample_answer(q_data: dict) -> str:
    sample = str(q_data.get("sample_answer", "") or "").strip()
    if sample:
        return sample
    model = str(q_data.get("model_answer", "") or "").strip()
    if not model:
        return ""
    # 모델답안을 그대로 노출하지 않도록 길이 축약 + 안내 문구로 사용
    short = model[:90] + ("..." if len(model) > 90 else "")
    return short


def get_theme_status(m_key: str):
    idx = SCENARIO_ORDER.index(m_key)
    if m_key in st.session_state.completed:
        return "clear"
    if idx == 0:
        return "open"
    prev_key = SCENARIO_ORDER[idx - 1]
    return "open" if prev_key in st.session_state.completed else "locked"


def theme_score_from_submissions(m_key: str):
    ensure_quiz_progress(m_key)
    subs = st.session_state.quiz_progress[m_key]["submissions"]
    return int(sum(int(result.get("awarded_score", 0)) for result in subs.values()))



def finalize_theme_if_ready(m_key: str) -> dict:
    """테마(스테이지) 점수 확정. '정복 연출' 등 과한 효과는 사용하지 않습니다.
    반환값에는 스테이지 점수(10점 환산) 등 팝업에 필요한 값이 들어갑니다.
    """
    ensure_quiz_progress(m_key)
    subs = st.session_state.quiz_progress[m_key]["submissions"]
    total_q = len(SCENARIOS[m_key]["quiz"])
    if len(subs) != total_q:
        return {"ready": False}

    # 테마 점수 확정
    raw = int(theme_score_from_submissions(m_key))
    max_raw = int(theme_max_score(m_key)) or 1
    st.session_state.mission_scores[m_key] = raw
    recalc_total_score()

    if m_key not in st.session_state.completed:
        st.session_state.completed.append(m_key)
        st.session_state.last_cleared_mission = m_key

    # 스테이지(테마) 점수는 10점 환산으로 표시
    scaled_10 = int(round((raw / max_raw) * 10))
    scaled_10 = max(0, min(10, scaled_10))
    return {"ready": True, "raw": raw, "max_raw": max_raw, "scaled_10": scaled_10, "scaled_max": 10}
# =========================================================
# 5) 유틸 함수 (이미지 / 사운드 / 평가)
# =========================================================
def get_current_map_image():
    stage_idx = min(len(st.session_state.get("completed", [])), 3)
    path = MAP_STAGE_IMAGES.get(stage_idx)
    if path and path.exists():
        return path
    if DEFAULT_MAP_IMAGE.exists():
        return DEFAULT_MAP_IMAGE
    return None


def get_ending_image():
    for name in ENDING_IMAGE_CANDIDATE_NAMES:
        p = ASSET_DIR / name
        if p.exists():
            return p
    return None


def show_map_with_fade(map_path: Path, caption: str = None, celebrate: bool = False):
    if not map_path or not map_path.exists():
        st.warning("맵 이미지 파일을 찾을 수 없습니다.")
        return
    try:
        img_bytes = map_path.read_bytes()
        encoded = base64.b64encode(img_bytes).decode("utf-8")
        pollen_html = ""
        if celebrate:
            pollen_positions = [
                (8,18,6,0.0),(14,68,5,0.7),(22,35,7,1.2),(28,82,5,0.2),(35,12,6,0.9),
                (42,58,5,1.6),(50,28,7,0.4),(57,76,6,1.1),(64,44,5,1.9),(72,16,6,0.5),
                (79,62,7,1.4),(86,34,5,0.8),(18,50,4,1.8),(61,88,4,0.3),(74,92,4,1.5),
                (10,90,4,0.6),(90,8,4,1.0),(46,6,4,1.7)
            ]
            dots = []
            for top,left,size,delay in pollen_positions:
                dots.append(
                    f"<span class='pollen-dot' style='top:{top}%;left:{left}%;width:{size}px;height:{size}px;animation-delay:{delay}s;'></span>"
                )
            pollen_html = f"<div class='map-pollen-overlay'>{''.join(dots)}</div>"

        st.markdown(
            f"""
            <div class="map-fade-wrap{' celebrate' if celebrate else ''}">
                <img class="map-fade-img" src="data:image/png;base64,{encoded}" />
                {pollen_html}
            </div>
            """,
            unsafe_allow_html=True
        )
        if caption:
            st.caption(caption)
    except Exception:
        st.image(str(map_path), use_container_width=True)
        if caption:
            st.caption(caption)


def resolve_bgm_path(bgm_key: str) -> Path | None:
    # 1) 전체 공통 BGM 우선 사용
    for name in GLOBAL_BGM_CANDIDATE_NAMES:
        gp = BASE_DIR / name
        if gp.exists():
            return gp
    # 2) 없으면 단계별 BGM fallback
    p = BGM.get(bgm_key)
    if p and p.exists():
        return p
    return None


def _audio_component_html(audio_b64: str, *, loop: bool = False, hidden_label: str = "audio"):
    loop_attr = " loop" if loop else ""
    html = f"""
    <html>
      <body style="margin:0; padding:0; background:transparent;">
        <audio id="{hidden_label}" autoplay{loop_attr} playsinline webkit-playsinline preload="auto" style="display:none;">
          <source src="data:audio/mp3;base64,{audio_b64}" type="audio/mpeg">
        </audio>
        <script>
          (function() {{
            const a = document.getElementById("{hidden_label}");
            if (!a) return;
            a.volume = 0.65;
            const tryPlay = () => {{
              const p = a.play();
              if (p && p.catch) p.catch(() => {{}});
            }};
            // 최초 진입 시 자동재생 시도
            tryPlay();
            setTimeout(tryPlay, 120);
            setTimeout(tryPlay, 400);
            // 브라우저 자동재생 제한 시 첫 사용자 상호작용에서 재시도
            ["click", "keydown", "touchstart"].forEach((evt) => {{
              document.addEventListener(evt, tryPlay, {{ once: false, passive: true }});
            }});
          }})();
        </script>
      </body>
    </html>
    """
    components.html(html, height=0, width=0)


def queue_sfx(sfx_key: str):
    st.session_state.pending_sfx = sfx_key


def play_sfx_now(sfx_key: str):
    sfx_path = SFX.get(sfx_key)
    if not sfx_path or not sfx_path.exists():
        return
    try:
        sfx_b64 = base64.b64encode(sfx_path.read_bytes()).decode("utf-8")
        _audio_component_html(sfx_b64, loop=False, hidden_label=f"sfx_now_{sfx_key}_{int(time.time()*1000)}")
    except Exception:
        pass


def _resolve_bgm_key():
    stage = st.session_state.get("stage", "intro")
    current = st.session_state.get("current_mission")

    if stage == "intro":
        return "intro"
    if stage == "map":
        return "map"
    if stage in ("briefing", "quiz") and current in SCENARIOS:
        return current
    if stage == "ending":
        return "ending"
    return "map"


def render_audio_system():
    # 1) Background music (loop)
    if st.session_state.get("bgm_enabled", True):
        bgm_key = _resolve_bgm_key()
        bgm_path = resolve_bgm_path(bgm_key)
        if bgm_path and bgm_path.exists():
            try:
                bgm_b64 = base64.b64encode(bgm_path.read_bytes()).decode("utf-8")
                # 전체 공통 BGM 사용 시 stage 전환에도 끊김을 최소화하도록 고정 라벨 사용
                _audio_component_html(bgm_b64, loop=True, hidden_label="bgm_global")
            except Exception:
                pass

    # 2) One-shot SFX (queued to survive st.rerun)
    pending_key = st.session_state.get("pending_sfx")
    if pending_key:
        sfx_path = SFX.get(pending_key)
        if sfx_path and sfx_path.exists():
            try:
                sfx_b64 = base64.b64encode(sfx_path.read_bytes()).decode("utf-8")
                _audio_component_html(sfx_b64, loop=False, hidden_label=f"sfx_{pending_key}_{int(time.time()*1000)}")
            except Exception:
                pass
        st.session_state.pending_sfx = None


def render_audio_status_hint():
    # 패널 제거 (최종본에서 사용하지 않음)
    return

def _normalize_log_row(raw: dict) -> dict:
    raw = raw or {}
    clean = {}
    for k, v in raw.items():
        if k is None:
            continue
        key = str(k).strip()
        if key == "":
            continue
        if isinstance(v, list):
            v = " | ".join([str(x) for x in v if str(x).strip()])
        clean[key] = v

    # 스키마 호환 보정 (구버전 로그 포함)
    if "employee_no" not in clean:
        clean["employee_no"] = clean.get("emp_no", "") or clean.get("사번", "") or clean.get("직원번호", "")
    if not str(clean.get("organization", "")).strip():
        clean["organization"] = clean.get("department", "") or "미분류"
    if "department" not in clean:
        clean["department"] = clean.get("organization", "")
    if "mission_key" not in clean and "question_code" in clean:
        clean["mission_key"] = str(clean.get("question_code", "")).split("_Q")[0]
    if "question_index" not in clean or str(clean.get("question_index", "")).strip() == "":
        qc = str(clean.get("question_code", ""))
        m = re.search(r"_Q(\d+)", qc)
        clean["question_index"] = int(m.group(1)) if m else 0
    if not str(clean.get("question_code", "")).strip():
        mk = str(clean.get("mission_key", "")).strip()
        qn = str(clean.get("question_index", "")).strip()
        clean["question_code"] = f"{mk}_Q{qn}" if mk and qn else ""
    if not str(clean.get("mission_title", "")).strip():
        mk = str(clean.get("mission_key", "")).strip()
        clean["mission_title"] = SCENARIOS.get(mk, {}).get("title", mk)

    # 새 컬럼 호환 (구버전 로그에는 없음)
    if "training_attempt_id" not in clean:
        clean["training_attempt_id"] = clean.get("session_id", "") or ""
    if "attempt_round" not in clean or str(clean.get("attempt_round", "")).strip() == "":
        clean["attempt_round"] = clean.get("attempt_round_total", 1) or 1

    norm = {k: clean.get(k, "") for k in LOG_FIELDNAMES}

    # 숫자형 컬럼 보정
    for col in ["question_index", "awarded_score", "max_score", "attempt_no_for_mission", "attempt_round"]:
        v = norm.get(col, "")
        try:
            if v == "" or v is None:
                norm[col] = 0
            else:
                norm[col] = int(float(v))
        except Exception:
            norm[col] = 0

    # 문자열 컬럼 보정
    for col in [
        "timestamp", "training_attempt_id", "employee_no", "name", "organization", "department",
        "mission_key", "mission_title", "question_code", "question_type", "question", "selected_or_text", "is_correct"
    ]:
        val = norm.get(col, "")
        if val is None:
            val = ""
        norm[col] = str(val)

    if not norm["organization"].strip():
        norm["organization"] = "미분류"
    if norm["attempt_round"] <= 0:
        norm["attempt_round"] = 1
    return norm


def _read_log_rows_tolerant():
    """
    로그 CSV를 최대한 관대하게 읽는다.
    - UTF-8/CP949 인코딩 혼합 대응
    - NUL 바이트 제거
    - 헤더/행 컬럼 수 불일치 허용
    """
    if not LOG_FILE.exists():
        return []

    import io as _io

    raw_bytes = LOG_FILE.read_bytes()
    if not raw_bytes:
        return []

    # NUL 제거 (간헐적으로 깨진 CSV에 섞이는 경우 대응)
    raw_bytes = raw_bytes.replace(b"\x00", b"")

    decoded = None
    for enc in ("utf-8-sig", "utf-8", "cp949", "euc-kr", "latin1"):
        try:
            decoded = raw_bytes.decode(enc)
            break
        except Exception:
            continue

    if decoded is None:
        decoded = raw_bytes.decode("utf-8", errors="replace")

    decoded = decoded.replace("\r\n", "\n").replace("\r", "\n")
    if not decoded.strip():
        return []

    rows = []

    try:
        reader = csv.reader(_io.StringIO(decoded))
        all_rows = list(reader)
    except Exception:
        lines = [ln for ln in decoded.split("\n") if ln.strip()]
        all_rows = [ln.split(",") for ln in lines]

    if not all_rows:
        return []

    header = [str(x).strip() for x in (all_rows[0] or [])]
    if not header or all(h == "" for h in header):
        header = LOG_FIELDNAMES
        data_rows = all_rows
    else:
        data_rows = all_rows[1:]

    if len(header) < len(LOG_FIELDNAMES):
        header = header + [f"__extra_col_{i}" for i in range(len(LOG_FIELDNAMES) - len(header))]

    seen = {}
    fixed_header = []
    for h in header:
        key = h if h else "unnamed"
        if key in seen:
            seen[key] += 1
            key = f"{key}__dup{seen[key]}"
        else:
            seen[key] = 0
        fixed_header.append(key)
    header = fixed_header

    for r in data_rows:
        if r is None:
            continue
        r = list(r)
        if not any(str(x).strip() for x in r):
            continue

        row_dict = {}
        for i, col in enumerate(header):
            row_dict[col] = r[i] if i < len(r) else ""
        if len(r) > len(header):
            row_dict["__extra__"] = r[len(header):]

        rows.append(_normalize_log_row(row_dict))

    return rows


def _ensure_log_schema_file():
    """헤더가 구버전이거나 스키마가 섞인 경우 현재 스키마로 정규화."""
    if not LOG_FILE.exists():
        return

    need_rewrite = False
    try:
        with open(LOG_FILE, "r", newline="", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            header = next(reader, [])
        if [str(x).strip() for x in header] != LOG_FIELDNAMES:
            need_rewrite = True
    except Exception:
        need_rewrite = True

    if not need_rewrite:
        return

    rows = _read_log_rows_tolerant()
    with open(LOG_FILE, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=LOG_FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow(_normalize_log_row(row))


def _coerce_log_df(df: pd.DataFrame) -> pd.DataFrame:
    """관리자 통계용 컬럼/타입 정규화."""
    if df is None:
        return pd.DataFrame()

    df = df.copy()
    # 중복 컬럼 제거 (구버전/깨진 CSV 방어)
    if hasattr(df.columns, "duplicated") and df.columns.duplicated().any():
        df = df.loc[:, ~df.columns.duplicated()].copy()
    # 예상 컬럼 채우기
    for col in LOG_FIELDNAMES:
        if col not in df.columns:
            df[col] = ""

    # 문자열 컬럼 정리
    for col in ["training_attempt_id", "employee_no", "name", "organization", "department", "mission_key", "mission_title", "question_code", "question_type", "question", "selected_or_text", "is_correct"]:
        df[col] = df[col].fillna("").astype(str)

    # 기관 보정
    df["organization"] = df["organization"].replace("", pd.NA).fillna(df["department"]).fillna("미분류").astype(str)

    # question_index / question_code 복원
    qidx_from_code = pd.to_numeric(df["question_code"].astype(str).str.extract(r"_Q(\d+)")[0], errors="coerce")
    qidx_existing = pd.to_numeric(df["question_index"], errors="coerce")
    df["question_index"] = qidx_existing.fillna(qidx_from_code).fillna(0).astype(int)

    mk_from_code = df["question_code"].astype(str).str.split("_Q").str[0]
    df["mission_key"] = df["mission_key"].replace("", pd.NA).fillna(mk_from_code).fillna("").astype(str)

    # mission_title 복원
    if "mission_title" not in df.columns:
        df["mission_title"] = ""
    df["mission_title"] = df["mission_title"].replace("", pd.NA)
    mapped_titles = df["mission_key"].map(lambda x: SCENARIOS.get(str(x), {}).get("title", str(x)))
    df["mission_title"] = df["mission_title"].fillna(mapped_titles).fillna("미상 테마").astype(str)

    # 숫자 컬럼
    for col in ["awarded_score", "max_score", "attempt_no_for_mission", "attempt_round"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # 시간 컬럼
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    # 완전 빈 행 제거
    if "question_code" in df.columns:
        df = df[~((df["question_code"].str.strip() == "") & (df["question"].str.strip() == ""))].copy()

    return df


def _normalize_col_key(col_name: str) -> str:
    return re.sub(r"[\s_\-\(\)\[\]/]+", "", str(col_name).strip().lower())


def _find_first_matching_column(columns, aliases):
    norm_map = {_normalize_col_key(c): c for c in columns}
    alias_norms = [_normalize_col_key(a) for a in aliases]
    for a in alias_norms:
        if a in norm_map:
            return norm_map[a]
    # 부분 일치 fallback
    for c in columns:
        nc = _normalize_col_key(c)
        if any(a in nc or nc in a for a in alias_norms if a):
            return c
    return None




def _read_excel_employee_file(xlsx_path: Path) -> pd.DataFrame:
    """
    직원명단 엑셀(.xlsx/.xls) 로더
    - 1차: pandas.read_excel(engine=openpyxl)
    - 2차: openpyxl 직접 파싱 (pandas optional dependency 오류 우회)
    - 실패 시: CSV 저장 안내 메시지 포함 예외 발생
    """
    suffix = xlsx_path.suffix.lower()

    # .xlsx 우선 처리
    if suffix == ".xlsx":
        # 1) pandas + openpyxl 엔진 시도
        try:
            return pd.read_excel(xlsx_path, engine="openpyxl")
        except Exception as e1:
            # 2) openpyxl 직접 파싱 시도 (pandas optional dependency 문제 우회)
            try:
                import openpyxl  # type: ignore
            except Exception:
                raise RuntimeError(
                    "엑셀 파일 읽기 모듈(openpyxl)이 설치되어 있지 않습니다. "
                    "requirements.txt에 openpyxl을 추가하거나, 직원명단을 CSV로 저장해 주세요."
                ) from e1

            try:
                wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
                ws = wb.active

                # 첫 번째 유효 행을 헤더로 사용
                header = None
                data_rows = []
                for row in ws.iter_rows(values_only=True):
                    vals = ["" if v is None else str(v).strip() for v in row]
                    if header is None:
                        # 완전 빈 행은 스킵
                        if all(v == "" for v in vals):
                            continue
                        header = vals
                        # 중복/빈 헤더 정리
                        seen = {}
                        clean_header = []
                        for i, h in enumerate(header):
                            h2 = h if h else f"col_{i+1}"
                            if h2 in seen:
                                seen[h2] += 1
                                h2 = f"{h2}_{seen[h2]}"
                            else:
                                seen[h2] = 0
                            clean_header.append(h2)
                        header = clean_header
                        continue

                    # 본문 행
                    # trailing empty columns 제거는 pandas처럼 엄격히 안 하고 길이만 맞춤
                    if len(vals) < len(header):
                        vals = vals + [""] * (len(header) - len(vals))
                    elif len(vals) > len(header):
                        vals = vals[:len(header)]
                    if all(v == "" for v in vals):
                        continue
                    data_rows.append(vals)

                if not header:
                    return pd.DataFrame()

                return pd.DataFrame(data_rows, columns=header)
            except Exception as e2:
                raise RuntimeError(f"엑셀 파일 파싱 실패: {e2}") from e2

    # .xls는 pandas 엔진 의존 (xlrd 등)
    try:
        return pd.read_excel(xlsx_path)
    except Exception as e:
        raise RuntimeError(
            "구형 엑셀(.xls) 파일을 읽지 못했습니다. .xlsx 또는 CSV로 저장 후 다시 시도해주세요. "
            f"(원인: {e})"
        ) from e


def load_employee_master_df():
    """
    app.py와 같은 폴더의 직원명단(csv/xlsx)을 자동 탐색해 표준 컬럼(employee_no/name/organization)으로 반환.
    """
    candidate_paths = []
    existing_names = {p.name.lower(): p for p in BASE_DIR.iterdir() if p.is_file()}

    # 1) 우선순위 파일명
    for nm in EMPLOYEE_MASTER_CANDIDATE_NAMES:
        p = BASE_DIR / nm
        if p.exists() and p.is_file():
            candidate_paths.append(p)

    # 2) 패턴 탐색
    for p in BASE_DIR.iterdir():
        if not p.is_file():
            continue
        lower = p.name.lower()
        if p.suffix.lower() not in [".csv", ".xlsx", ".xls"]:
            continue
        if p not in candidate_paths and any(k in lower for k in ["employee", "employees", "staff", "직원", "사번", "명단", "임직원"]):
            candidate_paths.append(p)

    if not candidate_paths:
        return None, "직원 명단 파일 미탐지 (예: employee_master.xlsx / 직원명단.xlsx)"

    last_err = None
    for p in candidate_paths:
        try:
            if p.suffix.lower() in [".xlsx", ".xls"]:
                raw_df = _read_excel_employee_file(p)
            else:
                raw_df = None
                for enc in ["utf-8-sig", "cp949", "euc-kr", "utf-8"]:
                    try:
                        raw_df = pd.read_csv(p, encoding=enc)
                        break
                    except Exception:
                        continue
                if raw_df is None:
                    raw_df = pd.read_csv(p, engine="python", on_bad_lines="skip")

            if raw_df is None or raw_df.empty:
                continue

            raw_df.columns = [str(c).strip() for c in raw_df.columns]
            emp_col = _find_first_matching_column(raw_df.columns, EMPLOYEE_COL_ALIASES["employee_no"])
            name_col = _find_first_matching_column(raw_df.columns, EMPLOYEE_COL_ALIASES["name"])
            org_col = _find_first_matching_column(raw_df.columns, EMPLOYEE_COL_ALIASES["organization"])

            if name_col is None:
                last_err = f"{p.name}: 이름 컬럼을 찾지 못함"
                continue

            # 사번 컬럼 없으면 빈값 허용(단, 동명이인 구분력 저하 안내)
            if emp_col is None:
                raw_df["__employee_no__"] = ""
                emp_col = "__employee_no__"
            if org_col is None:
                raw_df["__organization__"] = "미분류"
                org_col = "__organization__"

            df = pd.DataFrame({
                "employee_no": raw_df[emp_col],
                "name": raw_df[name_col],
                "organization": raw_df[org_col],
            })

            for c in ["employee_no", "name", "organization"]:
                df[c] = df[c].fillna("").astype(str).str.strip()

            df = df[df["name"] != ""].copy()
            df["organization"] = df["organization"].replace("", "미분류")
            # 중복 행 제거
            df = df.drop_duplicates(subset=["employee_no", "name", "organization"]).reset_index(drop=True)

            msg = f"직원 명단 파일 로드 완료: {p.name} · {len(df)}명"
            if (df["employee_no"].str.strip() == "").all():
                msg += " (사번 컬럼 미검출: 동명이인 구분은 소속 기준으로만 가능)"
            return df, msg

        except Exception as e:
            last_err = f"{p.name}: {e}"
            continue

    return None, f"직원 명단 파일을 읽지 못했습니다. ({last_err or '형식 확인 필요'})"


def _employee_candidate_label(row: dict) -> str:
    emp_no = str(row.get("employee_no", "")).strip() or "사번없음"
    name = str(row.get("name", "")).strip() or "이름미상"
    org = str(row.get("organization", "")).strip() or "미분류"
    return f"[{emp_no}] {name} / {org}"



def _render_modal_readonly_field(container, label: str, value: str):
    label_safe = html.escape(str(label))
    value_safe = html.escape(str(value) if value is not None else "")
    container.markdown(
        f"""
        <div class="modal-readonly-field">
            <div class="modal-readonly-label">{label_safe}</div>
            <div class="modal-readonly-value">{value_safe}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_confirm_readonly_field(container, label: str, value: str):
    with container:
        st.markdown(
            f"""
            <div class='confirm-readonly-field'>
              <div class='confirm-readonly-label'>{label}</div>
              <div class='confirm-readonly-value'>{html.escape(str(value or '-'))}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_employee_lookup_popup_body(name_query: str = ""):
    st.markdown("<div style='font-size:1.05rem;font-weight:800;color:#172233;margin-bottom:4px;'>📋 직원 정보 확인</div>", unsafe_allow_html=True)
    st.caption("사번, 이름, 소속 기관을 확인한 뒤 정확한 본인 정보를 선택하세요.")
    candidates = pd.DataFrame(st.session_state.get("employee_lookup_candidates", []))
    if candidates.empty:
        st.info("조회 결과가 없습니다.")
        if st.button("닫기", key="employee_modal_close_empty", use_container_width=True):
            st.session_state.employee_lookup_modal_open = False
            st.rerun()
        return

    for col in ["employee_no", "name", "organization"]:
        if col not in candidates.columns:
            candidates[col] = ""
    show_df = candidates[["employee_no", "name", "organization"]].copy()
    show_df.columns = ["사번", "이름", "소속 기관"]

    safe_dataframe(show_df, use_container_width=True, height=min(320, 90 + len(show_df) * 35))

    exact_name = (name_query or "").strip()
    exact_cnt = int((candidates["name"].astype(str).str.strip() == exact_name).sum()) if exact_name else 0
    if exact_cnt >= 2:
        st.warning(f"동명이인 {exact_cnt}명이 확인되었습니다. 반드시 사번을 확인해 선택해주세요.")

    options = list(range(len(candidates)))
    default_idx = 0
    if st.session_state.get("employee_selected_record"):
        sel = st.session_state.get("employee_selected_record") or {}
        for i, row in candidates.iterrows():
            if str(row.get("employee_no", "")).strip() == str(sel.get("employee_no", "")).strip() and str(row.get("name", "")).strip() == str(sel.get("name", "")).strip():
                default_idx = int(i)
                break

    selected_idx = st.selectbox(
        "본인 정보 선택",
        options=options,
        index=default_idx if options else 0,
        format_func=lambda i: _employee_candidate_label(candidates.iloc[int(i)].to_dict()),
        key="employee_candidate_select_idx_modal",
    )

    preview = candidates.iloc[int(selected_idx)].to_dict()
    p1, p2, p3 = st.columns(3)
    _render_modal_readonly_field(p1, "사번", str(preview.get("employee_no", "")))
    _render_modal_readonly_field(p2, "이름", str(preview.get("name", "")))
    _render_modal_readonly_field(p3, "소속 기관", str(preview.get("organization", "")))

    st.markdown("<div class='brief-actions-wrap'></div>", unsafe_allow_html=True)
    c1, c2 = st.columns([1, 1], gap='large')
    with c1:
        if st.button("✅ 이 정보로 확인", key="employee_modal_confirm_btn", use_container_width=True):
            row = candidates.iloc[int(selected_idx)].to_dict()
            st.session_state.employee_selected_record = {
                "employee_no": str(row.get("employee_no", "")).strip(),
                "name": str(row.get("name", "")).strip(),
                "organization": str(row.get("organization", "")).strip() or "미분류",
            }
            st.session_state.employee_lookup_modal_open = False
            try:
                st.toast("참가자 정보가 확인되었습니다.", icon="✅")
            except Exception:
                pass
            st.rerun()
    with c2:
        if st.button("닫기", key="employee_modal_close_btn", use_container_width=True):
            st.session_state.employee_lookup_modal_open = False
            st.rerun()


if hasattr(st, "dialog"):
    @st.dialog("📋 직원 정보 확인")
    def render_employee_lookup_popup(name_query: str = ""):
        _render_employee_lookup_popup_body(name_query)
else:
    def render_employee_lookup_popup(name_query: str = ""):
        st.markdown("### 📋 직원 정보 확인")
        _render_employee_lookup_popup_body(name_query)


def append_attempt_log(mission_key: str, q_idx: int, q_type: str, payload: dict):
    user = st.session_state.get("user_info", {})
    mission = SCENARIOS[mission_key]
    question = mission["quiz"][q_idx]

    row = _normalize_log_row({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "training_attempt_id": st.session_state.get("training_attempt_id", ""),
        "attempt_round": st.session_state.get("training_attempt_round", 1),
        "employee_no": user.get("employee_no", ""),
        "name": user.get("name", ""),
        "organization": user.get("org", ""),
        "department": "",
        "mission_key": mission_key,
        "mission_title": mission["title"],
        "question_index": q_idx + 1,
        "question_code": f"{mission_key}_Q{q_idx+1}",
        "question_type": q_type,
        "question": question["question"],
        "selected_or_text": payload.get("selected_or_text", ""),
        "is_correct": payload.get("is_correct", ""),
        "awarded_score": payload.get("awarded_score", 0),
        "max_score": question.get("score", 0),
        "attempt_no_for_mission": st.session_state.attempt_counts.get(mission_key, 0),
    })

    st.session_state.attempt_history.append(row)

    try:
        _ensure_log_schema_file()
        file_exists = LOG_FILE.exists()
        with open(LOG_FILE, "a", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=LOG_FIELDNAMES)
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)
    except Exception as e:
        st.session_state.log_write_error = str(e)

_TEXT_KEYWORD_SYNONYM_MAP = {
    "서면": ["문서", "서류", "계약서", "발주서", "합의서", "기록"],
    "서면계약": ["계약서", "서면 계약", "문서 계약"],
    "기록": ["증빙", "보관", "남기", "기재"],
    "공식": ["정식", "회사 채널", "공식채널", "정규"],
    "채널": ["창구", "경로", "프로세스"],
    "보고": ["알림", "공유", "상신", "신고"],
    "승인": ["결재", "사전승인", "승인받"],
    "거절": ["불가", "어렵", "제공하지", "응할수없", "응할 수 없", "거부"],
    "중단": ["멈추", "보류", "정지", "중지"],
    "재검토": ["다시 검토", "검토", "확인"],
    "공정": ["공정성", "형평", "동일기회", "동일 기회"],
    "동일": ["같은", "동일하게", "일관"],
    "비공개": ["내부정보", "미공개", "민감정보"],
    "질의": ["문의", "질문", "질의응답"],
    "접수": ["등록", "남기", "신청"],
    "회신": ["답변", "안내", "응답"],
    "증빙": ["근거", "자료", "문서"],
    "사전": ["미리", "선행"],
    "점검": ["확인", "체크", "검토"],
    "교육": ["안내", "고지", "공유"],
    "분리": ["분리보관", "분리 저장", "접근통제"],
    "최소": ["최소한", "필요한 범위", "필요 최소"],
    "보관": ["저장", "유지", "관리"],
    "파기": ["삭제", "폐기"],
}

def _normalize_korean_text_for_keyword_match(text: str) -> str:
    s = str(text or "").lower()
    s = re.sub(r"\s+", "", s)
    s = re.sub(r"[^0-9a-zA-Z가-힣]", "", s)
    return s

def _expand_keyword_variants(keyword: str) -> list[str]:
    kw = str(keyword or "").strip()
    if not kw:
        return []
    variants = [kw]
    base_norm = _normalize_korean_text_for_keyword_match(kw)
    if base_norm:
        variants.append(base_norm)
    for canon, alts in _TEXT_KEYWORD_SYNONYM_MAP.items():
        canon_norm = _normalize_korean_text_for_keyword_match(canon)
        if kw == canon or base_norm == canon_norm or kw in alts:
            variants.extend([canon])
            variants.extend(alts)
    if len(base_norm) >= 3:
        variants.append(base_norm[: max(3, len(base_norm)-1)])
    out = []
    seen = set()
    for v in variants:
        v2 = str(v).strip()
        if not v2:
            continue
        n = _normalize_korean_text_for_keyword_match(v2)
        key = n or v2.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(v2)
    return out

def evaluate_text_answer(answer_text: str, rubric_keywords: dict, max_score: int):
    """주관식 키워드 기반 평가 (가중치/최소일치수/유사표현 보정 지원)"""
    text = (answer_text or "").strip()
    if not text:
        return {
            "awarded_score": 0,
            "found_groups": [],
            "missing_groups": list(rubric_keywords.keys()),
            "quality": "empty",
            "score_breakdown": [],
        }

    lowered = text.lower()
    compact = _normalize_korean_text_for_keyword_match(text)
    group_specs = []
    for group_name, spec in (rubric_keywords or {}).items():
        if isinstance(spec, dict):
            keywords = [str(k).strip() for k in spec.get("keywords", []) if str(k).strip()]
            weight = float(spec.get("weight", 1))
            min_hits = int(spec.get("min_hits", 1))
        else:
            keywords = [str(k).strip() for k in (spec or []) if str(k).strip()]
            weight = 1.0
            min_hits = 1

        if min_hits < 1:
            min_hits = 1
        if weight <= 0:
            weight = 1.0

        expanded = []
        for kw in keywords:
            expanded.extend(_expand_keyword_variants(kw))
        if not expanded:
            expanded = keywords

        dedup = []
        seen_kw = set()
        for kw in expanded:
            key = _normalize_korean_text_for_keyword_match(kw) or str(kw).lower()
            if key in seen_kw:
                continue
            seen_kw.add(key)
            dedup.append(kw)

        group_specs.append({
            "name": str(group_name),
            "keywords": dedup,
            "weight": weight,
            "min_hits": min_hits,
        })

    if not group_specs:
        return {
            "awarded_score": 0,
            "found_groups": [],
            "missing_groups": [],
            "quality": "empty",
            "score_breakdown": [],
        }

    found, missing = [], []
    raw_total = 0.0
    raw_earned = 0.0
    breakdown = []

    for g in group_specs:
        matched = []
        seen = set()
        for kw in g["keywords"]:
            kw_norm = _normalize_korean_text_for_keyword_match(kw)
            kw_low = str(kw).lower().strip()
            hit_now = False
            if kw_norm and kw_norm in compact:
                hit_now = True
            elif kw_low and kw_low in lowered:
                hit_now = True
            if hit_now:
                dedup_key = kw_norm or kw_low
                if dedup_key not in seen:
                    seen.add(dedup_key)
                    matched.append(kw)
        hit_count = len(matched)
        hit = hit_count >= g["min_hits"]

        raw_total += g["weight"]
        if hit:
            raw_earned += g["weight"]
            found.append(g["name"])
            earned_weight = g["weight"]
        else:
            missing.append(g["name"])
            earned_weight = 0.0

        breakdown.append({
            "group": g["name"],
            "weight": int(round(g["weight"])),
            "earned": int(round(earned_weight)),
            "matched": matched[:8],
            "min_hits": g["min_hits"],
            "hit_count": hit_count,
        })

    ratio = (raw_earned / raw_total) if raw_total else 0
    awarded = int(round(max_score * ratio))

    if len(text) < 12 and awarded > 0:
        awarded = max(0, awarded - max(1, int(round(max_score * 0.2))))
    elif len(text) < 25 and awarded > 0 and ratio >= 0.5:
        awarded = max(0, awarded - 1)

    if ratio >= 0.8:
        quality = "good"
    elif ratio >= 0.45:
        quality = "partial"
    else:
        quality = "needs_more"

    return {
        "awarded_score": awarded,
        "found_groups": found,
        "missing_groups": missing,
        "quality": quality,
        "score_breakdown": breakdown,
    }


def get_grade(score: int, total: int):
    ratio = score / total if total else 0
    if ratio >= 0.9:
        return "마스터 가디언 🏆"
    if ratio >= 0.7:
        return "실전 가디언 ✅"
    if ratio >= 0.5:
        return "수습 가디언 📘"
    return "재학습 권장 🔁"



def reset_game():
    st.session_state.clear()
    st.rerun()




def _derive_attempt_uid_series(df: pd.DataFrame) -> pd.Series:
    if df is None or df.empty:
        return pd.Series(dtype=str)
    tmp = df.copy()
    if "training_attempt_id" not in tmp.columns:
        tmp["training_attempt_id"] = ""
    base_id = tmp["training_attempt_id"].fillna("").astype(str).str.strip()
    if "learner_id" not in tmp.columns:
        if "employee_no" not in tmp.columns:
            tmp["employee_no"] = ""
        if "organization" not in tmp.columns:
            tmp["organization"] = "미분류"
        if "name" not in tmp.columns:
            tmp["name"] = "이름미상"
        tmp["learner_id"] = tmp["employee_no"].astype(str).where(
            tmp["employee_no"].astype(str).str.strip() != "",
            tmp["organization"].astype(str) + "|" + tmp["name"].astype(str)
        )
    legacy_id = "legacy|" + tmp["learner_id"].astype(str)
    return base_id.where(base_id != "", legacy_id)

def _summarize_user_attempts(employee_no: str, name: str, organization: str):
    total_questions = sum(len(SCENARIOS[k]["quiz"]) for k in SCENARIO_ORDER)
    df, err = _load_log_df()
    if err or df is None or df.empty:
        return {"attempts_started": 0, "completed_attempts": 0, "best_score": 0, "last_score": 0, "attempts_df": pd.DataFrame()}

    df = _coerce_log_df(df)
    if df.empty:
        return {"attempts_started": 0, "completed_attempts": 0, "best_score": 0, "last_score": 0, "attempts_df": pd.DataFrame()}

    employee_no = str(employee_no or "").strip()
    name = str(name or "").strip()
    organization = str(organization or "").strip() or "미분류"

    if employee_no:
        u = df[df["employee_no"].astype(str).str.strip() == employee_no].copy()
    else:
        u = df[
            (df["name"].astype(str).str.strip() == name) &
            (df["organization"].astype(str).str.strip().replace("", "미분류") == organization)
        ].copy()

    if u.empty:
        return {"attempts_started": 0, "completed_attempts": 0, "best_score": 0, "last_score": 0, "attempts_df": pd.DataFrame()}

    u["organization"] = u["organization"].fillna("").astype(str).str.strip().replace("", "미분류")
    u["employee_no"] = u["employee_no"].fillna("").astype(str).str.strip()
    u["name"] = u["name"].fillna("").astype(str).str.strip()
    u["learner_id"] = u["employee_no"].where(u["employee_no"] != "", u["organization"] + "|" + u["name"])
    u["attempt_uid"] = _derive_attempt_uid_series(u)
    u = u.sort_values(["timestamp"], ascending=True)

    latest_per_q_attempt = u.drop_duplicates(subset=["attempt_uid", "question_code"], keep="last")
    per_attempt = (
        latest_per_q_attempt.groupby(["attempt_uid"], as_index=False)
        .agg(
            answered_questions=("question_code", "nunique"),
            score_sum=("awarded_score", "sum"),
            last_activity=("timestamp", "max"),
            attempt_round_logged=("attempt_round", "max"),
        )
    )
    per_attempt["total_score"] = pd.to_numeric(per_attempt["score_sum"], errors="coerce").fillna(0.0)
    per_attempt.loc[per_attempt["answered_questions"] > 0, "total_score"] += PARTICIPATION_SCORE
    per_attempt["total_score"] = per_attempt["total_score"].round(0).astype(int)
    per_attempt["is_completed"] = per_attempt["answered_questions"] >= total_questions
    per_attempt = per_attempt.sort_values(["last_activity", "total_score"], ascending=[True, True]).reset_index(drop=True)

    return {
        "attempts_started": int(per_attempt["attempt_uid"].nunique()),
        "completed_attempts": int(per_attempt["is_completed"].sum()),
        "best_score": int(per_attempt["total_score"].max()) if not per_attempt.empty else 0,
        "last_score": int(per_attempt.iloc[-1]["total_score"]) if not per_attempt.empty else 0,
        "attempts_df": per_attempt,
    }

def _set_retry_offer(user_info: dict, completed_attempts: int, context: str = "intro"):
    st.session_state.retry_offer = {
        "user_info": dict(user_info or {}),
        "completed_attempts": int(completed_attempts or 0),
        "context": context,
        "created_at": time.time(),
    }

def _clear_retry_offer():
    st.session_state.retry_offer = None

def start_training_attempt_session(user_info: dict, attempt_round: int, *, skip_to_stage: str = "map"):
    user_info = dict(user_info or {})
    keep_keys = {
        "admin_authed": st.session_state.get("admin_authed", False),
        "audio_debug": st.session_state.get("audio_debug", False),
        "employee_lookup_candidates": st.session_state.get("employee_lookup_candidates", []),
        "employee_selected_record": st.session_state.get("employee_selected_record"),
        "employee_lookup_modal_open": False,
    }

    st.session_state.user_info = {
        "employee_no": str(user_info.get("employee_no", "")).strip(),
        "name": str(user_info.get("name", "")).strip(),
        "org": str(user_info.get("org", user_info.get("organization", ""))).strip() or "미분류",
    }
    st.session_state.stage = skip_to_stage
    st.session_state.current_mission = None
    st.session_state.completed = []
    st.session_state.mission_scores = {}
    st.session_state.score = 0
    st.session_state.participation_awarded = False
    st.session_state.participation_score = 0
    st.session_state.quiz_progress = {}
    st.session_state.attempt_counts = {}
    st.session_state.attempt_history = []
    st.session_state.show_conquer_fx = False
    st.session_state.map_fx_done = False
    st.session_state.last_cleared_mission = None
    st.session_state.map_celebrate_until = 0.0
    st.session_state.map_celebrate_theme = None
    st.session_state.log_write_error = None
    st.session_state.played_final_fanfare = False
    st.session_state.retry_offer = None
    st.session_state.training_attempt_round = int(max(1, attempt_round))
    st.session_state.training_attempt_id = f"run-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"

    for k, v in keep_keys.items():
        st.session_state[k] = v

    award_participation_points_if_needed()

def render_retry_offer_box(context: str):
    offer = st.session_state.get("retry_offer")
    if not offer or offer.get("context") != context:
        return

    user = offer.get("user_info", {})
    completed_attempts = int(offer.get("completed_attempts", 0) or 0)
    next_round = completed_attempts + 1
    max_attempts = 3
    remaining_after = max(0, max_attempts - next_round)

    if completed_attempts >= max_attempts:
        st.error("이미 최대 참여 횟수(총 3회)를 모두 사용했습니다. 관리자에게 문의해주세요.")
        return

    name = html.escape(str(user.get("name", "참가자")))
    org = html.escape(str(user.get("org", user.get("organization", "")) or "미분류"))

    if next_round >= max_attempts:
        title = "⚠️ Bonus attempt (3rd) notice"
        desc = (
            "This is your last chance. Attempt 3 is a bonus learning opportunity and will NOT affect "
            "your institution’s cumulative/average score. Focus on learning and challenge again."
        )
    else:
        title = "🔄 Re-participation (Re-challenge) information"
        desc = (
            "Re-participation is limited. You may re-participate up to two additional times (max 3 attempts). "
            "For institution scores, the higher score between Attempts 1 and 2 will be reflected in the "
            "cumulative/average score after the round ends."
        )

    st.markdown(
        f"""
        <div class="retry-offer-card">
          <div class="retry-offer-title">{title}</div>
          <div class="retry-offer-body"><b>{name}</b> ({org}) · Status: Completed <b>{completed_attempts}</b> / Max <b>{max_attempts}</b> attempts</div>
          <div class="retry-offer-desc">{desc}</div>
          <div class="retry-offer-note">If selected, it will skip the main screen and start directly from Stage 1. (Remaining retry opportunities: {remaining_after})</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns([1, 1], gap="large")
    with c1:
        if st.button("✅ 예, 다시 도전할게요", key=f"retry_yes_{context}", use_container_width=True):
            start_training_attempt_session(user, next_round, skip_to_stage="map")
            st.rerun()
    with c2:
        if st.button("아니오", key=f"retry_no_{context}", use_container_width=True):
            _clear_retry_offer()
            st.rerun()

def _load_log_df():
    """
    관리자 탭용 로그 로더 (절대 크래시 방지)
    """
    if not LOG_FILE.exists():
        return None, "아직 누적 로그 파일이 없습니다."

    try:
        rows = _read_log_rows_tolerant()
        if rows:
            df = pd.DataFrame(rows)
            df = _coerce_log_df(df)
            if not df.empty:
                return df, None
        first_err = "rows empty"
    except Exception as e1:
        first_err = str(e1)

    try:
        df = pd.read_csv(LOG_FILE, encoding="utf-8-sig", engine="python", on_bad_lines="skip")
        df = _coerce_log_df(df)
        if not df.empty:
            return df, None
        second_err = "pandas empty"
    except Exception as e2:
        second_err = str(e2)

    return None, f"로그 파일을 읽지 못했습니다. (1차: {first_err}) (2차: {second_err})"


def _build_participant_snapshot(df: pd.DataFrame):
    df = df.copy()

    for c, default in [("organization", "미분류"), ("employee_no", ""), ("name", "이름미상"), ("department", "")]:
        if c not in df.columns:
            df[c] = default
    df["organization"] = df["organization"].fillna("").astype(str).str.strip().replace("", "미분류")
    df["employee_no"] = df["employee_no"].fillna("").astype(str).str.strip()
    df["name"] = df["name"].fillna("").astype(str).str.strip().replace("", "이름미상")
    df["department"] = df["department"].fillna("").astype(str)

    for col in ["awarded_score", "max_score", "question_index", "attempt_round"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        else:
            df[col] = 0

    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    else:
        df["timestamp"] = pd.NaT

    if "question_code" not in df.columns:
        if "mission_key" in df.columns:
            df["question_code"] = df["mission_key"].astype(str) + "_Q" + df["question_index"].astype(int).astype(str)
        else:
            df["question_code"] = "Q?"
    if "mission_key" not in df.columns:
        df["mission_key"] = df["question_code"].astype(str).str.split("_Q").str[0]

    if "training_attempt_id" not in df.columns:
        df["training_attempt_id"] = ""
    df["training_attempt_id"] = df["training_attempt_id"].fillna("").astype(str).str.strip()

    df["learner_id"] = df["employee_no"].where(df["employee_no"].str.strip() != "", df["organization"] + "|" + df["name"])
    df["attempt_uid"] = _derive_attempt_uid_series(df)

    df_sorted = df.sort_values(["timestamp"], ascending=True)
    latest_per_q_attempt = df_sorted.drop_duplicates(subset=["learner_id", "attempt_uid", "question_code"], keep="last")

    total_questions = sum(len(SCENARIOS[k]["quiz"]) for k in SCENARIO_ORDER)
    theme_question_counts = {k: len(SCENARIOS[k]["quiz"]) for k in SCENARIO_ORDER}

    theme_counts = (
        latest_per_q_attempt.groupby(["learner_id", "attempt_uid", "mission_key"], as_index=False)
        .agg(answered_in_theme=("question_code", "nunique"))
    )
    theme_counts["theme_total_questions"] = theme_counts["mission_key"].map(theme_question_counts).fillna(999)
    theme_counts["theme_completed"] = theme_counts["answered_in_theme"] >= theme_counts["theme_total_questions"]

    completed_theme_cnt = (
        theme_counts.groupby(["learner_id", "attempt_uid"], as_index=False)
        .agg(completed_themes=("theme_completed", "sum"))
    )

    per_attempt = (
        latest_per_q_attempt.groupby(["learner_id", "attempt_uid", "employee_no", "organization", "name"], as_index=False)
        .agg(
            raw_score=("awarded_score", "sum"),
            answered_questions=("question_code", "nunique"),
            last_activity=("timestamp", "max"),
            latest_attempt_round=("attempt_round", "max"),
        )
    )
    per_attempt = per_attempt.merge(completed_theme_cnt, on=["learner_id", "attempt_uid"], how="left")
    per_attempt["completed_themes"] = per_attempt["completed_themes"].fillna(0).astype(int)
    per_attempt["raw_score"] = pd.to_numeric(per_attempt["raw_score"], errors="coerce").fillna(0)
    per_attempt["answered_questions"] = pd.to_numeric(per_attempt["answered_questions"], errors="coerce").fillna(0).astype(int)
    per_attempt["total_score"] = per_attempt["raw_score"]
    per_attempt.loc[per_attempt["answered_questions"] > 0, "total_score"] += PARTICIPATION_SCORE
    per_attempt["total_score"] = per_attempt["total_score"].round(0).astype(int)
    per_attempt["completion_rate_q"] = ((per_attempt["answered_questions"] / max(total_questions, 1)) * 100).round(1)
    per_attempt["score_rate"] = ((per_attempt["total_score"] / max(TOTAL_SCORE, 1)) * 100).round(1)
    per_attempt["is_completed"] = per_attempt["answered_questions"] >= total_questions

    attempt_meta = (
        per_attempt.groupby(["learner_id"], as_index=False)
        .agg(
            attempts_started=("attempt_uid", "nunique"),
            completed_attempts=("is_completed", "sum"),
            last_activity_all=("last_activity", "max"),
            best_score_any=("total_score", "max"),
        )
    )
    submission_meta = (
        df_sorted.groupby(["learner_id"], as_index=False)
        .agg(total_attempts=("question_code", "count"))
    )
    attempt_meta = attempt_meta.merge(submission_meta, on="learner_id", how="left")

    # Institution score policy:
    # - Attempts 1–2: institution score reflects the higher score between rounds 1 and 2.
    # - Attempt 3 is a bonus learning opportunity and does NOT affect institution score.
    per_attempt["latest_attempt_round"] = pd.to_numeric(per_attempt["latest_attempt_round"], errors="coerce").fillna(1).astype(int)
    per_attempt["latest_attempt_round"] = per_attempt["latest_attempt_round"].clip(lower=1).astype(int)

    per_attempt_counted = per_attempt[per_attempt["latest_attempt_round"] <= 2].copy()
    if per_attempt_counted.empty:
        # Fallback (should be rare): if no round<=2 exists, use all attempts for display.
        per_attempt_counted = per_attempt.copy()

    best_attempt_institution = per_attempt_counted.sort_values(
        ["learner_id", "is_completed", "total_score", "answered_questions", "last_activity"],
        ascending=[True, False, False, False, False]
    ).drop_duplicates(subset=["learner_id"], keep="first")

    best_attempt_any = per_attempt.sort_values(
        ["learner_id", "is_completed", "total_score", "answered_questions", "last_activity"],
        ascending=[True, False, False, False, False]
    ).drop_duplicates(subset=["learner_id"], keep="first")

    participants = best_attempt_institution.merge(attempt_meta, on="learner_id", how="left")
    participants["completed_attempts"] = participants["completed_attempts"].fillna(0).astype(int)
    participants["attempts_started"] = participants["attempts_started"].fillna(0).astype(int)
    participants["is_completed"] = participants["is_completed"].fillna(False).astype(bool)

    # Scores
    participants["institution_score"] = pd.to_numeric(participants["total_score"], errors="coerce").fillna(0).astype(int)
    participants["personal_best_score"] = pd.to_numeric(participants["best_score_any"], errors="coerce").fillna(0).astype(int)

    # Status label (institution score policy)
    participants["status"] = participants["is_completed"].map({
        True: "Completed (Institution score: best of Attempts 1–2)",
        False: "In progress (Institution score: best of Attempts 1–2)"
    })

    org_summary = (
        participants.groupby("organization", as_index=False)
        .agg(
            participants=("learner_id", "nunique"),
            completed=("is_completed", "sum"),
            cumulative_score=("total_score", "sum"),
            avg_score=("total_score", "mean"),
            avg_score_rate=("score_rate", "mean"),
            avg_completion_rate=("completion_rate_q", "mean"),
            latest_activity=("last_activity_all", "max"),
        )
    )
    org_attempts = per_attempt.groupby("organization", as_index=False).agg(total_attempts=("attempt_uid", "nunique"))
    org_summary = org_summary.merge(org_attempts, on="organization", how="left")
    for col in ["cumulative_score", "avg_score", "avg_score_rate", "avg_completion_rate", "total_attempts"]:
        org_summary[col] = pd.to_numeric(org_summary[col], errors="coerce").fillna(0)
    org_summary["cumulative_score"] = org_summary["cumulative_score"].round(0).astype(int)
    org_summary["avg_score"] = org_summary["avg_score"].round(1)
    org_summary["avg_score_rate"] = org_summary["avg_score_rate"].round(1)
    org_summary["avg_completion_rate"] = org_summary["avg_completion_rate"].round(1)
    org_summary["completion_rate"] = ((org_summary["completed"] / org_summary["participants"].replace(0, 1)) * 100).round(1)
    org_summary = org_summary.sort_values(
        ["cumulative_score", "avg_score", "participants", "organization"],
        ascending=[False, False, False, True]
    ).reset_index(drop=True)

    participants_view = participants.copy()
    # For admin views: show both institution score and personal best (incl. attempt 3, if any)
    if "personal_best_score" in participants_view.columns:
        participants_view["Personal best score (all attempts)"] = participants_view["personal_best_score"]
    participants_view["Institution-reflected score"] = participants_view["total_score"]
    participants_view["last_activity"] = pd.to_datetime(participants_view["last_activity"], errors="coerce").dt.strftime("%Y-%m-%d %H:%M").fillna("-")
    participants_view["last_activity_all"] = pd.to_datetime(participants_view["last_activity_all"], errors="coerce").dt.strftime("%Y-%m-%d %H:%M").fillna("-")
    participants_view = participants_view.sort_values(["total_score", "last_activity"], ascending=[False, False])

    return {
        "raw": df,
        "latest_per_q": latest_per_q_attempt,
        "per_attempt": per_attempt,
        "participants": participants,
        "participants_view": participants_view,
        "org_summary": org_summary,
        "total_questions": total_questions,
    }


def render_intro_org_cumulative_board():
    """메인 화면 전용: 기관별 누적 점수/참여 현황 대시보드 (참여자용 요약 뷰)."""
    st.markdown("### 🏢 Cumulative score and participation status by institution")

    df, err = _load_log_df()
    if err:
        st.info(err)
        return

    try:
        snap = _build_participant_snapshot(df)
        participants = snap.get("participants", pd.DataFrame())
        if participants is None or participants.empty:
            st.info("표시할 누적 점수 데이터가 없습니다.")
            return

        # 참여자 최신 점수 기준 집계
        org_score = (
            participants.groupby("organization", as_index=False)
            .agg(
                cumulative_score=("total_score", "sum"),
                participant_count=("learner_id", "nunique"),
                avg_score=("total_score", "mean"),
            )
        )
        org_score["organization"] = org_score["organization"].fillna("미분류").astype(str)

        # 직원명단 기반 전체 인원(분모) 집계 -> 참여율 계산
        emp_df, _ = load_employee_master_df()
        if emp_df is not None and not emp_df.empty:
            emp_base = emp_df.copy()
            emp_base["organization"] = emp_base["organization"].fillna("미분류").astype(str)
            # 사번이 비어있는 경우를 대비해 이름 기준으로 대체 식별
            emp_base["_emp_key"] = emp_base["employee_no"].astype(str).str.strip()
            emp_base.loc[emp_base["_emp_key"] == "", "_emp_key"] = emp_base["name"].astype(str).str.strip()
            org_base = (
                emp_base.groupby("organization", as_index=False)
                .agg(total_employees=("_emp_key", "nunique"))
            )
        else:
            org_base = pd.DataFrame(columns=["organization", "total_employees"])

        merged = org_base.merge(org_score, on="organization", how="outer")
        for col in ["total_employees", "cumulative_score", "participant_count", "avg_score"]:
            if col not in merged.columns:
                merged[col] = 0
        merged["total_employees"] = pd.to_numeric(merged["total_employees"], errors="coerce").fillna(0).astype(int)
        merged["cumulative_score"] = pd.to_numeric(merged["cumulative_score"], errors="coerce").fillna(0.0)
        merged["participant_count"] = pd.to_numeric(merged["participant_count"], errors="coerce").fillna(0).astype(int)
        merged["avg_score"] = pd.to_numeric(merged["avg_score"], errors="coerce").fillna(0.0)

        merged["participation_rate"] = np.where(
            merged["total_employees"] > 0,
            (merged["participant_count"] / merged["total_employees"] * 100.0),
            np.nan,
        )

        merged = merged.sort_values(
            ["cumulative_score", "avg_score", "participant_count", "organization"],
            ascending=[False, False, False, True],
        ).reset_index(drop=True)
        merged["rank"] = np.arange(1, len(merged) + 1)

        if merged.empty:
            st.info("기관별 누적 점수 데이터가 없습니다.")
            return

        # 시각 강조용 HTML 테이블
        st.markdown(
            """
            <style>
            .intro-org-board-wrap{
              background: linear-gradient(180deg, rgba(12,20,38,.95), rgba(10,15,28,.96));
              border:1px solid rgba(71,106,178,.35);
              border-radius:16px;
              padding:14px 14px 10px 14px;
              box-shadow: 0 8px 24px rgba(0,0,0,.28);
              margin-bottom: 8px;
            }
            .intro-org-board-sub{
              color:#BFD2FF; font-size:.86rem; margin-top:-2px; margin-bottom:10px; opacity:.95;
            }
            .intro-org-table{
              width:100%;
              border-collapse: separate;
              border-spacing:0 6px;
              table-layout: fixed;
            }
            .intro-org-table thead th{
              text-align:left;
              font-size:.86rem;
              color:#DDE8FF;
              background: rgba(62,90,152,.30);
              border-top:1px solid rgba(120,150,220,.22);
              border-bottom:1px solid rgba(120,150,220,.16);
              padding:9px 10px;
            }
            .intro-org-table thead th:first-child{border-radius:10px 0 0 10px;}
            .intro-org-table thead th:last-child{border-radius:0 10px 10px 0;}
            .intro-org-table tbody td{
              padding:10px 10px;
              background: rgba(19,28,50,.92);
              border-top:1px solid rgba(114,145,214,.16);
              border-bottom:1px solid rgba(114,145,214,.10);
              color:#F4F8FF;
              font-size:.92rem;
              vertical-align: middle;
            }
            .intro-org-table tbody tr td:first-child{
              border-radius:12px 0 0 12px;
              width:68px;
              font-weight:700;
            }
            .intro-org-table tbody tr td:last-child{border-radius:0 12px 12px 0;}
            .org-rank-badge{
              display:inline-flex; align-items:center; justify-content:center;
              min-width:34px; height:28px; border-radius:999px;
              font-weight:800; font-size:.86rem;
              border:1px solid rgba(255,255,255,.18);
              background: rgba(255,255,255,.06);
              color:#EAF1FF;
            }
            .org-rank-top1{ background: linear-gradient(135deg,#7A5A00,#D9B342); color:#FFF8DA; border-color:#E8CF75; }
            .org-rank-top2{ background: linear-gradient(135deg,#4B5563,#AEB7C2); color:#F5F7FA; border-color:#C9D0D8; }
            .org-rank-top3{ background: linear-gradient(135deg,#5D3D1E,#C9853A); color:#FFF1DF; border-color:#E3AE72; }
            .org-name-cell{font-weight:700; color:#FFFFFF; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;}
            .org-num-strong{font-weight:800; color:#79F2B0;}
            .org-subtle{color:#C5D5FB; font-size:.82rem;}
            .org-rate-wrap{
              display:flex; align-items:center; gap:8px;
            }
            .org-rate-bar{
              flex:1; min-width:110px; height:10px; border-radius:999px;
              background: rgba(255,255,255,.08);
              overflow:hidden; border:1px solid rgba(255,255,255,.06);
            }
            .org-rate-fill{
              height:100%;
              background: linear-gradient(90deg, #2BD676, #83F1FF);
              box-shadow: 0 0 12px rgba(43,214,118,.35);
            }
            .org-rate-text{min-width:48px; text-align:right; font-weight:700; color:#EFFFF7; font-size:.86rem;}
        .map-pollen-overlay{
            position:absolute; inset:0; pointer-events:none; overflow:hidden;
            border-radius:14px;
        }
        .map-pollen-overlay .pollen-dot{
            position:absolute;
            border-radius:50%;
            background: radial-gradient(circle, rgba(255,244,169,.95) 0%, rgba(255,220,101,.55) 48%, rgba(255,220,101,0) 72%);
            box-shadow:0 0 14px rgba(255,221,102,.35);
            animation: pollenFloat 5s ease-in-out forwards;
            opacity:0;
        }
        .map-fade-wrap.celebrate{
            box-shadow: 0 0 0 1px rgba(255,227,130,.22), 0 10px 28px rgba(255,221,102,.12);
        }
        @keyframes pollenFloat{
            0%{ transform:translateY(12px) scale(.85); opacity:0; }
            10%{ opacity:.95; }
            65%{ opacity:.88; }
            100%{ transform:translateY(-42px) scale(1.18); opacity:0; }
        }
        .stage-clear-banner{ animation: stageClearPulse .9s ease-in-out 2; }
        @keyframes stageClearPulse{
            0%{ transform:scale(0.995); box-shadow:0 0 0 rgba(0,0,0,0); }
            50%{ transform:scale(1.01); box-shadow:0 8px 18px rgba(59,130,246,.16); }
            100%{ transform:scale(1); box-shadow:0 0 0 rgba(0,0,0,0); }
        }
        .retry-offer-card{
            margin: 10px 0 10px 0;
            padding: 14px 16px;
            border-radius: 14px;
            border:1px solid rgba(255,214,102,.35);
            background: linear-gradient(180deg, rgba(38,31,10,.78), rgba(19,22,33,.88));
            box-shadow: 0 8px 24px rgba(0,0,0,.22);
            text-align: center;
        }
        .retry-offer-title{ color:#FFE7A0; font-weight:800; font-size:1.03rem; margin-bottom:6px; }
        .retry-offer-body{ color:#F3F7FF; font-size:.94rem; margin-bottom:4px; }
        .retry-offer-desc{ color:#DCE8FF; font-size:.90rem; line-height:1.45; margin-bottom:6px; }
        .retry-offer-note{ color:#BFD1F6; font-size:.82rem; }
            </style>
            """,
            unsafe_allow_html=True,
        )

        rows_html = []
        for _, row in merged.iterrows():
            rank = int(row.get("rank", 0) or 0)
            org_name = html.escape(str(row.get("organization", "미분류")))
            cum = int(round(float(row.get("cumulative_score", 0) or 0)))
            avg = float(row.get("avg_score", 0) or 0.0)
            p_cnt = int(row.get("participant_count", 0) or 0)
            total_emp = int(row.get("total_employees", 0) or 0)
            rate = row.get("participation_rate", np.nan)
            has_rate = pd.notna(rate)
            rate_val = float(rate) if has_rate else 0.0
            rate_pct = max(0.0, min(100.0, rate_val))
            rank_cls = "org-rank-badge"
            if rank == 1:
                rank_cls += " org-rank-top1"
            elif rank == 2:
                rank_cls += " org-rank-top2"
            elif rank == 3:
                rank_cls += " org-rank-top3"
            if rank <= 3:
                rank_label = {1: "🥇1", 2: "🥈2", 3: "🥉3"}[rank]
            else:
                rank_label = str(rank)

            participant_label = f"{p_cnt}명"
            if total_emp > 0:
                participant_label = f"{p_cnt} / {total_emp}명"

            rate_display = f"{rate_val:.1f}%" if has_rate else "-"

            rows_html.append(
                f"""
                <tr>
                  <td><span class="{rank_cls}">{rank_label}</span></td>
                  <td class="org-name-cell" title="{org_name}">{org_name}</td>
                  <td><span class="org-num-strong">{cum:,}점</span></td>
                  <td>{avg:.1f}점</td>
                  <td>{participant_label}<div class="org-subtle">참여자수</div></td>
                  <td>
                    <div class="org-rate-wrap">
                      <div class="org-rate-bar"><div class="org-rate-fill" style="width:{rate_pct:.1f}%;"></div></div>
                      <div class="org-rate-text">{rate_display}</div>
                    </div>
                  </td>
                </tr>
                """
            )

        html_table = textwrap.dedent(
            f"""
            <div class="intro-org-board-wrap">
            <div class="intro-org-board-sub">메인 화면에서는 기관별 누적 현황 요약만 표시됩니다. 상세 로그/통계는 관리자 대시보드에서 확인하세요.</div>
            <table class="intro-org-table">
            <thead>
            <tr>
            <th style="width:68px;">순위</th>
            <th>기관명</th>
            <th style="width:140px;">누적 점수</th>
            <th style="width:140px;">참가자 평균점수</th>
            <th style="width:150px;">참여자 수</th>
            <th style="width:220px;">참여율</th>
            </tr>
            </thead>
            <tbody>
            {''.join(rows_html)}
            </tbody>
            </table>
            </div>
            """,
        ).strip()
        st.markdown(html_table, unsafe_allow_html=True)

    except Exception as e:
        st.info(f"기관별 누적 현황 표시 중 오류가 발생했습니다: {e}")


def render_admin_password_gate():
    st.markdown(
        """
        <div class='admin-lock'>
          <div style='font-weight:800; margin-bottom:4px;'>🔐 관리자 화면</div>
          <div style='font-size:0.9rem; color:#EADFC4;'>기관별 누적 대시보드 / 문항별 통계 / 전체 참가자 현황은 관리자 인증 후 확인할 수 있습니다.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    pwd = st.text_input("관리자 비밀번호", type="password", key="admin_pwd_input", placeholder="비밀번호 입력")
    c1, c2 = st.columns([2, 1])
    with c1:
        if st.button("관리자 인증", use_container_width=True):
            if pwd == ADMIN_PASSWORD:
                st.session_state.admin_authed = True
                try:
                    st.toast("관리자 인증 완료", icon="✅")
                except Exception:
                    pass
                st.rerun()
            else:
                st.error("비밀번호가 올바르지 않습니다.")
    with c2:
        if st.button("맵으로", use_container_width=True):
            if st.session_state.get("user_info"):
                st.session_state.stage = "map"
            else:
                st.session_state.stage = "intro"
            st.rerun()
    st.caption("※ 보안을 위해 실제 운영 시 환경변수 COMPLIANCE_ADMIN_PASSWORD 설정을 권장합니다.")


def _render_org_ranking_cards(org_summary: pd.DataFrame, top_n: int = 5):
    if org_summary.empty:
        st.info("기관 요약 데이터가 없습니다.")
        return
    top_df = org_summary.head(top_n).copy()
    st.markdown("#### 🏅 기관별 평균 점수 랭킹")
    for i, row in top_df.reset_index(drop=True).iterrows():
        pct = float(row.get("avg_score_rate", 0) or 0)
        st.markdown(
            f"""
            <div class='rank-card'>
              <div class='rank-title'>{i+1}. {row['organization']}</div>
              <div class='rank-bar'><div class='rank-fill' style='width:{max(0, min(100, pct))}%;'></div></div>
              <div class='rank-meta'>
                평균 점수율 {pct:.1f}% · 참여자 {int(row.get('participants', 0))}명 · 수료율 {float(row.get('completion_rate', 0) or 0):.1f}%
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_org_dashboard(compact: bool = False):
    st.markdown("### 🏢 기관별 참여/점수 대시보드")

    df, err = _load_log_df()
    if err:
        st.info(err)
        return

    snap = _build_participant_snapshot(df)
    participants = snap["participants"]
    participants_view = snap["participants_view"]
    org_summary = snap["org_summary"]

    if participants.empty:
        st.info("표시할 참여자 데이터가 없습니다.")
        return

    total_people = int(participants["learner_id"].nunique())
    completed_people = int(participants["is_completed"].sum())
    avg_score_all = float(participants["total_score"].mean()) if total_people else 0.0
    avg_completion_all = float(participants["completion_rate_q"].mean()) if total_people else 0.0

    st.markdown(
        f"""
        <div class='dash-grid'>
          <div class='dash-card'><div class='label'>참여자 수</div><div class='value'>{total_people}명</div></div>
          <div class='dash-card'><div class='label'>수료자 수</div><div class='value'>{completed_people}명</div></div>
          <div class='dash-card'><div class='label'>전체 평균 점수</div><div class='value'>{avg_score_all:.1f}/{TOTAL_SCORE}</div></div>
          <div class='dash-card'><div class='label'>전체 평균 진행률</div><div class='value'>{avg_completion_all:.1f}%</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c_left, c_right = st.columns([1.2, 1])
    with c_left:
        org_view = org_summary.copy()
        if not org_view.empty:
            org_view["latest_activity"] = pd.to_datetime(org_view["latest_activity"], errors="coerce").dt.strftime("%Y-%m-%d %H:%M").fillna("-")
            org_view = org_view.rename(columns={
                "organization": "기관",
                "participants": "참여자 수",
                "completed": "수료자 수",
                "completion_rate": "수료율(%)",
                "avg_score": "평균 점수",
                "avg_score_rate": "평균 점수율(%)",
                "avg_completion_rate": "평균 진행률(%)",
                "attempts_started": "참여 회차 수",
        "completed_attempts": "완료 회차 수",
        "total_attempts": "누적 제출 수",
                "latest_activity": "최근 참여",
            })
            safe_dataframe(org_view, use_container_width=True, height=280 if compact else None)

            chart_df = org_view[["기관", "평균 점수율(%)"]].set_index("기관")
            safe_bar_chart(chart_df)
        else:
            st.info("기관 집계 데이터가 없습니다.")

    with c_right:
        _render_org_ranking_cards(org_summary, top_n=5 if not compact else 3)

    if compact:
        return

    st.markdown("#### 👥 참가자 누적 현황")
    org_filter_options = ["전체"] + sorted([x for x in participants_view["organization"].dropna().astype(str).unique().tolist() if x])
    selected_org = st.selectbox("기관 필터", org_filter_options, key="org_dashboard_filter")

    p_view = participants_view.copy()
    if selected_org != "전체":
        p_view = p_view[p_view["organization"] == selected_org]

    p_view["employee_no"] = p_view.get("employee_no", "").fillna("").astype(str).replace("", "-")
    p_view = p_view.rename(columns={
        "employee_no": "사번",
        "organization": "기관",
        "name": "이름",
        "status": "상태",
        "total_score": "총점",
        "score_rate": "점수율(%)",
        "answered_questions": "제출 문항수",
        "completed_themes": "완료 테마수",
        "completion_rate_q": "문항 진행률(%)",
        "total_attempts": "누적 제출 수",
        "last_activity": "최근 참여",
    })
    show_cols = ["사번", "기관", "이름", "상태", "총점", "점수율(%)", "참여 회차 수", "완료 회차 수", "완료 테마수", "제출 문항수", "문항 진행률(%)", "누적 제출 수", "최근 참여"]
    safe_dataframe(p_view[show_cols], use_container_width=True)

    csv_bytes = p_view[show_cols].to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
    st.download_button(
        "📥 참가자 현황 CSV 다운로드",
        data=csv_bytes,
        file_name=f"participants_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        use_container_width=True,
    )


def render_admin_page():
    st.title("🔐 관리자 대시보드")

    if not st.session_state.get("admin_authed", False):
        render_admin_password_gate()
        return

    st.success("관리자 인증 완료")
    c1, c2, c3 = st.columns([1,1,1])
    with c1:
        if st.button("🗺️ 맵으로 돌아가기", use_container_width=True):
            st.session_state.stage = "map" if st.session_state.get("user_info") else "intro"
            st.rerun()
    with c2:
        if st.button("🏠 첫 화면", use_container_width=True):
            st.session_state.stage = "intro"
            st.rerun()
    with c3:
        if st.button("🔓 로그아웃", use_container_width=True):
            st.session_state.admin_authed = False
            st.rerun()

    tab1, tab2, tab3 = st.tabs(["🏢 기관 대시보드", "🧠 문항 통계", "📄 로그 관리"])

    with tab1:
        render_org_dashboard(compact=False)

    with tab2:
        try:
            render_admin_question_stats()
        except Exception as e:
            st.error(f"문항 통계 탭 오류: {e}")
            if st.button("🛠 로그 스키마 자동 복구 시도", key="repair_log_from_tab2", use_container_width=True):
                try:
                    _ensure_log_schema_file()
                    st.success("로그 스키마 복구를 시도했습니다. 다시 열어보세요.")
                except Exception as ee:
                    st.error(f"복구 실패: {ee}")

    with tab3:
        try:
            df, err = _load_log_df()
            if err:
                st.info(err)
            else:
                st.write(f"누적 로그 건수: {len(df):,}건")
                if "organization" in df.columns:
                    st.write("기관별 로그 건수")
                    cnt = df["organization"].fillna("미분류").value_counts().reset_index()
                    cnt.columns = ["기관", "로그 건수"]
                    safe_dataframe(cnt, use_container_width=True)
                safe_dataframe(df.tail(200), use_container_width=True, height=320)
                st.download_button(
                    "📥 전체 로그 CSV 다운로드",
                    data=df.to_csv(index=False).encode("utf-8-sig"),
                    file_name=f"compliance_training_full_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
            st.caption("로그 파일이 과거 버전과 섞여 있어도 자동 복구를 시도합니다.")
            if st.button("🛠 로그 스키마 재정렬(복구)", key="repair_log_from_tab3", use_container_width=True):
                try:
                    _ensure_log_schema_file()
                    st.success("로그 스키마를 현재 버전 형식으로 재정렬했습니다.")
                except Exception as ee:
                    st.error(f"복구 실패: {ee}")
        except Exception as e:
            st.error(f"로그 관리 탭 오류: {e}")

def render_admin_question_stats():
    st.markdown("### 🛠 관리자용 문항별 정답률 통계")

    df, err = _load_log_df()
    if err:
        st.info(err)
        return

    df = _coerce_log_df(df)
    if df.empty:
        st.info("로그 데이터가 비어 있습니다.")
        return

    def _is_correct_norm(row):
        qtype = str(row.get("question_type", "")).lower()
        is_correct = str(row.get("is_correct", "")).upper()
        if qtype == "mcq":
            return is_correct == "Y"
        max_score = float(row.get("max_score", 0) or 0)
        awarded = float(row.get("awarded_score", 0) or 0)
        ratio = (awarded / max_score) if max_score > 0 else 0
        return ratio >= TEXT_CORRECT_THRESHOLD

    df["is_correct_norm"] = df.apply(_is_correct_norm, axis=1)

    emp_series = df["employee_no"].astype(str).fillna("") if "employee_no" in df.columns else pd.Series([""] * len(df))
    name_series = df["name"].astype(str) if "name" in df.columns else pd.Series([""] * len(df))
    org_series = df["organization"].astype(str) if "organization" in df.columns else pd.Series([""] * len(df))
    df["learner_key"] = emp_series.where(emp_series.str.strip() != "", name_series + "|" + org_series)

    qidx_src = df["question_index"] if "question_index" in df.columns else pd.Series([0]*len(df))
    if isinstance(qidx_src, pd.DataFrame):
        qidx_src = qidx_src.iloc[:, 0]
    qidx = pd.to_numeric(qidx_src, errors="coerce").fillna(0).astype(int)
    mtitle_src = df["mission_title"] if "mission_title" in df.columns else pd.Series(["미상 테마"] * len(df))
    if isinstance(mtitle_src, pd.DataFrame):
        mtitle_src = mtitle_src.iloc[:, 0]
    mtitle = mtitle_src.astype(str)
    df["question_label"] = mtitle + " · Q" + qidx.astype(str)

    blank_qc = df["question_code"].astype(str).str.strip() == ""
    df.loc[blank_qc, "question_code"] = (
        df.loc[blank_qc, "mission_key"].astype(str) + "_Q" + qidx.loc[blank_qc].astype(str)
    )

    stat_df = df[df["question_code"].astype(str).str.strip() != ""].copy()
    if stat_df.empty:
        st.info("문항 통계를 만들 수 있는 로그가 없습니다.")
        return

    attempt_stats = (
        stat_df.groupby(["question_code", "question_label"], as_index=False)
        .agg(
            attempts=("is_correct_norm", "count"),
            corrects=("is_correct_norm", "sum"),
            avg_score=("awarded_score", "mean"),
            max_score=("max_score", "max"),
        )
    )
    attempt_stats["attempt_correct_rate"] = (
        attempt_stats["corrects"] / attempt_stats["attempts"].replace(0, 1) * 100
    ).round(1)

    df_sorted = stat_df.sort_values("timestamp", ascending=True)
    first_attempt_df = df_sorted.drop_duplicates(subset=["learner_key", "question_code"], keep="first")

    first_stats = (
        first_attempt_df.groupby(["question_code"], as_index=False)
        .agg(
            first_attempts=("is_correct_norm", "count"),
            first_corrects=("is_correct_norm", "sum"),
        )
    )
    first_stats["first_correct_rate"] = (
        first_stats["first_corrects"] / first_stats["first_attempts"].replace(0, 1) * 100
    ).round(1)

    stats = attempt_stats.merge(first_stats, on="question_code", how="left")
    stats["avg_score_rate"] = ((stats["avg_score"] / stats["max_score"].replace(0, 1)) * 100).round(1)
    stats = stats.sort_values(["question_code"]).reset_index(drop=True)

    view_cols = [
        "question_label",
        "attempts",
        "attempt_correct_rate",
        "first_attempts",
        "first_correct_rate",
        "avg_score_rate",
    ]
    rename_map = {
        "question_label": "문항",
        "attempts": "전체 제출 수",
        "attempt_correct_rate": "전체 정답률(%)",
        "first_attempts": "첫 시도 수",
        "first_correct_rate": "첫 시도 정답률(%)",
        "avg_score_rate": "평균 점수율(%)",
    }
    view_df = stats[view_cols].rename(columns=rename_map)

    safe_dataframe(view_df, use_container_width=True)
    if not view_df.empty:
        chart_df = view_df[["문항", "첫 시도 정답률(%)"]].copy().set_index("문항")
        safe_bar_chart(chart_df)

    st.caption(
        f"※ 주관식은 점수율 {int(TEXT_CORRECT_THRESHOLD*100)}% 이상을 '정답'으로 집계합니다. "
        "임계값은 TEXT_CORRECT_THRESHOLD로 조정할 수 있습니다."
    )

# =========================================================
# 6) UI 조각들

# =========================================================
# 6) UI 조각들 (맵, 브리핑, 퀴즈)
# =========================================================

def render_conquer_fx_if_needed():
    if not st.session_state.get("show_conquer_fx", False):
        return
    if st.session_state.get("map_fx_done", False):
        return

    pending_theme = st.session_state.get("last_cleared_mission")
    is_final_clear = len(st.session_state.get("completed", [])) >= len(SCENARIO_ORDER)

    if is_final_clear:
        msg = "🏁 최종 테마 정복 완료!"
        style = "border:1px solid rgba(250,204,21,.45); background: linear-gradient(90deg, rgba(250,204,21,.14), rgba(59,130,246,.10)); color:#FFF6D8;"
    else:
        title = SCENARIOS.get(str(pending_theme), {}).get("title", "테마")
        title_plain = title.split(" ", 1)[1] if " " in title else title
        msg = f"✨ {html.escape(title_plain)} 정복 완료! 가디언 맵이 업데이트되었습니다."
        style = "border:1px solid rgba(74, 222, 128, .35); background: linear-gradient(90deg, rgba(16,185,129,.12), rgba(59,130,246,.08)); color:#EAFBF1;"

    st.markdown(
        f"""
        <div class="stage-clear-banner" style="margin:6px 0 12px 0; padding:10px 14px; border-radius:12px; {style} font-weight:700;">
            {msg}
        </div>
        """,
        unsafe_allow_html=True,
    )

    try:
        st.toast("🏁 최종 테마 정복 완료!" if is_final_clear else "가디언 맵 업데이트!", icon="🎉" if is_final_clear else "🗺️")
    except Exception:
        pass
    try:
        st.balloons()
    except Exception:
        pass

    st.session_state.map_fx_done = True
    st.session_state.show_conquer_fx = False


def render_guardian_map():
    st.subheader("🗺️ Guardian’s Map")

    map_img = get_current_map_image()
    cleared_cnt = len(st.session_state.get("completed", []))
    stage_idx = min(cleared_cnt, 3)

    celebrate = float(st.session_state.get("map_celebrate_until", 0) or 0) > float(time.time())
    if map_img:
        show_map_with_fade(map_img, caption=f"현재 맵 단계: world_map_{stage_idx}.png", celebrate=celebrate)
    else:
        st.warning("맵 이미지가 없습니다. world_map_0~3.png 경로를 확인해주세요.")
        return

    total_themes = len(SCENARIO_ORDER)
    st.progress(cleared_cnt / total_themes if total_themes else 0)
    st.caption(f"정복 진행률: {cleared_cnt} / {total_themes}")

    status_labels = []
    for m_key in SCENARIO_ORDER:
        title = SCENARIOS[m_key]["title"]
        score = st.session_state.get("mission_scores", {}).get(m_key)
        if m_key in st.session_state.get("completed", []):
            txt = f"✅ {title}"
            if score is not None:
                txt += f" ({score}/{theme_max_score(m_key)})"
        else:
            idx = SCENARIO_ORDER.index(m_key)
            if idx == 0 or SCENARIO_ORDER[idx - 1] in st.session_state.get("completed", []):
                txt = f"🟡 {title}"
            else:
                txt = f"🔒 {title}"
        status_labels.append(txt)

    st.caption(" · ".join(status_labels))


def render_briefing(m_key: str):
    mission = SCENARIOS[m_key]
    brief = mission["briefing"]

    st.markdown(
        f"<div class='mission-header'><div style='font-size:1.1rem; font-weight:800;'>{mission['title']} · 브리핑</div></div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class='card'>
          <div class='card-title'>📘 {brief['title']}</div>
          <div>{brief['summary']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    chips = "".join([f"<span class='brief-chip'>{k}</span>" for k in brief["keywords"]])
    st.markdown(f"<div style='margin-bottom:10px;'>{chips}</div>", unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1], gap='large')
    with col1:
        red_html = "".join([f"<li>{x}</li>" for x in brief["red_flags"]])
        st.markdown(
            f"""
            <div class='brief-box'>
              <div class='brief-title'>🚨 Red Flags</div>
              <ul>{red_html}</ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        chk_html = "".join([f"<li>{x}</li>" for x in brief["checklist"]])
        st.markdown(
            f"""
            <div class='brief-box'>
              <div class='brief-title'>✅ 실무 체크리스트</div>
              <ul>{chk_html}</ul>
            </div>
            """,
            unsafe_allow_html=True,
        )


    st.markdown("<div class='brief-actions-wrap'></div>", unsafe_allow_html=True)
    c1, c2 = st.columns([1, 1], gap='large')
    with c1:
        if st.button("📝 퀴즈 시작", use_container_width=True):
            st.session_state.stage = "quiz"
            st.rerun()
    with c2:
        if st.button("🗺️ 맵으로 돌아가기", use_container_width=True):
            st.session_state.current_mission = None
            st.session_state.stage = "map"
            st.rerun()


def render_mcq_question(m_key: str, q_idx: int, q_data: dict):
    ensure_quiz_progress(m_key)
    progress = st.session_state.quiz_progress[m_key]
    submissions = progress["submissions"]

    if q_idx in submissions:
        res = submissions[q_idx]
        if res["is_correct"] == "Y":
            st.success(f"✅ 정답 ({res['awarded_score']}/{q_data['score']}점)")
        else:
            st.error(f"❌ 오답 ({res['awarded_score']}/{q_data['score']}점)")

        st.markdown(
            f"""
            <div class='card'>
              <div class='card-title'>선택한 답변</div>
              <div>{res['selected_text']}</div>
              <hr style="border-color:#2A3140;">
              <div><b>선택지 설명</b><br>{res['choice_feedback']}</div>
              <div style="margin-top:8px;"><b>핵심 해설</b><br>{res['explain']}</div>
              {"<div style='margin-top:8px; color:#FFCC80;'><b>오답 보완 포인트</b><br>" + res['wrong_extra'] + "</div>" if res['is_correct']=='N' else ''}
            </div>
            """,
            unsafe_allow_html=True,
        )

        c_edit, c_hint = st.columns([1.1, 1.9])
        with c_edit:
            if st.button("✏️ 답안 수정하기", key=f"edit_mcq_{m_key}_{q_idx}", use_container_width=True):
                submissions.pop(q_idx, None)
                st.rerun()
        with c_hint:
            st.caption("이전/다음 문제 버튼으로 이동할 수 있습니다. 수정 후 다시 제출하면 최신 답안 기준으로 점수가 반영됩니다.")
        return

    q_text = html.escape(str(q_data['question']))
    st.markdown(
        f"""
        <div class='quiz-question-box'>
          <div class='quiz-question-kicker'>QUESTION {q_idx+1}</div>
          <div class='quiz-question-title'>Q{q_idx+1}. {q_text}</div>
        </div>
        <div class='quiz-help-text'>아래 보기 중 가장 적절한 답을 선택하세요.</div>
        """,
        unsafe_allow_html=True,
    )
    selected = st.radio(
        "답을 선택하세요",
        options=list(range(len(q_data["options"]))),
        format_func=lambda i: q_data["options"][i],
        key=f"radio_{m_key}_{q_idx}",
    )

    if st.button("제출하기", key=f"submit_mcq_{m_key}_{q_idx}", use_container_width=True):
        is_correct = selected == q_data["answer"]
        awarded = q_data["score"] if is_correct else 0
        st.session_state.attempt_counts[m_key] = st.session_state.attempt_counts.get(m_key, 0) + 1

        result = {
            "question_type": "mcq",
            "is_correct": "Y" if is_correct else "N",
            "awarded_score": awarded,
            "selected_idx": selected,
            "selected_text": q_data["options"][selected],
            "choice_feedback": q_data["choice_feedback"][selected],
            "explain": q_data["explain"],
            "wrong_extra": q_data["wrong_extra"],
        }
        submissions[q_idx] = result

        queue_sfx("correct" if is_correct else "wrong")
        try:
            st.toast("정답입니다!" if is_correct else "다시 생각해보세요", icon="✨" if is_correct else "⚠️")
        except Exception:
            pass

        append_attempt_log(
            mission_key=m_key,
            q_idx=q_idx,
            q_type="mcq",
            payload={
                "selected_or_text": q_data["options"][selected],
                "is_correct": "Y" if is_correct else "N",
                "awarded_score": awarded,
            },
        )
        st.rerun()


def render_text_question(m_key: str, q_idx: int, q_data: dict):
    ensure_quiz_progress(m_key)
    progress = st.session_state.quiz_progress[m_key]
    submissions = progress["submissions"]

    if q_idx in submissions:
        res = submissions[q_idx]
        st.success(f"📝 주관식 평가 완료 ({res['awarded_score']}/{q_data['score']}점)")

        if res["quality"] == "good":
            quality_badge = "좋아요 ✅"
        elif res["quality"] == "partial":
            quality_badge = "부분 충족 ☑️"
        else:
            quality_badge = "답변 필요 ✍️"

        found_text = ", ".join(res["found_groups"]) if res["found_groups"] else "없음"
        missing_text = ", ".join(res["missing_groups"]) if res["missing_groups"] else "없음"

        breakdown_lines = []
        for item in res.get("score_breakdown", []) or []:
            matched = ", ".join(item.get("matched", [])) if item.get("matched") else "미반영"
            breakdown_lines.append(f"• {item.get('group')} ({item.get('earned', 0)}/{item.get('weight', 0)}점): {matched}")
        breakdown_html = "<br>".join(html.escape(x) for x in breakdown_lines) if breakdown_lines else ""

        st.markdown(
            f"""
            <div class='card'>
              <div class='card-title'>내 답안</div>
              <div>{res['answer_text'] if res['answer_text'] else '(비어 있음)'}</div>
              <hr style="border-color:#2A3140;">
              <div><b>평가 결과</b> · {quality_badge}</div>
              <div style="margin-top:6px;"><b>잘 반영한 요소</b>: {found_text}</div>
              <div style="margin-top:4px;"><b>보완 포인트</b>: {missing_text}</div>
              {f"<div style='margin-top:8px;'><b>세부 배점</b><br>{breakdown_html}</div>" if breakdown_html else ""}
            </div>
            """,
            unsafe_allow_html=True,
        )

        toggle_key = f"show_model_answer_{m_key}_{q_idx}"
        if toggle_key not in st.session_state:
            st.session_state[toggle_key] = False

        c_ma_btn, c_ma_sp = st.columns([1.0, 2.0])
        with c_ma_btn:
            if st.button("모범답안 보기", key=f"btn_{toggle_key}", use_container_width=True):
                st.session_state[toggle_key] = not st.session_state[toggle_key]

        if st.session_state.get(toggle_key, False):
            model_answer_text = html.escape(str(q_data.get("model_answer", ""))).replace('\n', '<br>')
            st.markdown(
                f"""
                <div class='card'>
                  <div class='card-title'>📘 모범답안</div>
                  <div style='line-height:1.6; color:#F4F7FF;'>{model_answer_text}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        c_edit, c_hint = st.columns([1.1, 1.9])
        with c_edit:
            if st.button("✏️ 답안 수정하기", key=f"edit_text_{m_key}_{q_idx}", use_container_width=True):
                submissions.pop(q_idx, None)
                st.rerun()
        with c_hint:
            st.caption("이전/다음 문제 버튼으로 이동할 수 있습니다. 수정 후 다시 제출하면 최신 답안 기준으로 점수가 반영됩니다.")
        return

    q_text = html.escape(str(q_data['question']))
    st.markdown(
        f"""
        <div class='quiz-question-box'>
          <div class='quiz-question-kicker'>QUESTION {q_idx+1}</div>
          <div class='quiz-question-title'>Q{q_idx+1}. {q_text}</div>
        </div>
        <div class='quiz-help-text'>원칙을 설명하고, 가능한 대안이나 후속 조치를 함께 적어보세요.</div>
        """,
        unsafe_allow_html=True,
    )
    sample_answer = get_text_question_sample_answer(q_data)
    if sample_answer:
        st.markdown(
            f"""
            <div class='card'>
              <div class='card-title'>🧩 Sample Answer (예시)</div>
              <div style='line-height:1.55;'>{sample_answer}</div>
              <div style='margin-top:8px; color:#B7C7E6; font-size:0.88rem;'>
                ※ 예시는 작성 방향(원칙 설명 + 대안 제시)을 보여주는 참고 문장입니다. 그대로 복사하지 말고 본인 표현으로 바꿔 작성하세요.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    answer_text = st.text_area(
        "답안을 입력하세요",
        key=f"text_{m_key}_{q_idx}",
        height=150,
        placeholder=(sample_answer if sample_answer else "예: 원칙을 설명하고, 가능한 대안(보고/확인/절차)을 함께 적어보세요."),
    )

    if st.button("제출하기", key=f"submit_text_{m_key}_{q_idx}", use_container_width=True):
        if is_near_copy_answer(answer_text, q_data.get("sample_answer", ""), q_data.get("model_answer", "")):
            st.warning("예시/모범답안 문장을 그대로 복사한 답안은 제출할 수 없습니다. 같은 뜻이어도 본인 표현으로 바꿔 작성해주세요.")
            return

        eval_res = evaluate_text_answer(answer_text, q_data["rubric_keywords"], q_data["score"])
        st.session_state.attempt_counts[m_key] = st.session_state.attempt_counts.get(m_key, 0) + 1

        result = {
            "question_type": "text",
            "is_correct": "PARTIAL" if eval_res["awarded_score"] < q_data["score"] else "Y",
            "awarded_score": eval_res["awarded_score"],
            "answer_text": answer_text.strip(),
            "found_groups": eval_res["found_groups"],
            "missing_groups": eval_res["missing_groups"],
            "quality": eval_res["quality"],
            "score_breakdown": eval_res.get("score_breakdown", []),
        }
        submissions[q_idx] = result

        ratio = (eval_res["awarded_score"] / q_data["score"]) if q_data["score"] else 0
        is_good = ratio >= TEXT_CORRECT_THRESHOLD
        queue_sfx("correct" if is_good else "wrong")
        try:
            st.toast("주관식 답안이 잘 작성되었어요!" if is_good else "보완 포인트를 확인해보세요", icon="✨" if is_good else "⚠️")
        except Exception:
            pass

        append_attempt_log(
            mission_key=m_key,
            q_idx=q_idx,
            q_type="text",
            payload={
                "selected_or_text": answer_text.strip(),
                "is_correct": result["is_correct"],
                "awarded_score": eval_res["awarded_score"],
            },
        )
        st.rerun()



def render_quiz_navigation_controls(m_key: str):
    """퀴즈 이전/다음 + 스테이지 제출 버튼.
    - Stage 1~2: 제출 시 3초 팝업 후 자동 다음 스테이지로 이동
    - Stage 3: 제출 시 최종 제출(YES) / 재도전(Try again) 선택 팝업
    """
    ensure_quiz_progress(m_key)
    progress = st.session_state.quiz_progress[m_key]
    q_list = SCENARIOS[m_key]["quiz"]
    total_q = len(q_list)
    idx = int(progress.get("current_idx", 0))
    submissions = progress.get("submissions", {})
    current_submitted = idx in submissions

    st.markdown("<div class='quiz-nav-wrap'></div>", unsafe_allow_html=True)
    if current_submitted:
        st.markdown("<div class='quiz-nav-hint'>제출 완료된 문항입니다. 이전 문항으로 돌아가 답안을 수정하거나 다음 문항으로 이동할 수 있습니다.</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='quiz-nav-hint'>먼저 현재 문항을 제출한 뒤 다음 문항으로 이동할 수 있습니다.</div>", unsafe_allow_html=True)

    c1, c2 = st.columns([1, 1], gap='large')
    with c1:
        if st.button("◀ 이전 문제", key=f"nav_prev_{m_key}_{idx}", use_container_width=True, disabled=(idx <= 0)):
            progress["current_idx"] = max(0, idx - 1)
            st.rerun()
    with c2:
        if idx < total_q - 1:
            if st.button("다음 문제 ▶", key=f"nav_next_{m_key}_{idx}", use_container_width=True, disabled=(not current_submitted)):
                progress["current_idx"] = min(total_q - 1, idx + 1)
                st.rerun()
        else:
            all_submitted = len(submissions) == total_q
            if st.button("✅ 스테이지 제출", key=f"nav_submit_stage_{m_key}", use_container_width=True, disabled=(not all_submitted)):
                info = finalize_theme_if_ready(m_key)
                if not info.get("ready"):
                    st.warning("아직 모든 문항이 제출되지 않았습니다.")
                    st.stop()

                # Stage 번호 및 다음 스테이지 결정
                stage_num = SCENARIO_ORDER.index(m_key) + 1
                user = st.session_state.get("user_info", {})
                name = str(user.get("name", "") or "참가자")
                stage_name = STAGE_DISPLAY_NAMES.get(m_key, SCENARIOS[m_key].get("territory_name", SCENARIOS[m_key].get("title", m_key)))

                if stage_num < len(SCENARIO_ORDER):
                    next_key = SCENARIO_ORDER[stage_num]  # 다음 스테이지 key
                    st.session_state.stage_transition = {
                        "kind": "auto_next",
                        "stage_num": stage_num,
                        "theme_key": m_key,
                        "stage_name": stage_name,
                        "name": name,
                        "score_10": int(info.get("scaled_10", 0)),
                        "max_10": 10,
                        "next_key": next_key,
                    }
                    st.session_state.stage = "stage_transition"
                    st.rerun()
                else:
                    # 마지막 스테이지: 최종 제출 여부 팝업
                    award_participation_points_if_needed()
                    st.session_state.stage_transition = {
                        "kind": "final_prompt",
                        "stage_num": stage_num,
                        "theme_key": m_key,
                        "stage_name": stage_name,
                        "name": name,
                        "total_score": int(st.session_state.get("score", 0) or 0),
                    }
                    st.session_state.stage = "final_prompt"
                    st.rerun()


def render_quiz(m_key: str):

    mission = SCENARIOS[m_key]
    ensure_quiz_progress(m_key)

    progress = st.session_state.quiz_progress[m_key]
    q_list = mission["quiz"]
    if progress["current_idx"] >= len(q_list):
        progress["current_idx"] = len(q_list) - 1

    current_idx = progress["current_idx"]
    q_data = q_list[current_idx]
    current_theme_score = theme_score_from_submissions(m_key)
    submitted_count = len(progress["submissions"])
    theme_icon = THEME_ICONS.get(m_key, "🧭")

    st.markdown(
        f"""
        <div class='mission-header'>
          <div style='font-size:1.05rem; font-weight:800;'>{theme_icon} {mission['title']} · 퀴즈</div>
          <div style='margin-top:4px; font-size:0.9rem; opacity:.92;'>문항 진행: {submitted_count} / {len(q_list)} · 테마 점수(누적): {current_theme_score}/{theme_max_score(m_key)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 15인치 노트북 기준 가독성을 고려해 좌/우 비율과 여백을 조금 넉넉하게 조정
    col_left, col_right = st.columns([1.05, 1.95], gap='large')
    with col_left:
        st.markdown(
            """
            <div class='card' style='margin-bottom:10px;'>
              <div class='card-title'>안내 캐릭터</div>
              <div style='color:#D0DCF2; font-size:0.92rem; line-height:1.45;'>문항 옆에서 핵심 포인트를 함께 확인해보세요.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if MASTER_IMAGE.exists():
            img_c1, img_c2, img_c3 = st.columns([0.05, 0.90, 0.05])
            with img_c2:
                st.image(str(MASTER_IMAGE), use_container_width=True)
            st.markdown("<div class='quiz-left-caption'>클린 마스터</div>", unsafe_allow_html=True)
        else:
            st.info("클린 마스터 이미지 없음")

        st.markdown(
            """
            <div class='card quiz-side-tip'>
              <div class='card-title'>진행 팁</div>
              <div>정답 여부보다 <b>왜 그런지</b>를 이해하는 게 핵심이에요.</div>
              <div style='margin-top:6px; color:#C7D7F2;'>보기/해설을 읽고 현업 상황에 어떻게 적용할지 같이 생각해보세요.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("🗺️ 맵으로 나가기", key=f"back_map_{m_key}", use_container_width=True):
            st.session_state.stage = "map"
            st.rerun()

    with col_right:
        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
        if q_data["type"] == "mcq":
            render_mcq_question(m_key, current_idx, q_data)
        elif q_data["type"] == "text":
            render_text_question(m_key, current_idx, q_data)
        else:
            st.error("지원하지 않는 문항 타입입니다.")

        # 제출 버튼과 너무 붙지 않도록 하단 여백 + 내비게이션 제공
        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
        render_quiz_navigation_controls(m_key)

# =========================================================
# 7) 메인 화면 분기
# =========================================================
init_state()
render_audio_system()

with st.sidebar:
    st.checkbox("🔊 배경음악 재생", key="bgm_enabled")
    st.markdown("---")
    st.caption("관리자")
    if st.button("🔐 관리자 대시보드", use_container_width=True):
        st.session_state.stage = "admin"
        st.rerun()
    if st.session_state.get("admin_authed", False):
        if st.button("🔓 관리자 로그아웃", use_container_width=True):
            st.session_state.admin_authed = False
            st.rerun()

if st.session_state.stage == "intro":
    render_top_spacer()

    intro_map = get_current_map_image()
    if intro_map:
        show_map_with_fade(intro_map)
    else:
        st.info("맵 이미지를 추가하면 인트로 연출이 더 좋아집니다.")

    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
    st.title("🛡️ 2026 Compliance Adventure")
    st.caption("Guardian Training · 컴플라이언스 테마 정복형 학습")

    st.markdown(
        """
        <div class='card'>
          <div class='card-title'>게임 방식</div>
          <div>맵에서 테마를 선택 → 핵심 브리핑 학습 → 퀴즈(4지선다 + 주관식) → 정복 완료!</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_intro_org_cumulative_board()

    emp_df, emp_meta_msg = load_employee_master_df()

    st.markdown("### 👤 참가자 확인")
    st.caption("사전에 업로드한 직원 명단을 기준으로 성명을 조회하고, 사번/소속기관을 확인한 뒤 시작합니다.")

    if emp_meta_msg:
        st.info(emp_meta_msg)

    name_query = st.text_input("성함 입력 (사번 조회)", key="intro_name_query", placeholder="예: 홍길동")
    c_lookup1, c_lookup2 = st.columns([2, 1])
    with c_lookup1:
        lookup_clicked = st.button("🔎 성명 조회", use_container_width=True)
    with c_lookup2:
        clear_clicked = st.button("초기화", use_container_width=True)

    if clear_clicked:
        st.session_state.employee_lookup_candidates = []
        st.session_state.employee_selected_record = None
        st.session_state.employee_lookup_modal_open = False
        st.rerun()

    if lookup_clicked:
        q = (name_query or "").strip()
        st.session_state.employee_selected_record = None
        st.session_state.employee_lookup_modal_open = False
        if not q:
            st.warning("성함을 입력한 뒤 조회해주세요.")
        elif emp_df is None or emp_df.empty:
            st.warning("직원 명단 파일을 찾지 못했습니다. app.py와 같은 폴더에 직원 명단 파일(csv/xlsx)을 넣어주세요.")
        else:
            exact = emp_df[emp_df["name"].astype(str).str.strip() == q].copy()
            partial = emp_df[emp_df["name"].astype(str).str.contains(q, case=False, na=False)].copy()
            candidates = exact if not exact.empty else partial
            st.session_state.employee_lookup_candidates = candidates.to_dict("records")
            if candidates.empty:
                st.warning("일치하는 성명이 없습니다. 성함을 다시 확인해주세요.")
            else:
                st.success(f"조회 결과 {len(candidates)}건 · 팝업에서 본인 정보를 확인해주세요.")
                st.session_state.employee_lookup_modal_open = True

    if st.session_state.get("employee_lookup_modal_open", False):
        render_employee_lookup_popup(name_query)
    elif st.session_state.get("employee_lookup_candidates"):
        st.caption("최근 조회 결과가 있습니다. 다시 확인하려면 아래 버튼을 누르세요.")
        if st.button("📋 조회 결과 팝업 다시 열기", use_container_width=True, key="reopen_employee_popup"):
            st.session_state.employee_lookup_modal_open = True
            st.rerun()

    selected_emp = st.session_state.get("employee_selected_record")
    if selected_emp:
        st.markdown("### ✅ 확인된 참가자 정보")
        col_a, col_b, col_c = st.columns(3)
        _render_confirm_readonly_field(col_a, "사번", selected_emp.get("employee_no", ""))
        _render_confirm_readonly_field(col_b, "이름", selected_emp.get("name", ""))
        _render_confirm_readonly_field(col_c, "소속 기관", selected_emp.get("organization", ""))

        st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
        if st.button("모험 시작하기", use_container_width=True):
            emp_no = str(selected_emp.get("employee_no", "")).strip()
            emp_name = str(selected_emp.get("name", "")).strip()
            emp_org = str(selected_emp.get("organization", "")).strip() or "미분류"
            if emp_name:
                user_info = {"employee_no": emp_no, "name": emp_name, "org": emp_org}
                hist = _summarize_user_attempts(emp_no, emp_name, emp_org)
                completed_attempts = int(hist.get("completed_attempts", 0) or 0)

                if completed_attempts >= 3:
                    st.error("이 참가자는 최대 참여 횟수(총 3회)를 모두 사용했습니다. 관리자에게 문의해주세요.")
                elif completed_attempts >= 1:
                    _set_retry_offer(user_info, completed_attempts, context="intro")
                    st.rerun()
                else:
                    start_training_attempt_session(user_info, attempt_round=1, skip_to_stage="map")
                    st.rerun()
            else:
                st.warning("참가자 확인 정보를 다시 선택해주세요.")

    render_retry_offer_box("intro")

elif st.session_state.stage == "map":
    render_top_spacer()
    user_name = st.session_state.user_info.get("name", "가디언")
    user_org = st.session_state.user_info.get("org", "")

    st.title(f"🗺️ {user_name} 가디언의 지도")
    cap_parts = []
    user_emp_no = st.session_state.user_info.get("employee_no", "")
    if user_emp_no:
        cap_parts.append(f"사번: {user_emp_no}")
    if user_org:
        cap_parts.append(f"소속 기관: {user_org}")
    if cap_parts:
        st.caption(" | ".join(cap_parts))

    render_guardian_map()

    st.write("관문을 선택하세요:")
    cols = st.columns(3)
    for i, m_key in enumerate(SCENARIO_ORDER):
        mission = SCENARIOS[m_key]
        status = get_theme_status(m_key)
        with cols[i]:
            if status == "clear":
                score = st.session_state.mission_scores.get(m_key, 0)
                _mx = max(theme_max_score(m_key), 1)
                _rt = score / _mx
                badge = "🏅" if _rt >= 0.9 else ("✅" if _rt >= 0.7 else "📘")
                st.success(f"{badge} {mission['title']}")
                st.caption(f"점수 {score}/{theme_max_score(m_key)}")
            elif status == "open":
                if st.button(f"{mission['title']} 진입", key=f"enter_{m_key}", use_container_width=True):
                    st.session_state.current_mission = m_key
                    ensure_quiz_progress(m_key)
                    st.session_state.stage = "briefing"
                    st.rerun()
            else:
                st.button("🔒 잠겨 있음", key=f"locked_{m_key}", disabled=True, use_container_width=True)

    st.write("---")
    st.markdown(
        f"""
        <div class='card'>
          <div class='card-title'>🏆 현재 점수</div>
          <div><b>{st.session_state.score} / {TOTAL_SCORE}</b> · 등급 예상: {get_grade(st.session_state.score, TOTAL_SCORE)}</div>
          <div style='font-size:0.88rem; opacity:.9;'>구성: 객관식 60점 + 주관식 30점 + 참여 10점</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if len(st.session_state.completed) == len(SCENARIO_ORDER):
        if st.button("최종 결과 보기", use_container_width=True):
            st.session_state.stage = "ending"
            st.rerun()

elif st.session_state.stage == "briefing":
    render_top_spacer()
    m_key = st.session_state.get("current_mission")
    if not m_key or m_key not in SCENARIOS:
        st.warning("테마 정보가 없어 지도로 돌아갑니다.")
        st.session_state.stage = "map"
        st.rerun()

    if m_key in st.session_state.completed:
        st.info("이미 정복한 테마입니다. 지도로 돌아갑니다.")
        st.session_state.stage = "map"
        st.rerun()

    render_briefing(m_key)

elif st.session_state.stage == "quiz":
    render_top_spacer()
    m_key = st.session_state.get("current_mission")
    if not m_key or m_key not in SCENARIOS:
        st.warning("퀴즈 정보가 없어 지도로 돌아갑니다.")
        st.session_state.stage = "map"
        st.rerun()
    ensure_quiz_progress(m_key)

    render_quiz(m_key)

elif st.session_state.stage == "admin":
    render_top_spacer()
    render_admin_page()


elif st.session_state.stage == "stage_transition":
    render_top_spacer()
    info = st.session_state.get("stage_transition") or {}
    # 자동 다음 스테이지 이동 팝업 (3초)
    if info.get("kind") != "auto_next":
        st.session_state.stage = "map"
        st.rerun()

    name = str(info.get("name") or "참가자")
    stage_num = int(info.get("stage_num") or 1)
    stage_name = str(info.get("stage_name") or "")
    score_10 = int(info.get("score_10") or 0)
    max_10 = int(info.get("max_10") or 10)

    title = f"{name} has cleared Stage {stage_num} \"{stage_name}\""
    body = f"Score: {score_10}/{max_10}"
    render_stage_popup_html(title=title, body=body, note="Moving to the next stage...")

    time.sleep(3)

    next_key = info.get("next_key")
    if next_key in SCENARIOS:
        st.session_state.current_mission = next_key
        ensure_quiz_progress(next_key)
        st.session_state.stage = "briefing"
    else:
        st.session_state.stage = "map"
    st.rerun()

elif st.session_state.stage == "final_prompt":
    render_top_spacer()
    info = st.session_state.get("stage_transition") or {}
    user = st.session_state.get("user_info", {})
    name = str(info.get("name") or user.get("name") or "참가자")
    total_score = int(info.get("total_score") or st.session_state.get("score", 0) or 0)

    # 중앙 대화상자(YES / Try again)
    @st.dialog("🏁 Final submission")
    def _final_submit_dialog():
        st.markdown(f"**{name}** cleared all stages with **{total_score}/100** points (including **{PARTICIPATION_SCORE} participation points**).")
        st.markdown("Do you want to submit the final score?")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Yes", use_container_width=True):
                st.session_state.stage = "ending"
                st.rerun()
        with c2:
            if st.button("Try again", use_container_width=True):
                # 마지막 도전 안내 후 Stage 1로 이동
                st.session_state.stage_transition = {"kind": "retry_transition", "name": name}
                st.session_state.stage = "retry_transition"
                st.rerun()

    _final_submit_dialog()
    st.stop()

elif st.session_state.stage == "retry_transition":
    render_top_spacer()
    user = st.session_state.get("user_info", {})
    name = str((st.session_state.get("stage_transition") or {}).get("name") or user.get("name") or "참가자")

    # 남은 시도 횟수 확인 (총 3회)
    current_round = int(st.session_state.get("training_attempt_round", 1) or 1)
    if current_round >= 3:
        render_stage_popup_html(
            title="No more retries",
            body="You have used all available attempts.",
            note="Returning to the main screen...",
        )
        time.sleep(2)
        st.session_state.stage = "intro"
        st.rerun()

    render_stage_popup_html(
        title="Last challenge",
        body="This is your last chance. Focus on studying to achieve a higher score.",
        note="Moving to Stage 1...",
    )
    time.sleep(3)

    # 다음 회차 시작 + Stage 1(briefing)로 바로 이동
    next_round = current_round + 1
    start_training_attempt_session(user, attempt_round=next_round, skip_to_stage="briefing")
    st.session_state.current_mission = SCENARIO_ORDER[0]
    ensure_quiz_progress(SCENARIO_ORDER[0])
    st.session_state.stage = "briefing"
    st.rerun()
elif st.session_state.stage == "ending":
    render_top_spacer()
    user_name = st.session_state.user_info.get("name", "가디언")
    user_org = st.session_state.user_info.get("org", "")
    score = st.session_state.score
    grade = get_grade(score, TOTAL_SCORE)

    total_attempts = len(st.session_state.attempt_history)
    wrong_like = sum(1 for r in st.session_state.attempt_history if str(r.get("is_correct", "")) in ["N", "PARTIAL"])

    st.balloons()
    if not st.session_state.get("played_final_fanfare", False):
        play_sfx_now("final")
        st.session_state.played_final_fanfare = True

    st.title("🏆 Guardian Training Complete")
    st.success(f"{user_name} 가디언님, 모든 테마를 정복했습니다!")

    _ending_img = get_ending_image()
    if _ending_img:
        st.image(str(_ending_img), use_container_width=True)

    st.markdown("<div class='brief-actions-wrap'></div>", unsafe_allow_html=True)
    c1, c2 = st.columns([1, 1], gap='large')
    with c1:
        st.markdown(
            f"""
            <div class='card'>
              <div class='card-title'>최종 결과</div>
              <div>소속 기관: <b>{user_org or "-"}</b></div><div>사번: <b>{st.session_state.user_info.get("employee_no","-") or "-"}</b></div>
              <div>총점: <b>{score} / {TOTAL_SCORE}</b></div>
              <div style='font-size:0.9rem; opacity:.9;'>객관식 60점 + 주관식 30점 + 참여 10점</div>
              <div>등급: <b>{grade}</b></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        theme_lines = []
        for m_key in SCENARIO_ORDER:
            t = SCENARIOS[m_key]["title"]
            s = st.session_state.mission_scores.get(m_key, 0)
            theme_lines.append(f"<li>{t}: <b>{s}/{theme_max_score(m_key)}</b></li>")
        st.markdown(
            f"""
            <div class='card'>
              <div class='card-title'>테마별 점수</div>
              <ul>{''.join(theme_lines)}</ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        f"""
        <div class='card'>
          <div class='card-title'>학습 로그 요약</div>
          <div>총 제출 횟수: <b>{total_attempts}회</b> · 오답/부분정답 포함: <b>{wrong_like}회</b></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.session_state.log_write_error:
        st.warning(f"참고: 파일 로그 저장 실패 ({st.session_state.log_write_error}) — 앱 동작에는 문제 없습니다.")

    if st.session_state.attempt_history:
        output = io.StringIO()
        fieldnames = list(st.session_state.attempt_history[0].keys())
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(st.session_state.attempt_history)
        st.download_button(
            label="📥 이번 교육 응답 로그 다운로드 (CSV)",
            data=output.getvalue().encode("utf-8-sig"),
            file_name=f"compliance_training_log_{user_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    st.info("관리자용 기관 대시보드 / 문항 통계는 좌측 사이드바의 ‘관리자 대시보드’에서 확인할 수 있습니다.")

    st.markdown("<div class='brief-actions-wrap'></div>", unsafe_allow_html=True)
    c1, c2 = st.columns([1, 1], gap='large')
    with c1:
        if st.button("🗺️ 지도 다시 보기", use_container_width=True):
            st.session_state.stage = "map"
            st.rerun()
    with c2:
        if st.button("🔄 다시 도전", use_container_width=True):
            u = st.session_state.get("user_info", {}) or {}
            emp_no = str(u.get("employee_no", "")).strip()
            emp_name = str(u.get("name", "")).strip()
            emp_org = str(u.get("org", "")).strip() or "미분류"
            if not emp_name:
                st.warning("참가자 정보가 없어 처음 화면으로 이동합니다.")
                reset_game()
            else:
                hist = _summarize_user_attempts(emp_no, emp_name, emp_org)
                completed_attempts = int(hist.get("completed_attempts", 0) or 0)
                if completed_attempts >= 3:
                    st.error("이미 최대 참여 횟수(총 3회)를 모두 사용했습니다.")
                else:
                    _set_retry_offer({"employee_no": emp_no, "name": emp_name, "org": emp_org}, completed_attempts, context="ending")
                    st.rerun()

    render_retry_offer_box("ending")
else:
    st.error("알 수 없는 stage입니다. 앱을 다시 시작해주세요.")