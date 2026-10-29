Adopt a xippios-core minor in xippios-cashctrl, on sdk-template v0.2.2 for good: $ARGUMENTS

Expected argument: the core version to adopt, e.g. `0.4.0`, never a template tag. Without
one, stop and ask; there is no default. cashctrl stays on sdk-template v0.2.2 (D35,
Johannes 2026-10-26) and adopts a core minor without a template release (D85, 2026-10-27):
no `copier update` runs, and `copier update` past v0.2.2 is forbidden (`CLAUDE.md`,
Never). The family rule is still the adoption PR of conventions §15 (ADR-0018): one PR,
before the next release, that adopts core `X.Y.Z` and changes nothing else; no new
endpoints, tasks or fixtures ride along. It may delete the fixtures, mounts and tests
that the adoption itself makes dead, and nothing more (ADR-0018, amendment (d)). A
release tag is not part of an adoption. The PR meets the definition of done,
https://github.com/xippios/sdk-core/blob/main/docs/definition-of-done.md, and the
reviewer judges it against
https://github.com/xippios/sdk-core/blob/main/docs/review-checklist.md.

1. **Where the repository stands.** `.copier-answers.yml` stays at `_commit: v0.2.2` and
   is not edited; its `core_version` is the record of the last render, not the floor.
   `pyproject.toml` is the floor's source of truth: the `xippios-core~=` bound, with no
   `[tool.uv.sources]` pin. Start from a clean `main` on a branch
   `chore/template-update-<core version>` (e.g. `chore/template-update-0.4.0`), which
   keeps the `chore/template-update*` class that rule 8 of the coordination rules names.

2. **What core X.Y.Z asks.** Read sdk-core at `vX.Y.Z`
   (`https://github.com/xippios/sdk-core/tree/vX.Y.Z`, or
   `git -C <workspace root>/sdk-core show vX.Y.Z:<path>` where the family workspace holds
   a clone, the workspace root being the directory that holds the workspace's own
   `CLAUDE.md`; a relative path does not resolve from a worktree): its `CHANGELOG.md`
   section `[X.Y.Z]`, the ADRs it names with their Consequences, and `docs/handover.md`,
   "Adopting core X.Y.Z", its "Every source" and "sdk-cashctrl" sections, for what this
   source deletes and declares. Read sdk-template's `CHANGELOG.md`
   (`https://github.com/xippios/sdk-template/blob/<tag>/CHANGELOG.md`, or
   `git -C <workspace root>/sdk-template show <tag>:CHANGELOG.md`) only to see which
   template release accompanies core X.Y and its Hand-apply list: since no
   `copier update` runs, the template changes the new conventions version needs are
   applied by hand (step 4, row 118).

3. **Item 1: the core floor, by hand.** In `pyproject.toml`, raise `xippios-core` and its
   `mcp`, `http` and `testing` extras to `~=X.Y.0` (or `~=X.Y.Z` when patch `Z` shipped
   what cashctrl adopts; still one minor, conventions §12, ADR-0018 amendment (c)), from
   PyPI with no `[tool.uv.sources]`. Then `uv lock` and `uv sync --all-extras`. No copier
   command runs. Item 2 is unticked with "no template release to adopt (D35)".

4. **Hand-apply.** Port by hand every template change the new conventions version needs:
   the Hand-apply bullets of the template releases after v0.2.2 up to the one that
   accompanies core X.Y, and the template-owned files' changes it makes (`ci.yml`,
   `publish.yml`, `gates.yml`, `live.yml`, the PR template, `.claude/commands/`,
   `.claude/settings.json`, `.claude/family.md`, `tests/conftest.py`,
   `tests/test_family.py`, the template's parts of `CLAUDE.md`; row 118): path, change,
   reason. Every template-rendered file is cashctrl's own, so a change is ported in
   cashctrl's form; `.claude/family.md` alone is copied again whole from the template's
   file at that tag, and a line of cashctrl's own goes to `CLAUDE.md`, never into it.
   A change that does not apply says why in the PR,
   among them every one D35 rules out (deleting `mcp_write.py`, `tasks_write.py` or
   `tests/test_tasks_write.py`, `api_key_location: query`).

