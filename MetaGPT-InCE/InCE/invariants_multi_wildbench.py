import re
from typing import Iterable, List, Optional


class InvariantManager:
    def __init__(
        self,
        max_items: Optional[int] = 35,
        max_item_words: int = 120,
    ) -> None:
        self.max_items = max_items
        self.max_item_words = max_item_words
        self._items: List[str] = []

    def items(self) -> List[str]:
        return list(self._items)

    def update(self, new_items: Optional[Iterable[str]]) -> None:
        self.update_for_round(new_items, target_count=None)

    def update_for_round(
        self,
        new_items: Optional[Iterable[str]],
        target_count: Optional[int],
    ) -> None:
        if target_count == 0:
            return

        cleaned_new: List[str] = []
        for item in new_items or []:
            cleaned = self._clean_item(item)
            if not cleaned:
                continue
            if not self._exists_in_list(cleaned, cleaned_new):
                cleaned_new.append(cleaned)

        if target_count is not None:
            cleaned_new = cleaned_new[:target_count]

        for item in cleaned_new:
            if not self._exists_in_list(item, self._items):
                self._items.append(item)

        if self.max_items and len(self._items) > self.max_items:
            self._items = self._items[-self.max_items :]

    def format_for_prompt(self) -> str:
        if not self._items:
            return ""

        lines = [f"{idx + 1}. {item}" for idx, item in enumerate(self._items)]
        block = "\n".join(lines)
        return f"GLOBAL INVARIANTS:\n{block}\nEND GLOBAL INVARIANTS"

    def _exists(self, candidate: str) -> bool:
        normalized = self._normalize(candidate)
        for item in self._items:
            if self._normalize(item) == normalized:
                return True
        return False

    def _clean_item(self, item: str) -> str:
        if not item:
            return ""

        text = str(item).strip()
        text = re.sub(r"^[\\-\\*\\d\\.\\)\\s]+", "", text)
        text = re.sub(r"\\s+", " ", text).strip()

        if not text:
            return ""

        if self.max_item_words:
            text = self._trim_words(text, self.max_item_words)

        return text

    @staticmethod
    def _normalize(text: str) -> str:
        return re.sub(r"\\s+", " ", text.strip().lower())

    def _exists_in_list(self, candidate: str, items: List[str]) -> bool:
        normalized = self._normalize(candidate)
        return any(self._normalize(item) == normalized for item in items)

    @staticmethod
    def _trim_words(text: str, max_words: int) -> str:
        words = text.split()
        if len(words) <= max_words:
            return text
        return " ".join(words[:max_words]).rstrip() + "..."
