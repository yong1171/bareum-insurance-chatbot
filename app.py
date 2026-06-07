from flask import Flask, request, jsonify
import anthropic
import os

app = Flask(__name__)

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """당신은 바른보험연구소 보험전문가 Mr.FC입니다.
답변규칙:
- 반드시 100자 이내로 매우 짧게
- 이모지 1~2개만 사용
- 핵심만 간단히
- 자세한 상담은 전화 유도"""

@app.route('/', methods=['GET'])
def health_check():
    return "OK", 200

@app.route('/ping', methods=['GET'])
def ping():
    return "pong", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json(force=True)
        print(f"요청데이터: {data}")

        user_message = ""
        if data:
            user_message = data.get('userRequest', {}).get('utterance', '').strip()

        print(f"사용자메시지: {user_message}")

        if not user_message:
            return jsonify(kakao_response("안녕하세요! 바른보험연구소 Mr.FC입니다 😊 궁금한 점 편하게 물어보세요!"))

        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=150,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}]
        )

        ai_response = message.content[0].text
        print(f"AI답변: {ai_response}")
        return jsonify(kakao_response(ai_response))

    except Exception as e:
        print(f"오류: {e}")
        return jsonify(kakao_response("잠시 후 다시 시도해주세요 😊"))

def kakao_response(text):
    return {
        "version": "2.0",
        "template": {
            "outputs": [{"simpleText": {"text": text}}],
            "quickReplies": [
                {"label": "보험금 청구", "action": "message", "messageText": "보험금 청구 방법"},
                {"label": "보장분석 신청", "action": "message", "messageText": "무료 보장분석 신청"},
                {"label": "보험료 절감", "action": "message", "messageText": "보험료 절감 방법"}
            ]
        }
    }

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
