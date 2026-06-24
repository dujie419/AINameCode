<template>
  <view class="page">
    <view class="topbar">
      <view>
        <view class="title">专家审核</view>
        <view class="sub">审核用户提交的专家申请</view>
      </view>
      <picker mode="selector" :range="statusLabels" :value="statusIndex" @change="changeStatus">
        <view class="filter">{{ statusLabels[statusIndex] }}</view>
      </picker>
    </view>

    <view v-if="experts.length === 0" class="empty">暂无申请记录</view>

    <view class="expert-card" v-for="item in experts" :key="item.id">
      <view class="card-head">
        <view>
          <view class="name">{{ item.name }}</view>
          <view class="title-line">{{ item.title }}</view>
        </view>
        <text :class="['status', item.status]">{{ statusText(item.status) }}</text>
      </view>

      <view class="desc">{{ item.description }}</view>
      <view class="meta">用户ID：{{ item.user_id }} · 经验 {{ item.experience_years }} 年 · ￥{{ item.price }}</view>
      <view class="tags">
        <text class="tag" v-for="tag in item.tags" :key="tag">{{ tag }}</text>
      </view>

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
const experts = ref([]);
const loadingId = ref(0);

const loadExperts = async () => {
  try {
    const status = statusOptions[statusIndex.value];
    const res = await adminApi.experts({ page: 1, page_size: 50, status });
    experts.value = res.items || [];
  } catch (error) {
    console.error("加载专家申请失败", error);
  }
};

const changeStatus = (event) => {
  statusIndex.value = Number(event.detail.value);
  loadExperts();
};

const statusText = (status) => {
  return { pending: "待审核", approved: "已通过", rejected: "已拒绝" }[status] || status;
};

const approve = async (id) => {
  loadingId.value = id;
  try {
    await adminApi.approveExpert(id);
    uni.showToast({ title: "已通过" });
    await loadExperts();
  } catch (error) {
    console.error("通过专家失败", error);
  } finally {
    loadingId.value = 0;
  }
};

const reject = async (id) => {
  loadingId.value = id;
  try {
    await adminApi.rejectExpert(id);
    uni.showToast({ title: "已拒绝" });
    await loadExperts();
  } catch (error) {
    console.error("拒绝专家失败", error);
  } finally {
    loadingId.value = 0;
  }
};

onShow(loadExperts);
</script>

<style scoped>
.page { min-height: 100vh; padding: 30rpx; background: #f5f7fa; box-sizing: border-box; }
.topbar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 26rpx; }
.title { font-size: 42rpx; font-weight: 700; color: #111827; }
.sub { color: #6b7280; font-size: 24rpx; margin-top: 8rpx; }
.filter { background: #fff; border-radius: 8rpx; padding: 14rpx 22rpx; color: #111827; }
.empty { text-align: center; color: #6b7280; margin-top: 120rpx; }
.expert-card { background: #fff; border-radius: 10rpx; padding: 26rpx; margin-bottom: 20rpx; box-shadow: 0 4rpx 12rpx rgba(0,0,0,0.04); }
.card-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 20rpx; }
.name { font-size: 34rpx; font-weight: 700; color: #111827; }
.title-line, .meta { color: #6b7280; margin-top: 8rpx; font-size: 25rpx; }
.desc { color: #374151; line-height: 1.6; margin-top: 18rpx; }
.status { border-radius: 999rpx; padding: 6rpx 16rpx; font-size: 24rpx; white-space: nowrap; }
.status.pending { background: #fff7ed; color: #c2410c; }
.status.approved { background: #ecfdf5; color: #047857; }
.status.rejected { background: #fef2f2; color: #b91c1c; }
.tags { margin-top: 14rpx; }
.tag { display: inline-block; background: #eef2ff; color: #1f3a8a; padding: 6rpx 12rpx; border-radius: 6rpx; margin: 8rpx 8rpx 0 0; font-size: 24rpx; }
.actions { display: flex; gap: 18rpx; margin-top: 22rpx; }
.approve { margin: 0; flex: 1; background: #16a34a; color: #fff; border-radius: 8rpx; }
.reject { margin: 0; flex: 1; background: #ef4444; color: #fff; border-radius: 8rpx; }
</style>
