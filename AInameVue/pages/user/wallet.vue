<template>
  <view class="page">
    <view class="summary">
      <view class="label">当前余额</view>
      <view class="amount">￥{{ balance }}</view>
      <view class="actions">
        <button class="primary" @tap="openPage('/pages/user/recharge')">余额充值</button>
        <button class="secondary" @tap="openPage('/pages/user/membership')">开通会员</button>
      </view>
    </view>
    <view v-if="transactions.length === 0" class="empty">暂无余额流水</view>
    <view v-for="item in transactions" :key="item.id" class="row">
      <view>
        <view class="type">{{ typeText(item.transaction_type) }}</view>
        <view class="desc">{{ item.description }}</view>
      </view>
      <view :class="['money', Number(item.amount) >= 0 ? 'plus' : 'minus']">{{ item.amount }}</view>
    </view>
  </view>
</template>

<script setup>
import { onShow } from "@dcloudio/uni-app";
import { ref } from "vue";
import http from "@/http/http.js";
import { goPage } from "@/utils/router.js";

const balance = ref("0.00");
const transactions = ref([]);
const map = { recharge: "充值", pay: "支付", refund: "退款", expert_income: "专家收入" };
const typeText = (value) => map[value] || value;
const openPage = (url) => goPage(url);

const load = async () => {
  const b = await http.getUserBalance();
  const t = await http.getWalletTransactions();
  balance.value = b.balance;
  transactions.value = t.items || [];
};

onShow(load);
</script>

<style scoped>
.page { min-height: 100vh; padding: 30rpx; background: #f5f7fa; box-sizing: border-box; }
.summary, .row { background: #fff; border-radius: 12rpx; padding: 28rpx; margin-bottom: 20rpx; }
.label, .desc, .empty { color: #6b7280; font-size: 24rpx; }
.amount { font-size: 48rpx; font-weight: 800; margin: 8rpx 0 22rpx; }
.actions { display: grid; grid-template-columns: 1fr 1fr; gap: 16rpx; }
.primary, .secondary { margin: 0; border-radius: 10rpx; }
.primary { background: #111827; color: #fff; }
.secondary { background: #eef2ff; color: #1f3a8a; }
.row { display: flex; justify-content: space-between; align-items: center; gap: 24rpx; }
.type { font-size: 30rpx; font-weight: 700; color: #111827; }
.money { font-size: 30rpx; font-weight: 700; }
.plus { color: #16a34a; }
.minus { color: #dc2626; }
.empty { text-align: center; margin-top: 100rpx; }
</style>
