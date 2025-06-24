from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import requests
import re
import json

# 기업명에서 (주), (주식회사) 접두사/접미사, 공백 제거
def filtering_company_name(name):
    """
    회사 이름에서 (주), (주식회사) 등 접두사/접미사 및 공백 제거
    """
    print(f"=== filtering_company_name 함수 실행 ===")
    removal_inc = re.sub(r'\(주\)', '', name, flags=re.IGNORECASE)
    removal_inc = re.sub(r'\(주식회사\)', '', removal_inc, flags=re.IGNORECASE)

    removal_inc = re.sub(r'\s+', ' ', removal_inc).strip()

    print(f"filtering_company_name 함수 결과: {removal_inc}")
    return removal_inc

# 기업명 검색, 검색된 기업명 비교
def compare_company_name(searching_keyword, searched_company):
    """
    두 회사 이름을 (주), (주식회사) 등의 문자열을 제외하고 비교
    """
    print(f"=== compare_company_name 함수 실행 ===")
    filtered_company_name = filtering_company_name(searched_company)

    result = searching_keyword == filtered_company_name
    print(f"searching_keyword == filtered_company_name 결과={result}")
    return result


# 재무현황 탭 이동
def get_financial_info_after_button(driver, target_button_text, wait_time=10):
    """
    재무정보 버튼을 클릭하고 재무현황 데이터 수집함. 
    """
    print(f"=== get_financial_info_after_button 함수 실행 ===")
    try:
        # 1. 좌측 모든 메뉴 버튼 찾기
        wait = WebDriverWait(driver, wait_time)
        buttons = wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul.menu_list button"))
        )

        found_button = None
        # 2. '재무정보' 텍스트 가진 버튼 식별
        for button in buttons:
            if button.text.strip() == target_button_text:
                found_button = button
                break

        if found_button:
            # 3. 버튼 클릭
            found_button.click()
            print(f"👉 버튼'{target_button_text}' 클릭.")

            # 4. 페이지 로딩
            wait.until(EC.presence_of_element_located(
                (By.CLASS_NAME, "main_content"))
            )
            print(f"✅ 버튼 클릭으로 [재무정보] 탭 사이트로 로딩 완료.")

            return BeautifulSoup(driver.page_source, 'html.parser')
        else:
            print(f"⚠️ 오류: '{target_button_text}' 텍스트를 가진 버튼을 찾을 수 없습니다.")
            return None

    except Exception as e:
            print(f"⚠️ 오류 발생: '{target_button_text}' 버튼을 찾거나 클릭하는 중 문제가 발생 - {e}")
            return None

# 재무현황 데이터 추출
def extract_financial_info(driver, company_data):
    """
    재무현황(매출, 영업이익, 순이익, 자본금)에 대한 재무정보 데이터 추출
    """
    print(f"=== extract_financial_info 함수 실행 ===")
    # 재무정보 탭으로 이동
    financial_soup = get_financial_info_after_button(driver, "재무정보")

    # 재무현황 데이터 div 선택        
    financial_sections = financial_soup.find_all('div', class_='box_finance')

    for box_finance in financial_sections:
        # 재무 필드명 (예: 매출액, 영업이익) 추출
        field_name_tag = box_finance.find('h3', class_='tit_finance')
        if not field_name_tag:
            continue
        field_name = field_name_tag.text.strip()
        print(f"👉 field_name = {field_name}")

        # 해당 재무 필드의 연도별 데이터 추출
        area_graph = box_finance.find('div', class_='area_graph')
        if area_graph:
            wrap_graphs = area_graph.find_all('div', class_='wrap_graph')
            for graph in wrap_graphs:
                year = graph.find('em', class_='tit_graph').text.strip()
                value_str = graph.find('span', class_='txt_value').text.strip()

                # company_data["financial_history"] 딕셔너리에 데이터 저장
                if year not in company_data["financial_history"]:
                    company_data["financial_history"][year] = {}
                
                # 요청하신 필드명으로 매핑 (총자산, 자본 총계는 HTML에 없어 현재 추출 불가)
                if field_name == "매출액":
                    company_data["financial_history"][year]["매출액"] = value_str
                elif field_name == "영업이익":
                    company_data["financial_history"][year]["영업이익"] = value_str
                elif field_name == "당기순이익":
                    company_data["financial_history"][year]["당기순이익"] = value_str
                elif field_name == "자본금":
                    company_data["financial_history"][year]["자본금"] = value_str

                print(f"✅ {field_name} => 년도{year}:{value_str}")

