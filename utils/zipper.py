"""Utility for creating course ZIP archive"""
import os
import zipfile
from pathlib import Path


def create_course_zip(base_dir="course", output_name="course.zip"):
    """
    Create a ZIP file of the entire course directory
    
    Args:
        base_dir: Base directory to zip (default: "course")
        output_name: Name of the output ZIP file (default: "course.zip")
    
    Returns:
        bool: True if successful, False otherwise
    """
    
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
        print(f"⚠ Directory {base_dir} not found - creating empty folder.")
    
    zip_path = os.path.join(base_dir, output_name)
    
    print(f"Creating ZIP archive...")
    
    try:
        file_count = 0
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(base_dir):
                for file in files:
                    if file != output_name:  # Don't include the zip itself
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, base_dir)
                        zipf.write(file_path, arcname)
                        file_count += 1
                        print(f"  • Added: {arcname}")
        
        zip_size = os.path.getsize(zip_path)
        zip_size_mb = zip_size / (1024 * 1024)
        
        print(f"\n✓ ZIP created successfully")
        print(f"  • Location: {zip_path}")
        print(f"  • Files: {file_count}")
        print(f"  • Size: {zip_size_mb:.2f} MB\n")
        
        return True
        
    except Exception as e:
        print(f"✗ Error creating ZIP: {e}")
        return False


def extract_course_zip(zip_path, extract_to="extracted_course"):
    """
    Extract a course ZIP file
    
    Args:
        zip_path: Path to the ZIP file
        extract_to: Directory to extract to
    
    Returns:
        bool: True if successful, False otherwise
    """
    
    if not os.path.exists(zip_path):
        print(f"✗ ZIP file not found: {zip_path}")
        return False
    
    try:
        print(f"Extracting {zip_path}...")
        
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            zipf.extractall(extract_to)
            file_count = len(zipf.namelist())
        
        print(f"✓ Extracted {file_count} files to {extract_to}")
        return True
        
    except Exception as e:
        print(f"✗ Error extracting ZIP: {e}")
        return False