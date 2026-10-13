# SiliconFlow 生图 API —— 各模型 Body 参数对照

> 来源：<https://docs.siliconflow.com/en/api-reference/images/images-generations>
> 整理时间：2026-10-13（文档页共 10 个模型 Tab，覆盖 12 个模型 ID）

## 1. 通用部分

| 项 | 值 |
|---|---|
| 接口 | `POST /v1/images/generations` |
| 完整地址 | `https://api.siliconflow.com/v1/images/generations`（与本仓库 `DEFAULT_BASE_URL` 一致，国际站） |
| 认证 | Header `Authorization: Bearer <SILICONFLOW_API_KEY>` |
| Content-Type | `application/json` |
| 返回 | `{ "images": [{ "url": "..." }], "timings": { "inference": 123 }, "seed": 123 }` |
| ⚠️ 时效 | 图片 URL **仅 1 小时有效**，需立即下载落盘 |

**所有模型共有**：`model`、`prompt`（必填）。
**全部模型共有**：`seed`（`0 <= x <= 9999999999`，整数）。
除此之外参数因模型而异，**没有统一超集** —— 传了模型不支持的字段可能报错或被忽略。

## 2. 模型 Tab ↔ 模型 ID

| 文档 Tab | 可选 `model` ID | 备注 |
|---|---|---|
| FLUX.2-pro | `black-forest-labs/FLUX.2-pro` | 默认单选项 |
| FLUX.2-flex | `black-forest-labs/FLUX.2-flex` | 默认单选项 |
| Qwen-Image | `Qwen/Qwen-Image`、`Qwen/Qwen-Image-Edit` | 唯一含"编辑"模型的 Tab |
| Z-Image | `Tongyi-MAI/Z-Image-Turbo` | **本仓库默认文生图模型** |
| FLUX.1-Kontext | `black-forest-labs/FLUX.1-Kontext-max`、`black-forest-labs/FLUX.1-Kontext-pro` | 图生图，默认 max |
| FLUX.1-Kontext-dev | `black-forest-labs/FLUX.1-Kontext-dev` | 图生图 |
| FLUX-1.1-pro | `black-forest-labs/FLUX-1.1-pro` | 用 width/height 而非 image_size |
| FLUX-1.1-pro-Ultra | `black-forest-labs/FLUX-1.1-pro-Ultra` | 参数最全 |
| FLUX.1-schnell | `black-forest-labs/FLUX.1-schnell` | ⚠️ 本仓库已知：S3 预签名 URL 403 |
| FLUX.1-dev | `black-forest-labs/FLUX.1-dev` | ⚠️ 同上 |

## 3. 逐模型参数

图例：**必** = required；`默认 x` = 文档给出的默认值；范围按文档 `Required range` 原样抄录。

### 3.1 FLUX.2-pro

| 参数 | 类型 | 必填 | 约束 / 可选值 |
|---|---|---|---|
| `model` | enum | 必 | 仅 `black-forest-labs/FLUX.2-pro` |
| `prompt` | string | 必 | —— |
| `image_size` | enum | 否 | 默认 `512x512`；`512x512` / `768x1024` / `1024x768` / `576x1024` / `1024x576` |
| `seed` | integer | 否 | `0..9999999999` |
| `output_format` | enum | 否 | 默认 `png`；`png` / `jpeg` |

> 只支持 512 档分辨率，**没有** batch_size / negative_prompt / steps。

### 3.2 FLUX.2-flex

| 参数 | 类型 | 必填 | 约束 / 可选值 |
|---|---|---|---|
| `model` | enum | 必 | 仅 `black-forest-labs/FLUX.2-flex` |
| `prompt` | string | 必 | —— |
| `image_size` | enum | 否 | 默认 `512x512`；同 FLUX.2-pro 的 5 档 |
| `seed` | integer | 否 | `0..9999999999` |
| `cfg` | number | 否 | `0.1..20`，见下方 ⚠️ |
| `num_inference_steps` | integer | 否 | 默认 `25`；`1..50` |
| `output_format` | enum | 否 | 默认 `png`；`png` / `jpeg` |

> ⚠️ **文档自相矛盾**：`cfg` 字段在 FLUX.2-flex 下也列出，但其描述原文写
> "This field is only applicable to **Qwen/Qwen-Image** models"。推测是文档从
> Qwen-Image 复制粘贴所致，实际是否生效需实测。

### 3.3 Qwen-Image

