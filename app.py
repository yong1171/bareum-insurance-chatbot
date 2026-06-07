from flask import Flask, request, jsonify
import anthropic
import os

app = Flask(__name__)

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """당신은 바른보험연구소의 보험전문가 Mr.FC입니다.

답변 규칙:
- 질문에 대해 친절하고 충분히 설명해주세요
- 카카오톡에 맞게 짧은 문단으로 나눠서 작성
- 이모지를 적절히 사용해서 읽기 쉽게
- 300자 이내로 핵심을 잘 설명
- 전화 유도 절대 하지 말것
- 모르는 내용은 솔직하게 모른다고 하고 보험사 문의 안내
- 보험 전문 용어는 쉽게 풀어서 설명

전문 분야:
- 생명보험, 손해보험, 실손보험
- 보험금 청구 방법
- 보장분석 및 보험 정리
- 암보험, 건강보험, 간병보험
- 보험료 절감 방법"""

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
            return jsonify(kakao_response("안녕하세요! 바른보험연구소입니다 😊\n\n보험금 청구, 보장분석, 보험 정리 등\n궁금한 점 편하게 물어보세요!"))

        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=400,
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
                {"label": "보험금 청구", "action": "message", "messageText": "보험금 청구 방법 알려주세요"},
                {"label": "보장분석 신청", "action": "message", "messageText": "무료 보장분석 신청하고 싶어요"},
                {"label": "보험료 절감", "action": "message", "messageText": "보험료 절감 방법 알려주세요"}
            ]
        }
    }

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
