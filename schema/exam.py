from pydantic import BaseModel, Field, model_validator
from enum import Enum


class QuestionEnum(str, Enum):
    singleQuestion = "singleQuestion"
    multipleQuestions = "multipleQuestions"
    shortAnswer = "shortAnswer"


class OptionsForm(BaseModel):
    option_value: str = Field(min_length=1, max_length=2000)
    is_correct: bool
    option_key: str = Field(min_length=1, max_length=20)


class QuestionForm(BaseModel):
    question_name: str = Field(min_length=1, max_length=2000)
    question_type: QuestionEnum
    options: list[OptionsForm] = Field(default_factory=list)
    answer: str | None = None

    @model_validator(mode="after")
    def validate_question(self):

        if not self.question_name.strip():
            raise ValueError("Question text cannot be blank")
        if len({option.option_key for option in self.options}) != len(self.options):
            raise ValueError("Option keys must be distinct")
        if self.question_type == QuestionEnum.singleQuestion:

            if len(self.options) < 2:
                raise ValueError("单选题至少需要两个选项")

            correct_count = sum(option.is_correct for option in self.options)

            if correct_count != 1:
                raise ValueError("单选题必须且只能有一个正确答案")

        elif self.question_type == QuestionEnum.multipleQuestions:

            if len(self.options) < 2:
                raise ValueError("多选题至少需要两个选项")

            correct_count = sum(option.is_correct for option in self.options)

            if correct_count < 2:
                raise ValueError("多选题至少需要两个正确答案")

        elif self.question_type == QuestionEnum.shortAnswer:

            if self.options:
                raise ValueError("简答题不能包含选项")

            if not self.answer:
                raise ValueError("简答题必须提供参考答案")

        return self


class ExamForm(BaseModel):
    exam_name: str = Field(min_length=1, max_length=200)
    lesson_id: int = Field(gt=0)
    questions: list[QuestionForm] = Field(min_length=1, max_length=200)


class SubmitQuestionForm(BaseModel):
    q_id: int
    answer: str | None


class SubmitExamForm(BaseModel):
    attempt_id: int
    questions: list[SubmitQuestionForm] = Field(max_length=200)

    @model_validator(mode="after")
    def distinct_answers(self):
        if len({item.q_id for item in self.questions}) != len(self.questions):
            raise ValueError("Question answers must be distinct")
        return self


class AttemptExamForm(BaseModel):
    lesson_id: int = Field(gt=0)
    exam_id: int = Field(gt=0)
    plan_id: int | None = Field(default=None, gt=0)