| 参数 | 类型 | 必填 | 约束 / 可选值 |
|---|---|---|---|
| `model` | enum | 必 | `Qwen/Qwen-Image` / `Qwen/Qwen-Image-Edit`（无默认值） |
| `prompt` | string | 必 | —— |
| `negative_prompt` | string | 否 | 负面提示词 |
| `image_size` | string | **必** | 见下方推荐值 |
| `batch_size` | integer | 否 | 默认 `1`；`1..4` |
| `seed` | integer | 否 | `0..9999999999` |
| `num_inference_steps` | integer | 否 | 默认 `20`；`1..100` |
| `guidance_scale` | number | 否 | 默认 `7.5`；`0..20`。越大越贴合 prompt，越小越有创造性 |
| `cfg` | number | 否 | `0.1..20`，**Qwen-Image 专属**；生成文字场景需 >1，官方配置 50 steps + CFG 4.0，过小几乎无法生成文字 |
| `image` | string | 否 | base64，形如 `data:image/png;base64, XXX`。**供 `Qwen/Qwen-Image-Edit` 使用** |

`image_size` 推荐值（文档称"强烈建议"）：

| 比例 | 尺寸 | 比例 | 尺寸 |
|---|---|---|---|
| 1:1 | `1328x1328` | 3:4 | `1140x1472` |
| 16:9 | `1664x928` | 3:2 | `1584x1056` |
| 9:16 | `928x1664` | 2:3 | `1056x1584` |
| 4:3 | `1472x1140` | | |

### 3.4 Z-Image（本仓库默认模型）

| 参数 | 类型 | 必填 | 约束 / 可选值 |
|---|---|---|---|
| `model` | enum | 必 | 仅 `Tongyi-MAI/Z-Image-Turbo`（无默认值） |
| `prompt` | string | 必 | —— |
| `negative_prompt` | string | 否 | 负面提示词 |
| `image_size` | string | **必** | 推荐：`512x512`(1:1) / `768x1024`(3:4) / `1024x576`(16:9) / `576x1024`(9:16) |
| `seed` | integer | 否 | `0..9999999999` |

> 参数极简：**没有** batch_size、output_format、steps。注意文档里 `image_size`
> 标为 Required，「推荐值」只是建议，非枚举白名单。

### 3.5 FLUX.1-Kontext（图生图，`-max` / `-pro`）

| 参数 | 类型 | 必填 | 约束 / 可选值 |
|---|---|---|---|
| `model` | enum | 必 | 默认 `black-forest-labs/FLUX.1-Kontext-max`；可选 `...-pro` |
| `prompt` | string | 必 | —— |
| `input_image` | string | 见注 | base64 `data:image/png;base64, XXX`；文档原文"image parameter is a required field" |
| `seed` | integer | 否 | `0..9999999999` |
| `aspect_ratio` | string | 否 | 21:9 ~ 9:21 之间，例 `"21:9"` |
| `output_format` | enum | 否 | 默认 `png`；`png` / `jpeg` |
| `prompt_upsampling` | boolean | 否 | 默认 `false`；开启后自动改写 prompt 以增强创造性 |
| `safety_tolerance` | integer | 否 | `0..6`（0 最严、6 最松），例 `2`；**图生图场景上限为 2** |

> 注意这里是 `input_image`，而 FLUX.1-Kontext-dev 用的是 `image` —— 同族不同名。
> `image_size` 在此模型不存在，改用 `aspect_ratio`。

### 3.6 FLUX.1-Kontext-dev（图生图）

| 参数 | 类型 | 必填 | 约束 / 可选值 |
|---|---|---|---|
| `model` | enum | 必 | 默认 `black-forest-labs/FLUX.1-Kontext-dev`（单选项） |
| `prompt` | string | 必 | 默认 `an island near sea, with seagulls, ...` |
| `image` | string | **必** | base64 `data:image/png;base64, XXX` |
| `seed` | integer | 否 | `0..9999999999` |
| `prompt_enhancement` | boolean | 否 | 默认 `false`；开启后 prompt 被优化得更详细、更模型友好 |

### 3.7 FLUX-1.1-pro

| 参数 | 类型 | 必填 | 约束 / 可选值 |
|---|---|---|---|
| `model` | enum | 否 | 默认 `black-forest-labs/FLUX-1.1-pro`（文档未标 required） |
| `prompt` | string | 否 | 文档未标 required，例 `"ein fantastisches bild"` |
| `image_prompt` | string | 否 | 可选，base64 图像作为生成提示 |
| `width` | integer | 否 | 默认 `1024`；`256..1440`，**必须为 32 的倍数** |
| `height` | integer | 否 | 默认 `768`；`256..1440`，**必须为 32 的倍数** |
| `prompt_upsampling` | boolean | 否 | 默认 `false` |
| `seed` | integer | 否 | `0..9999999999` |
| `safety_tolerance` | integer | 否 | 默认 `2`；`0..6` |
| `output_format` | enum | 否 | 无默认；`jpeg` / `png` |

