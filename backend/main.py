from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import uvicorn
import os
from tempfile import NamedTemporaryFile
from dotenv import load_dotenv
import asyncio
from pathlib import Path
import json
import subprocess
from google.cloud import storage
import vertexai
from vertexai import generative_models
from vertexai.language_models import TextGenerationModel
import requests
import uuid
import aiofiles
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get Google Cloud project settings
PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT')
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')

if not PROJECT_ID:
    raise ValueError("GOOGLE_CLOUD_PROJECT not found in environment variables")
if not ELEVENLABS_API_KEY:
    raise ValueError("ELEVENLABS_API_KEY not found in environment variables")

# Initialize Vertex AI
vertexai.init(project=PROJECT_ID, location="us-central1")

# Initialize Eleven Labs API
ELEVEN_LABS_API_URL = "https://api.elevenlabs.io/v1"
HEADERS = {
    "Accept": "application/json",
    "xi-api-key": ELEVENLABS_API_KEY
}

# Initialize Storage client
storage_client = storage.Client()

# Create or get bucket for temporary audio storage
BUCKET_NAME = "djassapro-audio-temp"
try:
    bucket = storage_client.get_bucket(BUCKET_NAME)
except Exception as e:
    print(f"Error accessing bucket: {str(e)}")
    print("Please make sure the bucket exists and the service account has access to it")
    # Instead of failing, we'll create a local temp directory for audio files
    temp_dir = Path("temp")
    temp_dir.mkdir(exist_ok=True)

