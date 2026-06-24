<template>
  <view class="page">
    <MainNavPane active="community" />

    <view class="bar">
      <button size="mini" @tap="goCreate">发起投票</button>
      <button size="mini" @tap="setSort('hot')">热门</button>
      <button size="mini" @tap="setSort('latest')">最新</button>
    </view>

    <EmptyState v-if="posts.length === 0" text="暂无投票" />

    <view class="post" v-for="post in posts" :key="post.id" @tap="goDetail(post.id)">
      <view class="post-head">
        <view class="title">{{ post.title }}</view>
        <view class="type-tag">{{ post.naming_type || "企业名" }}</view>
      </view>
      <view class="desc">{{ post.description }}</view>
      <view class="meta">
        {{ post.candidates.length }} 个候选
        <text v-if="post.name_record_id"> · 记录 #{{ post.name_record_id }}</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { onShow } from "@dcloudio/uni-app";
import { ref } from "vue";
import http from "@/http/http.js";
import { goPage } from "@/utils/router.js";
import EmptyState from "@/components/EmptyState.vue";
import MainNavPane from "@/components/MainNavPane.vue";

const posts = ref([]);
const sort = ref("latest");

const loadPosts = async () => {
  const res = await http.getCommunityPosts(`?sort=${sort.value}`);
  posts.value = res.items || [];
};

const setSort = async (value) => {
  sort.value = value;
  await loadPosts();
};

const goCreate = () => {
  goPage("/pages/community/create");
};

const goDetail = (id) => {
  goPage(`/pages/community/detail?id=${id}`);
};

onShow(loadPosts);
</script>

<style scoped>
.page {
  min-height: 100vh;
  padding: 24rpx 24rpx 152rpx;
  background: #f5f7fa;
  box-sizing: border-box;
}

.bar {
  display: flex;
  gap: 12rpx;
}

.post {
  background: #fff;
  border-radius: 10rpx;
  padding: 24rpx;
  margin-top: 18rpx;
}

.post-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18rpx;
}

.title {
  flex: 1;
  font-weight: 700;
  font-size: 32rpx;
}

.type-tag {
  flex-shrink: 0;
  padding: 6rpx 16rpx;
  border-radius: 999rpx;
  background: #e0f2fe;
  color: #0284c7;
  font-size: 22rpx;
  font-weight: 700;
}

.desc,
.meta {
  color: #6b7280;
  margin-top: 8rpx;
}
</style>
