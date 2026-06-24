import { request } from "@/utils/request.js";

export default {
  applyDeveloper: (data) => request("/developer/apply", { method: "POST", data }),
  getDeveloperProfile: () => request("/developer/profile", { method: "GET" }),
  getDeveloperDashboard: () => request("/developer/dashboard", { method: "GET" }),
  getDeveloperPlans: () => request("/developer/plans?page=1&page_size=50", { method: "GET" }),
  subscribeDeveloperPlan: (data) => request("/developer/subscription", { method: "POST", data }),
  createDeveloperApiKey: (data) => request("/developer/api-keys", { method: "POST", data }),
  getDeveloperApiKeys: () => request("/developer/api-keys", { method: "GET" }),
  disableDeveloperApiKey: (id) => request(`/developer/api-keys/${id}/disable`, { method: "PUT" }),
  deleteDeveloperApiKey: (id) => request(`/developer/api-keys/${id}`, { method: "DELETE" }),
  getDeveloperLogs: (params = "") => request("/developer/logs" + params, { method: "GET" })
};
