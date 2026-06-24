<template>
  <view class="page">
    <view class="topbar">
      <view>
        <view class="title">开放平台</view>
        <view class="sub">API Key、套餐额度、在线测试和调用记录</view>
      </view>
      <button size="mini" class="ghost" @tap="goLogs">调用记录</button>
    </view>

    <view v-if="profileStatus === 'none'" class="panel">
      <view class="panel-title">申请开发者</view>
      <input class="input" v-model="applyForm.company_name" placeholder="公司名称" placeholder-style="color:#9ca3af" />
      <input class="input" v-model="applyForm.contact_name" placeholder="联系人" placeholder-style="color:#9ca3af" />
      <button class="primary" :loading="loading" @tap="applyDeveloper">提交申请</button>
    </view>

    <view v-else-if="profileStatus !== 'approved'" class="panel">
      <view class="panel-title">审核状态</view>
      <view class="muted">当前状态：{{ profileStatus }}</view>
    </view>

    <template v-else>
      <view class="stats-grid">
        <view class="stat">
          <text class="label">当前套餐</text>
          <text class="value small">{{ dashboard.plan_name || '未开通' }}</text>
        </view>
        <view class="stat">
          <text class="label">订阅状态</text>
          <text class="value small">{{ dashboard.subscription_status || '-' }}</text>
        </view>
        <view class="stat">
          <text class="label">今日剩余额度</text>
          <text class="value">{{ quotaText(dashboard.today_quota_remaining) }}</text>
        </view>
        <view class="stat">
          <text class="label">本月剩余额度</text>
          <text class="value">{{ quotaText(dashboard.month_quota_remaining) }}</text>
        </view>
        <view class="stat">
          <text class="label">今日调用</text>
          <text class="value">{{ dashboard.today_calls }}</text>
        </view>
        <view class="stat">
          <text class="label">累计调用</text>
          <text class="value">{{ dashboard.total_calls }}</text>
        </view>
        <view class="stat">
          <text class="label">累计Token</text>
          <text class="value">{{ dashboard.total_tokens }}</text>
        </view>
        <view class="stat">
          <text class="label">本月费用</text>
          <text class="value">¥{{ money(dashboard.month_cost) }}</text>
        </view>
      </view>

      <view class="panel">
        <view class="panel-title">收费标准与套餐</view>
        <view class="plan" v-for="plan in plans" :key="plan.id">
          <view>
            <view class="plan-name">{{ plan.name }} · ¥{{ money(plan.price) }}/{{ cycleText(plan.billing_cycle) }}</view>
            <view class="muted">月额度：{{ quotaText(plan.quota) }} · 日额度：{{ quotaText(plan.daily_quota) }} · QPM：{{ plan.qpm_limit }}</view>
            <view class="muted">Token 单价：¥{{ plan.token_price }}/Token</view>
            <view class="muted" v-if="plan.description">{{ plan.description }}</view>
          </view>
          <button size="mini" class="plan-btn" :loading="subscribingId === plan.id" @tap="subscribePlan(plan.id)">开通/续费</button>
        </view>
      </view>

      <view class="panel">
        <view class="panel-title">创建 API Key</view>
        <input class="input" v-model="keyForm.name" placeholder="Key 名称，例如：游戏项目测试" placeholder-style="color:#9ca3af" />
        <input class="input" type="number" v-model.number="keyForm.quota" placeholder="调用额度" placeholder-style="color:#9ca3af" />
        <button class="primary" :loading="creating" @tap="createKey">创建</button>
      </view>

      <view v-if="createdKey.api_key" class="secret-box">
        <view class="secret-title">请立即保存，仅显示一次</view>
        <view class="code">API_KEY: {{ createdKey.api_key }}</view>
        <view class="code">SECRET_KEY: {{ createdKey.secret_key }}</view>
      </view>

      <view class="key-item" v-for="item in apiKeys" :key="item.id">
        <view>
          <view class="key-name">{{ item.name }}</view>
          <view class="muted">{{ item.api_key_prefix }}*** · {{ item.status }}</view>
          <view class="muted">额度 {{ item.used_quota }} / {{ item.quota }}，剩余 {{ Math.max((item.quota || 0) - (item.used_quota || 0), 0) }}</view>
        </view>
        <view class="key-actions">
          <button v-if="item.status === 'active'" size="mini" class="warn" @tap="disableKey(item.id)">禁用</button>
          <button size="mini" class="danger" @tap="deleteKey(item.id)">删除</button>
        </view>
      </view>

      <view class="panel">
        <view class="panel-title">在线测试 API</view>
        <picker :range="endpointOptions" range-key="label" @change="changeEndpoint">
          <view class="input">接口：{{ currentEndpoint.label }}</view>
        </picker>
        <textarea class="textarea" v-model="testBody" placeholder="请求 JSON"></textarea>
        <input class="input" v-model="testApiKey" placeholder="API_KEY" placeholder-style="color:#9ca3af" />
        <input class="input" v-model="testSecretKey" placeholder="SECRET_KEY" placeholder-style="color:#9ca3af" />
        <button class="primary" :loading="testing" @tap="runTest">发送测试请求</button>
        <view v-if="testResult" class="code-block">{{ testResult }}</view>
      </view>

      <view class="panel">
        <view class="panel-title">调用方式</view>
        <view class="doc-line">所有开放接口都需要请求头：</view>
        <view class="code-block">Authorization: Bearer API_KEY
