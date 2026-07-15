# cn-ex · 中国制霸

中国省级行政区域「制霸」标记工具：点亮去过的省，分数实时计算，**用 URL 参数 `?l=` 分享状态**。

体验与交互主要参考 [JapanEx 制县等级](https://zhung.com.tw/japanex/)：简化方块地图、等级色块、点选上色、可分享的状态串。  
实现为轻量静态页（无后端、无账号）。

## 打开

```bash
cd cn-ex
pnpm dev
# 或：python3 -m http.server 5178
```

浏览器访问：<http://127.0.0.1:5178/>

带状态示例：

```text
http://127.0.0.1:5178/?l=0050000000000033524303013330454033
```

可选标题：`?l=...&t=我的足迹`（会显示在地图标题）。

## 功能

| 能力 | 说明 |
| --- | --- |
| 点省设等级 | 居住 5 / 短居 4 / 游玩 3 / 出差 2 / 路过 1 / 没去过 0 |
| `?l=` 分享 | 34 位数字串，每位一省；改动时 `history.replaceState` 同步地址栏 |
| localStorage | key：`cn-ex-levels`；无 URL 时兜底恢复 |
| 复制链接 | 一键复制当前完整 URL |
| 保存图片 | SVG → Canvas → PNG 预览/下载 |
| 清空 | 重置全部为 0 |

### 状态优先级

1. 打开时若有 `?l=` → 以 URL 为准，并写回 localStorage  
2. 否则读 localStorage  
3. 每次改等级 → 更新 localStorage + 地址栏 `?l=`

### 省份顺序（勿改）

顺序一旦发布就应冻结，否则旧链接会错位：

```text
黑龙江 甘肃 吉林 内蒙古 山东 河北 北京 天津
西藏 新疆 河南 安徽 山西 湖北 青海 辽宁
广东 江苏 江西 浙江 福建 上海 陕西 湖南
广西 香港 澳门 贵州 重庆 四川 云南 宁夏
台湾 海南
```

## 等级约定

与 JapanEx 语义对齐的个人标准示例：

- **5 居住**：住过年以上  
- **4 短居**：住过月以上  
- **3 游玩**：旅行过  
- **2 出差**：去过但几乎没玩  
- **1 路过**：车船路过 / 飞机经停  
- **0 没去过**

## 目录

```text
cn-ex/
├── index.html
├── styles.css
├── app.js          # 地图、状态、URL、导出
├── package.json
└── README.md
```

## 致谢

- 交互与呈现参考：[JapanEx](https://zhung.com.tw/japanex/)  
- 中国省级简化方块地图轮廓常见于开源制霸类作品；本仓库以 JapanEx 为体验主参考独立实现分享与 UI。

## License

MIT


## 部署

- 生产域名：<https://cn-ex.ziki.top>
- 平台：Vercel（静态托管，无 build）
- DNS：Cloudflare `CNAME cn-ex` → Vercel 项目域名页给出的 `*.vercel-dns-*.com`（DNS only / 灰云）

本地预览：

```bash
pnpm dev
```
