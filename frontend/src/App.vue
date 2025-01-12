<template>
  <div class="container mx-auto p-4">
    <h1 class="text-3xl font-bold mb-8 text-center text-gray-800">Djassapro Ad Generator</h1>

    <!-- Voice Recorder Component -->
    <div class="bg-white rounded-lg shadow-md p-6 mb-6">
      <h2 class="text-xl font-semibold mb-4 text-gray-700">Record Your Message</h2>
      <VoiceRecorder @recording-complete="handleRecordingComplete" />

      <button 
        @click="submitRecording" 
        :disabled="!recordingBlob || isSubmitting"
        class="mt-4 w-full bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
      >
        {{ isSubmitting ? 'Processing...' : 'Submit Recording' }}
      </button>
    </div>

    <!-- Transcription Display -->
    <div v-if="transcription" class="bg-white rounded-lg shadow-md p-6 mb-6">
      <h2 class="text-xl font-semibold mb-4 text-gray-700">Transcription</h2>
      <p class="text-gray-600">{{ transcription }}</p>
      <button 
        @click="generateAdMessage" 
        class="mt-4 w-full bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700"
      >
        Generate Ad Message
      </button>
    </div>

    <!-- Generated Message Display -->
    <div v-if="generatedMessage" class="bg-white rounded-lg shadow-md p-6 mb-6">
      <h2 class="text-xl font-semibold mb-4 text-gray-700">Generated Ad Message</h2>
      <p class="text-gray-600 whitespace-pre-line">{{ generatedMessage }}</p>
      
      <div class="mt-4 space-y-4">
        <button 
          @click="generateVoice"
          :disabled="isGeneratingVoice" 
          class="w-full bg-purple-600 text-white px-6 py-2 rounded-lg hover:bg-purple-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          {{ isGeneratingVoice ? 'Generating Voice...' : 'Generate Voice' }}
        </button>

        <button 
          @click="shareOnWhatsApp"
          class="w-full bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 flex items-center justify-center gap-2"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12.031 6.172c-3.181 0-5.767 2.586-5.768 5.766-.001 1.298.38 2.27 1.019 3.287l-.582 2.128 2.182-.573c.978.58 1.911.928 3.145.929 3.178 0 5.767-2.587 5.768-5.766.001-3.187-2.575-5.771-5.764-5.771zm3.392 8.244c-.144.405-.837.774-1.17.824-.299.045-.677.063-1.092-.069-.252-.08-.575-.187-.988-.365-1.739-.751-2.874-2.502-2.961-2.617-.087-.116-.708-.94-.708-1.793s.448-1.273.607-1.446c.159-.173.346-.217.462-.217l.332.006c.106.005.249-.04.39.298.144.347.491 1.2.534 1.287.043.087.072.188.014.304-.058.116-.087.188-.173.289l-.26.304c-.087.086-.177.18-.076.354.101.174.449.741.964 1.201.662.591 1.221.774 1.394.86s.274.072.376-.043c.101-.116.433-.506.549-.68.116-.173.231-.145.39-.087s1.011.477 1.184.564.289.13.332.202c.045.072.045.419-.1.824z"/>
          </svg>
          Share on WhatsApp
        </button>
      </div>
    </div>

    <!-- Generated Voice Display -->
    <div v-if="generatedVoiceUrl" class="bg-white rounded-lg shadow-md p-6">
      <h2 class="text-xl font-semibold mb-4 text-gray-700">Generated Voice</h2>
      <audio ref="audioPlayer" :src="generatedVoiceUrl.streaming_url" controls class="w-full mb-4"></audio>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import VoiceRecorder from './components/VoiceRecorder.vue'

const recordingBlob = ref(null)
const audioUrl = ref(null)
const transcription = ref('')
const generatedMessage = ref('')
const generatedVoiceUrl = ref(null)
const isSubmitting = ref(false)
const isGeneratingVoice = ref(false)
const audioPlayer = ref(null)
const generatedVoiceBlob = ref(null)
const audioElement = ref(null)

const handleRecordingComplete = (blob) => {
  console.log('Recording complete, blob size:', blob.size)
  recordingBlob.value = blob
  if (audioUrl.value) {
    URL.revokeObjectURL(audioUrl.value)
  }
  audioUrl.value = URL.createObjectURL(blob)
}

const submitRecording = async () => {
  if (!recordingBlob.value) {
    alert('Please record a message first')
    return
  }

  isSubmitting.value = true
  const formData = new FormData()
  formData.append('audio', recordingBlob.value, 'recording.webm')

  try {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 30000) // 30 second timeout

    const response = await fetch('http://localhost:8000/api/transcribe', {
      method: 'POST',
      body: formData,
      signal: controller.signal
    })

    clearTimeout(timeoutId)

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const data = await response.json()
    transcription.value = data.text
  } catch (error) {
    console.error('Error:', error)
    alert('Error submitting recording. Please try again.')
  } finally {
    isSubmitting.value = false
  }
}

const generateAdMessage = async () => {
  try {
    const response = await fetch('http://localhost:8000/api/generate-message', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text: transcription.value,
        tone: 'friendly'
      })
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const data = await response.json()
    generatedMessage.value = data.message
  } catch (error) {
    console.error('Error:', error)
    alert('Error generating message. Please try again.')
  }
}

const generateVoice = async () => {
  if (!generatedMessage.value) return
  
  isGeneratingVoice.value = true
  try {
    const response = await fetch('http://localhost:8000/api/text-to-speech', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text: generatedMessage.value
      })
    })

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.detail || 'Error generating voice')
    }

    const data = await response.json()
    console.log('Voice generation response:', data)
    
    // Store both streaming and sharing URLs
    generatedVoiceUrl.value = {
      streaming_url: `http://localhost:8000${data.streaming_url}`,
      sharing_url: data.sharing_url
    }
    
    // Create audio element for playback
    if (!audioElement.value) {
      audioElement.value = new Audio()
    }
    audioElement.value.src = generatedVoiceUrl.value.streaming_url
    
  } catch (error) {
    console.error('Error generating voice:', error)
    alert(error.message)
  } finally {
    isGeneratingVoice.value = false
  }
}

const shareOnWhatsApp = async () => {
  console.log('Share button clicked!');
  
  try {
    // Format message with header, audio link, and footer
    const messageLines = [
      "📢 Message Publicitaire",
      "",
      generatedMessage.value,
      "",
      // Only include audio section if we have a sharing URL
      ...(generatedVoiceUrl.value?.sharing_url ? [
        "🎵 Message Audio:",
        generatedVoiceUrl.value.sharing_url,
        ""
      ] : []),
      "📱 Généré par Djassapro"
    ].filter(line => line !== "");

    const fullMessage = messageLines.join('\n');
    console.log('Full message:', fullMessage);

    // Basic URL encoding
    const encodedText = encodeURIComponent(fullMessage);
    console.log('Encoded text:', encodedText);

    // Create WhatsApp link
    const waLink = `https://api.whatsapp.com/send?text=${encodedText}`;
    console.log('WhatsApp link:', waLink);
    
    // Open in new tab
    window.open(waLink, '_blank');
  } catch (error) {
    console.error('Error:', error);
    alert('Une erreur est survenue lors du partage sur WhatsApp. Veuillez réessayer.');
  }
}
</script>
