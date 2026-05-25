# Changelog

本 Skill 遵循 [SemVer](https://help.aliyun.com/) 风格的版本号；只在 `SKILL.md` 行为变更时升 minor，措辞修订升 patch。

## 0.3.0 — 2026-05-18

### Changed

- **政策松绑**：取消"知识引用必须来自 `*.aliyun.com`"的强制约束。优先仍是阿里云官方文档；HashiCorp、Terraform Registry、阿里云在 GitHub 上的开源仓库（如 LZA）等第三方权威文档现可作为补充直接引用。
- `tests/test_links.py` 与 `scripts/check_links.py` 由白名单校验改为 URL 语法校验。
- `tests/test_structure.py` SKILL.md 行预算 350 → 380，吸收新增国际站/国内站说明等内容。
- AGENTS.md 第 4 节同步松绑措辞。

### Added

- SKILL.md 第 1 章新增 **国内站 vs 国际站** 子节：站点隔离原则、Landing Zone 选站建议、何时选国际站。
- caf-knowledge-base.md 配套补充 **国内站 vs 国际站 站点选型详解** 章节。
- reference.md / templates/terraform-quickstart.md 重新引入 HashiCorp install、Terraform Registry Provider 文档、Alibaba Cloud LZA GitHub 入口等链接。

## 0.2.0 — 2026-05-18

### Added

- 顶部新增"适用边界"章节。
- frontmatter 增加 `version` / `license` / `maintainer` / `tags` 字段。
- 中英文触发关键词共存于 `description`。
- `templates/terraform-quickstart.md`、`templates/README.md`、`scripts/check_links.py`。
- 测试拆分为 `test_structure.py` / `test_links.py` / `test_routing.py` / `test_content.py`。

### Changed

- 拆分 `SKILL.md` 至 ≤ 350 行，详细内容下沉至 `caf-knowledge-base.md` / `templates/`。
- 路由矩阵去重；OpenAPI 错误中心链接修订。
- 全部链接收敛至 `*.aliyun.com` 子域。

### Removed

- `tests/test-results.json`、`tests/test-report.md`、`tests/qa-test-report.md` 从仓库索引移除。

## 0.1.0 — 2026-05-15

- 初始版本：CAF + Landing Zone + WA + OpenAPI + Terraform + 合规 + Agent Skills 门户六大模块。
