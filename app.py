import streamlit as st
from datetime import datetime
from pathlib import Path
import csv
import io
import time
import base64
import pandas as pd
import streamlit.components.v1 as components
import os
import re

# =========================================================
# 1) 페이지 설정 / 스타일
# =========================================================
st.set_page_config(page_title="2026 Compliance Adventure", layout="centered")

st.markdown("""
<style>
.stApp {
    background-color: #0E1117;
    color: #EAEAEA;
}
.block-container {
    padding-top: 1.2rem;
    padding-bottom: 2rem;
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
    margin-bottom: 4px;
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

</style>
""", unsafe_allow_html=True)

# =========================================================
# 2) 파일 경로 / 에셋
#    (이미지/사운드 모두 app.py와 같은 폴더에 있다고 가정)
# =========================================================
BASE_DIR = Path(__file__).parent if "__file__" in globals() else Path.cwd()
ASSET_DIR = BASE_DIR
LOG_FILE = BASE_DIR / "compliance_training_log.csv"
LOG_FIELDNAMES = [
    "timestamp", "employee_no", "name", "organization", "department",
    "mission_key", "mission_title", "question_index", "question_code",
    "question_type", "question", "selected_or_text", "is_correct",
    "awarded_score", "max_score", "attempt_no_for_mission"
]

MAP_STAGE_IMAGES = {
    0: ASSET_DIR / "world_map_0.png",
    1: ASSET_DIR / "world_map_1.png",
    2: ASSET_DIR / "world_map_2.png",
    3: ASSET_DIR / "world_map_3.png",
}
DEFAULT_MAP_IMAGE = ASSET_DIR / "world_map.png"  # 선택 (fallback)
MASTER_IMAGE = ASSET_DIR / "master.png"

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

