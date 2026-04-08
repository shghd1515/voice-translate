import speech_recognition as sr


def transcribe_wav(path: str, language: str = "ko") -> str:
    recognizer = sr.Recognizer()
    with sr.AudioFile(path) as source:
        audio_data = recognizer.record(source)
    try:
        return recognizer.recognize_google(audio_data, language=language)
    except sr.UnknownValueError:
        return ""


if __name__ == "__main__":
    audio_file = "sample.wav"
    print("음성을 인식 중입니다....")
    text = transcribe_wav(audio_file, language="ko")
    print("변환된 텍스트 : ", text)
