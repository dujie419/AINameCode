export const goPage = (url, options = {}) => {
  const { relaunch = false, redirect = false } = options;

  // #ifdef H5
  window.location.hash = `#${url}`;
  return;
  // #endif

  if (relaunch) {
    uni.reLaunch({ url });
    return;
  }

  if (redirect) {
    uni.redirectTo({ url });
    return;
  }

  uni.navigateTo({ url });
};

export const goLogin = (mode = "", options = {}) => {
  const query = mode ? `?mode=${mode}` : "";
  goPage(`/pages/login/login${query}`, options);
};

export const goAdminLogin = (options = {}) => {
  goLogin("admin", { redirect: true, ...options });
};
