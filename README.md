# cuebo Skills

这里存放可以从 cuebo App 的「能力管理 → Skill 库」获取的 Skill。每个一级目录是一个独立 Skill；App 读取根目录的 [`index.json`](index.json) 展示列表，下载选中的目录，校验后让用户预览并安装。

## 目录

| Skill | 用途 |
| --- | --- |
| [`decision-record`](decision-record/) | 把一次选择整理成可以追溯的决策记录 |

## 编写和发布

1. 在根目录下新建与 Skill ID 同名的目录，例如 `my-skill/`。
2. 在目录根部写 `SKILL.md`。首部必须有 `name` 和 `description`，其中 `name` 是小写字母、数字、连字符组成的稳定 ID，且与目录名一致；`description` 是 Agent 在列表和提示中看到的简短用途。
3. 需要补充材料时放进 `references/`；需要脚本时放进 `scripts/`。`SKILL.md` 可引用这些相对路径。不要把密钥或个人数据提交到仓库。
4. 运行 `python3 scripts/generate-index.py` 更新列表，再运行 `python3 scripts/generate-index.py --check` 检查。

```text
my-skill/
├── SKILL.md
├── references/       # 可选
│   └── guide.md
└── scripts/          # 可选
    └── helper.sh
```

App 会逐个下载目录内的文件并检查路径、数量和 `SKILL.md`。安装 Skill 不会运行脚本；Agent 只在启用该 Skill 后收到其元信息，需要正文时才调用 `skill_load`。如果 Skill 需要浏览器、插件、日历等能力，请在正文中写明前提和调用方式，仍以用户当前启用的能力和授权为准。

Skill 已安装后可以在「我的 Skill」中查看文件。仓库发布更新时，当前版本不会自动覆盖用户的本地修改。
