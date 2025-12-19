import os
import json
import pandas as pd
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

def mcp_result_to_df(result) -> pd.DataFrame:
    rows = []
    for item in result.content:
        if getattr(item, "type", None) == "text":
            rows.append(json.loads(item.text))
    return pd.DataFrame(rows)

async def query_postgis(sql: str) -> pd.DataFrame:
    import os
    
    server_params = StdioServerParameters(
        command="python",
        args=["mcp_c_s/mcp_server.py"],
        env=os.environ
    )
    
    result_df = None
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                result = await session.call_tool(
                    "run_postgis_query", 
                    arguments={"sql": sql}
                )
                
                if result.content and len(result.content) > 0:
                    json_str = result.content[0].text
                    
                    # Check if it's an error message
                    if json_str.startswith("Error"):
                        print(f" Database error:\n{json_str}")
                        return pd.DataFrame()
                    
                    try:
                        data = json.loads(json_str)
                        result_df = pd.DataFrame(data)
                    except json.JSONDecodeError:
                        print(f" Invalid JSON response:\n{json_str}")
                        return pd.DataFrame()
                else:
                    result_df = pd.DataFrame()
                    
    except BaseException as e:
        # If we got data before cleanup errors, return it
        if result_df is not None and not result_df.empty:
            return result_df
        
        # Otherwise it's a real error
        if "Unknown tool" in str(e):
            print(f"Tool not found. Available tools on server:")
            # Could list tools here
        return pd.DataFrame()
    
    return result_df if result_df is not None else pd.DataFrame()