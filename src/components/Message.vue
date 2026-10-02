<template>
  <Transition name="message">
    <div
      v-if="visible"
      class="message"
      :class="type"
    >
      <span class="message-icon">
        {{ icon }}
      </span>

      <span class="message-text">
        {{ message }}
      </span>
    </div>
  </Transition>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },

  message: {
    type: String,
    default: ''
  },

  type: {
    type: String,
    default: 'warning'
  }
})

const icon = computed(() => {
  if (props.type === 'success') return '✓'
  if (props.type === 'error') return '×'

  return '!'
})
</script>

<style scoped>
.message {
  position: fixed;

  top: 30px;
  left: 50%;

  transform: translateX(-50%);

  z-index: 9999;

  min-width: 280px;
  max-width: 500px;

  padding: 14px 20px;

  display: flex;
  align-items: center;
  gap: 10px;

  box-sizing: border-box;

  background: #ffffff;

  border-radius: 8px;

  box-shadow:
    0 6px 24px rgba(0, 0, 0, 0.12);

  font-size: 14px;
}


/* 图标 */

.message-icon {
  width: 22px;
  height: 22px;

  flex-shrink: 0;

  display: flex;
  align-items: center;
  justify-content: center;

  border-radius: 50%;

  font-weight: bold;
}


/* 警告 */

.message.warning {
  border: 1px solid #f3d19e;
  color: #b88230;
}

.message.warning .message-icon {
  background: #e6a23c;
  color: #ffffff;
}


/* 成功 */

.message.success {
  border: 1px solid #b3e19d;
  color: #529b2e;
}

.message.success .message-icon {
  background: #67c23a;
  color: #ffffff;
}


/* 错误 */

.message.error {
  border: 1px solid #fab6b6;
  color: #c45656;
}

.message.error .message-icon {
  background: #f56c6c;
  color: #ffffff;
}


/* 动画 */

.message-enter-active,
.message-leave-active {
  transition: all 0.25s ease;
}

.message-enter-from,
.message-leave-to {
  opacity: 0;
  transform: translate(-50%, -15px);
}


/* 手机 */

@media (max-width: 480px) {

  .message {
    width: calc(100% - 32px);
    min-width: 0;

    top: 20px;
  }

}
</style>