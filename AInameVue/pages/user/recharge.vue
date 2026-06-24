<template>
  <view class="page">
    <view class="panel">
      <view class="title">余额充值</view>
      <view class="hint">当前为虚拟充值，后续可替换为支付宝或微信真实支付。</view>
      <input class="input" v-model.number="amount" type="number" placeholder="请输入充值金额" />
      <view class="input readonly">支付方式：虚拟支付</view>
      <button class="primary" :loading="loading" @tap="recharge">立即充值</button>
      <button class="secondary" @tap="openMembership">开通会员</button>
    </view>

    <view v-if="payment.payment_no" class="panel">
      <view class="result-title">充值支付单</view>
      <view class="line"><text>支付单号</text><text>{{ payment.payment_no }}</text></view>
      <view class="line"><text>渠道</text><text>{{ providerText(payment.provider) }}</text></view>
      <view class="line"><text>金额</text><text>￥{{ payment.amount }}</text></view>
      <view class="line"><text>状态</text><text>{{ statusText(payment.status) }}</text></view>
      <view class="pay-url">{{ payment.pay_url }}</view>
      <button v-if="payment.status !== 'paid'" class="secondary" @tap="refreshPayment">刷新支付状态</button>
    </view>
  </view>
</template>

<script setup>
import { onUnmounted, ref } from "vue";
import http from "@/http/http.js";
import { goPage } from "@/utils/router.js";

const amount = ref(100);
const loading = ref(false);
const payment = ref({});
let timer = null;

const providerText = (value) => ({ virtual: "虚拟支付", alipay: "支付宝", wechat: "微信支付" }[value] || value);
const statusText = (value) => ({ pending: "待支付", paid: "已支付", failed: "支付失败" }[value] || value || "-");

const stopPolling = () => {
  if (timer) {
    clearInterval(timer);
    timer = null;
  }
};

const refreshPayment = async () => {
  if (!payment.value.payment_no) return;
  const res = await http.getPaymentOrder(payment.value.payment_no);
  payment.value = { ...payment.value, ...res };
  if (payment.value.status === "paid") {
    stopPolling();
    uni.showToast({ title: "充值成功" });
  }
};

const startPolling = () => {
  stopPolling();
  timer = setInterval(refreshPayment, 1500);
};

const recharge = async () => {
  if (!amount.value || Number(amount.value) <= 0) {
    return uni.showToast({ title: "请输入正确金额", icon: "none" });
  }
  loading.value = true;
  try {
    const order = await http.createRecharge({ amount: amount.value, provider: "virtual" });
    payment.value = order;
    startPolling();
    const paid = await http.virtualPay(order.payment_no);
    payment.value = { ...payment.value, ...paid.payment };
    await refreshPayment();
  } finally {
    loading.value = false;
  }
};

const openMembership = () => goPage("/pages/user/membership");

onUnmounted(stopPolling);
</script>

<style scoped>
.page { min-height: 100vh; padding: 30rpx; background: #f5f7fa; box-sizing: border-box; }
.panel { background: #fff; border-radius: 12rpx; padding: 28rpx; margin-bottom: 24rpx; }
.title, .result-title { font-size: 38rpx; font-weight: 700; color: #111827; margin-bottom: 18rpx; }
.hint { color: #6b7280; font-size: 24rpx; line-height: 1.6; margin-bottom: 16rpx; }
.input { height: 88rpx; border-bottom: 1px solid #edf0f5; font-size: 30rpx; line-height: 88rpx; }
.readonly { color: #4b5563; }
.primary, .secondary { margin-top: 30rpx; background: #111827; color: #fff; border-radius: 10rpx; }
.secondary { background: #eef2ff; color: #1f3a8a; }
.line { display: flex; justify-content: space-between; gap: 20rpx; padding: 16rpx 0; color: #374151; font-size: 26rpx; }
.line text:last-child { text-align: right; word-break: break-all; }
.pay-url { margin-top: 18rpx; background: #f9fafb; color: #6b7280; padding: 20rpx; border-radius: 8rpx; word-break: break-all; font-size: 24rpx; }
</style>
