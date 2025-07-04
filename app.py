import requests
from flask import Flask, jsonify, request
from test import run
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

# 메시지 수신
@app.route('/db', methods=['POST'])
def handle_message():
    try:
        data = request.get_json()
        print(data)

        send_message = run(data)
        print(send_message)

        if send_message:
            requests.post(f'{os.getenv("iris_url")}/reply', json=send_message)
            return jsonify({'봇 응답 성공': True}), 200
        return jsonify({'봇 응답 실패': False}), 200
    except Exception as e:
        return jsonify({f'봇 응답 실패: {str(e)}'}), 500

# 메인 페이지
@app.route('/')
def home():
    return jsonify({
        'message': '카카오봇 서버에 오신 것을 환영합니다!',
        'endpoints': {
            '카카오봇 응답': 'POST /db',
        }
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 