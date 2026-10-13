# 生图模型能力表设计

日期：2026-10-13
状态：待评审
相关文档：[生图API-各模型参数.md](../../生图API-各模型参数.md)（API 参数原始整理）

> 2026-10-13 修订：工具签名从「按文档字段名扁平暴露」改为「模型无关的意图参数 + 能力表翻译」，
> 见第 5 节与第 8 节。原设计把工具签名写成了文档字段的抄本，调用方被迫知道每个模型吃什么。

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

### 参数差异的两种成因

模型间参数不同,成因有两种,**处理方式相反**:

| 成因 | 例子 | 处理 |
|---|---|---|
| **同一意图、不同字段名** | `resolution` / `image_size` / `width`+`height` / `aspect_ratio` | 归并成**一个意图参数**,库层翻译 |
| **真正独有的旋钮** | `raw`(Ultra)、`cfg`(Qwen)、`safety_tolerance`(Kontext) | **如实暴露**,能力表负责过滤 |

这条区分是本设计的主轴。把两类混在一起,工具签名就会退化成文档的抄本。

## 2. 目标与非目标

**目标**

1. 引入模型能力表作为单一事实源,驱动**意图→字段翻译**、参数过滤、尺寸解析、图片输入字段分派
2. **工具签名模型无关** —— 调用方只表达意图,不需要知道目标模型的字段名
3. 补齐文档中全部合法参数(以意图参数的形式)到 MCP 工具面
4. 未知模型不失效(宽松兜底)
5. 保持库层现有公开 API 向后兼容

**非目标**

1. 不改 `edit_image` 与 `generate_image` 的工具划分(保留两个独立工具)
2. 不动态拉取模型参数规格 —— `list_models` 只返回模型 id,不含参数 schema
3. 不做请求前的能力协商/自动降级到别的模型
4. 不改视频 / 语音模块

## 3. 决策记录

| 决策 | 取值 | 理由 |
|---|---|---|
| 改造深度 | 能力表 + 补齐参数面 | 缺的是数据层,补参数是它的自然产物 |
| 签名形态 | **模型无关的意图参数 + 能力表翻译** | 参数差异是库层的翻译问题,不该是调用方的认知负担 |
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
  IMAGE_MODELS          # dict[str, ImageModelSpec]
  _ALIASES              # dict[str, str],alias → 规范 id
  INTENTS               # 意图参数名 → 中文说明(供工具 description 生成)
  Note                  # 注记(level, message)
  resolve_spec()        # model id → spec | None(未知模型返回 None)
  parse_size()          # "1024x1024" | "16:9" → 结构化尺寸意图
  build_image_payload() # → (payload, notes)

images.py               ← 重构:两种入口都过 build_image_payload
  ImagesMixin.generate_image
  ImagesMixin.edit_image
  RESOLUTIONS / ASPECT_RATIOS / resolve_image_size  ← 保留为兼容导出
```

依赖方向:`images.py` → `image_specs.py`,单向,无环。

## 5. 数据模型

意图参数全集(14 个,含仅 `edit_image` 使用的 `image`)。工具签名 = `prompt` + `model` + 该工具实际暴露的意图子集:

| 意图参数 | 含义 | 折算到的 API 字段 |
|---|---|---|
| `size` | 尺寸或宽高比 | `image_size` / (`width`+`height`) / `aspect_ratio` |
| `seed` | 随机种子 | `seed` |
| `negative_prompt` | 负面提示词 | `negative_prompt` |
| `output_format` | 输出格式 | `output_format` |
| `batch_size` | 生成张数 | `batch_size` |
| `reference_image` | 参考图(base64) | `image_prompt` |
| `reference_strength` | 参考图混合强度 | `image_prompt_strength` |
| `steps` | 去噪步数 | `num_inference_steps` |
| `cfg` | CFG 系数 | `cfg` |
| `guidance` | 引导强度 | `guidance_scale` |
| `safety_tolerance` | 审核容忍度 | `safety_tolerance` |
| `enhance_prompt` | 自动优化提示词 | `prompt_upsampling` / `prompt_enhancement` |
| `raw` | 更少加工、更自然的输出 | `raw` |
| `image` | 待编辑图(仅 `edit_image`) | `image` / `input_image` |

```python
@dataclass(frozen=True)
class ImageModelSpec:
    intents: frozenset[str]                   # 该模型接受的意图参数集
    field_map: Mapping[str, str] = field(default_factory=dict)
                                              # 意图 → API 字段名,仅同名之外的需列出
    default_size: str | None = None           # 未指定尺寸时用;None = 该模型无尺寸参数
    sizes: tuple[str, ...] = ()               # 合法/推荐尺寸,用于"最近"兜底
    ratio_size: Mapping[str, str] = field(default_factory=dict)  # 比例 → 该模型的尺寸
    allow_free_size: bool = False             # 是否接受推荐集之外的尺寸(见第 9 节)
    aspect_ratio_native: bool = False         # 原生接受 aspect_ratio 字段
    width_height: bool = False                # 用 width/height 而非 image_size
    image_field: str | None = None            # "image" / "input_image"
    note: str = ""                            # 该模型的已知坑
