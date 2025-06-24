"""
잡코리아, 사람인 통합 정보를 데이터 정제
"""
import json
import re
from decimal import Decimal, InvalidOperation

# 금액 단위 숫자 변환
def korean_currency_to_number(currency_str):
    """
    한국 숫자 단위를 포함하는 금액 문자열을 Decimal 타입 숫자로 변환.
    예: "1조 4천억 원", "1,123억 8천만원", "- 262억 4,876만원"
    """
    if not isinstance(currency_str, str) or not currency_str.strip():
        return None

    currency_str = currency_str.strip().replace(" ", "").replace(",", "").replace("원", "").replace("만", "만원")
    
    is_negative = False
    if currency_str.startswith('-'):
        is_negative = True
        currency_str = currency_str[1:]

    total_value = Decimal(0)

    # '조' 단위 처리
    if "조" in currency_str:
        parts = currency_str.split("조", 1)
        try:
            val = Decimal(re.sub(r'[^0-9.]', '', parts[0])) # 숫자만 추출
            total_value += val * Decimal('1000000000000')
            currency_str = parts[1]
        except InvalidOperation:
            pass # 변환 실패 시 무시

    # '억' 단위 처리
    if "억" in currency_str:
        parts = currency_str.split("억", 1)
        try:
            val = Decimal(re.sub(r'[^0-9.]', '', parts[0]))
            total_value += val * Decimal('100000000')
            currency_str = parts[1]
        except InvalidOperation:
            pass

    # '만원' 단위 처리 (명시적으로 '만'이 붙은 경우)
    if "만원" in currency_str:
        parts = currency_str.split("만원", 1)
        try:
            val = Decimal(re.sub(r'[^0-9.]', '', parts[0]))
            total_value += val * Decimal('10000')
            currency_str = parts[1]
        except InvalidOperation:
            pass

    # 남아있는 순수 숫자 부분 처리 (예: "123456" 또는 "876")
    currency_str = re.sub(r'[^0-9.]', '', currency_str) # 숫자와 소수점만 남김
    if currency_str:
        try:
            total_value += Decimal(currency_str)
        except InvalidOperation:
            pass
            
    return -total_value if is_negative else total_value

# 직원수 숫자만 반환
def clean_employee_count(employee_count_str):
    """
    직원 수 문자열에서 숫자만 추출하여 정수로 반환.
    예: "510명" -> 510
    """
    if not isinstance(employee_count_str, str) or not employee_count_str.strip():
        return None
    
    match = re.search(r'(\d+)', employee_count_str)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return None
    return None

def to_json_string(data):
    """
    데이터를 JSON 문자열로 변환. 비어있으면 None을 반환.
    """
    if data is None or (isinstance(data, (dict, list)) and not data):
        return None
    try:
        return json.dumps(data, ensure_ascii=False)
    except TypeError:
        return None

