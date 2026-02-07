import argparse
import re
import sys
import asyncio
import os
import pathlib
import edge_tts

def sanitize_filename(name: str) -> str:
    """Sanitizes a string to be used as a valid filename."""
    # Replace invalid characters with an underscore
    s = re.sub(r'[<>:"/\\|?*]', '_', name)
    # Remove leading/trailing spaces and dots
    s = s.strip()
    s = s.strip('.')
    # Truncate to a reasonable length if necessary
    return s[:200]

async def speak_text(text: str, output_path: pathlib.Path, voice: str = "en-US-JennyNeural"):
    """
    Uses edge-tts to speak the given text.
    """
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(output_path))
    print(f"Chapter saved to {output_path}. Play it using an audio player.")

def parse_markdown_chapters(markdown_content: str) -> dict:
    """
    Parses markdown content into a dictionary of chapters.
    Chapters are identified by H1 headings (# Chapter Name).
    """
    chapters = {}
    # Split the content by H1 headings
    # The regex looks for a newline followed by '#' and a space, capturing the chapter title
    # and then the content until the next H1 or end of file.
    # re.DOTALL makes '.' match newlines, so content can span multiple lines.
    matches = re.finditer(r'''#\s*(.+?)\n([\s\S]*?)(?=(?:\n#\s*|$))''', markdown_content)

    for match in matches:
        chapter_title = match.group(1).strip()
        chapter_content = match.group(2).strip()
        chapters[chapter_title.lower()] = chapter_content # Store lowercased title for case-insensitive lookup
    return chapters

def main():
    parser = argparse.ArgumentParser(
        description="Read a specific chapter from a Markdown file using edge-tts."
    )
    parser.add_argument(
        "markdown_file",
        help="Path to the markdown file containing the chapters."
    )
    parser.add_argument(
        "-c", "--chapter",
        help="The name of the chapter to read. If not provided, you will be prompted."
    )
    parser.add_argument(
        "-a", "--all", action="store_true",
        help="Process all chapters and save them as MP3s in a dedicated folder."
    )
    args = parser.parse_args()

    try:
        with open(args.markdown_file, "r", encoding="utf-8") as f:
            markdown_content = f.read()
    except FileNotFoundError:
        print(f"Error: Markdown file not found at '{args.markdown_file}'")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading markdown file: {e}")
        sys.exit(1)

    chapters = parse_markdown_chapters(markdown_content)

    if not chapters:
        print("No chapters found in the markdown file. Chapters must start with '# Chapter Name'.")
        sys.exit(1)

    # Determine output directory
    markdown_file_path = pathlib.Path(args.markdown_file)
    output_dir_name = sanitize_filename(markdown_file_path.stem)
    output_dir = markdown_file_path.parent / output_dir_name
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output directory for MP3s: {output_dir}")

    async def process_chapter(title: str, content: str):
        sanitized_title = sanitize_filename(title)
        output_mp3_path = output_dir / f"{sanitized_title}.mp3"

        print(f"\nProcessing chapter: '{title.title()}'")
        if output_mp3_path.exists():
            print(f"  --> MP3 already exists for '{title.title()}'. Skipping generation.")
            return

        print("-" * (len(title) + 18))
        print(content)
        print("-" * (len(title) + 18))
        await speak_text(content, output_mp3_path)

    if args.all:
        print("\nProcessing all chapters...")
        for title, content in chapters.items():
            asyncio.run(process_chapter(title, content))
        print("\nAll chapters processed.")
    elif args.chapter:
        selected_chapter_title = args.chapter
        chapter_content = chapters.get(selected_chapter_title.lower())
        if chapter_content:
            asyncio.run(process_chapter(selected_chapter_title, chapter_content))
        else:
            print(f"Error: Chapter '{selected_chapter_title}' not found.")
            print("Available chapters are:")
            for title in chapters.keys():
                print(f"- {title.title()}")
            sys.exit(1)
    else:
        print("Available chapters:")
        for title in chapters.keys():
            print(f"- {title.title()}")
        selected_chapter_title = input("Enter the chapter name you want to read: ").strip()
        chapter_content = chapters.get(selected_chapter_title.lower())
        if chapter_content:
            asyncio.run(process_chapter(selected_chapter_title, chapter_content))
        else:
            print(f"Error: Chapter '{selected_chapter_title}' not found.")
            print("Available chapters are:")
            for title in chapters.keys():
                print(f"- {title.title()}")
            sys.exit(1)

if __name__ == "__main__":
    main()
