# 生图模型能力表设计

日期：2026-10-13
状态：待评审
相关文档：[生图API-各模型参数.md](../../生图API-各模型参数.md)（API 参数原始整理）

## 1. 背景

SiliconFlow `/v1/images/generations` 的 Body 参数**因模型而异,没有统一超集**。文档页共 10 个 Tab、12 个模型 ID,分辨率体系分四派(512 档枚举 / 1328 档大尺寸 / 1024 档枚举含 `others` / 数值宽高),图生图字段名在 `image` 与 `input_image` 之间分裂。

而当前实现 `packages/yuppie-siliconflow/src/yuppie_siliconflow/images.py` 隐含**"所有模型长一个样"**的假设,具体问题:

| # | 问题 | 影响 |
|---|---|---|
| 1 | `generate_image` 恒定发送 `image_size` / `output_format` / `batch_size` | `batch_size` 仅 Qwen-Image、Ultra 支持;`output_format` 有 5 个模型不支持 |
| 2 | `ASPECT_RATIOS["1:1"] = "1024x1024"`,但默认模型 Z-Image 只推荐 512 档 | **默认路径就在给默认模型发不合适的尺寸** |
| 3 | `RESOLUTIONS` 硬编码 FLUX-1.1-pro-Ultra / FLUX.1-dev 的尺寸集 | 换模型后未必合法 |
| 4 | `aspect_ratio` 折算成 `image_size` 后丢弃 | Kontext / Ultra 原生吃 `aspect_ratio` 字段,该能力被吞掉 |
| 5 | `edit_image` 恒定发送 `image` | Kontext 家族用 `input_image`,字段名错 |
| 6 | 文档中其余合法参数(`cfg` / `safety_tolerance` / `raw` / `image_prompt*` / `prompt_upsampling` / `prompt_enhancement` / `num_inference_steps` / `guidance_scale`)全部未暴露 | 能力面缺失 |

根因不是"少补几个参数",而是**缺一个模型能力数据层**。

## 2. 目标与非目标

**目标**

1. 引入模型能力表作为单一事实源,驱动参数过滤、尺寸解析、图片输入字段分派
2. 补齐文档中全部合法参数到 MCP 工具面
3. 未知模型不失效(宽松兜底)
4. 保持现有公开 API 向后兼容

**非目标**

1. 不改 `edit_image` 与 `generate_image` 的工具划分(保留两个独立工具)
2. 不动态拉取模型参数规格 —— `list_models` 只返回模型 id,不含参数 schema
3. 不做请求前的能力协商/自动降级到别的模型
4. 不改视频 / 语音模块

## 3. 决策记录

| 决策 | 取值 | 理由 |
|---|---|---|
| 改造深度 | 能力表 + 补齐参数面 | 缺的是数据层,补参数是它的自然产物 |
| 边界策略 | 宽松兜底 | 硅基流动上新模型频繁,严格白名单会导致"新模型 = 等发版" |
| 未知模型 | 不校验,全文透传 | 同上;能力表是"提示"不是"闸门" |
| 尺寸兜底 | 按比例选最近合法值 + 注记 | 不中断调用,同时不失真(用户能看到被改写) |
| 工具划分 | 保留 `generate_image` / `edit_image` 两个工具 | MCP 工具语义清晰,LLM 更容易选对;且取消 `edit_image` 属破坏性变更 |
| 三态布尔 | `None` = 未给,`False` = 显式关 | 避免"没传"被当成"关掉" |

## 4. 架构

新增库包模块 `packages/yuppie-siliconflow/src/yuppie_siliconflow/image_specs.py`,纯数据 + 纯函数,无 IO,可离线测试。

```
image_specs.py          ← 新增:能力表 + build_image_payload
  ImageModelSpec        # 每个模型的能力描述(frozen dataclass)
  IMAGE_MODELS          # dict[str, ImageModelSpec],含 alias 解析
  Note                  # 注记(level, message)
  resolve_spec()        # model id → spec | None(未知模型返回 None)
  build_image_payload() # → (payload, notes)

images.py               ← 重构:两种入口都过 build_image_payload
  ImagesMixin.generate_image
  ImagesMixin.edit_image
  RESOLUTIONS / ASPECT_RATIOS / resolve_image_size  ← 保留为兼容导出
```

依赖方向:`images.py` → `image_specs.py`,单向,无环。

## 5. 数据模型

