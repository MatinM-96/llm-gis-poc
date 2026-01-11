import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_c_s.mcp_client import query_postgis

async def main():
    print("Testing MCP client...\n")
    
    # Simple test
    sql = "SELECT * FROM buildings LIMIT 10"
    print(f"Test 1: {sql}")
    df = await query_postgis(sql)  
    print(f"Result: {df}\n")
    print(f"Shape: {df.shape}\n")
    print(f"Empty: {df.empty}\n")
    
    # Count buildings
    sql2 = "SELECT COUNT(*) as total FROM public.buildings"
    print(f"\nTest 2: {sql2}")
    df2 = await query_postgis(sql2) 
    print(f"Result: {df2}\n")
    print(f"Shape: {df2.shape}\n")
    print(f"Empty: {df2.empty}\n")

if __name__ == "__main__":
    asyncio.run(main())