5. **Items 3 and 4: workarounds.** Delete every local workaround a core change replaced,
   its tests with it: those core X.Y.Z's ADRs and `docs/handover.md` name for this
   source, and any other the CHANGELOG's breaking changes reach. The PR description names
   the core change for each (`placeholder_api_key` in `conftest.py` → the plugin's pin,
   ADR-0013). Logic duplicated across sources that core does not provide yet is carried
   by the source, named in the PR description and in a queue row; a second source may
   carry the same helper when the row names both, a third never: core takes it in that
   minor (ADR-0023). The fixtures, mounts and tests the adoption makes dead may go with
   it, nothing else.

6. **Item 5: tests that assert what the plugin turns off.** A test that asserts a limiter
   wait, a quota pause or a quota refusal is marked `rate_limited`; a module that tests key
   resolution defines a `placeholder_api_key` fixture that pins nothing; a test that must
   reach the network is marked `network` (ADR-0013, ADR-0015).
   `xippios_placeholder_key_envs` under `[tool.pytest.ini_options]` names
   `CASHCTRL_DEMO_API_KEY`, the demo organisation's key (the scaffold's `CASHCTRL_API_KEY`
   is never read, ADR-0024), and `tests/conftest.py` keeps no placeholder fixture of its
   own.

7. **Item 6: generated enums.** cashctrl has no generated enum file and no
   `scripts/refresh_reference.py`, since it packages no reference data: the item stays
   unticked with "no enum file". An adoption fetches nothing: `docs/upstream/FETCHED.md`
   stays as it is, left to the next `/refresh-upstream`; only the capture script's
   changes are ported (conventions §15, ADR-0003 amendment).

8. **Item 7: scripts.** `uv run mypy` covers `scripts/` too
   (`files = ["src", "tests", "scripts"]`); fix what `--strict` reports there.

9. **Item 8: conventions.** Core X.Y.Z names a conventions version (the header of
   sdk-core's `docs/conventions.md` at `vX.Y.Z`); every rule changed since the version
   this repository last applied (its `CHANGELOG.md` says which) holds after this PR, or
   the PR says why not.

10. **Item 9: changelog.** One line under Unreleased in `CHANGELOG.md` naming core
    X.Y.Z, template v0.2.2 and the conventions version, e.g. "Adopted xippios-core X.Y.Z
    and conventions N on sdk-template v0.2.2 (conventions §15, D35)."

11. **Checks**, all of them:
    `uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest && uv run pre-commit run --all-files`.

12. **The PR.** `gh pr create` from `chore/template-update-<core version>`; the body is
    `.github/PULL_REQUEST_TEMPLATE.md` with its **Enforced by CI**, **Adoption PR** and
    **Process** blocks only (Code, Tests and Docs deleted), ticked, an unticked item with
    a one-line reason, the core change named for each deleted workaround, the live calls
    spent counted (`none` is a count), assumptions and open questions listed, and the
    `## Decisions taken` block. Its merge class is `human` when a hand-maintained
    workflow changes (`ci.yml`, `publish.yml`, `gates.yml`, `live.yml`), and likewise for
    a protected path or a build or install route (ADR-0018, amendment (e); the merge
    classes are in the README of the gates repository,
    https://github.com/xippios/sdk-gates); a `human` adoption waits for Johannes. After
    the reviewer's `ready`, if the `merge-class` check says `auto`, the session enables
    auto-merge here, as `.claude/settings.json` allows; every other `gh pr merge` meets
    the permission prompt:

    ```bash
    gh pr merge --auto --squash -R xippios/sdk-cashctrl <number>
    ```

    GitHub merges once `ci` is green and review threads are resolved.
