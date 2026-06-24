<template>
  <view class="page">
    <view class="detail" v-if="order.id">
      <view class="title">订单详情</view>
      <view class="line"><text>订单号</text><text>{{ order.order_no }}</text></view>
      <view class="line"><text>类型</text><text>{{ typeText(order.order_type) }}</text></view>
      <view class="line"><text>金额</text><text>¥{{ money(order.amount) }}</text></view>
      <view class="line"><text>状态</text><text>{{ statusText(order.status) }}</text></view>
      <view class="line"><text>创建时间</text><text>{{ order.created_at || '-' }}</text></view>
      <view class="line"><text>支付时间</text><text>{{ order.paid_at || '-' }}</text></view>
      <view class="line"><text>完成时间</text><text>{{ order.completed_at || '-' }}</text></view>

      <button v-if="order.status === 'pending'" class="primary" :loading="loading" @tap="pay">余额支付</button>
      <button v-if="order.status === 'pending'" class="secondary" :loading="loading" @tap="createChannelPayment">渠道支付</button>
      <button v-if="canConfirm" class="primary" :loading="loading" @tap="confirmExpertService">确认服务</button>
      <button v-if="canAfterSale" class="danger" :loading="loading" @tap="submitAfterSale">申请售后</button>

      <view v-if="payment.payment_no" class="payment">
        <view class="line"><text>支付单</text><text>{{ payment.payment_no }}</text></view>
        <view class="line"><text>支付地址</text><text>{{ payment.pay_url }}</text></view>
      </view>
    </view>

    <view v-if="isExpertOrder" class="panel">
      <view class="panel-title">专家回复</view>
      <view v-if="expertLoading" class="muted">专家服务信息加载中...</view>
      <view v-else-if="!expertOrder.id" class="muted">暂无专家服务信息</view>
      <view v-else>
        <view class="line"><text>专家订单</text><text>#{{ expertOrder.id }}</text></view>
        <view class="line"><text>服务状态</text><text>{{ statusText(expertOrder.status) }}</text></view>
        <view v-if="!hasReport" class="muted report-empty">{{ expertStatusTip }}</view>
        <view v-else class="report">
          <view class="report-block" v-if="expertOrder.report_summary">
            <view class="report-label">报告摘要</view>
            <view class="report-text">{{ expertOrder.report_summary }}</view>
          </view>
          <view class="report-block" v-if="expertOrder.report_analysis">
            <view class="report-label">专业分析</view>
            <view class="report-text">{{ expertOrder.report_analysis }}</view>
          </view>
          <view class="report-block" v-if="expertOrder.report_suggestions">
            <view class="report-label">优化建议</view>
            <view class="report-text">{{ expertOrder.report_suggestions }}</view>
          </view>
          <view class="line" v-if="expertOrder.report_url"><text>报告文件</text><text>{{ expertOrder.report_url }}</text></view>
          <view class="line" v-if="expertOrder.delivered_at"><text>交付时间</text><text>{{ expertOrder.delivered_at }}</text></view>
        </view>
      </view>
    </view>

    <view v-if="canReview" class="panel">
      <view class="panel-title">评价专家服务</view>
      <picker :range="ratingOptions" @change="changeRating">
        <view class="input">评分：{{ reviewForm.rating }} 星</view>
      </picker>
      <textarea class="textarea" v-model="reviewForm.content" placeholder="写下本次服务体验"></textarea>
      <button class="primary" :loading="loading" @tap="submitReview">提交评价</button>
    </view>

    <view v-if="canAfterSale" class="panel">
      <view class="panel-title">售后说明</view>
      <picker :range="afterSaleTypes" range-key="label" @change="changeAfterSaleType">
        <view class="input">类型：{{ currentAfterSaleType.label }}</view>
      </picker>
      <input class="input" v-model="afterSaleForm.reason" placeholder="售后原因" />
      <textarea class="textarea" v-model="afterSaleForm.description" placeholder="补充说明"></textarea>
    </view>
  </view>
</template>

<script setup>
import { onLoad, onShow } from "@dcloudio/uni-app";
import { computed, ref } from "vue";
import http from "@/http/http.js";

const id = ref(0);
const order = ref({});
const expertOrder = ref({});
const payment = ref({});
const loading = ref(false);
const expertLoading = ref(false);
const reviewForm = ref({ rating: 5, content: "" });
const afterSaleForm = ref({ request_type: "refund", reason: "", description: "" });
const ratingOptions = [1, 2, 3, 4, 5];
const afterSaleTypes = [
  { label: "退款", value: "refund" },
  { label: "重做报告", value: "redo" },
  { label: "投诉", value: "complaint" }
];
const currentAfterSaleType = computed(() => afterSaleTypes.find((item) => item.value === afterSaleForm.value.request_type) || afterSaleTypes[0]);
const isExpertOrder = computed(() => order.value.order_type === "expert_service" && order.value.related_id);
const canConfirm = computed(() => isExpertOrder.value && ["delivered", "settle_pending"].includes(order.value.status));
const canReview = computed(() => isExpertOrder.value && ["settled", "completed"].includes(order.value.status));
const canAfterSale = computed(() => isExpertOrder.value && ["paid", "processing", "delivered", "confirmed", "settle_pending"].includes(order.value.status));
const hasReport = computed(() => !!(expertOrder.value.report_summary || expertOrder.value.report_analysis || expertOrder.value.report_suggestions || expertOrder.value.report_url));
const expertStatusTip = computed(() => {
  if (order.value.status === "pending") {
    return "订单尚未支付，专家暂不能处理。";
  }
  if (["paid", "processing"].includes(order.value.status)) {
    return "专家正在处理服务，完成后会在这里展示报告。";
  }
  if (order.value.status === "after_sale") {
    return "当前服务处于售后处理中。";
  }
  return "专家暂未提交报告。";
});