> ⚠️ 文档里 `height` 的描述文字写成了 "Width of the generated image..."，属复制粘贴笔误。

### 3.8 FLUX-1.1-pro-Ultra（参数最全）

| 参数 | 类型 | 必填 | 约束 / 可选值 |
|---|---|---|---|
| `model` | enum | 否 | 默认 `black-forest-labs/FLUX-1.1-pro-Ultra` |
| `prompt` | string | 否 | 默认 `an island near sea, with seagulls, ...` |
| `negative_prompt` | string | 否 | 负面提示词 |
| `image_size` | enum | 否 | 默认 `1024x1024`；`1024x1024` / `960x1280` / `768x1024` / `720x1440` / `720x1280` / `others` |
| `batch_size` | integer | 否 | 默认 `1`；`1..4` |
| `seed` | integer | 否 | `0..9999999999` |
| `aspect_ratio` | string | 否 | 21:9 ~ 9:21 |
| `safety_tolerance` | integer | 否 | 默认 `2`；`0..6` |
| `output_format` | enum | 否 | 无默认；`jpeg` / `png` |
| `raw` | boolean | 否 | 默认 `false`；生成更少加工、更自然的图像 |
| `image_prompt` | string | 否 | 可选，base64 图像用于 remix |
| `image_prompt_strength` | number | 否 | 默认 `0.1`；`0..1`，prompt 与 image_prompt 的混合强度 |

> `image_size` 含 `others` 选项 + 独立的 `aspect_ratio`，两者并存时优先级文档未说明。

### 3.9 FLUX.1-schnell ⚠️

| 参数 | 类型 | 必填 | 约束 / 可选值 |
|---|---|---|---|
| `model` | enum | 必 | 默认 `black-forest-labs/FLUX.1-schnell`（单选项） |
| `prompt` | string | 必 | 默认 `an island near sea, with seagulls, ...` |
| `image_size` | enum | **必** | 默认 `1024x1024`；`1024x1024` / `512x1024` / `768x512` / `768x1024` / `1024x576` / `576x1024` |
| `seed` | integer | 否 | `0..9999999999` |
| `prompt_enhancement` | boolean | 否 | 默认 `false` |

> ⚠️ 本仓库已知坑：该模型返回的 S3 预签名 URL 签名无效（403），**勿作默认模型**。

### 3.10 FLUX.1-dev ⚠️

| 参数 | 类型 | 必填 | 约束 / 可选值 |
|---|---|---|---|
| `model` | enum | 必 | 默认 `black-forest-labs/FLUX.1-dev`（单选项） |
| `prompt` | string | 必 | 默认 `an island near sea, with seagulls, ...` |
| `image_size` | enum | **必** | 默认 `1024x1024`；`1024x1024` / `960x1280` / `768x1024` / `720x1440` / `720x1280` / `others` |
| `num_inference_steps` | integer | **必** | 默认 `20`；`1..30` |
| `seed` | integer | 否 | `0..9999999999` |
| `prompt_enhancement` | boolean | 否 | 默认 `false` |

> ⚠️ 同 FLUX.1-schnell 的 S3 签名 403 坑。

## 4. 横向对比矩阵

`●` 支持　`—` 文档未列出（传了可能报错）

| 参数 | 2-pro | 2-flex | Qwen-Image | Z-Image | Kontext | Kontext-dev | 1.1-pro | 1.1-Ultra | schnell | dev |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| `prompt` | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● |
| `seed` | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● |
| `image_size` | ● | ● | ● | ● | — | — | — | ● | ● | ● |
| `width` / `height` | — | — | — | — | — | — | ● | — | — | — |
| `aspect_ratio` | — | — | — | — | ● | — | — | ● | — | — |
| `negative_prompt` | — | — | ● | ● | — | — | — | ● | — | — |
| `batch_size` | — | — | ● | — | — | — | — | ● | — | — |
| `output_format` | ● | ● | — | — | ● | — | ● | ● | — | — |
| `num_inference_steps` | — | ● | ● | — | — | — | — | — | — | ● |
| `guidance_scale` | — | — | ● | — | — | — | — | — | — | — |
| `cfg` | — | ●⚠️ | ● | — | — | — | — | — | — | — |
| `prompt_upsampling` | — | — | — | — | ● | — | ● | — | — | — |
| `prompt_enhancement` | — | — | — | — | — | ● | — | — | ● | ● |
| `safety_tolerance` | — | — | — | — | ● | — | ● | ● | — | — |
| `raw` | — | — | — | — | — | — | — | ● | — | — |
| `image` (base64) | — | — | ●¹ | — | — | ● | — | — | — | — |
| `input_image` | — | — | — | — | ● | — | — | — | — | — |
| `image_prompt` | — | — | — | — | — | — | ● | ● | — | — |
| `image_prompt_strength` | — | — | — | — | — | — | — | ● | — | — |
| **支持图片输入** | ✗ | ✗ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ |

