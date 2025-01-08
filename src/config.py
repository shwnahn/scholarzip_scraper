import os
import json
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# # 환경 변수 로드
# DB_PATH_UNIV = os.getenv("DB_PATH_UNIV")
# if not DB_PATH_UNIV:
#     raise EnvironmentError("환경 변수 DB_PATH_UNIV가 설정되지 않았습니다.")

# 프로젝트 루트의 설정 파일 경로
config_path = os.path.join(os.getcwd(), "db_config.json")

with open(config_path, "r") as config_file:
    db_config = json.load(config_file)

from datetime import datetime

def generate_dynamic_condition(dynamic_months):
    """
    dynamic_months 설정을 기반으로 SQL WHERE 조건을 생성합니다.

    :param dynamic_months: dynamic_months 설정 정보 (offset, current_month)
    :return: SQL WHERE 조건 문자열
    """
    current_month = datetime.now().month
    # Calculate target months based on the current month and offsets
    target_months = []
    for offset in dynamic_months["offset"]:
        # Calculate the target month
        target_month = (current_month + offset - 1) % 12 + 1
        target_months.append(target_month)
        
    conditions = [f"m{str(month).zfill(2)} = 'O'" for month in target_months]
    return "WHERE " + " OR ".join(conditions)