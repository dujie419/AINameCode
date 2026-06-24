<template>
  <view class="page">
    <view class="hero">
      <view class="hero-title">个人中心</view>
      <view class="halo halo-lg"></view>
      <view class="halo halo-md"></view>
      <view class="halo halo-sm"></view>

      <view class="profile-card">
        <view class="avatar-wrap" @tap="openPage('/pages/user/edit-profile')">
          <image class="avatar" :src="profile.avatar || '/static/logo.png'" mode="aspectFill"></image>
          <view class="edit-dot">✎</view>
        </view>
        <view class="nickname">昵称：{{ displayName }}</view>
        <view class="user-id">ID:{{ profile.username || profile.email || profile.id || '--' }}</view>
        <view class="badge-row">
          <view v-if="profile.is_expert" class="tag">专家</view>
          <view v-if="developerStatus" class="tag">开发者</view>
        </view>
      </view>
    </view>

    <view class="wave wave-one"></view>
    <view class="wave wave-two"></view>

    <view class="stats">
      <view class="stat" @tap="openPage('/pages/user/orders')">
        <view class="stat-value">{{ orders.length }}</view>
        <view class="stat-label">订单</view>
      </view>
      <view class="stat middle" @tap="openPage('/pages/user/wallet')">
        <view class="stat-value">{{ balanceText }}</view>
        <view class="stat-label">账户余额(元)</view>
      </view>
      <view class="stat">
        <view class="stat-value">{{ profile.points || 0 }}</view>
        <view class="stat-label">积分</view>
      </view>
    </view>

    <view class="quota-panel">
      <view class="quota-head">
        <view class="quota-title">本月剩余额度</view>
        <view class="quota-badge">{{ quotaSummary.membership_status === "vip" ? "VIP" : "免费用户" }}</view>
      </view>
      <view class="quota-grid">
        <view class="quota-item">
          <view class="quota-value">{{ quotaRemaining("name_generate") }}</view>
          <view class="quota-label">起名次数</view>
        </view>
        <view class="quota-item">
          <view class="quota-value">{{ quotaRemaining("business_card") }}</view>
          <view class="quota-label">名片次数</view>
        </view>
        <view class="quota-item">
          <view class="quota-value">{{ quotaRemaining("image_generate") }}</view>
          <view class="quota-label">图片生成</view>
        </view>
      </view>
    </view>

    <view class="content">
      <view class="menu-group">
        <view class="menu-item" @tap="openPage('/pages/user/recharge')">
          <view class="menu-icon cyan">▰</view>
          <view class="menu-text">充值</view>
        </view>
        <view class="menu-item" @tap="openPage('/pages/user/wallet')">
          <view class="menu-icon orange">▣</view>
          <view class="menu-text">余额流水</view>
        </view>
      </view>

      <view class="menu-group">
        <view class="menu-item" @tap="openPage('/pages/user/orders')">
          <view class="menu-icon red">▤</view>
          <view class="menu-text">我的订单</view>
        </view>
        <view class="menu-item" @tap="openPage('/pages/user/edit-profile')">
          <view class="menu-icon yellow">●</view>
          <view class="menu-text">我的资料</view>
        </view>
        <view class="menu-item" @tap="openPage('/pages/developer/index')">
          <view class="menu-icon blue">◒</view>
          <view class="menu-text">开发者中心</view>
        </view>
        <view class="menu-item" @tap="openExpertPage">
          <view class="menu-icon green">i</view>
          <view class="menu-text">{{ profile.is_expert ? '专家中心' : '申请成为专家' }}</view>
        </view>
      </view>

      <view class="preview" v-if="orders.length || transactions.length">
        <view class="preview-head">
          <view class="preview-title">最近动态</view>
        </view>
        <view class="preview-row" v-for="item in orders" :key="`order-${item.id}`" @tap="openPage(`/pages/user/order-detail?id=${item.id}`)">
          <view>
            <view class="row-title">{{ item.order_no || `订单 #${item.id}` }}</view>
            <view class="row-sub">{{ orderTypeText(item.order_type) }} · {{ orderStatusText(item.status) }}</view>
          </view>
          <view class="row-money">¥{{ item.amount }}</view>
        </view>
        <view class="preview-row" v-for="item in transactions" :key="`transaction-${item.id}`">
          <view>
            <view class="row-title">{{ transactionTypeText(item.transaction_type) }}</view>
            <view class="row-sub">{{ item.description || item.created_at }}</view>
          </view>
          <view :class="['row-money', Number(item.amount) >= 0 ? 'plus' : 'minus']">{{ item.amount }}</view>
        </view>
      </view>
    </view>

    <view class="tabbar">
      <view class="tab-item" @tap="openPage('/pages/index/index')">
        <view class="tab-icon home"></view>
        <view class="tab-text">首页</view>
      </view>
      <view class="tab-item" @tap="openPage('/pages/expert/index')">
        <view class="tab-icon expert"></view>
        <view class="tab-text">专家</view>
      </view>
      <view class="tab-item" @tap="openPage('/pages/community/index')">
        <view class="tab-icon cart"></view>
        <view class="tab-text">灵感池</view>
      </view>
      <view class="tab-item active">
        <view class="tab-icon user"></view>
        <view class="tab-text">个人中心</view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { onShow } from "@dcloudio/uni-app";
