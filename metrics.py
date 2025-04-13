#!/usr/bin/env python3
import re
import sys

def parse_code_scanned_line(line):
    """
    Parse a line that starts with "Code Scanned:".
    Expected example line:
      "Code Scanned: 10 files, 1200 lines"
    Returns a dictionary with keys 'files' and 'lines' if matched,
    or returns the original text.
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
    Expected example line:
      "Run Metrics: 15 tests, 0.45 sec"
    Returns a dictionary with keys 'total_tests' and 'scan_duration_sec'
    if matched, or the original text if not.
    """
    text = line[len("Run Metrics:"):].strip()
    m = re.search(r"(\d+)\s+tests?,\s+([\d\.]+)\s+sec", text, re.IGNORECASE)
    if m:
        return {"total_tests": int(m.group(1)), "scan_duration_sec": float(m.group(2))}
    else:
        return text

def extract_metrics(report_file):
    """
    Read the Bandit TXT report file and extract the metrics.
    Returns:
       code_scanned: Parsed information from the "Code Scanned:" line.
       run_metrics: Parsed information from the "Run Metrics:" line.
    """
    code_scanned = None
    run_metrics = None
    try:
        with open(report_file, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line.startswith("Code Scanned:"):
                    code_scanned = parse_code_scanned_line(line)
                elif line.startswith("Run Metrics:"):
                    run_metrics = parse_run_metrics_line(line)
    except FileNotFoundError:
        print(f"[ERROR] File not found: {report_file}")
    return code_scanned, run_metrics

def main():
    if len(sys.argv) != 2:
        print("Usage: python bandit_metrics.py <bandit_report_file>")
        sys.exit(1)
    
    report_file = sys.argv[1]
    code_scanned, run_metrics = extract_metrics(report_file)
    
    print("----- Bandit Metrics -----")
    if code_scanned:
        print("Code Scanned Metrics:")
        if isinstance(code_scanned, dict):
            print(f"  Files scanned: {code_scanned.get('files')}")
            print(f"  Lines of code: {code_scanned.get('lines')}")
        else:
            print(f"  {code_scanned}")
    else:
        print("No 'Code Scanned' information found.")

    print("")
    if run_metrics:
        print("Run Metrics:")
        if isinstance(run_metrics, dict):
            print(f"  Total tests run: {run_metrics.get('total_tests')}")
            print(f"  Scan duration (sec): {run_metrics.get('scan_duration_sec')}")
        else:
            print(f"  {run_metrics}")
    else:
        print("No 'Run Metrics' information found.")

if __name__ == "__main__":
    main()
