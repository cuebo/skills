# cuebo Skills

这里维护 cuebo App 的 Skill 商店清单。App 读取根目录的 [`index.json`](index.json) 展示列表，按 `sourceURL` 下载对应仓库的 Skill，校验后让用户预览并安装。也可直接收录本仓库的一级目录。

## 目录

| Skill | 用途 |
| --- | --- |
| [`pdf`](https://github.com/anthropics/skills/tree/main/skills/pdf) | Anthropic 的 PDF 处理 Skill；读取、创建、填写和整理 PDF |
| [`screenshot-device-frame`](screenshot-device-frame/) | 把手机/平板截图套进 iPhone、iPad、MacBook 机壳，生成 App Store 预览图或社媒配图 |

## 编写和发布

1. 在自己的公开 GitHub 仓库中新建 Skill 目录，例如 `my-skill/`；也可以直接在本仓库新建一级目录。
2. 在目录根部写 `SKILL.md`。首部必须有 `name` 和 `description`，其中 `name` 是小写字母、数字、连字符组成的稳定 ID，且与目录名一致；`description` 是 Agent 在列表和提示中看到的简短用途。
3. 需要补充材料时放进 `references/`；需要脚本时放进 `scripts/`。`SKILL.md` 可引用这些相对路径。不要把密钥或个人数据提交到仓库。
4. 外部 Skill 在 [`external-skills.json`](external-skills.json) 登记 `id`、`name`、`description`、`fileCount` 和 `sourceURL`。`sourceURL` 指向 `https://github.com/owner/repo/tree/branch/my-skill`，也可以是公开的 HTTPS ZIP 链接；App 当前不支持私有仓库凭据或带斜杠的分支名。内部 Skill 无需登记该文件。
5. 运行 `python3 scripts/generate-index.py` 更新列表，再运行 `python3 scripts/generate-index.py --check` 检查。

```text
my-skill/
├── SKILL.md
├── references/       # 可选
│   └── guide.md
└── scripts/          # 可选
    └── helper.sh
```

App 会逐个下载目录内的文件并检查路径、数量和 `SKILL.md`。安装 Skill 不会运行脚本；Agent 只在启用该 Skill 后收到其元信息，需要正文时才调用 `skill_load`。如果 Skill 需要浏览器、插件、日历等能力，请在正文中写明前提和调用方式，仍以用户当前启用的能力和授权为准。

`index.json` 中的 `sourceURL` 优先于 `path`。纯外部 Skill 可以只提供 `sourceURL`，无需复制文件到这里。PDF Skill 的文件和许可条款由 [Anthropic 原仓库](https://github.com/anthropics/skills/tree/main/skills/pdf)维护。

Skill 已安装后可以在「我的 Skill」中查看文件。仓库发布更新时，当前版本不会自动覆盖用户的本地修改。
