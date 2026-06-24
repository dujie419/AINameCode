<template>
  <view class="page">
    <view class="card">
      <view class="name">{{ expert.name }}</view>
      <view class="title">{{ expert.title }}</view>
      <view class="desc">{{ expert.description }}</view>
      <view class="meta">
        经验 {{ expert.experience_years }} 年 · 评分 {{ expert.rating }} · ¥{{ expert.price }}
      </view>
      <button class="btn" @tap="goOrder">购买专家服务</button>
    </view>
  </view>
</template>

<script setup>
import { onLoad } from "@dcloudio/uni-app";
import { ref } from "vue";
import http from "@/http/http.js";
import { goPage } from "@/utils/router.js";

const expert = ref({});
const id = ref("");

const goOrder = () => {
  goPage(`/pages/expert/order?expert_id=${id.value}`);
};

onLoad(async (query) => {
  id.value = query.id;
  expert.value = await http.getExpertDetail(id.value);
});
</script>

<style scoped>
.page {
  min-height: 100vh;
  padding: 30rpx;
  background: #f5f7fa;
}

.card {
  background: #fff;
  border-radius: 10rpx;
  padding: 30rpx;
}

.name {
  font-size: 40rpx;
  font-weight: 700;
}

.title,
.meta {
  color: #6b7280;
  margin-top: 12rpx;
}

.desc {
  line-height: 1.7;
  margin-top: 24rpx;
}

.btn {
  background: #1f6feb;
  color: #fff;
  margin-top: 36rpx;
  border-radius: 10rpx;
}
</style>
