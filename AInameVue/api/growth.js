import { request } from "@/utils/request.js";

export default {
  getInviteSummary: () => request("/growth/invite/summary", { method: "GET" }),
  getInviteRecords: (params = "") => request("/growth/invite/records" + params, { method: "GET" }),
  applyPartner: (data) => request("/growth/partner/apply", { method: "POST", data }),
  getPartnerProfile: () => request("/growth/partner/profile", { method: "GET" }),
  getPartnerAttributions: (params = "") => request("/growth/partner/attributions" + params, { method: "GET" }),
  getPartnerFinanceSummary: () => request("/growth/partner/finance/summary", { method: "GET" }),
  getPartnerCommissions: (params = "") => request("/growth/partner/commissions" + params, { method: "GET" }),
  settlePartnerCommissions: () => request("/growth/partner/commissions/settle-due", { method: "POST" }),
  createPartnerWithdrawal: (data) => request("/growth/partner/withdrawals", { method: "POST", data }),
  getPartnerWithdrawals: (params = "") => request("/growth/partner/withdrawals" + params, { method: "GET" })
};
