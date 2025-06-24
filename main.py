# main.py
from crawl.jobkorea import smart_crawl_jobkorea
from crawl.saramin import crawl_from_saramin
# from db.db_mysql import save_raw_data
from integration.integration_company_info import merge_company_info
import json

company_name = input("회사명을 입력하세요: ")

# 각 사이트 크롤링
jobkorea_data = smart_crawl_jobkorea(company_name)
saramin_data = crawl_from_saramin(company_name)

# raw 데이터 통합
raw_dict = {
    "jobkorea" : jobkorea_data,
    "saramin" : saramin_data
}

# raw 데이터 DB 저장
# company_id = save_raw_data(company_name, raw_dict)
print("raw 데이터 저장=" + json.dumps(raw_dict, indent=2, ensure_ascii=False) + "\n")

# 수집 데이터 병합
integration_result = merge_company_info(jobkorea_data, saramin_data)

# 병합 결과 출력 (작업 완료 시, 삭제)
print("병합 결과 출력=" + json.dumps(integration_result, indent=2, ensure_ascii=False) + "\n")

# 정제 로직 실행

# 정제된 데이터 DB 저장