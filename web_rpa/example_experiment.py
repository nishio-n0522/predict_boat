"""
Example Web RPA Experiment Script

This script demonstrates the STRUCTURE of using the RPA framework.
It does NOT contain actual implementation for safety and compliance reasons.

BEFORE USING THIS CODE:
======================
1. Read and understand Boatrace website terms of service
2. Ensure you have proper authorization for automation
3. Verify compliance with all applicable laws
4. Use ONLY in authorized test environments
5. Implement actual logic carefully and responsibly

This is for EDUCATIONAL PURPOSES ONLY.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from web_rpa.boatrace_rpa_experiment import create_experiment_instance
from web_rpa.config import RPAConfig


def experiment_1_browser_initialization():
    """
    Experiment 1: Browser initialization and basic navigation

    This demonstrates how to:
    - Initialize the RPA framework
    - Navigate to a website
    - Take screenshots
    - Cleanup resources
    """
    print("\n" + "=" * 80)
    print("EXPERIMENT 1: Browser Initialization")
    print("=" * 80)

    # Create RPA instance
    rpa = create_experiment_instance(headless=False)

    try:
        # Start browser
        print("Starting browser...")
        rpa.start()

        # Navigate to Boatrace homepage
        print("Navigating to Boatrace homepage...")
        rpa.navigate_to("https://www.boatrace.jp")

        # Take screenshot
        print("Taking screenshot...")
        screenshot_path = rpa.take_screenshot("homepage")
        print(f"Screenshot saved to: {screenshot_path}")

        # Wait for user to observe
        input("\nPress Enter to continue...")

    finally:
        # Always cleanup
        print("Cleaning up...")
        rpa.stop()

    print("Experiment 1 complete!\n")


def experiment_2_element_inspection():
    """
    Experiment 2: Inspecting page elements

    This demonstrates how to:
    - Find elements on a page
    - Extract information from elements
    - Handle element not found scenarios
    """
    print("\n" + "=" * 80)
    print("EXPERIMENT 2: Element Inspection")
    print("=" * 80)
    print("NOTE: This is a structure demonstration - actual selectors must be updated")

    rpa = create_experiment_instance(headless=False)

    try:
        rpa.start()

        # Navigate to a page
        rpa.navigate_to("https://www.boatrace.jp")

        # Example: Try to find an element (selector must be updated based on actual page)
        # element = rpa.find_element_safe(By.CSS_SELECTOR, ".some-class")
        # if element:
        #     print(f"Element found: {element.text}")
        # else:
        #     print("Element not found")

        print("\nInspection logic not implemented - please add based on actual page structure")

        input("\nPress Enter to continue...")

    finally:
        rpa.stop()

    print("Experiment 2 complete!\n")


def experiment_3_workflow_structure():
    """
    Experiment 3: Understanding workflow structure

    This demonstrates the typical flow of an RPA workflow:
    1. Initialize
    2. Login (if required)
    3. Navigate to target page
    4. Extract information
    5. Perform actions (if authorized)
    6. Cleanup
    """
    print("\n" + "=" * 80)
    print("EXPERIMENT 3: Workflow Structure")
    print("=" * 80)

    rpa = create_experiment_instance(headless=False)

    try:
        # Use context manager for automatic cleanup
        with rpa:
            print("Browser started")

            # Step 1: Navigate to site
            print("\n[Step 1] Navigate to website")
            rpa.navigate_to("https://www.boatrace.jp")

            # Step 2: Login (placeholder - not implemented)
            print("\n[Step 2] Login (placeholder)")
            print("  -> Login logic must be implemented by user")

            # Step 3: Navigate to specific page
            print("\n[Step 3] Navigate to specific page (placeholder)")
            print("  -> Navigation logic must be implemented by user")

            # Step 4: Extract information
            print("\n[Step 4] Extract information (placeholder)")
            print("  -> Extraction logic must be implemented by user")

            # Step 5: Perform actions (if authorized)
            print("\n[Step 5] Perform actions (placeholder)")
            print("  -> NEVER implement without proper authorization")

            # Step 6: Logout
            print("\n[Step 6] Logout (placeholder)")
            print("  -> Logout logic must be implemented by user")

            input("\nPress Enter to finish...")

        # Context manager automatically calls rpa.stop()
        print("\nBrowser closed automatically by context manager")

    except Exception as e:
        print(f"Error occurred: {e}")
        rpa.handle_error(e, "workflow_experiment")

    print("Experiment 3 complete!\n")


def experiment_4_error_handling():
    """
    Experiment 4: Error handling and screenshots

    This demonstrates:
    - Automatic error screenshots
    - Error logging
    - Retry logic
    """
    print("\n" + "=" * 80)
    print("EXPERIMENT 4: Error Handling")
    print("=" * 80)

    # Create config with error screenshots enabled
    config = RPAConfig(
        headless=False,
        screenshot_on_error=True,
        max_retries=3,
        retry_delay=1,
    )

    rpa = create_experiment_instance(headless=False)

    try:
        rpa.start()

        # Example: Try to find a non-existent element
        print("\nAttempting to find non-existent element...")
        from selenium.webdriver.common.by import By
        element = rpa.find_element_safe(By.ID, "non_existent_element_id", timeout=5)

        if not element:
            print("Element not found (as expected)")
            print("Check logs and screenshots directory for details")

        # Example: Demonstrate retry logic
        print("\nDemonstrating retry logic...")

        def failing_function():
            raise Exception("This is a test error")

        result = rpa.execute_with_retry(failing_function)
        print(f"Retry result: {result} (should be None after all retries)")

        input("\nPress Enter to continue...")

    finally:
        rpa.stop()

    print("Experiment 4 complete!\n")


def main():
    """
    Main entry point for experiments

    Run different experiments to understand the RPA framework structure.
    """
    print("\n" + "=" * 80)
    print("Web RPA Experimental Framework - Examples")
    print("=" * 80)
    print("\nIMPORTANT DISCLAIMER:")
    print("- These experiments are for EDUCATIONAL PURPOSES ONLY")
    print("- DO NOT use for unauthorized automation")
    print("- ALWAYS comply with website terms of service")
    print("- Use ONLY in authorized test environments")
    print("=" * 80)

    while True:
        print("\nAvailable Experiments:")
        print("1. Browser Initialization and Navigation")
        print("2. Element Inspection")
        print("3. Workflow Structure")
        print("4. Error Handling")
        print("0. Exit")

        choice = input("\nSelect experiment (0-4): ").strip()

        if choice == "0":
            print("\nExiting experiments. Goodbye!")
            break
        elif choice == "1":
            experiment_1_browser_initialization()
        elif choice == "2":
            experiment_2_element_inspection()
        elif choice == "3":
            experiment_3_workflow_structure()
        elif choice == "4":
            experiment_4_error_handling()
        else:
            print("\nInvalid choice. Please select 0-4.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