CHROME_DRIVER_PATH = "C:\\Users\\okoko\\Downloads\\chromedriver-win64\\chromedriver.exe" # 본인 경로로 수정 필요!
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

# === 사람인 웹크롤링 === 
def crawl_from_saramin(search_keyword: str) -> dict:
    """
    사람인 웹사이트에서 기업 정보를 크롤링하여 딕셔너리 형태로 반환
    """
    print(f"=== crawl_from_saramin 함수 실행 - '{search_keyword}' 기업 정보 수집 시작 ===")

    company_data = {
        "name": "", # 회사명
        "established_year": "", # 설립 연도
        "company_type": "", # 회사 유형 (주식회사, 유한회사 등)
        "is_listed": "", # 상장 여부
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
        "recent_news": "" # 최근 뉴스/보도자료
    }

    saramin_company_url = ""
    logo_url = ""

    driver = None
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument(f"user-agent={USER_AGENT}")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

        service = Service(executable_path=CHROME_DRIVER_PATH)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        # print("✅ Chrome 드라이버 초기화 성공.")
        
        SARAMIN_BASIC_URL = "https://www.saramin.co.kr"
        # 검색어 URL 인코딩 및 검색 URL 생성
        encoded_search_keyword = requests.utils.quote(search_keyword)
        initial_search_url = f"{SARAMIN_BASIC_URL}/zf_user/search/company?search_area=main&search_done=y&search_optional_item=n&searchType=search&searchword={encoded_search_keyword}"
        
        # --- 1단계: 검색 결과 페이지로 이동 ---
        print(f"👉 사람인 '{encoded_search_keyword}' 검색 페이지로 이동: {initial_search_url}")
        driver.get(initial_search_url)

        # 검색 결과 페이지 로딩 대기
        try:
            # `.cnt_result`는 검색 결과 수를, `.corp_name > a`는 첫 번째 회사 링크를 의미
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.cnt_result, .corp_name > a'))
            )
            print("✅ 사람인 검색 결과 페이지 로딩 완료.")
        except Exception as e:
            print(f"⚠️ 사람인 검색 결과 페이지 로딩 실패 또는 요소 미발견: {e}")
            print(f"❌ '{search_keyword}'에 대한 검색 결과를 찾을 수 없습니다.")
            return company_data # 검색 결과가 없으면 여기서 함수 종료

        # 로드된 검색 결과 페이지 HTML 파싱
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        # 1-1. 검색 결과 수 확인 및 첫 번째 기업 링크 추출
        cnt_result_span = soup.select_one('.cnt_result')
        result_count = 0
        if cnt_result_span:
            cnt_text = cnt_result_span.get_text(strip=True)
            match = re.search(r'\d+', cnt_text)
            if match:
                result_count = int(match.group(0))
        
        print(f"사람인 검색 결과 수: {result_count}건")

        # 1-2. result_count > 0 AND search_keyword == corp_name
        if result_count > 0:
            company_popup_names = soup.select('.company_popup')
            print(f">> company_popup_names (조회된 개수): {len(company_popup_names)}")

            # 1-3. 검색 기업명(search_keyword)과 여러 검색 결과 중 기업명(corp_name)이 일치하는 것 선택
            found_match = False

            for corp_name_element in company_popup_names:
                corp_name = corp_name_element.attrs.get('title')

                if not corp_name:
                    continue

                corp_name = corp_name.strip()

                result = compare_company_name(search_keyword, corp_name)

                if result == True:
                    company_data["name"] = corp_name
                    company_name_link_suffix = corp_name_element.attrs.get('href')
                    if company_name_link_suffix:
                        saramin_company_url = requests.compat.urljoin(SARAMIN_BASIC_URL, company_name_link_suffix)
                    
                    print(f"✅ 사람인에서 찾은 기업명: '{company_data['name']}'")
                    print(f"✅ 사람인 기업 상세 링크: {saramin_company_url}")
                    
                    found_match = True                
                    break
            
            if not found_match:
                print(f"❌ '{search_keyword}'에 일치하는 검색 결과가 존재하지 않습니다.")
                return company_data
        else: # result_count == 0인 경우 
            print(f"❌ 검색 키워드 '{search_keyword}'에 대한 검색 결과가 0건입니다.")
            return company_data

        # --- 2단계: 기업 상세 페이지로 이동하여 정보 추출 ---
        if saramin_company_url != "":
            print(f"👉 기업 상세 페이지로 이동: {saramin_company_url}")
            try:
                driver.get(saramin_company_url)
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '.company_details')) # 상세 정보 컨테이너
                )
                print("✅ 회사 상세 페이지 로딩 완료.")
            except Exception as e:
                print(f"⚠️ 회사 상세 페이지 로딩 실패 또는 요소 미발견 (URL: {saramin_company_url}): {e}")
                print("크롤링을 계속 시도하지만, 정보가 불완전할 수 있습니다.")
                pass # 실패 시에도 다음 정보 추출 로직 진행

            # 상세 페이지 HTML 파싱
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')

            # --- [기업소개] 탭에서 정보 추출 --- 
            # 회사 유형(주식회사, 유한회사 등)
            if "(주)" in corp_name or "(주식회사)" in corp_name:
                company_data["company_type"] = "주식회사"
                company_data["is_listed"] = True
            elif "(유)" in corp_name or "(유한회사)" in corp_name:
                company_data["company_type"] = "유한회사" 
            else:
                company_data["is_listed"] = False

            # 직원수
            employee_count_element = soup.select_one('.company_summary_item:nth-child(3) .box_align')
            if employee_count_element:
                company_data["employee_count"] = employee_count_element.select_one('.company_summary_tit').text.strip()

            # 산업 분야
            industry_element = soup.select_one('.company_details_group:nth-child(1) dd')
            if industry_element:
                company_data["industry"] = industry_element.text.strip()
            
            # 제품/서비스 명(JSON)
            products_services_element = soup.select_one('dt:-soup-contains("브랜드명") + dd > p')
            if products_services_element:
                company_data["products_services"] = products_services_element.text.strip()

            # CEO
            key_executives_element = soup.select_one('.company_details_group:nth-child(2) dd')
            if key_executives_element:
                company_data['key_executive'] = key_executives_element.text.strip()

            # 홈페이지 URL
            homepage_element = soup.select_one('dt:-soup-contains("홈페이지") + dd > a')
            if homepage_element:
                company_data["homepage"] = homepage_element.get('href')
            
            # 회사 주소
            address_element = soup.select_one('dt:-soup-contains("주소") + dd > p')
            if address_element:
                company_data["address"] = address_element.text.strip() # 주소만 출력(지도 제외)

            # 설립일
            founded_element = soup.select_one('.company_summary_item:nth-child(1) .company_summary_desc')
            if founded_element:
                raw_date = founded_element.text.strip() # yyyy-mm-dd 형식

                company_data["established_year"] = raw_date
                print(f"설립일 = {company_data["established_year"]}")

            # 회사 요약/설명
            summary_element = soup.select_one('.company_introduce .txt')
            if summary_element:
                company_data["description"] = summary_element.text.strip()

            # 로고 URL
            logo_element = soup.select_one('.box_logo img')
            if logo_element and 'src' in logo_element.attrs:
                logo_url = logo_element['src']
                print(f"logo_url = {logo_url}")

            # --- 3단계: 기업 상세 페이지의 [재무정보] 탭에서 재무현황 financial_history 추출 ---
            extract_financial_info(driver, company_data)

            # "financial_history" 에서 최근 매출액,영업이익,당기순이익,회계연도 출력
            if company_data["financial_history"]:
                latest_year = max(company_data["financial_history"].keys(), key=int)

                latest_financial_data = company_data["financial_history"][latest_year]

                company_data["latest_fiscal_year"] = latest_year
                company_data["latest_revenue"] = latest_financial_data.get("매출액")
                company_data["latest_operating_income"] = latest_financial_data.get("영업이익")
                company_data["latest_net_income"] = latest_financial_data.get("당기순이익")

                print(f"최근 회계연도: {company_data['latest_fiscal_year']}")
                print(f"최근 매출액: {company_data['latest_revenue']}")
                print(f"최근 영업이익: {company_data['latest_operating_income']}")
                print(f"최근 순이익: {company_data['latest_net_income']}")
            else:
                print("🚫 financial_history가 비어 있어 최신 재무 정보를 추출할 수 없습니다.")

    except Exception as e:
        print(f"🚫 크롤링 중 치명적인 오류 발생: {e}")
        pass

    finally:
        if driver:
            driver.quit()
            print("✅ Chrome 드라이버 종료.")
    
    return company_data


if __name__ == "__main__":
    test_keyword = input("기업명: ")
    print(f"\n===== 기업 크롤링 시작: '{test_keyword}' =====")

    # 1. 기업 정보 크롤링
    crawled_data = crawl_from_saramin(test_keyword)

    print("\n--- 크롤링 결과 ---")
    print(json.dumps(crawled_data, indent=2, ensure_ascii=False))
    print("==================================\n")
