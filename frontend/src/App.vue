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
          {{ isGeneratingVoice ? 'Génération en cours...' : 'Générer la Voix' }}
        </button>

        <!-- Progress Bar -->
        <div v-if="isGeneratingVoice" class="w-full">
          <div class="w-full bg-gray-200 rounded-full h-2.5">
            <div 
              class="bg-purple-600 h-2.5 rounded-full transition-all duration-300 ease-out"
              :style="{ width: `${generationProgress}%` }"
            ></div>
          </div>
          <p class="text-sm text-gray-600 mt-1">{{ generationStatus }}</p>
        </div>

        <button 
          @click="shareOnWhatsApp"
          class="w-full bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 flex items-center justify-center gap-2"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12.031 6.172c-3.181 0-5.767 2.586-5.768 5.766-.001 1.298.38 2.27 1.019 3.287l-.582 2.128 2.182-.573c.978.58 1.911.928 3.145.929 3.178 0 5.767-2.587 5.768-5.766.001-3.187-2.575-5.771-5.764-5.771zm3.392 8.244c-.144.405-.837.774-1.17.824-.299.045-.677.063-1.092-.069-.252-.08-.575-.187-.988-.365-1.739-.751-2.874-2.502-2.961-2.617-.087-.116-.708-.94-.708-1.793s.448-1.273.607-1.446c.159-.173.346-.217.462-.217l.332.006c.106.005.249-.04.39.298.144.347.491 1.2.534 1.287.043.087.072.188.014.304-.058.116-.087.188-.173.289l-.26.304c-.087.086-.177.18-.076.354.101.174.449.741.964 1.201.662.591 1.221.774 1.394.86s.274.072.376-.043c.101-.116.433-.506.549-.68.116-.173.231-.145.39-.087s1.011.477 1.184.564.289.13.332.202c.045.072.045.419-.1.824z"/>
          </svg>
          Share on WhatsApp
        </button>

        <div class="space-y-2">
          <label class="block text-sm font-medium text-gray-700">
            Ajouter des images (optionnel)
          </label>
          <div class="space-y-4">
            <div class="flex items-center space-x-4">
              <input
                type="file"
                accept="image/*"
                @change="handleImageUpload"
                :disabled="isUploadingImage"
                class="hidden"
                ref="imageInput"
                multiple
              />
              <button
                @click="$refs.imageInput.click()"
                :disabled="isUploadingImage"
                class="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:bg-gray-400"
              >
                {{ isUploadingImage ? 'Téléchargement...' : 'Choisir des images' }}
              </button>
            </div>
            
            <!-- Image Previews Grid -->
            <div v-if="uploadedImages.length > 0" class="grid grid-cols-4 gap-4">
              <div v-for="(image, index) in uploadedImages" 
                :key="index" 
                class="relative w-20 h-20"
              >
                <img
                  :src="image.url"
                  class="w-full h-full object-cover rounded-lg"
                  alt="Preview"
                />
                <button
                  @click="removeImage(index)"
                  class="absolute -top-2 -right-2 bg-red-500 text-white rounded-full p-1 hover:bg-red-600"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>

        <button 
          @click="shareOnWhatsAppWithImage"
          :disabled="!uploadedImages.length || isUploadingImage" 
          class="w-full bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 flex items-center justify-center gap-2"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12.031 6.172c-3.181 0-5.767 2.586-5.768 5.766-.001 1.298.38 2.27 1.019 3.287l-.582 2.128 2.182-.573c.978.58 1.911.928 3.145.929 3.178 0 5.767-2.587 5.768-5.766.001-3.187-2.575-5.771-5.764-5.771zm3.392 8.244c-.144.405-.837.774-1.17.824-.299.045-.677.063-1.092-.069-.252-.08-.575-.187-.988-.365-1.739-.751-2.874-2.502-2.961-2.617-.087-.116-.708-.94-.708-1.793s.448-1.273.607-1.446c.159-.173.346-.217.462-.217l.332.006c.106.005.249-.04.39.298.144.347.491 1.2.534 1.287.043.087.072.188.014.304-.058.116-.087.188-.173.289l-.26.304c-.087.086-.177.18-.076.354.101.174.449.741.964 1.201.662.591 1.221.774 1.394.86s.274.072.376-.043c.101-.116.433-.506.549-.68.116-.173.231-.145.39-.087s1.011.477 1.184.564.289.13.332.202c.045.072.045.419-.1.824z"/>
          </svg>
          Share on WhatsApp with Image
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
const uploadedImages = ref([])
const isUploadingImage = ref(false)
const imageInput = ref(null)
const generationProgress = ref(0)
const generationStatus = ref('')

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
  generationProgress.value = 0
  generationStatus.value = 'Initialisation...'
  
  try {
    // Start request
    generationProgress.value = 10
    generationStatus.value = 'Envoi de la requête...'
    
    const response = await fetch('http://localhost:8000/api/text-to-speech', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text: generatedMessage.value,
        voice_id: "Fo36sCvJyueYOBE0TqjC", // CousineDjassaPro voice
        optimize_streaming_latency: 0
      })
    })

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.detail || 'Erreur lors de la génération de la voix')
    }

    // Simulate progress for each step
    generationProgress.value = 30
    generationStatus.value = 'Validation de la voix...'
    await new Promise(resolve => setTimeout(resolve, 500))
    
    generationProgress.value = 50
    generationStatus.value = 'Génération de la voix...'
    await new Promise(resolve => setTimeout(resolve, 500))
    
    generationProgress.value = 70
    generationStatus.value = 'Sauvegarde du fichier...'
    await new Promise(resolve => setTimeout(resolve, 500))
    
    generationProgress.value = 90
    generationStatus.value = 'Préparation de l\'audio...'
    
    const data = await response.json()
    console.log('Voice generation response:', data)
    
    generatedVoiceUrl.value = {
      streaming_url: `http://localhost:8000${data.streaming_url}`,
      sharing_url: data.sharing_url
    }
    
    generationProgress.value = 100
    generationStatus.value = 'Terminé!'
    
  } catch (error) {
    console.error('Error generating voice:', error)
    generationStatus.value = 'Erreur: ' + error.message
    alert(error.message)
  } finally {
    // Reset progress after completion or error
    setTimeout(() => {
      if (generationProgress.value === 100) {
        isGeneratingVoice.value = false
        generationProgress.value = 0
        generationStatus.value = ''
      }
    }, 1000)
  }
}

