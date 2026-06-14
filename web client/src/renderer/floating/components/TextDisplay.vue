<template>
  <div class="text-display" v-if="displayText" ref="_innerRef">
    <span
      v-for="(item, index) in textChars"
      :key="index"
      :data-char-idx="index"
      :class="getCharClass(item)"
    >{{ item.char === ' ' ? '\u00A0' : item.char }}</span>
  </div>
</template>

<script setup>
import { ref } from 'vue';

const props = defineProps({
  displayText: { type: String, default: '' },
  textChars: { type: Array, default: () => [] }
});

// 内部 ref，用固定名字不和 prop 冲突
const _innerRef = ref(null);

// 关键：通过 defineExpose 把内部 ref 暴露给父组件
// 这样父组件可以用 ref 语法直接拿到这个 div 的 DOM 元素
defineExpose({
  innerRef: _innerRef
});

// getCharClass 读取 item.status（初始化/重置时触发）
const getCharClass = (item) => {
  return {
    'char-read': item.status === 'read',
    'char-current': item.status === 'current',
    'char-upcoming': item.status === 'upcoming'
  };
};
</script>

<style scoped>
@import '../../styles/text-display.css';
</style>