SCENARIOS = {
    "subcontracting": {
        "title": "🚜 하도급의 계곡",
        "territory_name": "하도급의 계곡",
        "briefing": {
            "title": "하도급 기본 원칙 브리핑",
            "summary": "하도급 거래에서는 '먼저 서면, 그다음 착공'이 핵심 원칙입니다. 급한 업무라도 절차를 생략하면 분쟁과 법적 리스크가 커집니다.",
            "red_flags": [
                "“일단 시작하고 계약서는 나중에”라는 지시",
                "대금/범위/납기 미확정 상태에서 착수",
                "구두 지시만 있고 서면 증빙 없음"
            ],
            "checklist": [
                "착공 전 서면 발급 여부 확인",
                "작업 범위·단가·납기 명시 확인",
                "내부 승인 절차 완료 후 진행"
            ],
            "keywords": ["서면 발급", "착공 전", "분쟁 예방", "책임 명확화"]
        },
        "quiz": [
            {
                "type": "mcq",
                "question": "하도급 업무에서 착공 전에 가장 먼저 확인해야 할 항목은 무엇인가요?",
                "options": [
                    "현장 인력 배치 여부",
                    "협력사 담당자 연락처",
                    "서면 계약(발주서 포함) 발급 여부",
                    "작업 속도와 긴급성"
                ],
                "answer": 2,
                "score": 30,
                "choice_feedback": {
                    0: "인력 배치도 중요하지만, 법적·계약상 리스크 예방의 출발점은 아닙니다.",
                    1: "실무 편의 요소일 뿐, 준법 핵심 포인트는 아닙니다.",
                    2: "정답입니다. 착공 전 서면 발급이 핵심 원칙입니다.",
                    3: "긴급성은 절차 생략의 근거가 될 수 없습니다."
                },
                "explain": "서면에는 범위·대금·납기·책임 등이 담겨야 하며, 이를 먼저 확정해야 분쟁과 법 위반 리스크를 줄일 수 있습니다.",
                "wrong_extra": "현업에서 자주 하는 실수는 ‘급하니까 먼저 시작’입니다. 하지만 이 관행이 누적되면 감사/분쟁 때 가장 취약해집니다."
            },
            {
                "type": "mcq",
                "question": "팀장이 “이번 건 급하니까 먼저 시작하고 계약서는 나중에 정리하자”고 말했습니다. 가장 적절한 대응은?",
                "options": [
                    "관행이니 이번만 예외로 진행한다",
                    "이메일로만 남기고 바로 착수한다",
                    "서면 발급 후 진행 원칙을 설명하고 절차 진행을 요청한다",
                    "협력사에 책임을 떠넘기고 진행한다"
                ],
                "answer": 2,
                "score": 30,
                "choice_feedback": {
                    0: "‘관행’은 리스크 면책 사유가 되지 않습니다.",
                    1: "사후 이메일 정리는 분쟁 시 불충분할 수 있습니다.",
                    2: "정답입니다. 원칙 설명 + 대안 제시가 가장 좋은 실무 대응입니다.",
                    3: "책임 전가는 문제 해결이 아니라 리스크 확대입니다."
                },
                "explain": "실무적으로는 단순 거절보다 ‘왜 안 되는지’와 ‘어떻게 하면 되는지(절차)’를 함께 안내하는 것이 중요합니다.",
                "wrong_extra": "관리자/팀장에게도 설명 가능한 표현으로 대응해야 이후 같은 요청이 반복되지 않습니다."
            },
            {
                "type": "text",
                "question": "팀장에게 보낼 답변 문장을 짧게 작성해보세요. (원칙 설명 + 대안 제시 포함)",
                "score": 40,
                "rubric_keywords": {
                    "원칙 언급": ["서면", "계약", "발급"],
                    "절차/대안": ["절차", "승인", "확인", "진행"],
                    "리스크 인식": ["위반", "분쟁", "리스크"]
                },
                "model_answer": "서면 계약(또는 발주서) 발급 없이 착공하면 분쟁 및 준법 리스크가 있어, 관련 서면 발급과 승인 절차 확인 후 바로 진행하겠습니다."
            }
        ]
    },
    "security": {
        "title": "🔐 보안의 요새",
        "territory_name": "보안의 요새",
        "briefing": {
            "title": "보안 기본 원칙 브리핑",
            "summary": "출처가 불분명한 메일·링크·첨부파일은 클릭하지 않는 것이 원칙입니다. 특히 실행 파일(.exe)은 악성코드/랜섬웨어 위험이 큽니다.",
            "red_flags": [
                "발신자가 모호하거나 도메인이 이상함",
                "‘긴급 확인’ ‘즉시 클릭’ 등 압박 문구",
                "실행 파일(.exe), 매크로 파일 첨부"
            ],
            "checklist": [
                "클릭 전 발신자/도메인 확인",
                "의심 메일은 보안팀 신고",
                "첨부파일 실행 금지, 내부 채널로 재확인"
            ],
            "keywords": ["피싱", "첨부파일", "신고", "실행 금지"]
        },
        "quiz": [
            {
                "type": "mcq",
                "question": "출처가 불분명한 메일에 ‘인사평가 결과.exe’가 첨부되어 왔을 때 가장 적절한 행동은?",
                "options": [
                    "파일명을 바꿔 실행해본다",
                    "궁금하니 개인 PC에서 먼저 열어본다",
                    "클릭하지 않고 보안팀에 신고한다",
                    "동료에게 먼저 열어보라고 전달한다"
                ],
                "answer": 2,
                "score": 30,
                "choice_feedback": {
                    0: "파일명 변경은 안전성을 높이지 않습니다.",
                    1: "개인 PC라도 회사 계정/자료와 연결되어 있으면 위험합니다.",
                    2: "정답입니다. 클릭 금지 + 신고가 원칙입니다.",
                    3: "위험을 전파하는 행동으로 더 큰 사고를 부를 수 있습니다."
                },
                "explain": "출처 불명 실행 파일은 악성코드 감염 가능성이 매우 높습니다. 의심 메일은 즉시 신고하고 별도 채널로 진위를 확인해야 합니다.",
                "wrong_extra": "피싱 메일은 ‘궁금증’과 ‘긴급함’을 자극합니다. 호기심에 여는 순간 사고가 시작될 수 있습니다."
            },
            {
                "type": "mcq",
                "question": "보안 관점에서 가장 위험 신호가 큰 조합은 무엇인가요?",
                "options": [
                    "사내 공지 + PDF 첨부",
                    "익숙한 동료 이름 + 사내 메신저 링크",
                    "모르는 발신자 + .exe 첨부 + 긴급 클릭 요청",
                    "거래처 문의 + 전화번호 기재"
                ],
                "answer": 2,
                "score": 30,
                "choice_feedback": {
                    0: "PDF도 위험할 수 있지만 일반적으로 실행 파일보다 위험 신호가 약합니다.",
                    1: "메신저 링크도 확인은 필요하지만 조합 위험도는 상대적으로 낮습니다.",
                    2: "정답입니다. 발신자 불명 + 실행 파일 + 긴급 유도는 대표적 피싱 패턴입니다.",
                    3: "거래처 문의도 검증 필요하지만, 이 조합만으로 최고 위험은 아닙니다."
                },
                "explain": "위험 신호는 단일 요소보다 ‘여러 요소가 겹칠 때’ 강해집니다. (발신자 불명 + 실행파일 + 긴급 유도)",
                "wrong_extra": "실무에서는 ‘이상한데 급해서 열었다’가 가장 흔한 사고 원인입니다. 이상하면 멈추는 습관이 중요합니다."
            },
            {
                "type": "text",
                "question": "의심 메일을 받은 후 팀/보안담당자에게 보낼 보고 문장을 1~2문장으로 작성해보세요.",
                "score": 40,
                "rubric_keywords": {
                    "의심 정황": ["출처", "발신자", "의심", "exe", "첨부"],
                    "행동": ["클릭", "열지", "실행", "중단"],
                    "보고/확인": ["보안팀", "신고", "확인", "공유"]
                },
                "model_answer": "출처가 불분명한 메일에 실행 파일(.exe) 첨부가 있어 의심되어 파일은 열지 않았습니다. 보안팀에 신고하고 진위 여부를 확인 부탁드립니다."
            }
        ]
    },
    "fairtrade": {
        "title": "🛡️ 반부패의 성",
        "territory_name": "반부패의 성",
        "briefing": {
            "title": "반부패(재산상 이익) 기본 원칙 브리핑",
            "summary": "업무 관련자에게 금품, 상품권, 편의 제공 등 재산상 이익을 받거나 요구하는 행위는 반부패 리스크가 큽니다. 애매한 경우에도 먼저 수수하지 말고 즉시 보고/상담하는 것이 안전합니다.",
            "red_flags": [
                "업무 협력사/이해관계자가 상품권·현금성 선물을 제안",
                "“작은 성의”라며 개인 계좌·개인 연락처로 전달 시도",
                "승인/평가/계약 직전·직후에 금품 또는 편의 제공 제안"
            ],
            "checklist": [
                "금품·상품권·현금성 이익은 원칙적으로 수수 금지",
                "즉시 정중히 거절하고, 대화/정황을 기록",
                "상급자·감사/준법 담당자에게 보고 및 상담"
            ],
            "keywords": ["재산상 이익", "금품 수수 금지", "거절", "보고"]
        },
        "quiz": [
            {
                "type": "mcq",
                "question": "계약이 막 완료된 후 협력사 담당자가 감사의 의미라며 모바일 상품권을 보내왔습니다. 가장 적절한 대응은?",
                "options": [
                    "소액이므로 받는다",
                    "개인적으로 받고 외부에 알리지 않는다",
                    "정중히 거절하고 관련 사실을 내부에 보고한다",
                    "이번만 받고 다음부터 조심한다"
                ],
                "answer": 2,
                "score": 30,
                "choice_feedback": {
                    0: "금액이 작아도 업무 관련 이해관계자에게 받는 재산상 이익은 리스크가 있습니다.",
                    1: "비공개 수수는 사후에 더 큰 문제로 이어질 수 있습니다.",
                    2: "정답입니다. 수수하지 않고 거절 + 내부 보고가 기본 대응입니다.",
                    3: "‘이번만’은 반복 위험을 키우고 기준을 무너뜨립니다."
                },
                "explain": "핵심은 금액보다 ‘업무 관련성’입니다. 이해관계자와의 관계에서 금품·상품권 수수는 공정성 훼손 및 부정청탁/반부패 이슈로 이어질 수 있어 거절 및 보고가 원칙입니다.",
                "wrong_extra": "실무에서는 ‘감사 표시’라는 표현으로 제안되는 경우가 많습니다. 표현보다 관계와 시점(계약/평가 전후)을 기준으로 판단하세요."
            },
            {
                "type": "mcq",
                "question": "업무 상대방이 “현금은 아니고 식사/골프/차량 지원 같은 편의 제공인데 괜찮지 않냐”고 말합니다. 가장 적절한 판단은?",
                "options": [
                    "현금이 아니므로 문제가 없다",
                    "상대가 먼저 제안했으니 괜찮다",
                    "편의 제공도 재산상 이익이 될 수 있어 수수하지 않고 기준을 확인한다",
                    "개인 시간에 받으면 업무와 무관하다"
                ],
                "answer": 2,
                "score": 30,
                "choice_feedback": {
                    0: "재산상 이익은 현금만 의미하지 않습니다.",
                    1: "상대 제안 여부와 무관하게 수수 리스크는 발생할 수 있습니다.",
                    2: "정답입니다. 편의 제공도 재산상 이익에 해당할 수 있어 원칙적으로 거절·확인이 필요합니다.",
                    3: "개인 시간이라도 업무 관련 이해관계자면 리스크가 남습니다."
                },
                "explain": "반부패 관점에서 재산상 이익에는 현금 외에도 상품권, 식사·접대, 편의 제공 등이 포함될 수 있습니다. 애매하면 받지 않고 기준 확인 및 보고가 우선입니다.",
                "wrong_extra": "‘현금만 아니면 된다’는 오해가 가장 흔합니다. 실제로는 현금성/비현금성 모두 리스크가 될 수 있습니다."
            },
            {
                "type": "text",
                "question": "업무 상대방의 금품/편의 제공 제안을 거절하고 내부 보고까지 포함하는 답변 문장을 1~2문장으로 작성해보세요.",
                "score": 40,
                "rubric_keywords": {
                    "거절 표현": ["거절", "받을 수 없습니다", "어렵습니다", "불가"],
                    "재산상 이익/원칙 언급": ["금품", "상품권", "편의", "재산상", "규정", "반부패"],
                    "보고/기록 조치": ["보고", "공유", "담당", "준법", "감사", "기록"]
                },
                "model_answer": "업무 관련자에게 금품이나 편의 제공을 받는 것은 반부패 기준상 수수할 수 없어 정중히 거절드립니다. 관련 제안 내용은 내부 준법/감사 담당자에게 보고하고 기록하겠습니다."
            }
        ]
    }
}

