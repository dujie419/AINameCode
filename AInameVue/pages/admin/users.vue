<template>
  <view class="page">
    <view class="toolbar">
      <button size="mini" @tap="goBack">返回</button>
      <input class="search-input" v-model="keyword" placeholder="搜索邮箱或用户名" confirm-type="search" @confirm="search" />
      <button size="mini" @tap="search">搜索</button>
    </view>

    <view class="user-item" v-for="item in users" :key="item.id">
      <view class="info">
        <view class="name">{{ item.username }}</view>
        <view class="email">{{ item.email }}</view>
        <view :class="['status', item.status === 'active' ? 'active' : 'disabled']">
          {{ item.status === 'active' ? '启用' : '禁用' }}
        </view>
      </view>
      <button size="mini" @tap="toggleStatus(item)">
        {{ item.status === 'active' ? '禁用' : '启用' }}
      </button>
      <button size="mini" class="detail-btn" @tap="openDetail(item.id)">详情</button>
    </view>

    <view v-if="users.length === 0" class="empty">暂无用户</view>

    <view class="pager">
      <button size="mini" :disabled="page <= 1" @tap="prevPage">上一页</button>
      <text>{{ page }} / {{ totalPage }}</text>
      <button size="mini" :disabled="page >= totalPage" @tap="nextPage">下一页</button>
    </view>

    <view v-if="selectedUser.id" class="detail-panel">
      <view class="detail-head">
        <view>
          <view class="detail-title">{{ selectedUser.username }}</view>
          <view class="detail-sub">{{ selectedUser.email }}</view>
        </view>
        <button size="mini" @tap="closeDetail">关闭</button>
      </view>

      <view class="summary-grid">
        <view class="summary-item">
          <view class="summary-value">¥{{ selectedUser.balance }}</view>
          <view class="summary-label">余额</view>
        </view>
        <view class="summary-item">
          <view class="summary-value">¥{{ selectedUser.frozen_balance }}</view>
          <view class="summary-label">冻结余额</view>
        </view>
        <view class="summary-item">
          <view class="summary-value">{{ selectedUser.membership_status === "active" ? "VIP" : "普通" }}</view>
          <view class="summary-label">{{ selectedUser.membership_expires_at || "未开通" }}</view>
        </view>
        <view class="summary-item">
          <view class="summary-value">{{ selectedUser.user_level }}</view>
          <view class="summary-label">用户级别</view>
        </view>
      </view>

      <view class="quota-list">
        <view class="quota-row" v-for="item in quotaItems" :key="item.usage_type">
          <text>{{ item.label }}</text>
          <text>剩余 {{ item.remaining }} / 已用 {{ item.used }} / 总额 {{ item.quota }}</text>
        </view>
      </view>

      <view class="ops">
        <view class="op-card">
          <view class="op-title">调整余额</view>
          <input class="op-input" type="number" v-model.number="balanceForm.amount" placeholder="金额，正数增加，负数减少" />
          <input class="op-input" v-model="balanceForm.reason" placeholder="原因：补偿/活动赠送/违规惩罚/客服处理" />
          <button size="mini" @tap="submitBalance">提交</button>
        </view>

        <view class="op-card">
          <view class="op-title">调整次数</view>
          <picker mode="selector" :range="quotaOptions" range-key="label" @change="changeQuotaType">
            <view class="op-input">类型：{{ quotaLabel(quotaForm.usage_type) }}</view>
          </picker>
          <input class="op-input" type="number" v-model.number="quotaForm.amount" placeholder="次数，正数增加，负数减少" />
          <input class="op-input" v-model="quotaForm.reason" placeholder="原因：补偿/活动赠送/违规惩罚/客服处理" />
          <button size="mini" @tap="submitQuota">提交</button>
        </view>

        <view class="op-card">
          <view class="op-title">调整 VIP</view>
          <picker mode="selector" :range="membershipActions" range-key="label" @change="changeMembershipAction">
            <view class="op-input">操作：{{ membershipActionLabel }}</view>
          </picker>
          <input class="op-input" type="number" v-model.number="membershipForm.days" placeholder="天数" />
          <input class="op-input" v-model="membershipForm.reason" placeholder="原因：补偿/活动赠送/违规惩罚/客服处理" />
          <button size="mini" @tap="submitMembership">提交</button>
        </view>

        <view class="op-card">
          <view class="op-title">修改级别</view>
          <input class="op-input" v-model="levelForm.user_level" placeholder="normal / vip / blacklist / custom" />
          <input class="op-input" v-model="levelForm.reason" placeholder="原因：补偿/活动赠送/违规惩罚/客服处理" />
          <button size="mini" @tap="submitLevel">提交</button>
        </view>
      </view>

      <view class="audit">
        <view class="op-title">审计日志</view>
        <view class="audit-row" v-for="item in selectedUser.audit_logs || []" :key="item.id">
          <view>{{ item.action_type }} · {{ item.target_field }}</view>
          <view class="audit-sub">{{ item.before_value }} → {{ item.after_value }}</view>
          <view class="audit-sub">{{ item.reason }} · 管理员 #{{ item.admin_id }} · {{ item.created_at }}</view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { onShow } from "@dcloudio/uni-app";
