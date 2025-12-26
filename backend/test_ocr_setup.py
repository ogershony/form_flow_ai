#!/usr/bin/env python3
"""
Quick OCR Setup Verification Script

Tests that all OCR dependencies and enhancements are working properly.
"""
import sys
from pathlib import Path

def test_imports():
    """Test that all required libraries can be imported."""
    print("Testing imports...")
    
    tests = {
        'PyPDF2': lambda: __import__('PyPDF2'),
        'pdfplumber': lambda: __import__('pdfplumber'),
        'pytesseract': lambda: __import__('pytesseract'),
        'pdf2image': lambda: __import__('pdf2image'),
        'PIL (Pillow)': lambda: __import__('PIL'),
        'OpenCV': lambda: __import__('cv2'),
        'NumPy': lambda: __import__('numpy'),
    }
    
    results = {}
    for name, test_func in tests.items():
        try:
            test_func()
            results[name] = True
            print(f"  ✓ {name}")
        except ImportError as e:
            results[name] = False
            print(f"  ✗ {name} - {e}")
    
    return all(results.values())

def test_system_dependencies():
    """Test system-level dependencies."""
    print("\nTesting system dependencies...")
    
    import subprocess
    
    commands = {
        'poppler (pdftoppm)': ['pdftoppm', '-v'],
        'tesseract': ['tesseract', '--version'],
    }
    
    results = {}
    for name, cmd in commands.items():
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0 or 'version' in result.stdout.lower() or 'version' in result.stderr.lower():
                results[name] = True
                print(f"  ✓ {name}")
            else:
                results[name] = False
                print(f"  ✗ {name} - command failed")
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            results[name] = False
            print(f"  ✗ {name} - {e}")
    
    return all(results.values())

def test_document_service():
    """Test DocumentService initialization and features."""
    print("\nTesting DocumentService...")
    
    try:
        from app.services.document_service import DocumentService
        
        # Test initialization
        service = DocumentService(use_cache=True, high_quality=True)
        print(f"  ✓ Service initialized")
        print(f"    - OCR available: {service.ocr_available}")
        print(f"    - OpenCV available: {service.opencv_available}")
        print(f"    - PDF support: {service.pdf_available}")
        print(f"    - Cache enabled: {service.use_cache}")
        print(f"    - High quality: {service.high_quality}")
        
        # Test text extraction
        text = service._extract_text_from_text(b"Hello, World!")
        assert text == "Hello, World!"
        print(f"  ✓ Text extraction works")
        
        # Test validation
        assert service._validate_extracted_text("This is a valid text with enough words")
        assert not service._validate_extracted_text("Short")
        print(f"  ✓ Text validation works")
        
        return True
        
    except Exception as e:
        print(f"  ✗ DocumentService test failed: {e}")
        return False

def test_ocr_configs():
    """Test OCR configuration constants."""
    print("\nTesting OCR configurations...")
    
    try:
        from app.services import document_service
        
        configs = [
            ('FORM_OCR_CONFIG', document_service.FORM_OCR_CONFIG),
            ('FORM_OCR_CONFIG_ALT1', document_service.FORM_OCR_CONFIG_ALT1),
            ('FORM_OCR_CONFIG_ALT2', document_service.FORM_OCR_CONFIG_ALT2),
        ]
        
        for name, config in configs:
            print(f"  ✓ {name}: {config}")
        
        print(f"  ✓ DPI Settings: HIGH={document_service.HIGH_DPI}, "
              f"MEDIUM={document_service.MEDIUM_DPI}, LOW={document_service.LOW_DPI}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Configuration test failed: {e}")
        return False

def print_summary(results):
    """Print test summary."""
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    all_passed = all(results.values())
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status:8} {test_name}")
    
    print("="*70)
    
    if all_passed:
        print("\n✅ All tests passed! OCR enhancements are ready to use.")
        print("\nNext steps:")
        print("  1. Set CLAUDE_API_KEY environment variable")
        print("  2. Try processing a PDF document")
        print("  3. Run: cd tests/evaluation && python run_evaluation.py")
        return 0
    else:
        print("\n❌ Some tests failed. See OCR_SETUP.md for installation instructions.")
        print("\nQuick fix (macOS):")
        print("  brew install poppler tesseract")
        print("  pip install -r requirements.txt")
        print("\nQuick fix (Ubuntu):")
        print("  sudo apt-get install poppler-utils tesseract-ocr")
        print("  pip install -r requirements.txt")
        return 1

def main():
    """Run all tests."""
    print("="*70)
    print("FormFlow AI - OCR Setup Verification")
    print("="*70)
    
    # Add backend to path
    backend_dir = Path(__file__).parent
    sys.path.insert(0, str(backend_dir))
    
    results = {}
    
    # Run tests
    results["Python imports"] = test_imports()
    results["System dependencies"] = test_system_dependencies()
    results["DocumentService"] = test_document_service()
    results["OCR configurations"] = test_ocr_configs()
    
    # Print summary
    return print_summary(results)

if __name__ == "__main__":
    sys.exit(main())
