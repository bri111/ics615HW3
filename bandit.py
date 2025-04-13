#!/usr/bin/env python3
import os
import re
import subprocess
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

# Directories for cloning and storing reports.
BASE_CLONE_DIR = "cloned_repos"
BANDIT_REPORTS_DIR = "bandit_reports_1020"
BANDIT_SUMMARY_DIR = "bandit_summaries_1020"

def ensure_directories():
    """Ensure that all necessary directories exist."""
    for directory in [BASE_CLONE_DIR, BANDIT_REPORTS_DIR, BANDIT_SUMMARY_DIR]:
        os.makedirs(directory, exist_ok=True)

def clone_repo(repo_url, repo_dir):
    """
    Clone the repository into repo_dir if it does not already exist.
    """
    if os.path.exists(repo_dir):
        print(f"[INFO] {repo_dir} already exists. Skipping clone.")
    else:
        print(f"[INFO] Cloning {repo_url} into {repo_dir}")
        subprocess.run(["git", "clone", repo_url, repo_dir], check=True)

def run_bandit_txt(repo_dir, output_file):
    """
    Run Bandit to analyze Python code in the given repository directory,
    writing the output in plain text format to output_file.
    
    Arguments:
      --exit-zero : ensures Bandit returns a 0 exit code even if issues are found.
      -r          : recursively scan the repository.
      -f txt      : output the results as plain text.
      -o <file>   : direct the output to the specified file.
    """
    print(f"[INFO] Running Bandit on {repo_dir}")
    command = ["bandit", "--exit-zero", "-r", repo_dir, "-f", "txt", "-o", output_file]
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Bandit encountered an error on {repo_dir}: {e}")

def parse_code_scanned_line(line):
    """
    Parse a line that starts with "Code Scanned:".
    Expected format (example):
       "Code Scanned: 10 files, 1200 lines"
    Returns a dictionary with keys 'files' and 'lines' if the pattern matches,
    otherwise returns the original text.
    """
    text = line[len("Code Scanned:"):].strip()
    m = re.search(r"(\d+)\s+files?,\s+(\d+)\s+lines?", text, re.IGNORECASE)
    if m:
        return {"files": int(m.group(1)), "lines": int(m.group(2))}
    else:
        return text

def parse_run_metrics_line(line):
    """
    Parse a line that starts with "Run Metrics:".
    Expected format (example):
       "Run Metrics: 15 tests, 0.45 sec"
    Returns a dictionary with keys 'total_tests' and 'scan_duration_sec'
    if the pattern matches, otherwise returns the original text.
    """
    text = line[len("Run Metrics:"):].strip()
    m = re.search(r"(\d+)\s+tests?,\s+([\d\.]+)\s+sec", text, re.IGNORECASE)
    if m:
        return {"total_tests": int(m.group(1)), "scan_duration_sec": float(m.group(2))}
    else:
        return text

