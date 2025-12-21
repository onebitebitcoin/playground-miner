#!/usr/bin/env python3
"""
Gemini API 테스트 스크립트
.env 파일의 GEMINI_API_KEY를 사용하여 Gemini API를 테스트합니다.
"""

import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

def test_gemini_api():
    """Gemini API를 테스트합니다."""
    api_key = os.getenv('GEMINI_API_KEY')

    if not api_key:
        print("❌ GEMINI_API_KEY를 찾을 수 없습니다.")
        return

    print(f"✅ API Key 로드 완료: {api_key[:10]}...")

    try:
        import google.generativeai as genai
        print("✅ google-generativeai 패키지 import 성공")
    except ImportError:
        print("❌ google-generativeai 패키지가 설치되지 않았습니다.")
        print("설치 명령: pip install google-generativeai")
        return

    # Gemini API 설정
    genai.configure(api_key=api_key)
    print("✅ Gemini API 설정 완료")

    # 사용 가능한 모델 목록 확인
    print("\n📋 사용 가능한 모델 목록:")
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"  - {m.name}")
    except Exception as e:
        print(f"  ⚠️  모델 목록 조회 실패: {e}")

    # 모델 초기화 (첫 번째 사용 가능한 모델 사용)
    try:
        available_models = [
            m for m in genai.list_models()
            if 'generateContent' in m.supported_generation_methods
        ]
        if available_models:
            model_name = available_models[0].name.replace('models/', '')
            print(f"\n✅ 사용할 모델: {model_name}")
            model = genai.GenerativeModel(model_name)
        else:
            print("❌ 사용 가능한 모델이 없습니다.")
            return
    except Exception as e:
        print(f"❌ 모델 초기화 실패: {e}")
        return

    # 테스트 질문
    test_prompt = "비트코인이 무엇인지 한 문장으로 설명해주세요."
    print(f"\n📝 질문: {test_prompt}")
    print("⏳ Gemini API 호출 중...")

    try:
        # API 호출
        response = model.generate_content(test_prompt)
        print(f"\n✅ 응답 받음:")
        print(f"{'='*60}")
        print(response.text)
        print(f"{'='*60}")

        print("\n✅ Gemini API 테스트 성공!")

    except Exception as e:
        print(f"\n❌ API 호출 실패: {str(e)}")
        return

if __name__ == "__main__":
    print("🚀 Gemini API 테스트 시작\n")
    test_gemini_api()
