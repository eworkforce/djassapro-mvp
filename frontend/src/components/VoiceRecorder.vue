<template>
  <div>
    <div class="flex flex-col items-center space-y-4">
      <!-- Recording Button -->
      <button 
        @click="toggleRecording" 
        class="btn"
        :class="[isRecording ? 'btn-secondary' : 'btn-primary']"
      >
        <div class="flex items-center space-x-2">
          <!-- Recording indicator -->
          <div v-if="isRecording" class="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
          <span>{{ isRecording ? 'Stop Recording' : 'Start Recording' }}</span>
        </div>
      </button>

      <!-- Timer -->
      <div v-if="isRecording" class="text-gray-600">
        {{ formatTime(recordingTime) }}
      </div>

      <!-- Audio Preview -->
      <audio v-if="audioUrl" controls :src="audioUrl" class="mt-4"></audio>

      <!-- Error Message -->
      <div v-if="error" class="text-red-500 text-sm mt-2">
        {{ error }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onUnmounted } from 'vue';

const isRecording = ref(false);
const recordingTime = ref(0);
const audioUrl = ref(null);
const error = ref(null);
const mediaRecorder = ref(null);
const chunks = ref([]);
const timerInterval = ref(null);

// Format time in MM:SS
const formatTime = (seconds) => {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
};

// Start timer
const startTimer = () => {
  recordingTime.value = 0;
  timerInterval.value = setInterval(() => {
    recordingTime.value++;
  }, 1000);
};

// Stop timer
const stopTimer = () => {
  if (timerInterval.value) {
    clearInterval(timerInterval.value);
    timerInterval.value = null;
  }
};

// Start recording
const startRecording = async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder.value = new MediaRecorder(stream, {
      mimeType: 'audio/webm;codecs=opus'
    });
    chunks.value = [];

    mediaRecorder.value.ondataavailable = (e) => {
      if (e.data.size > 0) {
        chunks.value.push(e.data);
      }
    };

    mediaRecorder.value.onstop = () => {
      const blob = new Blob(chunks.value, { type: 'audio/webm' });
      if (audioUrl.value) {
        URL.revokeObjectURL(audioUrl.value);
      }
      audioUrl.value = URL.createObjectURL(blob);
      
      // Stop all tracks
      stream.getTracks().forEach(track => track.stop());
    };

    mediaRecorder.value.start(100); // Collect data every 100ms
    startTimer();
    isRecording.value = true;
    error.value = null;
  } catch (err) {
    error.value = 'Error accessing microphone. Please ensure microphone permissions are granted.';
    console.error('Error starting recording:', err);
  }
};

// Stop recording
const stopRecording = () => {
  if (mediaRecorder.value && mediaRecorder.value.state !== 'inactive') {
    mediaRecorder.value.stop();
    stopTimer();
    isRecording.value = false;
  }
};

// Toggle recording
const toggleRecording = () => {
  if (isRecording.value) {
    stopRecording();
  } else {
    startRecording();
  }
};

// Get the recorded audio blob
const getAudioBlob = () => {
  if (!chunks.value.length) return null;
  return new Blob(chunks.value, { type: 'audio/webm' });
};

// Clean up on component unmount
onUnmounted(() => {
  stopTimer();
  if (audioUrl.value) {
    URL.revokeObjectURL(audioUrl.value);
  }
});

// Expose methods and data for parent component
defineExpose({
  getAudioBlob,
  isRecording,
  audioUrl
});
</script>
