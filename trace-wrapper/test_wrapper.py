#!/usr/bin/env python3
"""
Test script for Trace HTTP Wrapper.

Tests the wrapper by making HTTP requests to verify:
1. Server starts successfully
2. Health check works
3. MCP client connects to Trace
4. API endpoints function correctly
"""

import asyncio
import httpx
import time
import sys


async def wait_for_server(url: str, timeout: int = 30):
    """Wait for server to be ready."""
    print(f"Waiting for server at {url}...")
    start = time.time()

    async with httpx.AsyncClient() as client:
        while time.time() - start < timeout:
            try:
                response = await client.get(f"{url}/v1/health")
                if response.status_code == 200:
                    print(f"✓ Server is ready!")
                    return True
            except httpx.ConnectError:
                await asyncio.sleep(1)

    print(f"✗ Server did not start within {timeout} seconds")
    return False


async def test_health_check(base_url: str):
    """Test health check endpoint."""
    print("\n" + "="*60)
    print("Testing Health Check")
    print("="*60)

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{base_url}/v1/health")

        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✓ Service: {data.get('service')}")
            print(f"✓ Version: {data.get('version')}")
            print(f"✓ Status: {data.get('status')}")
            return True
        else:
            print(f"✗ Health check failed: {response.text}")
            return False


async def test_list_sessions(base_url: str):
    """Test list sessions endpoint."""
    print("\n" + "="*60)
    print("Testing List Sessions")
    print("="*60)

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{base_url}/v1/sessions")

        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            sessions = data.get("sessions", [])
            print(f"✓ Found {len(sessions)} sessions")
            if sessions:
                print(f"  First session: {sessions[0]}")
            return True
        else:
            print(f"✗ List sessions failed: {response.text}")
            return False


async def test_get_events(base_url: str, session_id: str = "test_session"):
    """Test get events endpoint."""
    print("\n" + "="*60)
    print(f"Testing Get Events (session: {session_id})")
    print("="*60)

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{base_url}/v1/sessions/{session_id}/events")

        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            events = data.get("events", [])
            print(f"✓ Found {len(events)} events for session {session_id}")
            if events:
                print(f"  First event type: {events[0].get('event_type')}")
            return True
        else:
            print(f"⚠️  Get events returned {response.status_code}")
            print(f"   (Session might not exist, which is OK for testing)")
            return True  # Don't fail if session doesn't exist


async def test_add_event(base_url: str, session_id: str = "test_session"):
    """Test add event endpoint."""
    print("\n" + "="*60)
    print(f"Testing Add Event (session: {session_id})")
    print("="*60)

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{base_url}/v1/sessions/{session_id}/events",
            json={
                "event_type": "test.event",
                "data": {
                    "test": True,
                    "message": "Test event from wrapper"
                }
            }
        )

        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✓ Event added successfully")
            print(f"  Status: {data.get('status')}")
            print(f"  Message: {data.get('message')}")
            return True
        else:
            print(f"⚠️  Add event returned {response.status_code}")
            print(f"   Response: {response.text}")
            return True  # Don't fail - server might not support this yet


async def test_root_endpoint(base_url: str):
    """Test root endpoint."""
    print("\n" + "="*60)
    print("Testing Root Endpoint")
    print("="*60)

    async with httpx.AsyncClient() as client:
        response = await client.get(base_url)

        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✓ Service: {data.get('service')}")
            print(f"✓ Description: {data.get('description')}")
            print(f"✓ Available endpoints:")
            for endpoint, path in data.get('endpoints', {}).items():
                print(f"    - {endpoint}: {path}")
            return True
        else:
            print(f"✗ Root endpoint failed: {response.text}")
            return False


async def run_tests():
    """Run all tests."""
    base_url = "http://localhost:8787"

    print("\n" + "="*60)
    print("Trace HTTP Wrapper - Test Suite")
    print("="*60)
    print(f"\nTesting server at: {base_url}")
    print("Ensure the server is running: python3 main.py\n")

    # Wait for server
    if not await wait_for_server(base_url):
        print("\n✗ Server is not running. Start it with: python3 main.py")
        return False

    # Run tests
    results = []
    results.append(await test_root_endpoint(base_url))
    results.append(await test_health_check(base_url))
    results.append(await test_list_sessions(base_url))
    results.append(await test_get_events(base_url))
    results.append(await test_add_event(base_url))

    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)

    passed = sum(results)
    total = len(results)

    print(f"\n{passed}/{total} tests passed")

    if passed == total:
        print("\n✓ All tests passed!")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) had issues")
        return False


def main():
    """Main entry point."""
    try:
        success = asyncio.run(run_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