X-Api-Timestamp: 当前秒级时间戳
X-Api-Signature: HMAC_SHA256(SECRET_KEY, timestamp + "." + method + "." + path + "." + body)</view>
        <view class="doc" v-for="item in endpointOptions" :key="item.path">
          <view class="panel-title small">{{ item.label }}</view>
          <view class="doc-line">POST {{ item.path }}</view>
          <view class="code-block">{{ prettyJson(item.sample) }}</view>
        </view>
      </view>
    </template>
  </view>
</template>

<script setup>
import { computed, ref } from "vue";
import { onShow } from "@dcloudio/uni-app";
import http from "@/http/http.js";
import { BASE_URL } from "@/utils/config.js";
import { goPage } from "@/utils/router.js";

const loading = ref(false);
const creating = ref(false);
const testing = ref(false);
const subscribingId = ref(0);
const profileStatus = ref("none");
const applyForm = ref({ company_name: "", contact_name: "" });
const keyForm = ref({ name: "", quota: 1000 });
const createdKey = ref({});
const apiKeys = ref([]);
const plans = ref([]);
const dashboard = ref({
  api_key_count: 0,
  today_calls: 0,
  total_calls: 0,
  total_tokens: 0,
  month_cost: 0,
  plan_name: "",
  subscription_status: "",
  today_quota_remaining: null,
  month_quota_remaining: null
});

const endpointOptions = [
  { label: "游戏 NPC 起名", path: "/openapi/npc-name", sample: { race: "人类", gender: "男", style: "东方玄幻" } },
  { label: "小说角色起名", path: "/openapi/novel-character", sample: { novel_type: "仙侠", gender: "女" } },
  { label: "地名/组织命名", path: "/openapi/location-name", sample: { style: "古风山门" } },
  { label: "宝宝起名", path: "/openapi/baby-name", sample: { surname: "张", gender: "男" } },
  { label: "公司品牌命名", path: "/openapi/company-name", sample: { industry: "人工智能", style: "科技感" } }
];
const endpointIndex = ref(0);
const currentEndpoint = computed(() => endpointOptions[endpointIndex.value] || endpointOptions[0]);
const testBody = ref(JSON.stringify(endpointOptions[0].sample, null, 2));
const testApiKey = ref("");
const testSecretKey = ref("");
const testResult = ref("");

