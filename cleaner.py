#!/usr/bin/env python3
"""
Brave Bookmark Cleaner

A tool to batch remove bookmarks by domain from exported Brave/Chrome bookmark HTML files.

Usage:
    python cleaner.py                           # Use default settings
    python cleaner.py -i input.html -o out.html # Specify files
    python cleaner.py -d example.com spam.org   # Specify domains
    python cleaner.py --help                    # Show help
"""
import re
import os
import argparse

# --- Default Configuration ---
DEFAULT_INPUT = 'bookmarks_original.html'
DEFAULT_OUTPUT = 'bookmarks_clean.html'

# Default domains for testing with example/bookmarks_sample.html:
DEFAULT_DOMAINS = [
    "unwanted-site.com",    # 10 consecutive bookmarks (tests 50% bug)
    "spam-domain.org",      # 3 bookmarks (mixed with keepers)
    "example-remove.com",   # 4 bookmarks (tests http/https/www variants)
]
# --- End Default Configuration ---


def build_prefixes(domains):
    """
    Generate all URL prefix variants for given domains.
    Automatically handles http/https and www/non-www variants.
    """
    prefixes = []
    for domain in domains:
        # Check if domain already has a subdomain (e.g., jp.example.com)
        has_subdomain = domain.count('.') > 1

        for scheme in ["https://", "http://"]:
            prefixes.append(f"{scheme}{domain}")
            # Don't add www for subdomains
            if not has_subdomain:
                prefixes.append(f"{scheme}www.{domain}")

    return prefixes


def clean_bookmarks(input_file, output_file, domains):
    """Main function to clean bookmarks."""
    print("=" * 60)
    print("Brave Bookmark Cleaner")
    print("=" * 60)

    if not domains:
        print("\nError: No domains specified.")
        print("Use -d/--domains to specify domains, or edit DEFAULT_DOMAINS in cleaner.py")
        return False

    print(f"\nInput file:  {input_file}")
    print(f"Output file: {output_file}")

    if not os.path.exists(input_file):
        print(f"\nError: File '{input_file}' not found.")
        print("Please export your bookmarks from Brave and save as the input file.")
        return False

    # Build URL prefixes
    remove_prefixes = build_prefixes(domains)
    print(f"\nDomains to remove ({len(domains)}):")
    for domain in domains:
        print(f"  - {domain}")

    # Read input file (preserve original line endings)
    with open(input_file, 'rb') as f:
        content = f.read().decode('utf-8')

    # Regex pattern for bookmark entries
    #
    # CRITICAL FIX: The naive pattern using \s* and .*? causes ~50% of bookmarks
    # to be skipped because:
    #   - \s* at line end matches newline + next line's indentation
    #   - This causes one match to consume TWO lines, skipping every other bookmark
    #
    # WRONG (skips ~50% of entries):
    #   r'^\s*<DT><A\s+HREF="([^"]*)"[^>]*>.*?</A>\s*\r?\n?'
    #
    # CORRECT (processes all entries):
    #   - [ \t]* : matches only horizontal whitespace (space/tab), NOT newlines
    #   - [^\n\r]* : matches any character EXCEPT newlines (prevents cross-line matching)
    #   - \r?\n? : properly handles both Windows (CRLF) and Unix (LF) line endings
    #
    pattern = re.compile(
        r'^[ \t]*<DT><A\s+HREF="([^"]*)"[^>]*>[^\n\r]*</A>[ \t]*\r?\n?',
        re.MULTILINE | re.IGNORECASE
    )

    # Count total bookmarks
    all_urls = pattern.findall(content)
    total_bookmarks = len(all_urls)
    print(f"\nTotal bookmarks found: {total_bookmarks}")

    # Track deletions
    deleted_count = 0
    domain_counts = {domain: 0 for domain in domains}

    def should_remove(match):
        """Check if bookmark should be removed."""
        nonlocal deleted_count

        full_line = match.group(0)
        href = match.group(1)

        for prefix in remove_prefixes:
            if href.lower().startswith(prefix.lower()):
                deleted_count += 1
                # Track which domain matched
                for domain in domains:
                    if domain in prefix:
                        domain_counts[domain] += 1
                        break
                return ''  # Remove this line

        return full_line  # Keep this line

    # Perform replacement
    print("\nProcessing...")
    cleaned_content = pattern.sub(should_remove, content)

    # Print results
    print("\n" + "=" * 60)
    print("Results")
    print("=" * 60)
    print(f"Original bookmarks: {total_bookmarks}")
    print(f"Removed: {deleted_count}")
    print(f"Remaining: {total_bookmarks - deleted_count}")

    if deleted_count > 0:
        print("\nRemoved by domain:")
        for domain, count in domain_counts.items():
            if count > 0:
                print(f"  - {domain}: {count}")

    # Verify no target domains remain
    print("\nVerification:")
    remaining_urls = pattern.findall(cleaned_content)
    found_remaining = False
    for domain in domains:
        remaining = sum(1 for url in remaining_urls if domain in url.lower())
        if remaining > 0:
            print(f"  Warning: {remaining} '{domain}' bookmarks still remain.")
            found_remaining = True

    if not found_remaining:
        print("  All target domains successfully removed.")

    # Save output file
    output_dir = os.path.dirname(output_file)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_file, 'wb') as f:
        f.write(cleaned_content.encode('utf-8'))

    print(f"\nOutput saved to: {output_file}")
    print("=" * 60)
    return True


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Remove bookmarks by domain from Brave/Chrome bookmark HTML files.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python cleaner.py
      Use default settings (input: bookmarks_original.html)

  python cleaner.py -i exported.html -o cleaned.html
      Specify input and output files

  python cleaner.py -d spam.com ads.net
      Remove bookmarks from specified domains

  python cleaner.py -i my_bookmarks.html -d spam.com -o clean.html
      Full custom configuration
        '''
    )
    
    parser.add_argument(
        '-i', '--input',
        default=DEFAULT_INPUT,
        help=f'Input bookmark HTML file (default: {DEFAULT_INPUT})'
    )
    
    parser.add_argument(
        '-o', '--output',
        default=DEFAULT_OUTPUT,
        help=f'Output bookmark HTML file (default: {DEFAULT_OUTPUT})'
    )
    
    parser.add_argument(
        '-d', '--domains',
        nargs='+',
        default=DEFAULT_DOMAINS,
        help='Domains to remove (without http/https/www)'
    )
    
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    success = clean_bookmarks(args.input, args.output, args.domains)
    exit(0 if success else 1)
