import authApi from "@/api/auth.js";
import nameApi from "@/api/name.js";
import brandApi from "@/api/brand.js";
import expertApi from "@/api/expert.js";
import userApi from "@/api/user.js";
import communityApi from "@/api/community.js";
import developerApi from "@/api/developer.js";
import knowledgeApi from "@/api/knowledge.js";
import growthApi from "@/api/growth.js";

// 兼容旧页面的统一入口；新代码优先直接引入对应业务域 API。
export default {
  ...authApi,
  ...nameApi,
  ...brandApi,
  ...expertApi,
  ...userApi,
  ...communityApi,
  ...developerApi,
  ...knowledgeApi,
  ...growthApi
};
