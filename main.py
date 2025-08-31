"""
FastMCP quickstart example.

cd to the `examples/snippets/clients` directory and run:
    uv run server fastmcp_quickstart stdio
"""

from fastmcp import FastMCP

# Create an MCP server
mcp = FastMCP("Demo")


if __name__ == "__main__":
    mcp.run(transport="sse", host="127.0.0.1", port=8000)
