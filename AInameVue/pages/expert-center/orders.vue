<template>
  <view class="page">
    <picker :range="statusOptions" range-key="label" @change="changeStatus">
      <view class="filter">{{ currentStatus.label }}</view>
    </picker>
    <view v-if="orders.length === 0" class="empty">暂无专家订单</view>
    <view class="order" v-for="item in orders" :key="item.id">
      <view class="top">
        <text class="strong">专家订单 #{{ item.id }}</text>
        <text :class="['status', item.status]">{{ statusText(item.status) }}</text>
      </view>
      <view class="meta">用户ID：{{ item.user_id }} · 订单金额：¥{{ money(item.amount) }}</view>
      <view class="meta">平台抽成：¥{{ money(item.platform_fee) }} · 专家收入：¥{{ money(item.expert_income) }}</view>
      <view v-if="item.settlement_due_at" class="meta">可结算时间：{{ item.settlement_due_at }}</view>
      <view class="actions">
        <button v-if="item.status === 'paid'" size="mini" @tap="accept(item.id)">接单</button>
        <button v-if="item.status === 'paid' || item.status === 'processing'" class="dark" size="mini" @tap="complete(item.id)">交付订单</button>
        <button v-if="item.status === 'delivered' || item.status === 'settle_pending'" class="dark" size="mini" @tap="settle(item.id)">结算</button>
      </view>
    </view>
  </view>
</template>

<script setup>
import { onShow } from "@dcloudio/uni-app";
import { computed, ref } from "vue";
import http from "@/http/http.js";

const orders = ref([]);
const statusValue = ref("");
const statusOptions = [
  { label: "全部状态", value: "" },
  { label: "待接单", value: "paid" },
  { label: "服务中", value: "processing" },
  { label: "已交付", value: "delivered" },
  { label: "待结算", value: "settle_pending" },
  { label: "已结算", value: "settled" },
  { label: "售后中", value: "after_sale" },
  { label: "已退款", value: "after_sale_approved" }
];
const currentStatus = computed(() => statusOptions.find((item) => item.value === statusValue.value) || statusOptions[0]);

const money = (value) => Number(value || 0).toFixed(2);
const statusText = (status) => ({
  pending: "待支付",
  paid: "待接单",
  processing: "服务中",
  delivered: "已交付",
  confirmed: "已确认",
  settle_pending: "待结算",
  settled: "已结算",
  after_sale: "售后中",
  after_sale_approved: "已退款",
  after_sale_rejected: "售后驳回"
}[status] || status);

const load = async () => {
  const query = statusValue.value ? `?status=${statusValue.value}` : "";
  const res = await http.getExpertCenterOrders(query);
  orders.value = res.items || [];
};

const changeStatus = (e) => {
  statusValue.value = statusOptions[e.detail.value].value;
  load();
};

const accept = async (id) => {
  await http.acceptExpertCenterOrder(id);
  uni.showToast({ title: "已接单" });
  await load();
};

const complete = async (id) => {
  await http.completeExpertCenterOrder(id);
  uni.showToast({ title: "订单已交付" });
  await load();
};

const settle = async (id) => {
  await http.settleExpertCenterOrder(id);
  uni.showToast({ title: "订单已结算" });
  await load();
};

onShow(load);
</script>

<style scoped>
.page { min-height: 100vh; padding: 30rpx; background: #f5f7fa; box-sizing: border-box; }
.filter, .order { background: #fff; border-radius: 12rpx; padding: 26rpx; margin-bottom: 18rpx; }
.filter { text-align: center; }
.top { display: flex; justify-content: space-between; align-items: center; gap: 18rpx; }
.strong { font-size: 30rpx; font-weight: 700; color: #111827; }
.status, .meta, .empty { color: #6b7280; font-size: 24rpx; }
.status { flex-shrink: 0; border-radius: 999rpx; padding: 6rpx 14rpx; background: #eef2ff; color: #1f3a8a; }
.status.settled { background: #ecfdf5; color: #047857; }
.status.after_sale, .status.after_sale_approved { background: #fef2f2; color: #b91c1c; }
.meta { margin-top: 12rpx; }
.actions { display: flex; gap: 14rpx; margin-top: 18rpx; flex-wrap: wrap; }
.actions button { margin: 0; background: #eef2ff; color: #1f3a8a; border-radius: 8rpx; }
.actions .dark { background: #111827; color: #fff; }
.empty { text-align: center; margin-top: 100rpx; }
</style>