def filtering_company_info(integration_result: dict) -> dict:
    """
    통합된 기업 정보를 MySQL 스키마에 맞춰 정제.
    """
    final_data = {} # 최종 정제 데이터

    # name : varchar(100) 
    final_data['name'] = integration_result.get('name', '').strip()

    # established_year : int
    try:
        final_data['established_year'] = int(integration_result.get('established_year')) if integration_result.get('established_year') else None
    except (ValueError, TypeError):
        final_data['established_year'] = None

    # company_type : varchar(50) 
    final_data['company_type'] = integration_result.get('company_type', '').strip() or None
    
    # is_listed : boolean
    final_data['is_listed'] = 1 if integration_result.get('is_listed') is True else 0

    #  homepage : varchar(255) 
    final_data['homepage'] = integration_result.get('homepage', '').strip() or None

    # description : text 
    final_data['description'] = integration_result.get('description', '').strip() or None

    # address: varchar(255)
    final_data['address'] = integration_result.get('address', '').strip() or None

    # industry: json
    # 현재 데이터는 단일 문자열이므로, 리스트에 담아 JSON으로 변환
    industry_data = integration_result.get('industry')
    if isinstance(industry_data, str) and industry_data.strip():
        final_data['industry'] = to_json_string([industry_data.strip()])
    elif isinstance(industry_data, list): # 이미 리스트 형태라면 그대로
        final_data['industry'] = to_json_string([item.strip() for item in industry_data if isinstance(item, str) and item.strip()])
    else:
        final_data['industry'] = None

    # products_services: json
    # 현재 데이터는 단일 문자열이므로, 쉼표로 분리하여 리스트에 담아 JSON으로 변환
    products_services_data = integration_result.get('products_services')
    if isinstance(products_services_data, str) and products_services_data.strip():
        final_data['products_services'] = to_json_string([s.strip() for s in products_services_data.split(',') if s.strip()])
    elif isinstance(products_services_data, list): # 이미 리스트 형태라면 그대로
        final_data['products_services'] = to_json_string([item.strip() for item in products_services_data if isinstance(item, str) and item.strip()])
    else:
        final_data['products_services'] = None
    
    # key_executive: varchar(100)
    final_data['key_executive'] = integration_result.get('key_executive', '').strip() or None

    # employee_count: int
    final_data['employee_count'] = clean_employee_count(integration_result.get('employee_count'))

    # employee_history: json
    # 현재 데이터에는 없지만, 기본 None으로 설정
    final_data['employee_history'] = to_json_string(integration_result.get('employee_history'))

    # latest_revenue: decimal(20,2) 
    final_data['latest_revenue'] = korean_currency_to_number(integration_result.get('latest_revenue'))

    # latest_operating_income: decimal(20,2) 
    final_data['latest_operating_income'] = korean_currency_to_number(integration_result.get('latest_operating_income'))

    # latest_net_income: decimal(20,2)
    final_data['latest_net_income'] = korean_currency_to_number(integration_result.get('latest_net_income'))

    # latest_fiscal_year: int 
    try:
        final_data['latest_fiscal_year'] = int(integration_result.get('latest_fiscal_year')) if integration_result.get('latest_fiscal_year') else None
    except (ValueError, TypeError):
        final_data['latest_fiscal_year'] = None

    # financial_history: json 
    # 내부 값도 숫자로 변환하여 저장
    financial_history_data = {}
    for year, data in integration_result.get('financial_history', {}).items():
        year_data = {}
        for key, value in data.items():
            year_data[key] = str(korean_currency_to_number(value)) if korean_currency_to_number(value) is not None else None
        financial_history_data[year] = year_data
    final_data['financial_history'] = to_json_string(financial_history_data)

    # total_funding: decimal(20,2)
    final_data['total_funding'] = korean_currency_to_number(integration_result.get('total_funding'))

    # latest_funding_round: varchar(50)
    final_data['latest_funding_round'] = integration_result.get('latest_funding_round', '').strip() or None

    # latest_funding_date: date
    # 날짜 형식에 대한 정보가 없으므로 현재는 None으로 처리
    # 만약 'YYYY-MM-DD' 형식이라면 다음과 같이 변환 가능:
    # try:
    #     date_str = integration_result.get('latest_funding_date')
    #     final_data['latest_funding_date'] = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None
    # except (ValueError, TypeError):
    #     final_data['latest_funding_date'] = None
    final_data['latest_funding_date'] = None # 현재 데이터에는 없음

    # latest_valuation: decimal(20,2) 
    final_data['latest_valuation'] = korean_currency_to_number(integration_result.get('latest_valuation'))

    # investment_history: json
    final_data['investment_history'] = to_json_string(integration_result.get('investment_history'))

    # investors: json 
    final_data['investors'] = to_json_string(integration_result.get('investors'))

    # market_cap: decimal(20,2)
    final_data['market_cap'] = korean_currency_to_number(integration_result.get('market_cap'))

    # stock_ticker: varchar(20)
    final_data['stock_ticker'] = integration_result.get('stock_ticker', '').strip() or None

    # stock_exchange: varchar(50)
    final_data['stock_exchange'] = integration_result.get('stock_exchange', '').strip() or None

    # patent_count: int
    try:
        final_data['patent_count'] = int(integration_result.get('patent_count')) if integration_result.get('patent_count') else None
    except (ValueError, TypeError):
        final_data['patent_count'] = None

    # trademark_count: int
    try:
        final_data['trademark_count'] = int(integration_result.get('trademark_count')) if integration_result.get('trademark_count') else None
    except (ValueError, TypeError):
        final_data['trademark_count'] = None

    # ip_details: json 
    final_data['ip_details'] = to_json_string(integration_result.get('ip_details'))

    # tech_stack: json 
    final_data['tech_stack'] = to_json_string(integration_result.get('tech_stack'))

    # recent_news: json
    final_data['recent_news'] = to_json_string(integration_result.get('recent_news'))

    # created_at: timestamp
    final_data['created_at'] = integration_result.get('created_at')
    print(f"final_data['created_at'] = {final_data['created_at']}")

    # updated_at: timestamp
    final_data['updated_at'] = integration_result.get('updated_at')

    return final_data