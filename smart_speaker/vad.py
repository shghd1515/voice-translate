import time
from typing import Optional

import numpy as np
import sounddevice as sd
import soundfile as sf
import torch


def record_vad_to_wav(
    out_path: str = "vad_recorded.wav",
    record_seconds: int = 10,
    sampling_rate: int = 16000,
    block_size: int = 512,
    device: Optional[int] = None,
    verbose: bool = True,
) -> str:
    model, utils = torch.hub.load(
        repo_or_dir="snakers4/silero-vad",
        model="silero_vad",
    )
    (_, _, _, VADIterator, _) = utils
    vad_iterator = VADIterator(model)

    speech_buffer = []
    is_speaking = False

    if verbose:
        print("🎤 녹음 시작")

    start_time = time.time()

    with sd.InputStream(
        samplerate=sampling_rate,
        channels=1,
        blocksize=block_size,
        device=device,
    ) as stream:
        while True:
            audio_chunk, _ = stream.read(block_size)
            audio_chunk = audio_chunk.flatten()

            audio_tensor = torch.from_numpy(audio_chunk)
            speech_dict = vad_iterator(audio_tensor)

            if speech_dict:
                if "start" in speech_dict:
                    is_speaking = True
                    if verbose:
                        print("speech start")
                if "end" in speech_dict:
                    is_speaking = False
                    if verbose:
                        print("speech end")

            if is_speaking:
                speech_buffer.extend(audio_chunk)

            if time.time() - start_time > record_seconds:
                break

    if verbose:
        print("녹음 종료")

    speech_audio = np.array(speech_buffer)
    sf.write(out_path, speech_audio, sampling_rate)

    if verbose:
        print("파일 저장 완료")

    return out_path


if __name__ == "__main__":
    record_vad_to_wav()
