import os
from flask import Flask, request, jsonify
from openai import OpenAI
from dotenv import load_dotenv

# .env 파일에서 환경변수 로드
load_dotenv()

app = Flask(__name__)

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def kakao_text(text):
    """카카오톡 텍스트 응답 규격 생성 (1000자 제한 안전장치)"""
    # 카카오톡 제한인 1000자를 넘지 않도록 950자에서 안전하게 자릅니다.
    safe_text = text[:950] + "..." if len(text) > 950 else text
    return {
        "version": "2.0",
        "template": {
            "outputs": [{
                "simpleText": {
                    "text": safe_text
                }
            }]
        }
    }

def get_user_input(data):
    """
    카카오톡에서 넘어온 입력값을 추출하는 공통 함수
    1. 오픈빌더에서 설정한 'text' 파라미터 값을 먼저 찾습니다.
    2. 파라미터 값이 없다면 사용자가 타이핑한 전체 발화(utterance)를 사용합니다.
    """
    params = data.get("action", {}).get("params", {})
    user_text = params.get("text", "").strip() # 오픈빌더 스킬에서 설정할 파라미터명
    
    if not user_text:
        user_text = data.get("userRequest", {}).get("utterance", "").strip()
        
    return user_text

@app.route("/", methods=["GET"])
def home():
    return "Study Helper Chatbot Server is running."

# 1. 공부돕기 기능 (개념 설명 및 학습 보조)
@app.route("/study-help", methods=["POST"])
def study_help():
    data = request.get_json(silent=True) or {}
    user_input = get_user_input(data)

    if not user_input:
        return jsonify(kakao_text("공부하고 싶은 주제나 질문을 입력해 주세요!"))

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 친절하고 유능한 학생 맞춤형 선생님입니다. 사용자가 묻는 개념이나 주제에 대해 이해하기 쉽게 차근차근 설명해 주세요. 카카오톡 화면에서 읽기 좋게 단락을 나누고 중요한 단어는 강조해 주세요."},
                {"role": "user", "content": f"이 내용에 대해 쉽게 설명해줘 최대한 간결하게 : {user_input}"}
            ],
            temperature=0.7,
            max_tokens=600
        )
        result_text = response.choices[0].message.content.strip()
    except Exception as e:
        result_text = f"오류가 발생했습니다. 다시 시도해 주세요. ({str(e)})"

    return jsonify(kakao_text(result_text))

# 2. 한줄요약 기능 (긴 글 핵심 요약)
@app.route("/summary", methods=["POST"])
def summary():
    data = request.get_json(silent=True) or {}
    user_input = get_user_input(data)

    if not user_input:
        return jsonify(kakao_text("요약할 긴 텍스트를 입력해 주세요!"))

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 요약 전문가입니다. 사용자가 제시한 본문을 분석하여 핵심 내용을 관통하는 '딱 한 줄(한 문장)'로 명확하게 요약해 주세요. 부연 설명 없이 요약문만 즉시 출력하세요."},
                {"role": "user", "content": f"다음 내용을 한 줄로 요약해줘:\n\n{user_input}"}
            ],
            temperature=0.5,
            max_tokens=300
        )
        result_text = response.choices[0].message.content.strip()
    except Exception as e:
        result_text = f"오류가 발생했습니다. 다시 시도해 주세요. ({str(e)})"

    return jsonify(kakao_text(result_text))

# 3. 퀴즈생성 기능 (주제별 맞춤 문제 출제)
@app.route("/quiz", methods=["POST"])
def quiz():
    data = request.get_json(silent=True) or {}
    user_input = get_user_input(data)

    if not user_input:
        return jsonify(kakao_text("퀴즈를 만들고 싶은 주제나 단어를 입력해 주세요! (예: 한국사, 과학, 상식 등)"))

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 퀴즈 출제 위원입니다. 사용자가 제시한 주제에 맞는 유익하고 흥미로운 퀴즈를 딱 '1문제'만 생성해 주세요. 객관식(4지선다) 형태로 문제를 내고, 하단에 [정답]과 [해설]을 명확히 구분하여 작성해 주세요. 줄바꿈을 활용해 가독성을 높여야 합니다."},
                {"role": "user", "content": f"'{user_input}' 주제로 객관식 퀴즈 1개 만들어줘."}
            ],
            temperature=0.8,
            max_tokens=600
        )
        result_text = response.choices[0].message.content.strip()
    except Exception as e:
        result_text = f"오류가 발생했습니다. 다시 시도해 주세요. ({str(e)})"

    return jsonify(kakao_text(result_text))

# 4. 단어뜻 알려주기 기능 (사전적 의미 및 예문 제공)
@app.route("/definition", methods=["POST"])
def definition():
    data = request.get_json(silent=True) or {}
    user_input = get_user_input(data)

    if not user_input:
        return jsonify(kakao_text("뜻이 궁금한 단어를 입력해 주세요!"))

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 친절한 국어/외래어 사전 AI입니다. 사용자가 입력한 단어의 정확한 사전적 정의를 알기 쉽게 설명해 주고, 해당 단어가 실제 대화나 글에서 어떻게 쓰이는지 자연스러운 예문을 2개 이상 만들어 주세요."},
                {"role": "user", "content": f"'{user_input}' 단어의 뜻만 정확히 알려줘."}
            ],
            temperature=0.5,
            max_tokens=500
        )
        result_text = response.choices[0].message.content.strip()
    except Exception as e:
        result_text = f"오류가 발생했습니다. 다시 시도해 주세요. ({str(e)})"

    return jsonify(kakao_text(result_text))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
