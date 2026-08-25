# 青甘大环线旅行记账台

一个为 4 人 11 天青甘大环线自驾游设计的旅行记账与行程管理工作台。

## 功能特性

- 📊 **多人记账** — 4 人费用分摊、按人统计
- 🗓️ **行程管理** — 11 天行程规划与记录
- ☁️ **云端同步** — 基于 textdb.online 免费云存储实时同步
- 📱 **PWA 支持** — 可安装到手机主屏幕，离线可用
- 📱 **响应式设计** — 桌端与移动端自适应

## 技术栈

- 纯原生 HTML + CSS + JavaScript（单文件，无外部依赖）
- textdb.online 作为云存储后端
- Service Worker (Blob 注入) 实现 PWA 离线缓存

## 访问

- 线上地址: https://htwo666.github.io/qinggan-trip-ledger/
- 原始来源: WorkBuddy 资料库部署的工作台

## 部署

本项目为单页静态站点，已通过 GitHub Pages 自动部署。主分支 `main` 推送后会自动更新线上版本。
