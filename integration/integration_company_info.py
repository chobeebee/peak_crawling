"""
잡코리아 기준으로 사람인 데이터 통합
- 잡코리아 데이터가 비어 있는 경우("", None, {}, [], "null") → 사람인 데이터로 보완
- is_listed 필드는 두 값 중 하나라도 True면 True로 설정
"""
def merge_company_info (jobkorea_data: dict, saramin_data: dict) -> dict :
 
    merged_data = {} # 최종 통합 데이터

    def is_empty(value):
        return value in ["", None, {}, [], "null"]
    
    # 잡코리아 JSON 키 순서대로 탐색
    for key in jobkorea_data:
        jobkorea_value = jobkorea_data[key]
        saramin_value = saramin_data.get(key, "")

        if key == "is_listed":
            merged_data[key] = bool(jobkorea_value) or bool(saramin_value)

        elif is_empty(jobkorea_value) and not is_empty(saramin_value):
            merged_data[key] = saramin_value

        else:
            merged_data[key] = jobkorea_value

    return merged_data