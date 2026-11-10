# 素材版权说明 / Assets Notice

本仓库的 **MIT 协议只覆盖代码**。以下内容**不属于** MIT 协议的授权范围。

> 这句话故意不写进 LICENSE 里：GitHub 识别协议是把 LICENSE 跟官方模板做相似度匹配，
> 在 MIT 正文后面追加任何内容都会拉低相似度、导致仓库页面上显示不出 MIT 标识。
> 所以 LICENSE 里只有纯 MIT 文本，范围说明放在这里。

## 不在 MIT 范围内的内容

| 路径 | 内容 | 版权 |
|---|---|---|
| `src/common/story/` | 剧本数据（6975 个节点，4129 句对白 + 2827 句旁白） | 原作及其作者 |
| `src/common/img/b/` | 背景 111 张 | 同上 |
| `src/common/img/s/` | 立绘 158 张 | 同上 |
| `src/common/img/c/` | CG 44 张（剧情用） | 同上 |
| `src/common/img/g/` | CG 全图 44 张（鉴赏拖动用） | 同上 |
| `src/common/img/t/` | CG 缩略图 44 张 | 同上（由上面裁切而来） |
| `src/common/title_bg.png` | 标题背景（原作主菜单美术） | 同上 |
| `src/common/logo.png` | 官方 LOGO | 同上 |
| `src/common/ui/*.png` | 警告页三角、○/✕、锁定占位 | 同上（来自原作界面） |
| `preview/*.png` | 界面预览与宣传图 | 同上 |

这些都是从 PC 版 Ren'Py 原作 `archive.rpa` 解包并转码而来的衍生文件，
版权归 **《拆迁地球及爱情事故》** 的原作者所有。

收录它们只是为了让仓库能直接构建出可运行的包——代码本身不依赖任何具体素材，
换一套剧本和图片照样能跑（见 `tools/gen_story.py` / `tools/gen_assets.py`）。

## 使用限制

- 请勿用于任何商业用途。
- 本项目为非官方、非商业性的个人移植作品，与 **Astrobox**、**小米（Xiaomi）**
  均无关联，亦未获得其授权、赞助或认可。
- 如版权方有异议，删除上表中列出的目录与文件即可。
- 如有侵权，请联系删除。

## 在 MIT 范围内的内容

`src/pages/`、`src/common/reader.js`、`src/common/theme.js`、`src/app.ux`、
`src/manifest.json`、`tools/`、以及所有文档。详见 [LICENSE](LICENSE)。
