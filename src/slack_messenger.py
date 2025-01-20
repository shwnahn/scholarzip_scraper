from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import os
from datetime import datetime

def setup_slack_client():
    """
    Slack WebClient 객체를 생성하는 함수.

    Returns:
    - WebClient: Slack WebClient 객체
    """
    SLACK_TOKEN = os.getenv("SLACK_TOKEN")  # 환경 변수에서 Slack 토큰 가져오기
    client = WebClient(token=SLACK_TOKEN)
    return client

def send_slack_message(slack_client, channel, message):
    """
    일반적인 메시지를 슬랙으로 전송합니다.

    :param slack_client: Slack 클라이언트 객체
    :param channel: Slack 채널
    :param message: 전송할 메시지
    """
    try:
        response = slack_client.chat_postMessage(channel=channel, text=message)
        if response["ok"]:
            return {"status": "success"}
        else:
            return {"status": "error", "error": response["error"]}
    except Exception as e:
        return {"status": "error", "error": str(e)}

def send_slack_opening(config_key, slack_client, channel):
    """
    크롤링 시작 메시지를 슬랙으로 전송합니다.

    :param config_key: 설정 키
    :param slack_client: Slack 클라이언트 객체
    :param channel: Slack 채널
    """
    try:
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f":white_check_mark:   {current_datetime} | {config_key} 크롤링 시작"
        response = slack_client.chat_postMessage(channel=channel, text=message)
        if response["ok"]:
            return {"status": "success"}
        else:
            return {"status": "error", "error": response["error"]}
    except Exception as e:
        return {"status": "error", "error": str(e)}

def send_slack_failure_json(config_key, slack_client, channel, failure_data):
    """
    실패한 크롤링 목록을 슬랙으로 전송합니다.

    :param config_key: 설정 키
    :param slack_client: Slack 클라이언트 객체
    :param channel: Slack 채널
    :param failure_data: 실패한 크롤링 데이터 (JSON 형식)
    """
    try:
        if not failure_data:
            message = f":white_check_mark: {config_key} 크롤링 실패 데이터가 없습니다."
        else:
            # 메시지 구성
            formatted_list = []
            if config_key == "univ":
                for idx, (org_name, errors) in enumerate(failure_data.items(), start=1):
                    # 기관별 에러를 묶음
                    descriptions = "\n".join(f"- {error.get('description', 'No description provided')}" for error in errors)
                    formatted_list.append(f"{org_name} ({idx}):\n{descriptions}")

                message = (
                    f":warning: {config_key} 크롤링 실패 목록 ({len(formatted_list)} 건)\n\n"
                    + "\n\n".join(formatted_list)
                )
            else:
                message = f":white_check_mark: {config_key} 크롤링 실패 데이터가 없습니다."

        # Slack 메시지 전송
        response = slack_client.chat_postMessage(channel=channel, text=message)
        if response["ok"]:
            return {"status": "success"}
        else:
            return {"status": "error", "error": response["error"]}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def send_slack_scholarship(client, channel_id, org_name, details, link):
    """
    Slack 채널에 메시지를 전송하는 함수.

    Parameters:
    - client (WebClient): Slack WebClient 객체
    - channel_id (str): 메시지를 보낼 채널 ID
    - org_name (str): 알림 제목(재단명)
    - details (list): 메시지에 포함될 세부 내용 (각 항목은 문자열 또는 튜플)
    - link (str): 관련 URL

    Returns:
    - dict: 성공 시 {"status": "success", "message_ts": response["ts"]}
    - dict: 실패 시 {"status": "error", "error": e.response['error']}
    - dict: 데이터가 없을 때 {"status": "no_data"}
    """
    if not details:
        return {"status": "no_data"}
    
    if not isinstance(details, list):
        return {"status": "error", "error": "Details must be a list of strings or tuples."}

    # 메시지 구성
    try:
        detail_lines = "\n".join(item[0] if isinstance(item, tuple) else item for item in details)
        message = f":arrow_forward: *{org_name}*\n{link}\n{detail_lines}"
    except Exception as e:
        return {"status": "error", "error": f"Message formatting error: {str(e)}"}

    try:
        # 메시지 전송
        response = client.chat_postMessage(channel=channel_id, text=message)
        return {"status": "success", "message_ts": response["ts"]}
    except SlackApiError as e:
        return {"status": "error", "error": e.response['error']}

def send_slack_failure_list(config_key, slack_client, channel, failure_list):
    """
    실패한 크롤링 목록을 슬랙으로 전송합니다.

    :param slack_client: Slack 클라이언트 객체
    :param channel: Slack 채널
    :param failure_list: 실패한 크롤링 목록
    """
    try:
        message = f":warning: {config_key} 크롤링 실패 목록 ({len(failure_list)} 건)\n" + "\n".join(failure_list)
        response = slack_client.chat_postMessage(channel=channel, text=message)
        if response["ok"]:
            return {"status": "success"}
        else:
            return {"status": "error", "error": response["error"]}
    except Exception as e:
        return {"status": "error", "error": str(e)}
        

## TEST CODE
# from dotenv import load_dotenv
# load_dotenv()

# if __name__ == "__main__":
#     SLACK_TOKEN = os.getenv("SLACK_TOKEN")
#     SLACK_CHANNEL = os.getenv("SLACK_CHANNEL_TEST")
#     slack_client = WebClient(token=SLACK_TOKEN)

#     failure_data = {
#         "전남대학교": [
#             {"type": "general", "description": "[DB] URL 또는 crawling method가 없습니다."},
#             {"type": "method_error", "description": "CSS Selector가 비어 있습니다."}
#         ],
#         "서울대학교": [
#             {"type": "general", "description": "[DB] 데이터베이스 연결 실패"}
#         ]
#     }

#     response = send_slack_failure_json("university_config", slack_client, SLACK_CHANNEL, failure_data)
#     if response["status"] == "success":
#         print("Slack 메시지 전송 성공")
#     else:
#         print("Slack 메시지 전송 실패:", response["error"])


# # def slack_messaging(title, passed_data, url): # passed_data가 유효한 경우에만 Slack 메세지 전송   
# #     msg = f":arrow_forward: {title} / {current_datetime} \n {url} \n" + "\n".join(item[0] for item in passed_data)

# #     if passed_data:
# #         try:
# #             # 메시지 보내기
# #             response = client.chat_postMessage(channel=CHANNEL_ID, text=msg)
            
# #             # # 응답 확인 -> 오류 나서 주석처리함
# #             # assert response["message"]["text"] == msg
# #             print("     *** Slack 메세지 전송 완료 ***      ")
            
# #         except SlackApiError as e:
# #             print(f"!! slack message 전송 오류: {e.response['error']} !!")
# #     else:
