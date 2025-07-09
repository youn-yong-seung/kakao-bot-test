from flask import Flask, request, jsonify
import pymysql
import json
import os
from dotenv import load_dotenv
from datetime import datetime
import requests
import logging
from logging.handlers import TimedRotatingFileHandler
from utils.schedule import background_schedule_cron, background_schedule_interval
import traceback
from bot.placebot import placebot_run
from bot.weatherbot import weatherbot_run

# 환경변수 로드
load_dotenv()

app = Flask(__name__)

# 로깅 설정
def setup_logging():
    """매일 새로운 로그 파일을 생성하는 로깅 설정"""
    # logs 디렉토리 생성
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # 현재 날짜로 로그 파일명 생성
    current_date = datetime.now().strftime('%Y%m%d')
    log_filename = f'logs/{current_date}.log'
    
    # 로거 설정
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # 기존 핸들러 제거 (중복 방지)
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # 파일 핸들러 설정 (현재 날짜 파일명으로 직접 생성)
    file_handler = logging.FileHandler(
        filename=log_filename,
        encoding='utf-8'
    )
    
    # 콘솔 핸들러 설정
    console_handler = logging.StreamHandler()
    
    # 로그 포맷 설정
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 핸들러 추가
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# 날짜가 바뀌었을 때 로그 파일을 업데이트하는 함수
def update_log_file_if_needed():
    """날짜가 바뀌었으면 새로운 로그 파일로 변경"""
    current_date = datetime.now().strftime('%Y%m%d')
    expected_filename = f'logs/{current_date}.log'
    
    # 현재 파일 핸들러의 파일명 확인
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler):
            if handler.baseFilename != os.path.abspath(expected_filename):
                # 날짜가 바뀌었으므로 새로운 로그 파일로 변경
                handler.close()
                logger.removeHandler(handler)
                
                # 새로운 파일 핸들러 생성
                new_file_handler = logging.FileHandler(
                    filename=expected_filename,
                    encoding='utf-8'
                )
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
                new_file_handler.setFormatter(formatter)
                logger.addHandler(new_file_handler)
                logger.info(f"새로운 로그 파일로 변경: {expected_filename}")
                break

# 로깅 설정 초기화
logger = setup_logging()

# 데이터베이스 연결 설정
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT')),  # type: ignore
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME'),
    'charset': 'utf8mb4'
}

def get_db_connection():
    """데이터베이스 연결을 반환합니다."""
    try:
        connection = pymysql.connect(**DB_CONFIG)
        # logger.info("데이터베이스 연결 성공")
        return connection
    except Exception as e:
        logger.error(f"데이터베이스 연결 오류: {e}")
        return None

def save_message(data):
    """카카오톡 메시지 데이터를 데이터베이스에 저장합니다."""
    connection = get_db_connection()
    if not connection:
        return False, "데이터베이스 연결 실패"
    
    try:
        with connection.cursor() as cursor:
            # JSON 데이터에서 필요한 정보 추출
            json_data = data.get('json', {})
            
            # version_info JSON 문자열 처리
            version_info = json_data.get('v')
            if isinstance(version_info, str):
                try:
                    version_info = json.dumps(json.loads(version_info), ensure_ascii=False)
                except:
                    pass  # JSON 파싱 실패 시 원본 문자열 유지
            
            # INSERT 쿼리
            insert_query = """
                INSERT INTO kakao_messages (
                    msg, room, sender, message_id, message_type, chat_id, user_id,
                    message_content, attachment, created_at, deleted_at, client_message_id,
                    prev_id, referer, supplement, version_info
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    msg = VALUES(msg),
                    room = VALUES(room),
                    sender = VALUES(sender),
                    message_type = VALUES(message_type),
                    message_content = VALUES(message_content),
                    attachment = VALUES(attachment),
                    version_info = VALUES(version_info),
                    received_at = CURRENT_TIMESTAMP
            """
            
            # 데이터 준비
            values = (
                data.get('msg'),
                data.get('room'),
                data.get('sender'),
                json_data.get('id'),
                json_data.get('type'),
                json_data.get('chat_id'),
                json_data.get('user_id'),
                json_data.get('message'),
                json_data.get('attachment'),
                int(json_data.get('created_at', 0)) if json_data.get('created_at') else None,
                int(json_data.get('deleted_at', 0)) if json_data.get('deleted_at') else None,
                json_data.get('client_message_id'),
                json_data.get('prev_id'),
                json_data.get('referer'),
                json_data.get('supplement'),
                version_info
            )
            
            cursor.execute(insert_query, values)
            connection.commit()
            logger.info(f"메시지 저장 성공 - ID: {json_data.get('id')}, 발신자: {data.get('sender')}")
            
            return True, "메시지 저장 성공"
            
    except Exception as e:
        logger.error(f"데이터 저장 오류: {e}")
        return False, f"데이터 저장 오류: {str(e)}"
    finally:
        connection.close()

def send_message(data):
    """IRIS로 메시지를 전송합니다."""
    try:
        print(data)
        url = os.getenv('IRIS_URL') + "/reply" # type: ignore
        logger.info(f"메시지 전송 시도 - URL: {url}")
        send_data = {
            "room": data.get("chat_id"),
            "type": "image_multiple" if data.get("type") == "image" else "text",
            "data": data.get("data")
        }
        response = requests.post(url, json=send_data)
        logger.info(f"메시지 전송 성공 - 응답 코드: {response.status_code}")
        return response.json()
    except Exception as e:
        logger.error(f"메시지 전송 오류: {traceback.format_exc()}")
        raise

def get_src_info(data):
    """답장 정보를 조회합니다."""
    try:
        attachment = json.loads(data["json"]["attachment"])

        if attachment == {}:
            return None
        
        src_logId = attachment["src_logId"]
        
        src_query = f"SELECT sender, message_content FROM kakao_messages WHERE message_id = {src_logId}"
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        cursor.execute(src_query)
        row = cursor.fetchone()
        connection.close()

        return {
            "is_reply": True,
            "src_sender": row[0], # type: ignore
            "src_message": row[1], # type: ignore
        }
    
    except Exception as e:
        logger.error(f"답장 정보 조회 오류: {e}")
        return None
    
def get_exist_room(data):
    """채팅방 존재 여부를 확인합니다."""
    try:
        chat_id = data["json"]["chat_id"]

        # rooms 테이블에서 chat_id와 used_yn 확인
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        check_query = "SELECT chat_id FROM rooms WHERE chat_id = %s AND used_yn = 'Y'"
        cursor.execute(check_query, (chat_id,))
        result = cursor.fetchone()
        
        connection.close()
        
        if not result:
            # logger.warning(f"유효하지 않은 chat_id 또는 비활성화된 채팅방: {chat_id}")
            return None
        
        return True
    
    except Exception as e:
        logger.error(f"채팅방 존재 여부 확인 오류: {e}")
        return False


def send_webhook(data):
    """웹훅으로 데이터를 전송합니다."""
    try:
        chat_id = data["json"]["chat_id"]
        chat_time = datetime.fromtimestamp(int(data['json']['created_at'])).strftime('%Y-%m-%dT%H:%M:%S+09:00')
        url = os.getenv('WEBHOOK_URL')
        
        # rooms 테이블에 채팅방이 없으면 웹훅 전송 안함
        is_exist_room = get_exist_room(data)
        if not is_exist_room:
            return None

        # 메시지가 답장인지 조회
        src_info = get_src_info(data)


        logger.info(f"웹훅 전송 시도 - URL: {url}")
        
        if src_info:
            webhook_data = {
                "room": data.get("room"),
                "chat_id": chat_id,
                "sender": data.get("sender"),
                "msg": data.get("msg"),
                "chat_time": chat_time,
                "reply": {
                    "sender": src_info["src_sender"],
                    "msg": src_info["src_message"]
                }
            }
        else:
            webhook_data = {
                "room": data.get("room"),
                "chat_id": chat_id,
                "sender": data.get("sender"),
                "msg": data.get("msg"),
                "chat_time": chat_time
            }
        logger.info(f"웹훅 전송 데이터: {webhook_data}")
        response = requests.post(url, json=webhook_data) # type: ignore
        logger.info(f"웹훅 전송 성공 - 응답 코드: {response.status_code}")
        return True
    except Exception as e:
        logger.error(f"웹훅 전송 오류: {traceback.format_exc()}")
        raise


@app.route('/')
def home():
    return jsonify({"message": "Welcome to Flask API"})


# 메시지 전송
@app.route('/send', methods=['POST'])
def send():
    # 날짜가 바뀌었는지 확인하고 로그 파일 업데이트
    update_log_file_if_needed()
    
    try:
        data = request.json
        logger.info(f"메시지 전송 요청 수신 - 데이터: {data}")

        # 데이터 유효성 검사
        if not data:
            logger.warning("메시지 전송 요청에 데이터가 없음")
            return jsonify({"result": False, "error": "데이터가 없습니다."}), 400
        
        required_fields = ['chat_id', 'type', 'data']
        for field in required_fields:
            if field not in data:
                logger.warning(f"필수 필드 '{field}' 누락")
                return jsonify({"result": False, "error": f"필수 필드 '{field}' 없음"}), 400
            
        if not data['chat_id'].isdigit():
            logger.warning(f"chat_id는 숫자로만 이루어져야 합니다: {data['chat_id']}")
            return jsonify({
                "result": False,
                "error": "chat_id는 숫자로만 이루어져야 합니다"
            }), 400

        if data['type'] not in ['text', 'image']:
            logger.warning(f"지원하지 않는 메시지 타입: {data['type']}")
            return jsonify({
                "result": False, 
                "error": f"지원하지 않는 메시지 타입입니다. (지원 타입: text, image)"
            }), 400
        
        if data['type'] == 'image' and not isinstance(data['data'], list):
            logger.warning("이미지 타입의 데이터는 리스트 형태여야 합니다")
            return jsonify({
                "result": False,
                "error": "이미지 타입의 데이터는 리스트 형태여야 합니다"
            }), 400

        # 메시지 전송
        send_message(data)
        logger.info("메시지 전송 완료")

        return jsonify({"result": True, "data": data})
    
    except Exception as e:
        logger.error(f"메시지 전송 요청 처리 오류: {e}")
        return jsonify({
            "result": False,
            "error": "메시지 전송중 오류가 발생했습니다.",
            "message": str(e)
        }), 500

# 메시지 수신 이벤트
@app.route('/db', methods=['POST'])
def receive():
    # 날짜가 바뀌었는지 확인하고 로그 파일 업데이트
    update_log_file_if_needed()
    
    try:
        data = request.json
        logger.info(f"메시지 수신 - {data}")
        
        # 데이터 유효성 검사
        if not data:
            logger.warning("메시지 수신 요청에 데이터가 없음")
            return jsonify({"error": "데이터가 없습니다."}), 400
        
        # 필수 필드 확인
        required_fields = ['msg', 'room', 'sender', 'json']
        for field in required_fields:
            if field not in data:
                logger.warning(f"필수 필드 '{field}' 누락")
                return jsonify({"error": f"필수 필드 '{field}'가 없습니다."}), 400
        
        # 데이터베이스에 저장
        success, message = save_message(data)

        # 플레이스봇 처리
        placebot_run(data)

        # 수신 메시지 웹훅 전송
        send_webhook(data)
        
        if success:
            logger.info("메시지 수신 및 저장 완료")
            return jsonify({
                "result": True,
                "message": "데이터 수신 및 저장 성공",
                "data": data,
                "status": message
            }), 200
        else:
            logger.error(f"메시지 저장 실패: {message}")
            return jsonify({
                "result": False,
                "error": "데이터 저장 실패",
                "message": message,
                "data": data
            }), 500
            
    except Exception as e:
        logger.error(f"메시지 수신 요청 처리 오류: {e}")
        return jsonify({
            "result": False,
            "error": "요청 처리 중 오류 발생",
            "message": str(e)
        }), 500

# 날씨 테스트 메시지"
background_schedule_cron(lambda: weatherbot_run.weatherbot_run("18453992993191424"), hour=7, minute=0, job_id='weather_18453992993191424')

if __name__ == '__main__':
    logger.info("Flask 애플리케이션 시작")
    logger.info(f"서버 주소: http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)