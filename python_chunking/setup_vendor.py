"""
Setup script for downloading Tree-sitter parsers.
"""
import subprocess
import shutil
from pathlib import Path


def setup_vendor_parsers():
    """Setup Tree-sitter parsers in vendor directory"""
    vendor_dir = Path(__file__).parent / "vendor"
    vendor_dir.mkdir(exist_ok=True)
    
    # Remove existing parsers
    for parser_dir in ["tree-sitter-python", "tree-sitter-javascript", "tree-sitter-java"]:
        parser_path = vendor_dir / parser_dir
        if parser_path.exists():
            shutil.rmtree(parser_path)
    
    # Clone parsers
    parsers = [
        ("tree-sitter-python", "v0.20.0"),
        ("tree-sitter-javascript", "v0.20.1"), 
        ("tree-sitter-java", "v0.20.0"),
    ]
    
    for repo, tag in parsers:
        print(f"Cloning {repo}...")
        subprocess.run([
            "git", "clone", "--depth", "1", "--branch", tag,
            f"https://github.com/tree-sitter/{repo}",
            str(vendor_dir / repo)
        ], check=True)
    
    print("Tree-sitter parsers setup complete!")


if __name__ == "__main__":
    setup_vendor_parsers()