```python
@dataclass(frozen=True)
class ImageModelSpec:
    params: frozenset[str]                    # 该模型接受的请求字段白名单
    default_size: str | None = None           # 未指定尺寸时用;None = 该模型无尺寸参数
    sizes: tuple[str, ...] = ()               # 合法/推荐尺寸,用于"最近"兜底
    ratio_size: Mapping[str, str] = field(default_factory=dict)  # 比例 → 该模型的尺寸
    allow_free_size: bool = False             # 是否接受推荐集之外的尺寸(见第 9 节)
    aspect_ratio_native: bool = False         # 原生接受 aspect_ratio 字段
    width_height: bool = False                # 用 width/height 而非 image_size
    image_field: str | None = None            # "image" / "input_image"
    note: str = ""                            # 该模型的已知坑
```

alias 单独放在模块级 `_ALIASES: dict[str, str]`(alias → 规范 id),由 `resolve_spec()` 先查 alias 再查 `IMAGE_MODELS`,避免污染 spec 本身。

不变量(测试覆盖):

- `ratio_size` 的每个值必须出现在 `sizes` 中,或 `allow_free_size=True`
- `allow_free_size=True` ⟺ 该模型的尺寸枚举来自文档的 `others` 或文档用 `string` 类型描述
- `width_height=True` 时 `default_size` 必填(`WxH` 形式)
- `aspect_ratio_native=True` ⟺ `params` 含 `"aspect_ratio"`
- `image_field` 非 None ⟺ `params` 含该字段名

## 6. 能力表内容

12 个模型 ID(同 Tab 的 `-max` / `-pro` 共一条 spec,经 alias 解析)。

| model ID | 尺寸模式 | 默认尺寸 | 支持的尺寸 | 图片输入字段 |
|---|---|---|---|---|
| `black-forest-labs/FLUX.2-pro` | image_size 白名单 | `512x512` | 512x512 / 768x1024 / 1024x768 / 576x1024 / 1024x576 | — |
| `black-forest-labs/FLUX.2-flex` | 同上 | `512x512` | 同上 | — |
| `Qwen/Qwen-Image` | image_size 自由 | `1328x1328` | 1328x1328 / 1664x928 / 928x1664 / 1472x1140 / 1140x1472 / 1584x1056 / 1056x1584 | — |
| `Qwen/Qwen-Image-Edit` | 同上 | `1328x1328` | 同上 | `image` |
| `Tongyi-MAI/Z-Image-Turbo` | image_size 自由 | `512x512` | 512x512 / 768x1024 / 1024x576 / 576x1024 | — |
| `black-forest-labs/FLUX.1-Kontext-max` | aspect_ratio 原生 | — | — | `input_image` |
| `black-forest-labs/FLUX.1-Kontext-dev` | 无尺寸参数 | — | — | `image` |
| `black-forest-labs/FLUX-1.1-pro` | width/height | `1024x768` | 256..1440 且 32 的倍数 | `image_prompt` |
| `black-forest-labs/FLUX-1.1-pro-Ultra` | image_size + `others` | `1024x1024` | 1024x1024 / 960x1280 / 768x1024 / 720x1440 / 720x1280 / others | `image_prompt` |
| `black-forest-labs/FLUX.1-schnell` | image_size + `others` | `1024x1024` | 1024x1024 / 512x1024 / 768x512 / 768x1024 / 1024x576 / 576x1024 | — |
| `black-forest-labs/FLUX.1-dev` | image_size + `others` | `1024x1024` | 1024x1024 / 960x1280 / 768x1024 / 720x1440 / 720x1280 / others | — |

alias:

- `black-forest-labs/FLUX.1-Kontext-pro` → `-max` 的 spec
- `Qwen/Qwen-Image-Edit-2509` → `Qwen/Qwen-Image-Edit` 的 spec(**待实测确认 id 有效性**)

各模型的 `params` 白名单(逐字段):

| model | params |
|---|---|
| FLUX.2-pro | `prompt` `image_size` `seed` `output_format` |
| FLUX.2-flex | 上 + `cfg` `num_inference_steps` |
| Qwen-Image / -Edit | `prompt` `negative_prompt` `image_size` `batch_size` `seed` `num_inference_steps` `guidance_scale` `cfg` (+`image`) |
| Z-Image | `prompt` `negative_prompt` `image_size` `seed` |
| Kontext-max/-pro | `prompt` `input_image` `seed` `aspect_ratio` `output_format` `prompt_upsampling` `safety_tolerance` |
| Kontext-dev | `prompt` `image` `seed` `prompt_enhancement` |
| FLUX-1.1-pro | `prompt` `image_prompt` `width` `height` `prompt_upsampling` `seed` `safety_tolerance` `output_format` |
| FLUX-1.1-pro-Ultra | `prompt` `negative_prompt` `image_size` `batch_size` `seed` `aspect_ratio` `safety_tolerance` `output_format` `raw` `image_prompt` `image_prompt_strength` |
| FLUX.1-schnell | `prompt` `image_size` `seed` `prompt_enhancement` |
| FLUX.1-dev | `prompt` `image_size` `num_inference_steps` `seed` `prompt_enhancement` |

