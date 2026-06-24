<template>
  <view class="page">
    <view class="avatar-line">
      <image class="avatar" :src="form.avatar || '/static/logo.png'" mode="aspectFill"></image>
      <button class="ghost" :loading="uploading" @tap="chooseAvatar">上传头像</button>
    </view>
    <view class="form">
      <input class="input" v-model="form.nickname" placeholder="昵称" />
      <input class="input" v-model="form.phone" placeholder="手机号" />
      <input class="input" v-model="form.avatar" placeholder="头像 URL" />
      <textarea class="textarea" v-model="form.bio" placeholder="个人简介"></textarea>
      <button class="primary" :loading="saving" @tap="save">保存资料</button>
    </view>
  </view>
</template>

<script setup>
import { onShow } from "@dcloudio/uni-app";
import { reactive, ref } from "vue";
import http from "@/http/http.js";

const uploading = ref(false);
const saving = ref(false);
const form = reactive({ nickname: "", phone: "", avatar: "", bio: "" });

const load = async () => {
  const res = await http.getUserProfile();
  Object.assign(form, {
    nickname: res.nickname || "",
    phone: res.phone || "",
    avatar: res.avatar || "",
    bio: res.bio || ""
  });
};

const chooseAvatar = () => {
  uni.chooseImage({
    count: 1,
    success: async (res) => {
      uploading.value = true;
      try {
        const uploaded = await http.uploadUserAvatar(res.tempFilePaths[0]);
        form.avatar = uploaded.avatar || uploaded.url;
        uni.showToast({ title: "头像已上传" });
      } finally {
        uploading.value = false;
      }
    }
  });
};

const save = async () => {
  saving.value = true;
  try {
    await http.updateUserProfile(form);
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
.avatar-line { display: flex; align-items: center; gap: 24rpx; margin-bottom: 24rpx; }
.avatar { width: 128rpx; height: 128rpx; border-radius: 64rpx; background: #eef2f7; }
.ghost { margin: 0; background: #fff; color: #111827; border-radius: 10rpx; }
.form { background: #fff; border-radius: 12rpx; padding: 28rpx; }
.input { height: 86rpx; border-bottom: 1px solid #edf0f5; font-size: 28rpx; }
.textarea { width: 100%; min-height: 180rpx; box-sizing: border-box; margin-top: 22rpx; padding: 20rpx; background: #f8fafc; border-radius: 10rpx; font-size: 28rpx; }
.primary { margin-top: 30rpx; background: #111827; color: #fff; border-radius: 10rpx; }
</style>
