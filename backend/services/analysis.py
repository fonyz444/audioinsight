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
        """
        Анализирует содержание транскрипции
        """
        print("🔍 Воркер 2: Анализирую содержание для выявления тем и решений...")
        
        system_prompt = """Ты - эксперт по анализу деловых встреч. Анализируй транскрипцию встречи и выдели:

1. ТЕМЫ (topics) - основные темы обсуждения
2. РЕШЕНИЯ (decisions) - принятые решения
3. ТИП ВСТРЕЧИ (meeting_type) - тип встречи (standup, planning, review и т.д.)
4. ОЦЕНКА ЭФФЕКТИВНОСТИ (effectiveness_score) - от 1 до 10

Верни результат в формате JSON."""

        try:
            response = await self._call_claude(transcription, system_prompt)
            
            # Парсим JSON ответ
            result = json.loads(response)
            
            return {
                "topics": result.get("topics", []),
                "decisions": result.get("decisions", []),
                "meeting_type": result.get("meeting_type", "general"),
                "effectiveness_score": result.get("effectiveness_score", 5)
            }
            
        except Exception as e:
            print(f"❌ Ошибка в analyze_content: {str(e)}")
            return {
                "topics": [],
                "decisions": [],
                "meeting_type": "error",
                "effectiveness_score": 0
            }

    async def extract_tasks(self, transcription: str) -> List[Dict[str, Any]]:
        """
        Извлекает задачи и пункты действий
        """
        print("📋 Воркер 3: Извлекаю задачи и пункты действий...")
        
        system_prompt = """Ты - эксперт по планированию проектов. Найди в транскрипции встречи все задачи, пункты действий, поручения.
Для каждой задачи укажи:
- описание
- ответственного
- срок
- приоритет (high/medium/low)

Верни результат в формате JSON."""

        try:
            response = await self._call_claude(transcription, system_prompt)
            
            # Парсим JSON ответ
            tasks = json.loads(response)
            
            return tasks
            
        except Exception as e:
            print(f"❌ Ошибка в extract_tasks: {str(e)}")
            return []

    async def generate_insights(self, transcription: str) -> Dict[str, Any]:
        """
        Генерирует инсайты и рекомендации
        """
        print("💡 Воркер 4: Генерирую инсайты, риски и оценку эффективности...")
        
        system_prompt = """Ты - консультант по эффективности деловых процессов. Проанализируй транскрипцию встречи и предоставь:

1. ДИНАМИКА КОМАНДЫ (team_dynamics) - оценка взаимодействия участников
2. РЕКОМЕНДАЦИИ ПО ПРОЦЕССУ (process_recommendations) - как улучшить процесс
3. РИСКИ (risk_flags) - потенциальные проблемы
4. ПРЕДЛОЖЕНИЯ ПО ДАЛЬНЕЙШИМ ДЕЙСТВИЯМ (follow_up_suggestions)

Верни результат в формате JSON."""

        try:
            response = await self._call_claude(transcription, system_prompt)
            
            # Парсим JSON ответ
            insights = json.loads(response)
            
            return {
                "team_dynamics": insights.get("team_dynamics", ""),
                "process_recommendations": insights.get("process_recommendations", []),
                "risk_flags": insights.get("risk_flags", []),
                "follow_up_suggestions": insights.get("follow_up_suggestions", [])
            }
            
        except Exception as e:
            print(f"❌ Ошибка в generate_insights: {str(e)}")
            return {
                "team_dynamics": "",
                "process_recommendations": [],
                "risk_flags": ["Ошибка анализа"],
                "follow_up_suggestions": []
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