THEME_TOTAL_SCORE = 100
TOTAL_SCORE = len(SCENARIO_ORDER) * THEME_TOTAL_SCORE

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
        "quiz_progress": {},
        "attempt_counts": {},
        "attempt_history": [],
        "show_conquer_fx": False,
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
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def recalc_total_score():
    st.session_state.score = sum(st.session_state.mission_scores.values())


def ensure_quiz_progress(m_key: str):
    if m_key not in st.session_state.quiz_progress:
        st.session_state.quiz_progress[m_key] = {
            "current_idx": 0,
            "submissions": {}
        }


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


def mark_theme_complete_if_ready(m_key: str):
    ensure_quiz_progress(m_key)
    subs = st.session_state.quiz_progress[m_key]["submissions"]
    total_q = len(SCENARIOS[m_key]["quiz"])
    if len(subs) == total_q:
        st.session_state.mission_scores[m_key] = theme_score_from_submissions(m_key)
        recalc_total_score()
        if m_key not in st.session_state.completed:
            st.session_state.completed.append(m_key)
            st.session_state.last_cleared_mission = m_key
            st.session_state.show_conquer_fx = True

# =========================================================
# 5) 유틸 함수 (이미지 / 사운드 / 로그 / 평가)
# =========================================================
def get_current_map_image():
    stage_idx = min(len(st.session_state.get("completed", [])), 3)
    path = MAP_STAGE_IMAGES.get(stage_idx)
    if path and path.exists():
        return path
    if DEFAULT_MAP_IMAGE.exists():
        return DEFAULT_MAP_IMAGE
    return None


