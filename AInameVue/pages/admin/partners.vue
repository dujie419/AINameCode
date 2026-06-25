<template>
  <view class="page">
    <view class="topbar">
      <view>
        <view class="title">合伙人审核</view>
        <view class="sub">审核渠道合伙人申请和专属码启用状态</view>
      </view>
      <picker mode="selector" :range="statusLabels" :value="statusIndex" @change="changeStatus">
        <view class="filter">{{ statusLabels[statusIndex] }}</view>
      </picker>
    </view>

    <view v-if="partners.length === 0" class="empty">暂无申请记录</view>

    <view class="card" v-for="item in partners" :key="item.id">
      <view class="card-head">
        <view>
          <view class="name">{{ item.name }}</view>
          <view class="type">{{ typeText(item.partner_type) }} · {{ item.company_name || "未填写机构" }}</view>
        </view>
        <text :class="['status', item.status]">{{ statusText(item.status) }}</text>
      </view>
      <view class="desc">{{ item.description || "无说明" }}</view>
      <view class="meta">用户ID：{{ item.user_id }} · 专属码：{{ item.partner_code }} · 注册 {{ item.register_count || 0 }}</view>
      <view class="meta">电话：{{ item.contact_phone || "--" }} · 佣金率：{{ rateText(item.commission_rate) }}</view>
      <view class="actions" v-if="item.status === 'pending'">
        <button size="mini" class="approve" :loading="loadingId === item.id" @tap="approve(item.id)">通过</button>
        <button size="mini" class="reject" :loading="loadingId === item.id" @tap="reject(item.id)">拒绝</button>
      </view>
    </view>
  </view>
</template>

<script setup>
import { onShow } from "@dcloudio/uni-app";
import { ref } from "vue";
import adminApi from "@/api/admin.js";

const statusOptions = ["pending", "approved", "rejected", ""];
const statusLabels = ["待审核", "已通过", "已拒绝", "全部"];
const statusIndex = ref(0);
const partners = ref([]);
const loadingId = ref(0);

const loadPartners = async () => {
  const status = statusOptions[statusIndex.value];
  const res = await adminApi.partners({ page: 1, page_size: 50, status });
  partners.value = res.items || [];
};

const changeStatus = (event) => {
  statusIndex.value = Number(event.detail.value);
  loadPartners();
};

const typeText = (value) => ({ maternal_store: "孕婴店老板", business_agent: "工商代办专员" }[value] || value);
const statusText = (value) => ({ pending: "待审核", approved: "已通过", rejected: "已拒绝" }[value] || value);
const rateText = (value) => `${Math.round(Number(value || 0) * 100)}%`;

const approve = async (id) => {
  loadingId.value = id;
  try {
    await adminApi.approvePartner(id);
    uni.showToast({ title: "已通过" });
    await loadPartners();
  } finally {
    loadingId.value = 0;
  }
};

const reject = async (id) => {
  loadingId.value = id;
  try {
    await adminApi.rejectPartner(id);
    uni.showToast({ title: "已拒绝" });
    await loadPartners();
  } finally {
    loadingId.value = 0;
  }
};

onShow(loadPartners);
</script>

<style scoped>
.page { min-height: 100vh; padding: 30rpx; background: #f5f7fa; box-sizing: border-box; }
.topbar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 26rpx; }
.title { font-size: 42rpx; font-weight: 800; color: #111827; }
.sub { color: #6b7280; font-size: 24rpx; margin-top: 8rpx; }
.filter { background: #fff; border-radius: 8rpx; padding: 14rpx 22rpx; color: #111827; }
.empty { text-align: center; color: #6b7280; margin-top: 120rpx; }
.card { background: #fff; border-radius: 10rpx; padding: 26rpx; margin-bottom: 20rpx; }
.card-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 20rpx; }
.name { font-size: 34rpx; font-weight: 800; color: #111827; }
.type, .meta { color: #6b7280; margin-top: 8rpx; font-size: 25rpx; }
.desc { color: #374151; line-height: 1.6; margin-top: 18rpx; }
.status { border-radius: 999rpx; padding: 6rpx 16rpx; font-size: 24rpx; white-space: nowrap; }
.status.pending { background: #fff7ed; color: #c2410c; }
.status.approved { background: #ecfdf5; color: #047857; }
.status.rejected { background: #fef2f2; color: #b91c1c; }
.actions { display: flex; gap: 18rpx; margin-top: 22rpx; }
.approve { margin: 0; flex: 1; background: #16a34a; color: #fff; border-radius: 8rpx; }
.reject { margin: 0; flex: 1; background: #ef4444; color: #fff; border-radius: 8rpx; }
</style>
