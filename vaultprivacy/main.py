#!/usr/bin/env python3
"""
Main CLI interface for VaultPrivacy.

Usage: python vaultprivacy/main.py <bitwarden_export_file>
"""

import sys
import argparse
from pathlib import Path

from vaultprivacy.parser import extract_domains
from vaultprivacy.domain_normalizer import normalize
from vaultprivacy.api_client import lookup_tosdr
from vaultprivacy.reporting import generate_csv_report, generate_markdown_report


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze privacy risks of services in your Bitwarden vault",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python vaultprivacy/main.py vault_export.json
  python vaultprivacy/main.py vault_export.csv --output-dir ./reports
  python vaultprivacy/main.py vault_export.json --csv-only
        """
    )
    
    parser.add_argument(
        'vault_file',
        help='Path to Bitwarden vault export file (CSV or JSON)'
    )
    
    parser.add_argument(
        '--output-dir', '-o',
        type=Path,
        default=Path.cwd(),
        help='Output directory for reports (default: current directory)'
    )
    
    parser.add_argument(
        '--csv-only',
        action='store_true',
        help='Generate only CSV report'
    )
    
    parser.add_argument(
        '--markdown-only',
        action='store_true',
        help='Generate only Markdown report'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Validate input file
    vault_path = Path(args.vault_file)
    if not vault_path.exists():
        print(f"Error: File not found: {vault_path}")
        sys.exit(1)
    
    if vault_path.suffix.lower() not in ['.csv', '.json']:
        print("Error: File must be CSV or JSON format")
        sys.exit(1)
    
    try:
        print("🔍 VaultPrivacy - Privacy Analysis Tool")
        print("=" * 50)
        
        # Step 1: Extract domains
        print(f"1. Parsing Bitwarden export: {vault_path}")
        domains = extract_domains(str(vault_path))
        print(f"   Found {len(domains)} unique domains")
        
        if not domains:
            print("   No domains found in vault file")
            sys.exit(1)
        
        if args.verbose:
            print(f"   Domains: {', '.join(domains)}")
        
        # Step 2: Normalize domains
        print("2. Normalizing domains...")
        normalized_domains = []
        for domain in domains:
            normalized = normalize(domain)
            if normalized and normalized not in normalized_domains:
                normalized_domains.append(normalized)
        
        print(f"   Normalized to {len(normalized_domains)} unique root domains")
        
        if args.verbose:
            print(f"   Normalized domains: {', '.join(normalized_domains)}")
        
        # Step 3: Fetch ToS;DR ratings
        print("3. Fetching ToS;DR privacy ratings...")
        results = []
        for i, domain in enumerate(normalized_domains, 1):
            print(f"   [{i}/{len(normalized_domains)}] Looking up: {domain}")
            result = lookup_tosdr(domain)
            result['domain'] = domain
            results.append(result)
            
            if args.verbose:
                print(f"      Result: {result}")
        
        # Step 4: Generate reports
        print("4. Generating reports...")
        
        # Ensure output directory exists
        args.output_dir.mkdir(parents=True, exist_ok=True)
        
        reports_generated = []
        
        if not args.markdown_only:
            csv_file = args.output_dir / f"vault_privacy_analysis_{Path(args.vault_file).stem}.csv"
            generate_csv_report(results, str(csv_file))
            reports_generated.append(str(csv_file))
        
        if not args.csv_only:
            md_file = args.output_dir / f"vault_privacy_summary_{Path(args.vault_file).stem}.md"
            generate_markdown_report(results, str(md_file))
            reports_generated.append(str(md_file))
        
        # Summary
        print("\n" + "=" * 50)
        print("✅ ANALYSIS COMPLETE!")
        print("=" * 50)
        
        # Calculate summary stats
        total_services = len(results)
        found_services = sum(1 for r in results if r.get('grade') != 'Unknown')
        unknown_services = total_services - found_services
        
        # Grade distribution
        grade_counts = {}
        for result in results:
            grade = result.get('grade', 'Unknown')
            grade_counts[grade] = grade_counts.get(grade, 0) + 1
        
        print(f"📊 Summary:")
        print(f"   Total services analyzed: {total_services}")
        print(f"   Found in ToS;DR: {found_services}")
        print(f"   Unknown services: {unknown_services}")
        
        if grade_counts:
            print(f"   Grade distribution:")
            for grade in ['A', 'B', 'C', 'D', 'E', 'Unknown']:
                if grade in grade_counts:
                    print(f"     Grade {grade}: {grade_counts[grade]} services")
        
        # Show risky services
        risky_services = [r for r in results if r.get('grade') in ['D', 'E']]
        if risky_services:
            print(f"\n⚠️  Services with poor privacy practices:")
            for service in risky_services:
                print(f"   - {service.get('name', service.get('domain'))} ({service.get('domain')}): Grade {service.get('grade')}")
        
        print(f"\n📁 Reports generated:")
        for report in reports_generated:
            print(f"   - {report}")
        
        print("\n🎯 Next steps:")
        print("   1. Review the generated reports")
        print("   2. Consider alternatives for services with grades D or E")
        print("   3. Research unknown services manually")
        print("   4. Run this analysis periodically")
        
    except KeyboardInterrupt:
        print("\n\n❌ Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
