
from flask import Flask, request, send_file, render_template
import os, subprocess, uuid, requests

app = Flask(__name__)
BASE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(BASE, "assets")
OUTPUT = os.path.join(BASE, "output")
os.makedirs(OUTPUT, exist_ok=True)

ELEVEN_API_KEY = os.getenv("ELEVENLABS_API_KEY")

def ensure_assets():
    # Generate placeholder gameplay + tone audio if missing (no copyright)
    gameplay = os.path.join(ASSETS, "gameplay.mp4")
    music = os.path.join(ASSETS, "music.mp3")
    if not os.path.exists(gameplay):
        subprocess.run([
            "ffmpeg","-y","-f","lavfi","-i","color=c=black:s=1080x1920:d=10",
            "-vf","drawtext=text='ViralGen':fontcolor=white:fontsize=72:x=(w-text_w)/2:y=(h-text_h)/2",
            gameplay
        ], check=True)
    if not os.path.exists(music):
        subprocess.run([
            "ffmpeg","-y","-f","lavfi","-i","sine=frequency=440:duration=10",
            "-c:a","mp3", music
        ], check=True)

def eleven_tts(text, out_mp3):
    if not ELEVEN_API_KEY:
        # fallback local tone
        subprocess.run(["ffmpeg","-y","-f","lavfi","-i","sine=frequency=660:duration=8","-c:a","mp3", out_mp3], check=True)
        return
    url = "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM"
    headers = {"xi-api-key": ELEVEN_API_KEY, "Content-Type":"application/json","accept":"audio/mpeg"}
    payload = {"text": text, "model_id":"eleven_monolingual_v1","voice_settings":{"stability":0.5,"similarity_boost":0.7}}
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    with open(out_mp3,"wb") as f: f.write(r.content)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    ensure_assets()
    topic = request.form.get("topic","money motivation")
    uid = uuid.uuid4().hex[:8]
    voice = os.path.join(OUTPUT, f"voice_{uid}.mp3")
    base = os.path.join(OUTPUT, f"base_{uid}.mp4")
    out = os.path.join(OUTPUT, f"tiktok_{uid}.mp4")

    script = f"This sounds fake but it is real. {topic}. Stay focused. Follow for more."
    eleven_tts(script, voice)

    subprocess.run([
        "ffmpeg","-y","-stream_loop","-1","-i",os.path.join(ASSETS,"gameplay.mp4"),
        "-i",voice,"-t","10",
        "-vf","scale=1080:1920",
        "-c:v","libx264","-pix_fmt","yuv420p","-c:a","aac","-shortest", base
    ], check=True)

    subprocess.run(["ffmpeg","-y","-i",base,"-c","copy", out], check=True)
    return send_file(out, as_attachment=True, download_name="short_ready.mp4")

if __name__ == "__main__":
    app.run(port=5000)
