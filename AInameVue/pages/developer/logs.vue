<template>
  <view class="app-page">
    <AppTopbar title="调用记录" subtitle="接口、耗时、Token 和费用">
      <template #action>
      <button size="mini" class="ghost" @tap="goHome">返回</button>
      </template>
    </AppTopbar>

    <EmptyState v-if="logs.length === 0" text="暂无调用记录" />

    <view class="log-item" v-for="item in logs" :key="item.id">
      <view class="row">
        <text class="endpoint">{{ item.endpoint }}</text>
        <text class="status">{{ item.status_code }}</text>
      </view>
      <view class="meta">{{ item.created_at }}</view>
      <view class="metrics">
        <text>{{ item.response_time }}ms</text>
        <text>{{ item.tokens }} Token</text>
        <text>¥{{ item.cost }}</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { onShow } from "@dcloudio/uni-app";
import { ref } from "vue";
import http from "@/http/http.js";
import { goPage } from "@/utils/router.js";
import AppTopbar from "@/components/AppTopbar.vue";
import EmptyState from "@/components/EmptyState.vue";

const logs = ref([]);

const goHome = () => goPage("/pages/developer/index");

const loadLogs = async () => {
  const res = await http.getDeveloperLogs("?page=1&page_size=50");
  logs.value = res.items || [];
};

onShow(loadLogs);
</script>

<style scoped>
.ghost { margin: 0; background: #fff; color: #111827; border-radius: 8rpx; }
.log-item { background: #fff; border-radius: 10rpx; padding: 26rpx; margin-bottom: 18rpx; }
.row { display: flex; justify-content: space-between; align-items: center; }
.endpoint { color: #111827; font-size: 30rpx; font-weight: 700; }
.status { color: #047857; font-size: 24rpx; }
.meta { color: #6b7280; font-size: 24rpx; margin-top: 10rpx; }
.metrics { display: flex; justify-content: space-between; margin-top: 18rpx; color: #374151; font-size: 24rpx; }
</style>
