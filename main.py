import os
import openai
import requests
from slugify import slugify
from TTS.api import TTS
import ffmpeg
from dotenv import load_dotenv

# Charger les clés API depuis .env
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PEXELS_KEY = os.getenv("PEXELS_KEY")

# Configurer OpenAI
openai.api_key = OPENAI_API_KEY

# Créer les dossiers nécessaires
for folder in ['scripts', 'audio', 'images', 'subs', 'video']:
    os.makedirs(f'output/{folder}', exist_ok=True)

# Lire les sujets depuis topics.txt
def read_topics():
    with open('topics.txt', 'r') as f:
        return [line.strip() for line in f if line.strip()]

# Générer un script avec OpenAI
def gen_script(title):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": f"Écris un script de 45 secondes sur : {title}"}]
    )
    return response.choices[0].message.content

# Générer un fichier audio avec TTS
def make_tts(text, output_file):
    tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC")
    tts.tts_to_file(text=text, file_path=output_file)

# Télécharger des images depuis l'API Pexels
def get_images(query, slug):
    url = "https://api.pexels.com/v1/search"
    headers = {"Authorization": PEXELS_KEY}
    params = {"query": query, "per_page": 3}
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    for i, photo in enumerate(data.get("photos", [])):
        img_url = photo["src"]["landscape"]
        img_data = requests.get(img_url).content
        with open(f'output/images/{slug}_{i}.jpg', 'wb') as f:
            f.write(img_data)

# Assembler une vidéo avec FFmpeg
def create_video(slug):
    images = [f'output/images/{slug}_{i}.jpg' for i in range(3)]
    audio = f'output/audio/{slug}.wav'
    video = f'output/video/{slug}.mp4'

    # Créer une vidéo à partir des images et de l'audio
    input_images = ffmpeg.input('concat:' + '|'.join(images), framerate=1)
    input_audio = ffmpeg.input(audio)
    ffmpeg.output(input_images, input_audio, video, vcodec='libx264', acodec='aac', strict='experimental').run()

# Pipeline principal
def main():
    topics = read_topics()
    for topic in topics:
        slug = slugify(topic)
        print(f"Traitement du sujet : {topic}")

        # Générer le script
        script = gen_script(topic)
        with open(f'output/scripts/{slug}.txt', 'w') as f:
            f.write(script)

        # Générer l'audio
        audio_file = f'output/audio/{slug}.wav'
        make_tts(script, audio_file)

        # Télécharger les images
        get_images(topic, slug)

        # Créer la vidéo
        create_video(slug)

        print(f"Vidéo générée pour : {topic}")

if __name__ == "__main__":
    main()