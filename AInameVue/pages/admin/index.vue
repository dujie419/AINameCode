<template>
  <view class="app-page">
    <AppTopbar title="后台首页" :subtitle="`当前角色：${role}`">
      <template #action>
      <button size="mini" @tap="logout">退出</button>
      </template>
    </AppTopbar>

    <view class="stats-grid">
      <view class="stat-item">
        <text class="label">用户总数</text>
        <text class="value">{{ stats.user_total }}</text>
      </view>
      <view class="stat-item">
        <text class="label">今日新增用户</text>
        <text class="value">{{ stats.today_new_users }}</text>
      </view>
      <view class="stat-item">
        <text class="label">命名总次数</text>
        <text class="value">{{ stats.name_record_total }}</text>
      </view>
      <view class="stat-item">
        <text class="label">今日命名次数</text>
        <text class="value">{{ stats.today_name_count }}</text>
      </view>
      <view class="stat-item">
        <text class="label">专家总数</text>
        <text class="value">{{ stats.expert_total }}</text>
      </view>
      <view class="stat-item">
        <text class="label">待审核专家</text>
        <text class="value warn">{{ stats.pending_expert_total }}</text>
      </view>
    </view>

    <view class="menu">
      <button class="menu-btn" @tap="goUsers">用户管理</button>
      <button class="menu-btn" @tap="goRecords">命名记录</button>
      <button class="menu-btn important" @tap="goExperts">专家审核</button>
      <button class="menu-btn partner" @tap="goPartners">合伙人审核</button>
      <button class="menu-btn finance" @tap="goPartnerFinance">合伙人财务</button>
      <button class="menu-btn platform" @tap="goOpenPlatform">开放平台管理</button>
    </view>
  </view>
</template>

<script setup>
import { onShow } from "@dcloudio/uni-app";
import { ref } from "vue";
import adminApi from "@/api/admin.js";
import { goAdminLogin, goPage } from "@/utils/router.js";
import AppTopbar from "@/components/AppTopbar.vue";

const role = ref(uni.getStorageSync("admin_role") || "");
const stats = ref({
  user_total: 0,
  today_new_users: 0,
  name_record_total: 0,
  today_name_count: 0,
  expert_total: 0,
  pending_expert_total: 0
});

const loadData = async () => {
  stats.value = await adminApi.statistics();
};

const goUsers = () => goPage("/pages/admin/users");
const goRecords = () => goPage("/pages/admin/name-records");
const goExperts = () => goPage("/pages/admin/experts");
const goPartners = () => goPage("/pages/admin/partners");
const goPartnerFinance = () => goPage("/pages/admin/partner-finance");
const goOpenPlatform = () => goPage("/pages/admin/open-platform");
const logout = () => {
  uni.removeStorageSync("admin_token");
  uni.removeStorageSync("admin_role");
  goAdminLogin();
};

onShow(loadData);
</script>

<style scoped>
.stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20rpx; }
.stat-item { background: #fff; border-radius: 10rpx; padding: 28rpx; }
.label { display: block; color: #6b7280; font-size: 24rpx; }
.value { display: block; color: #111827; font-size: 44rpx; font-weight: 700; margin-top: 14rpx; }
.value.warn { color: #c2410c; }
.menu { margin-top: 40rpx; }
.menu-btn { background: #fff; color: #1f2937; border-radius: 10rpx; margin-bottom: 20rpx; }
.menu-btn.important { background: #111827; color: #fff; }
.menu-btn.partner { background: #7c3aed; color: #fff; }
.menu-btn.finance { background: #1d4ed8; color: #fff; }
.menu-btn.platform { background: #0f766e; color: #fff; }
</style>
