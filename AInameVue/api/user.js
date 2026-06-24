import { request, uploadFile } from "@/utils/request.js";

export default {
  getUserProfile: () => request("/user/profile", { method: "GET" }),
  getQuotaSummary: () => request("/user/quota/summary", { method: "GET" }),
  updateUserProfile: (data) => request("/user/profile", { method: "PUT", data }),
  uploadUserAvatar: (filePath) => uploadFile("/user/avatar/upload", filePath),
  getUserBalance: () => request("/user/balance", { method: "GET" }),
  createRecharge: (data) => request("/user/recharge", { method: "POST", data }),
  virtualPay: (paymentNo) => request(`/user/payments/${paymentNo}/virtual-pay`, { method: "POST" }),
  getPaymentOrder: (paymentNo) => request(`/user/payments/${paymentNo}`, { method: "GET" }),
  createOrderPayment: (id, provider = "virtual") => request(`/user/orders/${id}/payment?provider=${provider}`, { method: "POST" }),
  getMembershipPlans: () => request("/user/membership/plans", { method: "GET" }),
  getCurrentMembership: () => request("/user/membership/current", { method: "GET" }),
  createMembershipOrder: (data) => request("/user/membership/orders", { method: "POST", data }),
  refundUserOrder: (id, data) => request(`/user/orders/${id}/refund`, { method: "POST", data }),
  createInvoice: (data) => request("/user/invoices", { method: "POST", data }),
  getUserOrders: (params = "") => request("/user/orders" + params, { method: "GET" }),
  getUserOrderDetail: (id) => request(`/user/orders/${id}`, { method: "GET" }),
  payUserOrder: (id) => request(`/user/orders/${id}/pay`, { method: "POST" }),
  getWalletTransactions: (params = "") => request("/user/wallet/transactions" + params, { method: "GET" })
};
