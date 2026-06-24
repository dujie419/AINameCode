<template>
  <view class="page">
    <view class="toolbar">
      <button size="mini" @tap="goBack">返回</button>
      <input class="input" v-model="filters.user_id" type="number" placeholder="用户ID" />
      <input class="input" v-model="filters.naming_type" placeholder="命名类型" />
    </view>
    <view class="filter-row">
      <input class="input" v-model="filters.keyword" placeholder="关键词" />
      <button size="mini" @tap="search">筛选</button>
    </view>

    <view v-if="records.length === 0" class="empty">暂无命名记录</view>
    <view v-for="item in records" :key="item.id" class="record-item">
      <view class="record-title">#{{ item.id }} · 用户 {{ item.user_id }} · {{ item.naming_type }} · {{ item.source_type }}</view>
      <view class="record-content">Thread: {{ item.thread_id }}</view>
      <view class="record-content">关键词：{{ item.keyword || item.surname || "-" }}</view>
      <view v-if="item.feedback" class="record-content">反馈：{{ item.feedback }}</view>
      <view class="candidate-row">
        <text class="candidate" v-for="candidate in item.candidates" :key="candidate.id">
          {{ candidate.name }}
        </text>
      </view>
      <view class="record-time">{{ item.created_at }}</view>
    </view>

    <view class="pager">
      <button size="mini" :disabled="page <= 1" @tap="prevPage">上一页</button>
      <text>{{ page }} / {{ totalPage }}</text>
      <button size="mini" :disabled="page >= totalPage" @tap="nextPage">下一页</button>
    </view>
  </view>
</template>

<script setup>
import { onShow } from "@dcloudio/uni-app";
import { computed, ref } from "vue";
import adminApi from "@/api/admin.js";
import { goPage } from "@/utils/router.js";

const records = ref([]);
const total = ref(0);
const page = ref(1);
const pageSize = ref(10);
const filters = ref({ user_id: "", naming_type: "", keyword: "" });
const totalPage = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)));

const goBack = () => {
  goPage("/pages/admin/index");
};

const loadRecords = async () => {
  const res = await adminApi.nameRecords({
    page: page.value,
    page_size: pageSize.value,
    ...filters.value
  });
  records.value = res.items || [];
  total.value = res.total || 0;
};

const search = () => {
  page.value = 1;
  loadRecords();
};

const prevPage = () => {
  if (page.value > 1) {
    page.value--;
    loadRecords();
  }
};

const nextPage = () => {
  if (page.value < totalPage.value) {
    page.value++;
    loadRecords();
  }
};

onShow(loadRecords);
</script>

<style scoped>
.page { min-height: 100vh; padding: 24rpx; background: #f5f7fa; box-sizing: border-box; }
.toolbar { display: grid; grid-template-columns: auto 1fr 1fr; gap: 16rpx; margin-bottom: 16rpx; align-items: center; }
.filter-row { display: grid; grid-template-columns: 1fr auto; gap: 16rpx; margin-bottom: 24rpx; }
.input { background: #fff; border-radius: 8rpx; padding: 20rpx; font-size: 26rpx; }
.empty { background: #fff; color: #6b7280; text-align: center; padding: 80rpx 20rpx; border-radius: 10rpx; }
.record-item { background: #fff; border-radius: 10rpx; padding: 24rpx; margin-bottom: 18rpx; }
.record-title { font-size: 28rpx; font-weight: 700; color: #111827; }
.record-content { color: #6b7280; font-size: 24rpx; margin-top: 10rpx; word-break: break-all; }
.candidate-row { display: flex; flex-wrap: wrap; gap: 10rpx; margin-top: 14rpx; }
.candidate { background: #eef2ff; color: #1f3a8a; border-radius: 6rpx; padding: 6rpx 12rpx; font-size: 24rpx; }
.record-time { color: #9ca3af; font-size: 22rpx; margin-top: 14rpx; }
.pager { display: flex; align-items: center; justify-content: center; gap: 24rpx; padding: 30rpx 0; color: #4b5563; }
</style>
