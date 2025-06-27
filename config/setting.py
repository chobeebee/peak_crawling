import os
from dotenv import load_dotenv

load_dotenv() # .env 파일 로드

# saramin 설정
CHROME_DRIVER_PATH = os.getenv("CHROME_DRIVER_PATH")
USER_AGENT = os.getenv("USER_AGENT")

if not CHROME_DRIVER_PATH:
    print("경고: CHROME_DRIVER_PATH 환경 변수가 설정되지 않았습니다. .env 변수 설정해주세요.")

if not USER_AGENT:
    print("경고: USER_AGENT 환경 변수가 설정되지 않았습니다. .env 변수 설정해주세요.")
