import { uploadFile } from "@/utils/request.js";

export default {
  uploadKnowledge: (filePath) => uploadFile("/knowledge/upload", filePath)
};
