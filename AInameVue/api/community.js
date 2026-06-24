import { request } from "@/utils/request.js";

export default {
  createCommunityPost: (data) => request("/community/posts", { method: "POST", data }),
  getCommunityPosts: (params = "") => request("/community/posts" + params, { method: "GET" }),
  getCommunityPostDetail: (id) => request(`/community/posts/${id}`, { method: "GET" }),
  voteCommunityPost: (id, data) => request(`/community/posts/${id}/vote`, { method: "POST", data }),
  getCommunityResult: (id) => request(`/community/posts/${id}/result`, { method: "GET" }),
  getCommunityRank: () => request("/community/rank", { method: "GET" })
};
