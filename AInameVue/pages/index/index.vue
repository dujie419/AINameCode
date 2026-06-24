<template>
  <view class="container">
    <view class="top-actions">
      <button size="mini" class="logout-btn" @tap.stop="logout">退出登录</button>
    </view>

    <view class="tabs">
      <view
        v-for="item in categories"
        :key="item"
        :class="['tab', formData.category === item ? 'active' : '']"
        @tap="switchCategory(item)"
      >
        {{ item }}
      </view>
    </view>

    <view class="upload-section" v-if="formData.category === '企业名'">
      <view class="upload-tip">有企业命名规范？让 AI 学习你的专属标准</view>
      <button size="mini" @tap="handleUploadDocs">上传专属知识库 TXT/PDF</button>
    </view>

    <view class="form-group">
      <input
        v-if="formData.category === '人名'"
        class="input-box"
        v-model="formData.surname"
        placeholder="请输入姓氏，例如：张"
      />

      <picker
        v-if="formData.category === '人名'"
        mode="selector"
        :range="genderOptions"
        @change="e => formData.gender = genderOptions[e.detail.value]"
      >
        <view class="input-box">性别倾向：{{ formData.gender }}</view>
      </picker>

      <picker mode="selector" :range="lengthOptions" @change="e => formData.length = lengthOptions[e.detail.value]">
        <view class="input-box">字数要求：{{ formData.length }}</view>
      </picker>

      <textarea class="textarea-box" v-model="formData.other" placeholder="核心诉求"></textarea>
    </view>

    <button class="btn-primary" :loading="loading" @tap="handleGenerate">开始智能起名</button>

    <view class="result-box" v-if="names.length > 0">
      <view class="result-title">为您生成的专属方案：</view>
      <view class="name-card" v-for="(item, index) in names" :key="index">
        <view class="name-header">
          <text class="name-text">{{ item.name }}</text>
          <text v-if="item.domain" class="domain-tag">{{ item.domain }} {{ item.domain_status }}</text>
        </view>
        <view class="name-detail"><text class="label">出处：</text>{{ item.reference }}</view>
        <view class="name-detail"><text class="label">寓意：</text>{{ item.moral }}</view>
        <view class="result-actions">
          <button v-if="canCreateVisual" class="brand-btn" size="mini" @tap="goBrandVisual(item)">
            {{ visualButtonText }}
          </button>
          <button v-if="canUseExpert" class="brand-btn light" size="mini" @tap="goExpert">找专家精批</button>
          <button v-if="canCreateVote" class="brand-btn light" size="mini" @tap="goCommunityCreate">发布投票</button>
        </view>
      </view>

      <view class="feedback-box">
        <textarea class="textarea-box" v-model="feedbackText" placeholder="对结果不满意？请输入修改意见"></textarea>
        <button class="btn-secondary" :loading="loading" @tap="handleFeedback">基于意见重新生成</button>
      </view>
    </view>

    <view class="home-tabbar">
      <view class="home-tab-item home-active">
        <view class="home-tab-icon home-home-icon"></view>
        <view class="home-tab-text">首页</view>
      </view>
      <view class="home-tab-item" @tap="goExpert">
        <view class="home-tab-icon home-expert-icon"></view>
        <view class="home-tab-text">专家</view>
      </view>
      <view class="home-tab-item" @tap="goCommunity">
        <view class="home-tab-icon home-cart-icon"></view>
        <view class="home-tab-text">灵感池</view>
      </view>
      <view class="home-tab-item" @tap="goUserCenter">
        <view class="home-tab-icon home-user-icon"></view>
        <view class="home-tab-text">个人中心</view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from "vue";
import http from "@/http/http.js";
import { goPage } from "@/utils/router.js";

const categories = ["人名", "企业名", "宠物名"];
const genderOptions = ["不限", "男", "女"];
const lengthOptions = ["不限", "单字", "两字", "多字"];

const createCategoryForm = (category) => ({
  category,
  surname: "",
  gender: "不限",
  length: "不限",
  other: "",
  exclude: []
});

const categoryDrafts = ref({
  人名: createCategoryForm("人名"),
  企业名: createCategoryForm("企业名"),
  宠物名: createCategoryForm("宠物名")
});

const formData = ref({ ...categoryDrafts.value["人名"] });
const loading = ref(false);
const names = ref([]);
const threadId = ref("");
const latestNameRecordId = ref("");
const feedbackText = ref("");

const canCreateVisual = computed(() => formData.value.category !== "宠物名");
const canUseExpert = computed(() => formData.value.category !== "宠物名");
const canCreateVote = computed(() => formData.value.category !== "人名");
const visualButtonText = computed(() => formData.value.category === "人名" ? "生成名片方案" : "生成品牌视觉");

