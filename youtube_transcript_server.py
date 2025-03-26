# youtube_transcript_server.py
"""
MCP server for YouTube video transcripts.
Provides tools to download transcripts and resources to access them.
Includes prompts for summary and information analysis.
"""

from mcp.server.fastmcp import FastMCP, Context
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
import httpx
import re
import os
from typing import Optional
import json
from dataclasses import dataclass
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

# Create MCP server with dependencies
mcp = FastMCP(
    "YouTube Transcript Server",
    dependencies=["youtube_transcript_api", "httpx"]
)

# Create a transcript cache directory
TRANSCRIPT_CACHE_DIR = "transcript_cache"
os.makedirs(TRANSCRIPT_CACHE_DIR, exist_ok=True)

# Data models
@dataclass
class VideoInfo:
    """Store video metadata"""
    video_id: str
    title: str
    channel: str


@dataclass
class TranscriptInfo:
    """Store transcript with metadata"""
    video_id: str
    video_info: Optional[VideoInfo] = None
    text: Optional[str] = None
    

# State management for the server
class TranscriptCache:
    """Cache for transcripts"""
    def __init__(self):
        self.transcripts = {}  # video_id -> TranscriptInfo

    def get(self, video_id: str) -> Optional[TranscriptInfo]:
        """Get transcript from cache"""
        return self.transcripts.get(video_id)

    def add(self, info: TranscriptInfo):
        """Add transcript to cache"""
        self.transcripts[info.video_id] = info
        # Also save to disk for persistence
        self._save_to_disk(info)
    
    def list_all(self):
        """List all cached transcripts"""
        return list(self.transcripts.values())
    
    def _save_to_disk(self, info: TranscriptInfo):
        """Save transcript to disk"""
        if info.text:
            file_path = os.path.join(TRANSCRIPT_CACHE_DIR, f"{info.video_id}.txt")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(info.text)
            
            # Save metadata if available
            if info.video_info:
                meta_path = os.path.join(TRANSCRIPT_CACHE_DIR, f"{info.video_id}_meta.json")
                with open(meta_path, "w", encoding="utf-8") as f:
                    json.dump({
                        "title": info.video_info.title,
                        "channel": info.video_info.channel
                    }, f)
    
    def load_from_disk(self):
        """Load all saved transcripts from disk"""
        if not os.path.exists(TRANSCRIPT_CACHE_DIR):
            return
            
        for filename in os.listdir(TRANSCRIPT_CACHE_DIR):
            if filename.endswith(".txt") and not filename.endswith("_meta.txt"):
                video_id = filename.replace(".txt", "")
                file_path = os.path.join(TRANSCRIPT_CACHE_DIR, filename)
                
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read()
                
                # Try to load metadata
                meta_path = os.path.join(TRANSCRIPT_CACHE_DIR, f"{video_id}_meta.json")
                video_info = None
                if os.path.exists(meta_path):
                    try:
                        with open(meta_path, "r", encoding="utf-8") as f:
                            meta = json.load(f)
                            video_info = VideoInfo(
                                video_id=video_id,
                                title=meta.get("title", "Unknown Title"),
                                channel=meta.get("channel", "Unknown Channel")
                            )
                    except (json.JSONDecodeError, KeyError):
                        pass
                
                info = TranscriptInfo(video_id=video_id, text=text, video_info=video_info)
                self.transcripts[video_id] = info


# Server lifespan and context
@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[TranscriptCache]:
    """Initialize and clean up server resources"""
    # Initialize cache and load existing transcripts
    cache = TranscriptCache()
    cache.load_from_disk()
    
    try:
        yield cache
    finally:
        # Any cleanup would go here
        pass


# Apply lifespan to server
mcp = FastMCP("YouTube Transcript Server", lifespan=app_lifespan)


# Helper functions
def extract_video_id(url: str) -> str:
    """Extract video ID from a YouTube URL"""
    # Handle mobile URLs and shortened URLs
    if "youtu.be" in url:
        path = urlparse(url).path
        return path.strip("/")
    
    # Handle standard URLs
    parsed_url = urlparse(url)
    if parsed_url.netloc in ('youtube.com', 'www.youtube.com', 'm.youtube.com'):
        query_params = parse_qs(parsed_url.query)
        return query_params.get('v', [''])[0]
    
    # If input is already just the ID
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url):
        return url
    
    raise ValueError(f"Could not extract YouTube video ID from {url}")


