<template>
  <view class="app-topbar">
    <view>
      <view class="app-title">{{ title }}</view>
      <view v-if="subtitle" class="app-subtitle">{{ subtitle }}</view>
    </view>
    <slot name="action"></slot>
  </view>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    required: true
  },
  subtitle: {
    type: String,
    default: ""
  }
});
</script>
