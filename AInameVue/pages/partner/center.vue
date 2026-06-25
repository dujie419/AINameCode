<template>
  <view class="page">
    <view v-if="!profile" class="empty">
      <view class="empty-title">尚未申请合伙人</view>
      <button class="btn" @tap="goApply">立即申请</button>
    </view>

    <view v-else>
      <view class="profile">
        <view>
          <view class="title">{{ profile.name }}</view>
          <view class="sub">{{ typeText(profile.partner_type) }} · {{ statusText(profile.status) }}</view>
        </view>
        <button v-if="profile.status === 'rejected'" size="mini" @tap="goApply">重新申请</button>
      </view>

      <view class="qr-card">
        <view class="qr-title">专属二维码</view>
        <image v-if="profile.status === 'approved'" class="qr" :src="qrImage" mode="aspectFit"></image>
        <view v-else class="qr locked">审核通过后启用</view>
        <view class="code">专属码：{{ profile.partner_code }}</view>
        <view class="actions">
          <button class="primary" :disabled="profile.status !== 'approved'" @tap="copyLink">复制注册链接</button>
          <button class="secondary" @tap="copyCode">复制专属码</button>
        </view>
      </view>

      <view class="stats">
        <view class="stat">
          <view class="value">{{ finance.register_count || profile.register_count || 0 }}</view>
          <view class="label">注册归因</view>
        </view>
        <view class="stat">
          <view class="value">{{ money(finance.available_balance) }}</view>
          <view class="label">可提现余额</view>
        </view>
        <view class="stat">
          <view class="value">{{ money(finance.pending_commission) }}</view>
          <view class="label">待结算佣金</view>
        </view>
        <view class="stat">
          <view class="value">{{ money(finance.settled_commission) }}</view>
          <view class="label">已结算佣金</view>
        </view>
      </view>

      <view class="withdraw">
        <view class="section-title">提现申请</view>
        <input class="input" v-model.number="withdrawForm.amount" type="number" placeholder="提现金额" />
        <input class="input" v-model="withdrawForm.account_name" placeholder="收款人姓名" />
        <input class="input" v-model="withdrawForm.account_no" placeholder="收款账号" />
        <input class="input" v-model="withdrawForm.bank_name" placeholder="开户行/渠道" />
        <button class="primary full" :disabled="profile.status !== 'approved'" @tap="submitWithdrawal">提交提现</button>
      </view>

      <view class="records">
        <view class="section-title">佣金流水</view>
        <view v-if="commissions.length === 0" class="empty-line">暂无佣金流水</view>
        <view v-for="item in commissions" :key="`c-${item.id}`" class="record">
          <view>
            <view class="name">{{ item.business_type }} #{{ item.business_id }}</view>
            <view class="time">{{ statusText(item.status) }} · {{ formatTime(item.created_at) }}</view>
          </view>
          <view class="money">{{ money(item.commission_amount) }}</view>
        </view>
      </view>

      <view class="records">
        <view class="section-title">提现记录</view>
        <view v-if="withdrawals.length === 0" class="empty-line">暂无提现记录</view>
        <view v-for="item in withdrawals" :key="`w-${item.id}`" class="record">
          <view>
            <view class="name">{{ item.withdrawal_no }}</view>
            <view class="time">{{ statusText(item.status) }} · {{ formatTime(item.created_at) }}</view>
          </view>
          <view class="money">{{ money(item.amount) }}</view>
        </view>
      </view>

      <view class="records">
        <view class="section-title">扫码注册记录</view>
        <view v-if="records.length === 0" class="empty-line">暂无记录</view>
        <view v-for="item in records" :key="item.id" class="record">
          <view>
            <view class="name">{{ item.username || item.email || `用户 ${item.user_id}` }}</view>
            <view class="time">{{ formatTime(item.created_at) }}</view>
          </view>
          <view class="tag">注册</view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from "vue";
import { onShow } from "@dcloudio/uni-app";
import http from "@/http/http.js";
import { goPage } from "@/utils/router.js";

const profile = ref(null);
const records = ref([]);
const finance = ref({});
const commissions = ref([]);
const withdrawals = ref([]);
const withdrawForm = ref({
  amount: "",
  account_name: "",
  account_no: "",
  bank_name: ""
});

const registerLink = computed(() => {
  const code = profile.value && profile.value.partner_code;
  if (!code) return "";
  // #ifdef H5
  const origin = window.location.origin + window.location.pathname;
  return `${origin}#/pages/register/register?partner_code=${encodeURIComponent(code)}`;
  // #endif
  return `/pages/register/register?partner_code=${encodeURIComponent(code)}`;
});

const qrImage = computed(() => {
  return `https://api.qrserver.com/v1/create-qr-code/?size=220x220&data=${encodeURIComponent(registerLink.value)}`;
});

const rateText = computed(() => `${Math.round(Number(profile.value?.commission_rate || 0) * 100)}%`);

