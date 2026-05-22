module.exports = function (api) {
  api.cache(true);
  return {
    presets: [
      ["babel-preset-expo", { jsxImportSource: "nativewind" }],
      "nativewind/babel",
    ],
    // NOTE: 애니메이션(reanimated) 도입 시 "react-native-reanimated/plugin"을
    // plugins 배열 마지막에 추가할 것. 현재 미사용이라 제거(번들 안정).
  };
};
