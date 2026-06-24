<template>
  <view class="page">
    <picker mode="selector" :range="categoryOptions" @change="changeCategory">
      <view class="field picker-field">投票类型：{{ form.naming_type }}</view>
    </picker>
    <view v-if="form.name_record_id" class="source-tip">已关联命名记录 #{{ form.name_record_id }}，发布时以后端记录候选名为准</view>
    <input class="field input-field" v-model="form.title" placeholder="标题，例如：帮我选一个AI公司名称" />
    <textarea class="field textarea-field" v-model="form.description" placeholder="描述，例如：做AI硬件创业"></textarea>
    <textarea class="field textarea-field candidates" v-model="candidateText" placeholder="候选名称，每行一个"></textarea>
    <button class="btn" :loading="loading" @tap="submit">发布投票</button>
  </view>
</template>

<script setup>
import { onLoad } from "@dcloudio/uni-app";
import { ref } from "vue";
import http from "@/http/http.js";
import { goPage } from "@/utils/router.js";

const categoryOptions = ["企业名", "人名", "宠物名"];
const form = ref({ title: "", description: "", naming_type: "企业名", name_record_id: "" });
const candidateText = ref("");
const loading = ref(false);

onLoad((query) => {
  if (query.category && categoryOptions.includes(decodeURIComponent(query.category))) {
    form.value.naming_type = decodeURIComponent(query.category);
  }
  if (query.name_record_id) {
    form.value.name_record_id = decodeURIComponent(query.name_record_id);
  }
  if (query.title) {
    form.value.title = decodeURIComponent(query.title);
  }
  if (query.description) {
    form.value.description = decodeURIComponent(query.description);
  }
  if (query.candidates) {
    candidateText.value = decodeURIComponent(query.candidates);
  }
});

const changeCategory = (event) => {
  form.value.naming_type = categoryOptions[event.detail.value];
};

const submit = async () => {
  const candidates = candidateText.value.split("\n").map((x) => x.trim()).filter(Boolean);
  if (!form.value.name_record_id && candidates.length < 2) {
    return uni.showToast({ title: "至少填写两个候选名称", icon: "none" });
  }
  if (!form.value.title.trim()) {
    return uni.showToast({ title: "请填写投票标题", icon: "none" });
  }

  loading.value = true;
  uni.showLoading({ title: "发布中..." });
  try {
    await http.createCommunityPost({
      ...form.value,
      name_record_id: form.value.name_record_id ? Number(form.value.name_record_id) : null,
      candidates
    });
    uni.showToast({ title: "发布成功" });
    goPage("/pages/community/index");
  } catch (error) {
    console.error("发布投票失败", error);
  } finally {
    loading.value = false;
    uni.hideLoading();
  }
};
</script>

<style scoped>
.page { min-height: 100vh; padding: 30rpx; background: #f5f7fa; box-sizing: border-box; }
.field { width: 100%; box-sizing: border-box; background: #fff; border-radius: 8rpx; padding: 20rpx; margin-bottom: 18rpx; color: #111827; font-size: 28rpx; line-height: 1.5; }
.picker-field { min-height: 88rpx; display: flex; align-items: center; }
.input-field { height: 88rpx; line-height: 48rpx; }
.source-tip { color: #2563eb; font-size: 24rpx; margin: 0 0 18rpx; }
.textarea-field { height: 150rpx; min-height: 150rpx; }
.candidates { min-height: 240rpx; }
.btn { background: #1f6feb; color: #fff; border-radius: 10rpx; }
</style>
