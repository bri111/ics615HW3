import os
import subprocess
import json
from datetime import datetime

def clone_repo(repo_url, repo_dir):
    """
    Clone the repository into the specified directory.
    If it already exists, skip cloning.
    """
    if os.path.exists(repo_dir):
        print(f"[INFO] {repo_dir} already exists. Skipping clone.")
    else:
        print(f"[INFO] Cloning {repo_url} into {repo_dir}")
        try:
            subprocess.run(["git", "clone", repo_url, repo_dir], check=True)
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Failed to clone repository {repo_url}: {e}")

def run_bandit_txt(repo_dir, txt_output_file):
    """
    Run Bandit in TXT mode, similar to your command:
        bandit --exit-zero -r . -f txt -o <txt_output_file>
    This writes the detailed output to a text file.
    Additionally, we run Bandit in JSON mode for extracting a summary.
    Returns the JSON output as a string.
    """
    # Run Bandit in TXT mode to get your familiar full output
    print(f"[INFO] Running Bandit (TXT mode) on {repo_dir}")
    try:
        subprocess.run(
            ["bandit", "--exit-zero", "-r", repo_dir, "-f", "txt", "-o", txt_output_file],
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Bandit TXT run failed: {e}")
    
    # Run Bandit in JSON mode to extract structured data for summary
    print(f"[INFO] Running Bandit (JSON mode) on {repo_dir} for summary")
    process = subprocess.run(
        ["bandit", "-r", repo_dir, "-f", "json"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    if process.returncode != 0:
        print(f"[ERROR] Bandit JSON run encountered an error: {process.stderr}")
    return process.stdout

def analyze_bandit_results_from_json(bandit_json_output):
    """
    Parse the Bandit JSON output and generate a summary dictionary.
    Returns a dictionary with the total count and a severity breakdown.
    """
    summary = {}
    try:
        data = json.loads(bandit_json_output)
        results = data.get("results", [])
        severity_count = {}
        for issue in results:
            severity = issue.get("issue_severity", "UNKNOWN")
            severity_count[severity] = severity_count.get(severity, 0) + 1
        summary['total_issues'] = len(results)
        summary['severity_breakdown'] = severity_count
    except json.JSONDecodeError:
        print("[ERROR] Failed to parse Bandit JSON output.")
        summary['total_issues'] = 0
        summary['severity_breakdown'] = {}
    return summary

def run_trufflehog(repo_dir):
    """
    Run TruffleHog on the given repository.
    This function uses the filesystem scanning mode with JSON output.
    Adjust the command if your version of TruffleHog requires different syntax.
    """
    print(f"[INFO] Running TruffleHog on {repo_dir}")
    # Some versions of trufflehog require additional flags or different command positioning;
    # update this command as needed.
    try:
        process = subprocess.run(
            ["trufflehog", "filesystem", "--path", repo_dir, "--json"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        # If no output is produced and an error message exists, print the error.
        if process.returncode != 0 and not process.stdout:
            print(f"[ERROR] TruffleHog encountered an error: {process.stderr}")
        return process.stdout
    except Exception as e:
        print(f"[ERROR] Exception during TruffleHog run: {e}")
        return ""

def analyze_trufflehog_results(trufflehog_output):
    """
    Parse the TruffleHog JSON output.
    TruffleHog outputs one JSON object per secret found.
    Returns a summary dictionary and a detailed string.
    """
    secrets = []
    details = ""
    for line in trufflehog_output.splitlines():
        try:
            secret = json.loads(line)
            secrets.append(secret)
            # Adjust the keys according to the output produced by your version of TruffleHog.
            reason = secret.get('reason', 'Secret detected')
            path = secret.get('path', 'Unknown path')
            details += f"- {reason} in {path}\n"
        except json.JSONDecodeError:
            # Sometimes non-JSON lines may be present.
            continue
    summary = {"total_secrets": len(secrets)}
    return summary, details

def generate_report(repo_name, bandit_summary, bandit_txt_details, trufflehog_summary, trufflehog_details):
    """
    Generate a comprehensive text report for a repository.
    The report includes:
      - Bandit analysis summary (total issues and severity breakdown)
      - Detailed Bandit output (from your TXT file)
      - TruffleHog analysis summary and details
      - Observations regarding possible false positives/negatives
      - A sample critical vulnerability analysis section
    """
    report = f"Analysis Report for {repo_name}\n"
    report += "=" * 60 + "\n\n"
    
    # Bandit Section
    report += "Bandit Analysis Summary:\n"
    report += f"Total issues detected: {bandit_summary.get('total_issues', 0)}\n"
    report += "Severity Breakdown:\n"
    for sev, count in bandit_summary.get("severity_breakdown", {}).items():
        report += f"  {sev}: {count}\n"
    report += "\nDetailed Bandit Output:\n"
    report += bandit_txt_details + "\n"
    
    # TruffleHog Section
    report += "TruffleHog Analysis Summary:\n"
    report += f"Total secrets detected: {trufflehog_summary.get('total_secrets', 0)}\n"
    report += "\nDetailed TruffleHog Findings:\n"
    report += trufflehog_details + "\n"
    
    # Observations and Sample Critical Vulnerability Analysis
    report += "\nObservations on False Positives/Negatives:\n"
    report += (
        "Note that static analysis tools may report false positives (flagging safe code as problematic) or miss issues (false negatives). "
        "Manual review is recommended.\n"
    )
    
    report += "\nCritical Vulnerability Analysis (Example):\n"
    report += (
        "Example Vulnerability:\n"
        "File: example.py at line 42\n"
        "Issue: Usage of 'eval' can lead to remote code execution if unsanitized input is provided.\n"
        "Explanation: Directly using 'eval' on user input may allow an attacker to execute arbitrary code. "
        "Exploitation of this vulnerability could lead to system compromise.\n"
        "Fix: Replace 'eval' with safer alternatives by thoroughly validating and sanitizing inputs or using specialized libraries.\n"
    )
    
    return report

def write_report_to_file(filename, report_content):
    """
    Write the report to a file. This uses 'w' mode, so it will overwrite existing files.
    """
    with open(filename, 'w') as f:
        f.write(report_content)
    print(f"[INFO] Report written to {filename}")

def main():
    # Dictionary of repositories (update URLs as provided)
    repos = {
        "project1": "https://github.com/docling-project/docling.git",
        "project2": "https://github.com/openvla/openvla.git",
        "project3": "https://github.com/pipilurj/G-LLaVA.git",
        "project4": "https://github.com/facebookresearch/vggt.git",
        "project5": "https://github.com/Docta-ai/docta.git",
        "project6": "https://github.com/vllm-project/vllm.git",
    }
    
    # Base directories for cloning and storing reports
    base_clone_dir = "cloned_repos"
    output_dir = "analysis_reports"
    
    if not os.path.exists(base_clone_dir):
        os.makedirs(base_clone_dir)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Optionally add a timestamp to report filenames so each run is unique.
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Process each repository
    for repo_name, repo_url in repos.items():
        print("\n" + "="*80)
        print(f"[INFO] Starting analysis for {repo_name}")
        
        repo_dir = os.path.join(base_clone_dir, repo_name)
        clone_repo(repo_url, repo_dir)
        
        # Define a Bandit TXT output file (inside repo_dir)
        bandit_txt_file = os.path.join(repo_dir, f"bandit_output_{repo_name}.txt")
        # Run Bandit (TXT mode + JSON mode for summary)
        bandit_json_output = run_bandit_txt(repo_dir, bandit_txt_file)
        bandit_summary = analyze_bandit_results_from_json(bandit_json_output)
        
        # Read the Bandit TXT output details
        try:
            with open(bandit_txt_file, 'r') as f:
                bandit_txt_details = f.read()
        except Exception as e:
            bandit_txt_details = f"Error reading Bandit TXT output: {e}"
        
        # Run TruffleHog and analyze its output
        trufflehog_output = run_trufflehog(repo_dir)
        trufflehog_summary, trufflehog_details = analyze_trufflehog_results(trufflehog_output)
        
        # Generate the full analysis report
        report = generate_report(repo_name, bandit_summary, bandit_txt_details, trufflehog_summary, trufflehog_details)
        
        # Write report to a file (with timestamp to avoid overwriting unless desired)
        output_filename = os.path.join(output_dir, f"{repo_name}_analysis_{timestamp}.txt")
        write_report_to_file(output_filename, report)
        
        print(f"[INFO] Completed analysis for {repo_name}")

if __name__ == "__main__":
    main()
