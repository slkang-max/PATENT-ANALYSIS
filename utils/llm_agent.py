import google.generativeai as genai
import re
import os
import streamlit as st
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv(override=True)

def get_env_api_key():
    if "GEMINI_API_KEY" in st.secrets:
        return st.secrets["GEMINI_API_KEY"]
    return os.getenv("GEMINI_API_KEY")

def analyze_patent(text, api_key):
    """Gemini API를 이용한 특허 요약 분석"""
    try:
        genai.configure(api_key=api_key)
        # 쿼터가 더 넉넉한 안정 모델로 변경
        model = genai.GenerativeModel('gemini-flash-latest')
        
        prompt = f"""
        다음은 특허 명세서 원문입니다. 이 내용을 바탕으로 특허의 전반적인 요약 정보를 만들어 주세요.

        [요구사항]
        - 발명의 명칭, 기술 분야, 해결하려는 과제(목적), 핵심 구성 요소를 명확하게 요약해 주세요.
        - 전문 용어를 최대한 알기 쉽게 풀어서 설명해 주세요.
        - 답변 마지막에 이 특허를 대표하는 '핵심 키워드 5개'를 콤마(,)로 구분하여 [KEYWORDS] 형식으로 제공해 주세요. 예: [KEYWORDS] 인공지능, 자율주행, 라이다, 센서퓨전, 신경망
        
        [명세서 원문]
        {text[:15000]}
        """
        response = model.generate_content(prompt)
        result_text = response.text
        return _parse_keywords(result_text)
    except Exception as e:
        return None, {"msg": str(e)}

def generate_defense_strategy(text, api_key):
    """Gemini API를 이용한 방어 및 회피 전략 도출"""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-flash-latest')
        
        prompt = f"""
        다음은 특허 명세서 원문입니다. 이 기술에 대한 방어 전략과 회피(우회) 설계 전략을 도출해 주세요.

        [요구사항]
        - 1. 방어 전략: 청구항을 분석하여, 경쟁 회사가 침해하기 어렵도록 권리 범위를 강화하거나 좁히는 논리를 제시해 주세요.
        - 2. 회피 전략: 만약 우리가 이 특허를 피해 경쟁 제품을 만들어야 한다면, 어떤 구성요소를 변경, 대체, 또는 삭제하여 우회 설계를 할 수 있는지 구체적인 아이디어를 3가지 이상 제시해 주세요.
        
        [명세서 원문]
        {text[:15000]}
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return {"msg": str(e)}

def suggest_solutions(text, api_key):
    """Gemini API를 이용한 기술 발전 방안 제시"""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-flash-latest')
        
        prompt = f"""
        다음은 특허 명세서 원문입니다. 이 발명이 가진 한계점이나 단점을 극복하고, 기술적으로 더 발전시킬 수 있는 솔루션을 제안해 주세요.

        [요구사항]
        - 현재 발명의 구조적, 또는 원리적 한계점 분석
        - 해당 한계를 극복하기 위해 최신 기술(AI, IoT, 신소재 등)이나 새로운 메커니즘을 접목하는 아이디어 3가지 이상 제시
        
        [명세서 원문]
        {text[:15000]}
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return {"msg": str(e)}

def condense_to_strategic_report(content_dict, api_key):
    """분석 결과를 전문가용 1페이지 리포트 형식으로 전략적으로 함축 요약"""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-flash-latest')
        
        # 합친 컨텐츠 구성
        full_context = f"""
        [기본 요약 분석]
        {content_dict.get('summary', '정보 없음')}
        
        [방어 및 회피 전략]
        {content_dict.get('strategy', '정보 없음')}
        
        [해결 및 발전 방안]
        {content_dict.get('solution', '정보 없음')}
        """
        
        prompt = f"""
        당신은 특허 전략 컨설턴트입니다. 다음의 상세 특허 분석 결과들을 바탕으로, 경영진이 한눈에 파악할 수 있는 '1페이지 핵심 전략 리포트'용 함축 요약을 작성해 주세요.
        
        [요구사항]
        - 각 섹션은 가장 중요한 핵심 포인트 3개 이내로 함축해 주세요.
        - 불필요한 미사여구는 빼고, 비즈니스/기술적 영향력이 큰 내용 위주로 '전략적'으로 작성해 주세요.
        - 결과는 반드시 아래의 태그 형식을 포함하여 답변해 주세요.
        
        [결과 형식]
        [SUMMARY]
        (함축된 요약 분석 내용)
        
        [STRATEGY]
        (함축된 방어/회피 전략 내용)
        
        [SOLUTION]
        (함축된 해결 및 발전 방안 내용)
        
        [분석 데이터]
        {full_context}
        """
        
        response = model.generate_content(prompt)
        res_text = response.text
        
        # 태그별 파싱
        condensed = {
            "summary": _extract_tag_content(res_text, "SUMMARY"),
            "strategy": _extract_tag_content(res_text, "STRATEGY"),
            "solution": _extract_tag_content(res_text, "SOLUTION")
        }
        return condensed
    except Exception as e:
        print(f"Error in condensation: {e}")
        return content_dict # 에러 발생 시 원본 반환

def _extract_tag_content(text, tag):
    """특정 태그 사이의 컨텐츠 추출"""
    pattern = rf'\[{tag}\](.*?)(?=\[|$)'
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return ""

def _parse_keywords(result_text):
    """결과 텍스트에서 키워드 추출"""
    keywords = []
    # **[KEYWORDS]** 또는 [KEYWORDS]: 등 LLM의 다양한 응답 포맷 대응
    match = re.search(r'\*?\*?\[KEYWORDS\]\*?\*?[:\s]*(.*?)(?:\n|$)', result_text, re.IGNORECASE)
    if match:
        keyword_str = match.group(1).replace('**', '').replace('*', '').strip()
        keywords = [k.strip() for k in keyword_str.split(',') if k.strip()]
        # 전체 텍스트에서는 매칭된 전체 줄 제거
        result_text = result_text.replace(match.group(0), '')
    return result_text.strip(), keywords
