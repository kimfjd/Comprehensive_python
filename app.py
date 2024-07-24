from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import requests
import datetime

app = Flask(__name__)
# CORS(app, resources={r"/*": {"origins": "*"}})  # 모든 도메인에서의 요청을 허용
CORS(app, resources={r"/*": {"origins": "*", "supports_credentials": True}})

## 포트원의 IP 주소
# allowed_ips = ["52.78.100.19", "52.78.48.223", "52.78.5.241", "127.0.0.1"]
#
# # IP 주소 확인 함수
# def is_allowed_ip(remote_addr):
#     return remote_addr in allowed_ips

# 토큰 받기
@app.route('/api/iamport/getToken', methods=['POST'])
def get_token():
    try:
        url = "https://api.iamport.kr/users/getToken"
        payload = {
            "imp_key": "6441713254138051",
            "imp_secret": "y05rJjyDEsXLg78LiYn0e6XnbqcyzSS4LYfhf7P1MQqCx4s8O1Vpcsm0QUqqzKbU4wKhSFpezSdMaNB2"
        }
        headers = {"Content-Type": "application/json"}

        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # HTTP 오류 발생 시 예외 처리

        return jsonify(response.json()), response.status_code

    except requests.exceptions.HTTPError as http_err:
        app.logger.error(f"HTTP error occurred: {http_err}")
        return jsonify({'error': f'HTTP error occurred: {http_err}'}), 500
    except requests.exceptions.RequestException as req_err:
        app.logger.error(f"Request error occurred: {req_err}")
        return jsonify({'error': f'Request error occurred: {req_err}'}), 500
    except Exception as e:
        app.logger.error(f"Unexpected error: {e}")
        return jsonify({'error': f'Unexpected error: {e}'}), 500


# 예약 결제
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
# 에약 해지
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
# 결제 정보 포트원에 등록
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
# 결제 예약 해지 한거 다시 예약
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
# 결제 사후 검증( 정확히는 결제 정보 단건 조회) ( 단건 조회 후 프론트에서 사후 검증함)
@app.route('/api/iamport/verifyPayment', methods=['POST'])
def verify_payment():
    imp_uid = request.json.get('imp_uid')
    iamport_token = request.headers.get('Authorization')

    url = f"https://api.iamport.kr/payments/{imp_uid}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {iamport_token}"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return jsonify(response.json())
    else:
        return jsonify({'error': 'Failed to verify payment'}), response.status_code
# 결제 취소
@app.route('/api/iamport/cancelPayment', methods=['POST'])
def cancel_payment():
    imp_uid = request.json.get('imp_uid')
    iamport_token = request.headers.get('Authorization')

    url = "https://api.iamport.kr/payments/cancel"
    payload = {
        "imp_uid": imp_uid
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {iamport_token}"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # HTTP 오류 발생 시 예외 처리

        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'error': 'Failed to cancel payment'}), response.status_code

    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500  # 예기치 못한 오류 발생 시 처리


