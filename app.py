import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. 페이지 설정 및 디자인 ---
st.set_page_config(page_title=2026 컴플라이언스 어드벤처, layout=wide)

# CSS 주입 게임 테마 및 버튼 디자인
st.markdown(
    style
    .stApp { background-color #0E1117; color #E0E0E0; }
    div.stButton  buttonfirst-child {
        background-color #00C853; color white; border-radius 10px;
        font-size 20px; font-weight bold; width 100%; height 60px;
        box-shadow 0 0 15px rgba(0, 200, 83, 0.4);
    }
    .status-box {
        background-color #1A1C24; padding 20px; border-radius 15px;
        border-left 5px solid #00C853; margin-bottom 20px;
    }
    style
    , unsafe_allow_html=True)

# --- 2. 시스템 상태 초기화 ---
if 'stage' not in st.session_state
    st.session_state.stage = 'intro'
    st.session_state.score = 0
    st.session_state.user_info = {}
    st.session_state.completed = []

# --- 3. 데이터 저장 함수 (KPI 집계용) ---
def save_data(name, dept, score)
    # 베타 버전에서는 로컬 CSV에 저장 (배포 환경에 따라 DB로 확장 가능)
    new_data = {
        날짜 datetime.now().strftime(%Y-%m-%d %H%M),
        성함 name,
        부서 dept,
        점수 score
    }
    try
        df = pd.read_csv(compliance_results.csv)
        df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
    except FileNotFoundError
        df = pd.DataFrame([new_data])
    df.to_csv(compliance_results.csv, index=False)

# --- 4. 미션 시나리오 데이터 ---
SCENARIOS = {
    subcontracting {
        title 🚜 하도급의 계곡,
        q 팀장님이 급한 건이라며 계약서 없이 먼저 작업을 지시하라고 합니다. 어떻게 할까요,
        options [속도가 생명! 구두로 먼저 지시한다, 법 위반입니다. 서면 발급 후 착공한다],
        answer 1,
        success 정답! '선발급 후착공' 원칙을 준수하셨습니다.,
        fail 오답! 서면 미발급은 중대한 법 위반 사항입니다.
    },
    security {
        title 🔐 보안의 요새,
        q 출처가 불분명한 '2026 인사평가.exe' 메일이 도착했습니다. 당신의 행동은,
        options [내 점수가 궁금하니 실행한다, 절대 클릭하지 않고 보안팀에 신고한다],
        answer 1,
        success 정답! 피싱 공격으로부터 사내 망을 보호했습니다.,
        fail 오답! 악성코드에 감염되어 회사 기밀이 유출되었습니다.
    },
    fairtrade {
        title 🏰 공정의 성,
        q 경쟁사 동기가 식사 자리에서 이번 입찰가를 서로 맞추자고 속삭입니다.,
        options [우정을 생각해 이번만 협조한다, 명백한 담합이므로 단호히 거절한다],
        answer 1,
        success 정답! 담합의 유혹을 물리치고 시장 질서를 지켰습니다.,
        fail 오답! 부당 공동행위로 엄청난 과징금을 물게 되었습니다.
    }
}

# --- 5. 게임 로직 구현 ---

# [인트로 사용자 정보 입력]
if st.session_state.stage == 'intro'
    st.title(🛡️ 2026 컴플라이언스 어드벤처)
    st.image(httpgoogleusercontent.comimage_generation_content0, use_column_width=True)
    with st.container()
        st.subheader(가디언 등록)
        name = st.text_input(성함)
        dept = st.selectbox(소속 부서, [영업팀, 구매팀, 인사팀, IT지원팀, 개발팀])
        if st.button(어드벤처 시작)
            if name
                st.session_state.user_info = {name name, dept dept}
                st.session_state.stage = 'map'
                st.rerun()
            else
                st.warning(성함을 입력해주세요.)

# [월드 맵 미션 선택]
elif st.session_state.stage == 'map'
    st.header(f📍 {st.session_state.user_info['name']} 가디언의 지도)
    st.write(각 구역을 클릭하여 미션을 해결하세요.)
    
    cols = st.columns(3)
    for i, (key, data) in enumerate(SCENARIOS.items())
        with cols[i]
            if key in st.session_state.completed
                st.success(f{data['title']} 완료! ✅)
            else
                st.info(data['title'])
                if st.button(f{data['title']} 진입)
                    st.session_state.current_mission = key
                    st.session_state.stage = 'mission'
                    st.rerun()

    if len(st.session_state.completed) == 3
        if st.button(🏁 최종 결과 확인 및 점수 제출)
            save_data(st.session_state.user_info['name'], st.session_state.user_info['dept'], st.session_state.score)
            st.session_state.stage = 'ending'
            st.rerun()

# [미션 수행 화면]
elif st.session_state.stage == 'mission'
    m_key = st.session_state.current_mission
    mission = SCENARIOS[m_key]
    
    st.markdown(fdiv class='status-box'h2{mission['title']}h2div, unsafe_allow_html=True)
    st.subheader(mission['q'])
    
    # 캐릭터 조언 (가정)
    st.chat_message(assistant).write(가디언님, 신중하게 선택하세요. 회사의 운명이 달렸습니다!)
    
    for idx, opt in enumerate(mission['options'])
        if st.button(opt, key=fopt_{idx})
            if idx == mission['answer']
                st.success(mission['success'])
                st.session_state.score += 100
            else
                st.error(mission['fail'])
            st.session_state.completed.append(m_key)
            st.session_state.stage = 'map'
            st.rerun()

# [엔딩 수료증 및 KPI 모니터링]
elif st.session_state.stage == 'ending'
    st.balloons()
    st.title(🏆 미션 클리어!)
    st.subheader(f{st.session_state.user_info['dept']} {st.session_state.user_info['name']} 가디언님)
    st.write(f최종 점수 {st.session_state.score}  300)
    st.info(귀하의 기록은 부서 KPI 점수에 안전하게 반영되었습니다.)
    
    if st.checkbox(베타 버전 관리자용 모니터링 데이터 보기)
        try
            df = pd.read_csv(compliance_results.csv)
            st.table(df)
        except
            st.write(아직 저장된 데이터가 없습니다.)

    if st.button(처음으로 돌아가기)
        st.session_state.clear()
        st.rerun()