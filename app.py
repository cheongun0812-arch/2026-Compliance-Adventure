import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. 페이지 설정 및 애니메이션 CSS ---
st.set_page_config(page_title="2026 Compliance Adventure", layout="centered")

st.markdown("""
    <style>
    /* 배경 및 기본 스타일 */
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    
    /* 시작 버튼 깜박임 애니메이션 */
    @keyframes blinking {
        0% { opacity: 1.0; transform: scale(1); }
        50% { opacity: 0.5; transform: scale(1.1); }
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
        margin-top: -50px; /* 이미지 위에 겹치게 조정 */
    }

    div.stButton > button:first-child {
        background-color: #00C853 !important; color: white !important;
        border-radius: 10px !important; font-size: 18px !important; font-weight: bold !important;
        height: 50px !important; width: 100% !important; border: none !important;
    }

    .status-box {
        background-color: #1A1C24; padding: 20px; border-radius: 15px;
        border-left: 5px solid #00C853; margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 이미지 에셋 정의 (오류 해결 핵심) ---
IMAGES = {
    "world_map": "world_map.png",
    "clean_master": "master.png"
}

# --- 3. 게임 상태 및 데이터 초기화 ---
if 'stage' not in st.session_state:
    st.session_state.stage = 'intro' # intro -> map -> mission -> map -> ending
    st.session_state.score = 0
    st.session_state.completed = []
    st.session_state.user_info = {}

# 시나리오 데이터
SCENARIOS = {
    "subcontracting": {
        "title": "🚜 하도급의 계곡",
        "q": "팀장님이 급한 건이라며 계약서 없이 먼저 작업을 지시하라고 합니다. 어떻게 할까요?",
        "options": ["속도가 생명! 구두로 먼저 지시한다", "법 위반입니다. 서면 발급 후 착공한다"],
        "answer": 1,
        "advice": "가디언님, 하도급법의 '선발급 후착공' 원칙을 기억하세요! 이대로 진행하면 나중에 큰 문제가 됩니다."
    },
    "security": {
        "title": "🔐 보안의 요새",
        "q": "출처가 불분명한 '2026 인사평가 결과.exe' 메일이 도착했습니다.",
        "options": ["내 점수가 궁금하니 실행한다", "절대 클릭하지 않고 보안팀에 신고한다"],
        "answer": 1,
        "advice": "알 수 없는 출처의 메일은 절대 클릭 금지입니다! 피싱 메일은 단 한 번의 실수로도 치명적입니다."
    },
    "fairtrade": {
        "title": "🏰 공정의 성",
        "q": "경쟁사 동기가 식사 자리에서 이번 입찰가를 서로 맞추자고 속삭입니다.",
        "options": ["우정을 생각해 이번만 협조한다", "명백한 담합이므로 단호히 거절한다"],
        "answer": 1,
        "advice": "이건 전형적인 '부당한 공동행위(담합)'의 시작입니다. 사적인 친분보다 법적 원칙이 우선입니다!"
    }
}

# --- 4. 게임 로직 구현 ---

# [1단계: 인트로 및 등록]
if st.session_state.stage == 'intro':
    st.title("🛡️ 2026 컴플라이언스 어드벤처")
    st.image(IMAGES["world_map"], use_container_width=True)
    
    # 애니메이션 효과 버튼박스
    st.markdown("<div style='text-align: center;'><div class='start-btn-box'>ADVENTURE READY</div></div>", unsafe_allow_html=True)
    
    with st.container():
        st.subheader("신규 가디언 등록")
        name = st.text_input("성함")
        dept = st.selectbox("소속 부서", ["영업팀", "구매팀", "인사팀", "IT지원팀", "감사팀"])
        if st.button("모험 시작하기"):
            if name:
                st.session_state.user_info = {"name": name, "dept": dept}
                st.session_state.stage = 'map'
                st.rerun()
            else:
                st.warning("가디언의 이름을 입력해주세요.")

# [2단계: 메인 작전 지도]
elif st.session_state.stage == 'map':
    st.header(f"📍 {st.session_state.user_info.get('name')} 가디언의 지도")
    st.image(IMAGES["world_map"], width=700)
    
    st.write("진입할 관문을 선택하세요:")
    cols = st.columns(3)
    
    # 스테이지 순차적 오픈 로직
    mission_keys = list(SCENARIOS.keys())
    
    for i, key in enumerate(mission_keys):
        with cols[i]:
            data = SCENARIOS[key]
            if key in st.session_state.completed:
                st.success(f"✅ {data['title']} 완료")
            else:
                # 이전 단계 완료 여부 확인 (순차적 진행)
                can_enter = True if i == 0 else (mission_keys[i-1] in st.session_state.completed)
                
                if can_enter:
                    if st.button(f"{data['title']} 진입", key=f"btn_{key}"):
                        st.session_state.current_mission = key
                        st.session_state.stage = 'mission'
                        st.rerun()
                else:
                    st.write("🔒 잠겨 있음")

    if len(st.session_state.completed) == 3:
        st.write("---")
        if st.button("🏁 최종 결과 확인 및 제출"):
            st.session_state.stage = 'ending'
            st.rerun()

# [3단계: 개별 미션 화면]
elif st.session_state.stage == 'mission':
    m_key = st.session_state.current_mission
    mission = SCENARIOS[m_key]
    
    col_char, col_q = st.columns([1, 2])
    
    with col_char:
        st.image(IMAGES["clean_master"], caption="[클린 마스터]")
        st.chat_message("assistant").write(mission["advice"])
        
    with col_q:
        st.markdown(f"<div class='status-box'><h2>{mission['title']}</h2></div>", unsafe_allow_html=True)
        st.subheader(mission['q'])
        
        for idx, opt in enumerate(mission['options']):
            if st.button(opt, key=f"opt_{m_key}_{idx}"):
                if idx == mission['answer']:
                    st.success("✨ 정답입니다! 리스크를 방어했습니다.")
                    st.session_state.score += 100
                else:
                    st.error("🚨 오답입니다! 규정 위반이 감지되었습니다.")
                st.session_state.completed.append(m_key)
                st.session_state.stage = 'map'
                st.rerun()

# [4단계: 엔딩 화면]
elif st.session_state.stage == 'ending':
    st.balloons()
    st.title("🏆 미션 컴플리트!")
    st.image(IMAGES["clean_master"], width=300)
    st.success(f"{st.session_state.user_info.get('name')} 가디언님, 수고하셨습니다!")
    st.write(f"최종 준법 점수: **{st.session_state.score} / 300**")
    
    if st.button("다시 도전하기"):
        st.session_state.clear()
        st.rerun()
