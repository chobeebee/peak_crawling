from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from copy import deepcopy
from common.common_field_template import basic_template
from config.setting import USER_AGENT
import json, time

# 공통 유틸 함수
""" 기업정보 영역 """
def get_info(driver, label: str) -> str:
    try:
        rows = driver.find_elements(By.CSS_SELECTOR, "table.table-basic-infomation-primary tr.field")
        for row in rows:
            ths = row.find_elements(By.CSS_SELECTOR, "th.field-label")
            tds = row.find_elements(By.CSS_SELECTOR, "td.field-value")
            for i, th in enumerate(ths):
                if label in th.text and i < len(tds):
                    return tds[i].find_element(By.CSS_SELECTOR, ".value").text.strip()       
    except:
        pass
    return ""


""" 재무분석 영역 """
def get_financial_value(driver, metric: str) -> str:
    try:
        cards = driver.find_elements(By.CSS_SELECTOR, "div.financial-analysis-card")
        for card in cards:
            header = card.find_element(By.CSS_SELECTOR, "h3.header").text.strip()
            if metric in header:
                return card.find_element(By.CSS_SELECTOR, "div.revenue .value").text.strip()
    except:
        pass
    return ""


""" 회계연도 추출 """
def get_latest_fiscal_year(driver) -> str:
    try:
        cards = driver.find_elements(By.CSS_SELECTOR, "div.financial-analysis-card")
        for card in cards:
            try:
                update_date = card.find_element(By.CSS_SELECTOR, "div.update").text.strip()
                year = update_date.split(".")[0]

                if year.isdigit():
                    return year
            except:
                continue
    except:
        pass
    return ""


""" 고용현황 영역 """
def get_employee_history(driver) -> str:
    try:
        chart = driver.find_element(By.CSS_SELECTOR, "div.chart-bar-number-of-employees")
        bars = chart.find_elements(By.CSS_SELECTOR, "div.bar")

        history = {}
        for bar in bars:
            year = bar.find_element(By.CSS_SELECTOR, "div.label").text.strip()
            value = bar.find_element(By.CSS_SELECTOR, "div.value").text.strip()
            history[year] = value

        return json.dumps(history, ensure_ascii=False)

    except:
        pass
    return ""


""" 근무환경 영역 """
def get_company_introduction(driver) -> str:
    try:
        container = driver.find_element(By.CSS_SELECTOR, "div.working-environment-introduce div.introduce-body")
        html = container.get_attribute("innerHTML")

        # 태그 및 줄자꿈 제거
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(separator=" ", strip=True) # 줄 바꿈을 공백으로 처리
        return text
    except:
        return ""
    

""" 재무현황 전체보기 팝업창 """
def get_financial_history(driver) -> dict:
    try:
        # 재무현황 전체보기 버튼 클릭
        view_more_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a.button-view-financial-status"))
        )
        driver.execute_script("arguments[0].click();", view_more_btn)
        time.sleep(1)  # 팝업 뜰 때까지 잠깐 대기

        # 팝업 테이블 로딩 대기
        soup = BeautifulSoup(driver.page_source, "html.parser")
        table = soup.select_one("table.table-financial-statements")
        if not table:
            return {}

        # 연도 추출
        year_ths = table.select("thead tr th")[1:]
        years = [th.text.strip()[:4] for th in year_ths if th.text.strip()[:4].isdigit()]

        # 추출 필드
        fields = ["자산 합계", "자본금", "자본금 합계", "매출 액", "영업 이익", "당기순이익"]
        data_by_year = {year : {} for year in years}

        # 데이터 추출
        for row in table.select("tbody tr"):
            cells = row.select("td")
            if not cells:
                continue
            category = cells[0].text.strip()
            if category not in fields:
                continue
            for i, year in enumerate(years):
                data_by_year[year][category.replace(" ", "")] = cells[i + 1].text.strip()

        return data_by_year
    except:
        return ""
    

""" 재무분석 카드 그래프 """
def get_financial_graph(driver) -> dict:
    field_mappings = {
        "총자산 증가율": "자산 합계",
        "매출액": "매출액",
        "영업이익": "영업이익",
        "당기순이익": "당기순이익"
    }
    financial_data = {}

    cards = driver.find_elements(By.CSS_SELECTOR, ".financial-analysis-card")
    for card in cards:
        try:
            title = card.find_element(By.CSS_SELECTOR, "h3.header").text.strip()
            if title not in field_mappings:
                continue  # 매핑에 없는 필드는 건너뜀

            mapped_key = field_mappings[title]  # 저장할 필드명

            bars = card.find_elements(By.CSS_SELECTOR, ".chart-bar-wrap .bar")
            for bar in bars:
                year = bar.find_element(By.CSS_SELECTOR, ".label").text.strip()
                value = bar.find_element(By.CSS_SELECTOR, ".value").text.strip()
                financial_data.setdefault(year, {})[mapped_key] = value
        except:
            continue  # 일부 카드에 차트가 없을 수도 있음

    return financial_data

    
