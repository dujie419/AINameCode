<template>
  <view class="expert-nav-bottom">
    <view
      v-for="item in navItems"
      :key="item.key"
      :class="['expert-nav-item', active === item.key ? 'expert-nav-active' : '']"
      @tap="open(item)"
    >
      <view :class="['expert-nav-icon', item.icon]"></view>
      <view class="expert-nav-text">{{ item.label }}</view>
    </view>
  </view>
</template>

<script setup>
import { goPage } from "@/utils/router.js";

const props = defineProps({
  active: {
    type: String,
    default: "workbench"
  }
});

const navItems = [
  { key: "workbench", label: "工作台", url: "/pages/expert/workbench", icon: "expert-nav-workbench" },
  { key: "reviews", label: "评价", url: "/pages/expert-center/reviews", icon: "expert-nav-reviews" },
  { key: "afterSales", label: "售后", url: "/pages/expert-center/after-sales", icon: "expert-nav-after-sales" },
  { key: "profile", label: "个人中心", url: "/pages/expert-center/index", icon: "expert-nav-profile" }
];

const open = (item) => {
  if (item.key === props.active) {
    return;
  }
  goPage(item.url);
};
</script>

<style scoped>
.expert-nav-bottom {
  position: fixed;
  z-index: 20;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  height: 112rpx;
  padding-bottom: env(safe-area-inset-bottom);
  background: #fff;
  border-top: 1px solid #e7e7e7;
  box-shadow: 0 -2rpx 10rpx rgba(17, 24, 39, 0.06);
}

.expert-nav-item {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  color: #b7b7b7;
}

.expert-nav-active {
  color: #16a3e6;
}

.expert-nav-icon {
  position: relative;
  width: 44rpx;
  height: 44rpx;
  margin-bottom: 6rpx;
}

.expert-nav-workbench {
  border: 7rpx solid currentColor;
  border-radius: 8rpx;
  box-sizing: border-box;
}

.expert-nav-workbench::before {
  content: "";
  position: absolute;
  left: 9rpx;
  right: 9rpx;
  top: 12rpx;
  height: 6rpx;
  background: currentColor;
}

.expert-nav-reviews::before,
.expert-nav-reviews::after {
  content: "";
  position: absolute;
  border-radius: 8rpx;
  background: currentColor;
}

.expert-nav-reviews::before {
  left: 3rpx;
  top: 5rpx;
  width: 36rpx;
  height: 26rpx;
}

.expert-nav-reviews::after {
  left: 12rpx;
  top: 27rpx;
  width: 14rpx;
  height: 14rpx;
  transform: rotate(45deg);
}

.expert-nav-after-sales {
  border: 7rpx solid currentColor;
  border-radius: 50%;
  box-sizing: border-box;
}

.expert-nav-after-sales::before {
  content: "";
  position: absolute;
  left: 13rpx;
  top: -9rpx;
  width: 12rpx;
  height: 14rpx;
  background: #fff;
}

.expert-nav-profile::before {
  content: "";
  position: absolute;
  left: 10rpx;
  top: 0;
  width: 24rpx;
  height: 24rpx;
  border-radius: 50%;
  background: currentColor;
}

.expert-nav-profile::after {
  content: "";
  position: absolute;
  left: 3rpx;
  bottom: 0;
  width: 38rpx;
  height: 24rpx;
  border-radius: 20rpx 20rpx 6rpx 6rpx;
  background: currentColor;
}

.expert-nav-text {
  font-size: 26rpx;
  line-height: 1.2;
}
</style>