```

`size` 与 `image` 是仅有的两个"由能力表特殊处理"的意图,不放进 `field_map`:

- `size` 经 `default_size` / `ratio_size` / `aspect_ratio_native` / `width_height` 四个字段共同决定落点
- `image` 经 `image_field` 决定落点

其余意图一律走 `field_map`,缺省即同名。

alias 单独放在模块级 `_ALIASES: dict[str, str]`(alias → 规范 id),由 `resolve_spec()` 先查 alias 再查 `IMAGE_MODELS`,避免污染 spec 本身。

不变量(测试覆盖):

- `ratio_size` 的每个值必须出现在 `sizes` 中,或 `allow_free_size=True`
- `allow_free_size=True` ⟺ 该模型的尺寸枚举来自文档的 `others` 或文档用 `string` 类型描述
- `width_height=True` 时 `default_size` 必填(`WxH` 形式)
- `"size" in intents` ⟺ `aspect_ratio_native or width_height or default_size is not None or bool(sizes)`
  —— 即"该模型有尺寸参数"与"能力表知道尺寸落点"必须同时成立
- `aspect_ratio_native=True` 时宽高比直接透传为 `aspect_ratio` 字段,不查 `ratio_size`
- `image_field` 非 None ⟺ `"image" in intents`
- `field_map` 的每个键都必须出现在 `intents` 中
- `intents` 里除 `size` / `image` 外的每个意图,都能通过 `field_map` + 同名默认解析出 API 字段

## 6. 能力表内容

12 个模型 ID(同 Tab 的 `-max` / `-pro` 共一条 spec,经 alias 解析)。

### 6.1 意图集与字段翻译

| model ID | intents | field_map |
|---|---|---|
| `black-forest-labs/FLUX.2-pro` | `size` `seed` `output_format` | — |
| `black-forest-labs/FLUX.2-flex` | 上 + `cfg` `steps` | `steps`→`num_inference_steps` |
| `Qwen/Qwen-Image` | `size` `seed` `negative_prompt` `batch_size` `steps` `guidance` `cfg` | `steps`→`num_inference_steps`; `guidance`→`guidance_scale` |
| `Qwen/Qwen-Image-Edit` | 上 + `image` | 同上 |
| `Tongyi-MAI/Z-Image-Turbo` | `size` `seed` `negative_prompt` | — |
| `black-forest-labs/FLUX.1-Kontext-max` | `size` `seed` `output_format` `enhance_prompt` `safety_tolerance` `image` | `enhance_prompt`→`prompt_upsampling` |
| `black-forest-labs/FLUX.1-Kontext-dev` | `seed` `enhance_prompt` `image` | `enhance_prompt`→`prompt_enhancement` |
| `black-forest-labs/FLUX-1.1-pro` | `size` `seed` `output_format` `enhance_prompt` `safety_tolerance` `reference_image` | `enhance_prompt`→`prompt_upsampling`; `reference_image`→`image_prompt` |
| `black-forest-labs/FLUX-1.1-pro-Ultra` | `size` `seed` `negative_prompt` `batch_size` `safety_tolerance` `output_format` `raw` `reference_image` `reference_strength` | `reference_image`→`image_prompt`; `reference_strength`→`image_prompt_strength` |
| `black-forest-labs/FLUX.1-schnell` | `size` `seed` `enhance_prompt` | `enhance_prompt`→`prompt_enhancement` |
| `black-forest-labs/FLUX.1-dev` | `size` `seed` `steps` `enhance_prompt` | `steps`→`num_inference_steps`; `enhance_prompt`→`prompt_enhancement` |

本表只列**能力差异**部分:`prompt` 与 `model` 恒保留,不出现在 `intents` 里(第 5 节)。

**注意 `enhance_prompt` 的落点随模型而变**:Kontext / 1.1-pro 是 `prompt_upsampling`,Kontext-dev / schnell / dev 是 `prompt_enhancement`。两者在文档里是不同字段,但语义都是"自动优化 prompt 使其更模型友好",故归并为一个意图。

### 6.2 尺寸落点

为表格可读性,本节 model ID 省略 vendor 前缀(`black-forest-labs/`、`Qwen/`、`Tongyi-MAI/`);完整 ID 见 6.1。

| model ID | 尺寸模式 | 默认尺寸 | 支持的尺寸 | 图片输入字段 |
|---|---|---|---|---|
| `FLUX.2-pro` | image_size 白名单 | `512x512` | 512x512 / 768x1024 / 1024x768 / 576x1024 / 1024x576 | — |
| `FLUX.2-flex` | 同上 | `512x512` | 同上 | — |
| `Qwen/Qwen-Image` | image_size 自由 | `1328x1328` | 1328x1328 / 1664x928 / 928x1664 / 1472x1140 / 1140x1472 / 1584x1056 / 1056x1584 | — |
| `Qwen/Qwen-Image-Edit` | 同上 | `1328x1328` | 同上 | `image` |
| `Tongyi-MAI/Z-Image-Turbo` | image_size 自由 | `512x512` | 512x512 / 768x1024 / 1024x576 / 576x1024 | — |
| `FLUX.1-Kontext-max` | aspect_ratio 原生 | — | — | `input_image` |
| `FLUX.1-Kontext-dev` | 无尺寸参数 | — | — | `image` |
| `FLUX-1.1-pro` | width/height | `1024x768` | 256..1440 且 32 的倍数 | — |
| `FLUX-1.1-pro-Ultra` | image_size + `others` | `1024x1024` | 1024x1024 / 960x1280 / 768x1024 / 720x1440 / 720x1280 / others | — |
| `FLUX.1-schnell` | image_size + `others` | `1024x1024` | 1024x1024 / 512x1024 / 768x512 / 768x1024 / 1024x576 / 576x1024 | — |
| `FLUX.1-dev` | image_size + `others` | `1024x1024` | 1024x1024 / 960x1280 / 768x1024 / 720x1440 / 720x1280 / others | — |

`allow_free_size` 取值:`True` —— Qwen-Image / -Edit(文档用 `string`)、Z-Image(文档用 `string`)、Ultra / schnell / dev(枚举含 `others`);`False` —— FLUX.2-pro / flex(纯枚举);Kontext 家族无尺寸参数。

`ratio_size` 逐模型(未列出的比例走第 7 节的"最近"兜底):

| model | ratio_size |
|---|---|
| FLUX.2-pro / flex | `1:1`→512x512; `3:4`→768x1024; `4:3`→1024x768; `9:16`→576x1024; `16:9`→1024x576 |
| Qwen-Image / -Edit | `1:1`→1328x1328; `16:9`→1664x928; `9:16`→928x1664; `4:3`→1472x1140; `3:4`→1140x1472; `3:2`→1584x1056; `2:3`→1056x1584 |
| Z-Image | `1:1`→512x512; `3:4`→768x1024; `16:9`→1024x576; `9:16`→576x1024; *(无 `4:3`)* |
| FLUX-1.1-pro | `1:1`→1024x1024; `4:3`→1024x768; `3:4`→768x1024; `16:9`→1280x720; `9:16`→720x1280 |
| FLUX-1.1-pro-Ultra | `1:1`→1024x1024; `4:3`→1024x768; `3:4`→768x1024; `16:9`→1280x720; `9:16`→720x1280 |
| FLUX.1-schnell | `1:1`→1024x1024; `3:4`→768x1024; `16:9`→1024x576; `9:16`→576x1024; *(无 `4:3`)* |
| FLUX.1-dev | `1:1`→1024x1024; `4:3`→1024x768; `3:4`→768x1024; `16:9`→1280x720; `9:16`→720x1280 |

其中 `1024x768` / `1280x720` 落在 Ultra / dev 枚举的 `others` 里,靠 `allow_free_size=True` 放行。

**Z-Image 与 schnell 没有 `4:3`** —— 这两处正是兜底逻辑的触发场景(见第 7 节)。

### 6.3 alias

- `black-forest-labs/FLUX.1-Kontext-pro` → `FLUX.1-Kontext-max` 的 spec
- `Qwen/Qwen-Image-Edit-2509` → `Qwen/Qwen-Image-Edit` 的 spec(**待实测确认 id 有效性**)

## 7. 调用路径

```python
def build_image_payload(
    spec: ImageModelSpec | None,
    *,
    size_input: str | None,          # "1024x1024" 或 "16:9",未归一
    intents: Mapping[str, Any],      # 意图参数 → 值,None 值已被调用方剔除
) -> tuple[dict[str, Any], list[Note]]:
    """spec=None(未知模型)→ 原样透传,notes 为空。"""