const goLogs = () => goPage("/pages/developer/logs");
const money = (value) => Number(value || 0).toFixed(4).replace(/\.?0+$/, "");
const quotaText = (value) => value === null || value === undefined || Number(value) === 0 ? "不限" : String(value);
const cycleText = (value) => ({ month: "月", year: "年", once: "次" }[value] || value || "月");
const prettyJson = (value) => JSON.stringify(value, null, 2);

const loadData = async () => {
  try {
    const profile = await http.getDeveloperProfile();
    profileStatus.value = profile.status;
    if (profile.status !== "approved") return;
    const [dashboardRes, keyRes, planRes] = await Promise.all([
      http.getDeveloperDashboard(),
      http.getDeveloperApiKeys(),
      http.getDeveloperPlans()
    ]);
    dashboard.value = dashboardRes;
    apiKeys.value = keyRes || [];
    plans.value = planRes.items || [];
  } catch (error) {
    profileStatus.value = "none";
  }
};

const applyDeveloper = async () => {
  if (!applyForm.value.company_name || !applyForm.value.contact_name) {
    return uni.showToast({ title: "请填写申请信息", icon: "none" });
  }
  loading.value = true;
  try {
    const res = await http.applyDeveloper(applyForm.value);
    profileStatus.value = res.status;
    uni.showToast({ title: "申请已提交" });
  } finally {
    loading.value = false;
  }
};

const createKey = async () => {
  if (!keyForm.value.name) {
    return uni.showToast({ title: "请填写 Key 名称", icon: "none" });
  }
  creating.value = true;
  try {
    createdKey.value = await http.createDeveloperApiKey(keyForm.value);
    testApiKey.value = createdKey.value.api_key || testApiKey.value;
    testSecretKey.value = createdKey.value.secret_key || testSecretKey.value;
    await loadData();
  } finally {
    creating.value = false;
  }
};

const subscribePlan = async (planId) => {
  subscribingId.value = planId;
  try {
    await http.subscribeDeveloperPlan({ plan_id: planId, months: 1 });
    uni.showToast({ title: "套餐已开通" });
    await loadData();
  } finally {
    subscribingId.value = 0;
  }
};

const disableKey = async (id) => {
  await http.disableDeveloperApiKey(id);
  await loadData();
};

const deleteKey = async (id) => {
  uni.showModal({
    title: "删除 API Key",
    content: "删除后该 Key 将立即不可用，历史调用记录仍会保留。",
    success: async (res) => {
      if (!res.confirm) return;
      await http.deleteDeveloperApiKey(id);
      uni.showToast({ title: "已删除" });
      await loadData();
    }
  });
};

const changeEndpoint = (event) => {
  endpointIndex.value = event.detail.value;
  testBody.value = JSON.stringify(currentEndpoint.value.sample, null, 2);
};

const hmacSha256Hex = async (secret, message) => {
  if (!globalThis.crypto || !globalThis.crypto.subtle) {
    throw new Error("当前环境不支持 WebCrypto，请在 H5 浏览器中测试签名请求");
  }
  const encoder = new TextEncoder();
  const key = await globalThis.crypto.subtle.importKey(
    "raw",
    encoder.encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"]
  );
  const signature = await globalThis.crypto.subtle.sign("HMAC", key, encoder.encode(message));
  return Array.from(new Uint8Array(signature)).map((item) => item.toString(16).padStart(2, "0")).join("");
};

