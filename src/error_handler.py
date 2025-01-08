def log_error(method_name, message, logger):
    """
    에러를 로깅합니다.
    """
    logger.error(f"[ERROR] {method_name} | 오류: {message}")

def add_error_dict(org_name, method_name, message, error_dict):
    """
    에러를 기록하고 error_dict에 추가합니다.
    """
    # 에러 구조 초기화
    if org_name not in error_dict:
        error_dict[org_name] = []
    
    # 에러 항목 추가
    error_entry = {
        "type": method_name,
        "description": message
    }
    error_dict[org_name].append(error_entry)
