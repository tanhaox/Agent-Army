#!/usr/bin/env python3
"""
Add pytest import to test files that use @pytest.mark.asyncio but don't import pytest
"""

import re
from pathlib import Path


def add_pytest_import(file_path: Path) -> bool:
    """Add pytest import to file if needed

    Args:
        file_path: Path to the test file

    Returns:
        True if file was modified, False otherwise
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')

    # Check if pytest is already imported
    has_pytest_import = any('import pytest' in line for line in lines)

    # Check if file uses @pytest.mark.asyncio
    uses_pytest_decorator = any('@pytest.mark.asyncio' in line for line in lines)

    if has_pytest_import or not uses_pytest_decorator:
        return False

    # Find the best place to insert the import
    insert_index = 0

    # Skip docstring at the beginning
    if lines and lines[0].strip().startswith('"""'):
        for i in range(1, len(lines)):
            if '"""' in lines[i]:
                insert_index = i + 1
                break
    else:
        # Find the first import statement
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                insert_index = i
                break

    # Insert pytest import
    lines.insert(insert_index, 'import pytest')

    # Write back to file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    return True


def main():
    """Main function"""
    test_dir = Path('tests')

    if not test_dir.exists():
        print("Error: tests/ directory not found")
        return

    # Find all test files
    test_files = sorted(test_dir.glob('test_*.py'))

    print(f"Found {len(test_files)} test files")
    print("=" * 60)

    fixed_count = 0
    for test_file in test_files:
        if add_pytest_import(test_file):
            print(f"[OK] Added pytest import: {test_file.name}")
            fixed_count += 1

    print("=" * 60)
    print(f"Total files modified: {fixed_count}/{len(test_files)}")


if __name__ == '__main__':
    main()