`allow_free_size` 取值:`True` —— Qwen-Image / -Edit(文档用 `string`)、Z-Image(文档用 `string`)、Ultra / schnell / dev(枚举含 `others`);`False` —— FLUX.2-pro / flex(纯枚举);Kontext 家族无尺寸参数。

`ratio_size` 逐模型(未列出的比例走第 7 节的"最近"兜底):

| model | ratio_size |
|---|---|
| FLUX.2-pro / flex | `1:1`→512x512　`3:4`→768x1024　`4:3`→1024x768　`9:16`→576x1024　`16:9`→1024x576 |
| Qwen-Image / -Edit | `1:1`→1328x1328　`16:9`→1664x928　`9:16`→928x1664　`4:3`→1472x1140　`3:4`→1140x1472　`3:2`→1584x1056　`2:3`→1056x1584 |
| Z-Image | `1:1`→512x512　`3:4`→768x1024　`16:9`→1024x576　`9:16`→576x1024　*(无 `4:3`)* |
| FLUX-1.1-pro | `1:1`→1024x1024　`4:3`→1024x768　`3:4`→768x1024　`16:9`→1280x720　`9:16`→720x1280 |
| FLUX-1.1-pro-Ultra | `1:1`→1024x1024　`4:3`→1024x768　`3:4`→768x1024　`16:9`→1280x720　`9:16`→720x1280 |
| FLUX.1-schnell | `1:1`→1024x1024　`3:4`→768x1024　`16:9`→1024x576　`9:16`→576x1024　*(无 `4:3`)* |
| FLUX.1-dev | `1:1`→1024x1024　`4:3`→1024x768　`3:4`→768x1024　`16:9`→1280x720　`9:16`→720x1280 |

其中 `1024x768` / `1280x720` 落在 Ultra / dev 枚举的 `others` 里,靠 `allow_free_size=True` 放行。

**Z-Image 与 schnell 没有 `4:3`** —— 这两处正是兜底逻辑的触发场景(见第 7 节第 4 条)。

## 7. 调用路径

```python
def build_image_payload(
    spec: ImageModelSpec | None,
    *,
    image_size_input: str | None,   # 已由 resolution / aspect_ratio 归一
    **fields: Any,
) -> tuple[dict[str, Any], list[Note]]:
    """spec=None(未知模型)→ 原样透传,notes 为空。"""
```

**尺寸解析优先级**(spec 已知时):

1. `aspect_ratio` 给定 且 `spec.aspect_ratio_native` → **直接透传 `aspect_ratio` 字段**,不折成尺寸
2. `resolution` 给定 → 原样使用
3. `aspect_ratio` 给定 → 查 `spec.ratio_size`;命中即用
4. 未命中 → 取**比例最接近**的键的尺寸,追加 `warn` 注记
5. 都未给定 → `spec.default_size`
6. `spec.width_height` → 把最终 `WxH` 拆成 `width` / `height`
7. `spec` 无任何尺寸字段(Kontext-dev)→ 丢弃尺寸并追加 `info` 注记

**最近比例算法**:把 `"4:3"` 解析为 `4/3`,与各候选键比较 `|log(r) − log(r_key)|` 取最小。用 log 保证 `4:3` 与 `3:4` 到 `1:1` 的距离对称。

**字段过滤**:遍历 payload,凡不在 `spec.params` 中的字段剔除并追加 `warn` 注记。`prompt` 与 `model` 恒保留。

**未知模型**:`resolve_spec()` 返回 `None`,`build_image_payload` 原样透传全部字段、不做任何尺寸推断(此时 `image_size` 用调用方给的或库层默认 `1024x1024`)。

## 8. MCP 工具面

`GenerateImageInput` 与 `tool_generate_image` 新增 **9 个全可选参数**:

| 参数 | 类型 | 说明 |
|---|---|---|
| `num_inference_steps` | `int \| None` | 去噪步数 |
| `guidance_scale` | `float \| None` | Qwen-Image 专属 |
| `cfg` | `float \| None` | Qwen-Image 专属 |
| `safety_tolerance` | `int \| None` | Kontext / FLUX-1.1-pro / Ultra |
| `raw` | `bool \| None` | Ultra 专属 |
| `prompt_upsampling` | `bool \| None` | Kontext / FLUX-1.1-pro |
| `prompt_enhancement` | `bool \| None` | Kontext-dev / schnell / dev |
| `image_prompt` | `str \| None` | FLUX-1.1-pro / Ultra,base64 |
| `image_prompt_strength` | `float \| None` | Ultra,`0..1` |