def show_map_with_fade(map_path: Path, caption: str = None):
    if not map_path or not map_path.exists():
        st.warning("맵 이미지 파일을 찾을 수 없습니다.")
        return
    try:
        img_bytes = map_path.read_bytes()
        encoded = base64.b64encode(img_bytes).decode("utf-8")
        st.markdown(
            f"""
            <div class="map-fade-wrap">
                <img class="map-fade-img" src="data:image/png;base64,{encoded}" />
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



def _audio_component_html(audio_b64: str, *, loop: bool = False, hidden_label: str = "audio"):
    loop_attr = " loop" if loop else ""
    html = f"""
    <html>
      <body style=\"margin:0; padding:0; background:transparent;\">
        <audio id=\"{hidden_label}\" autoplay{loop_attr} style=\"display:none;\">
          <source src=\"data:audio/mp3;base64,{audio_b64}\" type=\"audio/mpeg\">
        </audio>
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
        bgm_path = BGM.get(bgm_key)
        if bgm_path and bgm_path.exists():
            try:
                bgm_b64 = base64.b64encode(bgm_path.read_bytes()).decode("utf-8")
                _audio_component_html(bgm_b64, loop=True, hidden_label=f"bgm_{bgm_key}")
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
    with st.expander("🔊 사운드 파일 점검", expanded=False):
        rows = []
        for k, v in BGM.items():
            rows.append({"구분": f"BGM · {k}", "파일명": v.name, "존재": "✅" if v.exists() else "❌"})
        for k, v in SFX.items():
            rows.append({"구분": f"SFX · {k}", "파일명": v.name, "존재": "✅" if v.exists() else "❌"})
        st.dataframe(pd.DataFrame(rows), use_container_width=True)
        st.caption("※ 브라우저 자동재생 정책에 따라 첫 클릭(모험 시작/버튼 클릭) 이후에 사운드가 재생되는 경우가 있습니다.")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("정답 효과음 테스트", key="sfx_test_correct"):
                play_sfx_now("correct")
            if st.button("정복 효과음 테스트", key="sfx_test_conquer"):
                play_sfx_now("conquer")
        with c2:
            if st.button("오답 효과음 테스트", key="sfx_test_wrong"):
                play_sfx_now("wrong")
            if st.button("최종 효과음 테스트", key="sfx_test_final"):
                play_sfx_now("final")



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

    norm = {k: clean.get(k, "") for k in LOG_FIELDNAMES}
    # 숫자형 컬럼 보정
    for col in ["question_index", "awarded_score", "max_score", "attempt_no_for_mission"]:
        v = norm.get(col, "")
        try:
            if v == "" or v is None:
                norm[col] = 0
            else:
                norm[col] = int(float(v))
        except Exception:
            norm[col] = 0
    # 문자열 컬럼 보정
    for col in ["timestamp", "employee_no", "name", "organization", "department", "mission_key", "mission_title", "question_code", "question_type", "question", "selected_or_text", "is_correct"]:
        val = norm.get(col, "")
        if val is None:
            val = ""
        norm[col] = str(val)
    if not norm["organization"].strip():
        norm["organization"] = "미분류"
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
    for col in ["employee_no", "name", "organization", "department", "mission_key", "mission_title", "question_code", "question_type", "question", "selected_or_text", "is_correct"]:
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
    for col in ["awarded_score", "max_score", "attempt_no_for_mission"]:
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


def _render_employee_lookup_popup_body(name_query: str = ""):
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

    st.caption("사번, 이름, 소속 기관을 확인한 뒤 정확한 본인 정보를 선택하세요.")
    st.dataframe(show_df, use_container_width=True, height=min(320, 90 + len(show_df) * 35))

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
    p1.text_input("사번", value=str(preview.get("employee_no", "")), disabled=True, key="employee_modal_preview_no")
    p2.text_input("이름", value=str(preview.get("name", "")), disabled=True, key="employee_modal_preview_name")
    p3.text_input("소속 기관", value=str(preview.get("organization", "")), disabled=True, key="employee_modal_preview_org")

    c1, c2 = st.columns(2)
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

def evaluate_text_answer(answer_text: str, rubric_keywords: dict, max_score: int):
    text = (answer_text or "").strip()
    if not text:
        return {
            "awarded_score": 0,
            "found_groups": [],
            "missing_groups": list(rubric_keywords.keys()),
            "quality": "empty",
        }

    found, missing = [], []
    lowered = text.lower()
    for group_name, keywords in rubric_keywords.items():
        hit = any(str(k).lower() in lowered for k in keywords)
        if hit:
            found.append(group_name)
        else:
            missing.append(group_name)

    ratio = len(found) / max(len(rubric_keywords), 1)
    awarded = int(round(max_score * ratio))
    if len(text) < 8 and awarded > 0:
        awarded = max(0, awarded - 5)

    quality = "good" if ratio >= 0.67 else "partial"
    return {
        "awarded_score": awarded,
        "found_groups": found,
        "missing_groups": missing,
        "quality": quality,
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

    # 기본 컬럼 보정
    if "organization" not in df.columns:
        if "department" in df.columns:
            df["organization"] = df["department"]
        else:
            df["organization"] = "미분류"
    df["organization"] = df["organization"].fillna("").astype(str).str.strip().replace("", "미분류")

    if "employee_no" not in df.columns:
        df["employee_no"] = ""
    df["employee_no"] = df["employee_no"].fillna("").astype(str).str.strip()

    if "name" not in df.columns:
        df["name"] = "이름미상"
    df["name"] = df["name"].fillna("").astype(str).str.strip().replace("", "이름미상")

    if "department" not in df.columns:
        df["department"] = ""

    for col in ["awarded_score", "max_score", "question_index"]:
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
        # question_code 기반으로 복원 시도
        df["mission_key"] = df["question_code"].astype(str).str.split("_Q").str[0]

    df["learner_id"] = df["employee_no"].where(df["employee_no"].str.strip() != "", df["organization"] + "|" + df["name"])

    # 최신 제출 기준 문항 스냅샷(문항별 중복 제거)
    df_sorted = df.sort_values(["timestamp"], ascending=True)
    latest_per_q = df_sorted.drop_duplicates(subset=["learner_id", "question_code"], keep="last")

    # 총 문항 수 / 테마별 문항 수
    total_questions = sum(len(SCENARIOS[k]["quiz"]) for k in SCENARIO_ORDER)
    theme_question_counts = {k: len(SCENARIOS[k]["quiz"]) for k in SCENARIO_ORDER}

    # 참여자별 기본 집계
    attempts_by_user = (
        df.groupby(["learner_id", "employee_no", "organization", "name"], as_index=False)
          .agg(
              total_attempts=("question_code", "count"),
              last_activity=("timestamp", "max"),
          )
    )

    score_by_user = (
        latest_per_q.groupby(["learner_id"], as_index=False)
        .agg(
            total_score=("awarded_score", "sum"),
            answered_questions=("question_code", "nunique"),
        )
    )

    # 참여자별 완료 테마 수 계산
    theme_counts = (
        latest_per_q.groupby(["learner_id", "mission_key"], as_index=False)
        .agg(answered_in_theme=("question_code", "nunique"))
    )
    theme_counts["theme_total_questions"] = theme_counts["mission_key"].map(theme_question_counts).fillna(999)
    theme_counts["theme_completed"] = theme_counts["answered_in_theme"] >= theme_counts["theme_total_questions"]

    completed_theme_cnt = (
        theme_counts.groupby("learner_id", as_index=False)
        .agg(completed_themes=("theme_completed", "sum"))
    )

    participants = attempts_by_user.merge(score_by_user, on="learner_id", how="left").merge(completed_theme_cnt, on="learner_id", how="left")
    participants["total_score"] = participants["total_score"].fillna(0).astype(int)
    participants["answered_questions"] = participants["answered_questions"].fillna(0).astype(int)
    participants["completed_themes"] = participants["completed_themes"].fillna(0).astype(int)
    participants["completion_rate_q"] = ((participants["answered_questions"] / max(total_questions, 1)) * 100).round(1)
    participants["score_rate"] = ((participants["total_score"] / max(TOTAL_SCORE, 1)) * 100).round(1)
    participants["is_completed"] = participants["answered_questions"] >= total_questions
    participants["status"] = participants["is_completed"].map({True: "수료", False: "진행중"})

    # 기관별 요약
    org_summary = (
        participants.groupby("organization", as_index=False)
        .agg(
            participants=("learner_id", "nunique"),
            completed=("is_completed", "sum"),
            avg_score=("total_score", "mean"),
            avg_score_rate=("score_rate", "mean"),
            avg_completion_rate=("completion_rate_q", "mean"),
            latest_activity=("last_activity", "max"),
        )
    )
    org_attempts = (
        df.groupby("organization", as_index=False)
          .agg(total_attempts=("question_code", "count"))
    )
    org_summary = org_summary.merge(org_attempts, on="organization", how="left")
    org_summary["avg_score"] = org_summary["avg_score"].round(1)
    org_summary["avg_score_rate"] = org_summary["avg_score_rate"].round(1)
    org_summary["avg_completion_rate"] = org_summary["avg_completion_rate"].round(1)
    org_summary["completion_rate"] = ((org_summary["completed"] / org_summary["participants"].replace(0, 1)) * 100).round(1)
    org_summary = org_summary.sort_values(["avg_score", "participants"], ascending=[False, False]).reset_index(drop=True)

    # 보기 좋은 참여자 테이블
    participants_view = participants.copy()
    participants_view["last_activity"] = participants_view["last_activity"].dt.strftime("%Y-%m-%d %H:%M").fillna("-")
    participants_view = participants_view.sort_values(["last_activity", "total_score"], ascending=[False, False])

    return {
        "raw": df,
        "latest_per_q": latest_per_q,
        "participants": participants,
        "participants_view": participants_view,
        "org_summary": org_summary,
        "total_questions": total_questions,
    }




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
                "total_attempts": "누적 제출 수",
                "latest_activity": "최근 참여",
            })
            st.dataframe(org_view, use_container_width=True, height=280 if compact else None)

            chart_df = org_view[["기관", "평균 점수율(%)"]].set_index("기관")
            st.bar_chart(chart_df)
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
    show_cols = ["사번", "기관", "이름", "상태", "총점", "점수율(%)", "완료 테마수", "제출 문항수", "문항 진행률(%)", "누적 제출 수", "최근 참여"]
    st.dataframe(p_view[show_cols], use_container_width=True)

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
    if st.session_state.get("audio_debug"):
        render_audio_status_hint()

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
                    st.dataframe(cnt, use_container_width=True)
                st.dataframe(df.tail(200), use_container_width=True, height=320)
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

    st.dataframe(view_df, use_container_width=True)
    if not view_df.empty:
        chart_df = view_df[["문항", "첫 시도 정답률(%)"]].copy().set_index("문항")
        st.bar_chart(chart_df)

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
    if not st.session_state.get("show_conquer_fx"):
        return

    m_key = st.session_state.get("last_cleared_mission")
    if not m_key or m_key not in SCENARIOS:
        st.session_state.show_conquer_fx = False
        return

    title = SCENARIOS[m_key]["title"]
    theme_icon = THEME_ICONS.get(m_key, "🏳️")
    cleared_cnt = len(st.session_state.get("completed", []))

    fx_box = st.empty()
    fx_progress = st.progress(0)
    fx_steps = [
        "🗺️ Guardian’s Map 갱신 중...",
        f"⚔️ {title} 정복 기록 반영...",
        f"✨ {title} 정복 완료! 새로운 단계가 열립니다.",
    ]

    for i, msg in enumerate(fx_steps, start=1):
        fx_box.markdown(
            f"""
            <div style="
                background: linear-gradient(135deg, #102313, #152B1A);
                border: 1px solid #2F7D32;
                border-radius: 14px;
                padding: 12px 14px;
                margin-bottom: 10px;
                color: #E8F5E9;
                font-weight: 700;
            ">{msg}</div>
            """,
            unsafe_allow_html=True,
        )
        fx_progress.progress(int(i / len(fx_steps) * 100))
        time.sleep(0.28)

    play_sfx_now("conquer")

    new_map = get_current_map_image()
    if new_map:
        show_map_with_fade(new_map, caption=f"✨ Guardian’s Map Updated · stage {min(cleared_cnt, 3)}")
    else:
        st.warning("갱신된 맵 이미지를 찾을 수 없습니다. (world_map_0~3.png 확인)")

    st.success(f"{theme_icon} {title} 정복 완료!")
    try:
        st.toast(f"{theme_icon} 새 구역이 해방되었습니다!", icon="✨")
    except Exception:
        pass

    st.session_state.show_conquer_fx = False


