import os
import json
import asyncio
from datetime import datetime
from typing import Dict, Any
import logging
from .speech_service import speech_service, GoogleSpeechService
from .analysis import AnalysisWorker
import traceback

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "backend/audioinsight-460812-12bcf2327c7f.json"

class MeetingOrchestrator:
    """
    Главный оркестратор для обработки meeting-ов
    Использует Google Cloud Speech для транскрипции
    """
    
    def __init__(self):
        self.results_dir = os.getenv("RESULTS_DIR", "./results")
        os.makedirs(self.results_dir, exist_ok=True)
        logger.info("MeetingOrchestrator initialized with Google Speech")
        
        self.speech_service = GoogleSpeechService()
        self.analysis_worker = AnalysisWorker(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    async def process_meeting(self, meeting_id: str, file_path: str, filename: str) -> Dict[str, Any]:
        """
        Основной метод обработки meeting-а с Google Speech
        """
        logger.info(f"Starting processing for meeting {meeting_id}: {filename}")
        
        try:
            # Инициализация результата в соответствии с моделью MeetingAnalysisResults
            result = {
                "id": meeting_id,
                "filename": filename,
                "status": "processing",
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "transcription": None,
                "tasks": [],
                "decisions": [],
                "topics": [],
                "insights": [],
                "effectiveness_score": 0.0,
                "risks": [],
                "meeting_duration_estimate": None,
                "participant_count_estimate": None
            }
            
            # Сохраняем промежуточный результат
            await self._save_result(meeting_id, result)
            
            # Step 1: Transcription с Google Cloud Speech
            logger.info(f"Step 1: Transcribing audio with Google Speech for {meeting_id}")
            transcript_data = await self.speech_service.transcribe_audio(file_path)
            result["transcription"] = transcript_data["text"]
            await self._save_result(meeting_id, result)
            
            # Step 2: Content Analysis (Claude)
            logger.info(f"Step 2: Analyzing content with Claude for {meeting_id}")
            analysis_result = await self.analysis_worker.analyze(transcript_data["text"])
            
            # Обновляем результат анализа
            result.update({
                "content": {
                    "topics": analysis_result["content_analysis"]["topics"],
                    "decisions": analysis_result["content_analysis"]["decisions"],
                    "meetingType": analysis_result["content_analysis"]["meeting_type"],
                    "effectivenessScore": analysis_result["content_analysis"]["effectiveness_score"]
                },
                "actionItems": analysis_result["tasks"],
                "insights": {
                    "teamDynamics": analysis_result["insights"]["team_dynamics"],
                    "processRecommendations": analysis_result["insights"]["process_recommendations"],
                    "riskFlags": analysis_result["insights"]["risk_flags"],
                    "followUpSuggestions": analysis_result["insights"]["follow_up_suggestions"]
                }
            })
            
            # Финализация
            result["status"] = "completed"
            result["meeting_duration_estimate"] = transcript_data.get("duration", "Unknown")
            result["participant_count_estimate"] = transcript_data.get("participant_count", 0)
            
            # Сохраняем финальный результат
            await self._save_result(meeting_id, result)
            
            logger.info(f"Processing completed for meeting {meeting_id}")
            
            # Очистка временного файла
            try:
                if os.path.exists(file_path) and "temp_uploads" in file_path:
                    os.remove(file_path)
                    logger.info(f"Cleaned up temporary file: {file_path}")
            except Exception as e:
                logger.warning(f"Could not clean up file {file_path}: {str(e)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing meeting {meeting_id}: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Обновляем статус на error
            result["status"] = "error"
            result["error"] = str(e)
            await self._save_result(meeting_id, result)
            
            raise
    
    async def _save_result(self, meeting_id: str, result: Dict[str, Any]) -> None:
        """
        Сохранение результата в файл
        """
        try:
            result_file = os.path.join(self.results_dir, f"{meeting_id}.json")
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            logger.info(f"Result saved for meeting {meeting_id}")
        except Exception as e:
            logger.error(f"Failed to save result for meeting {meeting_id}: {str(e)}")
            raise e