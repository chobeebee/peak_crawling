import json
import re
import urllib.parse
import requests
import time
from collections import Counter # 빈도수 계산을 위해 추가 
from config.setting import USER_AGENT 

def ooai_crawler(query: str) -> dict:
    """
    oo.ai에 특정 쿼리 검색하여 검색 결과를 파싱하여 전환

    Args:
    query(str): 검색할 검색어 (예:  "삼성전자 주요 타겟 고객층") 
  
    Returns:
    dict: 검색 결과와 관련된 정보 담은 딕셔너리
        {
            'json': {'search_id': ..., 'full_html_answer': ..., 'plain_text_answer': ...}}
        }
        검색 실패 시 빈 딕셔너리 반환.
    """  
    encoded_query = urllib.parse.quote(query)

    # 1. CSRF 토큰 추출
    url = f'https://oo.ai/search?q={encoded_query}'
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"[{query}] 초기 페이지 접근 오류: {e}")
        return {}

    html = response.text
    token = None
    # 정규표현식을 사용하여 token 값 추출
    token_match = re.search(r'token:\s*"([^"]+)"', html)
    if token_match:
        token = token_match.group(1)

    # 추출된 토큰이 없다면 에러 메시지 출력
    if not token:
        print(f"[{query}] CSRF 토큰을 찾을 수 없습니다.")
        return {}
    
    # 추출된 토큰을 출력
    print({"json": {"csrf_token": token}})

    # 2. 검색 API 호출
    search_url = f"https://oo.ai/api/search?q={encoded_query}&lang=ko&tz=Asia/Seoul"
    headers = {
        "accept": "*/*",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "cookie": "_variant=stable; lang=ko",
        "origin": "https://oo.ai",
        "referer": f"https://oo.ai/search?q={encoded_query}",
        "user-agent": USER_AGENT,
        "x-csrf-token": f"Bearer {token}"
    }

    try:
        response = requests.post(search_url, headers=headers, timeout=20)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"[{query}] 검색 API 호출 오류: {e}")
        return {}
    
    parsed_data = parse_sse_response(response.text)
    print(json.dumps(parsed_data, ensure_ascii=False, indent=4))

    return parsed_data

def parse_sse_response(stream_data:str) -> dict:
    """
    SSE 형식의 응답을 파싱하여 최종 답변 추출

    Args:
        stream_data(str) : SEE 형식의 문자열 데이터
    
    Returns:
        dict: 파싱된 검색 결과(search_id, full_html_answer, plain_text_answer)
    """
    lines = stream_data.split('\n')
    final_answer_html = None
    sid = None
    for line in lines:
        if line.startswith('data:'):
            try:
                json_data_string = line[5:].strip()
                if json_data_string:
                    parsed_data = json.loads(json_data_string)
                    if parsed_data.get('type') == 'save':
                        if 'answer' in parsed_data:
                            final_answer_html = parsed_data['answer']
                        if 'id' in parsed_data:
                            sid = parsed_data['id']
                        if final_answer_html and sid:
                            break
            except Exception:
                # JSON 파싱 오류는 무시하고 다음 라인으로 진행
                continue

    plain_text_answer = None
    if final_answer_html:
        # <webblock> 태그와 그 내용 제거
        temp_answer = re.sub(r'<webblock>.*?</webblock>', '', final_answer_html, flags=re.DOTALL).strip()
        # 나머지 HTML 태그를 공백으로 변환 후, 여러 공백을 하나로 합치고 앞뒤 공백 제거
        plain_text_answer = re.sub(r'<[^>]+>', ' ', temp_answer)
        plain_text_answer = re.sub(r'\s+', ' ', plain_text_answer).strip()
    return {
        'json': {
            'search_id': sid,
            'full_html_answer': final_answer_html,
            'plain_text_answer': plain_text_answer
        }
    }