def parse_bandit_txt(report_file):
    """
    Parse the Bandit TXT output file to extract:
      - total issues (by counting lines with "Severity:" and "Confidence:")
      - a breakdown by severity and by confidence
      - the "Code Scanned" details (if available)
      - the "Run Metrics" details (if available)
    
    Returns a tuple:
      (total_issues, severity_counts, confidence_counts, code_scanned, run_metrics)
    """
    total_issues = 0
    severity_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    confidence_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    code_scanned = None
    run_metrics = None

    # Regex pattern for issue lines.
    issue_pattern = r"Severity:\s+(\w+)\s+Confidence:\s+(\w+)"
    
    if not os.path.exists(report_file):
        return total_issues, severity_counts, confidence_counts, code_scanned, run_metrics

    with open(report_file, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            # Check for "Code Scanned:" line.
            if line.startswith("Code Scanned:"):
                code_scanned = parse_code_scanned_line(line)
            # Check for "Run Metrics:" line.
            elif line.startswith("Run Metrics:"):
                run_metrics = parse_run_metrics_line(line)
            else:
                # Check for issue lines.
                match = re.search(issue_pattern, line)
                if match:
                    severity = match.group(1).upper()
                    confidence = match.group(2).upper()
                    total_issues += 1
                    if severity in severity_counts:
                        severity_counts[severity] += 1
                    if confidence in confidence_counts:
                        confidence_counts[confidence] += 1
    return total_issues, severity_counts, confidence_counts, code_scanned, run_metrics

def generate_summary_text(repo_name, total_issues, severity_counts, confidence_counts, code_scanned, run_metrics):
    """
    Generate a textual summary of the Bandit analysis for the given repository.
    This summary includes:
      - Total issues detected.
      - Breakdown of issues by severity and by confidence.
      - Parsed "Code Scanned" metrics.
      - Parsed "Run Metrics" (total tests and scan duration).
    """
    lines = []
    lines.append(f"Bandit Summary Report for {repo_name}")
    lines.append("=" * 60)
    lines.append(f"Total issues detected: {total_issues}")
    lines.append("\nSeverity Breakdown:")
    for sev, count in severity_counts.items():
        lines.append(f"  {sev}: {count}")
    lines.append("\nConfidence Breakdown:")
    for conf, count in confidence_counts.items():
        lines.append(f"  {conf}: {count}")

    lines.append("\nCode Scanned:")
    if isinstance(code_scanned, dict):
        lines.append(f"  Files scanned: {code_scanned.get('files', 'N/A')}")
        lines.append(f"  Lines of code: {code_scanned.get('lines', 'N/A')}")
    elif code_scanned:
        lines.append(f"  {code_scanned}")
    else:
        lines.append("  No code scanned metrics available.")

    lines.append("\nRun Metrics:")
    if isinstance(run_metrics, dict):
        lines.append(f"  Total tests run: {run_metrics.get('total_tests', 'N/A')}")
        lines.append(f"  Scan duration (seconds): {run_metrics.get('scan_duration_sec', 'N/A')}")
    elif run_metrics:
        lines.append(f"  {run_metrics}")
    else:
        lines.append("  No run metrics available.")

    lines.append("\nNote: Bandit may produce false positives. Please review each finding manually.")
    return "\n".join(lines)

def main():
    ensure_directories()
    # Create a unique timestamp for report filenames.
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for repo_name, repo_url in repos.items():
        print("\n" + "=" * 80)
        print(f"[INFO] Processing repository: {repo_name}")
        
        # Define the local clone directory.
        repo_dir = os.path.join(BASE_CLONE_DIR, repo_name)
        try:
            clone_repo(repo_url, repo_dir)
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Cloning failed for {repo_name}: {e}")
            continue
        
        # Define the full Bandit report file (TXT output).
        bandit_txt_file = os.path.join(BANDIT_REPORTS_DIR, f"{repo_name}_bandit_report_{timestamp}.txt")
        run_bandit_txt(repo_dir, bandit_txt_file)
        print(f"[INFO] Bandit report saved to {bandit_txt_file}")
        
        # Parse the Bandit TXT report.
        total_issues, severity_counts, confidence_counts, code_scanned, run_metrics = parse_bandit_txt(bandit_txt_file)
        
        # Generate the summary report text.
        summary_text = generate_summary_text(repo_name, total_issues, severity_counts, confidence_counts, code_scanned, run_metrics)
        
        # Save the summary report to a file.
        summary_file = os.path.join(BANDIT_SUMMARY_DIR, f"{repo_name}_bandit_summary_{timestamp}.txt")
        with open(summary_file, "w", encoding="utf-8") as sf:
            sf.write(summary_text)
        print(f"[INFO] Summary for {repo_name} saved to {summary_file}")
    
    print("\n[INFO] Bandit analysis and summary generation complete for all repositories.")

if __name__ == "__main__":
    main()
