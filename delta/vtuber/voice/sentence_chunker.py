"""
Sentence Chunker for Delta VTuber Voice pipeline.
Splits continuous text or streaming tokens into clean, sentence-level chunks suitable for TTS synthesis.
"""

import re
from typing import List, Optional, Tuple
from delta.vtuber.events import VTuberEmotion
from delta.vtuber.voice.schemas import SpeechChunk


class SentenceChunker:
    """
    Splits text into natural sentence boundaries while preserving punctuation.
    Supports both batch splitting and incremental streaming token accumulation.
    """

    # Sentence-ending punctuation regex (respects ellipses, multiple punctuation marks, and newlines)
    # Matches: . ! ? ... followed by whitespace or end-of-string, or standalone newlines.
    _SPLIT_REGEX = re.compile(r"(\.{3,}|\.|\!|\?|\n+)", re.UNICODE)

    def __init__(self, min_chunk_len: int = 4, max_chunk_len: int = 250):
        self.min_chunk_len = min_chunk_len
        self.max_chunk_len = max_chunk_len
        self._stream_buffer: str = ""
        self._seq_counter: int = 0

    def chunk_text(
        self,
        text: str,
        emotion: VTuberEmotion = VTuberEmotion.NEUTRAL,
        intensity: float = 1.0,
        start_sequence: int = 0,
        speech_id: Optional[str] = None,
    ) -> List[SpeechChunk]:
        """
        Split a full text string into a list of SpeechChunks.
        """
        if not text or not text.strip():
            return []

        clean_text = text.strip()
        raw_parts = self._split_into_sentences(clean_text)

        chunks: List[SpeechChunk] = []
        seq = start_sequence
        import uuid
        s_id = speech_id or str(uuid.uuid4())

        for part in raw_parts:
            part_str = part.strip()
            if not part_str:
                continue

            # If a part exceeds max_chunk_len, divide by clauses/commas/spaces
            sub_parts = self._split_long_sentence(part_str)
            for sub in sub_parts:
                sub_clean = sub.strip()
                if sub_clean:
                    chunks.append(
                        SpeechChunk(
                            speech_id=s_id,
                            sequence=seq,
                            text=sub_clean,
                            emotion=emotion,
                            intensity=intensity,
                        )
                    )
                    seq += 1

        return chunks

    def append_stream_token(
        self,
        token: str,
        emotion: VTuberEmotion = VTuberEmotion.NEUTRAL,
        intensity: float = 1.0,
    ) -> List[SpeechChunk]:
        """
        Incrementally append token and emit SpeechChunks as soon as sentence boundaries are detected.
        """
        self._stream_buffer += token
        ready_chunks: List[SpeechChunk] = []

        # Find boundaries in buffer
        sentences, remaining = self._extract_completed_sentences(self._stream_buffer)
        self._stream_buffer = remaining

        for sentence in sentences:
            sentence_clean = sentence.strip()
            if len(sentence_clean) >= self.min_chunk_len:
                ready_chunks.append(
                    SpeechChunk(
                        sequence=self._seq_counter,
                        text=sentence_clean,
                        emotion=emotion,
                        intensity=intensity,
                    )
                )
                self._seq_counter += 1

        return ready_chunks

    def flush_stream(
        self,
        emotion: VTuberEmotion = VTuberEmotion.NEUTRAL,
        intensity: float = 1.0,
    ) -> List[SpeechChunk]:
        """
        Flush remaining buffer into final SpeechChunks.
        """
        remaining = self._stream_buffer.strip()
        self._stream_buffer = ""
        if not remaining:
            return []

        chunks = self.chunk_text(
            remaining,
            emotion=emotion,
            intensity=intensity,
            start_sequence=self._seq_counter,
        )
        self._seq_counter += len(chunks)
        return chunks

    def reset_stream(self) -> None:
        """Reset streaming state buffer and sequence counter."""
        self._stream_buffer = ""
        self._seq_counter = 0

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text while preserving terminal punctuation attached to preceding sentence."""
        tokens = self._SPLIT_REGEX.split(text)
        sentences: List[str] = []
        current = ""

        i = 0
        while i < len(tokens):
            item = tokens[i]
            if not item:
                i += 1
                continue

            if self._SPLIT_REGEX.fullmatch(item):
                # This is a delimiter (e.g. '.', '!', '?', '\n')
                if current:
                    current += item.strip() if "\n" not in item else ""
                    if len(current.strip()) >= self.min_chunk_len:
                        sentences.append(current.strip())
                        current = ""
                i += 1
            else:
                # Text content
                current = (current + " " + item).strip() if current else item.strip()
                # Check if next token is delimiter
                if i + 1 < len(tokens) and self._SPLIT_REGEX.fullmatch(tokens[i + 1]):
                    delim = tokens[i + 1]
                    current += delim.strip() if "\n" not in delim else ""
                    if len(current.strip()) >= self.min_chunk_len:
                        sentences.append(current.strip())
                        current = ""
                    i += 2
                else:
                    i += 1

        if current and current.strip():
            sentences.append(current.strip())

        return sentences

    def _split_long_sentence(self, sentence: str) -> List[str]:
        """Break down excessively long sentence by comma/semicolon/spaces without truncating words."""
        if len(sentence) <= self.max_chunk_len:
            return [sentence]

        # Try clause split by comma/semicolon
        clause_split = re.split(r"([,;:\-—]\s+)", sentence)
        result: List[str] = []
        curr = ""

        for part in clause_split:
            if len(curr) + len(part) <= self.max_chunk_len:
                curr += part
            else:
                if curr.strip():
                    result.append(curr.strip())
                curr = part

        if curr.strip():
            result.append(curr.strip())

        return result if result else [sentence]

    def _extract_completed_sentences(self, buffer: str) -> Tuple[List[str], str]:
        """Extract all finished sentences from stream buffer, returning (completed_list, leftover)."""
        tokens = self._SPLIT_REGEX.split(buffer)
        if len(tokens) <= 1:
            return [], buffer

        completed: List[str] = []
        accum = ""

        # Process pairs of (text, delimiter)
        idx = 0
        while idx < len(tokens) - 1:
            part = tokens[idx]
            next_part = tokens[idx + 1]

            if self._SPLIT_REGEX.fullmatch(next_part):
                sentence = (accum + " " + part).strip() if accum else part.strip()
                delim = next_part.strip() if "\n" not in next_part else ""
                full_sentence = f"{sentence}{delim}".strip()
                if full_sentence:
                    completed.append(full_sentence)
                accum = ""
                idx += 2
            else:
                accum = (accum + " " + part).strip() if accum else part.strip()
                idx += 1

        leftover = (accum + " " + tokens[-1]).strip() if accum else tokens[-1]
        return completed, leftover
