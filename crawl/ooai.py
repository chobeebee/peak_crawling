import json
import re
import urllib.parse
import requests


def ooai_crawler(name: str):
  encoded_name = urllib.parse.quote(name)
  url = f'https://oo.ai/search?q={encoded_name}'

  response = requests.get(url)

  html = response.text
  token = None
  # 정규표현식을 사용하여 token 값을 추출합니다.
  token_match = re.search(r'token:\s*"([^"]+)"', html)
  if token_match:
    token = token_match.group(1)
  # 추출된 토큰이 없다면 에러 메시지 출력
  if not token:
    print("토큰을 찾을 수 없습니다.")

  # 추출된 토큰을 출력
  print({"json": {"csrf_token": token}})

  search_url = f"https://oo.ai/api/search?q={encoded_name}&lang=ko&tz=Asia/Seoul"
  headers = {
    "accept": "*/*",
    "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "cookie": "_variant=stable; lang=ko",
    "origin": "https://oo.ai",
    "referer": f"https://oo.ai/search?q={encoded_name}",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "x-csrf-token": f"Bearer {token}"
  }

  response = requests.post(search_url, headers=headers)

  parsed_data = parse_sse_response(response.text)
  print(json.dumps(parsed_data, ensure_ascii=False, indent=4))

def parse_sse_response(stream_data):
    lines = stream_data.split('\n')
    final_answer_html = None
    sid = None
    for line in lines:
        if line.startswith('data:'):
            try:
                json_data_string = line[5:].strip()
                if json_data_string:
                    parsed_data = json.loads(json_data_string)
                    if parsed_data.get('type') == 'save':
                        if 'answer' in parsed_data:
                            final_answer_html = parsed_data['answer']
                        if 'id' in parsed_data:
                            sid = parsed_data['id']
                        if final_answer_html and sid:
                            break
            except Exception:
                # JSON 파싱 오류는 무시하고 다음 라인으로 진행
                continue
    plain_text_answer = None
    if final_answer_html:
        # <webblock> 태그와 그 내용 제거
        temp_answer = re.sub(r'<webblock>.*?</webblock>', '', final_answer_html, flags=re.DOTALL).strip()
        # 나머지 HTML 태그를 공백으로 변환 후, 여러 공백을 하나로 합치고 앞뒤 공백 제거
        plain_text_answer = re.sub(r'<[^>]+>', ' ', temp_answer)
        plain_text_answer = re.sub(r'\s+', ' ', plain_text_answer).strip()
    return {
        'json': {
            'search_id': sid,
            'full_html_answer': final_answer_html,
            'plain_text_answer': plain_text_answer
        }
    }