"""
Test suite for Agent Orchestrator.

Tests:
1. Server health check
2. List agents
3. Orchestrate echo task
4. Get contracts
5. Orchestrate multiple tasks
6. Get status
"""

import httpx
import asyncio
import sys
from typing import Optional


BASE_URL = "http://localhost:8888"


async def test_health_check() -> bool:
    """Test 1: Health check."""
    print("\n" + "=" * 60)
    print("[Test 1] Health Check")
    print("=" * 60)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/v1/health")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Status: {response.status_code}")
                print(f"✓ Service: {data.get('service')}")
                print(f"✓ Version: {data.get('version')}")
                return True
            else:
                print(f"✗ Failed with status: {response.status_code}")
                return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


async def test_list_agents() -> bool:
    """Test 2: List agents."""
    print("\n" + "=" * 60)
    print("[Test 2] List Agents")
    print("=" * 60)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/v1/agents")
            
            if response.status_code == 200:
                data = response.json()
                agents = data.get("agents", [])
                total = data.get("total", 0)
                
                print(f"✓ Status: {response.status_code}")
                print(f"✓ Total agents: {total}")
                
                for agent in agents:
                    print(f"\n  Agent: {agent['name']} ({agent['agent_id']})")
                    print(f"    Status: {agent['status']}")
                    print(f"    Capabilities: {[c['name'] for c in agent['capabilities']]}")
                    print(f"    Tasks: {agent['tasks_completed']} completed, {agent['tasks_failed']} failed")
                
                return total > 0
            else:
                print(f"✗ Failed with status: {response.status_code}")
                return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


async def test_orchestrate_echo() -> Optional[str]:
    """Test 3: Orchestrate echo task."""
    print("\n" + "=" * 60)
    print("[Test 3] Orchestrate Echo Task")
    print("=" * 60)
    
    try:
        payload = {
            "session_id": "test_session_001",
            "capability": "echo",
            "parameters": {
                "text": "Hello from orchestrator!"
            },
            "intent": "Test echo capability"
        }
        
        print(f"Sending task: {payload['capability']}")
        print(f"Parameters: {payload['parameters']}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BASE_URL}/v1/orchestrate",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"\n✓ Status: {response.status_code}")
                print(f"✓ Success: {data.get('success')}")
                print(f"✓ Agent ID: {data.get('agent_id')}")
                print(f"✓ Contract ID: {data.get('contract_id')}")
                
                if data.get("data"):
                    print(f"✓ Result: {data['data']}")
                
                if data.get("error"):
                    print(f"✗ Error: {data['error']}")
                    return None
                
                return data.get("contract_id")
            else:
                print(f"✗ Failed with status: {response.status_code}")
                print(f"  Response: {response.text}")
                return None
    except Exception as e:
        print(f"✗ Error: {e}")
        return None


async def test_orchestrate_uppercase() -> Optional[str]:
    """Test 4: Orchestrate uppercase task."""
    print("\n" + "=" * 60)
    print("[Test 4] Orchestrate Uppercase Task")
    print("=" * 60)
    
    try:
        payload = {
            "session_id": "test_session_001",
            "capability": "uppercase",
            "parameters": {
                "text": "convert me to uppercase"
            }
        }
        
        print(f"Sending task: {payload['capability']}")
        print(f"Parameters: {payload['parameters']}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BASE_URL}/v1/orchestrate",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"\n✓ Status: {response.status_code}")
                print(f"✓ Success: {data.get('success')}")
                print(f"✓ Result: {data.get('data', {}).get('result')}")
                
                return data.get("contract_id")
            else:
                print(f"✗ Failed with status: {response.status_code}")
                return None
    except Exception as e:
        print(f"✗ Error: {e}")
        return None


async def test_get_contracts() -> bool:
    """Test 5: Get contracts."""
    print("\n" + "=" * 60)
    print("[Test 5] Get Contracts")
    print("=" * 60)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/v1/contracts",
                params={"session_id": "test_session_001"}
            )
            
            if response.status_code == 200:
                data = response.json()
                contracts = data.get("contracts", [])
                total = data.get("total", 0)
                
                print(f"✓ Status: {response.status_code}")
                print(f"✓ Total contracts: {total}")
                
                # Show contract flow
                for contract in contracts:
                    contract_type = contract["contract_type"]
                    from_agent = contract["from_agent"]
                    to_agent = contract["to_agent"]
                    status = contract["status"]
                    
                    print(f"\n  {contract_type}: {from_agent} → {to_agent}")
                    print(f"    Status: {status}")
                    
                    if contract.get("capability"):
                        print(f"    Capability: {contract['capability']}")
                    
                    if contract.get("result"):
                        print(f"    Result: {contract['result']}")
                
                return total >= 4  # Expect at least 4 contracts (2 REQUEST + 2 RESPONSE)
            else:
                print(f"✗ Failed with status: {response.status_code}")
                return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


async def test_get_status() -> bool:
    """Test 6: Get status."""
    print("\n" + "=" * 60)
    print("[Test 6] Get Status")
    print("=" * 60)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/v1/status")
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"✓ Status: {response.status_code}")
                print(f"✓ Orchestrator: {data.get('orchestrator')}")
                
                # Agents
                agents_info = data.get("agents", {})
                print(f"\n  Agents:")
                print(f"    Total: {agents_info.get('total')}")
                print(f"    By status: {agents_info.get('by_status')}")
                
                # Contracts
                contracts_info = data.get("contracts", {})
                print(f"\n  Contracts:")
                print(f"    Total sessions: {contracts_info.get('total_sessions')}")
                print(f"    Total contracts: {contracts_info.get('total_contracts')}")
                print(f"    By status: {contracts_info.get('by_status')}")
                
                # Integrations
                integrations = data.get("integrations", {})
                print(f"\n  Integrations:")
                print(f"    MemAgent: {'✓' if integrations.get('memagent') else '✗'}")
                print(f"    Trace: {'✓' if integrations.get('trace') else '✗'}")
                
                return True
            else:
                print(f"✗ Failed with status: {response.status_code}")
                return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


async def check_server_ready() -> bool:
    """Check if server is ready."""
    print("Checking if Agent Orchestrator is running...")
    print(f"Server URL: {BASE_URL}")
    
    for i in range(10):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{BASE_URL}/v1/health", timeout=2.0)
                if response.status_code == 200:
                    print("✓ Server is ready!")
                    return True
        except Exception:
            pass
        
        await asyncio.sleep(1)
    
    print("✗ Server is not responding")
    return False


async def run_tests():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Agent Orchestrator - Test Suite")
    print("=" * 60)
    
    # Check server
    if not await check_server_ready():
        print("\n✗ Server not running. Start it with:")
        print("  python3 main.py")
        return False
    
    # Run tests
    results = []
    
    # Test 1: Health check
    results.append(("Health Check", await test_health_check()))
    
    # Test 2: List agents
    results.append(("List Agents", await test_list_agents()))
    
    # Test 3: Orchestrate echo
    contract_id = await test_orchestrate_echo()
    results.append(("Orchestrate Echo", contract_id is not None))
    
    # Test 4: Orchestrate uppercase
    contract_id = await test_orchestrate_uppercase()
    results.append(("Orchestrate Uppercase", contract_id is not None))
    
    # Test 5: Get contracts
    results.append(("Get Contracts", await test_get_contracts()))
    
    # Test 6: Get status
    results.append(("Get Status", await test_get_status()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed!")
        return True
    else:
        print(f"\n✗ {total - passed} tests failed")
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
        print(f"\n✗ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
