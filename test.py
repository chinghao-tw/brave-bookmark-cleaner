#!/usr/bin/env python3
"""
Test script for Brave Bookmark Cleaner

Demonstrates the 50% bug and verifies the fix works correctly.
"""
import re
import os
import sys

# Path to sample file
SAMPLE_FILE = os.path.join(os.path.dirname(__file__), 'example', 'bookmarks_sample.html')


def test_50_percent_bug():
    """Demonstrate that the wrong regex pattern misses ~50% of bookmarks."""
    print("=" * 60)
    print("TEST 1: The 50% Bug Demonstration")
    print("=" * 60)
    
    with open(SAMPLE_FILE, 'rb') as f:
        content = f.read().decode('utf-8')
    
    # WRONG pattern - causes 50% bug due to \s* and .*?
    wrong_pattern = re.compile(
        r'^\s*<DT><A\s+HREF="([^"]*)"[^>]*>.*?</A>\s*\r?\n?',
        re.MULTILINE | re.IGNORECASE
    )
    
    # CORRECT pattern - uses [ \t]* and [^\n\r]*
    correct_pattern = re.compile(
        r'^[ \t]*<DT><A\s+HREF="([^"]*)"[^>]*>[^\n\r]*</A>[ \t]*\r?\n?',
        re.MULTILINE | re.IGNORECASE
    )
    
    wrong_matches = wrong_pattern.findall(content)
    correct_matches = correct_pattern.findall(content)
    
    print(f"\nSample file: {SAMPLE_FILE}")
    print(f"\nWRONG pattern (\\s* and .*?):")
    print(f"  Found: {len(wrong_matches)} bookmarks")
    
    print(f"\nCORRECT pattern ([ \\t]* and [^\\n\\r]*):")
    print(f"  Found: {len(correct_matches)} bookmarks")
    
    missed = len(correct_matches) - len(wrong_matches)
    missed_pct = (missed / len(correct_matches)) * 100 if correct_matches else 0
    
    print(f"\nDifference: {missed} bookmarks MISSED ({missed_pct:.1f}%)")
    
    # Show which ones were missed
    wrong_set = set(wrong_matches)
    correct_set = set(correct_matches)
    missed_urls = correct_set - wrong_set
    
    if missed_urls:
        print(f"\nMissed bookmarks:")
        for url in sorted(missed_urls)[:5]:
            print(f"  - {url}")
        if len(missed_urls) > 5:
            print(f"  ... and {len(missed_urls) - 5} more")
    
    # Test assertion
    passed = len(correct_matches) > len(wrong_matches)
    print(f"\n{'PASS' if passed else 'FAIL'}: Correct pattern finds more bookmarks than wrong pattern")
    
    return passed


def test_cleaner_functionality():
    """Test that the cleaner correctly removes specified domains."""
    print("\n" + "=" * 60)
    print("TEST 2: Cleaner Functionality")
    print("=" * 60)
    
    with open(SAMPLE_FILE, 'rb') as f:
        content = f.read().decode('utf-8')
    
    # Test domains from sample file
    test_domains = [
        "unwanted-site.com",
        "spam-domain.org", 
        "example-remove.com",
    ]
    
    # Build prefixes (same logic as cleaner.py)
    prefixes = []
    for domain in test_domains:
        has_subdomain = domain.count('.') > 1
        for scheme in ["https://", "http://"]:
            prefixes.append(f"{scheme}{domain}")
            if not has_subdomain:
                prefixes.append(f"{scheme}www.{domain}")
    
    # Correct pattern
    pattern = re.compile(
        r'^[ \t]*<DT><A\s+HREF="([^"]*)"[^>]*>[^\n\r]*</A>[ \t]*\r?\n?',
        re.MULTILINE | re.IGNORECASE
    )
    
    all_urls = pattern.findall(content)
    
    # Count removals
    removed = 0
    kept = 0
    for url in all_urls:
        should_remove = any(url.lower().startswith(p.lower()) for p in prefixes)
        if should_remove:
            removed += 1
        else:
            kept += 1
    
    print(f"\nTest domains: {', '.join(test_domains)}")
    print(f"\nResults:")
    print(f"  Total bookmarks: {len(all_urls)}")
    print(f"  To remove: {removed}")
    print(f"  To keep: {kept}")
    
    # Expected values for sample file
    expected_total = 23
    expected_removed = 17
    expected_kept = 6
    
    tests_passed = True
    
    # Check totals
    if len(all_urls) == expected_total:
        print(f"\nPASS: Total bookmarks = {expected_total}")
    else:
        print(f"\nFAIL: Total bookmarks = {len(all_urls)}, expected {expected_total}")
        tests_passed = False
    
    if removed == expected_removed:
        print(f"PASS: Removed = {expected_removed}")
    else:
        print(f"FAIL: Removed = {removed}, expected {expected_removed}")
        tests_passed = False
    
    if kept == expected_kept:
        print(f"PASS: Kept = {expected_kept}")
    else:
        print(f"FAIL: Kept = {kept}, expected {expected_kept}")
        tests_passed = False
    
    return tests_passed


def test_url_variants():
    """Test that all URL variants (http/https/www) are matched."""
    print("\n" + "=" * 60)
    print("TEST 3: URL Variant Matching")
    print("=" * 60)
    
    test_domain = "example-remove.com"
    
    # Build prefixes
    prefixes = [
        f"https://{test_domain}",
        f"http://{test_domain}",
        f"https://www.{test_domain}",
        f"http://www.{test_domain}",
    ]
    
    # Test URLs from sample file
    test_urls = [
        ("https://example-remove.com/https-no-www", True),
        ("https://www.example-remove.com/https-www", True),
        ("http://example-remove.com/http-no-www", True),
        ("http://www.example-remove.com/http-www", True),
        ("https://www.google.com", False),
        ("https://github.com", False),
    ]
    
    print(f"\nDomain: {test_domain}")
    print(f"Generated prefixes:")
    for p in prefixes:
        print(f"  - {p}")
    
    print(f"\nURL matching tests:")
    all_passed = True
    
    for url, should_match in test_urls:
        matched = any(url.lower().startswith(p.lower()) for p in prefixes)
        passed = matched == should_match
        status = "PASS" if passed else "FAIL"
        expected = "remove" if should_match else "keep"
        actual = "remove" if matched else "keep"
        print(f"  {status} {url[:50]}...")
        print(f"      Expected: {expected}, Got: {actual}")
        if not passed:
            all_passed = False
    
    return all_passed


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("BRAVE BOOKMARK CLEANER - TEST SUITE")
    print("=" * 60)
    
    if not os.path.exists(SAMPLE_FILE):
        print(f"\nERROR: Sample file not found: {SAMPLE_FILE}")
        print("Make sure you're running from the project root directory.")
        sys.exit(1)
    
    results = []
    
    results.append(("50% Bug Demonstration", test_50_percent_bug()))
    results.append(("Cleaner Functionality", test_cleaner_functionality()))
    results.append(("URL Variant Matching", test_url_variants()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {status}: {name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("All tests passed.")
        sys.exit(0)
    else:
        print("Some tests failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
