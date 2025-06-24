# main.py
from typing import Any, Dict
from crawl.jobkorea import smart_crawl_jobkorea
from crawl.saramin import crawl_from_saramin
# from db.db_mysql import save_raw_data
from integration.integration_company_info import merge_company_info
from filtering.data_field_filtering import filtering_company_info
from decimal import Decimal, InvalidOperation
import json
import os
import webbrowser
from pathlib import Path
from jinja2 import Environment, FileSystemLoader


def decimal_default_encoder(obj):
    """JSON 직렬화 시 Decimal 객체를 처리하기 위한 사용자 정의 함수"""
    if isinstance(obj, Decimal):
        # Decimal 객체를 float 또는 str으로 변환.
        # 정밀도를 유지하려면 str이 더 안전합니다.
        return str(obj)
    raise TypeError(f'Object of type {obj.__class__.__name__} is not JSON serializable')


def crawl_company_data(company_name: str) -> tuple:
    """
    회사명을 받아서 각 사이트에서 크롤링을 수행하는 함수
    
    Args:
        company_name (str): 크롤링할 회사명
        
    Returns:
        tuple: (jobkorea_data, saramin_data)
    """
    print(f"🔍 '{company_name}' 회사 정보 크롤링 시작...")
    
    # 각 사이트 크롤링
    print("📊 잡코리아 크롤링 중...")
    jobkorea_data = smart_crawl_jobkorea(company_name)
    
    print("📊 사람인 크롤링 중...")
    saramin_data = crawl_from_saramin(company_name)
    
    return jobkorea_data, saramin_data


def process_raw_data(company_name: str, jobkorea_data: dict, saramin_data: dict) -> dict:
    """
    크롤링된 raw 데이터를 처리하고 저장하는 함수
    
    Args:
        company_name (str): 회사명
        jobkorea_data (dict): 잡코리아 크롤링 데이터
        saramin_data (dict): 사람인 크롤링 데이터
        
    Returns:
        dict: raw 데이터 딕셔너리
    """
    # raw 데이터 통합
    raw_dict = {
        "jobkorea": jobkorea_data,
        "saramin": saramin_data
    }
    
    # raw 데이터 DB 저장 (현재 주석 처리됨)
    # company_id = save_raw_data(company_name, raw_dict)
    
    # raw 데이터 출력
    print("📝 Raw 데이터:")
    print(json.dumps(raw_dict, indent=2, ensure_ascii=False))
    print("-" * 50)
    
    return raw_dict


def integrate_and_filter_data(jobkorea_data: dict, saramin_data: dict) -> dict:
    """
    데이터를 병합하고 정제하는 함수
    
    Args:
        jobkorea_data (dict): 잡코리아 크롤링 데이터
        saramin_data (dict): 사람인 크롤링 데이터
        
    Returns:
        dict: 정제된 회사 정보
    """
    print("🔄 데이터 병합 중...")
    # 수집 데이터 병합
    integration_result = merge_company_info(jobkorea_data, saramin_data)
    
    # 병합 결과 출력
    print("📋 병합된 데이터:")
    print(json.dumps(integration_result, indent=2, ensure_ascii=False))
    print("-" * 50)
    
    print("✨ 데이터 정제 중...")
    # 정제 로직 실행
    filtered_data = filtering_company_info(integration_result)
    
    return filtered_data


def save_filtered_data(company_name: str, filtered_data: dict):
    """
    정제된 데이터를 저장하는 함수
    
    Args:
        company_name (str): 회사명
        filtered_data (dict): 정제된 회사 정보
    """
    # 정제된 데이터 DB 저장 (현재 주석 처리됨)
    # company_id = save_raw_data(company_name, filtered_data)
    
    print("💾 정제된 데이터 저장 완료")


def format_korean_currency(value_str: str) -> str:
    """숫자 문자열을 한국식 화폐 단위(조, 억, 만)로 변환하는 함수"""
    try:
        value = int(value_str)
    except (ValueError, TypeError):
        return str(value_str)  # 숫자로 변환할 수 없으면 원본 문자열 반환

    sign = "-" if value < 0 else ""
    value = abs(value)

    if value >= 10**12:
        # 조 단위, 소수점 첫째 자리까지 표시
        return f"{sign}{value / 10**12:.1f}조"
    elif value >= 10**8:
        # 억 단위, 정수로 표시
        return f"{sign}{value // 10**8:,}억"
    elif value >= 10**4:
        # 만 단위, 정수로 표시
        return f"{sign}{value // 10**4:,}만"
    else:
        # 만 단위 미만은 쉼표만 추가
        return f"{sign}{value:,}"


def format_financial_history(financial_history: Any) -> Dict:
    """
    재무 히스토리 데이터의 숫자 값들을 한국식 화폐 단위로 포맷팅하는 함수
    
    Args:
        financial_history: 연도별 재무 데이터 딕셔너리 또는 JSON 문자열
        
    Returns:
        Dict: 숫자 값들이 포맷팅된 재무 데이터 딕셔너리
    """
    # financial_history가 JSON 문자열일 수 있으므로 먼저 파싱
    if isinstance(financial_history, str):
        try:
            financial_history = json.loads(financial_history)
        except json.JSONDecodeError:
            return {}  # 파싱 실패 시 빈 딕셔너리 반환
    
    if not isinstance(financial_history, dict):
        return {}

    formatted_data = {}
    for year, data in financial_history.items():
        formatted_year_data = {}
        for key, value in data.items():
            # 키 이름에 '합계'가 있는 경우 ' 합계'로 변경 (자산합계 -> 자산 합계)
            new_key = key.replace('합계', ' 합계') if '합계' in key and ' ' not in key else key
            formatted_year_data[new_key] = format_korean_currency(str(value))
        formatted_data[year] = formatted_year_data
    
    return formatted_data


