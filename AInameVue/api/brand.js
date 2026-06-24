import { request } from "@/utils/request.js";

export default {
  generateBrandVisual: (data) => request("/brand/visual/generate", { method: "POST", data }),
  generateBrandLogoImage: (data) => request("/brand/visual/image", { method: "POST", data })
};
