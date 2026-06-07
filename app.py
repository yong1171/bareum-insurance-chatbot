from flask import Flask, request, jsonify
import anthropic
import os
import threading

app = Flask(__name__)

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """당신은 바른보험연구소 보험전문가 Mr.FC입니다.

규칙:
- 친절하고 전문적으로 답변
- 카카오톡에 맞게 짧은 문단으로 나눠서 작성
- 이모지 적절히 사용
- 보험 전문용어는 쉽게 설명
- 전화 유도 절대 하지 말것
- 핵심을 명확하게 설명

전문분야: 생명보험, 손해보험, 실손보험, 보험금 청구, 보장분석, 암보험, 건강보험, 간병보험, 보험료 절감"""

# 임시 저장소 (답변 캐시)
pending_responses = {}

@app.route('/', methods=['GET'])
def health_check():
    return "OK", 200

@app.route('/ping', methods=['GET'])
def ping():
    return "pong", 200

def generate_ai_response(session_id, user_message):
    """백그라운드에서 AI 답변 생성"""
    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=400,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}]
        )
        pending_responses[session_id] = message.content[0].text
        print(f"AI답변 생성완료: {session_id}")
    except Exception as e:
        pending_responses[session_id] = f"오류: {e}"

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json(force=True)
        print(f"요청: {data}")

        user_message = ""
        session_id = ""
        if data:
            user_message = data.get('userRequest', {}).get('utterance', '').strip()
            session_id = data.get('userRequest', {}).get('user', {}).get('id', 'default')

        print(f"메시지: {user_message}, 세션: {session_id}")

        if not user_message:
            return jsonify(kakao_response("안녕하세요! 바른보험연구소 Mr.FC입니다 😊\n\n보험금 청구, 보장분석, 보험 정리 등\n궁금한 점 편하게 물어보세요!"))

        # 이전 답변이 캐시에 있으면 반환
        if session_id in pending_responses:
            response = pending_responses.pop(session_id)
            return jsonify(kakao_response(response))

        # 백그라운드에서 Sonnet 답변 생성 시작
        thread = threading.Thread(target=generate_ai_response, args=(session_id, user_message))
        thread.start()

        # 3초 기다려보기
        thread.join(timeout=3.5)

        # 3.5초 안에 답변 왔으면 바로 반환
        if session_id in pending_responses:
            response = pending_responses.pop(session_id)
            return jsonify(kakao_response(response))

        # 타임아웃 직전 빠른 답변 반환
        return jsonify(kakao_response("잠시만요 😊 답변을 준비중이에요!\n\n다시 한번 같은 질문을 보내주시면\n자세한 답변 드릴게요 🙏"))

    except Exception as e:
        print(f"오류: {e}")
        return jsonify(kakao_response("잠시 후 다시 시도해주세요 😊"))

def kakao_response(text):
    return {
        "version": "2.0",
        "template": {
            "outputs": [{"simpleText": {"text": text}}],
            "quickReplies": [
                {"label": "보험금 청구", "action": "message", "messageText": "보험금 청구 방법 알려주세요"},
                {"label": "보장분석 신청", "action": "message", "messageText": "무료 보장분석 신청하고 싶어요"},
                {"label": "보험료 절감", "action": "message", "messageText": "보험료 절감 방법 알려주세요"}
            ]
        }
    }

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
