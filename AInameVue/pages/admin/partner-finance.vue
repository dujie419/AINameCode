<template>
  <view class="page">
    <view class="topbar">
      <view>
        <view class="title">合伙人财务</view>
        <view class="sub">佣金结算、提现审核和渠道财务概览</view>
      </view>
      <button size="mini" class="settle" @tap="settleDue">结算到期佣金</button>
    </view>

    <view class="stats">
      <view class="stat"><view class="value">{{ summary.partner_total || 0 }}</view><view class="label">合伙人</view></view>
      <view class="stat"><view class="value">{{ summary.attributed_user_total || 0 }}</view><view class="label">归因用户</view></view>
      <view class="stat"><view class="value">{{ money(summary.pending_commission) }}</view><view class="label">待结算</view></view>
      <view class="stat"><view class="value">{{ money(summary.settled_commission) }}</view><view class="label">已结算</view></view>
      <view class="stat"><view class="value">{{ money(summary.pending_withdraw) }}</view><view class="label">提现待审</view></view>
      <view class="stat"><view class="value">{{ money(summary.paid_withdraw) }}</view><view class="label">已提现</view></view>
    </view>

    <view class="section">
      <view class="section-title">提现审核</view>
      <view v-if="withdrawals.length === 0" class="empty">暂无待审核提现</view>
      <view class="row" v-for="item in withdrawals" :key="item.id">
        <view>
          <view class="row-title">{{ item.withdrawal_no }}</view>
          <view class="row-sub">合伙人 {{ item.partner_id }} · {{ item.account_name }} · {{ item.bank_name || "未填银行" }}</view>
        </view>
        <view class="right">
          <view class="amount">{{ money(item.amount) }}</view>
          <view class="actions">
            <button size="mini" class="approve" @tap="approveWithdrawal(item.id)">通过</button>
            <button size="mini" class="reject" @tap="rejectWithdrawal(item.id)">拒绝</button>
          </view>
        </view>
      </view>
    </view>

    <view class="section">
      <view class="section-title">佣金流水</view>
      <view v-if="commissions.length === 0" class="empty">暂无佣金流水</view>
      <view class="row" v-for="item in commissions" :key="item.id">
        <view>
          <view class="row-title">{{ item.business_type }} #{{ item.business_id }}</view>
          <view class="row-sub">合伙人 {{ item.partner_id }} · {{ statusText(item.status) }}</view>
        </view>
        <view class="amount">{{ money(item.commission_amount) }}</view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { onShow } from "@dcloudio/uni-app";
import { ref } from "vue";
import adminApi from "@/api/admin.js";

const summary = ref({});
const withdrawals = ref([]);
const commissions = ref([]);

const money = (value) => Number(value || 0).toFixed(2);
const statusText = (status) => ({
  settle_pending: "待结算",
  settled: "已结算",
  reversed: "已冲正",
  clawback_pending: "待追回"
}[status] || status);

const loadPage = async () => {
  const [summaryRes, withdrawalRes, commissionRes] = await Promise.all([
    adminApi.partnerFinanceSummary(),
    adminApi.partnerWithdrawals({ page: 1, page_size: 20, status: "pending" }),
    adminApi.partnerCommissions({ page: 1, page_size: 20 })
  ]);
  summary.value = summaryRes || {};
  withdrawals.value = withdrawalRes.items || [];
  commissions.value = commissionRes.items || [];
};

const settleDue = async () => {
  const res = await adminApi.settlePartnerCommissions();
  uni.showToast({ title: `已结算 ${res.settled_count || 0} 条`, icon: "none" });
  await loadPage();
};

const approveWithdrawal = async (id) => {
  await adminApi.approvePartnerWithdrawal(id);
  uni.showToast({ title: "已通过" });
  await loadPage();
};

const rejectWithdrawal = async (id) => {
  await adminApi.rejectPartnerWithdrawal(id);
  uni.showToast({ title: "已拒绝" });
  await loadPage();
};

onShow(loadPage);
</script>

<style scoped>
.page { min-height: 100vh; padding: 30rpx; background: #f5f7fa; box-sizing: border-box; }
.topbar { display: flex; align-items: center; justify-content: space-between; gap: 18rpx; margin-bottom: 24rpx; }
.title { color: #111827; font-size: 42rpx; font-weight: 800; }
.sub { color: #6b7280; font-size: 24rpx; margin-top: 8rpx; }
.settle { margin: 0; background: #111827; color: #fff; border-radius: 8rpx; }
.stats { display: grid; grid-template-columns: repeat(2, 1fr); gap: 18rpx; }
.stat, .section { background: #fff; border-radius: 10rpx; padding: 24rpx; }
.value { color: #111827; font-size: 36rpx; font-weight: 800; }
.label { color: #64748b; font-size: 24rpx; margin-top: 6rpx; }
.section { margin-top: 22rpx; }
.section-title { color: #111827; font-size: 31rpx; font-weight: 800; margin-bottom: 8rpx; }
.empty { padding: 44rpx 0; text-align: center; color: #94a3b8; }
.row { display: flex; align-items: center; justify-content: space-between; gap: 20rpx; padding: 22rpx 0; border-bottom: 1px solid #edf2f7; }
.row-title { color: #1f2937; font-size: 28rpx; font-weight: 700; }
.row-sub { color: #94a3b8; font-size: 23rpx; margin-top: 6rpx; }
.right { text-align: right; }
.amount { color: #111827; font-size: 28rpx; font-weight: 800; }
.actions { display: flex; gap: 10rpx; margin-top: 10rpx; }
.approve { background: #16a34a; color: #fff; }
.reject { background: #ef4444; color: #fff; }
</style>
