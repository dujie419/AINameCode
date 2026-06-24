<template>
  <view class="page">
    <view class="title">{{ pageTitle }}</view>
    <view class="form">
      <input class="input" v-model="form.name" :placeholder="isCardMode ? '姓名' : '品牌名称'" />
      <input class="input" v-model="form.industry" :placeholder="isCardMode ? '身份/用途，例如：创始人、设计师、个人名片' : '行业，例如：人工智能硬件'" />
      <textarea class="textarea" v-model="form.meaning" :placeholder="isCardMode ? '姓名寓意或希望传达的个人气质' : '名字寓意'"></textarea>
      <picker mode="selector" :range="styleOptions" @change="changeStyle">
        <view class="input">{{ isCardMode ? "名片风格" : "品牌风格" }}：{{ form.style || '请选择' }}</view>
      </picker>
      <input class="input" v-model="form.target_users" :placeholder="isCardMode ? '目标受众，例如：客户、投资人、合作伙伴' : '目标用户，可选'" />
      <input class="input" v-model="form.usage_scene" :placeholder="isCardMode ? '使用场景，例如：线下会面、电子名片' : '使用场景，可选'" />
    </view>
    <button class="btn-primary" :loading="loading" @tap="generate">{{ submitText }}</button>
  </view>
</template>

<script setup>
import { onLoad } from "@dcloudio/uni-app";
import { computed, ref } from "vue";
import http from "@/http/http.js";
import { goPage } from "@/utils/router.js";

const styleOptions = ["科技感", "国风", "高端", "亲和", "年轻化", "极简"];
const loading = ref(false);
const mode = ref("brand");
const form = ref({
  mode: "brand",
  name: "",
  industry: "",
  style: "科技感",
  meaning: "",
  target_users: "",
  usage_scene: ""
});

const isCardMode = computed(() => mode.value === "card");
const pageTitle = computed(() => isCardMode.value ? "名片方案生成" : "品牌视觉生成");
const submitText = computed(() => isCardMode.value ? "生成名片方案" : "生成品牌视觉方案");

onLoad((query) => {
  form.value.name = decodeURIComponent(query.name || "");
  form.value.industry = decodeURIComponent(query.industry || "");
  form.value.meaning = decodeURIComponent(query.meaning || "");
  mode.value = decodeURIComponent(query.mode || "brand");
  form.value.mode = mode.value;
});

const changeStyle = (event) => {
  form.value.style = styleOptions[event.detail.value];
};

const openResult = (result) => {
  uni.setStorageSync("brand_visual_result", result);
  goPage("/pages/brand/visual-result");
};

const generate = async () => {
  if (!form.value.name) {
    return uni.showToast({ title: isCardMode.value ? "请填写姓名" : "请填写品牌名称", icon: "none" });
  }
  loading.value = true;
  uni.showLoading({ title: "生成中..." });
  try {
    const result = await http.generateBrandVisual({ ...form.value, mode: mode.value });
    openResult(result);
  } catch (error) {
    console.error("品牌视觉生成失败", error);
  } finally {
    loading.value = false;
    uni.hideLoading();
  }
};
</script>

<style scoped>
.page { min-height: 100vh; padding: 30rpx; background: #f5f7fa; box-sizing: border-box; }
.title { font-size: 42rpx; font-weight: 700; color: #111827; margin-bottom: 30rpx; }
.form { background: #fff; border-radius: 10rpx; padding: 24rpx; }
.input { border-bottom: 1px solid #e5e7eb; padding: 24rpx 4rpx; font-size: 28rpx; }
.textarea { width: 100%; min-height: 150rpx; background: #f9fafb; border-radius: 8rpx; padding: 20rpx; box-sizing: border-box; margin-top: 20rpx; font-size: 28rpx; }
.btn-primary { background: #1f6feb; color: #fff; border-radius: 10rpx; margin-top: 34rpx; }
</style>
