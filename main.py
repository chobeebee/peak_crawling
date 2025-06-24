# main.py
from crawl.jobkorea import smart_crawl_jobkorea
from crawl.saramin import crawl_from_saramin
# from db.db_mysql import save_raw_data
from integration.integration_company_info import merge_company_info
from filtering.data_field_filtering import filtering_company_info
from decimal import Decimal, InvalidOperation
import json

# company_name = input("회사명을 입력하세요: ")

# 각 사이트 크롤링
# jobkorea_data = smart_crawl_jobkorea(company_name)
# saramin_data = crawl_from_saramin(company_name)

# raw 데이터 통합
# raw_dict = {
    # "jobkorea" : jobkorea_data,
    # "saramin" : saramin_data
# }

# raw 데이터 DB 저장
# company_id = save_raw_data(company_name, raw_dict)
# print("raw 데이터 저장=" + json.dumps(raw_dict, indent=2, ensure_ascii=False) + "\n")

# 수집 데이터 병합
# integration_result = merge_company_info(jobkorea_data, saramin_data)

# 병합 결과 출력 (작업 완료 시, 삭제)
# print("병합 결과 출력=" + json.dumps(integration_result, indent=2, ensure_ascii=False) + "\n")

# 임의 크롤링 데이터(테스트용, 최종에선 삭제 예정!)
integration_result = {
  "name": "무신사",
  "established_year": "2012",
  "company_type": "주식회사",
  "is_listed": True,
  "homepage": "http://www.musinsa.com",
  "description": "무신사는 700만 회원을 보유한 국내 1위 온라인 패션 플랫폼입니다. 스트릿, 글로벌 명품, 디자이너 등 5천여 개 브랜드가 입점한 「무신사 스토어」와 국내·외 최신 패션 트렌드 와 정보를 전달하는 패션 매거진 「무신사 매거진」을 운영하고 있습니다. 2019년 연 거래액 9,000억 원을 돌파했으며, 아시아 No.1 패션 커머스를 비전 삼아 2020년 연 거래액 1조 4천억 원을 목표 하고 있습니다. 무신사는 2015년 모던 베이식 캐주얼웨어 브랜드 「무신사 스탠다드」와 2016년 여성 패션 브랜드 스토어 「우신사」를 론칭해 국내 최대 규모의 브랜드 패션 플랫폼으로 성장했습니 다. 2018년 문을 연 패션 특화 공유 오피스 「무신사 스튜디오」는 패션 스타트업 및 신진 디자이너에게 최적의 공간과 인프라, 네트워킹을 지원하고 있습니다. 2019년에는 무신사 최초의 오프라인  공간이자 브랜드와 고객을 연결하는 패션 문화 복합 공간 「무신사 테라스」를 오픈했고, 2020년에는 한정판 마켓 「솔드아웃」과 셀렉티드 브랜드 큐레이션 서비스 「셀렉트」를 론칭했습니다. 무신사와 함께 성장하며 대한민국 패션 생태계를 이끌어나갈 인재를 찾습니다. - 무신사 채용 홈페이지: recruit.musinsa.com - 무신사 채용 인스타그램: instagram.com/musinsa_recruit - 무신사 스토어: store.musinsa.com/app - 무신사 매거진: musinsa.com - 무신사 스튜디오: musinsastudio.com - 무신사 테라스: musinsaterrace.com - 솔드아웃: soldout.co.kr",
  "address": "서울 성동구 성수동2가 277-47 무신사캠퍼스 N1 성수역 2번출구",
  "industry": "쇼핑몰·오픈마켓·소셜커머스",
  "products_services": "웹매거진, 온라인쇼핑몰, 광고대행",
  "key_executive": "박준모",
  "employee_count": "510명",
  "employee_history": "",
  "latest_revenue": "1조 1,005억원",
  "latest_operating_income": "1,123억 8천만원",
  "latest_net_income": "- 262억 4,876만원",
  "latest_fiscal_year": "2024",
  "financial_history": {
    "2021": {
      "영업이익": "670억 2천만원",
      "자산 합계": "1조 5억원"
    },
    "2022": {
      "영업이익": "539억 3천만원",
      "자산 합계": "1조 4,011억원"
    },
    "2023": {
      "영업이익": "370억 9천만원",
      "자산 합계": "1조 7,891억원"
    },
    "2024": {
      "영업이익": "1,123억 8천만원",
      "자산 합계": "2조 1,547억원"
    }
  },
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
  "recent_news": "",
  "created_at" : "2025-06-24 10:21:09",
  "updated_at" : "2025-06-24 10:33:31"
}

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