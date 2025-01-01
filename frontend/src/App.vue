<template>
  <div class="min-h-screen bg-gray-50">
    <header class="bg-white shadow-sm">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <h1 class="text-2xl font-bold text-gray-900">Djassapro</h1>
      </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="card">
        <div class="space-y-6">
          <!-- Voice Recording Section -->
          <div>
            <h2 class="text-xl font-semibold text-gray-900 mb-4">Record Your Message</h2>
            <div class="flex flex-col items-center space-y-4 p-6 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
              <VoiceRecorder ref="voiceRecorder" />
              <button 
                v-if="!isLoading && voiceRecorder?.audioUrl" 
                @click="submitRecording" 
                class="btn btn-secondary"
              >
                Submit Recording
              </button>
              <div v-if="isLoading" class="text-gray-600">
                Processing your recording...
              </div>
            </div>
          </div>

          <!-- Transcription Section -->
          <div v-if="transcription" class="animate-fade-in">
            <h2 class="text-xl font-semibold text-gray-900 mb-4">Transcription</h2>
            <div class="bg-gray-50 rounded-lg p-4">
              <p class="text-gray-700">{{ transcription }}</p>
              <div class="mt-4 flex justify-end">
                <button @click="generateMessage" class="btn btn-primary">
                  Generate Ad Message
                </button>
              </div>
            </div>
          </div>

          <!-- Generated Message Section -->
          <div v-if="generatedMessage" class="animate-fade-in">
            <h2 class="text-xl font-semibold text-gray-900 mb-4">Generated Ad Message</h2>
            <div class="bg-gray-50 rounded-lg p-4">
              <p class="text-gray-700 whitespace-pre-line">{{ generatedMessage }}</p>
              <div class="mt-4 flex justify-end space-x-4">
                <button @click="generateVoice" class="btn btn-primary" :disabled="isGeneratingVoice">
                  {{ isGeneratingVoice ? 'Generating Voice...' : 'Generate Voice' }}
                </button>
                <button class="btn btn-secondary">
                  Share on WhatsApp
                </button>
              </div>
            </div>
          </div>

          <!-- Voice Preview Section -->
          <div v-if="audioUrl" class="animate-fade-in">
            <h2 class="text-xl font-semibold text-gray-900 mb-4">Voice Preview</h2>
            <div class="bg-gray-50 rounded-lg p-4">
              <audio controls :src="audioUrl" class="w-full"></audio>
              <div class="mt-4">
                <label class="block text-sm font-medium text-gray-700 mb-2">Select Voice</label>
                <select 
                  v-model="selectedVoice" 
                  class="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                >
                  <option v-for="voice in voices" :key="voice.voice_id" :value="voice.voice_id">
                    {{ voice.name }} ({{ voice.category }})
                  </option>
                </select>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import VoiceRecorder from './components/VoiceRecorder.vue';

const voiceRecorder = ref(null);
const isLoading = ref(false);
const transcription = ref('');
const generatedMessage = ref('');
const audioUrl = ref('');
const isGeneratingVoice = ref(false);
const selectedVoice = ref('ohItIVrXTBI80RrUECOD'); // Guillaume voice by default
const voices = ref([]);

// Fetch available voices on component mount
onMounted(async () => {
  try {
    const response = await fetch('http://localhost:8000/api/voices');
    const data = await response.json();
    voices.value = data.voices;
  } catch (error) {
    console.error('Error fetching voices:', error);
  }
});

const API_BASE_URL = 'http://localhost:8000';

const submitRecording = async () => {
  if (!voiceRecorder.value) return;
  
  const audioBlob = voiceRecorder.value.getAudioBlob();
  if (!audioBlob) {
    alert('No recording available');
    return;
  }

  isLoading.value = true;
  try {
    // Create a new File object from the Blob
    const audioFile = new File([audioBlob], 'recording.webm', {
      type: 'audio/webm',
      lastModified: Date.now()
    });

    const formData = new FormData();
    formData.append('audio', audioFile);

    console.log('Sending audio file:', audioFile);
    
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout

    const response = await fetch(`${API_BASE_URL}/api/transcribe`, {
      method: 'POST',
      body: formData,
      signal: controller.signal,
      mode: 'cors',
      credentials: 'include'
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Server error:', errorText);
      throw new Error(`Server error: ${response.status}`);
    }

    const data = await response.json();
    console.log('Transcription response:', data);
    
    if (!data.text) {
      throw new Error('No transcription text received');
    }
    
    transcription.value = data.text;
  } catch (error) {
    console.error('Error submitting recording:', error);
    if (error.name === 'AbortError') {
      alert('Request timed out. Please try again.');
    } else if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
      alert('Network error: Please check your connection and try again');
    } else {
      alert(`Error: ${error.message}`);
    }
  } finally {
    isLoading.value = false;
  }
};

const generateMessage = async () => {
  if (!transcription.value) return;
  
  isLoading.value = true;
  try {
    const response = await fetch(`${API_BASE_URL}/api/generate-message`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text: transcription.value,
        tone: 'friendly'
      }),
    });
    
    const data = await response.json();
    generatedMessage.value = data.message;
  } catch (error) {
    console.error('Error generating message:', error);
    alert('Error generating message. Please try again.');
  } finally {
    isLoading.value = false;
  }
};

const generateVoice = async () => {
  if (!generatedMessage.value) return;
  
  isGeneratingVoice.value = true;
  try {
    const response = await fetch('http://localhost:8000/api/text-to-speech', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text: generatedMessage.value,
        voice_id: selectedVoice.value
      })
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Error generating voice');
    }

    const audioBlob = await response.blob();
    if (audioUrl.value) {
      URL.revokeObjectURL(audioUrl.value);
    }
    audioUrl.value = URL.createObjectURL(audioBlob);
  } catch (error) {
    console.error('Error generating voice:', error);
    alert(error.message);
  } finally {
    isGeneratingVoice.value = false;
  }
};

const resetAll = () => {
  transcription.value = '';
  generatedMessage.value = '';
  if (voiceRecorder.value) {
    voiceRecorder.value.audioUrl = null;
  }
};
</script>

<style>
.animate-fade-in {
  animation: fadeIn 0.5s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
