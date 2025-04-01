# YouTube transcript extractor for your LLM
This project will download the transcript for a YouTube video, and make it avaiable to your LLM.  It does this via the MCP protocol.

## Installation

## Use
Use a prompt in the following format:

To download a transcript
> Download the transcript for https://www.youtube.com/watch?v=QGzgsSXdPjo.  Use the MCP server.

To get a summary
> Summarize the transcript

To extract new and interesting information from the transcript.  This prompt often reveals very interesting information:
> highlight new information from the transcript


## Motivation
I build this service to better understand how MCP servers work.  It has also allowed me to explore how to build software with LLMs (in this case Claude).

I've captured the (important) [prompts](DEVELOPMENT_PROMPTS.md) that I used when building the server.
