<template>
  <view>
    <view class="main-nav-bottom">
      <view
        v-for="item in navItems"
        :key="item.key"
        :class="['main-nav-bottom-item', active === item.key ? 'main-nav-active' : '']"
        @tap="open(item)"
      >
        <view :class="['main-nav-icon', item.icon]"></view>
        <view class="main-nav-text">{{ item.label }}</view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { goPage } from "@/utils/router.js";

const props = defineProps({
  active: {
    type: String,
    default: "home"
  }
});

const navItems = [
  { key: "home", label: "首页", url: "/pages/index/index", icon: "main-nav-home-icon" },
  { key: "expert", label: "专家", url: "/pages/expert/index", icon: "main-nav-expert-icon" },
  { key: "community", label: "灵感池", url: "/pages/community/index", icon: "main-nav-cart-icon" },
  { key: "user", label: "个人中心", url: "/pages/user/center", icon: "main-nav-user-icon" }
];

const open = (item) => {
  if (item.key === props.active) {
    return;
  }
  goPage(item.url);
};
</script>

<style scoped>
.main-nav-active {
  color: #16a3e6;
}

.main-nav-bottom {
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

.main-nav-bottom-item {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  color: #b7b7b7;
}

.main-nav-icon {
  position: relative;
  width: 44rpx;
  height: 44rpx;
  margin-bottom: 6rpx;
}

.main-nav-home-icon::before {
  content: "";
  position: absolute;
  left: 4rpx;
  top: 16rpx;
  width: 36rpx;
  height: 28rpx;
  background: currentColor;
}

.main-nav-home-icon::after {
  content: "";
  position: absolute;
  left: 9rpx;
  top: 0;
  width: 26rpx;
  height: 26rpx;
  background: currentColor;
  transform: rotate(45deg);
}

.main-nav-expert-icon {
  border: 8rpx solid currentColor;
  border-top: 0;
  border-radius: 0 0 8rpx 8rpx;
  box-sizing: border-box;
}

.main-nav-expert-icon::before {
  content: "";
  position: absolute;
  left: 8rpx;
  top: -12rpx;
  width: 26rpx;
  height: 12rpx;
  border: 5rpx solid currentColor;
  border-bottom: 0;
  border-radius: 12rpx 12rpx 0 0;
}

.main-nav-cart-icon {
  border-bottom: 10rpx solid currentColor;
  border-left: 8rpx solid transparent;
  border-right: 8rpx solid transparent;
  transform: skewX(-8deg);
  box-sizing: border-box;
}

.main-nav-cart-icon::before,
.main-nav-cart-icon::after {
  content: "";
  position: absolute;
  bottom: -20rpx;
  width: 9rpx;
  height: 9rpx;
  border-radius: 50%;
  background: currentColor;
}

.main-nav-cart-icon::before {
  left: 4rpx;
}

.main-nav-cart-icon::after {
  right: 4rpx;
}

.main-nav-user-icon::before {
  content: "";
  position: absolute;
  left: 10rpx;
  top: 0;
  width: 24rpx;
  height: 24rpx;
  border-radius: 50%;
  background: currentColor;
}

.main-nav-user-icon::after {
  content: "";
  position: absolute;
  left: 3rpx;
  bottom: 0;
  width: 38rpx;
  height: 24rpx;
  border-radius: 20rpx 20rpx 6rpx 6rpx;
  background: currentColor;
}

.main-nav-text {
  font-size: 26rpx;
  line-height: 1.2;
}
</style>
