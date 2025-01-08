import os
import json
import sqlite3
import time
import socket

from src.config import db_config, generate_dynamic_condition
from src.crawler_manager import setup_driver, perform_crawling, create_crawling_methods
from src.error_handler import log_error, add_error_dict
from src.data_handler import extract_element, is_empty_data, save_data, word_filter
from src.logging_config import setup_logging, log_with_border, current_date
from src.slack_messenger import send_slack_scholarship, setup_slack_client, send_slack_opening, send_slack_message, send_slack_failure_list

# 메인 실행 부분
def main(config_key):
    """
    주어진 config_key (univ 또는 nonuniv)를 기반으로 크롤링을 실행합니다.

    :param config_key: "univ" 또는 "nonuniv" 설정 키
    """
    # logger 설정
    logger = setup_logging(config_key)

    # 시작 시각 기록
    start_time = time.time()

    # DB 설정 로드
    if config_key not in db_config:
        logger.error(f"Invalid config_key: {config_key}")
        raise KeyError(f"Invalid config_key: {config_key}")
    config = db_config[config_key]
    db_path = config["db_path"]
    table_name = config["table"]
    columns = config["columns"]
    dynamic_months = config.get("dynamic_months", None) if config_key == "nonuniv" else None
    # 동적 조건 생성 (nonuniv일 때만)
    query_condition = generate_dynamic_condition(dynamic_months) if dynamic_months else ""
    query = f"SELECT * FROM {table_name} {query_condition}"
    logger.info(f"|| {config_key} || SQL: {query}")

    # 데이터 저장 경로
    base_path = f"data/{config_key}"
    os.makedirs(base_path, exist_ok=True)

    # 슬랙 설정
    SLACK_CHANNEL_TEST = os.getenv("SLACK_CHANNEL_TEST")
    SLACK_CHANNEL_JANGHAK = os.getenv("SLACK_CHANNEL_JANGHAK")
    SLACK_CHANNEL_NOTICE = os.getenv("SLACK_CHANNEL_NOTICE")

    # 에러와 실패 목록 관리
    error_dict = {}
    failure_list = []
    success_count, total_rows = 0, 0
    
    try:
         # 네트워크 연결 확인
        try:
            socket.create_connection(("www.google.com", 80), timeout=10)
            logger.info("[NETWORK] 네트워크 연결 확인 성공")
        except OSError:
            msg = "[NETWORK] 네트워크 연결 실패"
            log_error("network", msg, logger)
            return
        
        # WebDriver 생성
        try:
            driver = setup_driver()
        except Exception as e:
            logger.error(f"[DRIVER] 초기화 실패: {type(e).__name__} - {e}")
            raise RuntimeError(f"[DRIVER] 초기화 실패: {e}")  # 드라이버가 없으면 크롤링을 진행할 수 없으므로 예외 발생

        # SQLite 데이터베이스 연결
        conn = sqlite3.connect(db_path, timeout=5.0)
        cursor = conn.cursor()
        # SQL 실행 (테이블 이름 및 컬럼 동적 처리)
        cursor.execute(query)
        rows = cursor.fetchall()
        total_rows = len(rows)
        # cursor.description에서 컬럼명 추출
        col_names = [desc[0] for desc in cursor.description]
        column_indices = { key: col_names.index(val) for key, val in columns.items() }

        # 슬랙 연결
        slack_client = setup_slack_client()
        send_slack_opening(config_key, slack_client, SLACK_CHANNEL_JANGHAK)

        logger.info(f"|| {config_key} || 총 {total_rows}개 데이터 크롤링 시작")
        for idx, row in enumerate(rows, start=1):
            org_name = row[column_indices["name"]]
            url = row[column_indices["url"]]
            css_selector = row[column_indices["css"]]
            class_name = row[column_indices["class"]]
            save_path = os.path.join(base_path, f"{org_name}.json")
            
            # 로그 기록 시작 (기관명)
            log_with_border(f"{org_name}({idx})", logger)

            # URL이 없거나, 크롤링에 필요한 선택자/클래스가 모두 없으면 예외처리
            if not url or (not css_selector and not class_name):
                msg = "[DB] URL 또는 crawling method가 없습니다."
                log_error("general", msg, logger)
                add_error_dict(org_name, "general", msg, error_dict)
                failure_list.append(f"{org_name} ({idx}) - {msg}")
                continue

            # 크롤링 메서드 생성
            crawling_methods = create_crawling_methods(driver, url, css_selector, class_name, logger)
            logger.info(f"Available methods: {" | ".join(method[0] for method in crawling_methods)}")

            data, success_selector, method_name = None, None, None # 값 초기화
            error_details = {}  # 각 방식별 에러 저장

            # 크롤링 진행
            for method_name, method_func, method_args in crawling_methods:
                try:
                    elements = perform_crawling(method_func, method_name, *method_args, logger=logger)
                    if elements:
                        data = extract_element(elements)
                        success_selector = method_args[1] # 크롤링에 성공한 선택자 방식 저장
                        break
                except Exception as e:
                    error_details[method_name] = str(e)  # 에러 정보 임시 저장
                    log_error(method_name, str(e), logger)

            # 데이터가 없거나 네 가지 방식 모두 실패한 경우
            if not data or is_empty_data(data):
                logger.error(f"[FAILURE] {org_name} | 크롤링 실패 ")
                if error_details:
                     # `error_details`에 저장된 메서드별 에러를 `add_error_dict`로 전달
                    for method_name, error_msg in error_details.items():
                        add_error_dict(org_name, method_name, error_msg, error_dict)
                else:
                    add_error_dict(org_name, "general", "[기타] 원인 불명의 오류 발생", error_dict)
                failure_list.append(f"{org_name}({idx})")
                continue

            # 기존 값과 다른 데이터만, unique_data에 저장
            # data = { "method", "by", "last_update_date", "data"}
            unique_data = save_data(data, save_path, method_name, success_selector, logger)
            # unique_data 검증 및 기본값 설정
            if not unique_data or "data" not in unique_data or not isinstance(unique_data["data"], list):
                logger.info(f"[INFO] {org_name}: 새로운 데이터가 없습니다.")
                unique_data = {"data": []}

            # word_filter로 특정 키워드가 포함된 데이터만 추출
            keywords = ['장학', '지원']
            passed_unique_data, failed_data = [], []  # 초기화

            if unique_data["data"]:
                try:
                    passed_unique_data, failed_data = word_filter(keywords, unique_data["data"])
                    if not passed_unique_data:
                        logger.info(f"[INFO] {org_name}: 필터링된 데이터가 없습니다.")
                    if failed_data:
                        logger.debug(f"[DEBUG] {org_name}: 키워드에 매칭되지 않은 데이터: {len(failed_data)}개")
                except Exception as e:
                    logger.error(f"[ERROR] {org_name}: word_filter 호출 중 오류 발생: {e}")

            # Slack 메시지 전송
            if passed_unique_data:
                response = send_slack_scholarship(slack_client, SLACK_CHANNEL_JANGHAK, org_name, passed_unique_data, url)
                if response["status"] == "success":
                    logger.info("[SLACK] 메시지 전송 성공!")
                elif response["status"] == "error":
                    logger.error(f"[SLACK] 메시지 전송 실패: {response['error']}")

            success_count += 1

    except Exception as e:
        logger.error(f"{e}")
        raise

    finally:
        log_with_border("! FINISHED !", logger)
        
        # 반드시 자원 정리
        try:
            if driver:
                driver.quit()
                logger.info("[DRIVER] WebDriver 종료")
        except Exception as e:
            logger.error(f"[DRIVER] 종료 중 오류 발생: {e}")

        try:
            if conn:
                conn.close()
                logger.info("[DB] 데이터베이스 연결 종료")
        except Exception as e:
            logger.error(f"[DB] 종료 중 오류 발생: {e}")

        # 종료 시각 기록
        end_time = time.time()
        elapsed_time = end_time - start_time
        logger.info(f"총 소요 시간: {elapsed_time:.2f}초")

        # 총 결과 로그
        if total_rows:
            logger.info(f"총 {total_rows}개 데이터 중 {success_count}개 업데이트 성공, {len(failure_list)}개 실패")

        # 총 결과 로그를 Slack으로 전송
        try:
            result_message = (
                f"📊 *{config_key} 크롤링 결과 요약 ({current_date})*\n"
                f"> *총 데이터 수*: `{total_rows}`개\n"
                f"> *성공*: `{success_count}`개\n"
                f"> *실패*: `{len(failure_list)}`개\n"
                f"> *소요 시간*: `{elapsed_time:.2f}`초 ⏱️\n"
            )
            response = send_slack_message(slack_client, SLACK_CHANNEL_JANGHAK, result_message)
            if response["status"] == "success":
                logger.info("총 결과 로그 Slack 메시지 전송 성공")
            else:
                logger.error(f"총 결과 로그 Slack 메시지 전송 실패: {response['error']}")
        except Exception as e:
            logger.error(f"총 결과 로그 Slack 메시지를 전송하는 중 오류 발생: {e}")
        
        # 에러 딕셔너리를 JSON 파일로 log 폴더에 저장
        error_file_path = os.path.join("logs", config_key, current_date, f"failed_list_{current_date}.json")
        try:
            with open(error_file_path, 'w', encoding='utf-8') as error_file:
                json.dump(error_dict, error_file, ensure_ascii=False, indent=4)
            logger.info(f"에러 데이터를 {error_file_path}에 저장했습니다.")
        except Exception as e:
            logger.error(f"에러 데이터를 저장하는 중 오류 발생: {e}")
        
         # 에러 딕셔너리를 Slack으로 전송
        try:
            if error_dict:
                response = send_slack_failure_list(config_key, slack_client, SLACK_CHANNEL_NOTICE, error_dict)
                if response["status"] == "success":
                    logger.info("Slack 메시지 전송 성공")
                else:
                    logger.error(f"Slack 메시지 전송 실패: {response['error']}")
            else:
                logger.info("에러 데이터가 없어 Slack 메시지 전송을 건너뜁니다.")
        except Exception as e:
            logger.error(f"Slack 메시지를 전송하는 중 오류 발생: {e}")

        # 실패 목록을 파일로 저장
        failure_file_path = os.path.join("data", config_key, f"error_{config_key}.json")
        try:
            with open(failure_file_path, 'w', encoding='utf-8') as failure_file:
                json.dump(failure_list, failure_file, ensure_ascii=False, indent=4)
            logger.info(f"실패 목록을 {failure_file_path}에 저장했습니다.")
        except Exception as e:
            logger.error(f"실패 목록을 저장하는 중 오류 발생: {e}")

if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "univ"
    main(target)