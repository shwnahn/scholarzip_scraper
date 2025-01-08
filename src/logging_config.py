import logging
import os
from datetime import datetime

current_date = datetime.now().strftime("%Y-%m-%d")

def setup_logging(sub_dir):
    """
    주어진 서브 디렉토리(logs/{sub_dir})에 로그를 설정합니다.
    """
     # 기존 로거 초기화 여부 확인
    if sub_dir in logging.Logger.manager.loggerDict:
        print(f"[DEBUG] 로거 '{sub_dir}'는 이미 초기화되어 있습니다.")
        return logging.getLogger(sub_dir)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    # 로그 디렉토리 생성
    base_dir = "logs"
    log_dir = os.path.join(base_dir, sub_dir)
    current_date = datetime.now().strftime("%Y-%m-%d")
    current_time = datetime.now().strftime("%Y-%m-%d_%H:%M")
    daily_dir = os.path.join(log_dir, current_date)  # 날짜별 디렉토리 생성
    os.makedirs(daily_dir, exist_ok=True)

    # 로거 설정
    logger = logging.getLogger(sub_dir)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False # 로그 전파 방지

    # 기존 핸들러 제거 (중복 방지)
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # 포매터 설정
    formatter = logging.Formatter('[%(levelname)s] %(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    
    # 로그 파일 경로 설정
    info_log_file = os.path.join(daily_dir, f"info_{current_time}.log")
    error_log_file = os.path.join(daily_dir, f"error_{current_time}.log")

   # StreamHandler 설정 (콘솔 출력)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # FileHandler 설정 (INFO 레벨 로그 저장)
    info_file_handler = logging.FileHandler(info_log_file, encoding='utf-8')
    info_file_handler.setLevel(logging.INFO)
    info_file_handler.setFormatter(formatter)
    logger.addHandler(info_file_handler)

    # FileHandler 설정 (ERROR 레벨 로그 저장)
    error_file_handler = logging.FileHandler(error_log_file, encoding='utf-8')
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(formatter)
    logger.addHandler(error_file_handler)

    # 디버깅 출력
    print(f"[DEBUG] 현재 로거 '{sub_dir}'의 핸들러 수: {len(logger.handlers)}")
    for handler in logger.handlers:
        print(f"[DEBUG] 핸들러: {handler}")
    print(f"[DEBUG] ({sub_dir}) INFO 로그 파일: {info_log_file}")
    print(f"[DEBUG] ({sub_dir}) ERROR 로그 파일: {error_log_file}")
    
    return logger

def log_with_border(message, logger, width=50):
    border = "=" * width
    # 메시지 길이에 따라 중앙 정렬
    padded_message = f"{message}".center(width)
    logger.info(border)
    logger.info(padded_message)
    logger.info(border)

# # 로깅 설정
# logger = setup_logging("test")

# # 테스트 로그
# logger.debug("This is a DEBUG message.")   # 콘솔 및 파일 저장
# logger.info("This is an INFO message.")    # 콘솔 및 파일 저장
# logger.error("This is an ERROR message.")  # 콘솔, 파일1, 파일2 저장