const switchCategory = (cat) => {
  if (formData.value.category === cat) return;

  categoryDrafts.value[formData.value.category] = { ...formData.value };
  const nextForm = categoryDrafts.value[cat] || createCategoryForm(cat);
  formData.value = {
    ...nextForm,
    category: cat,
    surname: cat === "人名" ? nextForm.surname : "",
    gender: cat === "人名" ? nextForm.gender : "不限"
  };
  names.value = [];
  threadId.value = "";
  latestNameRecordId.value = "";
  feedbackText.value = "";
  uni.removeStorageSync("latest_name_record_id");
};

const goExpert = () => goPage("/pages/expert/index");
const goCommunity = () => goPage("/pages/community/index");
const goUserCenter = () => goPage("/pages/user/center");

const clearLoginState = () => {
  uni.removeStorageSync("token");
  uni.removeStorageSync("user");
  uni.removeStorageSync("admin_token");
  uni.removeStorageSync("admin_role");
};

const logout = () => {
  clearLoginState();
  uni.showToast({ title: "已退出登录", icon: "success" });
  setTimeout(() => {
    goPage("/pages/login/login", { relaunch: true });
  }, 300);
};

const goBrandVisual = (item) => {
  const query = [
    `name=${encodeURIComponent(item.name || "")}`,
    `industry=${encodeURIComponent(formData.value.category === "人名" ? "个人名片" : (formData.value.other || formData.value.category || ""))}`,
    `meaning=${encodeURIComponent(item.moral || "")}`,
    `mode=${encodeURIComponent(formData.value.category === "人名" ? "card" : "brand")}`
  ].join("&");
  goPage(`/pages/brand/visual-generate?${query}`);
};

const goCommunityCreate = () => {
  const candidateNames = names.value.map((item) => item.name).filter(Boolean).join("\n");
  if (!candidateNames) {
    return uni.showToast({ title: "请先生成候选名称", icon: "none" });
  }
  const titleText = `帮我选一个${formData.value.category}`;
  const descriptionText = formData.value.other || `从这组${formData.value.category}里选出更合适的方案`;
  const query = [
    `category=${encodeURIComponent(formData.value.category)}`,
    `name_record_id=${encodeURIComponent(latestNameRecordId.value || "")}`,
    `title=${encodeURIComponent(titleText)}`,
    `description=${encodeURIComponent(descriptionText)}`,
    `candidates=${encodeURIComponent(candidateNames)}`
  ].join("&");
  goPage(`/pages/community/create?${query}`);
};

const handleUploadDocs = () => {
  uni.chooseFile({
    count: 1,
    type: "all",
    extension: [".txt", ".pdf"],
    success: async (res) => {
      const tempFilePath = res.tempFiles[0].path;
      uni.showLoading({ title: "知识库解析中..." });
      try {
        await http.uploadKnowledge(tempFilePath);
        uni.showToast({ title: "知识库学习完成", icon: "success" });
      } finally {
        uni.hideLoading();
      }
    }
  });
};

const handleGenerate = async () => {
  if (formData.value.category === "人名" && !formData.value.surname.trim()) {
    return uni.showToast({ title: "人名必须填写姓氏", icon: "none" });
  }
  loading.value = true;
  uni.showLoading({ title: "AI 思考中..." });
  try {
    const res = await http.generateName(formData.value);
    names.value = res.names || [];
    threadId.value = res.thread_id || "";
    latestNameRecordId.value = res.name_record_id || "";
    if (latestNameRecordId.value) {
      uni.setStorageSync("latest_name_record_id", latestNameRecordId.value);
    }
    feedbackText.value = "";
  } finally {
    loading.value = false;
    uni.hideLoading();
  }
};

const handleFeedback = async () => {
  if (!feedbackText.value.trim()) {
    return uni.showToast({ title: "请输入修改意见", icon: "none" });
  }
  loading.value = true;
  uni.showLoading({ title: "微调修改中..." });
  try {
    const res = await http.feedbackName({
      thread_id: threadId.value,
      category: formData.value.category,
      feedback: feedbackText.value
    });
    names.value = res.names || [];
    latestNameRecordId.value = res.name_record_id || latestNameRecordId.value;
    if (latestNameRecordId.value) {
      uni.setStorageSync("latest_name_record_id", latestNameRecordId.value);
    }
    feedbackText.value = "";
  } finally {
    loading.value = false;
    uni.hideLoading();
  }
};
</script>