import { computed, ref } from "vue";
import adminApi from "@/api/admin.js";
import { goPage } from "@/utils/router.js";

const users = ref([]);
const total = ref(0);
const page = ref(1);
const pageSize = ref(10);
const keyword = ref("");
const selectedUser = ref({});
const balanceForm = ref({ amount: 0, reason: "" });
const quotaForm = ref({ usage_type: "name_generate", amount: 0, reason: "" });
const membershipForm = ref({ action: "open", days: 30, reason: "" });
const levelForm = ref({ user_level: "normal", reason: "" });
const quotaOptions = [
  { label: "起名次数", value: "name_generate" },
  { label: "名片次数", value: "business_card" },
  { label: "图片生成", value: "image_generate" },
  { label: "投票发布", value: "vote_publish" }
];
const membershipActions = [
  { label: "开通", value: "open" },
  { label: "延期", value: "extend" },
  { label: "取消", value: "cancel" }
];
const totalPage = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)));
const quotaItems = computed(() => Object.values(selectedUser.value.quota_items || {}));
const membershipActionLabel = computed(() => {
  const item = membershipActions.find((x) => x.value === membershipForm.value.action);
  return item ? item.label : membershipForm.value.action;
});

const goBack = () => {
  goPage("/pages/admin/index");
};

const loadUsers = async () => {
  try {
    const res = await adminApi.users({ page: page.value, page_size: pageSize.value, keyword: keyword.value });
    users.value = res.items || [];
    total.value = res.total || 0;
  } catch (error) {
    console.error("加载用户列表失败", error);
  }
};

const search = () => {
  page.value = 1;
  loadUsers();
};

const toggleStatus = async (item) => {
  const status = item.status === "active" ? "disabled" : "active";
  await adminApi.updateUserStatus(item.id, status);
  uni.showToast({ title: "操作成功" });
  loadUsers();
};

const openDetail = async (id) => {
  selectedUser.value = await adminApi.userDetail(id);
  levelForm.value.user_level = selectedUser.value.user_level || "normal";
};

const closeDetail = () => {
  selectedUser.value = {};
};

const requireReason = (reason) => {
  if (!String(reason || "").trim()) {
    uni.showToast({ title: "请填写操作原因", icon: "none" });
    return false;
  }
  return true;
};

const refreshDetail = async (res) => {
  selectedUser.value = res || await adminApi.userDetail(selectedUser.value.id);
  uni.showToast({ title: "操作成功" });
  loadUsers();
};

const quotaLabel = (value) => {
  const item = quotaOptions.find((x) => x.value === value);
  return item ? item.label : value;
};

const changeQuotaType = (event) => {
  quotaForm.value.usage_type = quotaOptions[event.detail.value].value;
};

const changeMembershipAction = (event) => {
  membershipForm.value.action = membershipActions[event.detail.value].value;
};

const submitBalance = async () => {
  if (!requireReason(balanceForm.value.reason)) return;
  const res = await adminApi.adjustUserBalance(selectedUser.value.id, balanceForm.value);
  balanceForm.value = { amount: 0, reason: "" };
  refreshDetail(res);
};

const submitQuota = async () => {
  if (!requireReason(quotaForm.value.reason)) return;
  const res = await adminApi.adjustUserQuota(selectedUser.value.id, quotaForm.value);
  quotaForm.value = { usage_type: quotaForm.value.usage_type, amount: 0, reason: "" };
  refreshDetail(res);
};