def enrich_company_data(company_name: str, existing_data: dict) -> dict:
    """
    기존 기업 데이터에서 부족한 필드를 oo.ai 검색을 통해 보완
    Args:
        company_name(str): 기업명
        existing_data(dict): 현재까지 수집된 기업 데이터 (필드: 값)
    
    Returns:
        dict: oo.ai 검색을 통해 보완된 기업 데이터(추후 통합 데이터와 병합 예정)   
    """
    # 보완할 필드
    fields_to_enrich = {
        "target_customers": f"{company_name} 기업의 주요 목표 고객층",
        "competitors": f"{company_name} 기업의 주요 경쟁사",
        "strengths": f"{company_name} 기업의 강점",
        "risk_factors": f"{company_name} 기업의 위험 요인",
        "recent_trends": f"{company_name} 기업의 최근 동향"
    }
    
    extra_prompt_guide = "에 대해 다음 가이드라인을 엄수하여 1문장으로 핵심만 요약해 주세요: 1. 불필요한 서론/결론 없이 바로 본론부터 시작. 2. 객관적인 정보만 포함. 3. 가능한 한 수치나 사실 기반으로 서술. 4. ~이다/입니다 체 종결 5. 관련 정보가 없을 경우 텍스트 대신 ''으로 출력."
    
    # 동일 쿼리 반복 실행 횟수
    NUM_RETRIES = 3 # 여러 번 호출하여 일관성 확보

    final_data = existing_data.copy()

    for field, query_template in fields_to_enrich.items():
        # 현재 필드 값이 비어있는지 확인
        if not final_data.get(field):
            print(f"🔍'{field}' 필드가 비어있습니다. OO.ai에서 검색을 시도합니다: '{query_template}'")
            
            collected_answers = []
            for i in range(NUM_RETRIES):
                print(f"  > 시도 {i+1}/{NUM_RETRIES}...")
                search_result = ooai_crawler(query_template + extra_prompt_guide)
                if search_result and search_result['json'].get('plain_text_answer'):
                    answer = search_result['json']['plain_text_answer'].strip()
                    if answer: # 빈 문자열이 아닌 유효한 답변만 추가
                        collected_answers.append(answer)
                # 약간의 딜레이를 주어 API 호출 간격을 띄움
                time.sleep(3)

            if collected_answers:
                # 가장 빈번하게 나온 답변 선택 (다양한 답변이 나올 경우 첫 번째 선택)
                # Counter를 사용하여 각 답변의 빈도수를 세고, 가장 많은 빈도수를 가진 답변을 선택
                most_common_answer = Counter(collected_answers).most_common(1)
                if most_common_answer:
                    chosen_answer = most_common_answer[0][0]
                    final_data[field] = chosen_answer
                    print(f"✅'{field}' 필드 채움 (최다빈도): {chosen_answer[:50]}...")
                else: # Counter가 비어있다면 (불가능한 경우지만 방어 코드)
                    print(f"❌ '{field}' 필드에 대한 OO.ai 검색 결과가 일관되지 않거나 유효하지 않습니다.")
                    final_data[field] = ""
            else:
                print(f"❌ '{field}' 필드에 대한 OO.ai 검색 결과가 없거나 유효하지 않습니다.")
                final_data[field] = ""

    return final_data

if __name__ == "__main__":
    company_name = input("기업명: ")
    print(f"\n===== oo.ai 정보 수집 시작: '{company_name}' =====")

    # 1. 초기 크롤링 데이터 (예시: 일부 필드가 비어있음)
    # initial_company_data = crawl_from_saramin(company_name)
    initial_company_data = {
        "name": "(주)깨끗한",
        "established_year": "2013년 2월 5일 설립",
        "company_type": "주식회사",
        "is_listed": True,
        "homepage": "",
        "description": "",
        "address": "경기 광주시 광주대로105번길 5-9",
        "industry": "토목시설물 건설업",
        "products_services": "",
        "key_executive": "김종찬",
        "employee_count": "",
        "employee_history": "",
        "latest_revenue": "",
        "latest_operating_income": "- 6,561만원",
        "latest_net_income": "- 2억 9,627만원",
        "latest_fiscal_year": "2024",
        "financial_history": {
            "2021": {
                "매출액": "2,764만원",
                "영업이익": "- 4,096만원",
                "당기순이익": "5억 364만원",
                "자본금": "5,000만원"
            },
            "2022": {
                "매출액": "923만원",
                "영업이익": "- 1억 824만원",
                "당기순이익": "10억 4,653만원",
                "자본금": "5,000만원"
            },
            "2023": {
                "영업이익": "- 1억 8,023만원",
                "당기순이익": "- 3억 8,809만원",
                "자본금": "5,000만원"
            },
            "2024": {
                "영업이익": "- 6,561만원",
                "당기순이익": "- 2억 9,627만원",
                "자본금": "5,000만원"
            }
        },
        "total_funding": "", # 총 투자 유치 금액 (원)
        "latest_funding_round": "", # 최근 투자 라운드 명칭
        "latest_funding_date": "", # 최근 투자 날짜
        "latest_valuation": "", # 최근 기업가치 (원)
        "investment_history": "", # 투자 히스토리
        "investors": "", # 주요 투자자 목록
        "market_cap": "", # 시가총액 (원)
        "stock_ticker": "", # 주식 종목 코드
        "stock_exchange": "", # 상장된 증권거래소
        "patent_count": "", # 특허 수
        "trademark_count": "", # 상표 수
        "ip_details": "", # 지식재산 상세 정보
        "tech_stack": "", # 기술 스택 키워드
        "recent_news": "", # 최근 뉴스/보도자료
        "target_customers": "",
        "competitors": "", 
        "strengths": "",
        "risk_factors": "",  
        "recent_trends": ""
    }
    print("\n--- '사람인' 초기 수집 데이터 (일부 필드 누락) ---")
    print(json.dumps(initial_company_data, ensure_ascii=False, indent=4))

    # 2. oo.ai 활용하여 부족한 기업 정보 필드 보완
    print("\n--- OO.ai를 활용한 데이터 보완 시작 ---")
    final_company_data = enrich_company_data(initial_company_data.get('name'), initial_company_data)
    # crawled_data = ooai_crawler(company_name)

    print("\n--- 최종 통합 데이터 ---")
    print(json.dumps(final_company_data, ensure_ascii=False, indent=4))