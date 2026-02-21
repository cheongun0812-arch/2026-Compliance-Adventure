import streamlit as st
from datetime import datetime
from pathlib import Path
import csv
import io
import time
import base64
import pandas as pd

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
</style>
""", unsafe_allow_html=True)

# =========================================================
# 2) 파일 경로 / 에셋
#    (이미지/사운드 모두 app.py와 같은 폴더에 있다고 가정)
# =========================================================
BASE_DIR = Path(__file__).parent if "__file__" in globals() else Path.cwd()
ASSET_DIR = BASE_DIR
LOG_FILE = BASE_DIR / "compliance_training_log.csv"

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
    "fairtrade": "🏰",
}

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
        "title": "🏰 공정의 성",
        "territory_name": "공정의 성",
        "briefing": {
            "title": "공정거래 기본 원칙 브리핑",
            "summary": "경쟁사와 가격·입찰·물량 등 경쟁정보를 맞추는 행위는 담합 리스크가 큽니다. 애매한 대화라도 즉시 선을 긋고 보고하는 것이 안전합니다.",
            "red_flags": [
                "입찰가/제안조건 공유 제안",
                "‘서로 손해보지 않게 맞추자’는 표현",
                "경쟁사와 비공식 정보 교환"
            ],
            "checklist": [
                "가격·입찰 관련 대화 즉시 중단",
                "거절 의사 명확히 표현",
                "내부 보고 및 기록 남기기"
            ],
            "keywords": ["담합", "입찰가", "거절", "보고"]
        },
        "quiz": [
            {
                "type": "mcq",
                "question": "경쟁사가 식사 자리에서 ‘이번 입찰가는 서로 맞추자’고 제안했습니다. 가장 적절한 대응은?",
                "options": [
                    "이번만 비공식적으로 맞춰준다",
                    "일단 듣기만 하고 나중에 생각한다",
                    "즉시 거절하고 관련 대화를 중단한다",
                    "회사에 유리하면 일부만 공유한다"
                ],
                "answer": 2,
                "score": 30,
                "choice_feedback": {
                    0: "비공식 제안이라도 담합 리스크는 동일하게 발생합니다.",
                    1: "‘듣기만 한 것’도 상황에 따라 문제 소지가 될 수 있습니다.",
                    2: "정답입니다. 즉시 거절 + 대화 중단이 기본 대응입니다.",
                    3: "일부 공유도 경쟁정보 교환에 해당할 수 있습니다."
                },
                "explain": "핵심은 애매하게 넘기지 않고, 선을 분명히 긋는 것입니다. 필요 시 내부 보고까지 이어져야 합니다.",
                "wrong_extra": "공정거래 이슈는 개인 판단보다 회사 전체 리스크로 확산되기 쉬워, 초기에 명확한 대응이 가장 중요합니다."
            },
            {
                "type": "mcq",
                "question": "아래 중 공정거래 리스크가 가장 큰 대화 주제는 무엇인가요?",
                "options": [
                    "업계 행사 일정 공유",
                    "일반적인 기술 트렌드 토론",
                    "입찰 가격/물량/제안조건 조율",
                    "공개된 보도자료 내용 확인"
                ],
                "answer": 2,
                "score": 30,
                "choice_feedback": {
                    0: "행사 일정 공유는 일반적으로 위험도가 낮습니다.",
                    1: "기술 트렌드 일반론은 보통 허용 범주입니다(구체 경쟁정보 제외).",
                    2: "정답입니다. 가격·물량·조건 조율은 담합 리스크가 큽니다.",
                    3: "공개된 정보 확인은 상대적으로 위험도가 낮습니다."
                },
                "explain": "경쟁사와의 대화는 ‘공개 정보 범위’를 넘지 않도록 특히 주의해야 합니다.",
                "wrong_extra": "실무에서는 ‘업계 정보 교류’라는 명목으로 가격/조건 이야기가 섞이는 순간 위험해집니다."
            },
            {
                "type": "text",
                "question": "경쟁사 제안을 거절하는 짧은 답변 문장을 작성해보세요. (거절 + 대화 중단 + 준법 의식 포함)",
                "score": 40,
                "rubric_keywords": {
                    "거절": ["거절", "불가", "할 수 없습니다", "어렵습니다"],
                    "대화중단": ["입찰", "가격", "논의", "중단"],
                    "준법/보고": ["준법", "규정", "보고", "내부"]
                },
                "model_answer": "입찰 가격이나 조건 관련 논의는 준법상 진행할 수 없습니다. 이 대화는 여기서 중단하겠습니다."
            }
        ]
    }
}

DEPT_GUIDE = {
    "영업팀": "거래처 접점이 많아 접대·리베이트·공정거래 이슈에 특히 민감합니다.",
    "구매팀": "계약·하도급·입찰 문서화와 절차 준수가 핵심입니다.",
    "인사팀": "개인정보 보호, 평가정보 보안, 공정한 절차가 중요합니다.",
    "IT지원팀": "피싱·첨부파일·권한관리·사고 대응 체계가 핵심 리스크입니다.",
    "감사팀": "증빙/보고체계/내부통제 점검 관점으로 보시면 좋습니다."
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


def play_sfx(sound_path: Path):
    if not sound_path or not sound_path.exists():
        return
    try:
        ext = sound_path.suffix.lower().replace(".", "") or "mp3"
        audio_b64 = base64.b64encode(sound_path.read_bytes()).decode("utf-8")
        st.markdown(
            f"""
            <audio autoplay style="display:none;">
              <source src="data:audio/{ext};base64,{audio_b64}" type="audio/{ext}">
            </audio>
            """,
            unsafe_allow_html=True,
        )
    except Exception:
        pass


def append_attempt_log(mission_key: str, q_idx: int, q_type: str, payload: dict):
    user = st.session_state.get("user_info", {})
    mission = SCENARIOS[mission_key]
    question = mission["quiz"][q_idx]

    row = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "name": user.get("name", ""),
        "department": user.get("dept", ""),
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
    }

    st.session_state.attempt_history.append(row)

    try:
        file_exists = LOG_FILE.exists()
        with open(LOG_FILE, "a", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=list(row.keys()))
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


def render_admin_question_stats():
    st.markdown("### 🛠 관리자용 문항별 정답률 통계")

    if not LOG_FILE.exists():
        st.info("아직 누적 로그 파일이 없습니다. 교육을 1회 이상 진행하면 통계가 생성됩니다.")
        return

    try:
        df = pd.read_csv(LOG_FILE, encoding="utf-8-sig")
    except Exception as e:
        st.error(f"로그 파일을 읽지 못했습니다: {e}")
        return

    if df.empty:
        st.info("로그 데이터가 비어 있습니다.")
        return

    for col in ["awarded_score", "max_score", "question_index"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    if "question_code" not in df.columns:
        df["question_code"] = df["mission_key"].astype(str) + "_Q" + df["question_index"].astype(int).astype(str)

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

    name_series = df["name"].astype(str) if "name" in df.columns else pd.Series([""] * len(df))
    dept_series = df["department"].astype(str) if "department" in df.columns else pd.Series([""] * len(df))
    df["learner_key"] = name_series + "|" + dept_series
    df["question_label"] = df["mission_title"].astype(str) + " · Q" + df["question_index"].astype(int).astype(str)

    attempt_stats = (
        df.groupby(["question_code", "question_label"], as_index=False)
          .agg(
              attempts=("is_correct_norm", "count"),
              corrects=("is_correct_norm", "sum"),
              avg_score=("awarded_score", "mean"),
              max_score=("max_score", "max"),
          )
    )
    attempt_stats["attempt_correct_rate"] = (attempt_stats["corrects"] / attempt_stats["attempts"] * 100).round(1)

    df_sorted = df.sort_values("timestamp", ascending=True) if "timestamp" in df.columns else df.copy()
    first_attempt_df = df_sorted.drop_duplicates(subset=["learner_key", "question_code"], keep="first")

    first_stats = (
        first_attempt_df.groupby(["question_code"], as_index=False)
        .agg(
            first_attempts=("is_correct_norm", "count"),
            first_corrects=("is_correct_norm", "sum"),
        )
    )
    first_stats["first_correct_rate"] = (first_stats["first_corrects"] / first_stats["first_attempts"] * 100).round(1)

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
    chart_df = view_df[["문항", "첫 시도 정답률(%)"]].copy().set_index("문항")
    st.bar_chart(chart_df)

    st.caption(
        f"※ 주관식은 점수율 {int(TEXT_CORRECT_THRESHOLD*100)}% 이상을 '정답'으로 집계합니다. "
        "임계값은 TEXT_CORRECT_THRESHOLD로 조정할 수 있습니다."
    )

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

    play_sfx(SFX["conquer"])

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
    user_dept = st.session_state.user_info.get("dept", "")

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

    if user_dept:
        st.info(f"부서 포인트 ({user_dept}) · {DEPT_GUIDE.get(user_dept, '기본 준법 원칙을 확인하세요.')}")

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

        play_sfx(SFX["correct"] if is_correct else SFX["wrong"])
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
        play_sfx(SFX["correct"] if is_good else SFX["wrong"])
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

if st.session_state.stage == "intro":
    st.title("🛡️ 2026 Compliance Adventure")
    st.caption("Guardian Training · 컴플라이언스 테마 정복형 학습")

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

    name = st.text_input("성함")
    dept = st.selectbox("소속 부서", ["영업팀", "구매팀", "인사팀", "IT지원팀", "감사팀"])

    if st.button("모험 시작하기", use_container_width=True):
        if name.strip():
            st.session_state.user_info = {"name": name.strip(), "dept": dept}
            st.session_state.stage = "map"
            st.rerun()
        else:
            st.warning("성함을 입력해주세요. (공백만 입력 불가)")

elif st.session_state.stage == "map":
    user_name = st.session_state.user_info.get("name", "가디언")
    user_dept = st.session_state.user_info.get("dept", "")

    st.title(f"🗺️ {user_name} 가디언의 지도")
    if user_dept:
        st.caption(f"부서 포인트 · {DEPT_GUIDE.get(user_dept, '')}")

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

elif st.session_state.stage == "ending":
    user_name = st.session_state.user_info.get("name", "가디언")
    user_dept = st.session_state.user_info.get("dept", "")
    score = st.session_state.score
    grade = get_grade(score, TOTAL_SCORE)

    total_attempts = len(st.session_state.attempt_history)
    wrong_like = sum(1 for r in st.session_state.attempt_history if str(r.get("is_correct", "")) in ["N", "PARTIAL"])

    st.balloons()
    if not st.session_state.get("played_final_fanfare", False):
        play_sfx(SFX["final"])
        st.session_state.played_final_fanfare = True

    st.title("🏆 Guardian Training Complete")
    st.success(f"{user_name} 가디언님, 모든 테마를 정복했습니다!")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            f"""
            <div class='card'>
              <div class='card-title'>최종 결과</div>
              <div>소속: <b>{user_dept}</b></div>
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

    with st.expander("🛠 관리자용 문항 통계 보기", expanded=False):
        render_admin_question_stats()

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
