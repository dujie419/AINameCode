import { BASE_URL } from "@/utils/config.js";
import { goAdminLogin, goLogin } from "@/utils/router.js";

const parseErrorMessage = (data, fallback = "服务器请求失败") => {
  if (data && Array.isArray(data.detail)) {
    return data.detail[0].msg || "参数校验失败";
  }

  if (data && typeof data.detail === "string") {
    return data.detail;
  }

  return fallback;
};

export const request = (url, options = {}) => {
  const token = uni.getStorageSync("token");

  return new Promise((resolve, reject) => {
    uni.request({
      url: BASE_URL + url,
      timeout: 180000,
      header: {
        "content-type": "application/json",
        authorization: token ? `Bearer ${token}` : ""
      },
      ...options,
      success: (res) => {
        if (res.statusCode === 200) {
          resolve(res.data);
          return;
        }

        if (res.statusCode === 401 || res.statusCode === 403) {
          uni.removeStorageSync("token");
          uni.removeStorageSync("user");
          goLogin("", { relaunch: true });
        }

        uni.showToast({
          title: String(parseErrorMessage(res.data)),
          icon: "none",
          duration: 3000
        });

        reject(res.data);
      },
      fail: (err) => {
        const errMsg = err && err.errMsg ? err.errMsg : JSON.stringify(err || {});
        uni.showModal({
          title: "网络连接失败",
          content: `请确认后端已启动，并检查接口地址：${BASE_URL}\n${errMsg}`,
          showCancel: false
        });
        reject(err);
      }
    });
  });
};

export const adminRequest = (url, options = {}) => {
  const token = uni.getStorageSync("admin_token");

  return new Promise((resolve, reject) => {
    uni.request({
      url: BASE_URL + url,
      timeout: 180000,
      header: {
        "content-type": "application/json",
        authorization: token ? `Bearer ${token}` : ""
      },
      ...options,
      success: (res) => {
        if (res.statusCode === 200) {
          resolve(res.data);
          return;
        }

        if (res.statusCode === 401) {
          uni.removeStorageSync("admin_token");
          uni.removeStorageSync("admin_role");
          goAdminLogin();
        }

        uni.showToast({
          title: String(parseErrorMessage(res.data)),
          icon: "none",
          duration: 3000
        });

        reject(res.data);
      },
      fail: (err) => {
        const errMsg = err && err.errMsg ? err.errMsg : JSON.stringify(err || {});
        uni.showModal({
          title: "网络连接失败",
          content: `请确认后端已启动，并检查接口地址：${BASE_URL}\n${errMsg}`,
          showCancel: false
        });
        reject(err);
      }
    });
  });
};

export const uploadFile = (url, filePath) => {
  const token = uni.getStorageSync("token");

  return new Promise((resolve, reject) => {
    uni.uploadFile({
      url: BASE_URL + url,
      timeout: 180000,
      filePath,
      name: "file",
      header: {
        authorization: token ? `Bearer ${token}` : ""
      },
      success: (res) => {
        if (res.statusCode === 200) {
          resolve(JSON.parse(res.data));
          return;
        }

        uni.showToast({ title: "文件上传失败", icon: "none" });
        reject(res);
      },
      fail: (err) => {
        uni.showToast({ title: "网络异常，上传中断", icon: "none" });
        reject(err);
      }
    });
  });
};
