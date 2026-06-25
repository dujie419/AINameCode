<template>
  <view class="page">
    <view class="summary">
      <view class="title">邀请好友</view>
      <view class="subtitle">好友注册成功后，你将获得 AI 起名赠送次数。</view>
      <view class="code-box">
        <view class="code-label">邀请码</view>
        <view class="code">{{ summary.invite_code || "--" }}</view>
      </view>
      <view class="actions">
        <button class="primary" @tap="copyLink">复制邀请链接</button>
        <button class="secondary" @tap="copyCode">复制邀请码</button>
      </view>
    </view>

    <view class="stats">
      <view class="stat">
        <view class="value">{{ summary.invited_count || 0 }}</view>
        <view class="label">已邀请</view>
      </view>
      <view class="stat">
        <view class="value">{{ summary.reward_total || 0 }}</view>
        <view class="label">累计奖励</view>
      </view>
      <view class="stat">
        <view class="value">{{ summary.bonus_remaining || 0 }}</view>
        <view class="label">剩余赠送</view>
      </view>
    </view>

    <view class="records">
      <view class="section-title">邀请记录</view>
      <view v-if="records.length === 0" class="empty">暂无邀请记录</view>
      <view v-for="item in records" :key="item.id" class="record">
        <view>
          <view class="name">{{ item.invitee_username || item.invitee_email || `用户 ${item.invitee_user_id}` }}</view>
          <view class="time">{{ formatTime(item.registered_at) }}</view>
        </view>
        <view :class="['status', item.reward_status === 'granted' ? 'ok' : 'pending']">
          {{ item.reward_status === "granted" ? "已奖励" : "待奖励" }}
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from "vue";
import { onShow } from "@dcloudio/uni-app";
import http from "@/http/http.js";

const summary = ref({});
const records = ref([]);

const inviteLink = computed(() => {
  const code = summary.value.invite_code || "";
  if (!code) return "";

  // #ifdef H5
  const origin = window.location.origin + window.location.pathname;
  return `${origin}#/pages/register/register?invite_code=${encodeURIComponent(code)}`;
  // #endif

  return `/pages/register/register?invite_code=${encodeURIComponent(code)}`;
});

const loadPage = async () => {
  const [summaryRes, recordRes] = await Promise.all([
    http.getInviteSummary(),
    http.getInviteRecords("?page=1&page_size=20")
  ]);
  summary.value = summaryRes || {};
  records.value = recordRes.items || [];
};

const copyText = (text, title) => {
  if (!text) return uni.showToast({ title: "暂无可复制内容", icon: "none" });
  uni.setClipboardData({
    data: text,
    success: () => uni.showToast({ title })
  });
};

const copyCode = () => copyText(summary.value.invite_code || "", "已复制邀请码");
const copyLink = () => copyText(inviteLink.value, "已复制邀请链接");

const formatTime = (value) => {
  if (!value) return "";
  return String(value).replace("T", " ").slice(0, 16);
};

onShow(loadPage);
</script>

<style scoped>
.page {
  min-height: 100vh;
  padding: 28rpx;
  background: #f6f7fb;
  box-sizing: border-box;
}

.summary,
.stats,
.records {
  background: #fff;
  border-radius: 12rpx;
  box-sizing: border-box;
}

.summary {
  padding: 34rpx;
}

.title {
  color: #111827;
  font-size: 42rpx;
  font-weight: 800;
}

.subtitle {
  margin-top: 12rpx;
  color: #6b7280;
  font-size: 26rpx;
  line-height: 1.5;
}

.code-box {
  margin-top: 30rpx;
  padding: 28rpx;
  border-radius: 10rpx;
  background: #f1f8ff;
}

.code-label {
  color: #64748b;
  font-size: 24rpx;
}

.code {
  margin-top: 10rpx;
  color: #0f172a;
  font-size: 48rpx;
  font-weight: 900;
  letter-spacing: 0;
}

.actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18rpx;
  margin-top: 28rpx;
}

.primary,
.secondary {
  height: 78rpx;
  line-height: 78rpx;
  border-radius: 8rpx;
  font-size: 27rpx;
}

.primary {
  background: #0ea5e9;
  color: #fff;
}

.secondary {
  background: #e2e8f0;
  color: #0f172a;
}

.stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  margin-top: 22rpx;
  padding: 26rpx 0;
}

.stat {
  text-align: center;
}

.value {
  color: #0f172a;
  font-size: 38rpx;
  font-weight: 800;
}

.label {
  margin-top: 8rpx;
  color: #64748b;
  font-size: 24rpx;
}

.records {
  margin-top: 22rpx;
  padding: 28rpx;
}

.section-title {
  color: #111827;
  font-size: 31rpx;
  font-weight: 800;
}

.empty {
  padding: 60rpx 0;
  color: #94a3b8;
  text-align: center;
  font-size: 26rpx;
}

.record {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
  padding: 24rpx 0;
  border-bottom: 1px solid #edf2f7;
}

.name {
  color: #1f2937;
  font-size: 28rpx;
  font-weight: 700;
}

.time {
  margin-top: 6rpx;
  color: #94a3b8;
  font-size: 23rpx;
}

.status {
  flex-shrink: 0;
  padding: 7rpx 16rpx;
  border-radius: 999rpx;
  font-size: 23rpx;
}

.status.ok {
  background: #dcfce7;
  color: #15803d;
}

.status.pending {
  background: #fef3c7;
  color: #b45309;
}
</style>