import { computed, ref } from "vue";
import http from "@/http/http.js";
import developerApi from "@/api/developer.js";
import { goPage } from "@/utils/router.js";

const profile = ref({});
const orders = ref([]);
const transactions = ref([]);
const developerStatus = ref("");
const quotaSummary = ref({ membership_status: "free", items: {} });

const orderStatusMap = {
  pending: "待支付",
  paid: "已支付",
  processing: "处理中",
  completed: "已完成",
  cancelled: "已取消",
  refunded: "已退款"
};
const orderTypeMap = {
  ai_name: "AI命名订单",
  brand_visual: "品牌视觉订单",
  expert_service: "专家服务订单",
  api_package: "API套餐订单"
};
const transactionTypeMap = {
  recharge: "充值",
  pay: "支付",
  refund: "退款",
  expert_income: "专家收入"
};

const displayName = computed(() => profile.value.nickname || profile.value.username || "用户中心");
const balanceText = computed(() => Number(profile.value.balance || 0).toFixed(2));

const openPage = (url) => goPage(url);
const openExpertPage = () => {
  openPage(profile.value.is_expert ? "/pages/expert/workbench" : "/pages/expert/apply");
};
const orderStatusText = (value) => orderStatusMap[value] || value || "未知状态";
const orderTypeText = (value) => orderTypeMap[value] || value || "订单";
const transactionTypeText = (value) => transactionTypeMap[value] || value || "流水";
const quotaRemaining = (type) => {
  const item = quotaSummary.value.items && quotaSummary.value.items[type];
  if (!item) return "--";
  return item.remaining;
};

const loadProfile = async () => {
  profile.value = await http.getUserProfile();
};

const loadQuotaSummary = async () => {
  quotaSummary.value = await http.getQuotaSummary();
};

const loadSummary = async () => {
  const [orderRes, transactionRes] = await Promise.all([
    http.getUserOrders("?page=1&page_size=3"),
    http.getWalletTransactions("?page=1&page_size=3")
  ]);
  orders.value = orderRes.items || [];
  transactions.value = transactionRes.items || [];
};

const loadDeveloperStatus = async () => {
  try {
    const developer = await developerApi.getDeveloperProfile();
    developerStatus.value = developer && developer.status ? developer.status : "";
  } catch (error) {
    developerStatus.value = "";
  }
};

const loadPage = async () => {
  await Promise.all([loadProfile(), loadQuotaSummary(), loadSummary(), loadDeveloperStatus()]);
};

onShow(loadPage);
</script>

<style scoped>
.page {
  min-height: 100vh;
  padding-bottom: 132rpx;
  background: #f1f1f1;
  box-sizing: border-box;
  overflow-x: hidden;
}

