from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import requests

app = Flask(__name__)
CORS(app, supports_credentials=True)  # 모든 도메인에서의 요청을 허용하고, credentials 지원

@app.route('/api/iamport/getToken', methods=['POST'])
def get_token():
    url = "https://api.iamport.kr/users/getToken"
    payload = {
        "imp_key": "6441713254138051",
        "imp_secret": "y05rJjyDEsXLg78LiYn0e6XnbqcyzSS4LYfhf7P1MQqCx4s8O1Vpcsm0QUqqzKbU4wKhSFpezSdMaNB2"
    }
    headers = {"Content-Type": "application/json"}

    response = requests.post(url, json=payload, headers=headers)
    return jsonify(response.json()), response.status_code

@app.route('/api/iamport/schedulePayment', methods=['POST','OPTIONS'])
@cross_origin(supports_credentials=True)
def schedule_payment():
    schedule_data = request.get_json()

    url = "https://api.iamport.kr/subscribe/payments/schedule"
    headers = {
        "Content-Type": "application/json",
        "Authorization": request.headers.get('Authorization')
    }

    response = requests.post(url, json=schedule_data, headers=headers)
    return jsonify(response.json()), response.status_code

@app.route('/api/iamport/unschedulePayment', methods=['POST', 'OPTIONS'])
@cross_origin(supports_credentials=True)
def unschedule_payment():
    if request.method == 'OPTIONS':
        return '', 200

    customer_uid = request.json.get("customer_uid")
    merchant_uid = request.json.get("merchant_uid")

    url = "https://api.iamport.kr/subscribe/payments/unschedule"
    headers = {
        "Content-Type": "application/json",
        "Authorization": request.headers.get('Authorization')
    }
    payload = {"customer_uid": customer_uid, "merchant_uid": merchant_uid}  # merchant_uid 추가

    response = requests.post(url, json=payload, headers=headers)
    return jsonify(response.json()), response.status_code

@app.route('/api/iamport/preparePayment', methods=['POST', 'OPTIONS'])
@cross_origin(supports_credentials=True)
def prepare_payment():
    if request.method == 'OPTIONS':
        return '', 200

    merchant_uid = request.json.get("merchant_uid")
    amount = request.json.get("amount")

    url = "https://api.iamport.kr/payments/prepare"
    headers = {
        "Content-Type": "application/json",
        "Authorization": request.headers.get('Authorization')
    }
    payload = {
        "merchant_uid": merchant_uid,
        "amount": amount
    }

    response = requests.post(url, json=payload, headers=headers)
    return jsonify(response.json()), response.status_code

@app.route('/api/iamport/reschedulePayment', methods=['POST', 'OPTIONS'])
@cross_origin(supports_credentials=True)
def reschedule_payment():
    if request.method == 'OPTIONS':
        return '', 200

    merchant_uid = request.json.get("merchant_uid")
    schedule_at = request.json.get("schedule_at")

    url = f"https://api.iamport.kr/subscribe/payments/schedule/{merchant_uid}/reschedule"
    headers = {
        "Content-Type": "application/json",
        "Authorization": request.headers.get('Authorization')
    }
    payload = {
        "schedule_at": schedule_at
    }

    response = requests.post(url, json=payload, headers=headers)
    return jsonify(response.json()), response.status_code

if __name__ == '__main__':
    app.run(debug=True, port=5000)


if __name__ == '__main__':
    app.run(debug=True, port=5000)


