#!/usr/bin/env python3
"""
Report generation module for VaultPrivacy.

Creates CSV and Markdown reports from ToS;DR analysis results.
"""

import csv
import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime


def generate_csv_report(domains_data: List[Dict[str, Any]], output_file: str = None) -> str:
    """
    Generate a CSV report with domain analysis results.
    
    Args:
        domains_data: List of dictionaries with domain analysis results
        output_file: Optional output filename
        
    Returns:
        Path to the generated CSV file
    """
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"vault_privacy_analysis_{timestamp}.csv"
    
    csv_path = Path(output_file)
    
    print(f"Generating CSV report: {csv_path}")
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['service', 'domain', 'tosdr_grade', 'service_id', 'status']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for data in domains_data:
            writer.writerow({
                'service': data.get('name', data.get('domain', '')),
                'domain': data.get('domain', ''),
                'tosdr_grade': data.get('grade', 'Unknown'),
                'service_id': data.get('service_id', ''),
                'status': 'Found' if data.get('grade') != 'Unknown' else 'Unknown'
            })
    
    print(f"CSV report generated with {len(domains_data)} entries")
    return str(csv_path)


def generate_markdown_report(domains_data: List[Dict[str, Any]], output_file: str = None) -> str:
    """
    Generate a comprehensive Markdown report.
    
    Args:
        domains_data: List of dictionaries with domain analysis results
        output_file: Optional output filename
        
    Returns:
        Path to the generated Markdown file
    """
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"vault_privacy_summary_{timestamp}.md"
    
    md_path = Path(output_file)
    
    print(f"Generating Markdown report: {md_path}")
    
    # Calculate statistics
    total_services = len(domains_data)
    found_services = sum(1 for d in domains_data if d.get('grade') != 'Unknown')
    unknown_services = total_services - found_services
    
    # Grade distribution
    grade_counts = {}
    for data in domains_data:
        grade = data.get('grade', 'Unknown')
        grade_counts[grade] = grade_counts.get(grade, 0) + 1
    
    # Sort by grade (A to E, then Unknown)
    grade_order = ['A', 'B', 'C', 'D', 'E', 'Unknown']
    sorted_grades = sorted(grade_counts.items(), key=lambda x: grade_order.index(x[0]) if x[0] in grade_order else 999)
    
    with open(md_path, 'w', encoding='utf-8') as mdfile:
        # Header
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        mdfile.write(f"""# VaultPrivacy Analysis Report

**Generated:** {timestamp}  
**Total Services Analyzed:** {total_services}  
**Services Found in ToS;DR:** {found_services}  
**Unknown Services:** {unknown_services}  

---

## Overview

This report analyzes the privacy practices of services found in your Bitwarden vault using data from [ToS;DR](https://tosdr.org/) (Terms of Service; Didn't Read). Each service is assigned a privacy grade from A (excellent) to E (very poor).

### Privacy Grade Scale

| Grade | Description |
|-------|-------------|
| A | Excellent privacy practices |
| B | Good privacy practices |
| C | Average privacy practices |
| D | Poor privacy practices |
| E | Very poor privacy practices |
| Unknown | No rating available |

---

## Executive Summary

- **Total Services:** {total_services}
- **Rated Services:** {found_services} ({found_services/total_services*100:.1f}%)
- **Unknown Services:** {unknown_services} ({unknown_services/total_services*100:.1f}%)

### Key Findings

""")
        
        # Add key findings
        if grade_counts.get('E', 0) > 0:
            mdfile.write(f"- **{grade_counts['E']} services** have very poor privacy practices (Grade E)\n")
        if grade_counts.get('D', 0) > 0:
            mdfile.write(f"- **{grade_counts['D']} services** have poor privacy practices (Grade D)\n")
        if grade_counts.get('A', 0) > 0:
            mdfile.write(f"- **{grade_counts['A']} services** have excellent privacy practices (Grade A)\n")
        if grade_counts.get('B', 0) > 0:
            mdfile.write(f"- **{grade_counts['B']} services** have good privacy practices (Grade B)\n")
        
        mdfile.write("\n---\n\n")
        
        # Grade distribution
        mdfile.write("## Grade Distribution\n\n")
        mdfile.write("| Grade | Count | Percentage |\n")
        mdfile.write("|-------|-------|------------|\n")
        
        for grade, count in sorted_grades:
            percentage = (count / total_services) * 100 if total_services > 0 else 0
            mdfile.write(f"| {grade} | {count} | {percentage:.1f}% |\n")
        
        mdfile.write("\n")
        
        # Top risky services (E and D grades)
        risky_services = [d for d in domains_data if d.get('grade') in ['E', 'D']]
        if risky_services:
            mdfile.write("##Services with Poor Privacy Practices\n\n")
            mdfile.write("| Service | Domain | Grade | ToS;DR ID |\n")
            mdfile.write("|---------|--------|-------|----------|\n")
            
            # Sort by grade (E first, then D)
            risky_services.sort(key=lambda x: ['E', 'D'].index(x.get('grade', '')) if x.get('grade') in ['E', 'D'] else 999)
            
            for service in risky_services:
                mdfile.write(f"| {service.get('name', '')} | {service.get('domain', '')} | {service.get('grade', '')} | {service.get('service_id', '')} |\n")
            
            mdfile.write("\n")
        
        # Complete service list
        mdfile.write("## Complete Service Analysis\n\n")
        mdfile.write("| Service | Domain | Grade | ToS;DR ID | Status |\n")
        mdfile.write("|---------|--------|-------|----------|--------|\n")
        
        # Sort by grade, then by service name
        sorted_services = sorted(domains_data, key=lambda x: (['A', 'B', 'C', 'D', 'E', 'Unknown'].index(x.get('grade', 'Unknown')), x.get('name', '')))
        
        for service in sorted_services:
            status = 'Found' if service.get('grade') != 'Unknown' else 'Unknown'
            mdfile.write(f"| {service.get('name', '')} | {service.get('domain', '')} | {service.get('grade', '')} | {service.get('service_id', '')} | {status} |\n")
        
        mdfile.write("\n")
        
        # Footer
        mdfile.write("""---

## About This Report

This report was generated by **VaultPrivacy**, a tool for analyzing privacy risks in your password manager vault.

### Data Sources

- **ToS;DR (Terms of Service; Didn't Read)**: https://tosdr.org/
- **Privacy Ratings**: Based on community-reviewed analysis of terms of service

### Recommendations

1. **Review Poor-Rated Services**: Consider alternatives for services with grades D or E
2. **Investigate Unknown Services**: Research privacy practices for services without ToS;DR data
3. **Regular Audits**: Re-run this analysis periodically as services update their policies
4. **Privacy Settings**: Review and adjust privacy settings for all services

### Disclaimer

This analysis is based on publicly available information and community reviews. Privacy practices can change over time, and this tool should not be the sole basis for privacy decisions.

---

*Generated by VaultPrivacy v1.0.0*
""")
    
    print(f"Markdown report generated with {len(domains_data)} entries")
    return str(md_path)


if __name__ == "__main__":
    # Test with sample data
    sample_data = [
        {"domain": "google.com", "grade": "E", "service_id": 217, "name": "Google"},
        {"domain": "github.com", "grade": "B", "service_id": 297, "name": "GitHub"},
        {"domain": "example.com", "grade": "Unknown", "service_id": None, "name": "example.com"}
    ]
    
    print("Testing report generation...")
    csv_file = generate_csv_report(sample_data, "test_report.csv")
    md_file = generate_markdown_report(sample_data, "test_report.md")
    print(f"Test reports generated: {csv_file}, {md_file}")


