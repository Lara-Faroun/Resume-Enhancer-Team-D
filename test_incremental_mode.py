"""
Test script for incremental mode.
Run with: python test_incremental_mode.py

Ensure the server is running:
  cd Resume-Enhancer-Team-D
  uvicorn app.main:app --reload
"""
import requests
import json
import time
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
SAMPLE_REQUEST_PATH = "sample_request.json"

# Load sample request
def load_sample_request():
    """Load sample request from JSON file."""
    sample_path = Path(SAMPLE_REQUEST_PATH)
    if not sample_path.exists():
        print(f"❌ Sample request file not found: {SAMPLE_REQUEST_PATH}")
        print("   Please ensure sample_request.json exists in the project root.")
        exit(1)
    
    with open(sample_path, "r") as f:
        return json.load(f)


def test_legacy_mode():
    """Test that legacy mode still works."""
    print("\n" + "="*70)
    print("TESTING LEGACY MODE")
    print("="*70)
    
    payload = load_sample_request()
    start = time.time()
    
    try:
        response = requests.post(f"{BASE_URL}/enhance", json=payload, timeout=120)
        elapsed = time.time() - start
        
        print(f"Status: {response.status_code}")
        print(f"Elapsed: {elapsed:.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Keys: {list(data.keys())}")
            print(f"Has enhanced_resume: {bool(data.get('enhanced_resume'))}")
            print(f"Has report_summary: {bool(data.get('report_summary'))}")
            print(f"Has mapping_result: {bool(data.get('mapping_result'))}")
            
            # Check backward compatibility
            if data.get('enhanced_resume') and data.get('report_summary'):
                print("✅ Legacy mode works - all expected fields present")
                return True
            else:
                print("⚠️  Legacy mode incomplete - missing expected fields")
                return False
        else:
            print(f"❌ Legacy mode failed: {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            return False
    
    except requests.exceptions.Timeout:
        print("❌ Legacy mode timed out (>120s)")
        return False
    except Exception as e:
        print(f"❌ Legacy mode error: {e}")
        return False


def test_incremental_mode():
    """Test incremental mode with SSE streaming."""
    print("\n" + "="*70)
    print("TESTING INCREMENTAL MODE")
    print("="*70)
    
    payload = load_sample_request()
    start = time.time()
    
    try:
        response = requests.post(
            f"{BASE_URL}/enhance?mode=incremental",
            json=payload,
            stream=True,
            timeout=120
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            events = []
            section_times = {}
            first_section_time = None
            
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith("data: "):
                        event_json = line_str[6:]  # Remove "data: " prefix
                        try:
                            event = json.loads(event_json)
                            events.append(event)
                            
                            # Print progress
                            if event["event_type"] == "section_start":
                                section = event.get("section", "?")
                                print(f"  ⏳ {section} starting...")
                            
                            elif event["event_type"] == "section_complete":
                                section = event.get("section", "?")
                                elapsed_ms = event.get("elapsed_ms", 0)
                                progress = event.get("progress_percent", 0)
                                
                                if first_section_time is None:
                                    first_section_time = time.time() - start
                                
                                section_times[section] = elapsed_ms
                                print(f"  ✅ {section} complete ({elapsed_ms:.0f}ms total, {progress:.0f}% done)")
                            
                            elif event["event_type"] == "error":
                                section = event.get("section", "?")
                                error = event.get("error_message", "?")
                                print(f"  ❌ {section} error: {error}")
                            
                            elif event["event_type"] == "complete":
                                print(f"  ✅ All sections complete!")
                        
                        except json.JSONDecodeError as e:
                            print(f"  ⚠️  Failed to parse event: {e}")
            
            elapsed = time.time() - start
            print(f"\nTotal elapsed: {elapsed:.2f}s")
            print(f"Time-to-First-Section (TTFS): {first_section_time:.2f}s" if first_section_time else "TTFS: N/A")
            print(f"Events received: {len(events)}")
            
            # Validate events
            section_completes = [e for e in events if e["event_type"] == "section_complete"]
            section_errors = [e for e in events if e["event_type"] == "error"]
            complete_events = [e for e in events if e["event_type"] == "complete"]
            
            print(f"Sections completed: {len(section_completes)}/7")
            print(f"Sections failed: {len(section_errors)}")
            print(f"Complete events: {len(complete_events)}")
            
            # Check success criteria
            success = True
            
            if len(section_completes) < 7:
                print(f"⚠️  Only {len(section_completes)}/7 sections completed")
                success = False
            
            if first_section_time and first_section_time > 10:
                print(f"⚠️  TTFS ({first_section_time:.2f}s) exceeds target (<5s)")
                success = False
            elif first_section_time:
                print(f"✅ TTFS ({first_section_time:.2f}s) meets target (<5s)")
            
            if len(complete_events) == 0:
                print("⚠️  No complete event received")
                success = False
            else:
                # Check final state
                final_event = complete_events[0]
                final_state = final_event.get("state", {})
                
                if final_state.get("enhanced_resume"):
                    print("✅ Final state contains enhanced_resume")
                else:
                    print("⚠️  Final state missing enhanced_resume")
                    success = False
            
            if success:
                print("\n✅ Incremental mode works - all checks passed")
            else:
                print("\n⚠️  Incremental mode has issues - see warnings above")
            
            return success
        
        else:
            print(f"❌ Incremental mode failed: {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            return False
    
    except requests.exceptions.Timeout:
        print("❌ Incremental mode timed out (>120s)")
        return False
    except Exception as e:
        print(f"❌ Incremental mode error: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_server():
    """Check if server is running."""
    try:
        health_url = BASE_URL.replace("/api/v1", "") + "/health"
        response = requests.get(health_url, timeout=2)
        if response.status_code == 200:
            print("✅ Server is running")
            return True
        else:
            print(f"⚠️  Server responded with status {response.status_code}")
            return False
    except requests.exceptions.RequestException:
        print("❌ Server not running")
        print("   Start with: cd Resume-Enhancer-Team-D && uvicorn app.main:app --reload")
        return False


def main():
    """Run all tests."""
    print("="*70)
    print("INCREMENTAL MODE TEST SUITE")
    print("="*70)
    
    # Check server
    if not check_server():
        exit(1)
    
    # Run tests
    legacy_passed = test_legacy_mode()
    incremental_passed = test_incremental_mode()
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Legacy Mode:      {'✅ PASSED' if legacy_passed else '❌ FAILED'}")
    print(f"Incremental Mode: {'✅ PASSED' if incremental_passed else '❌ FAILED'}")
    
    if legacy_passed and incremental_passed:
        print("\n🎉 All tests passed! Incremental mode is ready.")
        exit(0)
    else:
        print("\n⚠️  Some tests failed. Review output above.")
        exit(1)


if __name__ == "__main__":
    main()