const runTest = async () => {
  if (!testApiKey.value || !testSecretKey.value) {
    return uni.showToast({ title: "请填写 API_KEY 和 SECRET_KEY", icon: "none" });
  }
  let body = "";
  try {
    body = JSON.stringify(JSON.parse(testBody.value));
  } catch (error) {
    return uni.showToast({ title: "请求 JSON 格式错误", icon: "none" });
  }
  testing.value = true;
  testResult.value = "";
  try {
    const timestamp = String(Math.floor(Date.now() / 1000));
    const signature = await hmacSha256Hex(testSecretKey.value, `${timestamp}.POST.${currentEndpoint.value.path}.${body}`);
    const res = await new Promise((resolve, reject) => {
      uni.request({
        url: BASE_URL + currentEndpoint.value.path,
        method: "POST",
        data: body,
        header: {
          "content-type": "application/json",
          authorization: `Bearer ${testApiKey.value}`,
          "x-api-timestamp": timestamp,
          "x-api-signature": signature
        },
        success: resolve,
        fail: reject
      });
    });
    testResult.value = JSON.stringify({ statusCode: res.statusCode, data: res.data }, null, 2);
    await loadData();
  } catch (error) {
    testResult.value = error.message || JSON.stringify(error);
  } finally {
    testing.value = false;
  }
};

onShow(loadData);
</script>

<style scoped>
.page { min-height: 100vh; padding: 30rpx; background: #f5f7fa; box-sizing: border-box; }
.topbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 28rpx; }
.title { font-size: 42rpx; font-weight: 700; color: #111827; }
.sub, .muted { color: #6b7280; font-size: 24rpx; margin-top: 8rpx; }
.ghost { margin: 0; background: #fff; color: #111827; border-radius: 8rpx; }
.stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 18rpx; margin-bottom: 24rpx; }
.stat, .panel, .key-item, .secret-box { background: #fff; border-radius: 10rpx; padding: 26rpx; }
.label { display: block; color: #6b7280; font-size: 24rpx; }
.value { display: block; color: #111827; font-size: 38rpx; font-weight: 700; margin-top: 12rpx; word-break: break-all; }
.value.small { font-size: 30rpx; }
.panel { margin-bottom: 24rpx; }
.panel-title { font-size: 30rpx; font-weight: 700; color: #111827; margin-bottom: 20rpx; }
.panel-title.small { font-size: 26rpx; margin-top: 24rpx; margin-bottom: 12rpx; }
.input { width: 100%; box-sizing: border-box; background: #ffffff; color: #111827; border: 1px solid #d1d5db; border-radius: 8rpx; padding: 20rpx; margin-bottom: 18rpx; }
.textarea { width: 100%; min-height: 220rpx; box-sizing: border-box; background: #fff; color: #111827; border: 1px solid #d1d5db; border-radius: 8rpx; padding: 20rpx; margin-bottom: 18rpx; font-size: 26rpx; }
.primary { background: #111827; color: #fff; border-radius: 10rpx; }
.warn { margin: 0; color: #92400e; background: #fffbeb; border-radius: 8rpx; }
.danger { margin: 0; color: #dc2626; background: #fff1f2; border-radius: 8rpx; }
.key-item, .plan { display: flex; justify-content: space-between; align-items: center; gap: 18rpx; margin-bottom: 18rpx; }
.plan { background: #f8fafc; border-radius: 10rpx; padding: 20rpx; }
.plan-name, .key-name { font-size: 30rpx; font-weight: 700; color: #111827; }
.plan-btn { margin: 0; flex-shrink: 0; background: #eef2ff; color: #1f3a8a; border-radius: 8rpx; }
.key-actions { display: flex; gap: 12rpx; flex-shrink: 0; }
.secret-box { margin-bottom: 24rpx; background: #ecfdf5; }
.secret-title { font-weight: 700; color: #047857; margin-bottom: 12rpx; }
.code { font-size: 22rpx; color: #064e3b; word-break: break-all; margin-top: 8rpx; }
.doc { border-top: 1px solid #edf0f5; margin-top: 20rpx; padding-top: 8rpx; }
.doc-line { color: #374151; font-size: 24rpx; line-height: 1.6; margin-bottom: 8rpx; }
.code-block { background: #111827; color: #f9fafb; border-radius: 8rpx; padding: 20rpx; font-size: 22rpx; line-height: 1.6; white-space: pre-wrap; word-break: break-all; margin-top: 16rpx; }
</style>
