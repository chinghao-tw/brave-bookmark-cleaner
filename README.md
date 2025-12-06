# Brave Bookmark Cleaner

A simple Python tool to batch remove bookmarks by domain from exported Brave/Chrome bookmark HTML files.

## Features

- Remove bookmarks matching specified domains
- Automatically handles `http`/`https` and `www`/non-`www` variants
- Preserves original file encoding and format
- Works with both Brave and Chrome exported bookmarks
- Outputs detailed cleanup statistics

## Installation

```bash
git clone https://github.com/yourusername/brave-bookmark-cleaner.git
cd brave-bookmark-cleaner
```

No dependencies required - uses only Python standard library.

## Usage

### Command Line Interface

```bash
# Show help
python cleaner.py --help

# Use default settings
python cleaner.py

# Specify input and output files
python cleaner.py -i exported.html -o cleaned.html

# Specify domains to remove
python cleaner.py -d spam.com ads.net unwanted.org

# Full custom configuration
python cleaner.py -i my_bookmarks.html -o clean.html -d spam.com ads.net
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `-i`, `--input` | Input bookmark HTML file | `bookmarks_original.html` |
| `-o`, `--output` | Output bookmark HTML file | `bookmarks_clean.html` |
| `-d`, `--domains` | Domains to remove (space-separated) | See `DEFAULT_DOMAINS` in script |

### Step-by-Step Guide

#### 1. Export Bookmarks from Brave

1. Open Bookmark Manager (`Ctrl+Shift+O` or `Cmd+Shift+O`)
2. Click `⋮` (three dots menu) → `Export bookmarks`
3. Save as `bookmarks_original.html` in the project folder

#### 2. Configure Domains to Remove

Either use command line:
```bash
python cleaner.py -d example.com unwanted-site.org
```

Or edit `cleaner.py` and modify the `DEFAULT_DOMAINS` list:

```python
DEFAULT_DOMAINS = [
    "example.com",
    "unwanted-site.org",
    "subdomain.example.net",
]
```

The tool automatically generates URL variants:
- `https://example.com`
- `http://example.com`
- `https://www.example.com`
- `http://www.example.com`

### 3. Run the Cleaner

```bash
python cleaner.py
```

### 4. Import Cleaned Bookmarks

#### Step 1: Backup Current Bookmarks
Export your current bookmarks as a backup before making changes.

#### Step 2: Delete Existing Bookmarks
In Bookmark Manager, clear each system folder:
1. Enter `Bookmarks` → `Ctrl+A` → `Delete`
2. Enter `Other Bookmarks` → `Ctrl+A` → `Delete`
3. Enter `Mobile Bookmarks` → `Ctrl+A` → `Delete`

#### Step 3: Import Cleaned File
1. In Bookmark Manager, click `⋮` → `Import bookmarks`
2. Select `bookmarks_clean.html`

#### Step 4: Move Bookmarks to Desired Location

>  **Important:** Brave/Chrome always imports bookmarks into the `Bookmarks` folder. You cannot specify a different location during import.

If your bookmarks were originally in `Mobile Bookmarks` or `Other Bookmarks`:
1. Create a folder in your desired location (or use existing)
2. Select all imported bookmarks and drag them to the target folder

### 5. Sync (if enabled)

If Brave Sync is enabled:
- Changes on PC will automatically sync to cloud
- Other devices (phone, tablet) will receive the update

## Testing

Run the test suite to verify everything works correctly:

```bash
python test.py
```

This runs three tests:
1. **50% Bug Demonstration** - Proves the wrong regex misses ~50% of bookmarks
2. **Cleaner Functionality** - Verifies correct removal counts
3. **URL Variant Matching** - Confirms all http/https/www variants are handled

Expected output:
```
============================================================
TEST SUMMARY
============================================================
   PASS: 50% Bug Demonstration
   PASS: Cleaner Functionality
   PASS: URL Variant Matching

============================================================
All tests passed! 
```

## Example

A sample bookmark file is provided in `example/bookmarks_sample.html` with Windows-style CRLF line endings to demonstrate the 50% bug.

The sample file contains 23 bookmarks:
- **6 to keep:** Google, GitHub, Wikipedia, Stack Overflow, MDN, Hacker News
- **17 to remove:** from domains `unwanted-site.com`, `spam-domain.org`, `example-remove.com`

