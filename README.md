# 🎙️ Voice Translation Suite

한국어 음성을 실시간으로 인식하고, 일본어 · 영어 · 프랑스어 · 중국어로 번역하며 AI 예상 답변까지 생성하는 웹 기반 번역 도구입니다.

---

## 주요 기능

- **음성 인식 (STT)** — Web Speech API를 통해 한국어 음성을 실시간 텍스트로 변환
- **다국어 번역** — Gemini AI를 이용해 일본어 / 영어 / 프랑스어 / 중국어(간체) 번역
- **AI 예상 답변 생성** — 번역된 문장에 대한 상대방의 예상 답변을 외국어 + 한국어 해석으로 함께 제공
- **TTS (Text-to-Speech)** — 번역 결과 및 예상 답변을 음성으로 재생
- **번역 히스토리** — 세션 내 번역 기록 관리

---

## 기술 스택

| 구분 | 기술 |
|------|------|
| Backend | Python, FastAPI, Uvicorn |
| AI | Google Gemini API (`google-genai`) |
| Frontend | HTML / CSS / Vanilla JS |
| STT | Web Speech API (브라우저 내장) |
| TTS | Web Speech Synthesis API (브라우저 내장) |
| 환경변수 | python-dotenv |

---

## 프로젝트 구조

```
voice-translation/
├── app.py              # FastAPI 서버 (번역 API 포함)
├── requirement.txt     # Python 의존성
├── .env.example        # 환경변수 예시 (실제 키는 .env에 별도 관리)
├── .gitignore
└── static/
    └── index.html      # 프론트엔드 UI
```

> `index.html`은 `static/` 폴더 안에 위치해야 합니다.

---

## 시작하기

### 1. 저장소 클론

```bash
git clone https://github.com/shghd1515/voice-translation.git
cd voice-translation
```

### 2. 의존성 설치

```bash
pip install -r requirement.txt
```

### 3. 환경변수 설정

`.env.example`을 복사해 `.env` 파일을 생성한 후, 발급받은 API 키를 입력합니다.

```bash
cp .env.example .env
```

```env
GEMINI_API_KEY=your_google_ai_studio_api_key
GEMINI_MODEL=models/gemini-2.5-flash
HOST=127.0.0.1
PORT=5177
```

- Gemini API 키 발급: [Google AI Studio](https://aistudio.google.com/app/apikey)

### 4. 서버 실행

```bash
python app.py
```

브라우저에서 [http://127.0.0.1:5177](http://127.0.0.1:5177) 접속

---

## API 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| `GET` | `/` | 메인 UI (index.html) |
| `GET` | `/api/health` | 서버 상태 확인 |
| `GET` | `/api/models` | 사용 가능한 Gemini 모델 목록 |
| `POST` | `/api/translate` | 번역 + 예상 답변 생성 |

### POST `/api/translate` 요청 예시

```json
{
  "text": "안녕하세요, 만나서 반갑습니다.",
  "target": "ja"
}
```

### 응답 예시

```json
{
  "model": "models/gemini-2.5-flash",
  "translatedText": "こんにちは、お会いできて嬉しいです。",
  "predictedResponse": "こちらこそ、よろしくお願いします。",
  "predictedResponseKo": "저도 잘 부탁드립니다."
}
```

`target` 가능 값: `ja` / `en` / `fr` / `zh-CN`

---

## 주의사항

- **음성 인식은 Chrome 또는 Edge 브라우저에서만 정상 동작합니다.**
- `.env` 파일은 절대 Git에 커밋하지 마세요. `.gitignore`에 반드시 포함되어 있어야 합니다.

---

## 라이선스

MIT License
