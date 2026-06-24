<template>
  <view class="page">
    <view class="filters">
      <picker :range="statusOptions" range-key="label" @change="changeStatus">
        <view class="filter">{{ currentStatus.label }}</view>
      </picker>
      <picker :range="typeOptions" range-key="label" @change="changeType">
        <view class="filter">{{ currentType.label }}</view>
      </picker>
    </view>
    <view v-if="orders.length === 0" class="empty">暂无订单</view>
    <view class="order" v-for="item in orders" :key="item.id" @tap="openDetail(item.id)">
      <view class="top">
        <text class="no">{{ item.order_no }}</text>
        <text class="status">{{ statusText(item.status) }}</text>
      </view>
      <view class="meta">{{ typeText(item.order_type) }} · ¥{{ item.amount }}</view>
      <view v-if="isDeliveredExpertOrder(item)" class="report-tip">专家报告已送达，点击查看</view>
      <button v-if="item.status === 'pending'" class="pay" size="mini" @tap.stop="pay(item.id)">余额支付</button>
    </view>
  </view>
</template>

<script setup>
import { onShow } from "@dcloudio/uni-app";
import { computed, ref } from "vue";
import http from "@/http/http.js";
import { goPage } from "@/utils/router.js";

const orders = ref([]);
const statusValue = ref("");
const typeValue = ref("");
const statusOptions = [
  { label: "全部状态", value: "" },
  { label: "待支付", value: "pending" },
  { label: "已支付", value: "paid" },
  { label: "处理中", value: "processing" },
  { label: "已交付", value: "delivered" },
  { label: "待结算", value: "settle_pending" },
  { label: "已结算", value: "settled" },
  { label: "已完成", value: "completed" },
  { label: "已取消", value: "cancelled" },
  { label: "已退款", value: "refunded" }
];
const typeOptions = [
  { label: "全部类型", value: "" },
  { label: "AI命名订单", value: "ai_name" },
  { label: "品牌视觉订单", value: "brand_visual" },
  { label: "专家服务订单", value: "expert_service" },
  { label: "API套餐订单", value: "api_package" }
];
const currentStatus = computed(() => statusOptions.find((item) => item.value === statusValue.value) || statusOptions[0]);
const currentType = computed(() => typeOptions.find((item) => item.value === typeValue.value) || typeOptions[0]);
const statusText = (value) => (statusOptions.find((item) => item.value === value) || {}).label || value;
const typeText = (value) => (typeOptions.find((item) => item.value === value) || {}).label || value;
const isDeliveredExpertOrder = (item) => item.order_type === "expert_service" && ["delivered", "settle_pending", "settled", "completed"].includes(item.status);

const load = async () => {
  const query = [];
  if (statusValue.value) query.push(`status=${statusValue.value}`);
  if (typeValue.value) query.push(`order_type=${typeValue.value}`);
  const res = await http.getUserOrders(query.length ? `?${query.join("&")}` : "");
  orders.value = res.items || [];
};

const changeStatus = (e) => {
  statusValue.value = statusOptions[e.detail.value].value;
  load();
};

const changeType = (e) => {
  typeValue.value = typeOptions[e.detail.value].value;
  load();
};

const pay = async (id) => {
  await http.payUserOrder(id);
  uni.showToast({ title: "支付成功" });
  await load();
};

const openDetail = (id) => goPage(`/pages/user/order-detail?id=${id}`);

onShow(load);
</script>

<style scoped>
.page { min-height: 100vh; padding: 30rpx; background: #f5f7fa; box-sizing: border-box; }
.filters { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16rpx; margin-bottom: 20rpx; }
.filter { background: #fff; border-radius: 10rpx; padding: 22rpx; text-align: center; color: #111827; }
.order { background: #fff; border-radius: 12rpx; padding: 26rpx; margin-bottom: 18rpx; }
.top { display: flex; justify-content: space-between; gap: 20rpx; }
.no { font-weight: 700; color: #111827; font-size: 26rpx; word-break: break-all; }
.status { color: #1f6feb; font-size: 24rpx; flex-shrink: 0; }
.meta, .empty { color: #6b7280; font-size: 24rpx; margin-top: 12rpx; }
.report-tip { margin-top: 14rpx; color: #16a3e6; font-size: 25rpx; font-weight: 700; }
.pay { margin: 18rpx 0 0; background: #111827; color: #fff; border-radius: 8rpx; }
.empty { text-align: center; margin-top: 100rpx; }
</style>
