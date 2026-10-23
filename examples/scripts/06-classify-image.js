// 需要 v1.4.0、图片分类凭据和 screenshot.png；真实服务可能计费。
const candidates = await models.getAvailableOfType("classifier");
const vision = candidates.find(m => m.input?.includes("image"));
if (!vision) throw new Error("没有可用的图片分类器");
const photo = await tools.read({ path: "screenshot.png" });
if (photo.type !== "image") throw new Error("需要图片块");
const result = await models.classify(vision, {
  state: { task: "检查页面布局" },
  images: [photo],
  questions: {
    broken: {
      type: "bool",
      instructions: "图片中是否有重叠或被截断的内容？",
      criteria: { true: "存在布局缺陷", false: "未发现布局缺陷" },
    },
  },
});
if (result.stopReason !== "stop") {
  throw new Error(result.errorMessage ?? result.stopReason);
}
const answer = result.answers.broken;
if (answer?.type !== "bool") throw new Error("分类回答类型不符");
text({ probability: answer.probability });
