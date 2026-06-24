<template>
  <view class="page">
    <view class="card">
      <view class="title">确认购买专家服务</view>
      <view class="tip">命名记录 ID 可不填；如需关联某次命名结果，再填写对应记录 ID。</view>
      <input class="input" v-model="nameRecordId" placeholder="命名记录ID，可选" />
      <button class="btn" :loading="loading" @tap="submit">创建订单</button>
      <view v-if="order.id" class="result">
        <view>专家订单已创建：#{{ order.id }}，金额 ¥{{ order.amount }}</view>
        <view v-if="order.order_no" class="tip-line">支付订单：{{ order.order_no }}</view>
        <button v-if="order.order_id" class="pay-btn" @tap="goPay">去支付订单</button>
      </view>
    </view>
  </view>
</template>

<script setup>
import { onLoad } from "@dcloudio/uni-app";
import { ref } from "vue";
import http from "@/http/http.js";
import { goPage } from "@/utils/router.js";

const expertId = ref("");
const nameRecordId = ref("");
const order = ref({});
const loading = ref(false);

onLoad((query) => {
  expertId.value = query.expert_id || "";
  nameRecordId.value = query.name_record_id || uni.getStorageSync("latest_name_record_id") || "";
});

const submit = async () => {
  if (!expertId.value) {
    return uni.showToast({ title: "缺少专家ID，请从专家详情页进入", icon: "none" });
  }

  loading.value = true;
  try {
    order.value = await http.createExpertOrder({
      expert_id: Number(expertId.value),
      name_record_id: nameRecordId.value ? Number(nameRecordId.value) : null
    });
    uni.showToast({ title: "订单创建成功" });
  } catch (error) {
    console.error("创建专家订单失败", error);
  } finally {
    loading.value = false;
  }
};

const goPay = () => {
  goPage(`/pages/user/order-detail?id=${order.value.order_id}`);
};
</script>

<style scoped>
.page { min-height: 100vh; padding: 30rpx; background: #f5f7fa; box-sizing: border-box; }
.card { background: #fff; border-radius: 10rpx; padding: 30rpx; }
.title { font-size: 36rpx; font-weight: 700; color: #111827; }
.tip { color: #6b7280; font-size: 24rpx; line-height: 1.6; margin-top: 14rpx; }
.input { border-bottom: 1px solid #e5e7eb; padding: 24rpx 0; margin-top: 20rpx; }
.btn { background: #1f6feb; color: #fff; margin-top: 36rpx; border-radius: 10rpx; }
.result { margin-top: 24rpx; color: #374151; }
.tip-line { color: #6b7280; font-size: 24rpx; margin-top: 12rpx; }
.pay-btn { background: #111827; color: #fff; margin-top: 24rpx; border-radius: 10rpx; }
</style>
