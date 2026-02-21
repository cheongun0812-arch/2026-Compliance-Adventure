import streamlit as st
from datetime import datetime
from pathlib import Path
import csv
import io

# --- 1. 페이지 설정 및 스타일 ---
st.set_page_config(page_title="2026 Compliance Adventure", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #E0E0E0; }

    @keyframes blinking {
        0% { opacity: 1.0; transform: scale(1); }
        50% { opacity: 0.5; transform: scale(1.05); }
        100% { opacity: 1.0; transform: scale(1); }
    }

    .start-btn-box {
        animation: blinking 1.5s infinite;
        background-color: #00C853;
        color: white;
        padding: 15px 30px;
        border-radius: 50px;
        font-weight: bold;
        text-align: center;
        border: 2px solid #FFFFFF;
        box-shadow: 0 0 15px #00C853;
        display: inline-block;
        margin-top: -30px;
    }

    div.stButton > button:first-child {
        background-color: #00C853 !important;
        color: white !important;
        border-radius: 10px !important;
        font-size: 16px !important;
        font-weight: bold !important;
        min-height: 46px !important;
        border: none !important;
    }

    .status-box {
        background-color: #1A1C24;
        padding: 16px;
        border-radius: 15px;
        border-left: 5px solid #00C853;
        margin-bottom: 12px;
    }

    .explain-box {
        background-color: #151821;
        padding: 14px;
        border-radius: 12px;
        border: 1px solid #2A2F3A;
        margin-top: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. 경로/에셋 설정 ---
BASE_DIR = Path(__file__).parent if "__file__" in globals() else Path.cwd()
ASSET_DIR = BASE_DIR  # 필요하면 BASE_DIR / "assets" 로 변경
LOG_FILE = BASE_DIR / "compliance_training_log.csv"

IMAGES = {
    "world_map": ASSET_DIR / "world_map.png",
    "clean_master": ASSET_DIR / "master.png"
}

# --- 3. 시나리오 데이터 ---
SCENARIO_ORDER = ["subcontracting", "security", "fairtrade"]

SCENARIOS = {
    "subcontracting": {
        "title": "🚜 하도급의 계곡",
        "q": "팀장님이 급한 건이라며 계약서 없이 먼저 작업을 지시하라고 합니다. 어떻게 할까요?",
        "options": ["속도가 생명! 구두로 먼저 지시한다", "법 위반입니다. 서면 발급 후 착공한다"],
        "answer": 1,
        "hint": "하도급 업무에서는 '서면 발급' 시점이 핵심입니다.",
        "explain_correct": "정답입니다. 하도급법상 계약 조건이 명확히 기재된 서면을 먼저 발급한 뒤 착공해야 분쟁과 법적 리스크를 줄일 수 있습니다.",
        "explain_wrong": "오답입니다. 계약서 없이 먼저 착공하면 하도급법 위반 소지가 생기고, 대금/범위/책임 분쟁이 발생할 수 있습니다."
    },
    "security": {
        "title": "🔐 보안의 요새",
        "q": "출처가 불분명한 '2026 인사평가 결과.exe' 메일이 도착했습니다.",
        "options": ["내 점수가 궁금하니 실행한다", "절대 클릭하지 않고 보안팀에 신고한다"],
        "answer": 1,
        "hint": "실행 파일(.exe) + 출처 불명 메일 조합은 대표적인 보안 위험 신호입니다.",
        "explain_correct": "정답입니다. 출처 불명 실행 파일은 악성코드/랜섬웨어 위험이 크므로 즉시 신고하고 클릭하지 않는 것이 원칙입니다.",
        "explain_wrong": "오답입니다. 출처 불명 실행 파일을 열면 악성코드 감염, 정보 유출, 시스템 마비로 이어질 수 있습니다."
    },
    "fairtrade": {
        "title": "🏰 공정의 성",
        "q": "경쟁사 동기가 식사 자리에서 이번 입찰가를 서로 맞추자고 속삭입니다.",
        "options": ["우정을 생각해 이번만 협조한다", "명백한 담합이므로 단호히 거절한다"],
        "answer": 1,
        "hint": "경쟁사와 가격/물량/입찰 관련 대화를 맞추는 행위는 매우 위험합니다.",
        "explain_correct": "정답입니다. 입찰가 합의는 부당한 공동행위(담합)에 해당할 수 있어 즉시 거절하고 필요 시 보고 절차를 따르는 것이 안전합니다.",
        "explain_wrong": "오답입니다. 경쟁사와 입찰 정보를 맞추는 행위는 담합으로 판단될 수 있으며, 회사와 개인 모두 법적 제재를 받을 수 있습니다."
    }
}

DEPT_GUIDE = {
    "영업팀": "거래처 접점이 많으니 접대/리베이트·공정거래 이슈를 특히 조심하세요.",
    "구매팀": "계약·하도급·입찰 관련 문서화와 절차 준수가 핵심입니다.",
    "인사팀": "개인정보 보호, 채용 공정성, 평가 정보 보안이 중요합니다.",
    "IT지원팀": "피싱·악성코드·계정권한 관리가 핵심 리스크입니다.",
    "감사팀": "증빙 보존, 보고 체계, 내부통제 점검 관점이 중요합니다."
}

TOTAL_SCORE = len(SCENARIO_ORDER) * 100

# --- 4. 공통 유틸 함수 ---
def init_state():
    defaults = {
        "stage": "intro",               # intro -> map -> mission -> ending
        "score": 0,
        "completed": [],
        "user_info": {},
        "current_mission": None,
        "mission_feedback": {},         # {mission_key: {"is_correct": bool, "msg": str}}
        "attempt_counts": {},           # {mission_key: int}
        "attempt_history": []           # session 내 로그
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def show_image(image_key: str, **kwargs):
    path = IMAGES[image_key]
    if path.exists():
        st.image(str(path), **kwargs)
    else:
        st.warning(f"이미지 파일을 찾을 수 없습니다: {path.name}")

def append_attempt_log(mission_key: str, selected_idx: int, is_correct: bool):
    user = st.session_state.get("user_info", {})
    mission = SCENARIOS[mission_key]
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    row = {
        "timestamp": ts,
        "name": user.get("name", ""),
        "department": user.get("dept", ""),
        "mission_key": mission_key,
        "mission_title": mission["title"],
        "question": mission["q"],
        "selected_option": mission["options"][selected_idx],
        "is_correct": "Y" if is_correct else "N",
        "attempt_no_for_mission": st.session_state.attempt_counts.get(mission_key, 0)
    }

    # 세션 내 로그 저장
    st.session_state.attempt_history.append(row)

    # 파일 로그 저장 (실행환경에 따라 쓰기 권한 없을 수 있음)
    try:
        file_exists = LOG_FILE.exists()
        with open(LOG_FILE, "a", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=list(row.keys()))
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)
    except Exception as e:
        # 앱은 계속 동작하고, 로그 파일 저장 실패만 안내
        st.session_state["log_write_error"] = str(e)

def get_grade(score: int, total: int):
    ratio = (score / total) if total else 0
    if ratio >= 1.0:
        return "컴플라이언스 챔피언 🏅"
    if ratio >= 0.67:
        return "안전한 실무자 ✅"
    return "재학습 권장 📘"

def reset_game():
    st.session_state.clear()
    st.rerun()

init_state()

# --- 5. 화면 로직 ---

# [1단계: 인트로]
if st.session_state.stage == "intro":
    st.title("🛡️ 2026 컴플라이언스 어드벤처")
    show_image("world_map", use_container_width=True)

    st.markdown(
        "<div style='text-align:center;'><div class='start-btn-box'>ADVENTURE READY</div></div>",
        unsafe_allow_html=True
    )

    st.subheader("신규 가디언 등록")
    name = st.text_input("성함")
    dept = st.selectbox("소속 부서", ["영업팀", "구매팀", "인사팀", "IT지원팀", "감사팀"])

    if st.button("모험 시작하기"):
        cleaned_name = name.strip()
        if cleaned_name:
            st.session_state.user_info = {"name": cleaned_name, "dept": dept}
            st.session_state.stage = "map"
            st.rerun()
        else:
            st.warning("가디언의 이름을 입력해주세요. (공백만 입력 불가)")

# [2단계: 메인 지도]
elif st.session_state.stage == "map":
    user_name = st.session_state.user_info.get("name", "가디언")
    user_dept = st.session_state.user_info.get("dept", "")

    st.header(f"📍 {user_name} 가디언의 지도")
    show_image("world_map", width=700)

    if user_dept:
        st.caption(f"부서 맞춤 포인트: {DEPT_GUIDE.get(user_dept, '기본 준법 원칙을 지켜주세요.')}")

    st.write("진입할 관문을 선택하세요:")
    cols = st.columns(3)

    for i, key in enumerate(SCENARIO_ORDER):
        with cols[i]:
            data = SCENARIOS[key]
            if key in st.session_state.completed:
                st.success(f"✅ {data['title']} 완료")
            else:
                can_enter = True if i == 0 else (SCENARIO_ORDER[i - 1] in st.session_state.completed)
                if can_enter:
                    if st.button(f"{data['title']} 진입", key=f"btn_{key}"):
                        st.session_state.current_mission = key
                        st.session_state.stage = "mission"
                        st.rerun()
                else:
                    st.write("🔒 잠겨 있음")

    if len(st.session_state.completed) == len(SCENARIO_ORDER):
        st.write("---")
        if st.button("🏁 최종 결과 확인 및 제출"):
            st.session_state.stage = "ending"
            st.rerun()

# [3단계: 미션 화면]
elif st.session_state.stage == "mission":
    # 안전장치: current_mission 누락/오염 방지
    m_key = st.session_state.get("current_mission")
    if not m_key or m_key not in SCENARIOS:
        st.warning("미션 정보가 올바르지 않아 지도로 돌아갑니다.")
        st.session_state.stage = "map"
        st.rerun()

    mission = SCENARIOS[m_key]
    user_dept = st.session_state.user_info.get("dept", "")

    col_char, col_q = st.columns([1, 2])

    with col_char:
        show_image("clean_master", caption="[클린 마스터]")
        st.info("클린 마스터의 안내")
        with st.expander("💡 힌트 보기 (필요할 때만 열기)"):
            st.write(mission["hint"])
        if user_dept:
            st.caption(f"부서 관점: {DEPT_GUIDE.get(user_dept, '')}")

    with col_q:
        st.markdown(f"<div class='status-box'><h2>{mission['title']}</h2></div>", unsafe_allow_html=True)
        st.subheader(mission["q"])

        # 기존 피드백 표시
        feedback = st.session_state.mission_feedback.get(m_key)
        if feedback:
            if feedback["is_correct"]:
                st.success(feedback["title"])
            else:
                st.error(feedback["title"])
            st.markdown(
                f"<div class='explain-box'>{feedback['body']}</div>",
                unsafe_allow_html=True
            )

        # 정답 처리 완료 후에는 옵션 숨기고 복귀 버튼만 표시
        if m_key in st.session_state.completed:
            if st.button("🗺️ 지도로 돌아가기"):
                st.session_state.stage = "map"
                st.rerun()
        else:
            # 보기 버튼들
            for idx, opt in enumerate(mission["options"]):
                if st.button(opt, key=f"opt_{m_key}_{idx}"):
                    # 시도 횟수 증가
                    st.session_state.attempt_counts[m_key] = st.session_state.attempt_counts.get(m_key, 0) + 1

                    is_correct = (idx == mission["answer"])
                    append_attempt_log(mission_key=m_key, selected_idx=idx, is_correct=is_correct)

                    if is_correct:
                        # 중복 완료 방지
                        if m_key not in st.session_state.completed:
                            st.session_state.completed.append(m_key)
                            st.session_state.score += 100

                        st.session_state.mission_feedback[m_key] = {
                            "is_correct": True,
                            "title": "✨ 정답입니다! 리스크를 방어했습니다.",
                            "body": (
                                f"{mission['explain_correct']}<br><br>"
                                f"✅ 현재 점수: <b>{st.session_state.score} / {TOTAL_SCORE}</b><br>"
                                f"🔁 이 미션 시도 횟수: <b>{st.session_state.attempt_counts[m_key]}회</b>"
                            )
                        }
                    else:
                        st.session_state.mission_feedback[m_key] = {
                            "is_correct": False,
                            "title": "🚨 오답입니다! 다시 판단해보세요.",
                            "body": (
                                f"{mission['explain_wrong']}<br><br>"
                                "다시 시도해서 올바른 대응을 선택해보세요."
                            )
                        }

                    st.rerun()

            # 오답 피드백이 있을 때만 안내 버튼 제공 (선택사항)
            feedback = st.session_state.mission_feedback.get(m_key)
            if feedback and not feedback["is_correct"]:
                if st.button("↻ 해설 확인했어요. 다시 풀기", key=f"retry_{m_key}"):
                    st.session_state.mission_feedback.pop(m_key, None)
                    st.rerun()

# [4단계: 엔딩]
elif st.session_state.stage == "ending":
    user_name = st.session_state.user_info.get("name", "가디언")
    user_dept = st.session_state.user_info.get("dept", "")
    score = st.session_state.score
    grade = get_grade(score, TOTAL_SCORE)

    total_attempts = len(st.session_state.attempt_history)
    wrong_attempts = sum(1 for r in st.session_state.attempt_history if r["is_correct"] == "N")

    st.balloons()
    st.title("🏆 미션 컴플리트!")
    show_image("clean_master", width=300)

    st.success(f"{user_name} 가디언님, 수고하셨습니다!")
    st.write(f"소속: **{user_dept}**")
    st.write(f"최종 준법 점수: **{score} / {TOTAL_SCORE}**")
    st.write(f"등급: **{grade}**")
    st.write(f"총 시도 횟수: **{total_attempts}회** / 오답 시도: **{wrong_attempts}회**")

    if "log_write_error" in st.session_state:
        st.warning(f"참고: 파일 로그 저장은 실패했지만 앱 진행에는 문제가 없습니다. ({st.session_state['log_write_error']})")

    # 세션 로그 다운로드
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
            mime="text/csv"
        )

    if st.button("다시 도전하기"):
        reset_game()
