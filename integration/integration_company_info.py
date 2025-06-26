from copy import deepcopy

"""
잡코리아 기준으로 사람인 데이터 통합
- 잡코리아 데이터가 비어 있는 경우("", None, {}, [], "null") → 사람인 데이터로 보완
- is_listed 필드는 두 값 중 하나라도 True면 True로 설정
"""
def merge_company_info (jobkorea_data: dict, saramin_data: dict) -> dict :

    def is_empty(value):
        return value in ["", None, {}, [], "null"]
    
    # 기본 통합 데이터 템플릿
    basic_template = {
        "name": "", # 회사명
        "established_year": "", # 설립 연도
        "company_type": "", # 회사 유형 (주식회사, 유한회사 등)
        "is_listed": False, # 상장 여부
        "homepage": "", # 회사 홈페이지 URL
        "description": "", # 회사 설명
        "address": "", # 회사 주소
        "industry": "", # 산업 분야 정보
        "products_services": "", # 제품/서비스 이름 배열
        "key_executive": "", # 주요 경영진(대표자) 이름
        "employee_count": "", # 현재 직원 수
        "employee_history": "", # 과거 직원 수 추이
        "latest_revenue": "", # 최근 매출액 (원)
        "latest_operating_income": "", # 최근 영업이익 (원)
        "latest_net_income": "", # 최근 순이익 (원)
        "latest_fiscal_year": "", # 최근 재무 정보의 회계연도
        "financial_history": {}, # 과거 재무 정보 히스토리
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
        "target_customers": "", # 주요 목표 고객층
        "competitors": "", # 주요 경쟁사
        "strengths": "", # 강점
        "risk_factors": "", # 위험 요인  
        "recent_trends": "", # 최근 동향
    }

    # 데이터 수집이 실패된 경우
    if not isinstance(jobkorea_data, dict) or "error" in jobkorea_data:
        jobkorea_data = {}
    if not isinstance(saramin_data, dict) or "error" in saramin_data:
        saramin_data = {}

    # 모든 사이트가 실패한 경우
    if not jobkorea_data and not saramin_data:
        return deepcopy(basic_template)
    
    # 최종 통합 데이터
    merged_data = {}
    
    # 잡코리아 JSON 키 순서대로 탐색
    for key in basic_template:
        jobkorea_value = jobkorea_data.get(key)
        saramin_value = saramin_data.get(key)

        if key == "is_listed":
            merged_data[key] = bool(jobkorea_value) or bool(saramin_value)
        
        # financial_history 처리
        elif key == "financial_history":
            merged_data[key] = {}

            # 잡코리아 기준 먼저 복사
            if isinstance(jobkorea_value, dict):
                for year, jobkorea_year_data in jobkorea_value.items():
                    merged_data[key][year] = jobkorea_year_data.copy()

            # 사람인 연도별 병합
            if isinstance(saramin_value, dict):
                for year, saramin_year_data in saramin_value.items():
                    if year not in merged_data[key]:
                        merged_data[key][year] = saramin_year_data
                    else:
                        for metric, value in saramin_year_data.items():
                            if metric not in merged_data[key][year] or is_empty(merged_data[key][year][metric]):
                                merged_data[key][year][metric] = value

        # 일반 필드 처리
        elif is_empty(jobkorea_value) and not is_empty(saramin_value):
            merged_data[key] = saramin_value
        elif not is_empty(jobkorea_value):
            merged_data[key] = jobkorea_value
        else:
            merged_data[key] = deepcopy(basic_template[key])

    return merged_data