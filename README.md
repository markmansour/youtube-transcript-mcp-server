

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

## Listing transcripts returns an error
Using the MCP developer environment I found that the resrouce "transcripts://list" was not working.  I asked Claude to fix it.


> When I invoke the resource, "transcripts://list" I get the following error from the MCP inspector
>  
> ```
> Error
> MCP error 0: Error reading resource transcripts://list: 'FastMCP' object has no attribute 'current_context
> ```

## Provide feedback that resource calls are failing
Both the calls to resources do not work, including the `transcripts://list` function.  Claude removed the context instance, which is needed.  Claude uses the following prompt to make changes to the code.

> Both resource calls fail with the error:
>  
> ```
> Error retrieving transcript: Context is not available outside of a request
> ```

This required me to tell the server to "Continue", at which point it produced broken code.  It seems like Claude was half way through code editing (deleting lines, character by character) and lost track of where it was up to.  At this point I asked Claude to review the code again:

> `There are still artifacts left in the code.  Review the code and fix the errors`

At which point it used another MCP extension to read the file system (?) and then produced the next version of the server.