```

分四步。

**第一步:解析 `size_input`**(spec 已知时)

`parse_size()` 先判语法:含 `x` → 显式尺寸;含 `:` → 宽高比。按序执行:

1. 该模型 `"size" not in intents` 但调用方给了 `size`(Kontext-dev)→ 剔除并追加 `info` 注记,结束
2. `size_input` 为空 → 用 `spec.default_size`(可能为 None,即不下发尺寸字段),跳到第 6 步
3. 宽高比 且 `spec.aspect_ratio_native` → **直接透传 `aspect_ratio` 字段**,不折成尺寸,跳到第 6 步
4. 显式尺寸 → 越界时按 `allow_free_size` 决定是否纠正(见第 9 节),跳到第 6 步
5. 宽高比 且 非原生 → 查 `spec.ratio_size`;命中即用;未命中取**比例最接近**的键的尺寸并追加 `warn` 注记
6. `spec.width_height` → 把最终 `WxH` 拆成 `width` / `height`

**最近比例算法**:把 `"4:3"` 解析为 `4/3`,与各候选键比较 `|log(r) − log(r_key)|` 取最小。用 log 保证 `4:3` 与 `3:4` 到 `1:1` 的距离对称。

**第二步:翻译意图为字段**

对每个意图,API 字段名 = `spec.field_map.get(intent, intent)`,`image` 意图除外(用 `spec.image_field`)。

**第三步:过滤**

字段不在 `spec.intents` 中 → 剔除并追加 `warn` 注记。`prompt` 与 `model` 恒保留。

**第四步:未知模型**

`resolve_spec()` 返回 `None` 时跳过前三步,`size_input` 原样进 `image_size`(`16:9` 这类比例写法降级为库层默认 `1024x1024`),全部意图原样透传、`notes` 为空。

## 8. MCP 工具面

### 8.1 `generate_image`

```python
generate_image(
    prompt: str,                              # 必填
    model: str | None = None,
    size: str | None = None,                  # "1024x1024"(尺寸) 或 "16:9"(比例)
    seed: int | None = None,
    negative_prompt: str | None = None,
    output_format: str | None = None,
    batch_size: int | None = None,
    reference_image: str | None = None,
    reference_strength: float | None = None,
    steps: int | None = None,
    cfg: float | None = None,
    guidance: float | None = None,
    safety_tolerance: int | None = None,
    enhance_prompt: bool | None = None,
    raw: bool | None = None,
)
```

15 个参数,全部模型无关。`size` 的 description 需写明两种语法与"具体可用值随模型而异,不合法时自动取最接近的合法值"。

**`resolution` / `aspect_ratio` 的处理**:MCP 层直接换成 `size`。MCP 工具签名由 LLM 每次会话动态读取,重命名无破坏性 —— 正因为如此,更该趁现在改对。

### 8.2 `edit_image`

```python
edit_image(
    image: str,                               # 待编辑图的 URL 或 base64
    prompt: str,
    model: str | None = None,
    size: str | None = None,
    negative_prompt: str | None = None,
    output_format: str | None = None,
    safety_tolerance: int | None = None,
    enhance_prompt: bool | None = None,
)
```

调用方统一传 `image`,由 `spec.image_field` 分派为 `image`(Qwen-Image-Edit / Kontext-dev)或 `input_image`(Kontext-max / -pro)。

### 8.3 边界:`generate_image` 与 `edit_image`

| | `generate_image` + `reference_image` | `edit_image` + `image` |
|---|---|---|
| 意图 | "照这个样子再画一张" | "把这张图改成……" |
| 支持模型 | FLUX-1.1-pro / Ultra | Qwen-Image-Edit / Kontext 家族 |

### 8.4 注记渲染

`_format_images` 在 header 行下逐条输出注记:

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

后两类行为一致,区别只在"为何允许"。因此统一用 `allow_free_size: bool` 显式表达,**不从文档措辞或类型反推** —— 那是实现期的猜测,不该进代码。

差异仅体现在 `ratio_size` 能否覆盖全部比例:覆盖不全时走兜底。

注意:`allow_free_size` 只管**显式尺寸**;宽高比一律要查 `ratio_size`,因为比例必须先落到具体像素。

## 10. 测试

新增 `tests/test_image_specs.py`:

1. 能力表完整性:`intents` 非空、`ratio_size` 的值都在 `sizes` 或 `allow_free_size`、第 5 节不变量逐条校验
2. `resolve_spec` 对 12 个 id + 2 个 alias 都能命中;未知 id 返回 `None`
3. **意图翻译**:`enhance_prompt` 对 Kontext → `prompt_upsampling`、对 schnell → `prompt_enhancement`;`steps` → `num_inference_steps`;`guidance` → `guidance_scale`
4. 尺寸解析:7 条分支各一例
5. `parse_size`:`"1024x1024"` → 尺寸;`"16:9"` → 比例;`"1024X1024"`(大写)与非法串的处理
6. 最近比例:`Z-Image + 4:3` → `768x1024`;`4:3` 与 `3:4` 到 `1:1` 距离对称
7. 字段剔除:`Z-Image + raw=True` → payload 无 `raw`,notes 含 warn
8. 未知模型:`"foo/bar" + raw=True` → payload 含 `raw`,notes 为空
9. 字段名分派:Kontext → `input_image`;Kontext-dev → `image`
10. `aspect_ratio_native` 透传:Kontext + `size="9:16"` → payload 含 `aspect_ratio`,不含 `image_size`
11. `width_height` 拆分:`FLUX-1.1-pro + size="1280x720"` → `width=1280` `height=720`,无 `image_size`
12. 三态布尔:`raw=None` 不入 payload,`raw=False` 入 payload

改造 `tests/test_client.py`:`ASPECT_RATIOS` 相关断言改为"默认模型视角",或改为直接断言能力表。

## 11. 兼容性

**库层**(人类代码直接调用)保持不变:

- `RESOLUTIONS` / `ASPECT_RATIOS` / `resolve_image_size` 仍是导出名,`__all__` 不变
- `generate_image(prompt, resolution=..., aspect_ratio=..., model=..., ...)` 调用方式不变 —— `resolution` / `aspect_ratio` 保留为兼容入参,内部归一到 `size`
- `edit_image(image, prompt, model=...)` 不变

**MCP 层**:

- 工具名 `generate_image` / `edit_image` 不变
- `resolution` / `aspect_ratio` 两个参数合并为 `size` —— 破坏性,但 MCP 工具签名由 LLM 动态读取,影响可接受
- `batch_size` 默认值从 `1` 改为 `None`(未给),由能力表决定是否下发

**语义变化**(需在 README 注明):

- `ASPECT_RATIOS` 从"全局硬编码映射"变为"默认模型(Z-Image)的映射",数值随之修正(`1:1` 由 `1024x1024` → `512x512`)
- `resolve_image_size()` 保留为纯函数,但库内部改用能力表;保留它是为了不破坏外部 import

## 12. 已知坑与待办

| 项 | 状态 |
|---|---|
| FLUX.1-schnell / FLUX.1-dev 返回的 S3 预签名 URL 签名无效(403) | 已知,`note` 字段标注,不作默认模型 |
| `Qwen/Qwen-Image-Edit-2509` 未出现在文档模型列表中 | **待实测**;确认无效则改默认编辑模型为 `Qwen/Qwen-Image-Edit` |
| FLUX.2-flex 文档列出 `cfg`,但描述写"仅适用于 Qwen/Qwen-Image" | **待实测**;暂按其列出即支持处理 |
| FLUX-1.1-pro 文档 `height` 的描述文字误写为 "Width of..." | 文档笔误,不影响实现 |
| FLUX-1.1-pro-Ultra 同时有 `image_size` 含 `others` 与独立 `aspect_ratio` | 优先级文档未说明;本设计让 `aspect_ratio` 优先(第 7 节第一步第 3 条) |
| `edit_image` 只暴露编辑路径相关的 8 个意图;Qwen-Image-Edit 另支持 `steps` / `cfg` / `guidance` / `batch_size`,不经 MCP 暴露 | 有意的取舍:编辑场景几乎不需要调参,避免签名膨胀。若实测需要,后续加参数即可(能力表已支持) |
