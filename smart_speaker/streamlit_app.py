import io
from typing import Tuple

import numpy as np
import soundfile as sf
import streamlit as st

from llm_groq import generate_response
from stt import transcribe_wav
from tts import tts_to_mp3
from pydub import AudioSegment

try:
    from streamlit_mic_recorder import mic_recorder
except Exception as exc:  # noqa: BLE001
    mic_recorder = None
    _MIC_IMPORT_ERROR = exc
else:
    _MIC_IMPORT_ERROR = None


SAMPLE_RATE = 16000
FRAME_MS = 30
ENERGY_THRESHOLD = 0.01


def _load_audio_bytes(audio_bytes):
    audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
    
    samples = np.array(audio.get_array_of_samples()).astype("float32") / 32768.0
    sr = audio.frame_rate
    
    return samples, sr


def _resample_linear(audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
    if orig_sr == target_sr:
        return audio
    duration = audio.shape[0] / orig_sr
    target_len = int(duration * target_sr)
    if target_len <= 1:
        return audio
    x_old = np.linspace(0, duration, audio.shape[0], endpoint=False)
    x_new = np.linspace(0, duration, target_len, endpoint=False)
    return np.interp(x_new, x_old, audio).astype(np.float32)


def _trim_silence(audio: np.ndarray, sr: int) -> np.ndarray:
    frame_len = int(sr * FRAME_MS / 1000)
    if frame_len <= 0 or audio.size == 0:
        return audio

    frames = []
    for i in range(0, len(audio), frame_len):
        chunk = audio[i : i + frame_len]
        if chunk.size == 0:
            continue
        rms = float(np.sqrt(np.mean(np.square(chunk))))
        frames.append(rms > ENERGY_THRESHOLD)

    if not any(frames):
        return audio

    start_idx = next(i for i, v in enumerate(frames) if v)
    end_idx = len(frames) - 1 - next(i for i, v in enumerate(reversed(frames)) if v)
    start = start_idx * frame_len
    end = min(len(audio), (end_idx + 1) * frame_len)
    return audio[start:end]


st.set_page_config(page_title="Smart Speaker", page_icon="🎤")

st.markdown(
    """
<style>
:root {
  --bg: #f6f4f1;
  --panel: #ffffff;
  --ink: #1f2328;
  --muted: #6b7280;
  --bubble-user: #f1f1f1;
  --bubble-bot: #ffffff;
}
.stApp { background: var(--bg); }
header { visibility: hidden; }
.block-container { padding-top: 1.1rem; max-width: 720px; }
.topbar {
  display: flex; align-items: center; justify-content: space-between;
  font-size: 1.2rem; color: var(--ink); margin-bottom: 1rem;
}
.topbar .title { font-weight: 600; letter-spacing: -0.02em; }
.status { color: var(--muted); font-size: 0.92rem; margin: 0.2rem 0 0.8rem; }
.chat { display: flex; flex-direction: column; gap: 0.9rem; padding-bottom: 6rem; }
.msg { display: flex; align-items: flex-end; gap: 0.6rem; }
.msg.user { justify-content: flex-end; }
.bubble {
  max-width: 82%; padding: 0.7rem 0.9rem; border-radius: 18px;
  line-height: 1.4; font-size: 1rem; background: var(--bubble-bot);
  box-shadow: 0 1px 0 rgba(16, 24, 40, 0.04);
}
.user .bubble { background: var(--bubble-user); }
.actions { display: flex; gap: 0.8rem; color: var(--muted); font-size: 0.9rem; margin-top: 0.35rem; }
.audio { margin-top: 0.6rem; }
.composer {
  position: fixed; left: 0; right: 0; bottom: 0;
  padding: 0.8rem 1rem 1.2rem;
  background: linear-gradient(180deg, rgba(246,244,241,0) 0%, rgba(246,244,241,0.9) 30%, rgba(246,244,241,1) 100%);
}
.composer-inner {
  max-width: 720px; margin: 0 auto; display: grid;
  grid-template-columns: 52px 1fr; align-items: center; gap: 0.75rem;
}
.circle-btn {
  width: 44px; height: 44px; border-radius: 50%;
  background: var(--panel); border: 1px solid #e5e7eb;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.2rem; color: var(--ink);
}
.pill {
  height: 48px; border-radius: 999px; background: var(--panel);
  border: 1px solid #e5e7eb; display: flex; align-items: center;
  padding: 0 1rem; color: var(--muted); font-size: 1rem;
}
/* mic recorder component -> bottom-right floating */
div[data-testid="stComponent"] iframe {
  position: fixed; right: 24px; bottom: 24px;
  width: 64px; height: 64px; border-radius: 50%;
  border: none; background: #111827;
  box-shadow: 0 12px 30px rgba(0,0,0,0.18);
  z-index: 1001;
}
div[data-testid="stComponent"] {
  height: 0; margin: 0; padding: 0;
}
</style>
<div class="topbar">
  <div class="title">ChatGPT</div>
  <div>⋯</div>
</div>
""",
    unsafe_allow_html=True,
)

if mic_recorder is None:
    st.error(
        "streamlit-mic-recorder가 필요합니다. 설치 후 다시 실행해 주세요.\n"
        "pip install streamlit-mic-recorder"
    )
    if _MIC_IMPORT_ERROR:
        st.caption(f"Import error: {_MIC_IMPORT_ERROR}")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_audio_hash" not in st.session_state:
    st.session_state.last_audio_hash = None

status_box = st.empty()

st.markdown('<div class="chat">', unsafe_allow_html=True)
for message in st.session_state.messages:
    role = message["role"]
    bubble_class = "msg user" if role == "user" else "msg bot"
    st.markdown(
        f'<div class="{bubble_class}"><div class="bubble">{message["content"]}</div></div>',
        unsafe_allow_html=True,
    )
    if role == "assistant":
        st.markdown('<div class="actions">👍 👎 🔊 ↗︎</div>', unsafe_allow_html=True)
    if message.get("audio"):
        st.markdown('<div class="audio">', unsafe_allow_html=True)
        st.audio(message["audio"])
        st.markdown("</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

audio = mic_recorder(start_prompt=" ", stop_prompt=" ", key="mic_recorder")

if isinstance(audio, dict) and audio.get("recording"):
    status_box.markdown(
        '<div class="status">녹음 중... 중지하면 처리합니다.</div>',
        unsafe_allow_html=True,
    )
else:
    status_box.markdown(
        '<div class="status">대기 중... 녹음을 시작해 주세요.</div>',
        unsafe_allow_html=True,
    )

if audio and "bytes" in audio:
    audio_hash = hash(audio["bytes"])
    if audio_hash != st.session_state.last_audio_hash:
        st.session_state.last_audio_hash = audio_hash

        with st.spinner("음성 처리 중..."):
            raw_audio, sr = _load_audio_bytes(audio["bytes"])
            raw_audio = _resample_linear(raw_audio, sr, SAMPLE_RATE)
            trimmed = _trim_silence(raw_audio, SAMPLE_RATE)

        if len(trimmed) > 0:
            wav_path = "web_utterance.wav"
            sf.write(wav_path, trimmed, SAMPLE_RATE)

            with st.spinner("음성을 텍스트로 변환 중..."):
                user_text = transcribe_wav(wav_path, language="ko").strip()

            if user_text:
                st.session_state.messages.append(
                    {"role": "user", "content": user_text}
                )
                with st.spinner("답변 생성 중..."):
                    reply = generate_response(user_text)
                    mp3_path = tts_to_mp3(
                        reply, out_path="assistant_reply.mp3", lang="ko"
                    )

                st.session_state.messages.append(
                    {"role": "assistant", "content": reply, "audio": mp3_path}
                )
                st.rerun()
            else:
                st.warning("음성을 인식하지 못했습니다. 다시 시도해 주세요.")

st.markdown(
    """
<div class="composer">
  <div class="composer-inner">
    <div class="circle-btn">＋</div>
    <div class="pill">무엇이든 부탁하세요</div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# python -m streamlit run streamlit_app.py