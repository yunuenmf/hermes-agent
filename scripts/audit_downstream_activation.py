#!/usr/bin/env python3
"""Audit whether merged downstream PR source is present in the live runtime checkout.

Read-only against the runtime checkout. Writes report artifacts under the current worktree.
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

PR_NUMBERS = [14, 15, 17, 18, 19, 21, 22, 24]
RUNTIME = Path('/home/engs2272/.hermes/hermes-agent')


def run(cmd: list[str], cwd: str | Path | None = None, check: bool = True) -> str:
    p = subprocess.run(cmd, cwd=str(cwd) if cwd else None, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and p.returncode != 0:
        raise RuntimeError(f"command failed {cmd}: {p.stderr.strip()}\n{p.stdout}")
    return p.stdout


def git(args: list[str], repo: Path | str = '.') -> str:
    return run(['git', '-C', str(repo), *args])


def show_blob(repo: Path | str, rev: str, path: str) -> bytes | None:
    p = subprocess.run(['git', '-C', str(repo), 'show', f'{rev}:{path}'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    if p.returncode != 0:
        return None
    return p.stdout


def worktree_file(path: str) -> bytes | None:
    p = RUNTIME / path
    if not p.exists() or not p.is_file():
        return None
    return p.read_bytes()


def pr_json(n: int) -> dict:
    out = run([
        'gh', 'pr', 'view', str(n), '--repo', 'yunuenmf/hermes-agent',
        '--json', 'number,title,state,mergedAt,mergeCommit,headRefName,baseRefName,files,url'
    ])
    data = json.loads(out)
    data['mergeCommit'] = data['mergeCommit']['oid'] if data.get('mergeCommit') else None
    data['files'] = [f['path'] for f in data.get('files', [])]
    return data


def main() -> int:
    root = Path.cwd()
    outdir = root / 'artifacts' / 't_97799c27'
    outdir.mkdir(parents=True, exist_ok=True)

    runtime_head = git(['rev-parse', 'HEAD'], RUNTIME).strip()
    downstream_main = git(['rev-parse', 'yunuenmf/main']).strip()
    runtime_branch = git(['branch', '--show-current'], RUNTIME).strip()
    runtime_status = git(['status', '--porcelain=v1'], RUNTIME)
    dirty_paths = {line[3:] for line in runtime_status.splitlines() if len(line) >= 4}

    rows = []
    for n in PR_NUMBERS:
        pr = pr_json(n)
        merge = pr['mergeCommit']
        parent = git(['rev-parse', f'{merge}^'], root).strip()
        merge_in_runtime = subprocess.run(['git', '-C', str(RUNTIME), 'merge-base', '--is-ancestor', merge, 'HEAD']).returncode == 0
        merge_in_main = subprocess.run(['git', '-C', str(root), 'merge-base', '--is-ancestor', merge, 'yunuenmf/main']).returncode == 0
        files = pr['files']
        stats = {
            'files_total': len(files),
            'runtime_head_equals_merge': 0,
            'runtime_worktree_equals_merge': 0,
            'runtime_head_equals_main': 0,
            'runtime_worktree_equals_main': 0,
            'dirty_or_untracked_touched': [],
            'missing_in_runtime_worktree': [],
            'different_from_main_worktree': [],
        }
        file_rows = []
        for f in files:
            merge_blob = show_blob(root, merge, f)
            main_blob = show_blob(root, 'yunuenmf/main', f)
            runtime_head_blob = show_blob(RUNTIME, 'HEAD', f)
            runtime_work_blob = worktree_file(f)
            h_eq_merge = runtime_head_blob == merge_blob
            w_eq_merge = runtime_work_blob == merge_blob
            h_eq_main = runtime_head_blob == main_blob
            w_eq_main = runtime_work_blob == main_blob
            stats['runtime_head_equals_merge'] += int(h_eq_merge)
            stats['runtime_worktree_equals_merge'] += int(w_eq_merge)
            stats['runtime_head_equals_main'] += int(h_eq_main)
            stats['runtime_worktree_equals_main'] += int(w_eq_main)
            if runtime_work_blob is None and main_blob is not None:
                stats['missing_in_runtime_worktree'].append(f)
            if not w_eq_main:
                stats['different_from_main_worktree'].append(f)
            if f in dirty_paths or any(dp == f or dp.startswith(f + '/') for dp in dirty_paths):
                stats['dirty_or_untracked_touched'].append(f)
            file_rows.append({
                'path': f,
                'head_equals_merge': h_eq_merge,
                'worktree_equals_merge': w_eq_merge,
                'head_equals_main': h_eq_main,
                'worktree_equals_main': w_eq_main,
                'dirty_touched': f in stats['dirty_or_untracked_touched'],
            })
        if stats['runtime_worktree_equals_main'] == len(files):
            source_presence = 'present_in_runtime_worktree_for_all_touched_files'
        elif stats['runtime_worktree_equals_main'] > 0:
            source_presence = 'partial_or_overlapped_in_runtime_worktree'
        else:
            source_presence = 'not_present_in_runtime_worktree_for_touched_files'
        rows.append({
            'pr': n,
            'title': pr['title'],
            'url': pr['url'],
            'state': pr['state'],
            'merged_at': pr['mergedAt'],
            'merge_commit': merge,
            'merge_in_downstream_main': merge_in_main,
            'merge_commit_ancestor_of_runtime_head': merge_in_runtime,
            'source_presence_by_file_equality': source_presence,
            'stats': stats,
            'files': file_rows,
        })

    report = {
        'runtime_checkout': str(RUNTIME),
        'runtime_branch': runtime_branch,
        'runtime_head': runtime_head,
        'downstream_main': downstream_main,
        'runtime_dirty_file_count': len(dirty_paths),
        'runtime_dirty_paths': sorted(dirty_paths),
        'prs': rows,
    }
    (outdir / 'activation-audit.json').write_text(json.dumps(report, indent=2, sort_keys=True))
    # Markdown compact table.
    lines = []
    lines.append('| PR | merged | merge in runtime HEAD | runtime worktree vs downstream main on touched files | dirty overlap | source presence |')
    lines.append('|---:|---|---|---|---|---|')
    for r in rows:
        s = r['stats']
        dirty = ', '.join(s['dirty_or_untracked_touched'][:4]) + ('…' if len(s['dirty_or_untracked_touched']) > 4 else '')
        lines.append(
            f"| #{r['pr']} | {r['state']} {r['merged_at']} | {'yes' if r['merge_commit_ancestor_of_runtime_head'] else 'no'} | "
            f"{s['runtime_worktree_equals_main']}/{s['files_total']} files equal | {dirty or 'none'} | {r['source_presence_by_file_equality']} |"
        )
    (outdir / 'activation-matrix.md').write_text('\n'.join(lines) + '\n')
    print(outdir / 'activation-audit.json')
    print(outdir / 'activation-matrix.md')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
