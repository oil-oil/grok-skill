#!/usr/bin/env python3
"""Run Grok headlessly and emit a compact Markdown report."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prompt")
    parser.add_argument("--workspace", default=os.getcwd())
    parser.add_argument("--file", action="append", default=[])
    parser.add_argument("--session")
    parser.add_argument("--model")
    parser.add_argument("--reasoning")
    parser.add_argument("--read-only", action="store_true")
    parser.add_argument(
        "--check",
        action="store_true",
        help="ask Grok to run relevant checks; this is not forwarded to the Grok CLI",
    )
    parser.add_argument("--no-subagents", action="store_true")
    return parser.parse_args()


def newest_session(workspace: Path, started: float) -> str | None:
    root = Path.home() / ".grok" / "sessions"
    matches: list[tuple[float, str]] = []
    if not root.exists():
        return None
    for summary_path in root.glob("*/*/summary.json"):
        try:
            if summary_path.stat().st_mtime < started - 10:
                continue
            data = json.loads(summary_path.read_text(encoding="utf-8"))
            if data.get("session_kind") == "subagent":
                continue
            cwd = Path(data.get("info", {}).get("cwd", "")).resolve()
            if cwd == workspace:
                matches.append((summary_path.stat().st_mtime, data["info"]["id"]))
        except (OSError, ValueError, KeyError):
            continue
    return max(matches)[1] if matches else None


def export_session(session_id: str, cwd: Path) -> str:
    result = subprocess.run(
        ["grok", "export", session_id],
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.stdout if result.returncode == 0 else ""


def last_assistant_message(transcript: str) -> str:
    pieces = transcript.split("## Assistant\n\n")
    if len(pieces) < 2:
        return ""
    tail = pieces[-1]
    for heading in ("\n\n## User", "\n\n## Tools"):
        tail = tail.split(heading, 1)[0]
    return tail.strip()


def main() -> int:
    args = arguments()
    if shutil.which("grok") is None:
        print("error: grok is not installed or not on PATH", file=sys.stderr)
        return 127

    workspace = Path(args.workspace).expanduser().resolve()
    if not workspace.is_dir():
        print(f"error: workspace does not exist: {workspace}", file=sys.stderr)
        return 2

    files: list[Path] = []
    for value in args.file:
        path = Path(value).expanduser()
        if not path.is_absolute():
            path = workspace / path
        path = path.resolve()
        if not path.exists():
            print(f"error: context file does not exist: {path}", file=sys.stderr)
            return 2
        files.append(path)

    prompt = args.prompt.strip()
    if files:
        prompt += "\n\nStarting files (read these directly; discover other relevant files as needed):\n"
        prompt += "\n".join(f"- {path}" for path in files)
    if args.read_only:
        prompt = "READ-ONLY TASK: Do not modify files or external state.\n\n" + prompt
    if args.check:
        prompt += (
            "\n\nBefore finishing, run the relevant project checks or tests that are safe "
            "for this task. Report what you ran and any failures."
        )

    out_root = Path(os.environ.get("GROK_SKILL_OUTPUT_DIR", Path.home() / ".grok" / "skill-runs"))
    out_root.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    trace_path = out_root / f"{stamp}-trace.jsonl"
    stderr_path = out_root / f"{stamp}-stderr.log"

    command = [
        "grok", "-p", prompt,
        "--cwd", str(workspace),
        "--output-format", "streaming-json",
        "--permission-mode", "plan" if args.read_only else "bypassPermissions",
    ]
    if args.session:
        command.extend(["--resume", args.session])
    if args.model:
        command.extend(["--model", args.model])
    if args.reasoning:
        command.extend(["--reasoning-effort", args.reasoning])
    if args.no_subagents:
        command.append("--no-subagents")

    started = time.time()
    process = subprocess.Popen(
        command,
        cwd=workspace,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=1,
        start_new_session=True,
    )

    def copy_stderr() -> None:
        assert process.stderr is not None
        with stderr_path.open("w", encoding="utf-8") as handle:
            for line in process.stderr:
                handle.write(line)
                handle.flush()

    stderr_thread = threading.Thread(target=copy_stderr, daemon=True)
    stderr_thread.start()

    text_chunks: list[str] = []
    session_id: str | None = None
    assert process.stdout is not None
    with trace_path.open("w", encoding="utf-8") as trace:
        for line in process.stdout:
            trace.write(line)
            trace.flush()
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("type") == "text":
                chunk = str(event.get("data", ""))
                text_chunks.append(chunk)
                print(chunk, end="", file=sys.stderr, flush=True)
            if event.get("type") == "end":
                session_id = event.get("sessionId") or session_id
    return_code = process.wait()
    stderr_thread.join(timeout=2)
    if text_chunks:
        print(file=sys.stderr)

    if not session_id:
        session_id = args.session or newest_session(workspace, started)
    transcript = export_session(session_id, workspace) if session_id else ""
    summary = "".join(text_chunks).strip() or last_assistant_message(transcript)
    if not summary:
        summary = "Grok completed without a readable final message." if return_code == 0 else "Grok failed before returning a final message."

    elapsed = time.time() - started
    report_path = out_root / f"{stamp}-{session_id or 'unknown'}.md"
    details = [
        f"- Workspace: `{workspace}`",
        f"- Mode: `{'read-only' if args.read_only else 'write'}`",
        f"- Verification requested: `{'yes' if args.check else 'no'}`",
        f"- Exit code: `{return_code}`",
        f"- Streaming trace: `{trace_path}`",
        f"- Stderr log: `{stderr_path}`",
    ]
    if files:
        details.append("- Starting files: " + ", ".join(f"`{path}`" for path in files))
    report = "# Grok result\n\n## Summary\n\n" + summary + "\n\n## Details\n\n" + "\n".join(details)
    if transcript:
        report += "\n\n## Exported transcript\n\n" + transcript.strip()
    report += f"\n\n---\nelapsed {elapsed:.1f}s"
    report_path.write_text(report + "\n", encoding="utf-8")

    print(f"session_id={session_id or ''}")
    print(f"output_path={report_path}")
    print(f"elapsed={elapsed:.1f}s")
    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