def render_guardian_map():
    st.subheader("🗺️ Guardian’s Map")

    map_img = get_current_map_image()
    cleared_cnt = len(st.session_state.get("completed", []))
    stage_idx = min(cleared_cnt, 3)

    if map_img:
        show_map_with_fade(map_img, caption=f"현재 맵 단계: world_map_{stage_idx}.png")
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
                txt += f" ({score}/100)"
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

    col1, col2 = st.columns(2)
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


    c1, c2 = st.columns(2)
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

        total_q = len(SCENARIOS[m_key]["quiz"])
        if q_idx < total_q - 1:
            if st.button("다음 문제로 ▶", key=f"next_{m_key}_{q_idx}", use_container_width=True):
                progress["current_idx"] += 1
                st.rerun()
        else:
            mark_theme_complete_if_ready(m_key)
            if st.button("🏁 테마 정복 완료! 맵으로 돌아가기", key=f"finish_{m_key}", use_container_width=True):
                st.session_state.stage = "map"
                st.rerun()
        return

    st.markdown(f"### Q{q_idx+1}. {q_data['question']}")
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

        st.markdown(
            f"""
            <div class='card'>
              <div class='card-title'>내 답안</div>
              <div>{res['answer_text'] if res['answer_text'] else '(비어 있음)'}</div>
              <hr style="border-color:#2A3140;">
              <div><b>평가 결과</b> · {quality_badge}</div>
              <div style="margin-top:6px;"><b>잘 반영한 요소</b>: {found_text}</div>
              <div style="margin-top:4px;"><b>보완 포인트</b>: {missing_text}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.expander("모범답안 보기"):
            st.write(q_data["model_answer"])

        mark_theme_complete_if_ready(m_key)
        if st.button("🏁 테마 정복 완료! 맵으로 돌아가기", key=f"end_theme_{m_key}", use_container_width=True):
            st.session_state.stage = "map"
            st.rerun()
        return

    st.markdown(f"### Q{q_idx+1}. {q_data['question']}")
    answer_text = st.text_area(
        "답안을 입력하세요",
        key=f"text_{m_key}_{q_idx}",
        height=120,
        placeholder="예: 서면 계약 발급 없이 진행하면 리스크가 있어, 관련 절차 확인 후 진행하겠습니다.",
    )

    if st.button("제출하기", key=f"submit_text_{m_key}_{q_idx}", use_container_width=True):
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
          <div style='margin-top:4px; font-size:0.9rem; opacity:.92;'>문항 진행: {submitted_count} / {len(q_list)} · 테마 점수(누적): {current_theme_score}/100</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_left, col_right = st.columns([1, 2])
    with col_left:
        if MASTER_IMAGE.exists():
            st.image(str(MASTER_IMAGE), caption="클린 마스터", use_container_width=True)
        else:
            st.info("클린 마스터 이미지 없음")

        st.markdown(
            """
            <div class='card'>
              <div class='card-title'>진행 팁</div>
              <div>정답 여부보다 <b>왜 그런지</b>를 이해하는 게 핵심이에요.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("🗺️ 맵으로 나가기", key=f"back_map_{m_key}", use_container_width=True):
            st.session_state.stage = "map"
            st.rerun()

    with col_right:
        if q_data["type"] == "mcq":
            render_mcq_question(m_key, current_idx, q_data)
        elif q_data["type"] == "text":
            render_text_question(m_key, current_idx, q_data)
        else:
            st.error("지원하지 않는 문항 타입입니다.")

# =========================================================
# 7) 메인 화면 분기
# =========================================================
init_state()
render_audio_system()

with st.sidebar:
    st.checkbox("🔊 배경음악 재생", key="bgm_enabled")
    st.checkbox("사운드 파일 점검 패널", key="audio_debug")
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
    st.title("🛡️ 2026 Compliance Adventure")
    st.caption("Guardian Training · 컴플라이언스 테마 정복형 학습")
    if st.session_state.get("audio_debug"):
        render_audio_status_hint()

    intro_map = get_current_map_image()
    if intro_map:
        show_map_with_fade(intro_map)
    else:
        st.info("맵 이미지를 추가하면 인트로 연출이 더 좋아집니다.")

    st.markdown(
        """
        <div class='card'>
          <div class='card-title'>게임 방식</div>
          <div>맵에서 테마를 선택 → 핵심 브리핑 학습 → 퀴즈(4지선다 + 주관식) → 정복 완료!</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("🏢 기관별 누적 현황 (미리보기)", expanded=False):
        render_org_dashboard(compact=True)
    st.caption("상세 통계는 좌측 사이드바의 ‘관리자 대시보드’에서 확인할 수 있습니다.")

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
        with col_a:
            st.text_input("사번", value=selected_emp.get("employee_no", ""), disabled=True, key="confirm_emp_no")
        with col_b:
            st.text_input("이름", value=selected_emp.get("name", ""), disabled=True, key="confirm_emp_name")
        with col_c:
            st.text_input("소속 기관", value=selected_emp.get("organization", ""), disabled=True, key="confirm_emp_org")

        if st.button("모험 시작하기", use_container_width=True):
            if selected_emp.get("name"):
                st.session_state.user_info = {
                    "employee_no": selected_emp.get("employee_no", ""),
                    "name": selected_emp.get("name", ""),
                    "org": selected_emp.get("organization", ""),
                }
                st.session_state.stage = "map"
                st.rerun()
            else:
                st.warning("참가자 확인 정보를 다시 선택해주세요.")

elif st.session_state.stage == "map":
    user_name = st.session_state.user_info.get("name", "가디언")
    user_org = st.session_state.user_info.get("org", "")

    st.title(f"🗺️ {user_name} 가디언의 지도")
    if st.session_state.get("audio_debug"):
        render_audio_status_hint()
    cap_parts = []
    user_emp_no = st.session_state.user_info.get("employee_no", "")
    if user_emp_no:
        cap_parts.append(f"사번: {user_emp_no}")
    if user_org:
        cap_parts.append(f"소속 기관: {user_org}")
    if cap_parts:
        st.caption(" | ".join(cap_parts))

    render_conquer_fx_if_needed()
    render_guardian_map()

    st.write("관문을 선택하세요:")
    cols = st.columns(3)
    for i, m_key in enumerate(SCENARIO_ORDER):
        mission = SCENARIOS[m_key]
        status = get_theme_status(m_key)
        with cols[i]:
            if status == "clear":
                score = st.session_state.mission_scores.get(m_key, 0)
                badge = "🏅" if score >= 90 else ("✅" if score >= 70 else "📘")
                st.success(f"{badge} {mission['title']}")
                st.caption(f"점수 {score}/100")
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
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("🏢 기관별 누적 현황 (미리보기)", expanded=False):
        render_org_dashboard(compact=True)

    if len(st.session_state.completed) == len(SCENARIO_ORDER):
        if st.button("최종 결과 보기", use_container_width=True):
            st.session_state.stage = "ending"
            st.rerun()

elif st.session_state.stage == "briefing":
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
    m_key = st.session_state.get("current_mission")
    if not m_key or m_key not in SCENARIOS:
        st.warning("퀴즈 정보가 없어 지도로 돌아갑니다.")
        st.session_state.stage = "map"
        st.rerun()

    ensure_quiz_progress(m_key)
    if len(st.session_state.quiz_progress[m_key]["submissions"]) == len(SCENARIOS[m_key]["quiz"]):
        mark_theme_complete_if_ready(m_key)

    render_quiz(m_key)

elif st.session_state.stage == "admin":
    render_admin_page()

elif st.session_state.stage == "ending":
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

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            f"""
            <div class='card'>
              <div class='card-title'>최종 결과</div>
              <div>소속 기관: <b>{user_org or "-"}</b></div><div>사번: <b>{st.session_state.user_info.get("employee_no","-") or "-"}</b></div>
              <div>총점: <b>{score} / {TOTAL_SCORE}</b></div>
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
            theme_lines.append(f"<li>{t}: <b>{s}/100</b></li>")
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

    c1, c2 = st.columns(2)
    with c1:
        if st.button("🗺️ 지도 다시 보기", use_container_width=True):
            st.session_state.stage = "map"
            st.rerun()
    with c2:
        if st.button("🔄 처음부터 다시", use_container_width=True):
            reset_game()
else:
    st.error("알 수 없는 stage입니다. 앱을 다시 시작해주세요.")
