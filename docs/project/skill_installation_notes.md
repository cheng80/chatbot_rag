# 스킬 설치 메모

스냅샷 시각: 2026-06-01 KST

이 문서는 현재 로컬에 남겨둔 일부 스킬을 다른 컴퓨터에서 다시 설치하거나 복구하는 방법을 정리한다. 아래 경로는 프로젝트 경로가 아니라 각 컴퓨터의 사용자 홈 기준 로컬 경로다.

## 대상 디렉토리

Codex 직접 스킬:

```bash
mkdir -p ~/.codex/skills
```

Agent sidecar 스킬:

```bash
mkdir -p ~/.agents/skills
```

## Git 원격이 있는 스킬

### `codex-subagent-skill`

현재 설치 위치:

```text
~/.codex/skills/codex-subagent-skill
```

현재 원격:

```text
https://github.com/iipanda/codex-subagent-skill.git
```

설치:

```bash
git clone https://github.com/iipanda/codex-subagent-skill.git ~/.codex/skills/codex-subagent-skill
```

업데이트:

```bash
cd ~/.codex/skills/codex-subagent-skill
git pull --ff-only
```

## gstack이 생성하는 스킬

### `gstack-claude`

현재 설치 위치:

```text
~/.codex/skills/gstack-claude
```

이 스킬은 독립적으로 설치한 스킬이 아니다. gstack의 Codex용 setup 과정에서 생성되며, 관리 중인 gstack repo 안의 생성물로 연결된다.

```text
~/.gstack/repos/gstack/.agents/skills/gstack-claude
```

설치 또는 갱신:

```bash
mkdir -p ~/.gstack/repos

if [ ! -d ~/.gstack/repos/gstack ]; then
  git clone --single-branch --depth 1 https://github.com/garrytan/gstack.git ~/.gstack/repos/gstack
fi

cd ~/.gstack/repos/gstack
git pull --ff-only origin main
./setup --host codex --prefix
```

주의: `gstack-claude`는 upstream gstack에 포함된 Claude Code CLI wrapper 스킬이다. 이 스킬 자체가 Claude 설정, Claude hook, Claude MCP 서버를 다시 설치하지는 않는다.

## 자동 백업과 복원

아래 스크립트는 이 문서에 적은 대상 스킬을 백업하고 복원한다. symlink로 설치된 스킬도 다른 컴퓨터에서 깨지지 않도록 실제 파일 내용으로 백업한다.

자동 백업:

```bash
.venv/bin/python scripts/backup_selected_skills.py
```

기본 백업 위치는 `data/generated/skill_backups/skills-backup-<timestamp>`이며, 이 폴더는 git ignore 대상이다.

특정 위치에 백업:

```bash
.venv/bin/python scripts/backup_selected_skills.py --output-dir skills-backup
```

자동 복원:

```bash
.venv/bin/python scripts/restore_selected_skills.py skills-backup --replace
```

기존 스킬을 덮어쓰지 않고 없는 것만 복원:

```bash
.venv/bin/python scripts/restore_selected_skills.py skills-backup --skip-existing
```

권장 백업 구조:

```text
skills-backup/
├── codex/
│   ├── app-store-screenshots/
│   ├── codex-subagent-skill/
│   ├── gstack-claude/
│   └── slidev/
└── agents/
    ├── design-md/
    ├── enhance-prompt/
    ├── react-components/
    ├── remotion/
    ├── shadcn-ui/
    └── stitch-loop/
```

복구 명령:

```bash
mkdir -p ~/.codex/skills ~/.agents/skills

cp -R skills-backup/codex/app-store-screenshots ~/.codex/skills/
cp -R skills-backup/codex/codex-subagent-skill ~/.codex/skills/
cp -R skills-backup/codex/gstack-claude ~/.codex/skills/
cp -R skills-backup/codex/slidev ~/.codex/skills/

cp -R skills-backup/agents/design-md ~/.agents/skills/
cp -R skills-backup/agents/enhance-prompt ~/.agents/skills/
cp -R skills-backup/agents/react-components ~/.agents/skills/
cp -R skills-backup/agents/remotion ~/.agents/skills/
cp -R skills-backup/agents/shadcn-ui ~/.agents/skills/
cp -R skills-backup/agents/stitch-loop ~/.agents/skills/
```

## 로컬 복사로 관리하는 스킬

아래 스킬들은 현재 각 스킬 디렉토리 안에 `.git` 메타데이터가 없다. 따라서 다른 컴퓨터에서 복구하려면 백업, dotfiles repo, 또는 별도 스킬 repo에서 해당 스킬 디렉토리 전체를 복사해야 한다.

### `app-store-screenshots`

설치 위치:

```text
~/.codex/skills/app-store-screenshots
```

현재 필요한 파일:

```text
SKILL.md
mockup.png
```

### `slidev`

설치 위치:

```text
~/.codex/skills/slidev
```

현재 필요한 구성:

```text
README.md
SKILL.md
references/
```

### `design-md`

설치 위치:

```text
~/.agents/skills/design-md
```

현재 필요한 구성:

```text
README.md
SKILL.md
examples/DESIGN.md
```

### `enhance-prompt`

설치 위치:

```text
~/.agents/skills/enhance-prompt
```

현재 필요한 구성:

```text
README.md
SKILL.md
references/KEYWORDS.md
```

### `react-components`

설치 위치:

```text
~/.agents/skills/react-components
```

현재 필요한 구성:

```text
README.md
SKILL.md
examples/
resources/
scripts/
package.json
package-lock.json
```

### `remotion`

설치 위치:

```text
~/.agents/skills/remotion
```

현재 필요한 구성:

```text
README.md
SKILL.md
examples/
resources/
scripts/
```

### `shadcn-ui`

설치 위치:

```text
~/.agents/skills/shadcn-ui
```

현재 필요한 구성:

```text
README.md
SKILL.md
examples/
resources/
scripts/
```

### `stitch-loop`

설치 위치:

```text
~/.agents/skills/stitch-loop
```

현재 필요한 구성:

```text
README.md
SKILL.md
examples/
resources/
```

## 현재 관리 방침

이 컴퓨터에는 아직 Silent Casting을 적용하지 않았다. 따라서 이 문서의 스킬들은 현재 수동 관리 대상 로컬 스킬로 본다.

다른 컴퓨터에서는 아래 방식 중 하나로 복구한다.

```text
1. Git 원격이 확인된 스킬은 해당 repo를 직접 clone한다.
2. gstack처럼 다른 도구가 생성하는 스킬은 생성 도구를 다시 실행한다.
3. Git 원격이 없는 스킬은 백업에서 스킬 디렉토리 전체를 복사한다.
```

나중에 이 스킬들을 전용 스킬 repo로 옮긴다면, 각 스킬을 `SKILL.md`가 포함된 완전한 디렉토리 단위로 보관한다. `references/`, `resources/`, `examples/`, `scripts/`, 이미지, package 파일 같은 보조 파일도 같은 스킬 디렉토리 안에 함께 둔다.

## 검증

복구 후 아래 명령으로 확인한다.

```bash
find ~/.codex/skills ~/.agents/skills -name SKILL.md | sort
```

이 컴퓨터의 기대 목록은 아래 문서와 비교한다.

```text
docs/project/global_skills_inventory.md
```