# 웹훅 수신
@app.route('/api/iamport/webhook', methods=['POST'])
@cross_origin(supports_credentials=True)
def iamport_webhook():
    try:
        data = request.get_json()

        if not data:
            app.logger.info("Invalid data received")
            return jsonify({"message": "Invalid data"}), 400

        app.logger.info(f"Webhook data received: {data}")

        imp_uid = data.get('imp_uid')

        if not imp_uid:
            app.logger.error("Missing imp_uid in webhook data")
            return jsonify({"message": "Missing imp_uid"}), 400

        # 토큰
        token_response = requests.post(
            'http://localhost:5000/api/iamport/getToken'
        )

        if token_response.status_code == 200:
            access_token = token_response.json()['response']['access_token']
            app.logger.info(f"Access token: {access_token}")
        else:
            app.logger.error("Failed to receive access token")
            return jsonify({"message": "Failed to receive access token"}), 500

        # 사후검증(결제 단건 조회)
        verify_response = requests.post(
            'http://localhost:5000/api/iamport/verifyPayment',
            json={'imp_uid': imp_uid},
            headers={'Authorization': access_token}
        )

        if verify_response.status_code == 200:
            payment_data = verify_response.json()['response']
            app.logger.info(f"Payment data: {payment_data}")

            amount = payment_data.get('amount')
            customer_uid = payment_data.get('customer_uid')
            merchant_uid = payment_data.get('merchant_uid')
            pg_provider = payment_data.get('pg_provider')  # pg_provider 값을 가져옵니다.
            today_date = datetime.datetime.now().isoformat()  # 오늘 날짜
            next_schedule_at = int((datetime.datetime.now() + datetime.timedelta(days=30)).timestamp())  # 금일 날짜로 부터 한달뒤 시간을 유닉스 타임스템프 시간으로 변경
            next_schedule_at_local = datetime.datetime.fromtimestamp(next_schedule_at).isoformat()  # 위 유닉스 타임 스템프 시간을 로컬타입으로 변경

            if amount != 10:
                # Cancel payment
                cancel_response = requests.post(
                    'http://localhost:5000/api/iamport/cancelPayment',
                    json={'imp_uid': imp_uid},
                    headers={'Authorization': access_token}
                )

                if cancel_response.status_code == 200:
                    app.logger.info("Payment canceled successfully")
                    return jsonify({"message": "Payment canceled successfully"}), 200
                else:
                    app.logger.error("Failed to cancel payment")
                    return jsonify({"message": "Failed to cancel payment"}), 500
            else:
                # 결제 예약
                next_merchant_uid = f"order_{int(datetime.datetime.now().timestamp())}"

                schedule_data = {
                    'customer_uid': customer_uid,
                    'schedules': [{
                        'merchant_uid': next_merchant_uid,
                        'schedule_at': next_schedule_at,
                        'amount': amount,
                        'name': payment_data.get('name')
                    }]
                }

                schedule_response = requests.post(
                    'http://localhost:5000/api/iamport/schedulePayment',
                    json=schedule_data,
                    headers={'Authorization': access_token}
                )

                if schedule_response.status_code == 200:
                    app.logger.info("Payment scheduled successfully")
                else:
                    app.logger.error("Failed to schedule payment")
                    return jsonify({"message": "Failed to schedule payment"}), 500

                # Save 구독 정보
                subscription_data = {
                    'user': customer_uid,  # buyer_email
                    'transactionId': imp_uid,
                    'paymentDate': today_date,
                    'createdAt': today_date,
                    'validUntil': next_schedule_at_local,
                    'merchantuid': next_merchant_uid,
                    'customerUid': customer_uid,
                    'status': '구독',
                    'billingKeyCreatedAt': today_date
                }

                app.logger.info(f"Sending subscription data to Java backend: {subscription_data}")

                save_subscription_response = requests.post(
                    'http://localhost:8118/payments/subscriptions',  # 프로토콜을 포함한 URL
                    json=subscription_data
                )

                app.logger.info(f"Java backend response status: {save_subscription_response.status_code}")
                app.logger.info(f"Java backend response body: {save_subscription_response.text}")

                if save_subscription_response.status_code == 200:
                    app.logger.info("Subscription data sent to Java backend successfully")
                else:
                    app.logger.error(
                        f"Failed to send subscription data to Java backend: {save_subscription_response.text}")
                    return jsonify({"message": "Failed to send subscription data to Java backend"}), 500


                # 결제 내역 저장 부분
                paymenthistory_data = {
                    'member': customer_uid,  # buyer_email
                    'name': '아프다 1달 구독',
                    'paymentDate': today_date,
                    'paymentStatus': '결재 성공',
                    'transactionId': imp_uid,
                    'amount': amount
                }

                app.logger.info(f"paymenthistory Java backend: {paymenthistory_data}")

                save_paymenthistory_response = requests.post(
                    'http://localhost:8118/payments/save',
                    json=paymenthistory_data
                )

                app.logger.info(f"Java backend response status: {save_paymenthistory_response.status_code}")
                app.logger.info(f"Java backend response body: {save_paymenthistory_response.text}")


                paymentinfo_data= {
                    'email': customer_uid,
                    'paymentMethodCode': pg_provider,
                    'paymentDetails': imp_uid + str(amount) + today_date
                }

                app.logger.info(f"paymentinfo Java backend: {paymentinfo_data}")

                save_paymentinfo_response = requests.post(
                    'http://localhost:8118/payments/info',
                    json=paymentinfo_data
                )

                app.logger.info(f"Java backend response status: {save_paymentinfo_response.status_code}")
                app.logger.info(f"Java backend response body: {save_paymentinfo_response.text}")

                if save_paymentinfo_response.status_code == 200:
                    app.logger.info("paymentinfo data sent to Java backend successfully")
                    return jsonify({"message": "paymentinfo data sent to Java backend successfully"}), 200
                else:
                    app.logger.error(
                        f"Failed to send paymentinfo data to Java backend: {save_paymentinfo_response.text}")
                    return jsonify({"message": "Failed to send paymentinfo data to Java backend"}), 500
        else:
            app.logger.error("Failed to verify payment")
            return jsonify({"message": "Failed to verify payment"}), 500

    except Exception as e:
        app.logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'success': False, 'message': f"Unexpected error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(ssl_context=('cert.pem', 'key.pem'))
