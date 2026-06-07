from flask import Flask, request, jsonify
import anthropic
import os

app = Flask(__name__)

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """당신은 바른보험연구소의 보험 전문가 Mr.FC입니다.

역할:
- 보험 관련 질문에 친절하고 전문적으로 답변
- 보험금 청구 방법 안내
- 보장분석 및 불필요한 보험 정리 상담
- 새로운 보험 상품 추천

답변 규칙:
- 카카오톡 메시지에 맞게 간결하고 친근하게 작성
- 이모지를 적절히 사용
- 전문 용어는 쉽게 풀어서 설명
- 답변은 300자 이내로 간결하게
- 마지막에 항상 추가 상담 유도
"""

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "message": "바른보험연구소 챗봇 서버 정상 작동중"}), 200

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        
        # 카카오 오픈빌더 요청 파싱
        user_message = data.get('userRequest', {}).get('utterance', '')
        
        if not user_message:
            return jsonify(kakao_response("안녕하세요! 바른보험연구소입니다 😊 무엇이든 물어보세요!"))
        
        # Claude AI 답변 생성
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}]
        )
        
        ai_response = message.content[0].text
        return jsonify(kakao_response(ai_response))
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify(kakao_response("죄송해요 😊 잠시 후 다시 시도해주세요. 긴급 상담은 채널 프로필의 전화번호로 연락주세요!"))

def kakao_response(text):
    return {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {
                        "text": text
                    }
                }
            ],
            "quickReplies": [
                {
                    "label": "보험금 청구 방법",
                    "action": "message",
                    "messageText": "보험금 청구 방법 알려주세요"
                },
                {
                    "label": "보장분석 신청",
                    "action": "message", 
                    "messageText": "무료 보장분석 신청하고 싶어요"
                },
                {
                    "label": "보험료 절감",
                    "action": "message",
                    "messageText": "보험료 절감 방법 알려주세요"
                }
            ]
        }
    }

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
