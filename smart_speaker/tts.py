import shutil
import subprocess
from gtts import gTTS


def tts_to_mp3(text: str, out_path: str = "tts_output.mp3", lang: str = "ko") -> str:
    tts = gTTS(text=text, lang=lang)
    tts.save(out_path)
    return out_path


def play_audio(path: str) -> None:
    if shutil.which("afplay"):
        subprocess.run(["afplay", path], check=False)
        return
    if shutil.which("ffplay"):
        subprocess.run(["ffplay", "-nodisp", "-autoexit", path], check=False)
        return
    if shutil.which("mpg123"):
        subprocess.run(["mpg123", path], check=False)
        return
    print(f"재생 도구를 찾지 못했습니다: {path}")


if __name__ == "__main__":
    text_ko = "안녕하세요. 반갑습니다. hello"
    file_name = "sample2.mp3"
    tts_to_mp3(text_ko, out_path=file_name, lang="ko")
    play_audio(file_name)