### Quick Test

```bash
# 1. Copy sample file
cp example/bookmarks_sample.html bookmarks_original.html

# 2. Run cleaner (domains are pre-configured for testing)
python cleaner.py

# 3. Verify results
grep -c "<DT><A" bookmarks_original.html   # Should show: 23
grep -c "<DT><A" bookmarks_clean.html      # Should show: 6
```

### Test Domains (Pre-configured)

The sample file is designed to test with these domains:

```python
REMOVE_DOMAINS = [
    "unwanted-site.com",    # 10 consecutive bookmarks (tests 50% bug)
    "spam-domain.org",      # 3 bookmarks (mixed with keepers)
    "example-remove.com",   # 4 bookmarks (tests http/https/www variants)
]
```

### Expected Output

```
==================================================
Brave Bookmark Cleaner
==================================================

Total bookmarks found: 23

==================================================
Results
==================================================
Original bookmarks: 23
Removed: 17
Remaining: 6

Removed by domain:
  - unwanted-site.com: 10
  - spam-domain.org: 3
  - example-remove.com: 4

Verification:
  All target domains successfully removed.
==================================================
```

### Verify the 50% Bug Fix

To see why the correct regex matters, test both patterns:

```python
import re

with open('example/bookmarks_sample.html', 'rb') as f:
    content = f.read().decode('utf-8')

# WRONG pattern - misses ~50% of bookmarks
wrong = re.compile(r'^\s*<DT><A\s+HREF="([^"]*)"[^>]*>.*?</A>\s*\r?\n?', re.MULTILINE)

# CORRECT pattern - finds all bookmarks  
correct = re.compile(r'^[ \t]*<DT><A\s+HREF="([^"]*)"[^>]*>[^\n\r]*</A>[ \t]*\r?\n?', re.MULTILINE)

print(f"WRONG:   {len(wrong.findall(content))} bookmarks")    # Shows: 12
print(f"CORRECT: {len(correct.findall(content))} bookmarks")  # Shows: 23
```

## File Structure

```
brave-bookmark-cleaner/
├── README.md
├── LICENSE
├── cleaner.py                      # Main script with CLI support
├── test.py                         # Test suite
├── example/
│   └── bookmarks_sample.html       # Sample file for testing (CRLF format)
└── .gitignore
```

## Technical Details

### The 50% Bug - Why Naive Regex Fails

A common mistake when parsing bookmark HTML is using `\s*` and `.*?` in the regex pattern:

```python
# WRONG - This skips ~50% of bookmarks!
r'^\s*<DT><A\s+HREF="([^"]*)"[^>]*>.*?</A>\s*\r?\n?'
```

**Why it fails:**

The `\s*` at the end of the pattern matches not just spaces, but also **newlines and the next line's indentation**. This causes a single match to consume TWO lines:

```
Line N:   <DT><A HREF="...">Title</A>\r\n
Line N+1:     <DT><A HREF="...">Title2</A>\r\n
              ^^^^
              \s* matches this indentation too!
```

Result: Line N+1 is consumed as part of Line N's match and never processed independently.

### The Fix

```python
# CORRECT - Processes all bookmarks
r'^[ \t]*<DT><A\s+HREF="([^"]*)"[^>]*>[^\n\r]*</A>[ \t]*\r?\n?'
```

Key changes:
| Original | Fixed | Reason |
|----------|-------|--------|
| `\s*` | `[ \t]*` | Match only horizontal whitespace (space/tab), NOT newlines |
| `.*?` | `[^\n\r]*` | Match any character EXCEPT newlines (prevents cross-line matching) |

This ensures each bookmark line is matched independently.

### Bookmark HTML Format

Brave/Chrome uses the Netscape Bookmark File format:

```html
<!DOCTYPE NETSCAPE-Bookmark-file-1>
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks</H1>
<DL><p>
    <DT><H3>Folder Name</H3>
    <DL><p>
        <DT><A HREF="https://example.com">Page Title</A>
    </DL><p>
</DL><p>
```

## Requirements

- Python 3.6+
- No external dependencies

## License

MIT License - see [LICENSE](LICENSE) file.
