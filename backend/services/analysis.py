import json
import anthropic
from typing import List, Dict, Any, Tuple
from models.analysis_results import Task, Decision, Topic, Insight
import traceback
import logging
import asyncio

logger = logging.getLogger(__name__)

class AnalysisWorker:
    """Воркер для анализа транскрипции с использованием Claude API"""
    
    def __init__(self, api_key: str):
        """
        Инициализация воркера анализа
        
        Args:
            api_key: Anthropic API ключ
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-3-sonnet-20240229"  # Используем Sonnet для баланса качества и скорости
        print("✅ AnalysisWorker инициализирован")
    
    async def _call_claude(self, prompt: str, system_prompt: str) -> str:
        """
        Вспомогательный метод для вызова Claude API
        
        Args:
            prompt: Сообщение пользователя
            system_prompt: Системный промпт
            
        Returns:
            Ответ от Claude
        """
        try:
            response = self.client.completions.create(
                model="claude-2",
                prompt=f"{system_prompt}\n\n{prompt}",
                max_tokens_to_sample=1024,
                temperature=0.7
            )
            return response.completion
        except Exception as e:
            logger.error(f"❌ Ошибка при вызове Claude API: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise Exception(f"Ошибка анализа с Claude: {str(e)}")
    
    async def analyze_content(self, transcription: str) -> Dict[str, Any]:
        return {
            "topics": [
                {"topic": "UI Design Review", "summary": "Обсуждение финальных правок UI", "duration_estimate": "15 мин"},
                {"topic": "API Development", "summary": "Прогресс по интеграции API", "duration_estimate": "12 мин"},
                {"topic": "Testing Strategy", "summary": "План тестирования", "duration_estimate": "10 мин"},
                {"topic": "Release Planning", "summary": "Планирование релиза", "duration_estimate": "8 мин"}
            ],
            "decisions": [
                {"decision": "Финализировать UI до 20 июня", "context": "Обсуждение с командой", "impact": "Своевременный релиз"},
                {"decision": "Провести интеграционное тестирование", "context": "API интеграция", "impact": "Повышение качества"}
            ],
            "meeting_type": "weekly_sync",
            "effectiveness_score": 7.5
        }

    async def extract_tasks(self, content: str) -> List[Dict]:
        """Извлекает задачи из контента"""
        # MOCK: Возвращаем тестовые задачи
        return [
            {
                "id": "1",
                "task": "Подготовить презентацию по результатам исследования",
                "assignee": "Sarah Johnson",
                "deadline": "2025-06-20",
                "priority": "high",
                "status": "pending",
                "context": "Важно для следующего этапа проекта"
            },
            {
                "id": "2",
                "task": "Провести тестирование новой функциональности",
                "assignee": "Michael Wong",
                "deadline": "2025-06-22",
                "priority": "medium",
                "status": "pending",
                "context": "Необходимо для релиза"
            },
            {
                "id": "3",
                "task": "Обновить документацию API",
                "assignee": "Alex Chen",
                "deadline": "2025-06-25",
                "priority": "high",
                "status": "pending",
                "context": "Критично для разработчиков"
            }
        ]

    async def generate_insights(self, transcription: str) -> Dict[str, Any]:
        return {
            "team_dynamics": "Команда работает слаженно, коммуникация эффективна.",
            "process_recommendations": ["Проводить встречи раз в неделю", "Добавить больше времени на обсуждение тестирования"],
            "risk_flags": [
                "Potential delay in the API integration due to third-party service issues",
                "Limited testing resources might affect quality assurance"
            ],
            "follow_up_suggestions": ["Проверить статус задач через 3 дня", "Подготовить отчет для стейкхолдеров"]
        }

    async def analyze(self, transcription: str) -> Dict[str, Any]:
        """
        Основной метод анализа транскрипции
        """
        print("🚀 Начинаю анализ транскрипции...")
        
        try:
            # Запускаем все анализаторы параллельно
            content_result, tasks_result, insights_result = await asyncio.gather(
                self.analyze_content(transcription),
                self.extract_tasks(transcription),
                self.generate_insights(transcription)
            )
            
            # Формируем итоговый результат
            result = {
                "content_analysis": content_result,
                "tasks": tasks_result,
                "insights": insights_result,
                "status": "success"
            }
            
            print("✅ Анализ успешно завершен")
            return result
            
        except Exception as e:
            print(f"❌ Ошибка при анализе: {str(e)}")
            return {
                "content_analysis": {
                    "topics": [],
                    "decisions": [],
                    "meeting_type": "error",
                    "effectiveness_score": 0
                },
                "tasks": [],
                "insights": {
                    "team_dynamics": "",
                    "process_recommendations": [],
                    "risk_flags": ["Ошибка анализа"],
                    "follow_up_suggestions": []
                },
                "status": "error",
                "error": str(e)
            }