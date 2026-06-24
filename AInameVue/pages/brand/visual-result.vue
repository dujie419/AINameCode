<template>
  <view class="page">
    <view class="title">{{ result.name || pageTitle }}</view>
    <view class="section highlight">
      <view class="section-title">{{ isCardMode ? "名片短标语" : "品牌 Slogan" }}</view>
      <view class="text">{{ result.slogan }}</view>
    </view>
    <view class="section">
      <view class="section-title">{{ isCardMode ? "名片视觉概念" : "Logo 概念" }}</view>
      <view class="text">{{ result.logo_concept }}</view>
    </view>
    <view class="section">
      <view class="section-title">{{ isCardMode ? "名片图片 Prompt" : "Logo Prompt" }}</view>
      <view class="text">{{ result.logo_prompt }}</view>
      <button class="image-btn" :loading="imageLoading" @tap="generateImage">{{ imageButtonText }}</button>
      <image v-if="result.image_url" class="logo-image" :src="result.image_url" mode="widthFix"></image>
    </view>
    <view class="section">
      <view class="section-title">推荐配色</view>
      <view class="tag-list">
        <text class="tag" v-for="item in result.color_palette" :key="item">{{ item }}</text>
      </view>
    </view>
    <view class="section">
      <view class="section-title">字体风格</view>
      <view class="text">{{ result.typography_style }}</view>
    </view>
    <view class="section">
      <view class="section-title">名片排版建议</view>
      <view class="text">{{ result.business_card_layout }}</view>
    </view>
    <view v-if="isCardMode" class="section">
      <view class="section-title">正面布局</view>
      <view class="text">{{ result.business_card_copy.front_layout }}</view>
    </view>
    <view v-if="isCardMode" class="section">
      <view class="section-title">背面布局</view>
      <view class="text">{{ result.business_card_copy.back_layout }}</view>
    </view>
    <view v-if="isCardMode" class="section">
      <view class="section-title">联系方式占位</view>
      <view class="tag-list">
        <text class="tag" v-for="item in result.business_card_copy.contact_placeholders" :key="item">{{ item }}</text>
      </view>
    </view>
    <view class="section">
      <view class="section-title">{{ isCardMode ? "个人介绍方向" : "品牌故事" }}</view>
      <view class="text">{{ result.brand_story }}</view>
    </view>
    <view class="section">
      <view class="section-title">{{ isCardMode ? "使用建议" : "一键冷启动方案" }}</view>
      <view class="text">{{ result.marketing_copy }}</view>
    </view>
    <view class="section">
      <view class="section-title">{{ isCardMode ? "名片视觉说明" : "品牌视觉说明" }}</view>
      <view class="text">{{ result.brand_visual_report }}</view>
    </view>
  </view>
</template>

<script setup>
import { onShow } from "@dcloudio/uni-app";
import { computed, ref } from "vue";
import http from "@/http/http.js";

const result = ref({
  mode: "brand",
  name: "",
  slogan: "",
  logo_concept: "",
  logo_prompt: "",
  color_palette: [],
  typography_style: "",
  business_card_layout: "",
  business_card_copy: {
    contact_placeholders: [],
    front_layout: "",
    back_layout: ""
  },
  brand_story: "",
  marketing_copy: "",
  brand_visual_report: ""
});
const imageLoading = ref(false);
const isCardMode = computed(() => result.value.mode === "card");
const pageTitle = computed(() => isCardMode.value ? "名片方案" : "品牌视觉方案");
const imageButtonText = computed(() => isCardMode.value ? "生成名片图片" : "生成 Logo 图片");

onShow(() => {
  const stored = uni.getStorageSync("brand_visual_result");
  result.value = {
    ...result.value,
    ...(stored || {}),
    business_card_copy: {
      ...result.value.business_card_copy,
      ...((stored && stored.business_card_copy) || {})
    }
  };
});

const generateImage = async () => {
  if (!result.value.logo_prompt) {
    return uni.showToast({ title: isCardMode.value ? "缺少名片图片 Prompt" : "缺少 Logo Prompt", icon: "none" });
  }
  imageLoading.value = true;
  uni.showLoading({ title: "图片生成中..." });
  try {
    const res = await http.generateBrandLogoImage({
      logo_prompt: result.value.logo_prompt,
      record_id: result.value.id,
      size: "1024*1024",
      n: 1
    });
    if (res.image_url) {
      result.value.image_url = res.image_url;
      uni.setStorageSync("brand_visual_result", result.value);
      uni.showToast({ title: "图片生成成功" });
    } else {
      uni.showModal({ title: "图片生成未完成", content: res.message || res.status, showCancel: false });
    }
  } catch (error) {
    console.error(isCardMode.value ? "名片图片生成失败" : "Logo 图片生成失败", error);
  } finally {
    imageLoading.value = false;
    uni.hideLoading();
  }
};
</script>

<style scoped>
.page { min-height: 100vh; padding: 30rpx; background: #f5f7fa; box-sizing: border-box; }
.title { font-size: 42rpx; font-weight: 700; color: #111827; margin-bottom: 24rpx; }
.section { background: #fff; border-radius: 10rpx; padding: 26rpx; margin-bottom: 18rpx; }
.highlight { border-left: 8rpx solid #1f6feb; }
.section-title { font-size: 28rpx; font-weight: 700; color: #111827; margin-bottom: 14rpx; }
.text { font-size: 26rpx; color: #374151; line-height: 1.7; white-space: pre-wrap; }
.tag-list { display: flex; flex-wrap: wrap; gap: 12rpx; }
.tag { background: #eef2ff; color: #1f3a8a; border-radius: 8rpx; padding: 8rpx 14rpx; font-size: 24rpx; }
.image-btn { margin-top: 20rpx; margin-left: 0; background: #111827; color: #fff; border-radius: 8rpx; }
.logo-image { width: 100%; margin-top: 20rpx; border-radius: 10rpx; background: #f3f4f6; }
</style>
