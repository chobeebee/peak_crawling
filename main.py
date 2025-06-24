# main.py
from crawl.jobkorea import smart_crawl_jobkorea
from db.db_mysql import save_raw_data

company_name = input("회사명을 입력하세요: ")

# 각 사이트 크롤링
jobkorea_data = smart_crawl_jobkorea(company_name)

# raw 데이터 통합
raw_dict = {
    "jobkorea" : jobkorea_data
}

# raw 데이터 DB 저장
company_id = save_raw_data(company_name, raw_dict)

# 정제 로직 실행

# 정제된 데이터 DB 저장