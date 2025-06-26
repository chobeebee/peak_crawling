# main.py
from crawl.jobkorea import smart_crawl_jobkorea
from crawl.ooai import enrich_company_data
from crawl.saramin import crawl_from_saramin
# from db.db_mysql import save_raw_data
from integration.integration_company_info import merge_company_info
from filtering.data_field_filtering import filtering_company_info
from decimal import Decimal, InvalidOperation
import json

company_name = input("회사명을 입력하세요: ")

# 각 사이트 크롤링
jobkorea_data = smart_crawl_jobkorea(company_name)
saramin_data = crawl_from_saramin(company_name)
final_saramin_data = enrich_company_data(saramin_data.get('name'), saramin_data)

# raw 데이터 통합
raw_dict = {
    "jobkorea" : jobkorea_data,
#    "saramin" : saramin_data
     "saramin" : final_saramin_data
}

# raw 데이터 DB 저장
# company_id = save_raw_data(company_name, raw_dict)
print("raw 데이터=" + json.dumps(raw_dict, indent=2, ensure_ascii=False) + "\n")

# 수집 데이터 병합
# integration_result = merge_company_info(jobkorea_data, saramin_data)
integration_result = merge_company_info(jobkorea_data, final_saramin_data)

# 병합 결과 출력 (작업 완료 시, 삭제)
print("병합 데이터 출력=" + json.dumps(integration_result, indent=2, ensure_ascii=False) + "\n")

# JSON 직렬화 시 Decimal 객체를 처리하기 위한 사용자 정의 함수
def decimal_default_encoder(obj):
    if isinstance(obj, Decimal):
        # Decimal 객체를 float 또는 str으로 변환.
        # 정밀도를 유지하려면 str이 더 안전합니다.
        return str(obj) 
    raise TypeError(f'Object of type {obj.__class__.__name__} is not JSON serializable')

# 정제 로직 실행
filtered_data = filtering_company_info(integration_result)
print("\n=== 정제된 회사 정보 ===\n")
print(json.dumps(filtered_data, indent=2, ensure_ascii=False, default=decimal_default_encoder))
print("\n========================\n")

# 정제된 데이터 DB 저장
# company_id = save_raw_data(company_name, filtered_data)