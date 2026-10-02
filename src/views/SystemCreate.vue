<template>
  <div class="system-create-page">
    <div class="form-card">
      <h2>Create System</h2>

      <div class="form-item">
        <label>System Name</label>

        <input
          v-model="systemName"
          type="text"
          placeholder="Please enter system name"
          @keyup.enter="handleSubmit"
        />
      </div>

      <button
        class="submit-button"
        :disabled="loading"
        @click="handleSubmit"
      >
        {{ loading ? 'Submitting...' : 'Create System' }}
      </button>

      <div
        v-if="message"
        :class="['message', messageType]"
      >
        {{ message }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import request from '../api/request'
import router from '../router'

const systemName = ref('')
const loading = ref(false)

const message = ref('')
const messageType = ref('success')

const showMessage = (text, type = 'success') => {
  message.value = text
  messageType.value = type

  setTimeout(() => {
    message.value = ''
  }, 2500)
}

const handleSubmit = async () => {
  if (!systemName.value.trim()) {
    showMessage('Please enter system name', 'error')
    return
  }

  try {
    loading.value = true

    const response = await request.post(
      '/api/lessons/systemsubmit',
      null,
      {
        params: {
          system_name: systemName.value
        }
      }
    )

    showMessage(
      response.data.message || 'System created successfully',
      'success'
    )

    systemName.value = ''
    await router.push('/lessons/:major')

  } catch (error) {
    console.error('Create system failed:', error)

    showMessage(
      error.response?.data?.detail ||
      'Create system failed',
      'error'
    )

  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.system-create-page {
  display: flex;
  justify-content: center;
  padding-top: 80px;
}

.form-card {
  width: 420px;
  padding: 30px;
  border: 1px solid #ddd;
  border-radius: 12px;
  background: white;
}

.form-card h2 {
  margin-bottom: 24px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-item input {
  padding: 10px 12px;
  border: 1px solid #ccc;
  border-radius: 6px;
  font-size: 14px;
}

.submit-button {
  width: 100%;
  margin-top: 20px;
  padding: 11px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.submit-button:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.message {
  margin-top: 16px;
  padding: 10px;
  border-radius: 6px;
}

.message.success {
  background: #e8f5e9;
}

.message.error {
  background: #ffebee;
}
</style>