const submitMembership = async () => {
  if (!requireReason(membershipForm.value.reason)) return;
  const res = await adminApi.adjustUserMembership(selectedUser.value.id, membershipForm.value);
  membershipForm.value = { action: membershipForm.value.action, days: 30, reason: "" };
  refreshDetail(res);
};

const submitLevel = async () => {
  if (!requireReason(levelForm.value.reason)) return;
  const res = await adminApi.updateUserLevel(selectedUser.value.id, levelForm.value);
  levelForm.value = { user_level: res.user_level || "normal", reason: "" };
  refreshDetail(res);
};

const prevPage = () => {
  if (page.value > 1) {
    page.value--;
    loadUsers();
  }
};

const nextPage = () => {
  if (page.value < totalPage.value) {
    page.value++;
    loadUsers();
  }
};

onShow(loadUsers);
</script>

<style scoped>
.page { min-height: 100vh; padding: 24rpx; background: #f5f7fa; box-sizing: border-box; }
.toolbar { display: flex; align-items: center; gap: 16rpx; margin-bottom: 24rpx; }
.search-input { flex: 1; background: #fff; border-radius: 8rpx; padding: 20rpx; font-size: 28rpx; }
.user-item { display: flex; justify-content: space-between; align-items: center; background: #fff; padding: 24rpx; border-radius: 10rpx; margin-bottom: 18rpx; }
.info { flex: 1; min-width: 0; }
.detail-btn { margin-left: 12rpx; }
.name { font-size: 30rpx; font-weight: 700; color: #111827; }
.email { font-size: 24rpx; color: #6b7280; margin-top: 8rpx; word-break: break-all; }
.status { display: inline-block; margin-top: 12rpx; padding: 4rpx 14rpx; border-radius: 6rpx; font-size: 22rpx; }
.active { background: #e8f5e9; color: #2e7d32; }
.disabled { background: #fee2e2; color: #b91c1c; }
.empty { background: #fff; color: #6b7280; text-align: center; padding: 70rpx 20rpx; border-radius: 10rpx; }
.pager { display: flex; align-items: center; justify-content: center; gap: 24rpx; padding: 30rpx 0; color: #4b5563; }
.detail-panel { background: #fff; border-radius: 10rpx; padding: 24rpx; margin-top: 18rpx; }
.detail-head { display: flex; justify-content: space-between; align-items: center; gap: 20rpx; margin-bottom: 20rpx; }
.detail-title { font-size: 34rpx; font-weight: 800; color: #111827; }
.detail-sub { margin-top: 6rpx; font-size: 24rpx; color: #6b7280; word-break: break-all; }
.summary-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 14rpx; }
.summary-item { background: #f8fafc; border-radius: 8rpx; padding: 18rpx; min-width: 0; }
.summary-value { color: #111827; font-size: 30rpx; font-weight: 800; word-break: break-all; }
.summary-label { margin-top: 8rpx; color: #6b7280; font-size: 22rpx; word-break: break-all; }
.quota-list { margin-top: 20rpx; border: 1px solid #eef2f7; border-radius: 8rpx; overflow: hidden; }
.quota-row { display: flex; justify-content: space-between; gap: 18rpx; padding: 18rpx; border-bottom: 1px solid #eef2f7; color: #374151; font-size: 24rpx; }
.quota-row:last-child { border-bottom: 0; }
.ops { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16rpx; margin-top: 20rpx; }
.op-card { border: 1px solid #eef2f7; border-radius: 8rpx; padding: 18rpx; }
.op-title { font-size: 28rpx; font-weight: 800; color: #111827; margin-bottom: 14rpx; }
.op-input { width: 100%; box-sizing: border-box; background: #f8fafc; border-radius: 8rpx; padding: 18rpx; margin-bottom: 12rpx; font-size: 24rpx; }
.audit { margin-top: 20rpx; border-top: 1px solid #eef2f7; padding-top: 20rpx; }
.audit-row { padding: 16rpx 0; border-bottom: 1px solid #eef2f7; color: #374151; font-size: 24rpx; }
.audit-sub { margin-top: 6rpx; color: #6b7280; font-size: 22rpx; word-break: break-all; }

@media (max-width: 700px) {
  .ops { grid-template-columns: 1fr; }
}
</style>