const handleImageUpload = async (event) => {
  const files = Array.from(event.target.files)
  if (!files.length) return
  
  isUploadingImage.value = true
  
  try {
    for (const file of files) {
      const formData = new FormData()
      formData.append('file', file)
      
      const response = await fetch('http://localhost:8000/api/upload-image', {
        method: 'POST',
        body: formData
      })
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Erreur lors du téléchargement')
      }
      
      const data = await response.json()
      uploadedImages.value.push({
        url: data.url,
        filename: data.filename
      })
    }
    
  } catch (error) {
    console.error('Error uploading image:', error)
    alert(error.message)
  } finally {
    isUploadingImage.value = false
    // Reset input to allow uploading the same file again
    if (imageInput.value) {
      imageInput.value.value = ''
    }
  }
}

const removeImage = (index) => {
  uploadedImages.value.splice(index, 1)
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

const shareOnWhatsAppWithImage = async () => {
  console.log('Share button clicked!');
  
  try {
    let messageLines = []
    
    // Start with only the first image URL - no formatting, just raw URL
    if (uploadedImages.value.length > 0) {
      messageLines = [uploadedImages.value[0].url]
      
      // Add blank lines to separate content
      messageLines.push('', '', '')
    }
    
    // Add the main content
    messageLines.push(
      "📢 Message Publicitaire",
      "",
      generatedMessage.value
    )
    
    // Add audio if available
    if (generatedVoiceUrl.value?.sharing_url) {
      messageLines.push(
        "",
        "🎵 Message Audio:",
        generatedVoiceUrl.value.sharing_url
      )
    }
    
    // Add remaining images if there are any
    if (uploadedImages.value.length > 1) {
      messageLines.push(
        "",
        "📸 Autres Images:"
      )
      uploadedImages.value.slice(1).forEach((image, index) => {
        messageLines.push(`${index + 2}. ${image.url}`)
      })
    }
    
    // Add signature at the end
    messageLines.push("", "📱 Généré par Djassapro")
    
    // Join with newlines and remove any double spaces
    const fullMessage = messageLines.join('\n').replace(/\n\n\n+/g, '\n\n')
    
    // Basic URL encoding
    const encodedText = encodeURIComponent(fullMessage)
    
    // Create WhatsApp link
    const waLink = `https://api.whatsapp.com/send?text=${encodedText}`
    
    // Open in new tab
    window.open(waLink, '_blank')
  } catch (error) {
    console.error('Error:', error)
    alert('Une erreur est survenue lors du partage sur WhatsApp. Veuillez réessayer.')
  }
}
</script>
