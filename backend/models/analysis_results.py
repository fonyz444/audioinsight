from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class Task(BaseModel):
    """Модель для представления задачи/пункта действий"""
    description: str = Field(..., description="Описание задачи")
    assignee: Optional[str] = Field(None, description="Ответственный за выполнение")
    deadline: Optional[str] = Field(None, description="Срок выполнения")
    priority: Optional[str] = Field("medium", description="Приоритет: low, medium, high")


class Decision(BaseModel):
    """Модель для представления принятого решения"""
    decision: str = Field(..., description="Описание решения")
    context: Optional[str] = Field(None, description="Контекст принятия решения")
    impact: Optional[str] = Field(None, description="Ожидаемое влияние решения")


class Topic(BaseModel):
    """Модель для представления обсуждаемой темы"""
    topic: str = Field(..., description="Название темы")
    summary: Optional[str] = Field(None, description="Краткое резюме обсуждения")
    duration_estimate: Optional[str] = Field(None, description="Приблизительное время обсуждения")


class Insight(BaseModel):
    """Модель для представления инсайта или рекомендации"""
    insight: str = Field(..., description="Описание инсайта")
    category: Optional[str] = Field(None, description="Категория инсайта")
    recommendation: Optional[str] = Field(None, description="Рекомендация по действиям")


class MeetingAnalysisResults(BaseModel):
    """Полные результаты анализа встречи"""
    # Основная информация
    transcription: str = Field(..., description="Полная транскрипция встречи")
    analysis_timestamp: datetime = Field(default_factory=datetime.now, description="Время анализа")
    
    # Структурированные данные
    tasks: List[Task] = Field(default_factory=list, description="Список задач и пунктов действий")
    decisions: List[Decision] = Field(default_factory=list, description="Принятые решения")
    topics: List[Topic] = Field(default_factory=list, description="Обсуждаемые темы")
    insights: List[Insight] = Field(default_factory=list, description="Инсайты и рекомендации")
    
    # Оценки и риски
    effectiveness_score: float = Field(0.0, ge=0.0, le=10.0, description="Оценка эффективности встречи (0-10)")
    risks: List[str] = Field(default_factory=list, description="Выявленные потенциальные риски")
    
    # Метаданные
    meeting_duration_estimate: Optional[str] = Field(None, description="Оценочная продолжительность встречи")
    participant_count_estimate: Optional[int] = Field(None, description="Приблизительное количество участников")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }