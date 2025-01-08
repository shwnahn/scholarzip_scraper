import json
import re
import os
from datetime import datetime

def extract_element(elements):
    """
    BeautifulSoup 또는 Selenium WebElement 리스트에서 텍스트를 추출하고 정리하여 반환합니다.
    """
    data = []
    for element in elements:
        if hasattr(element, 'get_text'):  # BeautifulSoup 객체인 경우
            cleaned_text = re.sub(r'\s+', ' ', element.get_text()).strip()
        elif hasattr(element, 'text'):  # Selenium WebElement 객체인 경우
            cleaned_text = re.sub(r'\s+', ' ', element.text).strip()
        else:
            # 지원하지 않는 객체 유형일 경우 스킵
            continue
        data.append(cleaned_text)
    return data

def is_empty_data(data):
    """
    데이터가 비어 있는지 확인합니다.
    """
    for sublist in data:
        if any(item.strip() for item in sublist):
            return False
    return True

def word_filter(keywords, data_list):
    passed_data = []
    failed_data = []

    for data in data_list:
        if any(keyword in data for keyword in keywords):  # 키워드가 문자열에 포함되는지 확인
            passed_data.append(data)
        else:
            failed_data.append(data)

    return passed_data, failed_data

def extract_new_information(old_data, new_data):
    """
    기존 데이터와 새로운 데이터를 비교하여 새로운 정보만 추출합니다.

    :param old_data: 기존 데이터 (dict)
    :param new_data: 새로운 데이터 (dict)
    :return: 새로운 데이터만 포함한 dict
    """
    old_items = set(old_data.get("data", []))  # 기존 데이터의 'data' 항목
    new_items = set(new_data.get("data", []))  # 새로운 데이터의 'data' 항목

    # 새로운 데이터만 추출
    unique_items = new_items - old_items

    # 새로운 데이터의 구조 유지
    return {
        "method": new_data["method"],
        "by": new_data["by"],
        "last_update_date": new_data["last_update_date"],
        "data": list(unique_items)
    }

def save_data(data, save_path, method, selector_value, logger):
    """
    데이터를 JSON 파일로 저장하며 메타데이터를 포함합니다.

    :param data: 저장할 데이터
    :param save_path: JSON 파일 경로
    :param method: 사용한 크롤링 방식
    :param logger: 로깅 객체
    :return: unique_data (새로운 데이터) 또는 None
    """
    try:
        # 기존 파일 읽기
        if os.path.exists(save_path):
            with open(save_path, 'r', encoding='utf-8') as f:
                old_data = json.load(f)
        else:
            old_data = {}

        # 새로운 데이터 포맷
        new_data = {
            "method": method,
            "by": selector_value,
            "last_update_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "data": data
        }

        # 새로운 정보만 추출
        unique_data = extract_new_information(old_data, new_data)

        # 데이터 비교 및 저장
        if old_data.get("data") == new_data["data"]:
            return None  # 변경 사항이 없으면 None 반환
        else:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)  # 디렉토리 생성
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(new_data, f, ensure_ascii=False, indent=4)
            if unique_data["data"]:
                logger.info(f"[DATA] 새로운 데이터 '{len(unique_data['data'])}개' 발견!")
            logger.info(f"[DATA] 데이터가 업데이트되었습니다!")
            return unique_data  # 업데이트된 데이터 반환
    except Exception as e:
        logger.error(f"데이터 저장 중 오류 발생: {e}")
        raise e

