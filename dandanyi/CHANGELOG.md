# 单单易 (DanDanYi) 版本更新记录

**更新日期**: 2026-03-05
**版本**: v1.0.1
**项目**: 单单易 - 司机端订单管理助手

---

## 🎯 项目概述

**单单易** 是从 Miaoying（秒应）项目中分离出来的独立项目，专注于为网约车司机提供订单管理、OCR识别、智能推荐等功能。

- **域名**: dandanyi.com
- **服务器**: 阿里云 ECS (112.126.61.223)
- **数据库**: PostgreSQL (beijing_didi, beijing_auxiliary)
- **地图服务**: 天地图

---

## 🐛 Bug修复

### 修复天地图地理编码响应解析错误 ⭐ 核心修复

**问题描述**:
- 订单创建时，地理编码返回 `undefined, undefined`
- 导致所有订单缺少起点/终点坐标数据
- 最终导致公里数显示为 0 km

**根本原因**:
- 代码期望天地图API返回格式：`{ result: { location: {...} } }`
- 实际天地图API返回格式：`{ location: {...} }`

**修复内容**:
- 修改文件：`src/lib/tianditu/geocode.ts`（第151-170行）
- 修复：将 `data.result.location` 改为 `data.location`
- 修复：将 `data.result.address` 改为 `location.address`
- 添加：使用 `location.keyWord` 作为备用地址字段

---

## 📋 项目状态

### ✅ 已完成

1. **服务器部署**
   - Nginx 配置完成（80 → 6001 端口）
   - PM2 进程管理配置
   - 数据库创建和初始化

2. **数据库配置**
   - beijing_didi：业务数据库（订单、用户）
   - beijing_auxiliary：辅助数据库（天气、航班）
   - users 表结构完整（24个字段）

3. **API 服务配置**
   - 百度 OCR API
   - DeepSeek AI API
   - 天地图 API
   - 和风天气 API

4. **核心功能**
   - ✅ 用户登录（验证码）
   - ✅ OCR 订单识别
   - ✅ 订单管理
   - ⚠️ 地址距离计算（已修复，待部署）

### ⏳ 待完成

1. **部署代码更新**
   - 部署地理编码修复到服务器
   - 重启应用

2. **域名配置**
   - DNS 解析（等待域名审核通过）
   - SSL 证书安装

3. **功能测试**
   - 验证距离计算功能
   - 验证地图导航功能

---

## 🔄 与 Miaoying 的关系

### 项目分离

- **Miaoying (秒应)**: 原始项目，用于开发和测试
- **DanDanYi (单单易)**: 生产项目，部署到服务器

### 代码同步

核心功能保持同步：
- OCR 识别系统
- 订单管理模块
- 地图服务集成
- AI 智能推荐

---

## 🚀 部署步骤

### 1. 拉取最新代码

```bash
ssh root@112.126.61.223
cd /var/www/miaoying  # 或 /var/www/dandanyi
git pull origin master
```

### 2. 重启应用

```bash
pm2 restart miaoying
pm2 logs miaoying --lines 20
```

### 3. 验证功能

1. 访问 http://112.126.61.223
2. 登录系统
3. 上传订单截图
4. 检查公里数是否正确显示

---

## 📞 技术支持

- **开发者**: AI Assistant (Claude Code)
- **GitHub**: https://github.com/tanhaox/miaoying
- **服务器**: 阿里云 ECS (112.126.61.223)

---

**备注**: 此版本修复了订单公里数显示为 0 的关键问题，部署后请务必验证。
