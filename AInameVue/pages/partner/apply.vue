<template>
  <view class="page">
    <view class="header">
      <view class="title">申请合伙人</view>
      <view class="sub">审核通过后可获得专属二维码，用于客户扫码注册归因。</view>
    </view>

    <view class="form-card">
      <picker mode="selector" :range="typeLabels" :value="typeIndex" @change="changeType">
        <view class="select">{{ typeLabels[typeIndex] }}</view>
      </picker>
      <input class="input" v-model="form.name" placeholder="联系人姓名" />
      <input class="input" v-model="form.contact_phone" placeholder="联系电话" />
      <input class="input" v-model="form.company_name" placeholder="门店/机构名称" />
      <input class="input" v-model="form.address" placeholder="经营地址" />
      <textarea class="textarea" v-model="form.description" placeholder="业务说明、客户来源、合作场景"></textarea>
      <button class="btn" :loading="loading" @tap="submitApply">提交审核</button>
    </view>
  </view>
</template>

<script setup>
import { reactive, ref } from "vue";
import http from "@/http/http.js";
import { goPage } from "@/utils/router.js";

const typeOptions = ["maternal_store", "business_agent"];
const typeLabels = ["孕婴店老板", "工商代办专员"];
const typeIndex = ref(0);
const loading = ref(false);
const form = reactive({
  partner_type: typeOptions[0],
  name: "",
  contact_phone: "",
  company_name: "",
  address: "",
  description: ""
});

const changeType = (event) => {
  typeIndex.value = Number(event.detail.value);
  form.partner_type = typeOptions[typeIndex.value];
};

const submitApply = async () => {
  if (!form.name.trim() || !form.contact_phone.trim()) {
    return uni.showToast({ title: "请填写联系人和电话", icon: "none" });
  }
  loading.value = true;
  try {
    await http.applyPartner({ ...form });
    uni.showModal({
      title: "提交成功",
      content: "合伙人申请已提交，请等待管理员审核。",
      showCancel: false,
      success: () => goPage("/pages/partner/center", { redirect: true })
    });
  } catch (error) {
    console.error("apply partner failed", error);
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.page { min-height: 100vh; padding: 30rpx; background: #f5f7fa; box-sizing: border-box; }
.header { margin-bottom: 24rpx; }
.title { font-size: 42rpx; font-weight: 800; color: #111827; }
.sub { margin-top: 12rpx; color: #6b7280; line-height: 1.6; font-size: 26rpx; }
.form-card { background: #fff; border-radius: 12rpx; padding: 28rpx; }
.select, .input { height: 84rpx; line-height: 84rpx; border-bottom: 1px solid #edf0f5; font-size: 28rpx; color: #111827; }
.textarea { width: 100%; height: 190rpx; margin-top: 22rpx; padding: 20rpx; box-sizing: border-box; border-radius: 10rpx; background: #f8fafc; font-size: 28rpx; }
.btn { margin-top: 30rpx; background: #111827; color: #fff; border-radius: 10rpx; }
</style>
