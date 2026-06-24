<template>
  <view class="page">
    <view class="profile">
      <image class="avatar" :src="profile.avatar || '/static/logo.png'" mode="aspectFill"></image>
      <view>
        <view class="name">{{ profile.name || '专家中心' }}</view>
        <view class="title">{{ profile.title }}</view>
        <view class="status">状态：{{ profile.status }}</view>
      </view>
    </view>

    <view class="stats">
      <view><text>{{ stats.pending_orders || 0 }}</text><label>待处理</label></view>
      <view><text>{{ stats.completed_orders || 0 }}</text><label>已完成</label></view>
      <view><text>¥{{ stats.total_income || '0.00' }}</text><label>累计收入</label></view>
      <view><text>¥{{ stats.available_balance || '0.00' }}</text><label>可提现</label></view>
    </view>

    <view class="grid">
      <button @tap="openPage('/pages/expert/workbench')">专家工作台</button>
      <button @tap="openPage('/pages/expert-center/income')">收入明细</button>
      <button @tap="openPage('/pages/expert-center/profile')">编辑个人资料</button>
      <button class="dark" @tap="openPage('/pages/user/center')">返回普通用户中心</button>
    </view>

    <ExpertNavPane active="profile" />
  </view>
</template>

<script setup>
import { onShow } from "@dcloudio/uni-app";
import { ref } from "vue";
import http from "@/http/http.js";
import { goPage } from "@/utils/router.js";
import ExpertNavPane from "@/components/ExpertNavPane.vue";

const profile = ref({});
const stats = ref({});
const openPage = (url) => goPage(url);

const load = async () => {
  profile.value = await http.getExpertCenterProfile();
  stats.value = await http.getExpertCenterStatistics();
};

onShow(load);
</script>

<style scoped>
.page { min-height: 100vh; padding: 30rpx 30rpx 152rpx; background: #f5f7fa; box-sizing: border-box; }
.profile { display: flex; gap: 24rpx; align-items: center; background: #fff; border-radius: 12rpx; padding: 28rpx; }
.avatar { width: 128rpx; height: 128rpx; border-radius: 64rpx; background: #eef2f7; }
.name { font-size: 38rpx; font-weight: 700; color: #111827; }
.title, .status { color: #6b7280; font-size: 24rpx; margin-top: 8rpx; }
.stats { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16rpx; margin-top: 24rpx; }
.stats view { background: #fff; border-radius: 12rpx; padding: 26rpx; }
.stats text { display: block; font-size: 36rpx; font-weight: 800; color: #111827; }
.stats label { color: #6b7280; font-size: 24rpx; margin-top: 8rpx; display: block; }
.grid { display: grid; grid-template-columns: 1fr; gap: 18rpx; margin-top: 24rpx; }
.grid button { width: 100%; margin: 0; background: #fff; color: #111827; border-radius: 10rpx; font-size: 28rpx; }
.grid .dark { background: #111827; color: #fff; }
</style>
