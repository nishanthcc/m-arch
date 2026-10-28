from typing import List, Dict, Any, Optional
import re

class ChunkItem:
    def __init__(
        self,
        chunk_id: str,
        chunk_index: int,
        content: str,
        start_line: int,
        end_line: int,
        section_heading: Optional[str] = None,
        token_count: int = 0
    ):
        self.chunk_id = chunk_id
        self.chunk_index = chunk_index
        self.content = content
        self.start_line = start_line
        self.end_line = end_line
        self.section_heading = section_heading
        self.token_count = token_count

def chunk_text(
    source_id: str,
    content: str,
    file_type: str,
    max_chunk_lines: int = 40,
    overlap_lines: int = 6
) -> List[ChunkItem]:
    """
    Format-aware chunking preserving start_line, end_line, and headings.
    """
    lines = content.splitlines()
    if not lines:
        return []

    chunks: List[ChunkItem] = []
    chunk_index = 0

    if file_type == "markdown":
        # Split on markdown headings (# or ## or ###)
        current_heading = None
        current_block: List[str] = []
        block_start = 1

        for i, line in enumerate(lines, 1):
            heading_match = re.match(r'^(#{1,4})\s+(.+)', line)
            if heading_match and len(current_block) > 15:
                # Flush previous block
                chunk_str = "\n".join(current_block)
                chunks.append(
                    ChunkItem(
                        chunk_id=f"chk_{source_id}_{chunk_index}",
                        chunk_index=chunk_index,
                        content=chunk_str,
                        start_line=block_start,
                        end_line=i - 1,
                        section_heading=current_heading,
                        token_count=len(chunk_str.split())
                    )
                )
                chunk_index += 1
                current_block = [line]
                block_start = i
                current_heading = heading_match.group(2).strip()
            else:
                if heading_match and not current_heading:
                    current_heading = heading_match.group(2).strip()
                current_block.append(line)
                if len(current_block) >= max_chunk_lines:
                    chunk_str = "\n".join(current_block)
                    chunks.append(
                        ChunkItem(
                            chunk_id=f"chk_{source_id}_{chunk_index}",
                            chunk_index=chunk_index,
                            content=chunk_str,
                            start_line=block_start,
                            end_line=i,
                            section_heading=current_heading,
                            token_count=len(chunk_str.split())
                        )
                    )
                    chunk_index += 1
                    # Keep overlap
                    current_block = current_block[-overlap_lines:]
                    block_start = max(1, i - overlap_lines + 1)

        if current_block:
            chunk_str = "\n".join(current_block)
            chunks.append(
                ChunkItem(
                    chunk_id=f"chk_{source_id}_{chunk_index}",
                    chunk_index=chunk_index,
                    content=chunk_str,
                    start_line=block_start,
                    end_line=len(lines),
                    section_heading=current_heading,
                    token_count=len(chunk_str.split())
                )
            )

    else:
        # Code and general text: line-based chunking with semantic boundaries
        i = 0
        total_lines = len(lines)
        while i < total_lines:
            chunk_lines = lines[i : min(i + max_chunk_lines, total_lines)]
            start_line = i + 1
            end_line = min(i + max_chunk_lines, total_lines)
            chunk_str = "\n".join(chunk_lines)

            chunks.append(
                ChunkItem(
                    chunk_id=f"chk_{source_id}_{chunk_index}",
                    chunk_index=chunk_index,
                    content=chunk_str,
                    start_line=start_line,
                    end_line=end_line,
                    section_heading=None,
                    token_count=len(chunk_str.split())
                )
            )
            chunk_index += 1

            if end_line >= total_lines:
                break
            i += (max_chunk_lines - overlap_lines)

    return chunks