`EditImageInput` 与 `tool_edit_image` 新增:

| 参数 | 类型 | 说明 |
|---|---|---|
| `negative_prompt` | `str \| None` | 部分模型支持 |
| `aspect_ratio` | `str \| None` | Kontext 原生支持 |
| `output_format` | `str \| None` | 部分模型支持 |
| `safety_tolerance` | `int \| None` | Kontext / Ultra |

字段名分派由能力表的 `image_field` 完成,调用方仍统一传 `image`。

**注记渲染**:`_format_images` 在 header 行下逐条输出注记:

```
✅ 已生成 768x1024 图像(模型:Tongyi-MAI/Z-Image-Turbo),Seed:12345
ℹ️ 未指定尺寸,已使用该模型 3:4 推荐值 768x1024
⚠️ 已忽略该模型不支持的参数:raw
```

库层 `generate_image` / `edit_image` 返回值新增 `"notes": [{"level": ..., "message": ...}]`,MCP 层据此渲染。

## 9. 尺寸自由度的判定

三类模型对"给定尺寸不在推荐集"的容忍度不同:

- **白名单**(`allow_free_size=False`):非枚举值大概率被拒 → 越界时改为最接近的合法值 + `warn`
- **自由**(`allow_free_size=True`,文档用 `string` 描述):原样透传,不干预
- **半开放**(`allow_free_size=True`,枚举含 `others`):原样透传

前两类行为一致,区别只在"为何允许"。因此统一用 `allow_free_size: bool` 显式表达,**不从文档措辞或类型反推** —— 那是实现期的猜测,不该进代码。

差异仅体现在 `ratio_size` 能否覆盖全部比例:覆盖不全时走兜底。

## 10. 测试

新增 `tests/test_image_specs.py`:

1. 能力表完整性:每个 spec 非空、`ratio_size` 的值都在 `sizes` 或 `allow_free_size`、不变量逐条校验
2. `resolve_spec` 对 12 个 id + 1 个 alias 都能命中;未知 id 返回 `None`
3. 尺寸解析:6 条优先级分支各一例
4. 最近比例:`Z-Image + 4:3` → `768x1024`;`4:3` 与 `3:4` 到 `1:1` 距离对称
5. 字段剔除:`Z-Image + raw=True` → payload 无 `raw`,notes 含 warn
6. 未知模型:`"foo/bar" + raw=True` → payload 含 `raw`,notes 为空
7. 字段名分派:Kontext → `input_image`;Kontext-dev → `image`
8. `aspect_ratio_native` 透传:Kontext + `aspect_ratio="9:16"` → payload 含 `aspect_ratio`,不含 `image_size`
9. 三态布尔:`raw=None` 不入 payload,`raw=False` 入 payload

改造 `tests/test_client.py`:`ASPECT_RATIOS` 相关断言改为"默认模型视角",或改为直接断言能力表。

## 11. 兼容性

保持不变:

- `RESOLUTIONS` / `ASPECT_RATIOS` / `resolve_image_size` 仍是 `yuppie_siliconflow` 的导出名,`__all__` 不变
- `generate_image(prompt, resolution=..., aspect_ratio=..., model=..., ...)` 调用方式不变
- 现有 MCP 工具名与已有参数不变,仅新增可选参数

语义变化(需在 README 注明):

- `ASPECT_RATIOS` 从"全局硬编码映射"变为"默认模型(Z-Image)的映射",数值随之修正(`1:1` 由 `1024x1024` → `512x512`)
- `resolve_image_size()` 保留为纯函数,但库内部改用能力表;保留它是为了不破坏外部 import

## 12. 已知坑与待办

| 项 | 状态 |
|---|---|
| FLUX.1-schnell / FLUX.1-dev 返回的 S3 预签名 URL 签名无效(403) | 已知,`note` 字段标注,不作默认模型 |
| `Qwen/Qwen-Image-Edit-2509` 未出现在文档模型列表中 | **待实测**;确认无效则改默认编辑模型为 `Qwen/Qwen-Image-Edit` |
| FLUX.2-flex 文档列出 `cfg`,但描述写"仅适用于 Qwen/Qwen-Image" | **待实测**;暂按其列出即支持处理 |
| FLUX-1.1-pro 文档 `height` 的描述文字误写为 "Width of..." | 文档笔误,不影响实现 |
| FLUX-1.1-pro-Ultra 同时有 `image_size` 含 `others` 与独立 `aspect_ratio` | 优先级文档未说明;本设计让 `aspect_ratio` 优先(第 7 节第 1 条) |