def generate_html_report(filtered_data: dict) -> str:
    """
    정제된 데이터로 HTML 보고서를 생성하는 함수
    
    Args:
        filtered_data (dict): 정제된 회사 정보
        
    Returns:
        str: HTML 파일 경로
    """
    # templates 디렉토리 존재 확인 및 생성
    templates_dir = Path("templates")
    templates_dir.mkdir(exist_ok=True)
    
    # reports 디렉토리 존재 확인 및 생성
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    
    # Jinja2를 사용하여 템플릿 렌더링
    env = Environment(loader=FileSystemLoader('templates/'))
    template = env.get_template('report.html')
    
    # 템플릿 데이터 준비
    template_data = filtered_data.copy()

    # 주요 재무 지표 포맷팅
    for field in ['latest_revenue', 'latest_operating_income', 'latest_net_income']:
        if field in template_data and template_data[field] is not None:
            template_data[field] = format_korean_currency(str(template_data[field]))

    # financial_history 포맷팅
    template_data['financial_history'] = format_financial_history(
        template_data.get('financial_history')
    )
    
    html_output = template.render(data=template_data)
        
    # HTML 파일 저장
    safe_company_name = "".join(c for c in filtered_data.get('name', 'company') if c.isalnum() or c in (' ', '-', '_')).rstrip()
    html_filename = reports_dir / f"{safe_company_name}_report.html"
    
    with open(html_filename, "w", encoding="utf-8") as f:
        f.write(html_output)
    
    return str(html_filename.absolute())


def open_in_browser(file_path: str, auto_open: bool = True):
    """
    HTML 파일을 브라우저에서 열기
    
    Args:
        file_path (str): HTML 파일 경로
        auto_open (bool): 자동으로 브라우저를 열지 여부
    """
    if auto_open:
        try:
            # 파일 경로를 file:// URL로 변환
            file_url = f"file://{file_path}"
            print(f"🌐 브라우저에서 보고서를 여는 중...")
            print(f"📁 파일 경로: {file_path}")
            
            # 기본 브라우저에서 열기
            webbrowser.open(file_url)
            print("✅ 브라우저에서 보고서가 열렸습니다!")
            
        except Exception as e:
            print(f"❌ 브라우저 열기 실패: {e}")
            print(f"📂 수동으로 다음 파일을 열어주세요: {file_path}")
    else:
        print(f"📂 보고서가 생성되었습니다: {file_path}")


def main():
    """메인 실행 함수"""
    try:
        # 사용자 입력
        company_name = input("🏢 회사명을 입력하세요: ").strip()
        
        if not company_name:
            print("❌ 회사명을 입력해주세요.")
            return
        
        # 브라우저 자동 열기 옵션
        auto_open = input("📱 보고서를 브라우저에서 자동으로 열까요? (y/N): ").strip().lower()
        auto_open_browser = auto_open in ['y', 'yes', '예', 'ㅇ']
        
        # 1. 크롤링 수행
        jobkorea_data, saramin_data = crawl_company_data(company_name)
        
        # 2. Raw 데이터 처리
        raw_dict = process_raw_data(company_name, jobkorea_data, saramin_data)
        
        # 3. 데이터 병합 및 정제
        filtered_data = integrate_and_filter_data(jobkorea_data, saramin_data)
        
        # 4. 최종 결과 출력
        print("\n" + "=" * 60)
        print("🎉 정제된 회사 정보")
        print("=" * 60)
        print(json.dumps(filtered_data, indent=2, ensure_ascii=False, default=decimal_default_encoder))
        print("=" * 60)
        
        # 5. 정제된 데이터 저장
        save_filtered_data(company_name, filtered_data)
        
        # 6. HTML 보고서 생성
        print("\n📄 HTML 보고서 생성 중...")
        html_file_path = generate_html_report(filtered_data)
        
        # 7. 브라우저에서 열기
        open_in_browser(html_file_path, auto_open_browser)
        
        print("✅ 모든 작업이 완료되었습니다!")
        
    except KeyboardInterrupt:
        print("\n❌ 작업이 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"❌ 오류가 발생했습니다: {e}")
        import traceback
        traceback.print_exc()


# 독립적으로 HTML 보고서만 생성하는 함수
def generate_report_only(data_dict: dict, auto_open: bool = True):
    """
    기존 데이터로 HTML 보고서만 생성하는 함수
    
    Args:
        data_dict (dict): 회사 데이터
        auto_open (bool): 브라우저 자동 열기 여부
    """
    html_file_path = generate_html_report(data_dict)
    open_in_browser(html_file_path, auto_open)
    return html_file_path


if __name__ == "__main__":
    main()