app = FastAPI(title="Djassapro MVP API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MessageRequest(BaseModel):
    text: str
    tone: Optional[str] = "friendly"
    voice_id: Optional[str] = "Fo36sCvJyueYOBE0TqjC"  # Default French voice

class TTSRequest(BaseModel):
    text: str
    voice_id: Optional[str] = "Fo36sCvJyueYOBE0TqjC"  # Cousine Djassapro voice
    optimize_streaming_latency: Optional[int] = 0
    model_id: Optional[str] = "eleven_multilingual_v2"

def convert_to_wav(input_path: str, output_path: str) -> bool:
    """Convert audio file to WAV format using ffmpeg."""
    try:
        command = [
            'ffmpeg',
            '-i', input_path,
            '-acodec', 'pcm_s16le',
            '-ac', '1',
            '-ar', '16000',
            '-y',
            output_path
        ]
        
        logger.info(f"Running FFmpeg command: {' '.join(command)}")
        
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        if result.returncode != 0:
            logger.error(f"FFmpeg error: {result.stderr.decode()}")
            return False
            
        return True
    except Exception as e:
        logger.error(f"Error in audio conversion: {str(e)}")
        return False

async def upload_to_gcs(file_path: str, content_type: str) -> str:
    """Upload file to Google Cloud Storage and return public URL."""
    try:
        if not hasattr(storage_client, 'bucket'):
            # If no bucket access, return local file path
            return f"file://{file_path}"
            
        file_name = f"audio-{uuid.uuid4()}{Path(file_path).suffix}"
        blob = bucket.blob(file_name)
        
        # Upload the file
        blob.upload_from_filename(file_path, content_type=content_type)
        
        # Make the blob publicly readable
        blob.make_public()
        
        return f"gs://{BUCKET_NAME}/{file_name}"
    except Exception as e:
        logger.error(f"Error uploading to GCS: {str(e)}")
        # Return local file path as fallback
        return f"file://{file_path}"

async def delete_from_gcs(gcs_uri: str):
    """Delete file from Google Cloud Storage."""
    try:
        if not gcs_uri.startswith("gs://"):
            # Local file, just remove it
            local_path = gcs_uri.replace("file://", "")
            if os.path.exists(local_path):
                os.remove(local_path)
            return
            
        file_name = gcs_uri.split('/')[-1]
        blob = bucket.blob(file_name)
        blob.delete()
    except Exception as e:
        logger.error(f"Error deleting from GCS: {str(e)}")

async def transcribe_with_gemini(file_uri: str) -> dict:
    """Transcribe audio using Gemini Flash 2.0."""
    try:
        # Initialize Gemini Flash 2.0 model
        model = generative_models.GenerativeModel("gemini-2.0-flash-exp")
        
        # Create prompt for better French transcription
        prompt = generative_models.Part.from_text("""
        Transcrivez cet audio en français avec précision.
        Instructions spécifiques:
        - Conservez les expressions locales ivoiriennes
        - Gardez la ponctuation naturelle
        - Respectez le contexte culturel ivoirien
        - Assurez une transcription fidèle au langage parlé
        """)
        
        # If using local file, read it directly
        if file_uri.startswith("file://"):
            file_path = file_uri[7:]  # Remove "file://" prefix
            with open(file_path, "rb") as f:
                audio_data = f.read()
            audio_part = generative_models.Part.from_data(data=audio_data, mime_type="audio/wav")
        else:
            # For GCS files, use URI directly
            audio_part = generative_models.Part.from_uri(uri=file_uri, mime_type="audio/wav")
        
        # Generate response with audio understanding
        response = model.generate_content(
            [prompt, audio_part],
            generation_config={
                "max_output_tokens": 2048,
                "temperature": 0.1,
                "top_p": 0.8,
                "top_k": 40
            }
        )
        
        # Extract the transcription
        transcription = response.text.strip()
        
        return {
            "text": transcription,
            "confidence": 0.95,  # Gemini doesn't provide confidence scores
            "language_code": "fr-FR"
        }
        
    except Exception as e:
        logger.error(f"Error in Gemini transcription: {str(e)}")
        raise

async def generate_voice(text: str, voice_id: str = "Fo36sCvJyueYOBE0TqjC", optimize_streaming_latency: int = 0) -> bytes:
    """Generate voice using Eleven Labs."""
    try:
        # Get available voices
        response = requests.get(f"{ELEVEN_LABS_API_URL}/voices", headers=HEADERS)
        voices = response.json()["voices"]  # The voices are in a "voices" key
        selected_voice = next((v for v in voices if v["voice_id"] == voice_id), None)
        
        if not selected_voice:
            raise ValueError(f"Voice {voice_id} not found")
            
        # Create voice settings
        voice_settings = {
            "stability": 0.60,
            "similarity_boost": 0.75,
            "style": 0.9,
            "use_speaker_boost": True
        }
        
        # Generate audio
        response = requests.post(
            f"{ELEVEN_LABS_API_URL}/text-to-speech/{voice_id}",  # Add voice_id to URL
            headers={**HEADERS, "Content-Type": "application/json"},  # Add Content-Type
            json={
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": voice_settings
            }
        )
        
        if response.status_code != 200:
            raise ValueError(f"Error from Eleven Labs API: {response.text}")
            
        return response.content
        
    except Exception as e:
        logger.error(f"Error in voice generation: {str(e)}")
        raise

@app.get("/")
async def read_root():
    return {"status": "ok", "message": "Djassapro MVP API is running"}

@app.get("/api/voices")
async def list_voices():
    """List available voices."""
    # Since we're using a fixed voice, just return that one
    return {
        "voices": [{
            "voice_id": "Fo36sCvJyueYOBE0TqjC",
            "name": "Cousine Djassapro",
            "category": "custom"
        }]
    }

@app.post("/api/transcribe")
async def transcribe_audio(audio: UploadFile = File(...)):
    """Transcribe audio using Gemini."""
    try:
        # Print audio file info for debugging
        logger.info(f"Audio content type: {audio.content_type}")
        content = await audio.read()
        logger.info(f"Audio content length: {len(content)} bytes")
        
        # Create temp directory if it doesn't exist
        temp_dir = Path("temp")
        temp_dir.mkdir(exist_ok=True)
        
        # Save uploaded file
        input_path = temp_dir / f"input_{audio.filename}"
        output_path = temp_dir / f"{audio.filename}.wav"
        
        async with aiofiles.open(input_path, 'wb') as f:
            await f.write(content)
            
        # Convert to WAV using FFmpeg
        ffmpeg_cmd = f"ffmpeg -i {input_path} -acodec pcm_s16le -ac 1 -ar 16000 -y {output_path}"
        logger.info(f"Running FFmpeg command: {ffmpeg_cmd}")
        subprocess.run(ffmpeg_cmd.split(), check=True)
        
        # Upload to GCS
        gcs_uri = await upload_to_gcs(str(output_path), "audio/wav")
        logger.info(f"Uploaded audio to: {gcs_uri}")
        
        # Transcribe using Gemini
        try:
            result = await transcribe_with_gemini(gcs_uri)
            logger.info(f"Transcription result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error in transcription: {str(e)}")
            raise
            
    except Exception as e:
        logger.error(f"Error processing audio: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing audio: {str(e)}"
        )
    finally:
        # Cleanup temporary files
        try:
            if input_path.exists():
                input_path.unlink()
            if output_path.exists():
                output_path.unlink()
        except Exception as e:
            logger.error(f"Error cleaning up temp files: {str(e)}")

@app.post("/api/text-to-speech")
async def text_to_speech(request: TTSRequest):
    """Convert text to speech using Eleven Labs."""
    try:
        # Validate voice exists
        response = requests.get(f"{ELEVEN_LABS_API_URL}/voices", headers=HEADERS)
        voices = response.json().get("voices", [])
        voice_exists = any(voice["voice_id"] == request.voice_id for voice in voices)
        
        if not voice_exists:
            available_voices = ", ".join(f"{v['name']} ({v['voice_id']})" for v in voices)
            raise HTTPException(
                status_code=400,
                detail=f"Voice {request.voice_id} not found. Available voices: {available_voices}"
            )
        
        # Generate voice
        audio_content = await generate_voice(
            text=request.text,
            voice_id=request.voice_id,
            optimize_streaming_latency=request.optimize_streaming_latency
        )
        
        # Create temporary file
        temp_dir = Path("temp")
        temp_dir.mkdir(exist_ok=True)
        
        output_path = temp_dir / f"tts_{uuid.uuid4()}.mp3"
        
        # Save audio content
        async with aiofiles.open(output_path, 'wb') as f:
            await f.write(audio_content)
        
        # Return audio file
        return FileResponse(
            output_path,
            media_type="audio/mpeg",
            headers={"Content-Disposition": "attachment; filename=speech.mp3"}
        )
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error in text-to-speech: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-message")
async def generate_message(request: MessageRequest):
    """Generate ad message and optionally convert to speech."""
    try:
        # Initialize Gemini model for message generation
        #model = generative_models.GenerativeModel("gemini-1.0-pro")
        model = generative_models.GenerativeModel("gemini-2.0-flash-exp")
        
        # Create prompt for ad message generation
        prompt = f"""
        Générez un message publicitaire bref , et engageant en français professionnel à partir du texte suivant:
        "{request.text}"

        Instructions:
        - Ne générer que le message publicitaire. Sans aucun autre texte de description
        - Utilisez un style approprié
        - Ton: {request.tone}
        - de 5 à 10 phases maximum
        - Tutoyer amicalement mais respectueusement
        - Utilisez des émojis appropriés
        - Incluez un appel à l'action
        - le message doit etre inspurant et pousser à l'action 
        - le message concis et impactant
        - Mettez en valeur les points clés
        """
        
        try:
            # Generate the message
            response = model.generate_content(
                prompt,
                generation_config=generative_models.GenerationConfig(
                    max_output_tokens=1024,
                    temperature=0.7,
                    top_p=0.8,
                    top_k=40
                )
            )
            
            if not response or not response.text:
                raise ValueError("No response generated from Gemini")
                
            generated_message = response.text.strip()
            
            return {
                "message": generated_message,
                "audio_url": None
            }
            
        except Exception as model_error:
            logger.error(f"Text generation error: {str(model_error)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error generating message: {str(model_error)}"
            )
        
    except Exception as e:
        logger.error(f"Error in generate_message: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating message: {str(e)}"
        )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
