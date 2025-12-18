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
    server_params = StdioServerParameters(
        command="python",
        args=["mcp_c_s/mcp_server.py"],
        env=os.environ
    )
        
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(
                "run_postgis_query",
                {"sql": sql}
            )
            return mcp_result_to_df(result)
