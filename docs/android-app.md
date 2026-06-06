# OpenClaw Android App（Capacitor）

内测用 Android 壳：WebView 加载远程门户 `https://115.120.202.223`，不上架应用商店。

## 架构

- **Capacitor 8** + **Android WebView**
- `frontend/capacitor.config.ts` 中 `server.url` 指向生产门户
- 自签 HTTPS：信任 `res/raw/openclaw_server.crt`（与 Nginx `/etc/nginx/ssl/openclaw.crt` 一致）

改网页后 **无需重装 APK**（除非修改原生配置或证书）。

## 环境要求

在 **本机**（Windows / macOS / Linux）安装：

- [Android Studio](https://developer.android.com/studio)（含 SDK、Platform Tools）
- Node.js 22+（与 `frontend/` 一致）
- JDK 17+

> 服务器上通常只跑 Web 服务；APK 在开发机构建。

## 首次构建

```bash
cd frontend
npm install
npm run build
npx cap sync android
```

用 Android Studio 打开 **`frontend/android`**，或命令行：

```bash
cd frontend/android
./gradlew assembleDebug
```

Debug APK 路径：

`frontend/android/app/build/outputs/apk/debug/app-debug.apk`

## 安装到真机

```bash
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

或把 APK 传到手机安装（需允许「未知来源」）。

## 验证清单

1. 打开 App → 显示登录页  
2. 登录 / 注册  
3. 首页 OpenClaw 对话（WebSocket）  
4. 专题分析：列表 → 详情 → 返回  

若白屏，在 Logcat 过滤 `SSLHandshakeException` — 多为证书未信任或 IP 变更后未更新 `openclaw_server.crt`。

## 更新服务器证书

Nginx 证书轮换后：

```bash
openssl x509 -in /etc/nginx/ssl/openclaw.crt -outform PEM \
  -out frontend/android/app/src/main/res/raw/openclaw_server.crt
cd frontend && npx cap sync android
# 重新 assembleDebug
```

## 常用命令

| 命令 | 说明 |
|------|------|
| `npm run cap:sync` | 同步 Capacitor 配置到 Android |
| `npm run cap:open` | 用 Android Studio 打开工程 |
| `npm run android:debug` | 命令行打 debug APK |

## 分支

Android 相关开发在 **`apk-test`** 分支；门户业务仍在 **`main`**。

## 安全说明

`network_security_config.xml` 仅信任 OpenClaw 服务器自签证书，**仅用于内测 debug 包**。正式对外分发应使用 Let's Encrypt 等公网可信证书，并移除 debug 专用配置。
