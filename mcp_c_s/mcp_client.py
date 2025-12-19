import os
import json
import pandas as pd
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters


async def query_postgis(sql: str) -> pd.DataFrame:
        
    # Get the project root directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    server_script = os.path.join(current_dir, "mcp_server.py")
    
    server_params = StdioServerParameters(
        command="python",
        args=[server_script],
        env=os.environ,
        cwd=project_root
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
                        print(f"Invalid JSON response:\n{json_str}")
                        return pd.DataFrame()
                else:
                    result_df = pd.DataFrame()
                    
    except BaseException as e:
        print(f"Error: {e}")
        if result_df is not None and not result_df.empty:
            return result_df
        return pd.DataFrame()
    
    return result_df if result_df is not None else pd.DataFrame()

if __name__ == "__main__":
    print("Client started")