const loadPage = async () => {
  profile.value = await http.getPartnerProfile();
  if (profile.value) {
    const [attrRes, financeRes, commissionRes, withdrawalRes] = await Promise.all([
      http.getPartnerAttributions("?page=1&page_size=20"),
      http.getPartnerFinanceSummary(),
      http.getPartnerCommissions("?page=1&page_size=20"),
      http.getPartnerWithdrawals("?page=1&page_size=20")
    ]);
    records.value = attrRes.items || [];
    finance.value = financeRes || {};
    commissions.value = commissionRes.items || [];
    withdrawals.value = withdrawalRes.items || [];
  } else {
    records.value = [];
    finance.value = {};
    commissions.value = [];
    withdrawals.value = [];
  }
};

const goApply = () => goPage("/pages/partner/apply");
const typeText = (value) => ({ maternal_store: "孕婴店老板", business_agent: "工商代办专员" }[value] || value);
const statusText = (value) => ({ pending: "待审核", approved: "已通过", rejected: "已拒绝" }[value] || value);
const money = (value) => Number(value || 0).toFixed(2);
const formatTime = (value) => (value ? String(value).replace("T", " ").slice(0, 16) : "");
const copyText = (text, title) => {
  if (!text) return uni.showToast({ title: "暂无可复制内容", icon: "none" });
  uni.setClipboardData({ data: text, success: () => uni.showToast({ title }) });
};
const copyCode = () => copyText(profile.value?.partner_code || "", "已复制专属码");
const copyLink = () => copyText(registerLink.value, "已复制注册链接");
const submitWithdrawal = async () => {
  if (!withdrawForm.value.amount || !withdrawForm.value.account_name || !withdrawForm.value.account_no) {
    return uni.showToast({ title: "请填写提现信息", icon: "none" });
  }
  await http.createPartnerWithdrawal({ ...withdrawForm.value });
  uni.showToast({ title: "已提交提现" });
  withdrawForm.value = { amount: "", account_name: "", account_no: "", bank_name: "" };
  await loadPage();
};

onShow(loadPage);
</script>

<style scoped>
.page { min-height: 100vh; padding: 28rpx; background: #f6f7fb; box-sizing: border-box; }
.empty, .profile, .qr-card, .stats, .records, .withdraw { background: #fff; border-radius: 12rpx; box-sizing: border-box; }
.empty { padding: 70rpx 30rpx; text-align: center; }
.empty-title { color: #111827; font-size: 34rpx; font-weight: 800; margin-bottom: 28rpx; }
.profile { display: flex; align-items: center; justify-content: space-between; gap: 20rpx; padding: 30rpx; }
.title { color: #111827; font-size: 38rpx; font-weight: 800; }
.sub { margin-top: 8rpx; color: #64748b; font-size: 25rpx; }
.qr-card { margin-top: 22rpx; padding: 30rpx; text-align: center; }
.qr-title { color: #111827; font-size: 30rpx; font-weight: 800; }
.qr { width: 300rpx; height: 300rpx; margin: 26rpx auto 0; display: block; }
.qr.locked { display: flex; align-items: center; justify-content: center; background: #f1f5f9; color: #64748b; }
.code { margin-top: 20rpx; color: #0f172a; font-size: 28rpx; font-weight: 700; }
.actions { display: grid; grid-template-columns: 1fr 1fr; gap: 18rpx; margin-top: 24rpx; }
.primary, .secondary, .btn { height: 76rpx; line-height: 76rpx; border-radius: 8rpx; font-size: 27rpx; }
.primary, .btn { background: #111827; color: #fff; }
.secondary { background: #e2e8f0; color: #111827; }
.stats { display: grid; grid-template-columns: 1fr 1fr; margin-top: 22rpx; padding: 26rpx 0; row-gap: 22rpx; }
.stat { text-align: center; }
.value { color: #111827; font-size: 38rpx; font-weight: 800; }
.label { margin-top: 8rpx; color: #64748b; font-size: 24rpx; }
.records { margin-top: 22rpx; padding: 28rpx; }
.withdraw { margin-top: 22rpx; padding: 28rpx; }
.section-title { color: #111827; font-size: 31rpx; font-weight: 800; }
.input { height: 78rpx; border-bottom: 1px solid #edf2f7; font-size: 27rpx; }
.full { width: 100%; margin-top: 24rpx; }
.empty-line { padding: 50rpx 0; color: #94a3b8; text-align: center; }
.record { display: flex; justify-content: space-between; align-items: center; gap: 18rpx; padding: 22rpx 0; border-bottom: 1px solid #edf2f7; }
.name { color: #1f2937; font-size: 28rpx; font-weight: 700; }
.time { margin-top: 6rpx; color: #94a3b8; font-size: 23rpx; }
.tag { flex-shrink: 0; padding: 7rpx 16rpx; border-radius: 999rpx; background: #dcfce7; color: #15803d; font-size: 23rpx; }
.money { flex-shrink: 0; color: #111827; font-size: 28rpx; font-weight: 800; }
</style>
