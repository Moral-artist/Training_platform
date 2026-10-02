<template>
  <div class="lesson-create-page">
    <div class="form-card">

      <h2>Create Lesson</h2>

      <!-- System -->
      <div class="form-item">
        <label>System</label>

        <select
          v-model.number="lessonForm.system_id"
          :disabled="systemsLoading || loading || uploading"
        >
          <option disabled value="">
            {{ systemsLoading ? 'Loading systems...' : 'Please select system' }}
          </option>

          <option
            v-for="system in systems"
            :key="system.system_id"
            :value="system.system_id"
          >
            {{ system.system_name }}
          </option>
        </select>
      </div>


      <!-- Lesson Name -->
      <div class="form-item">
        <label>Lesson Name</label>

        <input
          v-model="lessonForm.lesson_name"
          type="text"
          placeholder="Enter lesson name"
          :disabled="loading || uploading"
        />
      </div>


      <!-- Description -->
      <div class="form-item">
        <label>Description</label>

        <textarea
          v-model="lessonForm.description"
          rows="5"
          placeholder="Enter lesson description"
          :disabled="loading || uploading"
        ></textarea>
      </div>


      <!-- Video -->
      <div class="form-item">
        <label>Lesson Video</label>

        <input
          type="file"
          accept="video/mp4,video/webm"
          :disabled="loading || uploading || courseCreated"
          @change="handleVideoChange"
        />

        <div
          v-if="selectedVideo"
          class="video-info"
        >
          {{ selectedVideo.name }}
          -
          {{ formatFileSize(selectedVideo.size) }}
        </div>

        <!-- 上传进度 -->
        <div
          v-if="uploading"
          class="upload-progress"
        >
          <div class="progress-text">
            Uploading {{ uploadProgress }}%
          </div>

          <div class="progress-bar">
            <div
              class="progress-value"
              :style="{ width: uploadProgress + '%' }"
            ></div>
          </div>
        </div>

        <!-- 上传成功 -->
        <div
          v-if="lessonForm.video_asset_id"
          class="upload-success"
        >
          源视频上传完成，处理状态：{{ videoStatus }}
        </div>
      </div>


      <p v-if="videoStatus === 'uploaded' || videoStatus === 'processing'">视频正在后台转码。课程可以先保存，转码完成后才能播放。</p>
      <p v-if="videoStatus === 'ready'">HLS 视频已就绪。</p>
      <button v-if="videoStatus === 'failed'" type="button" @click="retryVideo">重新转码</button>
      <p v-if="statusError">{{ statusError }}</p>
      <p v-if="courseCreated">课程已保存。请到课程授权页给学员授权，然后到首页观看。</p>
      <RouterLink v-if="courseCreated" to="/lessons/accessmanage">给学员授权</RouterLink>
      <RouterLink v-if="courseCreated" to="/home">返回首页</RouterLink>
      <button
        class="submit-button"
        :disabled="loading || uploading || courseCreated"
        @click="handleSubmit"
      >
        {{
          uploading
            ? `Uploading ${uploadProgress}%`
            : loading
              ? 'Submitting...'
              : 'Create Lesson'
        }}
      </button>


      <div
        v-if="messageBox.visible"
        :class="['message-box', messageBox.type]"
      >
        {{ messageBox.message }}
      </div>

    </div>
  </div>
</template>