.hero {
  position: relative;
  height: 490rpx;
  overflow: hidden;
  background: linear-gradient(180deg, #36b7f6 0%, #16a3e6 100%);
  color: #fff;
}

.hero-title {
  position: relative;
  z-index: 3;
  padding: 64rpx 40rpx 0;
  font-size: 38rpx;
  font-weight: 300;
}

.halo {
  position: absolute;
  left: 50%;
  top: 112rpx;
  transform: translateX(-50%);
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
}

.halo-lg {
  width: 560rpx;
  height: 560rpx;
}

.halo-md {
  top: 176rpx;
  width: 360rpx;
  height: 360rpx;
  background: rgba(255, 255, 255, 0.13);
}

.halo-sm {
  top: 254rpx;
  width: 200rpx;
  height: 200rpx;
  background: rgba(255, 255, 255, 0.16);
}

.profile-card {
  position: absolute;
  z-index: 4;
  left: 0;
  right: 0;
  top: 204rpx;
  display: flex;
  align-items: center;
  flex-direction: column;
}

.avatar-wrap {
  position: relative;
  width: 150rpx;
  height: 150rpx;
  border-radius: 50%;
  border: 8rpx solid #1c98d9;
  background: #fff;
}

.avatar {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  display: block;
}

.edit-dot {
  position: absolute;
  right: -4rpx;
  bottom: 8rpx;
  width: 38rpx;
  height: 38rpx;
  border-radius: 50%;
  background: #fff;
  color: #28a9e8;
  line-height: 38rpx;
  text-align: center;
  font-size: 26rpx;
  font-weight: 700;
}

.nickname {
  margin-top: 24rpx;
  font-size: 29rpx;
  line-height: 1.35;
}

.user-id {
  margin-top: 4rpx;
  color: rgba(255, 255, 255, 0.78);
  font-size: 28rpx;
  line-height: 1.35;
}

.badge-row {
  display: flex;
  gap: 12rpx;
  min-height: 34rpx;
  margin-top: 8rpx;
}

.tag {
  padding: 4rpx 16rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.22);
  color: #fff;
  font-size: 22rpx;
}

.wave {
  position: relative;
  z-index: 5;
  height: 40rpx;
  margin-top: -34rpx;
  border-radius: 50% 50% 0 0 / 100% 100% 0 0;
}

.wave-one {
  background: rgba(216, 242, 253, 0.86);
  transform: translateX(-8%) scaleX(1.16);
}

.wave-two {
  height: 42rpx;
  margin-top: -26rpx;
  background: #fff;
  transform: translateX(5%) scaleX(1.22);
}

.stats {
  position: relative;
  z-index: 6;
  display: flex;
  align-items: center;
  height: 124rpx;
  margin-top: -16rpx;
  background: #fff;
}

.stat {
  flex: 1;
  text-align: center;
}

.stat.middle {
  border-left: 1px solid #e5e5e5;
  border-right: 1px solid #e5e5e5;
}

.stat-value {
  color: #22a9e9;
  font-size: 31rpx;
  line-height: 1.35;
}

.stat-label {
  margin-top: 6rpx;
  color: #666;
  font-size: 28rpx;
}

.quota-panel {
  position: relative;
  z-index: 6;
  margin: 18rpx 24rpx 0;
  padding: 24rpx;
  border-radius: 12rpx;
  background: #fff;
  box-sizing: border-box;
}

.quota-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
  margin-bottom: 20rpx;
}

.quota-title {
  color: #333;
  font-size: 30rpx;
  font-weight: 700;
}

.quota-badge {
  flex-shrink: 0;
  padding: 6rpx 16rpx;
  border-radius: 999rpx;
  background: #e0f2fe;
  color: #0284c7;
  font-size: 22rpx;
  font-weight: 700;
}

.quota-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14rpx;
}

.quota-item {
  min-width: 0;
  padding: 18rpx 10rpx;
  border-radius: 10rpx;
  background: #f8fafc;
  text-align: center;
}

.quota-value {
  color: #111827;
  font-size: 34rpx;
  font-weight: 800;
  line-height: 1.25;
}

.quota-label {
  margin-top: 8rpx;
  color: #6b7280;
  font-size: 24rpx;
}

