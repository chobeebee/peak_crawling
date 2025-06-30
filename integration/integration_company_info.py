from copy import deepcopy
from common.common_field_template import basic_template

def merge_company_info (jobkorea_data: dict, saramin_data: dict) -> dict :
    """
    JobKorea 데이터를 기준으로 Saramin 데이터를 병합하는 함수
    
    - JobKorea의 값이 비어있거나 존재하지 않을 경우 Saramin 값을 사용
    - is_listed 필드는 두 값 중 하나라도 True일 경우 True로 설정
    - financial_history는 연도별로 병합 (비어있는 항목만 보완)
    - 병합 실패 시 기본 템플릿 반환

    Args:
        jobkorea_data (dict): JobKorea에서 수집한 회사 정보
        saramin_data (dict): Saramin에서 수집한 회사 정보

    Returns:
        dict: 병합된 최종 회사 정보
    """
    # 공통적으로 사용하는 빈값 판단 함수
    def is_empty(value):
        return value in ["", None, {}, [], "null"]

    # 데이터 수집이 실패된 경우 (에러 포함 시 빈 딕셔너리로 초기화)
    if not isinstance(jobkorea_data, dict) or "error" in jobkorea_data:
        jobkorea_data = {}
    if not isinstance(saramin_data, dict) or "error" in saramin_data:
        saramin_data = {}

    # 모든 사이트가 실패한 경우 기본 템플릿 반환
    if not jobkorea_data and not saramin_data:
        return deepcopy(basic_template) # 기본 데이터 템플릿
    
    # 최종 병합 결과 저장용 딕셔너리
    merged_data = {}
    
    # 기본 템플릿 JSON 키 순서대로 탐색
    for key in basic_template:
        jobkorea_value = jobkorea_data.get(key)
        saramin_value = saramin_data.get(key)

        # 상장 여부 병합 처리: 둘 중 하나라도 True면 True
        if key == "is_listed":
            merged_data[key] = bool(jobkorea_value) or bool(saramin_value)
        
        # financial_history 병합 처리
        elif key == "financial_history":
            merged_data[key] = {}

            # JobKorea 기준 먼저 복사
            if isinstance(jobkorea_value, dict):
                for year, jobkorea_year_data in jobkorea_value.items():
                    merged_data[key][year] = jobkorea_year_data.copy()

            # Saramin 데이터 병합 (비어있는 항목 보완)
            if isinstance(saramin_value, dict):
                for year, saramin_year_data in saramin_value.items():
                    if year not in merged_data[key]:
                        merged_data[key][year] = saramin_year_data
                    else:
                        for metric, value in saramin_year_data.items():
                            if metric not in merged_data[key][year] or is_empty(merged_data[key][year][metric]):
                                merged_data[key][year][metric] = value

        # 일반 필드 병합 처리
        elif is_empty(jobkorea_value) and not is_empty(saramin_value):
            # JobKorea 값이 비어 있고 Saramin 값이 있다면 Saramin 값 사용
            merged_data[key] = saramin_value
        elif not is_empty(jobkorea_value):
            # JobKorea 값이 존재한다면 우선 사용
            merged_data[key] = jobkorea_value
        else:
            # 둘 다 비어 있다면 기본 템플릿 값 사용
            merged_data[key] = deepcopy(basic_template[key])

    return merged_data