async def get_video_info(video_id: str) -> VideoInfo:
    """Get video metadata from YouTube's oEmbed API"""
    url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code == 200:
            data = response.json()
            return VideoInfo(
                video_id=video_id,
                title=data.get("title", "Unknown Title"),
                channel=data.get("author_name", "Unknown Channel")
            )
    
    # Return minimal info if API fails
    return VideoInfo(video_id=video_id, title="Unknown", channel="Unknown")


async def get_transcript(video_id: str, ctx: Context) -> str:
    """Download and format transcript from a YouTube video ID"""
    # Check cache first
    cache: TranscriptCache = ctx.request_context.lifespan_context
    cached_info = cache.get(video_id)
    if cached_info and cached_info.text:
        ctx.info(f"Returning cached transcript for video {video_id}")
        return cached_info.text
    
    # Download the transcript if not cached
    ctx.info(f"Downloading transcript for video {video_id}")
    
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        
        # Format the transcript with timestamps
        formatted_transcript = ""
        for entry in transcript_list:
            minutes = int(entry['start'] // 60)
            seconds = int(entry['start'] % 60)
            timestamp = f"[{minutes:02d}:{seconds:02d}]"
            formatted_transcript += f"{timestamp} {entry['text']}\n"
        
        # Get video info
        video_info = await get_video_info(video_id)
        
        # Create header with video information
        header = f"Title: {video_info.title}\n"
        header += f"Channel: {video_info.channel}\n"
        header += f"Video ID: {video_id}\n\n"
        header += "TRANSCRIPT:\n"
        
        full_transcript = header + formatted_transcript
        
        # Save to cache
        info = TranscriptInfo(
            video_id=video_id,
            video_info=video_info,
            text=full_transcript
        )
        cache.add(info)
        
        return full_transcript
        
    except Exception as e:
        error_msg = f"Error retrieving transcript: {str(e)}"
        ctx.error(error_msg)
        return error_msg


# Tools
@mcp.tool()
async def download_transcript(youtube_url: str, ctx: Context) -> str:
    """
    Download a video transcript from YouTube.
    
    Args:
        youtube_url: URL of the YouTube video
    
    Returns:
        The formatted transcript text with timestamps
    """
    try:
        video_id = extract_video_id(youtube_url)
        return await get_transcript(video_id, ctx)
    except ValueError as e:
        ctx.error(f"Invalid YouTube URL: {str(e)}")
        return f"Error: {str(e)}"


@mcp.tool()
async def list_available_transcripts(ctx: Context) -> str:
    """
    List all transcripts that have been downloaded and cached.
    
    Returns:
        A formatted list of available transcripts with video titles
    """
    cache: TranscriptCache = ctx.request_context.lifespan_context
    transcripts = cache.list_all()
    
    if not transcripts:
        return "No transcripts have been downloaded yet."
    
    result = "Available Transcripts:\n\n"
    for i, info in enumerate(transcripts, 1):
        title = info.video_info.title if info.video_info else "Unknown Title"
        channel = info.video_info.channel if info.video_info else "Unknown Channel"
        
        result += f"{i}. {title}\n"
        result += f"   Channel: {channel}\n"
        result += f"   ID: {info.video_id}\n"
    
    return result


# Resources
@mcp.resource("transcript://{video_id}")
async def get_transcript_resource(video_id: str, *, ctx: Context = None) -> str:
    """Get transcript by video ID, downloading if necessary"""
    return await get_transcript(video_id, ctx)


@mcp.resource("transcripts://list")
async def list_transcripts_resource(*, ctx: Context = None) -> str:
    """List all available transcripts"""
    return await list_available_transcripts(ctx)


# Prompts
@mcp.prompt()
def summarize_transcript(video_id: str) -> str:
    """Create a prompt to summarize a specific transcript"""
    return f"""Please provide a concise summary of this YouTube video transcript.
Focus on the main topics, key points, and conclusions.
Structure your summary with an introduction, main points, and conclusion.

Please use the following transcript as your source:
{{{{read 'transcript://{video_id}' }}}}
"""


@mcp.prompt()
def highlight_new_information(video_id: str, topic: str) -> str:
    """Create a prompt to identify new/unusual information in a transcript"""
    return f"""Please analyze this YouTube video transcript and highlight any new, 
unusual, or particularly insightful information about "{topic}".

Focus on:
1. Information that contradicts conventional wisdom
2. Novel approaches or perspectives
3. Surprising facts or statistics
4. Cutting-edge research or developments
5. Unique insights from the speaker's experience

For each point, explain why it's significant or how it differs from common knowledge.

Please use the following transcript as your source:
{{{{read 'transcript://{video_id}' }}}}
"""


# Run the server if executed directly
if __name__ == "__main__":
    mcp.run()
