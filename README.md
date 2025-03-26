

# Prompts
## Intitial MCP server build
Followed instructions from [Building MCP with LLMs](https://modelcontextprotocol.io/tutorials/building-mcp-with-llms).

> ```
> Build an MCP server that: 
> - Downloads a YouTube's video transcript given a YouTube URL. 
> - Exposes the transcript as a resource 
> - Includes prompts to summarize the document and highlight the new or unusual information presented in the video.
> ```

Attacheded `https://modelcontextprotocol.io/llms-full.txt` and `https://github.com/modelcontextprotocol/python-sdk/blob/main/README.md` as recommended.

and followed the installation instructions.

## Fix errors in the URI parameters
The generated code had errors, so I provided feedback to the prompt:

> I get the following error
>  
> ```
> uv run python youtube_transcript_server.py
> Traceback (most recent call last):
>   File "/Users/markmansour/Documents/Code/youtube-transcript-mcp-server/youtube_transcript_server.py", line 270, in <module>
>     @mcp.resource("transcript://{video_id}")
>      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
>   File "/Users/markmansour/Documents/Code/youtube-transcript-mcp-server/.venv/lib/python3.12/site-packages/mcp/server/fastmcp/server.py", line 373, in decorator
>     raise ValueError(
> ValueError: Mismatch between URI parameters {'video_id'} and function parameters {'video_id', 'ctx'}
> ```

