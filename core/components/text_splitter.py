from langchain_text_splitters import Language, RecursiveCharacterTextSplitter, TextSplitter
from typing import Any


class TextSplitterComponent:
    def __init__(self, chunk_size: int, chunk_overlap: int):
        self.code_language = "python"
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = self.build_text_splitter()

    def get_data_input(self) -> Any:
        return self.data_input

    def build_text_splitter(self) -> TextSplitter:
        return RecursiveCharacterTextSplitter(
                separators=[
                    "\n\n",
                    "\n",
                    " ",
                    ".",
                    ",",
                    "\u200b",  # Zero-width space
                    "\uff0c",  # Fullwidth comma
                    "\u3001",  # Ideographic comma
                    "\uff0e",  # Fullwidth full stop
                    "\u3002",  # Ideographic full stop
                    "",
                ],
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
    def split_text(self, text: str) -> list:
        return self.text_splitter.split_text(text)