""" 재무 정보 히스토리 """
def get_financial_info(driver) -> dict:
    try:
        # "재무현황 전체보기" 버튼 존재 여부 확인
        popup_button = driver.find_elements(By.CSS_SELECTOR, "a.button-view-financial-status")

        if popup_button:
            # 버튼 클릭 후 팝업창 정보 수집
            return get_financial_history(driver)
        else:
            # 버튼이 없을 경우, 그래프 정보 수집
            return get_financial_graph(driver)
    
    except:
        return {}
    
        
# 기업 정보 페이지 파싱 함수
def parse_company_info(driver) -> dict:
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.company-body-infomation"))
    )

    # 기업명 추출 및 회사 유형 추론
    name = driver.find_element(By.CSS_SELECTOR, "#corpHistName").get_attribute("value").strip()
    if any(keyword in name for keyword in ["주식회사", "(주)", "㈜"]):
        company_type = "주식회사"
        is_listed = True
    elif any(keyword in name for keyword in ["유한회사", "(유)"]):
        company_type = "유한회사"
        is_listed = False
    else:
        company_type = ""
        is_listed = False

    # 재무 관련 필드
    financial_history = get_financial_info(driver)
    latest_year = max(financial_history.keys(), default="")
    latest_revenue = financial_history.get(latest_year, {}).get("매출액", "")
    latest_operating_income = financial_history.get(latest_year, {}).get("영업이익", "")
    latest_net_income = financial_history.get(latest_year, {}).get("당기순이익", "")

    company_data = deepcopy(basic_template)

    company_data.update({
        "name": name, # 회사명
        "established_year": get_info(driver, "설립일")[:4], # 설립 연도
        "company_type": company_type, # 회사 유형 (주식회사, 유한회사 등)
        "is_listed": is_listed, # 상장 여부
        "homepage": get_info(driver, "홈페이지"), # 회사 홈페이지 URL
        "description": get_company_introduction(driver), # 회사 설명
        "address": get_info(driver, "주소"), # 회사 주소
        "industry": get_info(driver, "산업"), # 산업 분야 정보
        "products_services": get_info(driver, "주요사업"), # 제품/서비스 이름 배열
        "key_executive": get_info(driver, "대표자"), # 주요 경영진(대표자) 이름
        "employee_count": get_info(driver, "사원수"), # 현재 직원 수
        "employee_history": get_employee_history(driver), # 과거 직원 수 추이
        "latest_revenue": latest_revenue, # 최근 매출액 (원)
        "latest_operating_income": latest_operating_income, # 최근 영업이익 (원)
        "latest_net_income": latest_net_income, # 최근 순이익 (원)
        "latest_fiscal_year": latest_year, # 최근 재무 정보의 회계연도
        "financial_history": financial_history, # 과거 재무 정보 히스토리
    })
    
    return company_data

def smart_crawl_jobkorea(company_name: str) -> dict:
    print(f"=== '{company_name}' 기업 정보 수집 시작 ===")

    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--enable-unsafe-swiftshader")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument(f"user-agent={USER_AGENT}")

    driver = webdriver.Chrome(options=chrome_options)

    # 회사명 비교를 위한 정규화 함수
    def normalize(text: str) -> str:
        return ''.join(filter(str.isalnum, text)).lower()

    try:
        # 기업 검색
        search_url = f"https://www.jobkorea.co.kr/Search?stext={company_name}"
        driver.get(search_url)

        # '기업정보' 탭 클릭
        corp_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[.//span[text()='기업정보']]"))
        )
        corp_tab.click()
        time.sleep(2)  # 렌더링 대기

        normalized_target = normalize(company_name)
        info_url = ""

        # 1~5페이지까지 탐색
        for page in range(1, 6):
            # 기업 리스트 대기
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[@data-sentry-element='Tabs.Content' and contains(@id, '-content-corp')]//a[@data-sentry-element='BaseLink']"))
            )

            # 기업 리스트 중 이름이 정확히 일치하는 항목 클릭
            company_elements = driver.find_elements(By.XPATH, "//div[@data-sentry-element='Tabs.Content' and contains(@id, '-content-corp')]//a[@data-sentry-element='BaseLink']")
            for a in company_elements:
                name = a.text.strip()
                if not name:
                    # 빈 항목은 출력도, 비교도 하지 않음
                    continue

                print(f"검색된 회사명: {name}")

                if normalize(name) == normalized_target:
                    info_url = a.get_attribute("href")
                    break
            
            # 찾으면 종료
            if info_url:
                break
            
            # 다음 페이지로 이동
            if page < 5:
                try:
                    next_page_xpath = f"//a[@data-sentry-element='NextLink' and contains(@href, 'Page_No={page + 1}') and contains(@href, 'tabType=corp')]"
                    next_page_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, next_page_xpath))
                    )
                    next_page_button.click()
                    time.sleep(2)
                except Exception as e:
                    print(f"{page+1}페이지 이동 실패:", e)
                    break

        if not info_url:
            print(f"'{company_name}'과 일치하는 기업을 찾을 수 없습니다.")
            return deepcopy(basic_template) # 실패 시 리턴할 기본 템플릿

        print("▶ 기업정보 링크:", info_url)
        driver.get(info_url)

        return parse_company_info(driver)

    except Exception as e:
        print(f"[예외 발생] smart_crawl_jobkorea: {e}")
        return deepcopy(basic_template) # 실패 시 리턴할 기본 템플릿

    finally:
        driver.quit()