import { request } from "@/utils/request.js";

export default {
  applyExpert: (data) => request("/expert/apply", { method: "POST", data }),
  getExperts: (params = "") => request("/experts" + params, { method: "GET" }),
  getExpertDetail: (id) => request(`/experts/${id}`, { method: "GET" }),
  createExpertOrder: (data) => request("/expert-orders", { method: "POST", data }),
  getExpertOrder: (id) => request(`/expert-orders/${id}`, { method: "GET" }),
  confirmExpertOrder: (id) => request(`/expert-orders/${id}/confirm`, { method: "POST" }),
  createExpertReview: (id, data) => request(`/expert-orders/${id}/review`, { method: "POST", data }),
  getExpertReviews: (id, params = "") => request(`/experts/${id}/reviews${params}`, { method: "GET" }),
  createAfterSale: (id, data) => request(`/expert-orders/${id}/after-sales`, { method: "POST", data }),
  getAfterSales: (id) => request(`/expert-orders/${id}/after-sales`, { method: "GET" }),
  getExpertWorkbenchOrders: () => request("/expert/orders", { method: "GET" }),
  submitExpertReport: (id, data) => request(`/expert/orders/${id}/report`, { method: "POST", data }),
  getExpertCenterProfile: () => request("/expert/profile", { method: "GET" }),
  updateExpertCenterProfile: (data) => request("/expert/profile", { method: "PUT", data }),
  getExpertCenterStatistics: () => request("/expert/center/statistics", { method: "GET" }),
  getExpertCenterOrders: (params = "") => request("/expert/center/orders" + params, { method: "GET" }),
  acceptExpertCenterOrder: (id) => request(`/expert/center/orders/${id}/accept`, { method: "POST" }),
  completeExpertCenterOrder: (id) => request(`/expert/center/orders/${id}/complete`, { method: "POST" }),
  settleExpertCenterOrder: (id) => request(`/expert/center/orders/${id}/settle`, { method: "POST" }),
  getExpertCenterIncome: (params = "") => request("/expert/center/income" + params, { method: "GET" }),
  createExpertWithdrawal: (data) => request("/expert/center/withdrawals", { method: "POST", data }),
  getExpertWithdrawals: (params = "") => request("/expert/center/withdrawals" + params, { method: "GET" }),
  getExpertCenterReviews: (params = "") => request("/expert/center/reviews" + params, { method: "GET" }),
  replyExpertReview: (id, data) => request(`/expert/center/reviews/${id}/reply`, { method: "POST", data }),
  getExpertCenterAfterSales: (params = "") => request("/expert/center/after-sales" + params, { method: "GET" })
};