<script setup>
import {
  reactive,
  ref,
  onMounted,
  onBeforeUnmount
} from 'vue'

  import axios from 'axios'
  import request from '../api/request'



  const loading = ref(false)
  const systemsLoading = ref(false)

  const uploading = ref(false)
  const uploadProgress = ref(0)

  const systems = ref([])
  const videoStatus = ref('')
  const statusError = ref('')
  const courseCreated = ref(false)
  let pollTimer = null
  let alive = true
  let currentAssetId = null


  // 用户选择的视频
  const selectedVideo = ref(null)


  const lessonForm = reactive({
    system_id: '',
    lesson_name: '',
    description: '',

    // 仅提交视频资产 ID
    video_asset_id: ''
  })


  const messageBox = reactive({
    visible: false,
    message: '',
    type: 'warning'
  })

  let messageTimer = null


  const showMessage = (
    message,
    type = 'warning'
  ) => {
    messageBox.message = message
    messageBox.type = type
    messageBox.visible = true

    clearTimeout(messageTimer)

    messageTimer = setTimeout(() => {
      messageBox.visible = false
    }, 2500)
  }


  // ==========================
  // 获取 System
  // ==========================

  const getSystems = async () => {
    try {
      systemsLoading.value = true

      const response = await request.get(
        '/api/lessons/systems'
      )

      systems.value = response.data

    } catch (error) {

      showMessage(
        error.response?.data?.detail ||
        'Failed to load systems',
        'error'
      )

    } finally {

      systemsLoading.value = false

    }
  }


  // ==========================
  // 选择视频
  // ==========================

  const handleVideoChange = event => {

    const file = event.target.files[0]

    if (!file) {
      return
    }


    // 文件类型校验
    const allowedTypes = [
      'video/mp4',
      'video/webm'
    ]

    if (!allowedTypes.includes(file.type)) {

      showMessage(
        'Only MP4 and WebM videos are supported',
        'warning'
      )

      event.target.value = ''

      return
    }


    // 最大 300MB
    const maxSize = 300 * 1024 * 1024

    if (file.size > maxSize) {

      showMessage(
        'Video size cannot exceed 300MB',
        'warning'
      )

      event.target.value = ''

      return
    }


    selectedVideo.value = file

    // 如果重新选视频，旧 key 作废
    lessonForm.video_asset_id = ''
    currentAssetId = null
    videoStatus.value = ''
    clearTimeout(pollTimer)
    uploadProgress.value = 0
  }


  // ==========================
  // 向 FastAPI 获取预签名 URL
  // ==========================

  const getUploadUrl = async file => {

    const response = await request.post(
      '/api/lessons_video/upload_token',
      {
        filename: file.name,
        content_type: file.type,  
        size: file.size
      }
    )

    return response.data
  }


  // ==========================
  // 上传视频到 Cloudflare R2
  // ==========================

  const uploadVideo = async () => {

    if (!selectedVideo.value) {
      throw new Error('Please select video')
    }


    uploading.value = true
    uploadProgress.value = 0


    try {

      const file = selectedVideo.value


      // ① 获取上传地址与视频资产 ID
      const uploadInfo = await getUploadUrl(file)


      const {
        upload_url,
        asset_id
      } = uploadInfo


      // ② Vue 直接 PUT 到 R2
      //
      // 注意：
      // 不使用 request
      //
      // 因为 request 会自动携带
      // session cookie / csrf header
      //
      // 上传 R2 用普通 axios
      await axios.put(
        upload_url,
        file,
        {
          withCredentials: false,
          headers: {
            'Content-Type': file.type
          },

          onUploadProgress: progressEvent => {

            if (!progressEvent.total) {
              return
            }

            uploadProgress.value = Math.round(
              (
                progressEvent.loaded *
                100
              ) /
              progressEvent.total
            )
          }
        }
      )


      // ③ 通知后端检查 R2 文件，再加入转码队列。
      await request.post(`/api/lessons_video/${asset_id}/complete`)
      lessonForm.video_asset_id = asset_id
      currentAssetId = asset_id
      videoStatus.value = 'uploaded'
      pollVideoStatus(asset_id)


      showMessage(
        'Video uploaded successfully',
        'success'
      )


      return asset_id

    } finally {

      uploading.value = false

    }
  }


  // ==========================
  // 提交 Lesson
  // ==========================

  const handleSubmit = async () => {

    if (!lessonForm.system_id) {

      showMessage(
        'Please select system',
        'warning'
      )

      return
    }


    if (!lessonForm.lesson_name.trim()) {

      showMessage(
        'Please enter lesson name',
        'warning'
      )

      return
    }


    if (!lessonForm.description.trim()) {

      showMessage(
        'Please enter description',
        'warning'
      )

      return
    }


    if (!selectedVideo.value) {

      showMessage(
        'Please select lesson video',
        'warning'
      )

      return
    }


    try {

      loading.value = true


      // ==========================
      // 第一步：上传视频
      // ==========================

      if (!lessonForm.video_asset_id) {
        await uploadVideo()
      }


      // ==========================
      // 第二步：创建 Lesson
      // ==========================
      const response = await request.post(
        '/api/lessons/lessonsubmit',
        {
          system_id:
            lessonForm.system_id,

          lesson_name:
            lessonForm.lesson_name.trim(),

          description:
            lessonForm.description.trim(),

          video_asset_id:
            lessonForm.video_asset_id
        }
      )


      showMessage(
        response.data.message ||
        'Lesson created successfully',
        'success'
      )


      courseCreated.value = true


    } catch (error) {

      console.error(
        'Create lesson failed:',
        error
      )


      showMessage(
        error.response?.data?.detail ||
        error.message ||
        'Create lesson failed',
        'error'
      )

    } finally {

      loading.value = false

    }
  }


  // ==========================
  // 文件大小显示
  // ==========================

  const formatFileSize = bytes => {

    if (bytes < 1024 * 1024) {
      return `${(bytes / 1024).toFixed(1)} KB`
    }

    return `${(
      bytes /
      1024 /
      1024
    ).toFixed(1)} MB`
  }


  async function pollVideoStatus(assetId) {
    clearTimeout(pollTimer)
    try {
      const response = await request.get(`/api/lessons_video/${assetId}/status`)
      if (!alive || currentAssetId !== assetId) return
      videoStatus.value = response.data.status
      statusError.value = ''
      if (['uploaded', 'processing'].includes(videoStatus.value)) {
        pollTimer = setTimeout(() => pollVideoStatus(assetId), 5000)
      }
    } catch (error) {
      if (!alive || currentAssetId !== assetId) return
      statusError.value = '状态查询失败，请检查登录和网络后刷新。'
      if (![401, 403, 404].includes(error.response?.status)) {
        pollTimer = setTimeout(() => pollVideoStatus(assetId), 10000)
      }
    }
  }

  async function retryVideo() {
    try {
      await request.post(`/api/lessons_video/${lessonForm.video_asset_id}/retry`)
      videoStatus.value = 'uploaded'
      pollVideoStatus(lessonForm.video_asset_id)
    } catch (error) {
      showMessage(error.response?.data?.detail || '重试失败', 'error')
    }
  }

  onBeforeUnmount(() => {
    alive = false
    clearTimeout(pollTimer)
    clearTimeout(messageTimer)
  })

  // ==========================
  // 页面初始化
  // ==========================

  onMounted(() => {
    getSystems()
  })
