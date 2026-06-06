# OpenClaw Android 内测 APK（Capacitor）

内测用 Android 壳：WebView 加载远程门户 `https://115.120.202.223`，**不上架应用商店**。在本机（Windows / macOS / Linux）编译 debug APK 后安装到手机验证。

> **勿在云服务器上编译 APK。** 生产机只跑 Docker + Nginx 门户；Android SDK / JDK 体积大且与 Web 部署无关。

## 分支与仓库

| 项 | 说明 |
|----|------|
| Git 分支 | **`apk-test`**（Android 工程与 Capacitor 配置） |
| 门户业务 | **`main`** |
| 远程仓库 | `git@github.com:maniac1um/openclaw_market_analyser.git` |

```bash
git clone git@github.com:maniac1um/openclaw_market_analyser.git
cd openclaw_market_analyser
git checkout apk-test
```

## 架构

```mermaid
flowchart LR
  APK[Debug APK] --> WebView[Capacitor WebView]
  WebView --> HTTPS["https://115.120.202.223"]
  HTTPS --> Nginx[Nginx + 自签证书]
  Nginx --> Portal[FastAPI + SPA]
```

- **Capacitor 8** + **Android WebView**
- `frontend/capacitor.config.ts` 中 `server.url` 指向生产门户（远程加载，改网页后一般**无需重装 APK**）
- **appId**：`com.openclaw.portal`
- **自签 HTTPS**：App 信任 `res/raw/openclaw_server.crt`（与 Nginx `/etc/nginx/ssl/openclaw.crt` 一致）

改网页后无需重装 APK，除非修改原生配置或服务器证书。

## 环境要求

| 依赖 | 说明 |
|------|------|
| Git + Node.js 22+ | 与 `frontend/` 一致 |
| [Android Studio](https://developer.android.com/studio) | **推荐**；含 SDK、Platform Tools、内置 JDK |
| JDK 17 或 21 **完整版** | 须含 `javac`；命令行构建时必需 |

### Android SDK 组件

Android Studio → **Settings → Android SDK**，确认已安装：

- **Android 16 (API 36)** — 与工程 `compileSdkVersion = 36` 一致
- **Android SDK Build-Tools**（35.0.0 或更高）
- **Android SDK Platform-Tools**（含 `adb`）

默认 SDK 路径：

| 系统 | 路径 |
|------|------|
| Linux / macOS | `~/Android/Sdk` |
| Windows | `C:\Users\<用户名>\AppData\Local\Android\Sdk` |

## 配置 SDK 路径（每台机器一次）

`local.properties` 已在 `.gitignore`，**不会提交**。

```bash
cd frontend/android
echo "sdk.dir=$HOME/Android/Sdk" > local.properties
```

Windows 示例：

```properties
sdk.dir=C\:\\Users\\YourName\\AppData\\Local\\Android\\Sdk
```

或使用环境变量：

```bash
export ANDROID_HOME=$HOME/Android/Sdk
export PATH=$PATH:$ANDROID_HOME/platform-tools
```

## 编译 debug APK

### 方式 A — 命令行（完整流程）

```bash
cd frontend
npm install
npm run build
npx cap sync android
cd android
./gradlew assembleDebug
```

**产物路径：**

```text
frontend/android/app/build/outputs/apk/debug/app-debug.apk
```

`frontend/package.json` 快捷脚本（在 `frontend/` 目录）：

| 命令 | 说明 |
|------|------|
| `npm run cap:sync` | 同步 Capacitor 到 Android |
| `npm run cap:open` | 用 Android Studio 打开工程 |
| `npm run android:debug` | `./gradlew assembleDebug` |

### 方式 B — Android Studio（最省心）

1. 安装 Android Studio
2. **Open** → 选择仓库内 `frontend/android`
3. 等待 Gradle Sync（自动生成 `local.properties`）
4. **Build → Build Bundle(s) / APK(s) → Build APK(s)**

无需手动配置 `JAVA_HOME` / `sdk.dir`。

## 安装到手机

**USB + adb：**

```bash
adb install -r frontend/android/app/build/outputs/apk/debug/app-debug.apk
```

或把 APK 传到手机，开启「允许未知来源」后直接安装。

## 真机验证清单

1. 打开 App → 显示登录页（远程 `https://115.120.202.223`）
2. 登录 / 注册
3. 首页 OpenClaw 对话（WebSocket `wss://`）
4. 专题分析：列表 → 详情 → 返回

若 **白屏**：Logcat 过滤 `SSLHandshakeException` — 多为证书与 `openclaw_server.crt` 不一致，或 IP 变更未更新证书。

## 常见错误

### `does not provide the required capabilities: [JAVA_COMPILER]`

只装了 JRE 或未装 JDK。安装完整 JDK 并设置 `JAVA_HOME`：

```bash
sudo apt update
sudo apt install openjdk-17-jdk   # 或 openjdk-21-jdk
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
javac -version
```

### `SDK location not found`

未安装 Android SDK，或未配置 `sdk.dir`。见上文「配置 SDK 路径」。

### `Failed to install ... platforms;android-36`

SDK Manager 未安装 **Android 16 (API 36)**。

### `WARNING: Using flatDir should be avoided`

Capacitor 常见 Gradle 提示，**可忽略**，不影响 APK。

## 更新服务器证书

Nginx 证书轮换后，需更新 App 内嵌证书并**重新编译 APK**：

```bash
# 在服务器上导出（路径按实际 Nginx 配置）
openssl x509 -in /etc/nginx/ssl/openclaw.crt -outform PEM \
  -out frontend/android/app/src/main/res/raw/openclaw_server.crt

cd frontend && npx cap sync android
cd android && ./gradlew assembleDebug
```

## 相关文件

| 路径 | 说明 |
|------|------|
| `frontend/capacitor.config.ts` | 远程 URL、`appId` |
| `frontend/android/` | Android 工程 |
| `frontend/android/local.properties.example` | SDK 路径模板 |
| `frontend/android/app/src/main/res/xml/network_security_config.xml` | 自签证书信任策略 |
| `frontend/android/app/src/main/res/raw/openclaw_server.crt` | 服务器公钥证书 |

## 安全说明

`network_security_config.xml` 仅信任 OpenClaw 服务器自签证书，**仅用于内测 debug 包**。正式对外分发应使用 Let's Encrypt 等公网可信证书，并移除 debug 专用配置。

## 服务器侧说明

生产服务器（`115.120.202.223`）职责：

- Docker 运行 FastAPI + SPA
- Nginx 443 反代与 TLS
- **不在此机安装 Android SDK / JDK 用于打 APK**

Web 门户部署见 [server-deployment.md](server-deployment.md)。
