<template>
  <view class="page">
    <view class="header">
      <view class="title">申请成为专家</view>
      <view class="sub">提交资料后由管理员后台审核，通过后即可接收专家精批订单。</view>
    </view>

    <view class="form-card">
      <input class="input" v-model="form.name" placeholder="姓名/称呼，例如：张老师" />
      <input class="input" v-model="form.title" placeholder="专家头衔，例如：国学命名专家" />
      <input class="input" v-model.number="form.price" type="number" placeholder="服务价格，例如：199" />
      <input class="input" v-model.number="form.experience_years" type="number" placeholder="从业年限，例如：10" />
      <input class="input" v-model="tagText" placeholder="擅长标签，用逗号分隔，例如：国学,宝宝起名" />
      <textarea class="textarea" v-model="form.description" placeholder="个人介绍、服务内容、案例经验"></textarea>
      <button class="btn" :loading="loading" @tap="submitApply">提交审核</button>
    </view>
  </view>
</template>

<script setup>
import { reactive, ref } from "vue";
import http from "@/http/http.js";
import { goPage } from "@/utils/router.js";

const loading = ref(false);
const tagText = ref("");
const form = reactive({
  name: "",
  title: "",
  description: "",
  price: 199,
  experience_years: 0
});

const submitApply = async () => {
  if (!form.name.trim() || !form.title.trim() || !form.description.trim()) {
    return uni.showToast({ title: "请填写完整申请信息", icon: "none" });
  }

  loading.value = true;
  uni.showLoading({ title: "提交中..." });
  try {
    await http.applyExpert({
      ...form,
      tags: tagText.value
        .split(/[,，]/)
        .map((item) => item.trim())
        .filter(Boolean)
    });
    uni.showModal({
      title: "提交成功",
      content: "专家申请已提交，请等待管理员审核。",
      showCancel: false,
      success: () => {
        goPage("/pages/expert/index");
      }
    });
  } catch (error) {
    console.error("申请专家失败", error);
  } finally {
    loading.value = false;
    uni.hideLoading();
  }
};
</script>

<style scoped>
.page { min-height: 100vh; padding: 30rpx; background: #f5f7fa; box-sizing: border-box; }
.header { margin-bottom: 24rpx; }
.title { font-size: 42rpx; font-weight: 700; color: #111827; }
.sub { margin-top: 12rpx; color: #6b7280; line-height: 1.6; font-size: 26rpx; }
.form-card { background: #fff; border-radius: 12rpx; padding: 28rpx; box-shadow: 0 4rpx 16rpx rgba(0,0,0,0.04); }
.input { height: 84rpx; border-bottom: 1px solid #edf0f5; font-size: 28rpx; }
.textarea { width: 100%; height: 180rpx; margin-top: 22rpx; padding: 20rpx; box-sizing: border-box; border-radius: 10rpx; background: #f8fafc; font-size: 28rpx; }
.btn { margin-top: 30rpx; background: #111827; color: #fff; border-radius: 10rpx; }
</style>
