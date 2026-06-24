<template>
  <view class="page">
    <MainNavPane active="expert" />

    <view class="top">
      <input class="input" v-model="keyword" placeholder="搜索专家/标签" />
      <button size="mini" class="search-btn" @tap="loadExperts">搜索</button>
    </view>

    <view class="quick">
      <button class="quick-btn" @tap="goApply">申请成为专家</button>
    </view>

    <view class="item" v-for="e in experts" :key="e.id" @tap="goDetail(e.id)">
      <view class="name">{{ e.name }}</view>
      <view class="title">{{ e.title }}</view>
      <view class="meta">评分 {{ e.rating }} · ￥{{ e.price }}</view>
      <view>
        <text class="tag" v-for="t in e.tags" :key="t">{{ t }}</text>
      </view>
      <view class="hint">点击查看详情并下单</view>
    </view>

    <view v-if="experts.length === 0" class="empty">
      <view>暂无已审核专家</view>
      <button class="empty-btn" @tap="goApply">先申请成为专家</button>
    </view>
  </view>
</template>

<script setup>
import { onShow } from "@dcloudio/uni-app";
import { ref } from "vue";
import http from "@/http/http.js";
import { goPage } from "@/utils/router.js";
import MainNavPane from "@/components/MainNavPane.vue";

const experts = ref([]);
const keyword = ref("");

const open = (url) => goPage(url);

const loadExperts = async () => {
  try {
    const q = keyword.value ? `?keyword=${encodeURIComponent(keyword.value)}` : "";
    const res = await http.getExperts(q);
    experts.value = res.items || [];
  } catch (error) {
    console.error("加载专家列表失败", error);
  }
};

const goDetail = (id) => open(`/pages/expert/detail?id=${id}`);
const goApply = () => open("/pages/expert/apply");

onShow(loadExperts);
</script>

<style scoped>
.page { min-height: 100vh; padding: 24rpx 24rpx 152rpx; background: #f5f7fa; box-sizing: border-box; }
.top { display: flex; gap: 12rpx; }
.input { flex: 1; background: #fff; border-radius: 8rpx; padding: 18rpx; }
.search-btn { margin: 0; background: #111827; color: #fff; }
.quick { margin-top: 18rpx; }
.quick-btn { margin: 0; background: #eef2ff; color: #1f3a8a; border-radius: 10rpx; }
.item { background: #fff; border-radius: 10rpx; padding: 24rpx; margin-top: 18rpx; box-shadow: 0 4rpx 12rpx rgba(0,0,0,0.04); }
.name { font-size: 32rpx; font-weight: 700; }
.title, .meta, .hint { color: #6b7280; margin-top: 8rpx; }
.hint { font-size: 24rpx; }
.tag { display: inline-block; background: #eef2ff; color: #1f3a8a; padding: 6rpx 12rpx; border-radius: 6rpx; margin: 12rpx 8rpx 0 0; }
.empty { text-align: center; color: #6b7280; margin-top: 80rpx; }
.empty-btn { width: 320rpx; margin-top: 24rpx; background: #111827; color: #fff; border-radius: 10rpx; }
</style>
