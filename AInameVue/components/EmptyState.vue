<template>
  <view class="app-empty">
    <slot>{{ text }}</slot>
  </view>
</template>

<script setup>
defineProps({
  text: {
    type: String,
    default: "暂无数据"
  }
});
</script>
