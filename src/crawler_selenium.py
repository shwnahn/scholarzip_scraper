from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

def fetch_elements_selenium(driver, url, selector, by, logger):
    """
    Selenium을 사용하여 지정된 URL에서 요소를 추출합니다.
    """
    try:
        # URL 접속
        driver.get(url)
        logger.info(f"[SELENIUM] {url} 접속 성공")

        # 요소 대기 및 찾기
        elements = wait_and_find_elements(driver, selector, by, logger)
        if elements:
            return elements

        # iframe에서 요소 찾기
        logger.warning(f"[SELENIUM] {selector} 요소를 찾지 못함, iframe 탐색 시작")
        elements = search_in_iframes(driver, selector, by, logger)
        if elements:
            return elements

        logger.warning(f"[SELENIUM] 요소 탐색 실패: {selector}")
        return None

    except WebDriverException as e:
        logger.error(f"[SELENIUM] WebDriver 오류 발생: {e}")
        return None


def wait_and_find_elements(driver, selector, by, logger, timeout=7):
    """
    지정된 선택자로 요소를 대기하고 찾습니다.
    """
    try:
        WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, selector)))
        logger.info(f"[SELENIUM] 요소 로드 성공")
        elements = driver.find_elements(by, selector)
        if elements:
            logger.info(f"[SELENIUM] 요소 찾기 성공")
            return elements
        return None
    except TimeoutException:
        logger.warning(f"[SELENIUM] 요소 로드 시간 초과")
        return None


def search_in_iframes(driver, selector, by, logger):
    """
    모든 iframe을 순회하여 요소를 찾습니다.
    """
    iframes = driver.find_elements(By.TAG_NAME, 'iframe')
    if not iframes:
        logger.warning(f"[SELENIUM] IFrame이 존재하지 않음, {selector} 탐색 중단")
        return None
    
    for iframe in iframes:
        try:
            driver.switch_to.frame(iframe)
            logger.info(f"[SELENIUM] IFrame 전환 성공")
            elements = wait_and_find_elements(driver, selector, by, logger, timeout=3)
            if elements:
                return elements
            # 재귀적으로 내부 iframe 검색
            elements = search_in_iframes(driver, selector, by, logger)
            if elements:
                return elements

        except WebDriverException as e:
            logger.error(f"[SELENIUM] IFrame 처리 중 오류 발생: {e}")
        finally:
            driver.switch_to.default_content() # IFrame 탐색 후 기본 콘텐츠로 복귀
    return None

def selenium_crawling(driver, url, selector, by_type, logger):
    """
    Selenium을 사용하여 요소를 추출하는 일반 함수.
    :param driver: Selenium WebDriver 인스턴스
    :param url: 크롤링 대상 URL
    :param selector: 선택자 (CSS 셀렉터 또는 클래스 이름)
    :param by_type: 선택자 유형 ('css' 또는 'class')
    :param logger: 로깅 객체
    :return: 추출된 WebElement 리스트 또는 None
    """
    # 선택자 유형 매핑
    by_mapping = {
        "css": By.CSS_SELECTOR,
        "class": By.CLASS_NAME
    }
    by_method = by_mapping.get(by_type)

    if not by_method:
        logger.error(f"[SELENIUM] 잘못된 by_type: {by_type}")
        return None

    # fetch_elements_selenium 호출
    return fetch_elements_selenium(driver, url, selector, by_method, logger)
