from src.crawler_bs4 import bs4_css, bs4_class
from src.crawler_selenium import selenium_crawling
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from requests.exceptions import ConnectionError, Timeout

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # 백그라운드 실행을 원할 경우
    options.add_argument('window-size=1920x1080')
    options.add_argument("--disable-gpu")
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36")
    options.add_argument("lang=ko_KR") # 한국어!
    driver = webdriver.Chrome(options=options)
    return driver

def perform_crawling(method, method_name, *args, logger):
    """
    주어진 크롤링 메서드를 실행하고 결과를 반환하며, 에러가 발생하면 이를 기록합니다.

    :param method: 실행할 크롤링 메서드 (ex: bs4_css, selenium_crawling)
    :param method_name: 메서드 이름 (로깅 및 에러 기록용)
    :param *args: 메서드에 필요한 가변 인자
    :param logger: 로깅 객체
    :return: 성공 시 추출된 elements, 실패 시 None
    """
    try:
        # 크롤링 메서드 실행
        elements = method(*args)
        if elements:
            logger.info(f"[SUCCESS] 메서드: {method_name} | 데이터 추출 성공")
            return elements  # 성공 시 요소 반환
        raise ValueError(f"{method_name} 실패: 결과가 비어 있습니다.")
    except (ConnectionError, Timeout, WebDriverException) as e:
        logger.error(f"[{method_name}] 네트워크 관련 오류 발생: {str(e)}")
        return None  # 네트워크 오류 발생 시 None 반환
    except Exception as e:
        logger.error(f"[{method_name}] 일반 오류 발생: {str(e)}")
        return None
    except Exception as e:
        raise RuntimeError(f"[{method_name}] {str(e)}") from e

def create_crawling_methods(driver, url, css_selector, class_name, logger):
    """
    주어진 인자에 따라 크롤링 메서드 리스트를 생성합니다.
    """
    method_configs = [
        ("bs4_css", bs4_css, [url, css_selector, logger]) if css_selector else None,
        ("bs4_class", bs4_class, [url, class_name, logger]) if class_name else None,
        ("selenium_css", selenium_crawling, [driver, url, css_selector, "css", logger]) if css_selector else None,
        ("selenium_class", selenium_crawling, [driver, url, class_name, "class", logger]) if class_name else None
    ]
    
    # 유효한 메서드만 필터링,  None 값 제거
    return [method for method in method_configs if method is not None]
