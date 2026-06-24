"""Holds the research topic and produces the question list."""
from typing import List

from research import question_generator


class TopicManager:
    def __init__(self, topic: str):
        self.topic = topic.strip()
        self.questions: List[str] = []

    def build_questions(self, n: int = 5) -> List[str]:
        self.questions = question_generator.generate(self.topic, n)
        return self.questions
