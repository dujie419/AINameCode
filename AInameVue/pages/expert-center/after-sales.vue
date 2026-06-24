<template>
  <view class="page">
    <view class="header">
      <view>
        <view class="title">售后管理</view>
        <view class="subtitle">查看专家订单售后申请</view>
      </view>
      <picker :range="statusOptions" range-key="label" @change="changeStatus">
        <view class="filter">{{ currentStatus.label }}</view>
      </picker>
    </view>

    <EmptyState v-if="items.length === 0" text="暂无售后申请" />

    <view class="sale" v-for="item in items" :key="item.id">
      <view class="top">
        <view>
          <view class="strong">{{ item.request_no }}</view>
          <view class="meta">专家订单 #{{ item.expert_order_id }} · 用户ID：{{ item.user_id }}</view>
        </view>
        <view :class="['status', item.status]">{{ statusText(item.status) }}</view>
      </view>
      <view class="detail">
        <view class="line"><text>类型</text><text>{{ typeText(item.request_type) }}</text></view>
        <view class="line"><text>原因</text><text>{{ item.reason || '-' }}</text></view>
        <view class="line"><text>说明</text><text>{{ item.description || '-' }}</text></view>
        <view class="line"><text>处理结果</text><text>{{ item.resolution || '待平台处理' }}</text></view>
        <view class="line"><text>申请时间</text><text>{{ item.created_at || '-' }}</text></view>
        <view class="line"><text>处理时间</text><text>{{ item.handled_at || '-' }}</text></view>
      </view>
    </view>

    <ExpertNavPane active="afterSales" />
  </view>
</template>

<script setup>
import { onShow } from "@dcloudio/uni-app";
import { computed, ref } from "vue";
import http from "@/http/http.js";
import EmptyState from "@/components/EmptyState.vue";
import ExpertNavPane from "@/components/ExpertNavPane.vue";

const items = ref([]);
const statusValue = ref("");
const statusOptions = [
  { label: "全部状态", value: "" },
  { label: "待处理", value: "pending" },
  { label: "处理中", value: "processing" },
  { label: "已同意", value: "approved" },
  { label: "已驳回", value: "rejected" },
  { label: "已关闭", value: "closed" }
];
const currentStatus = computed(() => statusOptions.find((item) => item.value === statusValue.value) || statusOptions[0]);

const statusText = (status) => ({
  pending: "待处理",
  processing: "处理中",
  approved: "已同意",
  rejected: "已驳回",
  closed: "已关闭"
}[status] || status);
const typeText = (type) => ({ refund: "退款", redo: "重做报告", complaint: "投诉" }[type] || type);

const load = async () => {
  const query = statusValue.value ? `?status=${statusValue.value}` : "";
  const res = await http.getExpertCenterAfterSales(query);
  items.value = res.items || [];
};

const changeStatus = (e) => {
  statusValue.value = statusOptions[e.detail.value].value;
  load();
};

onShow(load);
</script>

<style scoped>
.page { min-height: 100vh; padding: 30rpx 30rpx 152rpx; background: #f5f7fa; box-sizing: border-box; }
.header { display: flex; justify-content: space-between; align-items: center; gap: 20rpx; margin-bottom: 22rpx; }
.title { font-size: 38rpx; font-weight: 800; color: #111827; }
.subtitle { color: #6b7280; font-size: 24rpx; margin-top: 8rpx; }
.filter { min-width: 180rpx; text-align: center; background: #fff; border-radius: 10rpx; padding: 18rpx 22rpx; color: #111827; font-size: 26rpx; }
.sale { background: #fff; border-radius: 12rpx; padding: 26rpx; margin-bottom: 22rpx; }
.top { display: flex; justify-content: space-between; align-items: flex-start; gap: 18rpx; }
.strong { font-weight: 800; font-size: 30rpx; color: #111827; word-break: break-all; }
.meta { color: #6b7280; margin-top: 10rpx; font-size: 24rpx; }
.status { flex-shrink: 0; border-radius: 999rpx; padding: 6rpx 14rpx; background: #eef2ff; color: #1f3a8a; font-size: 23rpx; }
.status.approved { background: #ecfdf5; color: #047857; }
.status.rejected { background: #fef2f2; color: #b91c1c; }
.detail { margin-top: 18rpx; background: #f8fafc; border-radius: 10rpx; padding: 8rpx 18rpx; }
.line { display: flex; justify-content: space-between; gap: 24rpx; padding: 14rpx 0; border-bottom: 1px solid #edf0f5; color: #374151; font-size: 25rpx; }
.line:last-child { border-bottom: none; }
.line text:first-child { color: #6b7280; flex-shrink: 0; }
.line text:last-child { text-align: right; word-break: break-all; }
</style>
