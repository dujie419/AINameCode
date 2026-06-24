<template>
  <view class="page">
    <view class="form">
      <input class="input" v-model="form.name" placeholder="专家名称" />
      <input class="input" v-model="form.title" placeholder="专家头衔" />
      <input class="input" v-model="form.avatar" placeholder="头像 URL" />
      <input class="input" v-model.number="form.price" type="number" placeholder="服务价格" />
      <input class="input" v-model="tagText" placeholder="标签，用逗号分隔" />
      <textarea class="textarea" v-model="form.description" placeholder="专家介绍"></textarea>
      <button class="primary" :loading="saving" @tap="save">保存专家资料</button>
    </view>
  </view>
</template>

<script setup>
import { onShow } from "@dcloudio/uni-app";
import { reactive, ref } from "vue";
import http from "@/http/http.js";

const saving = ref(false);
const tagText = ref("");
const form = reactive({ name: "", title: "", avatar: "", price: 0, description: "" });

const load = async () => {
  const res = await http.getExpertCenterProfile();
  Object.assign(form, {
    name: res.name || "",
    title: res.title || "",
    avatar: res.avatar || "",
    price: Number(res.price || 0),
    description: res.description || ""
  });
  tagText.value = (res.tags || []).join(",");
};

const save = async () => {
  saving.value = true;
  try {
    await http.updateExpertCenterProfile({
      ...form,
      tags: tagText.value.split(/[,，]/).map((item) => item.trim()).filter(Boolean)
    });
    uni.showToast({ title: "已保存" });
    setTimeout(() => uni.navigateBack(), 500);
  } finally {
    saving.value = false;
  }
};

onShow(load);
</script>

<style scoped>
.page { min-height: 100vh; padding: 30rpx; background: #f5f7fa; box-sizing: border-box; }
.form { background: #fff; border-radius: 12rpx; padding: 28rpx; }
.input { height: 86rpx; border-bottom: 1px solid #edf0f5; font-size: 28rpx; }
.textarea { width: 100%; min-height: 200rpx; box-sizing: border-box; margin-top: 22rpx; padding: 20rpx; background: #f8fafc; border-radius: 10rpx; font-size: 28rpx; }
.primary { margin-top: 30rpx; background: #111827; color: #fff; border-radius: 10rpx; }
</style>
