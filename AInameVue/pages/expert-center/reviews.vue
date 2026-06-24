<template>
  <view class="page">
    <view class="header">
      <view>
        <view class="title">评价管理</view>
        <view class="subtitle">查看用户评价并回复</view>
      </view>
    </view>

    <EmptyState v-if="reviews.length === 0" text="暂无评价" />

    <view class="review" v-for="item in reviews" :key="item.id">
      <view class="top">
        <view>
          <view class="strong">订单 #{{ item.expert_order_id }}</view>
          <view class="stars">{{ starText(item.rating) }}</view>
        </view>
        <view class="status">{{ item.status }}</view>
      </view>
      <view class="content">{{ item.content || '用户未填写评价内容' }}</view>
      <view class="meta">用户ID：{{ item.user_id }} · {{ item.created_at || '-' }}</view>

      <view v-if="item.reply" class="reply">
        <view class="reply-title">我的回复</view>
        <view class="reply-text">{{ item.reply }}</view>
        <view class="meta" v-if="item.replied_at">回复时间：{{ item.replied_at }}</view>
      </view>

      <textarea
        v-else
        class="textarea"
        v-model="replyForms[item.id]"
        placeholder="输入回复内容"
      ></textarea>
      <button
        v-if="!item.reply"
        class="primary"
        size="mini"
        :loading="replyingId === item.id"
        @tap="reply(item.id)"
      >
        回复评价
      </button>
    </view>

    <ExpertNavPane active="reviews" />
  </view>
</template>

<script setup>
import { onShow } from "@dcloudio/uni-app";
import { reactive, ref } from "vue";
import http from "@/http/http.js";
import EmptyState from "@/components/EmptyState.vue";
import ExpertNavPane from "@/components/ExpertNavPane.vue";

const reviews = ref([]);
const replyForms = reactive({});
const replyingId = ref(0);

const starText = (rating) => "★".repeat(Number(rating || 0)) + "☆".repeat(5 - Number(rating || 0));

const load = async () => {
  const res = await http.getExpertCenterReviews();
  reviews.value = res.items || [];
  reviews.value.forEach((item) => {
    if (!replyForms[item.id]) {
      replyForms[item.id] = "";
    }
  });
};

const reply = async (id) => {
  const text = (replyForms[id] || "").trim();
  if (!text) {
    return uni.showToast({ title: "请填写回复内容", icon: "none" });
  }
  replyingId.value = id;
  try {
    await http.replyExpertReview(id, { reply: text });
    replyForms[id] = "";
    uni.showToast({ title: "已回复" });
    await load();
  } finally {
    replyingId.value = 0;
  }
};

onShow(load);
</script>

<style scoped>
.page { min-height: 100vh; padding: 30rpx 30rpx 152rpx; background: #f5f7fa; box-sizing: border-box; }
.header { margin-bottom: 22rpx; }
.title { font-size: 38rpx; font-weight: 800; color: #111827; }
.subtitle { color: #6b7280; font-size: 24rpx; margin-top: 8rpx; }
.review { background: #fff; border-radius: 12rpx; padding: 26rpx; margin-bottom: 22rpx; }
.top { display: flex; justify-content: space-between; align-items: flex-start; gap: 18rpx; }
.strong { font-weight: 800; font-size: 30rpx; color: #111827; }
.stars { color: #f59e0b; margin-top: 8rpx; font-size: 28rpx; letter-spacing: 0; }
.status { flex-shrink: 0; border-radius: 999rpx; padding: 6rpx 14rpx; background: #ecfdf5; color: #047857; font-size: 23rpx; }
.content { margin-top: 18rpx; color: #374151; font-size: 28rpx; line-height: 1.6; }
.meta { color: #6b7280; margin-top: 10rpx; font-size: 24rpx; }
.reply { margin-top: 18rpx; padding: 18rpx; background: #f8fafc; border-radius: 10rpx; }
.reply-title { color: #111827; font-size: 26rpx; font-weight: 800; }
.reply-text { color: #374151; font-size: 26rpx; line-height: 1.6; margin-top: 8rpx; }
.textarea { width: 100%; min-height: 130rpx; box-sizing: border-box; margin-top: 18rpx; padding: 18rpx; background: #f8fafc; border-radius: 8rpx; font-size: 26rpx; }
.primary { margin: 18rpx 0 0; background: #111827; color: #fff; border-radius: 8rpx; }
</style>
