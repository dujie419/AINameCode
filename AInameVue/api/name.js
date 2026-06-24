import { request } from "@/utils/request.js";

export default {
  generateName: (data) => request("/name/generate", { method: "POST", data }),
  feedbackName: (data) => request("/name/feedback", { method: "POST", data })
};
