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
          class="w-full bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700"
        >
          Share on WhatsApp
        </button>
      </div>
    </div>

    <!-- Generated Voice Display -->
    <div v-if="generatedVoiceUrl" class="bg-white rounded-lg shadow-md p-6">
      <h2 class="text-xl font-semibold mb-4 text-gray-700">Generated Voice</h2>
      <audio :src="generatedVoiceUrl" controls class="w-full"></audio>
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

    const audioBlob = await response.blob()
    if (generatedVoiceUrl.value) {
      URL.revokeObjectURL(generatedVoiceUrl.value)
    }
    generatedVoiceUrl.value = URL.createObjectURL(audioBlob)
  } catch (error) {
    console.error('Error generating voice:', error)
    alert(error.message)
  } finally {
    isGeneratingVoice.value = false
  }
}

const shareOnWhatsApp = () => {
  const text = encodeURIComponent(generatedMessage.value)
  window.open(`https://wa.me/?text=${text}`, '_blank')
}
</script>
