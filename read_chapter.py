import argparse
import re
import sys
import asyncio
import edge_tts

async def speak_text(text: str, voice: str = "en-US-JennyNeural"):
    """
    Uses edge-tts to speak the given text.
    """
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save("temp_chapter.mp3")
    # You might want to play this automatically, but for CLI, saving to file is safer.
    # On Linux, you can use: os.system("mpg123 temp_chapter.mp3") if mpg123 is installed
    print("Chapter saved to temp_chapter.mp3. Play it using an audio player.")

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

    selected_chapter_title = args.chapter
    if not selected_chapter_title:
        print("Available chapters:")
        for title in chapters.keys():
            print(f"- {title.title()}") # Display titles nicely capitalized
        selected_chapter_title = input("Enter the chapter name you want to read: ").strip()

    chapter_content = chapters.get(selected_chapter_title.lower())

    if chapter_content:
        print(f"Reading chapter: '{selected_chapter_title.title()}'")
        print("-" * (len(selected_chapter_title) + 18)) # Separator for readability
        print(chapter_content)
        print("-" * (len(selected_chapter_title) + 18)) # Separator for readability
        asyncio.run(speak_text(chapter_content))
    else:
        print(f"Error: Chapter '{selected_chapter_title}' not found.")
        print("Available chapters are:")
        for title in chapters.keys():
            print(f"- {title.title()}")
        sys.exit(1)

if __name__ == "__main__":
    main()
