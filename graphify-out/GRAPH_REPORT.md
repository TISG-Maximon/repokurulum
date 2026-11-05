# Graph Report - repokurulum  (2026-11-05)

## Corpus Check
- Corpus is ~1,494 words - fits in a single context window. You may not need a graph.

## Summary
- 43 nodes · 63 edges · 8 communities
- Extraction: 86% EXTRACTED · 14% INFERRED · 0% AMBIGUOUS · INFERRED: 9 edges (avg confidence: 0.89)
- Token cost: 88,662 input · 0 output

## Community Hubs (Navigation)
- Betik Kurallari ve Hatalar
- MCP Kavramlari ve graphify MCP
- graphify Skill Altyapisi
- Ana Kurulum Akisi
- Opsiyonel MCP Sunuculari
- Claude Code ve Uzaktan Kontrol
- Uzak Masaustu ve Dogrulama
- Playwright Tarayici Zinciri

## God Nodes (most connected - your core abstractions)
1. `kurulum.bat (main installer)` - 17 edges
2. `CLAUDE.md (repo instructions)` - 10 edges
3. `Playwright MCP (@playwright/mcp)` - 7 edges
4. `graphify` - 7 edges
5. `repokurulum README` - 6 edges
6. `scripts/mcp-ekstra.bat` - 5 edges
7. `Common errors and fixes` - 5 edges
8. `cmd /c npx stdio MCP pattern` - 4 edges
9. `graphifyy PyPI package` - 3 edges
10. `scripts/graphify-proje.bat` - 3 edges

## Surprising Connections (you probably didn't know these)
- `kurulum.bat (main installer)` --implements--> `Idempotent scripts principle`  [INFERRED]
  README.md → CLAUDE.md
- `CLAUDE.md (repo instructions)` --implements--> `CLAUDE.md persistent instructions`  [INFERRED]
  CLAUDE.md → README.md
- `Call .cmd tools with call` --conceptually_related_to--> `Common errors and fixes`  [INFERRED]
  CLAUDE.md → README.md
- `CRLF line endings (.gitattributes)` --conceptually_related_to--> `Common errors and fixes`  [INFERRED]
  CLAUDE.md → README.md
- `cmd /c npx stdio MCP pattern` --rationale_for--> `Playwright MCP (@playwright/mcp)`  [INFERRED]
  CLAUDE.md → README.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Four ways to extend Claude Code (MCP, Skill, Hook, CLAUDE.md)** — readme_mcp_server, readme_skill, readme_hook, readme_claude_md_concept [EXTRACTED 1.00]
- **Windows batch script conventions** — claude_bat_ascii_rule, claude_call_cmd_tools_rule, claude_crlf_line_endings, claude_idempotent_scripts, claude_cmd_c_npx_pattern [EXTRACTED 1.00]
- **Base tools installed by kurulum.bat via winget** — readme_winget, readme_git_for_windows, readme_nodejs_lts, readme_uv, readme_google_chrome [EXTRACTED 1.00]

## Communities (8 total, 0 thin omitted)

### Community 0 - "Betik Kurallari ve Hatalar"
Cohesion: 0.24
Nodes (3): CLAUDE.md (repo instructions), CLAUDE.md persistent instructions, Common errors and fixes

### Community 1 - "MCP Kavramlari ve graphify MCP"
Cohesion: 0.29
Nodes (7): graphify-mcp server, scripts/graphify-proje.bat, Hook (PreToolUse), MCP scopes (local/project/user), MCP server (Model Context Protocol), ornek-mcp-windows.json, repokurulum README

### Community 2 - "graphify Skill Altyapisi"
Cohesion: 0.40
Nodes (6): graphifyy PyPI package, graphify, graphify workflow (query/path/explain), Skill (SKILL.md), tree-sitter, uv (Astral)

### Community 3 - "Ana Kurulum Akisi"
Cohesion: 0.33
Nodes (4): kurulum.bat (main installer), logs/kurulum.log, Manual installation steps, winget

### Community 4 - "Opsiyonel MCP Sunuculari"
Cohesion: 0.50
Nodes (4): context7 MCP, GitHub MCP, scripts/mcp-ekstra.bat, sequential-thinking MCP

### Community 5 - "Claude Code ve Uzaktan Kontrol"
Cohesion: 0.67
Nodes (3): Claude Code CLI, Git for Windows, Path B: Claude Code Remote Control

### Community 6 - "Uzak Masaustu ve Dogrulama"
Cohesion: 0.67
Nodes (3): scripts/dogrula.bat (verification), Playwright --headless option, Path A: Remote desktop install

### Community 7 - "Playwright Tarayici Zinciri"
Cohesion: 0.67
Nodes (3): Google Chrome, Node.js LTS / npx, Playwright MCP (@playwright/mcp)

## Knowledge Gaps
- **11 isolated node(s):** `logs/kurulum.log`, `winget`, `Skill (SKILL.md)`, `CLAUDE.md persistent instructions`, `graphify workflow (query/path/explain)` (+6 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 14 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `kurulum.bat (main installer)` connect `Ana Kurulum Akisi` to `Betik Kurallari ve Hatalar`, `MCP Kavramlari ve graphify MCP`, `graphify Skill Altyapisi`, `Opsiyonel MCP Sunuculari`, `Claude Code ve Uzaktan Kontrol`, `Uzak Masaustu ve Dogrulama`, `Playwright Tarayici Zinciri`?**
  _High betweenness centrality (0.560) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `kurulum.bat (main installer)` (e.g. with `Idempotent scripts principle` and `Manual installation steps`) actually correct?**
  _`kurulum.bat (main installer)` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `logs/kurulum.log`, `winget`, `Skill (SKILL.md)` to the rest of the system?**
  _11 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Why does `CLAUDE.md (repo instructions)` connect `Betik Kurallari ve Hatalar` to `MCP Kavramlari ve graphify MCP`, `graphify Skill Altyapisi`, `Playwright Tarayici Zinciri`?**
  _High betweenness centrality (0.238) - this node is a cross-community bridge._
- **Why does `repokurulum README` connect `MCP Kavramlari ve graphify MCP` to `Betik Kurallari ve Hatalar`, `Ana Kurulum Akisi`, `Opsiyonel MCP Sunuculari`, `Uzak Masaustu ve Dogrulama`?**
  _High betweenness centrality (0.207) - this node is a cross-community bridge._