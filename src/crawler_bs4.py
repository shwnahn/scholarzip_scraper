from bs4 import BeautifulSoup
import requests
import socket


def bs4_css(url, css_selector, logger):
    """
    BeautifulSoup를 사용하여 주어진 URL에서 CSS 셀렉터로 요소를 추출합니다.
    """
    try:
        # HTTP 요청 보내기
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        logger.info(f"[BS4_CSS] URL 요청 성공")
    except requests.exceptions.Timeout as e:
        logger.error(f"[BS4_CSS] 요청 시간이 초과되었습니다: {e}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"[BS4_CSS] URL 요청 중 오류가 발생했습니다: {e}")
        return None
    except socket.gaierror as e:
        logger.error(f"[BS4_CSS] 네트워크 연결 오류: {e}")
        return None
    except Exception as e:
        logger.error(f"[BS4_CSS] 기타 오류가 발생했습니다: {e}")
        return None

    try:
        # HTML 파싱하기
        soup = BeautifulSoup(res.content, 'html.parser')
        logger.info("[BS4_CSS] HTML 파싱 성공")
    except Exception as e:
        logger.error(f"[BS4_CSS] HTML 파싱 중 오류가 발생했습니다: {e}")
        return None

    try:
        # CSS 셀렉터로 요소 선택하기
        elements = soup.select(css_selector)
        if not elements:
            logger.warning("[BS4_CSS] 지정한 CSS 셀렉터에 해당하는 요소를 찾을 수 없습니다.")
            return None
        logger.info("[BS4_CSS] 요소 선택 성공")
    except Exception as e:
        logger.error(f"[BS4_CSS] 요소 선택 중 오류가 발생했습니다: {e}")
        return None

    return elements

def bs4_class(url, class_name, logger):
    """
    BeautifulSoup를 사용하여 주어진 URL에서 클래스 이름으로 요소를 추출합니다.
    """
    try:
        # HTTP 요청 보내기
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        logger.info("[BS4_CLASS] URL 요청 성공")
    except requests.exceptions.Timeout as e:
        logger.error(f"[BS4_CLASS] 요청 시간이 초과되었습니다: {e}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"[BS4_CLASS] URL 요청 중 오류가 발생했습니다: {e}")
        return None
    except socket.gaierror as e:
        logger.error(f"[BS4_CLASS] 네트워크 연결 오류: {e}")
        return None
    except Exception as e:
        logger.error(f"[BS4_CLASS] 기타 오류가 발생했습니다: {e}")
        return None

    try:
        # HTML 파싱하기
        soup = BeautifulSoup(res.content, 'html.parser')
        logger.info("[BS4_CLASS] HTML 파싱 성공")
    except Exception as e:
        logger.error(f"[BS4_CLASS] HTML 파싱 중 오류가 발생했습니다: {e}")
        return None

    try:
        # 클래스 이름으로 요소 선택하기
        elements = soup.find_all(class_=class_name)
        if not elements:
            logger.warning("[BS4_CLASS] 지정한 클래스 이름에 해당하는 요소를 찾을 수 없습니다.")
            return None
        logger.info("[BS4_CLASS] 요소 선택 성공")
    except Exception as e:
        logger.error(f"[BS4_CLASS] 요소 선택 중 오류가 발생했습니다: {e}")
        return None

    return elements
