import urllib.parse


def get_google_patents_url(keywords_string: str) -> str:
    """
    키워드 문자열(콤마 분리)을 Google Patents 검색 URL로 변환합니다.
    - 한국 특허(KR)와 전체 언어를 모두 커버
    """
    keywords = [k.strip() for k in keywords_string.split(',') if k.strip()]
    query = " OR ".join([f'"{k}"' if ' ' in k else k for k in keywords])
    encoded_query = urllib.parse.quote(query)
    return f"https://patents.google.com/?q={encoded_query}&hl=ko"


def get_kipris_url(keywords_string: str) -> str:
    """
    키워드 문자열로 KIPRIS 통합검색 URL을 생성합니다.
    KIPRIS 스마트검색은 GET 파라미터 방식이 불안정하므로 직접 링크를 제공합니다.
    """
    keywords = [k.strip() for k in keywords_string.split(',') if k.strip()]
    query = " ".join(keywords)
    encoded_query = urllib.parse.quote(query)
    return f"http://kpat.kipris.or.kr/kpat/searchLogina.do?next=MainSearch&query={encoded_query}"


# 기존 코드와의 하위 호환성 유지
def get_kipris_search_url(keywords_string: str) -> str:
    return get_google_patents_url(keywords_string)
