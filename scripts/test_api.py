#!/usr/bin/env python3
"""
Sample API Test Script

Tests the Gun Registry Adapter API endpoints with sample data.
"""

import base64
import json
import sys
from pathlib import Path
from typing import Optional

import requests
from rich.console import Console
from rich.table import Table
from rich import print as rprint

console = Console()

# API Configuration
API_BASE_URL = "http://localhost:8000"
HEALTH_ENDPOINT = f"{API_BASE_URL}/api/v1/health"
ELIGIBILITY_ENDPOINT = f"{API_BASE_URL}/api/v1/eligibility"


def check_server_health() -> bool:
    """Check if API server is running."""
    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=5)
        if response.status_code == 200:
            console.print("✅ Server is healthy", style="bold green")
            return True
        else:
            console.print(f"❌ Server returned status {response.status_code}", style="bold red")
            return False
    except requests.exceptions.ConnectionError:
        console.print("❌ Cannot connect to server. Is it running?", style="bold red")
        console.print(f"   Run: python adapter/main.py", style="yellow")
        return False
    except Exception as e:
        console.print(f"❌ Error checking server health: {e}", style="bold red")
        return False


def encode_image_to_base64(image_path: str) -> Optional[str]:
    """Encode image file to base64 string."""
    try:
        with open(image_path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode("utf-8")
            return encoded
    except FileNotFoundError:
        console.print(f"❌ Image not found: {image_path}", style="bold red")
        return None
    except Exception as e:
        console.print(f"❌ Error encoding image: {e}", style="bold red")
        return None


def test_eligibility_check(image_path: str, applicant_id: str = "test-12345") -> dict:
    """Test eligibility check endpoint."""
    console.print("\n" + "=" * 80, style="cyan")
    console.print("Testing Eligibility Check API", style="bold cyan")
    console.print("=" * 80 + "\n", style="cyan")

    # Encode image
    console.print(f"📷 Encoding image: {Path(image_path).name}", style="yellow")
    image_base64 = encode_image_to_base64(image_path)
    if not image_base64:
        return {}

    # Build request
    request_data = {
        "applicant_id": applicant_id,
        "id_image_base64": image_base64
    }

    console.print(f"🚀 Sending request to: {ELIGIBILITY_ENDPOINT}", style="yellow")
    console.print(f"   Applicant ID: {applicant_id}", style="dim")
    console.print(f"   Image size: {len(image_base64)} bytes (base64)", style="dim")

    # Make request
    try:
        response = requests.post(
            ELIGIBILITY_ENDPOINT,
            json=request_data,
            headers={"Content-Type": "application/json"},
            timeout=60  # OCR can take time
        )

        console.print(f"\n📡 Response Status: {response.status_code}", style="bold")

        if response.status_code == 200:
            result = response.json()
            display_eligibility_result(result)
            return result
        else:
            console.print(f"❌ Request failed with status {response.status_code}", style="bold red")
            console.print(f"Response: {response.text}", style="red")
            return {}

    except requests.exceptions.Timeout:
        console.print("❌ Request timed out (>60 seconds)", style="bold red")
        return {}
    except Exception as e:
        console.print(f"❌ Error making request: {e}", style="bold red")
        return {}


def display_eligibility_result(result: dict):
    """Display eligibility result in a formatted table."""
    console.print("\n" + "=" * 80, style="green")
    console.print("Eligibility Assessment Result", style="bold green")
    console.print("=" * 80, style="green")

    # Decision
    decision = result.get("decision", "UNKNOWN")
    decision_color = {
        "APPROVED": "bold green",
        "DENIED": "bold red",
        "MANUAL_REVIEW": "bold yellow"
    }.get(decision, "white")

    console.print(f"\n🎯 Decision: {decision}", style=decision_color)
    console.print(f"   Confidence: {result.get('confidence', 0):.2%}", style="bold")
    console.print(f"   Manual Review Required: {result.get('requires_manual_review', False)}", style="bold")

    # Extracted Data
    console.print("\n📋 Extracted Data (Model A - OCR):", style="bold cyan")
    extracted = result.get("extracted_data", {})
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white")

    for field, value in extracted.items():
        table.add_row(field, str(value))

    console.print(table)

    # Risk Assessment
    console.print("\n⚠️  Risk Assessment (Model B):", style="bold yellow")
    risk = result.get("risk_assessment", {})
    console.print(f"   Risk Score: {risk.get('risk_score', 0):.2%}", style="yellow")
    console.print(f"   Confidence: {risk.get('confidence', 0):.2%}", style="yellow")
    console.print(f"   Risk Factors:", style="yellow")
    for factor in risk.get("risk_factors", []):
        console.print(f"      • {factor}", style="dim yellow")

    # Linkage Result
    console.print("\n🔗 Linkage Result (Probabilistic Matching):", style="bold magenta")
    linkage = result.get("linkage_result", {})
    console.print(f"   Matched: {linkage.get('matched', False)}", style="magenta")
    console.print(f"   Confidence: {linkage.get('confidence', 0):.2%}", style="magenta")
    console.print(f"   Requires Review: {linkage.get('requires_review', False)}", style="magenta")

    if linkage.get("field_scores"):
        console.print(f"   Field Scores:", style="magenta")
        for field, score in linkage.get("field_scores", {}).items():
            console.print(f"      {field}: {score:.2%}", style="dim magenta")

    # Decision Rationale
    console.print("\n💭 Decision Rationale:", style="bold blue")
    for reason in result.get("decision_rationale", []):
        console.print(f"   • {reason}", style="blue")

    console.print("\n" + "=" * 80, style="green")


def find_sample_images() -> list:
    """Find sample driver license images."""
    sample_dir = Path("data/raw/synthetic_cards")
    if not sample_dir.exists():
        return []

    images = list(sample_dir.glob("*.png"))
    return sorted(images)[:5]  # Return first 5


def main():
    """Main test runner."""
    console.print("\n" + "=" * 80, style="bold cyan")
    console.print("Gun Registry Adapter - API Test Script", style="bold cyan")
    console.print("=" * 80 + "\n", style="bold cyan")

    # Check server health
    if not check_server_health():
        console.print("\n💡 Tip: Start the server with: python adapter/main.py", style="yellow")
        sys.exit(1)

    # Find sample images
    console.print("\n🔍 Looking for sample images...", style="yellow")
    sample_images = find_sample_images()

    if not sample_images:
        console.print("❌ No sample images found in data/raw/synthetic_cards/", style="bold red")
        console.print("   Please add driver license images to test with.", style="yellow")
        sys.exit(1)

    console.print(f"✅ Found {len(sample_images)} sample images", style="green")

    # Test with first image
    test_image = str(sample_images[0])
    console.print(f"\n📸 Testing with: {Path(test_image).name}", style="bold yellow")

    result = test_eligibility_check(test_image)

    if result:
        console.print("\n✅ Test completed successfully!", style="bold green")
        console.print(f"\n💾 Full response saved to: test_response.json", style="dim")

        # Save full response
        with open("test_response.json", "w") as f:
            json.dump(result, f, indent=2)

    else:
        console.print("\n❌ Test failed", style="bold red")
        sys.exit(1)

    # Offer to test more
    if len(sample_images) > 1:
        console.print(f"\n💡 {len(sample_images) - 1} more sample images available", style="dim")
        console.print(f"   Run again to test different images", style="dim")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\n⚠️  Test interrupted by user", style="yellow")
        sys.exit(0)
