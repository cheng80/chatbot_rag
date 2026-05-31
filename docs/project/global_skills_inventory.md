# 전역 스킬 목록

스냅샷 시각: 2026-06-01 08:11:22 KST

이 문서는 Claude 관련 정리와 gstack 중복 정리 이후 현재 이 컴퓨터에 남아 있는 전역 스킬 목록을 기록한다.

## 요약

- `~/.codex/skills`: Codex 직접 스킬과 Codex용 gstack 스킬이 있다.
- `~/.agents/skills`: agent sidecar 스킬만 남아 있다.
- `~/.agents/skills`에는 gstack 계열이 남아 있지 않다.
- `gstack-claude`는 아직 `~/.codex/skills`에 남아 있다. 이것은 Claude 앱/설정/MCP/hook이 아니라 gstack upstream에 포함된 Claude Code CLI wrapper 스킬이다.

## `~/.codex/skills`

### `SKILL.md` 기준 목록

아래 목록은 `SKILL.md` 파일을 기준으로 발견한 스킬이다.

```text
.system/imagegen
.system/openai-docs
.system/plugin-creator
.system/skill-creator
.system/skill-installer
app-store-screenshots
codex-subagent-skill
gstack
gstack/gstack-upgrade
huashu-design
pdf
playwright
slidev
technical-infographic
```

### 최상위 항목

아래 목록은 `~/.codex/skills` 바로 아래의 최상위 항목이다. gstack의 Codex용 스킬들은 대부분 최상위 symlink 디렉토리로 존재한다.

```text
.system
app-store-screenshots
codex-subagent-skill
gstack
gstack-autoplan
gstack-benchmark
gstack-benchmark-models
gstack-browse
gstack-canary
gstack-careful
gstack-claude
gstack-context-restore
gstack-context-save
gstack-cso
gstack-design-consultation
gstack-design-html
gstack-design-review
gstack-design-shotgun
gstack-devex-review
gstack-document-generate
gstack-document-release
gstack-freeze
gstack-guard
gstack-health
gstack-investigate
gstack-ios-clean
gstack-ios-design-review
gstack-ios-fix
gstack-ios-qa
gstack-ios-sync
gstack-land-and-deploy
gstack-landing-report
gstack-learn
gstack-make-pdf
gstack-office-hours
gstack-open-gstack-browser
gstack-pair-agent
gstack-plan-ceo-review
gstack-plan-design-review
gstack-plan-devex-review
gstack-plan-eng-review
gstack-plan-tune
gstack-qa
gstack-qa-only
gstack-retro
gstack-review
gstack-scrape
gstack-setup-browser-cookies
gstack-setup-deploy
gstack-setup-gbrain
gstack-ship
gstack-skillify
gstack-spec
gstack-sync-gbrain
gstack-unfreeze
gstack-upgrade
huashu-design
pdf
playwright
slidev
technical-infographic
```

참고: gstack의 실제 원본 repo는 `~/.gstack/repos/gstack`에 두고, `~/.codex/skills`에는 Codex에서 읽는 런타임 스킬과 symlink만 남기는 구조다.

## `~/.agents/skills`

### `SKILL.md` 기준 목록

```text
cavecrew
caveman
caveman-commit
caveman-compress
caveman-help
caveman-review
caveman-stats
design-md
enhance-prompt
react-components
remotion
shadcn-ui
stitch-loop
```

### 최상위 항목

현재 `SKILL.md` 기준 목록과 최상위 항목이 같다.

```text
cavecrew
caveman
caveman-commit
caveman-compress
caveman-help
caveman-review
caveman-stats
design-md
enhance-prompt
react-components
remotion
shadcn-ui
stitch-loop
```