.content {
  padding-top: 20rpx;
}

.menu-group {
  margin-top: 18rpx;
  background: #fff;
}

.menu-item {
  display: flex;
  align-items: center;
  min-height: 88rpx;
  padding: 0 22rpx;
  box-sizing: border-box;
}

.menu-item + .menu-item {
  border-top: 1px solid #e8e8e8;
}

.menu-icon {
  width: 38rpx;
  margin-right: 14rpx;
  text-align: center;
  font-size: 33rpx;
  font-weight: 800;
  line-height: 1;
}

.menu-icon.cyan {
  color: #18b8e6;
}

.menu-icon.orange {
  color: #ff9b45;
}

.menu-icon.red {
  color: #ef5b50;
}

.menu-icon.yellow {
  color: #f4bd24;
}

.menu-icon.blue {
  color: #5574ec;
}

.menu-icon.green {
  color: #17ccb0;
}

.menu-text {
  color: #333;
  font-size: 30rpx;
}

.preview {
  margin-top: 18rpx;
  background: #fff;
}

.preview-head {
  padding: 22rpx;
  border-bottom: 1px solid #e8e8e8;
}

.preview-title {
  color: #333;
  font-size: 30rpx;
  font-weight: 700;
}

.preview-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20rpx;
  padding: 20rpx 22rpx;
  border-bottom: 1px solid #e8e8e8;
}

.row-title {
  color: #333;
  font-size: 27rpx;
  font-weight: 700;
}

.row-sub {
  margin-top: 8rpx;
  color: #888;
  font-size: 24rpx;
}

.row-money {
  flex-shrink: 0;
  color: #333;
  font-size: 27rpx;
  font-weight: 700;
}

.row-money.plus {
  color: #16a34a;
}

.row-money.minus {
  color: #dc2626;
}

.tabbar {
  position: fixed;
  z-index: 20;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  height: 112rpx;
  padding-bottom: env(safe-area-inset-bottom);
  background: #fff;
  border-top: 1px solid #e7e7e7;
}

.tab-item {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  color: #b7b7b7;
}

.tab-item.active {
  color: #16a3e6;
}

.tab-icon {
  position: relative;
  width: 44rpx;
  height: 44rpx;
  margin-bottom: 6rpx;
}

.tab-icon.home {
  background: currentColor;
  clip-path: polygon(50% 0, 100% 42%, 86% 42%, 86% 100%, 14% 100%, 14% 42%, 0 42%);
}

.tab-icon.expert {
  border: 8rpx solid currentColor;
  border-top: 0;
  border-radius: 0 0 8rpx 8rpx;
  box-sizing: border-box;
}

.tab-icon.expert::before {
  content: "";
  position: absolute;
  left: 8rpx;
  top: -12rpx;
  width: 26rpx;
  height: 12rpx;
  border: 5rpx solid currentColor;
  border-bottom: 0;
  border-radius: 12rpx 12rpx 0 0;
}

.tab-icon.cart {
  border-bottom: 10rpx solid currentColor;
  border-left: 8rpx solid transparent;
  border-right: 8rpx solid transparent;
  transform: skewX(-8deg);
  box-sizing: border-box;
}

.tab-icon.cart::before,
.tab-icon.cart::after {
  content: "";
  position: absolute;
  bottom: -20rpx;
  width: 9rpx;
  height: 9rpx;
  border-radius: 50%;
  background: currentColor;
}

.tab-icon.cart::before {
  left: 4rpx;
}

.tab-icon.cart::after {
  right: 4rpx;
}

.tab-icon.user::before {
  content: "";
  position: absolute;
  left: 10rpx;
  top: 0;
  width: 24rpx;
  height: 24rpx;
  border-radius: 50%;
  background: currentColor;
}

.tab-icon.user::after {
  content: "";
  position: absolute;
  left: 3rpx;
  bottom: 0;
  width: 38rpx;
  height: 24rpx;
  border-radius: 20rpx 20rpx 6rpx 6rpx;
  background: currentColor;
}

.tab-text {
  font-size: 26rpx;
  line-height: 1.2;
}
</style>
