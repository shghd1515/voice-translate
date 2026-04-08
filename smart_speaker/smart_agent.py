from llm_groq import generate_response
from stt import transcribe_wav
from tts import play_audio, tts_to_mp3
from vad import record_vad_to_wav


def run_agent() -> None:
    wav_path = record_vad_to_wav(out_path="user_utterance.wav", record_seconds=10)
    print("STT 처리 중...")
    user_text = transcribe_wav(wav_path, language="ko").strip()
    print(f"인식 결과: {user_text}")

    if not user_text:
        print("인식된 텍스트가 없습니다.")
        return

    print("LLM 응답 생성 중...")
    reply = generate_response(user_text)
    print(f"LLM 응답: {reply}")

    print("TTS 생성 및 재생 중...")
    mp3_path = tts_to_mp3(reply, out_path="assistant_reply.mp3", lang="ko")
    play_audio(mp3_path)


if __name__ == "__main__":
    run_agent()
