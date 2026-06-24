<template>
  <view class="page">
    <view class="summary">
      <view class="label">可提现余额</view>
      <view class="amount">¥{{ money(profile.available_balance) }}</view>
      <view class="subline">冻结中：¥{{ money(profile.frozen_balance) }}</view>
      <input class="input" v-model.number="withdrawForm.amount" type="number" placeholder="提现金额" />
      <input class="input" v-model="withdrawForm.account_name" placeholder="收款人姓名" />
      <input class="input" v-model="withdrawForm.account_no" placeholder="收款账号" />
      <input class="input" v-model="withdrawForm.bank_name" placeholder="开户行，可选" />
      <button class="primary" :loading="withdrawing" @tap="withdraw">申请提现</button>
    </view>

    <view class="section-title">收入明细</view>
    <view v-if="records.length === 0" class="empty">暂无收入明细</view>
    <view v-for="item in records" :key="item.id" class="record">
      <view class="top">
        <text class="strong">订单 #{{ item.order_id }}</text>
        <text :class="['badge', item.status]">{{ statusText(item.status) }}</text>
      </view>
      <view class="money-line">实际收入 ¥{{ money(item.actual_income) }}</view>
      <view class="meta">订单收入：¥{{ money(item.amount) }} · 平台抽成：¥{{ money(item.platform_fee) }}</view>
      <view class="meta">创建时间：{{ item.created_at || '-' }}</view>
      <view v-if="item.reverse_reason" class="meta danger">冲销原因：{{ item.reverse_reason }}</view>
    </view>

    <view class="section-title">提现记录</view>
    <view v-if="withdrawals.length === 0" class="empty compact">暂无提现记录</view>
    <view v-for="item in withdrawals" :key="item.id" class="record">
      <view class="top">
        <text class="strong">{{ item.withdrawal_no }}</text>
        <text :class="['badge', item.status]">{{ withdrawalText(item.status) }}</text>
      </view>
      <view class="money-line">提现金额 ¥{{ money(item.amount) }}</view>
      <view class="meta">账号：{{ item.account_name }} · {{ item.bank_name || '未填写开户行' }}</view>
      <view class="meta">申请时间：{{ item.created_at || '-' }}</view>
      <view v-if="item.payment_trade_no" class="meta">打款流水：{{ item.payment_trade_no }}</view>
      <view v-if="item.reason" class="meta danger">原因：{{ item.reason }}</view>
    </view>
  </view>
</template>

<script setup>
import { onShow } from "@dcloudio/uni-app";
import { ref } from "vue";
import http from "@/http/http.js";

const profile = ref({});
const records = ref([]);
const withdrawals = ref([]);
const withdrawing = ref(false);
const withdrawForm = ref({ amount: "", account_name: "", account_no: "", bank_name: "" });

const money = (value) => Number(value || 0).toFixed(2);
const statusText = (status) => ({
  settle_pending: "待结算",
  settled: "已结算",
  reversed: "已冲销",
  clawback_pending: "待追扣"
}[status] || status);
const withdrawalText = (status) => ({
  pending: "审核中",
  paid: "已打款",
  rejected: "已拒绝"
}[status] || status);

const load = async () => {
  profile.value = await http.getExpertCenterProfile();
  const income = await http.getExpertCenterIncome();
  const withdrawalRes = await http.getExpertWithdrawals();
  records.value = income.items || [];
  withdrawals.value = withdrawalRes.items || [];
};

const withdraw = async () => {
  if (!withdrawForm.value.amount || !withdrawForm.value.account_name || !withdrawForm.value.account_no) {
    return uni.showToast({ title: "请填写提现信息", icon: "none" });
  }
  withdrawing.value = true;
  try {
    await http.createExpertWithdrawal(withdrawForm.value);
    uni.showToast({ title: "提现申请已提交" });
    withdrawForm.value = { amount: "", account_name: "", account_no: "", bank_name: "" };
    await load();
  } finally {
    withdrawing.value = false;
  }
};

onShow(load);
</script>

<style scoped>
.page { min-height: 100vh; padding: 30rpx; background: #f5f7fa; box-sizing: border-box; }
.summary, .record { background: #fff; border-radius: 12rpx; padding: 26rpx; margin-bottom: 18rpx; }
.label, .meta, .empty, .subline { color: #6b7280; font-size: 24rpx; margin-top: 12rpx; }
.amount { font-size: 46rpx; font-weight: 800; color: #111827; margin-top: 10rpx; }
.input { border-bottom: 1px solid #edf0f5; height: 80rpx; font-size: 28rpx; }
.primary { margin-top: 26rpx; background: #111827; color: #fff; border-radius: 10rpx; }
.section-title { font-size: 30rpx; font-weight: 700; color: #111827; margin: 28rpx 0 16rpx; }
.top { display: flex; justify-content: space-between; align-items: center; gap: 20rpx; }
.strong { font-size: 30rpx; font-weight: 700; color: #111827; word-break: break-all; }
.money-line { color: #16a34a; font-size: 32rpx; font-weight: 800; margin-top: 14rpx; }
.badge { flex-shrink: 0; border-radius: 999rpx; padding: 6rpx 14rpx; background: #eef2ff; color: #1f3a8a; font-size: 23rpx; }
.badge.settled, .badge.paid { background: #ecfdf5; color: #047857; }
.badge.reversed, .badge.rejected, .danger { color: #b91c1c; }
.badge.reversed, .badge.rejected { background: #fef2f2; }
.empty { text-align: center; margin-top: 100rpx; }
.empty.compact { margin-top: 20rpx; }
</style>
