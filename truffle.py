#!/usr/bin/env python3
import os
import subprocess
import json
from datetime import datetime

# Dictionary with your project repository URLs.
repos = {
    # "project1": "https://github.com/docling-project/docling.git",
    # "project2": "https://github.com/openvla/openvla.git",
    # "project3": "https://github.com/pipilurj/G-LLaVA.git",
    # "project4": "https://github.com/facebookresearch/vggt.git",
    # "project5": "https://github.com/Docta-ai/docta.git",
    "project6": "https://github.com/vllm-project/vllm.git",
}

def clone_repo(repo_url, repo_dir):
    """
    Clones the given repository into repo_dir if not already cloned.
    """
    if os.path.exists(repo_dir):
        print(f"[INFO] {repo_dir} already exists. Skipping clone.")
    else:
        print(f"[INFO] Cloning {repo_url} into {repo_dir}")
        subprocess.run(["git", "clone", repo_url, repo_dir], check=True)

def run_trufflehog(repo_dir):
    """
    Runs TruffleHog (v2.2) with --json output on the given repository directory.
    Returns the raw stdout output.
    """
    print(f"[INFO] Running TruffleHog on {repo_dir}")
    try:
        process = subprocess.run(
            ["trufflehog", "--json", repo_dir],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

# Optionally, print the return code:
        if process.returncode != 0:
            print(f"[WARNING] TruffleHog exited with code {process.returncode}")
        return process.stdout

    except subprocess.CalledProcessError as e:
        print(f"[ERROR] TruffleHog error for {repo_dir}:\n{e.stderr}")
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
            # Skip lines that aren't valid JSON.
            continue
    return secrets

def generate_report(repo_name, secrets):
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
    
    # Optionally, include observations.
    report_lines.append("\nObservations:")
    report_lines.append("TruffleHog may produce false positives. Manually verify the findings.")
    
    return "\n".join(report_lines)

def main():
    # Directories for cloned repositories and analysis reports.
    base_clone_dir = "cloned_repos"
    output_dir = "truffle_reports"
    
    # Create directories if they don't exist.
    os.makedirs(base_clone_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    
    # Use a timestamp string to create unique report filenames.
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for repo_name, repo_url in repos.items():
        print("\n" + "=" * 80)
        print(f"[INFO] Processing repository: {repo_name}")
        
        # Clone the repository
        repo_dir = os.path.join(base_clone_dir, repo_name)
        try:
            clone_repo(repo_url, repo_dir)
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Cloning failed for {repo_url}: {e}")
            continue
        
        # Run TruffleHog on the repository directory.
        truffle_output = run_trufflehog(repo_dir)
        secrets = parse_trufflehog_output(truffle_output)
        
        # Generate a report for this repository.
        report_text = generate_report(repo_name, secrets)
        report_filename = os.path.join(output_dir, f"{repo_name}_truffle_report_{timestamp}.txt")
        with open(report_filename, "w") as f:
            f.write(report_text)
        
        print(f"[INFO] Completed analysis for {repo_name}.")
        print(f"[INFO] Report saved to {report_filename}")

if __name__ == "__main__":
    main()