const money = (value) => Number(value || 0).toFixed(2);
const typeText = (type) => ({ expert_service: "专家服务" }[type] || type);
const statusText = (status) => ({
  pending: "待支付",
  paid: "已支付",
  processing: "服务中",
  delivered: "已交付",
  confirmed: "已确认",
  settle_pending: "待结算",
  settled: "已结算",
  after_sale: "售后中",
  after_sale_approved: "已退款",
  after_sale_rejected: "售后驳回",
  refunded: "已退款"
}[status] || status);

const load = async () => {
  if (!id.value) {
    return;
  }
  order.value = await http.getUserOrderDetail(id.value);
  await loadExpertOrder();
};

const loadExpertOrder = async () => {
  expertOrder.value = {};
  if (!isExpertOrder.value) {
    return;
  }
  expertLoading.value = true;
  try {
    expertOrder.value = await http.getExpertOrder(order.value.related_id);
  } finally {
    expertLoading.value = false;
  }
};

const pay = async () => {
  loading.value = true;
  try {
    await http.payUserOrder(id.value);
    uni.showToast({ title: "支付成功" });
    await load();
  } finally {
    loading.value = false;
  }
};

const createChannelPayment = async () => {
  loading.value = true;
  try {
    payment.value = await http.createOrderPayment(id.value, "virtual");
    const paid = await http.virtualPay(payment.value.payment_no);
    payment.value = { ...payment.value, ...paid.payment };
    await load();
    uni.showToast({ title: "支付成功" });
  } finally {
    loading.value = false;
  }
};

const confirmExpertService = async () => {
  loading.value = true;
  try {
    await http.confirmExpertOrder(order.value.related_id);
    uni.showToast({ title: "服务已确认" });
    await load();
  } finally {
    loading.value = false;
  }
};

const changeRating = (e) => {
  reviewForm.value.rating = ratingOptions[e.detail.value];
};

const changeAfterSaleType = (e) => {
  afterSaleForm.value.request_type = afterSaleTypes[e.detail.value].value;
};

const submitReview = async () => {
  if (!reviewForm.value.content.trim()) {
    return uni.showToast({ title: "请填写评价内容", icon: "none" });
  }
  loading.value = true;
  try {
    await http.createExpertReview(order.value.related_id, reviewForm.value);
    uni.showToast({ title: "评价已提交" });
    await load();
  } finally {
    loading.value = false;
  }
};

const submitAfterSale = async () => {
  if (!afterSaleForm.value.reason.trim()) {
    return uni.showToast({ title: "请填写售后原因", icon: "none" });
  }
  loading.value = true;
  try {
    await http.createAfterSale(order.value.related_id, afterSaleForm.value);
    uni.showToast({ title: "售后申请已提交" });
    await load();
  } finally {
    loading.value = false;
  }
};

onLoad((query) => {
  id.value = Number(query.id || 0);
});

onShow(load);
</script>

<style scoped>
.page { min-height: 100vh; padding: 30rpx; background: #f5f7fa; box-sizing: border-box; }
.detail, .panel { background: #fff; border-radius: 12rpx; padding: 28rpx; margin-bottom: 22rpx; }
.title { font-size: 38rpx; font-weight: 700; margin-bottom: 22rpx; }
.panel-title { font-size: 30rpx; font-weight: 700; color: #111827; margin-bottom: 18rpx; }
.line { display: flex; justify-content: space-between; gap: 24rpx; padding: 20rpx 0; border-bottom: 1px solid #edf0f5; font-size: 26rpx; color: #374151; }
.line text:last-child { text-align: right; word-break: break-all; }
.muted { color: #6b7280; font-size: 26rpx; line-height: 1.6; }
.report-empty { margin-top: 12rpx; }
.report { margin-top: 8rpx; }
.report-block { padding: 18rpx 0; border-bottom: 1px solid #edf0f5; }
.report-label { color: #111827; font-size: 27rpx; font-weight: 800; }
.report-text { color: #374151; font-size: 26rpx; line-height: 1.7; margin-top: 10rpx; }
.input { min-height: 84rpx; line-height: 84rpx; border-bottom: 1px solid #edf0f5; font-size: 28rpx; color: #374151; }
.textarea { width: 100%; height: 160rpx; background: #f9fafb; border-radius: 8rpx; padding: 18rpx; box-sizing: border-box; margin-top: 18rpx; font-size: 28rpx; }
.primary, .secondary, .danger { margin-top: 30rpx; background: #111827; color: #fff; border-radius: 10rpx; }
.secondary { background: #eef2ff; color: #1f3a8a; }
.danger { background: #fff1f2; color: #dc2626; }
.payment { margin-top: 20rpx; background: #f9fafb; border-radius: 8rpx; padding: 12rpx; }
</style>
