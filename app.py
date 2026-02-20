import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. 페이지 설정 및 디자인 ---
st.set_page_config(page_title="2026 컴플라이언스 어드벤처", layout="wide")

# CSS: 게임 인터페이스 느낌을 주기 위한 스타일
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    /* 버튼 스타일 강화 */
    div.stButton > button:first-child {
        background-color: #00C853 !important; color: white !important;
        border-radius: 10px !important; font-size: 18px !important; font-weight: bold !important;
        height: 50px !important; width: 100% !important; border: none !important;
    }
    .status-box {
        background-color: #1A1C24; padding: 20px; border-radius: 15px;
        border-left: 5px solid #00C853; margin-bottom: 20px;
    }
    .mission-card {
        background-color: #262730; padding: 15px; border-radius: 10px; border: 1px solid #464B5F;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 시스템 상태 초기화 ---
if 'stage' not in st.session_state:
    st.session_state.stage = 'intro'
    st.session_state.score = 0
    st.session_state.completed = []
    st.session_state.user_info = {}

# --- 3. 이미지 에셋 (제가 생성해 드린 이미지들입니다) ---
IMAGES = {
    "world_map": "https://r.jina.ai/i/06be6331908a4628a50f111534f40f0c",
    "clean_master": "https://r.jina.ai/i/9c458793b80b4396b27d49833503953e", # 클린 마스터 캐릭터
}

# --- 4. 시나리오 데이터 ---
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

# --- 5. 게임 로직 ---

# [인트로 화면]
if st.session_state.stage == 'intro':
    st.title("🛡️ 2026 컴플라이언스 어드벤처")
    st.image(IMAGES["world_map"], use_container_width=True, caption="[준법수호 지도] 3대 구역을 정복하세요!")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("신규 가디언 등록")
        name = st.text_input("성함")
        dept = st.selectbox("소속 부서", ["영업팀", "구매팀", "인사팀", "IT지원팀", "감사팀"])
        if st.button("어드벤처 시작"):
            if name:
                st.session_state.user_info = {"name": name, "dept": dept}
                st.session_state.stage = 'map'
                st.rerun()
    with col2:
        st.info("💡 **게임 안내**\n\n하도급, 보안, 공정거래 3가지 구역의 미션을 모두 클리어하세요. 획득한 점수는 부서 KPI에 반영됩니다.")

# [월드 맵 화면]
elif st.session_state.stage == 'map':
    st.header(f"📍 {st.session_state.user_info.get('name')} 가디언의 작전 지도")
    st.image(IMAGES["world_map"], width=700)
    
    st.write("진입하고 싶은 구역을 선택하세요:")
    cols = st.columns(3)
    for i, (key, data) in enumerate(SCENARIOS.items()):
        with cols[i]:
            if key in st.session_state.completed:
                st.success(f"✅ {data['title']} 완료")
            else:
                if st.button(f"{data['title']} 진입", key=f"btn_{key}"):
                    st.session_state.current_mission = key
                    st.session_state.stage = 'mission'
                    st.rerun()

    if len(st.session_state.completed) == 3:
        st.write("---")
        if st.button("🏁 모든 미션 완료! 최종 결과 제출"):
            st.session_state.stage = 'ending'
            st.rerun()

# [미션 화면: 이미지 + 캐릭터 가이드 결합]
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
                    st.success("✨ 탁월한 선택입니다! 정답입니다.")
                    st.session_state.score += 100
                else:
                    st.error("🚨 리스크 감지! 오답입니다.")
                st.session_state.completed.append(m_key)
                st.session_state.stage = 'map'
                st.rerun()

# [엔딩 화면]
elif st.session_state.stage == 'ending':
    st.balloons()
    st.title("🏆 미션 클리어! 컴플라이언스 가디언")
    st.image(IMAGES["clean_master"], width=300)
    st.success(f"{st.session_state.user_info.get('name')} 님, 수고하셨습니다!")
    st.write(f"최종 점수: **{st.session_state.score} 점**")
    st.info("참여 기록이 성공적으로 전송되었습니다. 부서 KPI 점수에 반영될 예정입니다.")
    
    if st.button("처음으로 돌아가기"):
        st.session_state.clear()
        st.rerun()