</script>
<style scoped>
.lesson-create-page {
  display: flex;
  justify-content: center;
  padding-top: 60px;
}

.form-card {
  width: 500px;
  padding: 30px;
  background: white;
  border: 1px solid #ddd;
  border-radius: 12px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 18px;
}

.form-item input,
.form-item textarea,
.form-item select {
  padding: 10px 12px;
  border: 1px solid #ccc;
  border-radius: 6px;
  font-size: 14px;
}

.submit-button {
  width: 100%;
  padding: 11px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.submit-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.message-box {
  margin-top: 16px;
  padding: 10px;
  border-radius: 6px;
}

.message-box.success {
  background: #e8f5e9;
}

.message-box.warning {
  background: #fff3cd;
}

.message-box.error {
  background: #ffebee;
}
.video-info {
  margin-top: 8px;
  font-size: 14px;
  color: #666;
}

.upload-progress {
  margin-top: 12px;
}

.progress-text {
  margin-bottom: 6px;
  font-size: 13px;
}

.progress-bar {
  height: 8px;
  background: #eee;
  border-radius: 4px;
  overflow: hidden;
}

.progress-value {
  height: 100%;
  background: #333;
  transition: width 0.2s;
}

.upload-success {
  margin-top: 10px;
  color: #2e7d32;
  font-size: 14px;
}
</style>