¹ 仅当 `model = Qwen/Qwen-Image-Edit`。

**其它结论**

- **纯文生图、参数最少**：Z-Image（`prompt` + `image_size` + `seed`，可选 `negative_prompt`）。
- **纯文生图、参数最多**：FLUX-1.1-pro-Ultra（11 个可选字段）。
- **图生图**：Qwen-Image-Edit / FLUX.1-Kontext(-max/-pro) / FLUX.1-Kontext-dev / FLUX-1.1-pro(`image_prompt`) / FLUX-1.1-pro-Ultra(`image_prompt`)。
- **`output_format` 不可用**：Qwen-Image、Z-Image、Kontext-dev、schnell、dev 共 5 个模型，固定输出不可选格式。
- 分辨率风格分三派：**512 档枚举**（FLUX.2-*）、**1328 档大尺寸**（Qwen-Image）、**1024 档枚举 / `others`**（Ultra、schnell、dev）、**数值宽高**（1.1-pro）、**无 image_size 只有 aspect_ratio**（Kontext）。

## 5. 与本仓库现状的差异

对照 `packages/yuppie-siliconflow/src/yuppie_siliconflow/images.py` 与
`packages/yuppie-mcp-siliconflow/src/yuppie_mcp_siliconflow/tools/images.py`：

| 项 | 仓库现状 | 文档/实际 | 处理建议 |
|---|---|---|---|
| 默认文生图模型 | `Tongyi-MAI/Z-Image-Turbo` | 一致 ✓ | 保持 |
| 默认编辑模型 | ~~`Qwen/Qwen-Image-Edit-2509`~~ `Qwen/Qwen-Image-Edit` | 文档只列出 `Qwen/Qwen-Image-Edit` | 已于 2026-10-13 改用文档列出的 ID |
| `RESOLUTIONS` 枚举 | `1024x1024 / 960x1280 / 768x1024 / 720x1440 / 720x1280` | 这是 **FLUX-1.1-pro-Ultra / FLUX.1-dev** 的集 | 对各模型并非都合法，需按模型校验 |
| `ASPECT_RATIOS` 映射 | 映射到 `1024x1024 / 768x1024 / 1024x768 / 576x1024 / 1024x576` | 其中 `1024x768 / 576x1024 / 1024x576` 只在 **FLUX.2-\*** 集里 | 同上；且这些模型根本不吃 `aspect_ratio` 字段 |
| 默认回退尺寸 | `1024x1024` | Qwen-Image 的推荐 1:1 是 `1328x1328`；FLUX.2-\* 只到 512 档 | 需按模型给默认值 |
| 无脑发送字段 | `generate_image` 恒定发送 `image_size` + `output_format` + `batch_size`（+ 条件发送 `negative_prompt` / `num_inference_steps` / `guidance_scale`） | `batch_size` 仅 Qwen-Image / Ultra 支持；`output_format` 有 5 个模型不支持 | 改为按模型白名单过滤，否则可能报错 |
| `aspect_ratio` 未透传 | `edit_image` / `generate_image` 都只把 aspect_ratio 折算成 image_size 后丢弃 | FLUX.1-Kontext / Ultra 用的是 `aspect_ratio` 字段本身 | 需要在客户端透传该字段 |
| `cfg` / `safety_tolerance` / `raw` / `image_prompt*` / `prompt_upsampling` / `prompt_enhancement` | 未支持 | 文档中的合法参数 | 可作为后续扩展项 |
| `input_image` vs `image` | `edit_image` 统一发 `image` | Kontext 用 `input_image`，Kontext-dev / Qwen-Image-Edit 用 `image` | 编辑路径需按模型分派字段名 |
