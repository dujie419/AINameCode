import { adminRequest } from "@/utils/request.js";

const buildQuery = (params = {}) => {
  return Object.keys(params)
    .filter((key) => params[key] !== undefined && params[key] !== null && params[key] !== "")
    .map((key) => `${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`)
    .join("&");
};

const withQuery = (url, params = {}) => {
  const query = buildQuery(params);
  return `${url}${query ? "?" + query : ""}`;
};

export default {
  login: (data) => adminRequest("/admin/login", { method: "POST", data }),
  statistics: () => adminRequest("/admin/dashboard/statistics", { method: "GET" }),
  users: (params = {}) => adminRequest(withQuery("/admin/users", params), { method: "GET" }),
  userDetail: (userId) => adminRequest(`/admin/users/${userId}`, { method: "GET" }),
  updateUserStatus: (userId, status) =>
    adminRequest(`/admin/users/${userId}/status`, {
      method: "PUT",
      data: { status }
    }),
  adjustUserBalance: (userId, data) => adminRequest(`/admin/users/${userId}/balance-adjust`, { method: "POST", data }),
  adjustUserQuota: (userId, data) => adminRequest(`/admin/users/${userId}/quota-adjust`, { method: "POST", data }),
  adjustUserMembership: (userId, data) => adminRequest(`/admin/users/${userId}/membership-adjust`, { method: "POST", data }),
  updateUserLevel: (userId, data) => adminRequest(`/admin/users/${userId}/level`, { method: "POST", data }),
  nameRecords: (params = {}) => adminRequest(withQuery("/admin/name-records", params), { method: "GET" }),
  experts: (params = {}) => adminRequest(withQuery("/admin/experts", params), { method: "GET" }),
  approveExpert: (expertId) => adminRequest(`/admin/experts/${expertId}/approve`, { method: "PUT" }),
  rejectExpert: (expertId) => adminRequest(`/admin/experts/${expertId}/reject`, { method: "PUT" }),
  partners: (params = {}) => adminRequest(withQuery("/admin/partners", params), { method: "GET" }),
  approvePartner: (partnerId) => adminRequest(`/admin/partners/${partnerId}/approve`, { method: "PUT" }),
  rejectPartner: (partnerId, reason = "审核拒绝") =>
    adminRequest(withQuery(`/admin/partners/${partnerId}/reject`, { reason }), { method: "PUT" }),
  partnerFinanceSummary: () => adminRequest("/admin/partner-finance/summary", { method: "GET" }),
  settlePartnerCommissions: () => adminRequest("/admin/partner-commissions/settle-due", { method: "POST" }),
  partnerCommissions: (params = {}) => adminRequest(withQuery("/admin/partner-commissions", params), { method: "GET" }),
  partnerWithdrawals: (params = {}) => adminRequest(withQuery("/admin/partner-withdrawals", params), { method: "GET" }),
  approvePartnerWithdrawal: (id) => adminRequest(`/admin/partner-withdrawals/${id}/approve`, { method: "PUT" }),
  rejectPartnerWithdrawal: (id, reason = "审核拒绝") =>
    adminRequest(withQuery(`/admin/partner-withdrawals/${id}/reject`, { reason }), { method: "PUT" }),
  developers: (params = {}) => adminRequest(withQuery("/admin/developers", params), { method: "GET" }),
  approveDeveloper: (developerId) => adminRequest(`/admin/developers/${developerId}/approve`, { method: "PUT" }),
  rejectDeveloper: (developerId) => adminRequest(`/admin/developers/${developerId}/reject`, { method: "PUT" }),
  apiKeys: (params = {}) => adminRequest(withQuery("/admin/api-keys", params), { method: "GET" }),
  apiUsageLogs: (params = {}) => adminRequest(withQuery("/admin/api-usage-logs", params), { method: "GET" }),
  billingRecords: (params = {}) => adminRequest(withQuery("/admin/billing-records", params), { method: "GET" }),
  plans: (params = {}) => adminRequest(withQuery("/admin/plans", params), { method: "GET" }),
  createPlan: (data) => adminRequest("/admin/plans", { method: "POST", data }),
  updatePlan: (planId, data) => adminRequest(`/admin/plans/${planId}`, { method: "PUT", data }),
  subscribeDeveloper: (developerId, data) =>
    adminRequest(`/admin/developers/${developerId}/subscription`, { method: "POST", data }),
  subscriptions: (params = {}) => adminRequest(withQuery("/admin/subscriptions", params), { method: "GET" }),
  createRateLimitRule: (data) => adminRequest("/admin/rate-limit-rules", { method: "POST", data }),
  rateLimitRules: (params = {}) => adminRequest(withQuery("/admin/rate-limit-rules", params), { method: "GET" }),
  billingSummaries: (params = {}) => adminRequest(withQuery("/admin/billing-summaries", params), { method: "GET" }),
  createApiReconciliation: (params = {}) => adminRequest(withQuery("/admin/api-reconciliations", params), { method: "POST" })
};
