import { request } from "@/utils/request.js";

export default {
  getEmailCode: (email) => request("/auth/code?email=" + email, { method: "GET" }),
  register: (data) => request("/auth/register", { method: "POST", data }),
  login: (data) => request("/auth/login", { method: "POST", data })
};
