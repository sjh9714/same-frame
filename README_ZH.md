<h1 align="center">same-frame</h1>

<div align="center">

[![stars](https://img.shields.io/github/stars/sjh9714/same-frame?style=flat&color=1f5d4c)](https://github.com/sjh9714/same-frame/stargazers)
[![gallery](https://img.shields.io/badge/gallery-before%20%2F%20after-1f5d4c)](https://sjh9714.github.io/same-frame/)
[![license](https://img.shields.io/badge/license-MIT-1f5d4c)](LICENSE)

**几何被锁住，材质没有。**

**5 个 Krea 2 图生图配方 · 每个 strength 和 seed 都有记录 · 每个都在并非其出处的素材上重跑过一次，tier 写的就是那次结果**

2 个成立 · 1 个有条件 · 1 个部分成立 · 1 个只在同类素材上成立 · 2 个拒绝执行，附证据

可以当一行命令的脚本用，也可以作为 agent skill 放进 Claude Code 或 Codex。

[English](README.md) | [中文](README_ZH.md) · [**前后对比画廊 →**](https://sjh9714.github.io/same-frame/)

</div>

<p align="center">
<img src="examples/02-before.webp" width="192" alt="冷白荧光下的走廊">
<img src="examples/02-after.webp" width="192" alt="同一条走廊，只由远端一个暖光源照亮">
<img src="examples/03-before.webp" width="192" alt="梯田照片">
<img src="examples/03-after.webp" width="192" alt="同一片梯田的水粉画">
</p>

<p align="center"><sub>同一条走廊，同一个灭点，同样的地砖。同一片梯田，同样的等高线。<br>
<a href="https://sjh9714.github.io/same-frame/">逐对并排查看 →</a></sub></p>

这里每个 strength 都是**实际产出配对图像的那个值**，不是建议起点。可用区间是 **0.50–0.60**，比看上去要窄。

这个仓库之所以是现在这个形状：一个只在自己来源图对上成立的配方，是一张结果截图，不是配方。所以五个配方都在**它们并非由之推导出来的素材**上重跑了一遍，下面的 tier 一栏是那次重跑的结果，不是估计。

---

## 五个配方

| 配方 | Tier | 改变什么 | Strength | 在什么素材上成立 |
|---|---|---|---|---|
| `medium-gouache` | **holds** | 照片 → 水粉，轮廓保持原位 | 0.60 | 任何素材，两个方向都行 |
| `palette-shift` | **holds** | 换成三个指定颜色 | 0.55 | 任何素材；照片素材请删掉 "flat colour field" 那句 |
| `relight-hard-sun` | **conditional** | 阴天 → 低角度硬光并投出长影 | 0.55 | 本身就硬且干的材质，已在第二张无关素材上验证 |
| `relight-single-source` | narrow | 单一暖光源，其余落入阴影 | 0.50 | 没有现存自然光的封闭空间 |
| `medium-cyanotype` | partial | → 蓝晒，蓝图形式或照片形式 | 0.60 | 线稿，以及平面化的照片主体 |

```bash
python3 same_frame.py --image photo.jpg --recipe medium-gouache \
  --slot subject="these terraced fields" --slot contour="terrace contour" \
  --out out.png
```

那些 slot 不是装饰。所有保留下来的编辑都在 prompt 里**明确点名了不许移动的东西**——"every terrace contour stays in exactly the same position"、"the rock placement, horizon line and framing identical"。含糊的写法会漂移，所以脚本在 slot 没填满时不会执行。遇到 `partial` 或 `narrow` 的配方，它会在花掉这次请求之前先警告你。

## "材质没有被锁住" 是什么意思

<table>
<tr><td width="33%" align="center"><img src="examples/03-before.webp" width="200"><br><sub>湿的水稻梯田</sub></td>
<td width="33%" align="center"><img src="examples/limit-relight-material-drift.webp" width="200"><br><sub><b>relight-hard-sun 之后</b></sub></td>
<td width="34%">

`relight-hard-sun` 跑在湿的水稻梯田上，strength 0.55，seed 232270180。每条等高线都留在原位，低角度硬光和长影也完全按要求出现了。

然后水田变成了**干燥的石砌阶梯**。水没了，植被也没了。

硬光会逼模型重新推导每个表面如何响应光照，而一个在平光下读作"湿"的表面，在硬光下会被重渲染成"干"。这个问题在配方来源的那张海岸线上看不出来，因为玄武岩本来就是干的。

**验收时要看东西是什么做的，而不只是看它在哪。**

</td></tr>
</table>

## 两个直接拒绝执行的请求

大多数 prompt 合集会告诉你什么都能做。这两件事跑过、失败了，失败的图就在这个仓库里。

<table>
<tr><td width="50%">

**增删物体 → 拒绝**

<img src="examples/refuse-removal-before.webp" width="150"> <img src="examples/refuse-removal-after.webp" width="150">

在 strength 0.5 下要求去掉热气、让液面平静如镜。热气原样返回了。给海岸线加雪，返回的是同一条稍微冷一点的海岸线；让天空变暗，返回的是同一片天空。

调高 strength 不能解决这个问题——它只会把你的主体换掉。**请用带 mask 的 inpainting。**

</td><td width="50%">

**同一个人物换场景 → 拒绝**

<img src="examples/refuse-identity-before.webp" width="150"> <img src="examples/refuse-identity-after.webp" width="150">

0.72 时场景确实是新的，人不是同一个，只有毛衣和配色延续了下来。0.45 时脸保住了，但源图构图被一起拖了过来——一张三视图影棚设定稿变成了同样三视图、只是搬到了港口。

两者之间不存在一个能只要其一的数值。**请训练 LoRA。**

</td></tr>
</table>

```
$ python3 same_frame.py --image mug.png --prompt "Remove the steam entirely." --strength 0.5

Refusing: Krea 2 does not add or remove objects. Refuse and say why.
  (triggered by 'remove the' — use --force if this read you wrong)

  This was already run at strength 0.5, seed 1499506316:
    asked for: Remove the steam entirely and let the coffee surface go still and mirror-flat.
    got:       The steam came back.
    see:       examples/refuse-removal-after.webp

  Instead: Use an inpainting model with a mask. This is a segmentation problem,
           not a strength problem.
```

两个拒绝都可以用 `--force` 越过。对别人的用例过于笃定本身就是一种失败模式，但默认值是实测结果。

## 另外两个限制，附图

**线稿无法被凭空造出来。** `medium-cyanotype` 跑在照片上（seed 2065751023），每块岩石的位置都保住了，颜色也变成了普鲁士蓝，但**完全没有线稿**——得到的是一张蓝调照片，不是蓝图（[`limit-cyanotype-on-photo.webp`](examples/limit-cyanotype-on-photo.webp)）。轮廓线是照片里不存在的内容，模型不会凭空造出它，就像它不会凭空造出你要求添加的物体一样。连续调 → 连续调可以；任何东西 → 线稿则需要素材本身就是线稿。反方向没问题：水粉跑在线稿爆炸图上是这个仓库里最干净的结果。

**重打光只会加光，不会减光。** `relight-single-source` 跑在室外（seed 1114110846），"近处一切落入阴影"完全没有发生（[`limit-single-source-outdoors.webp`](examples/limit-single-source-outdoors.webp)）。再跑一次，这次是带天窗的阁楼工作间（seed 1269377144），只成功了一半：工作灯亮了、角落暗下去了，而**天窗还是原来那么亮**（[`limit-single-source-daylight.webp`](examples/limit-single-source-daylight.webp)）。而且 prompt 写的是一盏灯，出来的是两盏。

所以"只有室内"说得太宽。真正的规则更锋利：现存光源是*内容*，把它关掉是*移除*，而移除正是这个模型不会做的事——和拒绝增删物体撞的是同一堵墙，只是低了一层。用在走廊、隧道、无窗房间。有活窗户的房间会保住它的窗户。

**材质那条注意事项现在是验证过的前提条件，不是猜测。** `relight-hard-sun` 原本因为一次失败被标为 partial。跑在清水混凝土楼梯间上（seed 561284942）完全成立——同样的踏面、同样的扶手、同样的天窗，低角度硬光沿右墙投下干净的对角阴影，混凝土仍然是混凝土（[`ok-relight-on-concrete.webp`](examples/ok-relight-on-concrete.webp)）。湿梯田那次漂移是材质的问题，不是配方的问题。

## 安装

**Claude Code**

```bash
git clone https://github.com/sjh9714/same-frame ~/.claude/skills/same-frame
```

**Codex**

```bash
git clone https://github.com/sjh9714/same-frame ~/.codex/skills/same-frame
```

**独立使用** —— 除标准库外无任何依赖：

```bash
git clone https://github.com/sjh9714/same-frame && cd same-frame
printf 'FAL_KEY=%s\n' 'YOUR_KEY' > .env && chmod 600 .env   # 不要把密钥贴进聊天窗口
python3 same_frame.py --list
```

在 [fal.ai](https://fal.ai/dashboard/keys) 获取密钥。约 **$0.008 每百万像素**——1024×1024 一次编辑大概八毫美元。`.env` 已在 gitignore 里。

## 复现

这个 endpoint 是确定性的：相同 seed、strength、prompt 和输入字节的两次运行，**1,048,576 个像素中有 0 个不同**。

所以如果重跑结果不一样，说明输入变了。这一点会在一个具体的地方咬人——把原本用 PNG 做出来的编辑改喂有损的 WebP 副本，结果偏移了 **17.0/255**（平均每像素）。构图、配色、媒介都回来了，笔触质感没有。请保留原始文件。对 image-to-image 而言，光有 seed 不足以复现一次生成，**seed 加上精确的输入字节**才行。

## 哪些没有验证过

上述区间是 **Krea 2 Turbo** 在接近正方形图像上的测量结果。0.55 在 Krea 2 non-turbo、别的模型或 16:9 上是否意味着同样的东西，没有测过——请重新测量，不要直接沿用这个数字。

每个配方只在**一张**无关素材上做过泛化测试。这足以区分"能用"和"只在自己来源上能用"，但不足以标出一个 `partial` 配方的边界在哪。五个配方、每个一次跨素材运行，样本量很小。这是诚实的样本量。

## 来源

从 [awesome-krea-2](https://github.com/sjh9714/awesome-krea-2) 中抽出——114 次生成、保留 85 张、砍掉 29 张，每个 seed 都有记录。这里的两个拒绝，就是被砍掉的其中两张。

代码和 prompt 采用 MIT。示例图像是 Krea 2 Turbo 的输出，在 Krea 2 Community License 下由仓库作者生成，作为模型输出而非照片或人类作品呈现。每次请求都开启了 safety checker。
