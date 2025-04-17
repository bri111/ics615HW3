#!/usr/bin/env python3
import os
import subprocess
import json
import shutil
from datetime import datetime

# Dictionary with your project repository URLs.
repos = {
    "project1": "https://github.com/docling-project/docling.git",
    "project2": "https://github.com/openvla/openvla.git",
    "project3": "https://github.com/pipilurj/G-LLaVA.git",
    "project4": "https://github.com/facebookresearch/vggt.git",
    "project5": "https://github.com/Docta-ai/docta.git",
    "project6": "https://github.com/vllm-project/vllm.git",
}


def locate_trufflehog():
    """
    Determine the correct TruffleHog command available in PATH.
    Prefers trufflehog3, then trufflehog, then falls back to python -m.
    """
    if shutil.which("trufflehog3"):
        return ["trufflehog3"]
    if shutil.which("trufflehog"):
        return ["trufflehog"]
    # Fallback to module invocation
    return [shutil.which("python3") or "python3", "-m", "trufflehog"]


def clone_repo(repo_url, repo_dir):
    """
    Clones the given repository into repo_dir if not already cloned.
    """
    if os.path.exists(repo_dir):
        print(f"[INFO] {repo_dir} already exists. Skipping clone.")
    else:
        print(f"[INFO] Cloning {repo_url} into {repo_dir}")
        subprocess.run(["git", "clone", repo_url, repo_dir], check=True)


def run_trufflehog(repo_dir, truffle_cmd):
    """
    Runs TruffleHog with JSON output on the given repository directory.
    Returns the raw stdout output.
    """
    cmd = truffle_cmd + ["--json", repo_dir]
    print(f"[INFO] Running {' '.join(cmd)}")
    try:
        process = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        if process.returncode not in (0, 1):
            # TruffleHog returns 1 if secrets found; >1 indicates error
            print(f"[WARNING] TruffleHog exited with code {process.returncode}")
            print(process.stderr)
        return process.stdout
    except Exception as e:
        print(f"[ERROR] Could not run TruffleHog: {e}")
        return ""


def parse_trufflehog_output(output):
    """
    Parses the output produced by TruffleHog (one JSON object per line)
    and returns a list of JSON objects.
    """
    secrets = []
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            secret = json.loads(line)
            secrets.append(secret)
        except json.JSONDecodeError:
            # Skip non‑JSON lines
            continue
    return secrets


def generate_report(repo_name, secrets, output_dir, timestamp):
    """
    Generates a text report containing the TruffleHog findings.
    """
    report_lines = [
        f"TruffleHog Analysis Report for {repo_name}",
        "=" * 60,
        f"Total secrets detected: {len(secrets)}",
        ""
    ]

    if secrets:
        for idx, secret in enumerate(secrets, start=1):
            report_lines.append(f"Secret #{idx}:")
            report_lines.append(json.dumps(secret, indent=2))
            report_lines.append("-" * 40)
    else:
        report_lines.append("No secrets found.")

    report_filename = os.path.join(
        output_dir,
        f"{repo_name}_truffle_report_{timestamp}.txt"
    )
    with open(report_filename, "w") as f:
        f.write("\n".join(report_lines))

    print(f"[INFO] Report saved to {report_filename}")


def main():
    base_clone_dir = "cloned_repos"
    output_dir = "truffle_reports"
    os.makedirs(base_clone_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    truffle_cmd = locate_trufflehog()
    print(f"[INFO] Using TruffleHog command: {' '.join(truffle_cmd)}")

    for repo_name, repo_url in repos.items():
        print("\n" + "=" * 80)
        print(f"[INFO] Processing repository: {repo_name}")

        repo_dir = os.path.join(base_clone_dir, repo_name)
        try:
            clone_repo(repo_url, repo_dir)
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Cloning failed for {repo_name}: {e}")
            continue

        output = run_trufflehog(repo_dir, truffle_cmd)
        secrets = parse_trufflehog_output(output)
        generate_report(repo_name, secrets, output_dir, timestamp)

    print("\n[INFO] All repositories processed.")

if __name__ == "__main__":
    main()
