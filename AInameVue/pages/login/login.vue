<template>
  <view class="login-page">
    <view class="login-card">
      <picker mode="selector" :range="modes" range-key="label" :value="modeIndex" @change="changeMode">
        <view class="login-ribbon">
          <text>AI智能起名-{{ currentMode.label }}登录</text>
          <text class="arrow">▾</text>
        </view>
      </picker>

      <input
        class="input-box"
        v-model="form.account"
        :placeholder="mode === 'admin' ? '请输入管理员账号' : '请输入邮箱'"
      />
      <input class="input-box" v-model="form.password" type="password" placeholder="请输入密码" />

      <button class="btn" :loading="loading" @tap="handleLogin">{{ loginText }}</button>

      <view v-if="mode !== 'admin'" class="link" @tap="goRegister">没有账号？去注册</view>
      <view class="tip" v-if="mode === 'expert'">专家登录使用普通用户账号，需先提交专家申请并通过管理员审核。</view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from "vue";
import { onLoad } from "@dcloudio/uni-app";
import http from "@/http/http.js";
import adminApi from "@/api/admin.js";
import { goPage } from "@/utils/router.js";

const modes = [
  { label: "普通用户", value: "user" },
  { label: "管理员", value: "admin" },
  { label: "专家", value: "expert" }
];

const mode = ref("user");
const form = ref({ account: "", password: "" });
const loading = ref(false);

const modeIndex = computed(() => Math.max(0, modes.findIndex((item) => item.value === mode.value)));
const currentMode = computed(() => modes[modeIndex.value] || modes[0]);
const loginText = computed(() => `${currentMode.value.label}登录`);

onLoad((query) => {
  if (query.mode && modes.some((item) => item.value === query.mode)) {
    mode.value = query.mode;
    form.value.account = query.mode === "admin" ? "admin" : "";
  }
});

const changeMode = (event) => {
  const nextMode = modes[event.detail.value] || modes[0];
  mode.value = nextMode.value;
  form.value = { account: nextMode.value === "admin" ? "admin" : "", password: "" };
};

const handleLogin = async () => {
  if (!form.value.account || !form.value.password) {
    return uni.showToast({ title: "请填写账号和密码", icon: "none" });
  }

  loading.value = true;
  try {
    if (mode.value === "admin") {
      const res = await adminApi.login({
        username: form.value.account,
        password: form.value.password
      });
      uni.setStorageSync("admin_token", res.access_token);
      uni.setStorageSync("admin_role", res.role);
      uni.showToast({ title: "登录成功" });
      setTimeout(() => goPage("/pages/admin/index", { relaunch: true }), 500);
      return;
    }

    const res = await http.login({
      email: form.value.account,
      password: form.value.password
    });
    uni.setStorageSync("token", res.token);
    uni.setStorageSync("user", res.user);
    uni.showToast({ title: "登录成功" });
    const target = mode.value === "expert" ? "/pages/expert/workbench" : "/pages/index/index";
    setTimeout(() => goPage(target, { relaunch: true }), 500);
  } catch (error) {
    console.error("登录失败", error);
  } finally {
    loading.value = false;
  }
};

const goRegister = () => goPage("/pages/register/register");
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 80rpx 32rpx;
  background: #dbe3ea;
  box-sizing: border-box;
}

.login-card {
  width: 620rpx;
  min-height: 500rpx;
  background: #fff;
  border-radius: 4rpx;
  padding: 70rpx 60rpx 56rpx;
  box-shadow: 0 20rpx 56rpx rgba(15, 23, 42, 0.18);
}

.login-ribbon {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: calc(100% + 56rpx);
  height: 80rpx;
  margin-left: -28rpx;
  margin-bottom: 42rpx;
  padding: 0 56rpx;
  box-sizing: border-box;
  background: #22aeea;
  color: #fff;
  font-size: 28rpx;
  font-weight: 700;
  box-shadow: 0 8rpx 18rpx rgba(14, 165, 233, 0.28);
}

.arrow {
  font-size: 24rpx;
  opacity: 0.9;
}

.input-box {
  width: 100%;
  box-sizing: border-box;
  background: #fff;
  border: 1px solid #dbe4ea;
  border-radius: 2rpx;
  padding: 0 24rpx;
  height: 72rpx;
  line-height: 72rpx;
  margin-bottom: 26rpx;
  font-size: 28rpx;
}

.btn {
  background-color: #22aeea;
  color: white;
  margin-top: 4rpx;
  border-radius: 2rpx;
  font-weight: 700;
  height: 76rpx;
  line-height: 76rpx;
  font-size: 30rpx;
}

.link {
  text-align: center;
  color: #0ea5e9;
  margin-top: 26rpx;
  font-size: 26rpx;
}

.tip {
  color: #6b7280;
  line-height: 1.6;
  font-size: 24rpx;
  margin-top: 24rpx;
  text-align: center;
}
</style>
