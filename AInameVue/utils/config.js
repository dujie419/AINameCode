const DEFAULT_API_PORT = 8000;
const DEFAULT_LAN_HOST = "192.168.0.105";

export const getBaseUrl = () => {
  const envBaseUrl = process.env.VUE_APP_API_BASE_URL;
  const lanBaseUrl = `http://${DEFAULT_LAN_HOST}:${DEFAULT_API_PORT}`;

  // #ifdef H5
  if (typeof window !== "undefined" && window.location && window.location.hostname) {
    const host = window.location.hostname;
    if (host === "localhost" || host === "127.0.0.1") {
      return `http://127.0.0.1:${DEFAULT_API_PORT}`;
    }
    return `${window.location.protocol}//${host}:${DEFAULT_API_PORT}`;
  }
  // #endif

  if (envBaseUrl) {
    return envBaseUrl;
  }

  return lanBaseUrl;
};

export const BASE_URL = getBaseUrl();
