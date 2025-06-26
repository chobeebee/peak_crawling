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
        "name": "",
        "established_year": "",
        "company_type": "",
        "is_listed": False,
        "homepage": "",
        "description": "",
        "address": "",
        "industry": "",
        "products_services": "",
        "key_executive": "",
        "employee_count": "",
        "employee_history": "",
        "latest_revenue": "",
        "latest_operating_income": "",
        "latest_net_income": "",
        "latest_fiscal_year": "",
        "financial_history": {},
        "total_funding": "",
        "latest_funding_round": "",
        "latest_funding_date": "",
        "latest_valuation": "",
        "investment_history": "",
        "investors": "",
        "market_cap": "",
        "stock_ticker": "",
        "stock_exchange": "",
        "patent_count": "",
        "trademark_count": "",
        "ip_details": "",
        "tech_stack": "",
        "recent_news": ""
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