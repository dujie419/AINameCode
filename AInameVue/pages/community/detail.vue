<template>
  <view class="page">
    <view class="card">
      <view class="head">
        <view class="title">{{ post.title }}</view>
        <view class="type-tag">{{ post.naming_type || "企业名" }}</view>
      </view>
      <view class="desc">{{ post.description }}</view>
      <view v-if="post.name_record_id" class="record">命名记录 #{{ post.name_record_id }}</view>
    </view>

    <view class="cand" v-for="candidate in post.candidates" :key="candidate.id">
      <view>
        <view class="name">{{ candidate.name }}</view>
        <view v-if="candidate.moral" class="candidate-desc">寓意：{{ candidate.moral }}</view>
        <view v-if="candidate.reference" class="candidate-desc">出处：{{ candidate.reference }}</view>
        <view v-if="candidate.domain" class="candidate-desc">域名：{{ candidate.domain }}</view>
        <view class="votes">{{ candidate.vote_count }} 票</view>
      </view>
      <button
        size="mini"
        :loading="votingCandidateId === candidate.id"
        :disabled="isVoting || hasVoted"
        @tap="vote(candidate.id)"
      >
        {{ votedCandidateId === candidate.id ? "已投票" : "投票" }}
      </button>
    </view>

    <button class="btn" :loading="resultLoading" @tap="loadResult">查看结果</button>
    <view v-if="result.winner" class="result">
      当前领先：{{ result.winner }}（{{ result.vote_count }}票）
    </view>
  </view>
</template>

<script setup>
import { onLoad } from "@dcloudio/uni-app";
import { ref } from "vue";
import http from "@/http/http.js";

const id = ref("");
const post = ref({ candidates: [] });
const result = ref({});
const isVoting = ref(false);
const votingCandidateId = ref(null);
const votedCandidateId = ref(null);
const hasVoted = ref(false);
const resultLoading = ref(false);

const load = async () => {
  post.value = await http.getCommunityPostDetail(id.value);
};

const vote = async (candidateId) => {
  if (isVoting.value || hasVoted.value) return;
  isVoting.value = true;
  votingCandidateId.value = candidateId;
  try {
    await http.voteCommunityPost(id.value, { candidate_id: candidateId });
    votedCandidateId.value = candidateId;
    hasVoted.value = true;
    uni.showToast({ title: "投票成功" });
    await load();
    await loadResult();
  } catch (error) {
    console.error("投票失败", error);
    await load();
  } finally {
    isVoting.value = false;
    votingCandidateId.value = null;
  }
};

const loadResult = async () => {
  resultLoading.value = true;
  try {
    result.value = await http.getCommunityResult(id.value);
  } catch (error) {
    console.error("加载投票结果失败", error);
  } finally {
    resultLoading.value = false;
  }
};

onLoad(async (query) => {
  id.value = query.id;
  try {
    await load();
  } catch (error) {
    console.error("加载投票详情失败", error);
    uni.showToast({ title: "投票详情加载失败", icon: "none" });
  }
});
</script>

<style scoped>
.page {
  min-height: 100vh;
  padding: 24rpx;
  background: #f5f7fa;
}

.card,
.cand {
  background: #fff;
  border-radius: 10rpx;
  padding: 24rpx;
  margin-bottom: 18rpx;
}

.cand {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 18rpx;
}

.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18rpx;
}

.title,
.name {
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
.votes,
.record,
.candidate-desc {
  color: #6b7280;
  margin-top: 8rpx;
}

.btn {
  background: #111827;
  color: #fff;
}

.result {
  margin-top: 20rpx;
}
</style>