<style scoped>
.container { width: 100%; max-width: 1180px; margin: 0 auto; padding: 28rpx 30rpx 172rpx; background-color: #f5f7fa; min-height: 100vh; box-sizing: border-box; }
.top-actions { display: flex; justify-content: flex-end; gap: 16rpx; margin-bottom: 20rpx; position: relative; z-index: 10; }
.logout-btn { margin: 0; min-width: 128rpx; height: 56rpx; line-height: 56rpx; border-radius: 8rpx; background: #111827; color: #fff; font-size: 24rpx; }
.tabs { display: flex; justify-content: space-around; background: #fff; padding: 18rpx 20rpx; border-radius: 12rpx; margin-bottom: 24rpx; box-shadow: 0 6rpx 18rpx rgba(17,24,39,0.04); }
.tab { flex: 1; text-align: center; font-size: 30rpx; color: #4b5563; padding: 12rpx 20rpx; }
.tab.active { color: #007aff; font-weight: 700; border-bottom: 4rpx solid #007aff; }
.upload-section { background: #ecfeff; padding: 22rpx; border-radius: 12rpx; margin-bottom: 24rpx; text-align: center; border: 1px solid #bae6fd; }
.upload-tip { font-size: 24rpx; color: #0369a1; margin-bottom: 12rpx; }
.form-group { background: #fff; padding: 24rpx; border-radius: 12rpx; margin-bottom: 30rpx; box-shadow: 0 6rpx 18rpx rgba(17,24,39,0.04); }
.input-box { border-bottom: 1px solid #edf0f5; padding: 26rpx 10rpx; font-size: 28rpx; color: #111827; }
.textarea-box { width: 100%; height: 180rpx; background: #f8fafc; padding: 22rpx; box-sizing: border-box; border-radius: 10rpx; font-size: 28rpx; margin-top: 20rpx; }
.btn-primary { background: #007aff; color: #fff; border-radius: 12rpx; margin-bottom: 40rpx; font-weight: 700; box-shadow: 0 10rpx 24rpx rgba(0,122,255,0.22); }
.btn-secondary { background: #ff9800; color: #fff; border-radius: 12rpx; margin-top: 20rpx; }
.result-actions { display: flex; flex-wrap: wrap; gap: 14rpx; margin-top: 18rpx; }
.brand-btn { margin: 0; background: #111827; color: #fff; border-radius: 8rpx; }
.brand-btn.light { background: #eef2ff; color: #1f3a8a; }
.result-box { margin-top: 40rpx; }
.result-title { font-size: 32rpx; font-weight: bold; margin-bottom: 20rpx; }
.name-card { background: #fff; padding: 30rpx; border-radius: 16rpx; margin-bottom: 24rpx; box-shadow: 0 4rpx 12rpx rgba(0,0,0,0.05); }
.name-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16rpx; gap: 20rpx; }
.name-text { font-size: 40rpx; font-weight: bold; color: #333; }
.domain-tag { font-size: 22rpx; padding: 6rpx 16rpx; border-radius: 30rpx; background: #e8f5e9; color: #4caf50; }
.name-detail { font-size: 26rpx; color: #666; line-height: 1.6; margin-bottom: 8rpx; }
.label { font-weight: bold; color: #333; }
.feedback-box { margin-top: 40rpx; background: #fff; padding: 30rpx; border-radius: 16rpx; }

.home-tabbar {
  position: fixed;
  z-index: 20;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  height: 112rpx;
  padding-bottom: env(safe-area-inset-bottom);
  background: #fff;
  border-top: 1px solid #e7e7e7;
  box-shadow: 0 -2rpx 10rpx rgba(17,24,39,0.06);
}

.home-tab-item {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  color: #b7b7b7;
}

.home-tab-item.home-active {
  color: #16a3e6;
}

.home-tab-icon {
  position: relative;
  width: 44rpx;
  height: 44rpx;
  margin-bottom: 6rpx;
}

.home-home-icon::before {
  content: "";
  position: absolute;
  left: 4rpx;
  top: 16rpx;
  width: 36rpx;
  height: 28rpx;
  background: currentColor;
}

.home-home-icon::after {
  content: "";
  position: absolute;
  left: 9rpx;
  top: 0;
  width: 26rpx;
  height: 26rpx;
  background: currentColor;
  transform: rotate(45deg);
}

.home-expert-icon {
  border: 8rpx solid currentColor;
  border-top: 0;
  border-radius: 0 0 8rpx 8rpx;
  box-sizing: border-box;
}

.home-expert-icon::before {
  content: "";
  position: absolute;
  left: 8rpx;
  top: -12rpx;
  width: 26rpx;
  height: 12rpx;
  border: 5rpx solid currentColor;
  border-bottom: 0;
  border-radius: 12rpx 12rpx 0 0;
}

.home-cart-icon {
  border-bottom: 10rpx solid currentColor;
  border-left: 8rpx solid transparent;
  border-right: 8rpx solid transparent;
  transform: skewX(-8deg);
  box-sizing: border-box;
}

.home-cart-icon::before,
.home-cart-icon::after {
  content: "";
  position: absolute;
  bottom: -20rpx;
  width: 9rpx;
  height: 9rpx;
  border-radius: 50%;
  background: currentColor;
}

.home-cart-icon::before {
  left: 4rpx;
}

.home-cart-icon::after {
  right: 4rpx;
}

.home-user-icon::before {
  content: "";
  position: absolute;
  left: 10rpx;
  top: 0;
  width: 24rpx;
  height: 24rpx;
  border-radius: 50%;
  background: currentColor;
}

.home-user-icon::after {
  content: "";
  position: absolute;
  left: 3rpx;
  bottom: 0;
  width: 38rpx;
  height: 24rpx;
  border-radius: 20rpx 20rpx 6rpx 6rpx;
  background: currentColor;
}

.home-tab-text {
  font-size: 26rpx;
  line-height: 1.2;
}
</style>
