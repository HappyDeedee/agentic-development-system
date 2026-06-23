# Code Understanding

Use this reference when a non-empty project may need code structure analysis
before planning or implementation.

## Core Position

Code understanding is an optional enhancement, not a bootstrap prerequisite.
The plugin may recommend an external repo-map tool such as aider, but it must
not require, install, configure, or run that tool by default.

## Aider Adapter Policy

- Treat aider as an optional external adapter for repo-map style code context.
- Do not add aider as a hard plugin dependency.
- Do not run aider automatically.
- Detect whether a repo-map pass would help, then explain the reason and scan
  boundary to the user.
- Only run a repo-map tool after the user confirms the scope.
- Treat repo-map output as baseline evidence, not as product requirements,
  ADRs, tests, or source-of-truth docs.

## Recommend Repo Map When

Recommend a repo-map pass when most of these are true:

- the target is a code repository;
- manifests such as `package.json`, `pyproject.toml`, `go.mod`,
  `Cargo.toml`, `pom.xml`, or `build.gradle` exist;
- there are many code files or multiple source directories;
- the user wants to understand, modify, refactor, migrate, or plan code work;
- architecture or technical stack docs are missing or stale;
- future work depends on current code structure.

## Do Not Recommend Or Defer When

Do not recommend automatic code mapping when:

- the target is empty;
- the target is primarily documentation or private evidence;
- the root is a mixed workspace with unconfirmed nested repositories;
- private legal/customer data, cookies, account profiles, local databases, or
  secrets are present;
- the user only asked for governance-doc initialization;
- the project is small enough to inspect directly.

## Scan Boundary

Before running any repo-map tool, state:

- target root;
- included code directories;
- excluded directories;
- nested repositories skipped;
- sensitive paths not read;
- whether `.gitignore` or a project-specific ignore file will be respected.

Default exclusions:

- `.git/`, `.hg/`, `.svn/`;
- dependency folders such as `node_modules/`, `vendor/`, `.venv/`, `venv/`;
- build/cache folders such as `dist/`, `build/`, `.next/`, `__pycache__/`;
- secrets and local runtime files such as `.env`, `.env.*`, `*.pem`,
  `*.key`, `*.cookie`, `*.cookies`;
- private evidence folders, customer data, legal materials, screenshots, and
  local exports unless explicitly selected by the user.

## Output Contract

If a repo-map pass is used, record:

- command or tool used;
- scan root;
- included and excluded paths;
- summary of discovered code structure;
- limitations and stale risks;
- how the map influenced the next plan.

Do not claim implementation readiness solely because a repo map was generated.
