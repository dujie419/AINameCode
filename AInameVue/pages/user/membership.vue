<template>
  <view class="page">
    <view class="summary">
      <view>
        <view class="label">会员状态</view>
        <view class="status">{{ current.status === "active" ? "已开通" : "未开通" }}</view>
      </view>
      <view v-if="current.expires_at" class="expire">到期：{{ current.expires_at }}</view>
    </view>

    <view class="plans">
      <view v-for="plan in plans" :key="plan.id" :class="['plan', selectedId === plan.id ? 'active' : '']" @tap="selectedId = plan.id">
        <view>
          <view class="plan-name">{{ plan.name }}</view>
          <view class="desc">{{ plan.description }}</view>
          <view class="duration">{{ plan.duration_days }} 天</view>
        </view>
        <view class="price">￥{{ plan.price }}</view>
      </view>
    </view>

    <button class="primary" :disabled="!selectedId" :loading="loading" @tap="buyMembership">立即开通</button>

    <view v-if="payment.payment_no" class="result">
      <view class="result-title">会员支付单</view>
      <view class="line"><text>支付单号</text><text>{{ payment.payment_no }}</text></view>
      <view class="line"><text>金额</text><text>￥{{ payment.amount }}</text></view>
      <view class="line"><text>状态</text><text>{{ statusText(payment.status) }}</text></view>
    </view>
  </view>
</template>

<script setup>
import { onShow } from "@dcloudio/uni-app";
import { onUnmounted, ref } from "vue";
import http from "@/http/http.js";

const plans = ref([]);
const current = ref({ status: "inactive" });
const selectedId = ref(0);
const payment = ref({});
const loading = ref(false);
let timer = null;

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
    current.value = await http.getCurrentMembership();
    uni.showToast({ title: "会员已开通" });
  }
};

const load = async () => {
  const [planList, membership] = await Promise.all([http.getMembershipPlans(), http.getCurrentMembership()]);
  plans.value = planList || [];
  current.value = membership || { status: "inactive" };
  if (!selectedId.value && plans.value.length > 0) {
    selectedId.value = plans.value[0].id;
  }
};

const buyMembership = async () => {
  if (!selectedId.value) return;
  loading.value = true;
  try {
    const order = await http.createMembershipOrder({ plan_id: selectedId.value, provider: "virtual" });
    payment.value = order;
    stopPolling();
    timer = setInterval(refreshPayment, 1500);
    const paid = await http.virtualPay(order.payment_no);
    payment.value = { ...payment.value, ...paid.payment };
    await refreshPayment();
  } finally {
    loading.value = false;
  }
};

onShow(load);
onUnmounted(stopPolling);
</script>

<style scoped>
.page { min-height: 100vh; padding: 30rpx; background: #f5f7fa; box-sizing: border-box; }
.summary, .result { background: #fff; border-radius: 12rpx; padding: 28rpx; margin-bottom: 24rpx; }
.summary { display: flex; justify-content: space-between; gap: 20rpx; align-items: center; }
.label, .desc, .duration, .expire { color: #6b7280; font-size: 24rpx; }
.status { color: #111827; font-size: 40rpx; font-weight: 800; margin-top: 8rpx; }
.plans { display: grid; gap: 20rpx; }
.plan { background: #fff; border: 2rpx solid transparent; border-radius: 12rpx; padding: 28rpx; display: flex; justify-content: space-between; gap: 24rpx; align-items: center; }
.plan.active { border-color: #1f3a8a; background: #f8fbff; }
.plan-name { color: #111827; font-size: 32rpx; font-weight: 800; margin-bottom: 10rpx; }
.duration { margin-top: 10rpx; }
.price { color: #111827; font-size: 36rpx; font-weight: 800; white-space: nowrap; }
.primary { margin-top: 30rpx; background: #111827; color: #fff; border-radius: 10rpx; }
.result-title { font-size: 34rpx; font-weight: 800; color: #111827; margin-bottom: 18rpx; }
.line { display: flex; justify-content: space-between; gap: 20rpx; padding: 16rpx 0; color: #374151; font-size: 26rpx; }
.line text:last-child { text-align: right; word-break: break-all; }
</style>
