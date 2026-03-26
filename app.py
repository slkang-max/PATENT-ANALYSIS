import streamlit as st
import os
import tempfile
from dotenv import load_dotenv
from utils.pdf_processor import extract_text_from_pdf, extract_images_from_pdf, create_pdf_report
from utils.llm_agent import analyze_patent, generate_defense_strategy, suggest_solutions, get_env_api_key, condense_to_strategic_report
from utils.search_api import get_google_patents_url

load_dotenv(override=True)

st.set_page_config(page_title="지능형 특허 분석 플랫폼", page_icon="💡", layout="wide")

# ─────────────────────────────────────────────
# 커스텀 CSS: 화이트 모드 + 고가독성
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@300;400;500;600;700&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background-color: #f8f9fb;
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif;
}

[data-testid="stHeader"] { background: transparent; }

/* 사이드바 */
[data-testid="stSidebar"] {
    background: #ffffff;
    border-right: 1px solid #e5e7eb;
}

/* 탭 */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: #f1f3f8;
    border-radius: 10px;
    padding: 4px;
    gap: 2px;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    background: transparent;
    color: #6b7280;
    border-radius: 8px;
    border: none;
    font-weight: 500;
    transition: all 0.2s ease;
}
[data-testid="stTabs"] [aria-selected="true"] {
    background: #ffffff !important;
    color: #2563eb !important;
    font-weight: 600;
/* 버튼 — Sky Blue (옅은 하늘색) */
.stButton > button {
    background: #3b82f6;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 0.48rem 1.5rem;
    font-weight: 700;
    font-size: 0.9rem;
    letter-spacing: 0.01em;
    transition: all 0.2s ease;
    box-shadow: 0 2px 8px rgba(59,130,246,0.25);
}
.stButton > button:hover {
    background: #2563eb;
    box-shadow: 0 4px 16px rgba(59,130,246,0.35);
    transform: translateY(-1px);
}
.stButton > button:active {
    transform: translateY(0);
    box-shadow: 0 1px 4px rgba(59,130,246,0.2);
}

/* 텍스트인풋 */
[data-testid="stTextInput"] input {
    border: 1px solid #d1d5db;
    border-radius: 8px;
    background: #ffffff;
    color: #111827;
}
[data-testid="stTextInput"] input:focus {
    border-color: #2563eb;
    box-shadow: 0 0 0 3px rgba(37,99,235,0.12);
}

/* 파일 업로더 */
[data-testid="stFileUploader"] {
    background: #f0f4ff;
    border: 2px dashed #93c5fd;
    border-radius: 10px;
}

/* 텍스트에어리어 */
textarea {
    border: 1px solid #d1d5db !important;
    border-radius: 8px !important;
    background: #ffffff !important;
    color: #111827 !important;
    font-family: 'Pretendard', monospace !important;
}

/* 체크박스 */
[data-testid="stCheckbox"] span { color: #374151 !important; }

p, li, label { color: #374151; }

/* 제목 계층 강조 */
h1 { color: #0f172a; font-size: 1.6rem !important; font-weight: 800 !important; }
h2 { color: #0f172a; font-size: 1.35rem !important; font-weight: 700 !important; }
h3 {
    color: #1e293b;
    font-size: 1.15rem !important;
    font-weight: 700 !important;
    border-bottom: 2px solid #e0e7ff;
    padding-bottom: 0.4rem;
    margin-bottom: 0.3rem;
}
h4 { color: #374151; font-size: 1rem !important; font-weight: 600 !important; }

/* 캡션 강조 */
[data-testid="stCaptionContainer"] p {
    color: #4b5563 !important;
    font-size: 0.83rem !important;
    font-weight: 500 !important;
}

hr { border-color: #e5e7eb; }

/* 성공/경고/에러 */
[data-testid="stAlert"] { border-radius: 8px; }
</style>
""", unsafe_allow_html=True)


# ─── 헬퍼 컴포넌트 ───

def render_hero():
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #eff6ff 0%, #f0f4ff 100%);
        border: 1px solid #bfdbfe;
        border-radius: 16px;
        padding: 1.6rem 2rem;
        margin-bottom: 1.4rem;
        display: flex;
        align-items: center;
        gap: 1rem;
    ">
        <span style="font-size: 2.2rem;">💡</span>
        <div>
            <div style="font-size: 1.4rem; font-weight: 700; color: #1e3a8a; margin-bottom: 0.25rem;">
                지능형 특허 분석 플랫폼
            </div>
            <div style="font-size: 0.875rem; color: #3b82f6; font-weight: 400;">
                Gemini AI 기반 · 특허 명세서 자동 분석 · 방어/회피 전략 도출 · 유사 특허 탐색
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


import re

def extract_patent_metrics(text):
    if not text:
        return "미검출", "미상"
    
    # 1. 청구항 추출
    claim_matches = re.findall(r'【청구항\s*\d+】|\[청구항\s*\d+\]|청구항\s*\d+', text)
    total_claims = len(claim_matches)
    dependent_count = len(re.findall(r'제\s*\d+\s*항에\s*있어서', text))
    independent_claims = max(1, total_claims - dependent_count) if total_claims > 0 else 0
    if independent_claims > total_claims: independent_claims = total_claims
    
    if total_claims == 0:
        claims_text = "미검출"
    else:
        claims_text = f"총 {total_claims}항 (독립 {independent_claims})"

    # 2. 출원인 추출
    applicant = "미상"
    patterns = [
        r'【출원인】\s*\n\s*([^\n]+)',
        r'\[출원인\]\s*\n\s*([^\n]+)',
        r'출원인\s*[:：]\s*([^\n]+)',
        r'출\s*원\s*인\s*([^\n]+)'
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            applicant = m.group(1).strip()
            applicant = re.sub(r'\(.*?\)', '', applicant).strip()
            applicant = re.sub(r'^[\d-]+\s*', '', applicant).strip()
            if applicant:
                break
            
    if len(applicant) > 16:
        applicant = applicant[:15] + "..."

    # 3. 도면 수 추출
    drawing_nums = []
    drawing_matches = re.finditer(r'【도\s*(\d+)】|\[도\s*(\d+)\]|도\s*(\d+)', text)
    for m in drawing_matches:
        for val in m.groups():
            if val and val.isdigit():
                drawing_nums.append(int(val))
    
    if drawing_nums:
        # 안전장치: 너무 큰 수는 도면 번호가 아닐 확률이 높음
        valid_nums = [n for n in drawing_nums if 0 < n < 400]
        actual_drawings = max(valid_nums) if valid_nums else 0
        drawing_text = f"{actual_drawings} 개" if actual_drawings > 0 else "미검출"
    else:
        drawing_text = "미검출"
        
    return claims_text, applicant, drawing_text


def render_metric_cards(claims_text, applicant, drawing_text, keyword_count):
    col1, col2, col3, col4 = st.columns(4)
    metrics = [
        (col1, "📝", "권리 범위", claims_text, "#eff6ff", "#2563eb"),
        (col2, "🏢", "출원인", applicant, "#fdf4ff", "#c026d3"),
        (col3, "🖼️", "도면 수", drawing_text, "#f0fdf4", "#16a34a"),
        (col4, "🔑", "핵심 키워드", f"{keyword_count} 개", "#fff7ed", "#ea580c"),
    ]
    for col, icon, label, value, bg, color in metrics:
        with col:
            st.markdown(f"""
            <div style="
                background: {bg};
                border: 1px solid {color}33;
                border-radius: 12px;
                padding: 1rem 0.5rem;
                text-align: center;
            ">
                <div style="font-size: 1.25rem;">{icon}</div>
                <div style="font-size: 1.15rem; font-weight: 700; color: {color}; margin: 0.25rem 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="{value}">
                    {value}
                </div>
                <div style="font-size: 0.73rem; color: #6b7280; font-weight: 600;">{label}</div>
            </div>
            """, unsafe_allow_html=True)

def render_result_card(content: str):
    """분석 결과를 흰 배경 카드 안에 표시하며 타이포그래피 강력 강조"""
    html = str(content)
    
    # 1. H3/H2 헤더 강조 (크고 파란색 폰트로 표출)
    html = re.sub(r'(?m)^### (.*?)$', r'<div style="font-size: 1.35rem; font-weight: 800; color: #1e3a8a; border-bottom: 2px solid #bfdbfe; padding-bottom: 0.35rem; margin-top: 1.5rem; margin-bottom: 0.6rem;">\1</div>', html)
    html = re.sub(r'(?m)^## (.*?)$', r'<div style="font-size: 1.5rem; font-weight: 800; color: #111827; margin-top: 1.8rem; margin-bottom: 0.8rem;">\1</div>', html)
    
    # 2. 볼드 강조
    html = re.sub(r'\*\*(.*?)\*\*', r'<strong style="color: #111827; font-weight: 800; font-size: 0.92rem;">\1</strong>', html)
    
    # 3. 리스트아이템
    html = re.sub(r'(?m)^[-*] (.*?)$', r'<li style="margin-left: 1.2rem; margin-bottom: 0.3rem;">\1</li>', html)

    # 개행 처리
    html = html.replace('\n', '<br>')

    st.markdown(f"""
    <div style="
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-left: 4px solid #2563eb;
        border-radius: 0 12px 12px 0;
        padding: 1.6rem 2.2rem;
        margin-top: 0.8rem;
        line-height: 1.75;
        color: #4b5563;
        font-size: 0.88rem;
        box-shadow: 0 1px 6px rgba(0,0,0,0.04);
    ">
    {html}
    </div>
    """, unsafe_allow_html=True)


def render_keyword_tags(keywords: list):
    if not keywords:
        return
    tags_html = "".join([
        f"""<span style="
            display: inline-block;
            background: #eff6ff;
            border: 1px solid #bfdbfe;
            color: #1d4ed8;
            border-radius: 999px;
            padding: 0.2rem 0.75rem;
            font-size: 0.78rem;
            font-weight: 600;
            margin: 0.2rem;
        ">{kw}</span>"""
        for kw in keywords
    ])
    st.markdown(f"""
    <div style="margin-top: 0.8rem;">
        <span style="color: #9ca3af; font-size: 0.78rem; font-weight: 600; letter-spacing: 0.05em;">
            핵심 키워드
        </span>
        <div style="margin-top: 0.35rem;">{tags_html}</div>
    </div>
    """, unsafe_allow_html=True)


def render_patent_search_buttons(search_keywords: str):
    """Google Patents + keywert 두 버튼을 나란히 표시"""
    gp_url = get_google_patents_url(search_keywords)
    ki_url = "https://www.keywert.com/"
    st.markdown(f"""
    <div style="display: flex; gap: 0.8rem; margin-top: 0.8rem; flex-wrap: wrap;">
        <a href="{gp_url}" target="_blank" style="
            display: inline-flex; align-items: center; gap: 0.4rem;
            background: #1e293b; color: #f8fafc;
            padding: 0.5rem 1.2rem; border-radius: 8px;
            text-decoration: none; font-weight: 600; font-size: 0.875rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.15);
        ">🔍 Google Patents에서 검색 ↗</a>
        <a href="{ki_url}" target="_blank" style="
            display: inline-flex; align-items: center; gap: 0.4rem;
            background: #ffffff; color: #374151;
            border: 1px solid #d1d5db;
            padding: 0.5rem 1.2rem; border-radius: 8px;
            text-decoration: none; font-weight: 600; font-size: 0.875rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        ">🇰🇷 키워트에서 검색 (keywert) ↗</a>
    </div>
    <div style="margin-top: 0.5rem; font-size: 0.78rem; color: #9ca3af;">
        keywert 접속 후 로그인하면 키워드 검색 결과를 바로 확인할 수 있습니다.
    </div>
    """, unsafe_allow_html=True)


# ─── 사이드바 다운로드 영역 (PDF 업로드 직후 표시) ───
def render_sidebar_download(results: dict, api_key: str):
    st.divider()
    st.markdown("""
    <div style="font-size: 0.83rem; font-weight: 600; color: #374151; margin-bottom: 0.5rem;">
        📥 리포트 다운로드
    </div>
    """, unsafe_allow_html=True)

    has_any = any(results.values())
    if not has_any:
        st.caption("분석을 먼저 실행하면 PDF를 다운로드할 수 있습니다.")

    selected_items = []
    if st.checkbox("요약 분석 포함", value=True, disabled=not results["summary"]):
        selected_items.append("summary")
    if st.checkbox("방어/회피 전략 포함", value=True, disabled=not results["strategy"]):
        selected_items.append("strategy")
    if st.checkbox("해결 방안 포함", value=True, disabled=not results["solution"]):
        selected_items.append("solution")

    if st.button("PDF 리포트 생성", disabled=not has_any):
        if not selected_items:
            st.warning("최소 1개 이상 선택하세요.")
        else:
            with st.spinner("전략적으로 리포트를 함축하는 중..."):
                try:
                    # 1. 전략적 함축 요약 생성
                    strategic_results = condense_to_strategic_report(results, api_key)
                    
                    # 2. 메트릭 정보 추출
                    claims_text, applicant, drawing_text = extract_patent_metrics(st.session_state.extracted_text)
                    metrics_dict = {
                        "claims": claims_text,
                        "applicant": applicant,
                        "drawings": drawing_text,
                        "keywords": ", ".join(st.session_state.keywords)
                    }
                    
                    # 3. PDF 생성 (함축된 결과 사용)
                    pdf_data = create_pdf_report(strategic_results, selected_items, metrics_dict)
                    st.download_button(
                        label="다운로드 ⬇️",
                        data=pdf_data,
                        file_name="strategic_patent_report.pdf",
                        mime="application/pdf"
                    )
                except Exception as e:
                    st.error(f"리포트 생성 오류: {e}")


# ──────────────────────────────────────────────
# 메인
# ──────────────────────────────────────────────
def main():
    render_hero()

    # 세션 상태 초기화
    defaults = {
        "results": {"summary": "", "strategy": "", "solution": ""},
        "keywords": [],
        "image_paths": [],
        "extracted_text": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    env_key = get_env_api_key()

    # ── 사이드바 ──
    with st.sidebar:
        st.markdown("""
        <div style="padding: 0.6rem 0 1rem;">
            <div style="font-size: 0.95rem; font-weight: 700; color: #111827;">⚙️ 서비스 설정</div>
        </div>
        """, unsafe_allow_html=True)

        if env_key and env_key != "your_api_key_here":
            st.success("✅ API 키 자동 로드 완료")
            api_key = env_key
            with st.expander("API 키 변경"):
                api_key = st.text_input("새 Gemini API Key", value=env_key, type="password")
        else:
            if env_key == "your_api_key_here":
                st.error("⚠️ .env의 예시 키를 실제 키로 수정하세요.")
            else:
                st.warning("🔑 API 키를 설정해 주세요.")
            api_key = st.text_input("Gemini API Key", type="password", placeholder="AIza...")
            st.caption("`.env` 파일에 키를 저장하면 자동 로드됩니다.")

        st.divider()
        st.markdown("""
        <div style="font-size: 0.83rem; font-weight: 600; color: #374151; margin-bottom: 0.5rem;">
            📄 분석 대상 문서
        </div>
        """, unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "PDF 명세서 업로드",
            type=["pdf"],
            label_visibility="collapsed"
        )

        if uploaded_file:
            st.markdown(f"""
            <div style="
                background: #f0fdf4; border: 1px solid #86efac;
                border-radius: 8px; padding: 0.5rem 0.8rem;
                font-size: 0.8rem; color: #15803d; margin-top: 0.4rem;
            ">✅ {uploaded_file.name}</div>
            """, unsafe_allow_html=True)

            # PDF 업로드 시 항상 다운로드 섹션 표시
            render_sidebar_download(st.session_state.results, api_key)

    # ── 메인 콘텐츠 ──
    if uploaded_file is not None:
        if not api_key:
            st.error("사이드바에서 Gemini API Key를 입력해 주세요.")
            return

        # 문서 처리 (최초 1회 또는 파일 변경 시)
        if "last_uploaded" not in st.session_state or st.session_state.last_uploaded != uploaded_file.name:
            with st.spinner("문서에서 텍스트 및 도면을 추출하고 있습니다..."):
                with tempfile.TemporaryDirectory() as tmp_dir:
                    tmp_file_path = os.path.join(tmp_dir, uploaded_file.name)
                    with open(tmp_file_path, "wb") as f:
                        f.write(uploaded_file.getvalue())

                    st.session_state.extracted_text = extract_text_from_pdf(tmp_file_path)

                    img_dir = os.path.join(os.getcwd(), "temp_images")
                    os.makedirs(img_dir, exist_ok=True)
                    for fname in os.listdir(img_dir):
                        try: os.remove(os.path.join(img_dir, fname))
                        except: pass

                    st.session_state.image_paths = extract_images_from_pdf(tmp_file_path, img_dir)

            st.session_state.last_uploaded = uploaded_file.name
            st.session_state.results = {"summary": "", "strategy": "", "solution": ""}
            st.session_state.keywords = []

        if not st.session_state.extracted_text:
            st.error("PDF 텍스트 추출 실패. 스캔본이 아닌지 확인하세요.")
            return

        # 메트릭 카드
        claims_text, applicant, drawing_text = extract_patent_metrics(st.session_state.extracted_text)
        render_metric_cards(
            claims_text=claims_text,
            applicant=applicant,
            drawing_text=drawing_text,
            keyword_count=len(st.session_state.keywords),
        )
        st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)

        # 탭
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📝 요약 분석", "🛡️ 방어/회피 전략", "💡 해결 방안",
            "🖼️ 특허 명세서(도면)", "🔍 유사특허 검색", "📄 원문 보기"
        ])

        with tab1:
            st.markdown("### 📝 특허 명세서 요약 분석")
            st.caption("핵심 청구항 · 기술 분류 · 발명의 목적을 자동 추출합니다.")
            if st.button("분석 실행", key="btn_summary"):
                with st.spinner("Gemini AI가 분석 중입니다..."):
                    result, data = analyze_patent(st.session_state.extracted_text, api_key)
                    if result:
                        st.session_state.results["summary"] = result
                        st.session_state.keywords = data
                        st.rerun()
                    else:
                        st.error(f"오류: {data.get('msg')}")
            if st.session_state.results["summary"]:
                render_result_card(st.session_state.results["summary"])
                render_keyword_tags(st.session_state.keywords)

        with tab2:
            st.markdown("### 🛡️ 방어 논리 및 회피 설계 전략")
            st.caption("선행 기술과의 차별점 · 특허 무효화 논거 · 설계 회피 방향을 제시합니다.")
            if st.button("전략 도출", key="btn_strategy"):
                with st.spinner("전략 수립 중..."):
                    result = generate_defense_strategy(st.session_state.extracted_text, api_key)
                    if isinstance(result, str):
                        st.session_state.results["strategy"] = result
                        st.rerun()
                    else:
                        st.error(f"오류: {result.get('msg')}")
            if st.session_state.results["strategy"]:
                render_result_card(st.session_state.results["strategy"])

        with tab3:
            st.markdown("### 💡 한계 극복 및 발전 방안 제시")
            st.caption("기술적 한계 분석 · 대체 솔루션 아이디어 · R&D 방향 제안")
            if st.button("해결책 모색", key="btn_solution"):
                with st.spinner("아이디어 구상 중..."):
                    result = suggest_solutions(st.session_state.extracted_text, api_key)
                    if isinstance(result, str):
                        st.session_state.results["solution"] = result
                        st.rerun()
                    else:
                        st.error(f"오류: {result.get('msg')}")
            if st.session_state.results["solution"]:
                render_result_card(st.session_state.results["solution"])

        with tab4:
            st.markdown("#### 🖼️ 원본 페이지 명세서(도면) 확인")
            if st.session_state.image_paths:
                claims_text, applicant, drawing_text = extract_patent_metrics(st.session_state.extracted_text)
                st.caption(f"문서 원본 전체: {len(st.session_state.image_paths)}페이지 (추출된 실제 도면 개수: {drawing_text})")
                cols = st.columns(2)
                for idx, img_path in enumerate(st.session_state.image_paths):
                    with cols[idx % 2]:
                        st.image(img_path, caption=f"원본 {idx+1}페이지", use_container_width=True)
            else:
                st.info("추출된 도면이 없습니다.")

        with tab5:
            st.markdown("#### 🔍 유사 특허 및 선행 기술 검색")
            st.markdown("""
            <div style="
                background: #fffbeb; border: 1px solid #fde68a;
                border-radius: 8px; padding: 0.6rem 0.9rem;
                font-size: 0.825rem; color: #92400e; margin-bottom: 0.8rem;
            ">
                💡 <b>Google Patents</b>를 기본으로 사용합니다. Keywert(키워트)는 로그인 후 검색이 가능합니다.
            </div>
            """, unsafe_allow_html=True)

            search_keywords_list = st.session_state.keywords or []
            search_keywords = st.text_input(
                "검색 키워드 (콤마로 구분)",
                value=", ".join(search_keywords_list),
                placeholder="예: 정수 필터, 역삼투압, 세라믹 멤브레인"
            )

            if search_keywords.strip():
                render_patent_search_buttons(search_keywords)
            else:
                st.info("검색어를 입력하면 특허 검색 링크가 표시됩니다.")

        with tab6:
            st.markdown("#### 📄 추출 원문")
            st.caption("PDF에서 추출된 텍스트 원문입니다.")
            st.text_area(
                "원문",
                value=st.session_state.extracted_text,
                height=420,
                disabled=True,
                label_visibility="collapsed"
            )

    elif not api_key:
        st.markdown("""
        <div style="
            background: #eff6ff; border: 1px solid #bfdbfe;
            border-radius: 14px; padding: 2rem; text-align: center; margin-top: 2rem;
        ">
            <div style="font-size: 2rem; margin-bottom: 0.6rem;">🔑</div>
            <div style="color: #1e40af; font-weight: 600; font-size: 1rem;">API 키를 먼저 설정하세요</div>
            <div style="color: #6b7280; font-size: 0.85rem; margin-top: 0.3rem;">
                왼쪽 사이드바에서 Gemini API Key를 입력하거나 .env 파일을 설정하세요.
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="
            background: #f8faff; border: 2px dashed #bfdbfe;
            border-radius: 16px; padding: 3rem 2rem; text-align: center; margin-top: 2rem;
        ">
            <div style="font-size: 2.8rem; margin-bottom: 0.8rem;">📂</div>
            <div style="color: #1e40af; font-weight: 600; font-size: 1.05rem;">특허 명세서 PDF를 업로드하세요</div>
            <div style="color: #9ca3af; font-size: 0.875rem; margin-top: 0.4rem;">
                왼쪽 사이드바의 업로드 영역에 PDF 파일을 드래그하거나 선택하세요.
            </div>
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
