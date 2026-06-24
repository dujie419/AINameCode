<script setup>
import { onShow } from "@dcloudio/uni-app";
import { goAdminLogin, goLogin } from "@/utils/router.js";

onShow(() => {
  const pages = getCurrentPages();
  const currentPage = pages[pages.length - 1];
  const route = currentPage ? currentPage.route : "";
  const whiteList = ["pages/login/login", "pages/register/register", "pages/admin/login"];

  if (whiteList.includes(route)) {
    return;
  }

  if (route.startsWith('pages/admin')) {
    const adminToken = uni.getStorageSync("admin_token");
    if (!adminToken) {
      goAdminLogin();
    }
    return;
  }

  const token = uni.getStorageSync("token");
  if (!token) {
    goLogin("", { relaunch: true });
  }
});
</script>

<style>
@import "@/styles/common.css";
</style>
