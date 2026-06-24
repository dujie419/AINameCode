<template>
  <view class="page">
    <view class="text">正在打开管理员登录...</view>
  </view>
</template>

<script setup>
import { onLoad } from "@dcloudio/uni-app";
import { goAdminLogin } from "@/utils/router.js";

onLoad(() => {
  goAdminLogin();
});
</script>

<style scoped>
.page { min-height: 100vh; display: flex; align-items: center; justify-content: center; background: #f5f7fa; }
.text { color: #6b7280; font-size: 28rpx; }
</style>
