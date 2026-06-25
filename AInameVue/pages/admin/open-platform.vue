<template>
  <view class="page">
    <view class="topbar">
      <view>
        <view class="title">开放平台管理</view>
        <view class="sub">开发者审核、Key、日志、计费</view>
      </view>
      <button size="mini" class="ghost" @tap="loadData">刷新</button>
    </view>

    <view class="tabs">
      <view :class="['tab', activeTab === 'developers' ? 'active' : '']" @tap="activeTab = 'developers'">开发者</view>
      <view :class="['tab', activeTab === 'keys' ? 'active' : '']" @tap="activeTab = 'keys'">API Key</view>
      <view :class="['tab', activeTab === 'logs' ? 'active' : '']" @tap="activeTab = 'logs'">调用日志</view>
      <view :class="['tab', activeTab === 'plans' ? 'active' : '']" @tap="activeTab = 'plans'">套餐</view>
    </view>

    <view v-if="activeTab === 'developers'">
      <view class="item" v-for="item in developers" :key="item.id">
        <view>
          <view class="name">{{ item.company_name }}</view>
          <view class="meta">{{ item.contact_name }} · {{ item.email }}</view>
          <view class="meta">状态：{{ item.status }}</view>
        </view>
        <view class="actions" v-if="item.status === 'pending'">
          <button size="mini" class="ok" @tap="approveDeveloper(item.id)">通过</button>
          <button size="mini" class="danger" @tap="rejectDeveloper(item.id)">拒绝</button>
        </view>
      </view>
    </view>

    <view v-if="activeTab === 'keys'">
      <view class="item" v-for="item in apiKeys" :key="item.id">
        <view>
          <view class="name">{{ item.name }}</view>
          <view class="meta">{{ item.api_key_prefix }}*** · {{ item.status }}</view>
          <view class="meta">额度：{{ item.used_quota }} / {{ item.quota }}</view>
        </view>
      </view>
    </view>

    <view v-if="activeTab === 'logs'">
      <view class="item" v-for="item in logs" :key="item.id">
        <view>
          <view class="name">{{ item.endpoint }}</view>
          <view class="meta">{{ item.tokens }} Token · {{ item.response_time }}ms · {{ item.status_code }}</view>
          <view class="meta">{{ item.created_at }}</view>
        </view>
      </view>
    </view>

    <view v-if="activeTab === 'plans'">
      <view class="item" v-for="item in plans" :key="item.id">
        <view>
          <view class="name">{{ item.name }} · ¥{{ money(item.price) }}</view>
          <view class="meta">额度：{{ quotaText(item.quota) }}</view>
          <view class="meta">{{ item.description }}</view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { onShow } from "@dcloudio/uni-app";
import { ref, watch } from "vue";
import adminApi from "@/api/admin.js";

const activeTab = ref("developers");
const developers = ref([]);
const apiKeys = ref([]);
const logs = ref([]);
const plans = ref([]);

const loadData = async () => {
  if (activeTab.value === "developers") {
    const res = await adminApi.developers({ page: 1, page_size: 50 });
    developers.value = res.items || [];
  }
  if (activeTab.value === "keys") {
    const res = await adminApi.apiKeys({ page: 1, page_size: 50 });
    apiKeys.value = res.items || [];
  }
  if (activeTab.value === "logs") {
    const res = await adminApi.apiUsageLogs({ page: 1, page_size: 50 });
    logs.value = res.items || [];
  }
  if (activeTab.value === "plans") {
    const res = await adminApi.plans({ page: 1, page_size: 50 });
    plans.value = res.items || [];
  }
};

const approveDeveloper = async (id) => {
  await adminApi.approveDeveloper(id);
  await loadData();
};

const rejectDeveloper = async (id) => {
  await adminApi.rejectDeveloper(id);
  await loadData();
};

const money = (value) => {
  const amount = Number(value || 0);
  return Number.isInteger(amount) ? String(amount) : amount.toFixed(2);
};

const quotaText = (value) => {
  const quota = Number(value || 0);
  return quota > 0 ? String(quota) : "不限量";
};

watch(activeTab, loadData);
onShow(loadData);
</script>

<style scoped>
.page { min-height: 100vh; padding: 30rpx; background: #f5f7fa; box-sizing: border-box; }
.topbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24rpx; }
.title { font-size: 42rpx; font-weight: 700; color: #111827; }
.sub, .meta { color: #6b7280; font-size: 24rpx; margin-top: 8rpx; }
.ghost { margin: 0; background: #fff; color: #111827; border-radius: 8rpx; }
.tabs { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12rpx; margin-bottom: 22rpx; }
.tab { text-align: center; background: #fff; color: #374151; border-radius: 8rpx; padding: 18rpx 8rpx; font-size: 24rpx; }
.tab.active { background: #111827; color: #fff; }
.item { display: flex; justify-content: space-between; align-items: center; background: #fff; border-radius: 10rpx; padding: 24rpx; margin-bottom: 18rpx; }
.name { color: #111827; font-size: 30rpx; font-weight: 700; }
.actions { display: flex; gap: 12rpx; }
.ok { margin: 0; background: #ecfdf5; color: #047857; border-radius: 8rpx; }
.danger { margin: 0; background: #fff1f2; color: #dc2626; border-radius: 8rpx; }
</style>
