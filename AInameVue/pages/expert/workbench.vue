<template>
  <view class="page">
    <view class="header">
      <view>
        <view class="title">专家工作台</view>
        <view class="subtitle">处理订单并提交专业报告</view>
      </view>
      <picker :range="statusOptions" range-key="label" @change="changeStatus">
        <view class="filter">{{ currentStatus.label }}</view>
      </picker>
    </view>

    <EmptyState v-if="orders.length === 0" text="暂无专家订单" />

    <view class="order" v-for="item in orders" :key="item.id">
      <view class="order-top">
        <view>
          <view class="strong">专家订单 #{{ item.id }}</view>
          <view class="meta">用户ID：{{ item.user_id }} · 金额：¥{{ money(item.amount) }}</view>
        </view>
        <view :class="['status', item.status]">{{ statusText(item.status) }}</view>
      </view>

      <view class="meta" v-if="item.order_no">关联订单：{{ item.order_no }}</view>
      <view class="meta" v-if="item.name_record_id">命名记录ID：{{ item.name_record_id }}</view>
      <view v-if="item.status === 'pending'" class="notice">用户尚未支付，暂不能接单或交付报告。</view>
      <view class="report" v-if="item.report_summary || item.report_analysis || item.report_suggestions">
        <view class="report-title">已提交报告</view>
        <view class="report-text" v-if="item.report_summary">摘要：{{ item.report_summary }}</view>
        <view class="report-text" v-if="item.report_analysis">分析：{{ item.report_analysis }}</view>
        <view class="report-text" v-if="item.report_suggestions">建议：{{ item.report_suggestions }}</view>
      </view>

      <view v-if="canSubmitReport(item)" class="form">
        <textarea class="textarea" v-model="reports[item.id].summary" placeholder="报告摘要"></textarea>
        <textarea class="textarea" v-model="reports[item.id].analysis" placeholder="专业分析"></textarea>
        <textarea class="textarea" v-model="reports[item.id].suggestions" placeholder="优化建议"></textarea>
      </view>

      <view class="actions">
        <button v-if="item.status === 'paid'" size="mini" @tap="accept(item.id)">接单</button>
        <button
          v-if="canSubmitReport(item)"
          class="dark"
          size="mini"
          :loading="submittingId === item.id"
          @tap="submitReport(item.id)"
        >
          提交报告并交付
        </button>
        <button v-if="item.status === 'delivered' || item.status === 'settle_pending'" class="dark" size="mini" @tap="settle(item.id)">结算</button>
      </view>
    </view>

    <ExpertNavPane active="workbench" />
  </view>
</template>

<script setup>
import { onShow } from "@dcloudio/uni-app";
import { computed, reactive, ref } from "vue";
import http from "@/http/http.js";
import EmptyState from "@/components/EmptyState.vue";
import ExpertNavPane from "@/components/ExpertNavPane.vue";

const orders = ref([]);
const reports = reactive({});
const submittingId = ref(0);
const statusValue = ref("");
const statusOptions = [
  { label: "全部状态", value: "" },
  { label: "待接单", value: "paid" },
  { label: "服务中", value: "processing" },
  { label: "已交付", value: "delivered" },
  { label: "待结算", value: "settle_pending" },
  { label: "已结算", value: "settled" },
  { label: "售后中", value: "after_sale" }
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

const canSubmitReport = (item) => ["paid", "processing"].includes(item.status);

const ensureReportForm = (item) => {
  if (!reports[item.id]) {
    reports[item.id] = { summary: "", analysis: "", suggestions: "" };
  }
};

const loadOrders = async () => {
  const query = statusValue.value ? `?status=${statusValue.value}` : "";
  const res = await http.getExpertCenterOrders(query);
  orders.value = res.items || [];
  orders.value.forEach(ensureReportForm);
};

const changeStatus = (e) => {
  statusValue.value = statusOptions[e.detail.value].value;
  loadOrders();
};

const accept = async (id) => {
  await http.acceptExpertCenterOrder(id);
  uni.showToast({ title: "已接单" });
  await loadOrders();
};

const submitReport = async (id) => {
  const data = reports[id];
  if (!data.summary || !data.analysis || !data.suggestions) {
    return uni.showToast({ title: "请填写完整报告", icon: "none" });
  }
  submittingId.value = id;
  try {
    await http.submitExpertReport(id, data);
    reports[id] = { summary: "", analysis: "", suggestions: "" };
    uni.showToast({ title: "报告已提交" });
    await loadOrders();
  } finally {
    submittingId.value = 0;
  }
};

const settle = async (id) => {
  await http.settleExpertCenterOrder(id);
  uni.showToast({ title: "订单已结算" });
  await loadOrders();
};

onShow(loadOrders);
</script>

<style scoped>
.page { min-height: 100vh; padding: 30rpx 30rpx 152rpx; background: #f5f7fa; box-sizing: border-box; }
.header { display: flex; justify-content: space-between; align-items: center; gap: 20rpx; margin-bottom: 22rpx; }
.title { font-size: 38rpx; font-weight: 800; color: #111827; }
.subtitle { color: #6b7280; font-size: 24rpx; margin-top: 8rpx; }
.filter { min-width: 180rpx; text-align: center; background: #fff; border-radius: 10rpx; padding: 18rpx 22rpx; color: #111827; font-size: 26rpx; }
.order { background: #fff; border-radius: 12rpx; padding: 26rpx; margin-bottom: 22rpx; }
.order-top { display: flex; justify-content: space-between; align-items: flex-start; gap: 18rpx; }
.strong { font-weight: 800; font-size: 32rpx; color: #111827; }
.meta { color: #6b7280; margin-top: 10rpx; font-size: 24rpx; }
.notice { margin-top: 18rpx; padding: 18rpx; border-radius: 10rpx; background: #fff7ed; color: #c2410c; font-size: 25rpx; }
.status { flex-shrink: 0; border-radius: 999rpx; padding: 6rpx 14rpx; background: #eef2ff; color: #1f3a8a; font-size: 23rpx; }
.status.settled { background: #ecfdf5; color: #047857; }
.status.after_sale, .status.after_sale_approved { background: #fef2f2; color: #b91c1c; }
.report { margin-top: 18rpx; background: #f8fafc; border-radius: 10rpx; padding: 18rpx; }
.report-title { font-size: 26rpx; font-weight: 800; color: #111827; }
.report-text { color: #4b5563; font-size: 24rpx; line-height: 1.6; margin-top: 8rpx; }
.form { margin-top: 18rpx; }
.textarea { width: 100%; min-height: 120rpx; box-sizing: border-box; margin-top: 16rpx; padding: 18rpx; background: #f8fafc; border-radius: 8rpx; font-size: 26rpx; }
.actions { display: flex; gap: 14rpx; margin-top: 18rpx; flex-wrap: wrap; }
.actions button { margin: 0; background: #eef2ff; color: #1f3a8a; border-radius: 8rpx; }
.actions .dark { background: #111827; color: #fff; }
</style>
