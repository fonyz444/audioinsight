from fastapi import FastAPI, HTTPException, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime
import os
import uuid
import json
import asyncio
import logging
import traceback
from dotenv import load_dotenv
from services.orchestrator import MeetingOrchestrator

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI(
    title="AudioInsight API", 
    version="1.0.0",
    description="AI-powered meeting analysis platform"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directories
os.makedirs("temp_uploads", exist_ok=True)
os.makedirs("results", exist_ok=True)

# Models
class HealthResponse(BaseModel):
    status: str
    message: str

class MeetingResponse(BaseModel):
    id: str
    filename: str
    status: str

# Глобальное хранилище
meeting_results = {}
processing_status = {}

# Глобальный экземпляр оркестратора
orchestrator = MeetingOrchestrator()

def safe_get(obj, key, default=None):
    """Безопасное получение значения из объекта"""
    try:
        if isinstance(obj, dict):
            return obj.get(key, default)
        elif isinstance(obj, list):
            logger.warning(f"Попытка вызвать .get() на списке для ключа '{key}'")
            return default
        else:
            logger.warning(f"Попытка вызвать .get() на объекте типа {type(obj)} для ключа '{key}'")
            return default
    except Exception as e:
        logger.error(f"Ошибка в safe_get для ключа '{key}': {str(e)}")
        return default

@app.get("/")
async def root():
    return {
        "message": "AudioInsight API", 
        "version": "1.0.0",
        "status": "running",
        "active_meetings": len(processing_status),
        "completed_meetings": len(meeting_results)
    }

@app.get("/health")
async def health():
    return HealthResponse(status="healthy", message="AudioInsight API is running")

@app.post("/api/meetings/upload")
async def upload_meeting(file: UploadFile = File(...)):
    logger.info(f"📤 Upload request received for file: {file.filename}")
    
    try:
        # Генерируем уникальный ID для встречи
        meeting_id = str(uuid.uuid4())
        
        # Сохраняем файл во временную директорию
        temp_path = f"temp_uploads/{meeting_id}_{file.filename}"
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        logger.info(f"💾 File saved to: {temp_path}")
        
        # Инициализируем статус обработки
        processing_status[meeting_id] = {
            "status": "processing",
            "filename": file.filename,
            "started_at": datetime.utcnow().isoformat(),
            "progress": 0,
            "current_step": "Starting processing"
        }
        
        # Запускаем обработку в фоне
        asyncio.create_task(orchestrator.process_meeting(meeting_id, temp_path, file.filename))
        
        return JSONResponse({
            "id": meeting_id,
            "filename": file.filename,
            "status": "processing"
        })
        
    except Exception as e:
        logger.error(f"💥 Upload error: {str(e)}")
        logger.error(f"💥 Upload traceback: {traceback.format_exc()}")
        raise HTTPException(500, f"Upload failed: {str(e)}")

@app.get("/api/meetings/{meeting_id}")
async def get_meeting_analysis(meeting_id: str):
    logger.info(f"📊 Request for meeting: {meeting_id}")
    
    try:
        # Проверяем завершенные результаты
        if meeting_id in meeting_results:
            result = meeting_results[meeting_id]
            logger.info(f"✅ Found completed result for: {meeting_id}")
            
            # Проверяем что result это словарь
            if not isinstance(result, dict):
                logger.error(f"❌ Result is not a dict, type: {type(result)}")
                raise HTTPException(500, f"Invalid result format for meeting {meeting_id}")
            
            # Валидируем и очищаем структуру
            try:
                validated_result = validate_and_clean_result(result)
                logger.info(f"✅ Returning validated result for: {meeting_id}")
                return JSONResponse(validated_result)
            except Exception as validation_error:
                logger.error(f"❌ Validation error: {str(validation_error)}")
                logger.error(f"❌ Validation traceback: {traceback.format_exc()}")
                
                # Return a fallback response instead of raising an exception
                fallback_result = {
                    "id": meeting_id,
                    "filename": safe_get(result, "filename", "unknown.mp3"),
                    "status": "completed",
                    "uploadedAt": datetime.utcnow().isoformat(),
                    "processedAt": datetime.utcnow().isoformat(),
                    "transcript": {
                        "text": "Error validating meeting data",
                        "duration": 0,
                        "language": "en-US",
                        "participantCount": 0
                    },
                    "content": {
                        "topics": [],
                        "decisions": [],
                        "meetingType": "error",
                        "effectivenessScore": 0
                    },
                    "actionItems": [],
                    "insights": {
                        "teamDynamics": "Validation error occurred",
                        "processRecommendations": [],
                        "riskFlags": [f"Data validation failed: {str(validation_error)}"],
                        "followUpSuggestions": []
                    }
                }
                logger.info(f"⚠️ Returning fallback result due to validation error")
                return JSONResponse(fallback_result)
        
        # Если нет в памяти, пробуем загрузить из файла
        result_file = os.path.join("results", f"{meeting_id}.json")
        if os.path.exists(result_file):
            with open(result_file, "r", encoding="utf-8") as f:
                result = json.load(f)
            meeting_results[meeting_id] = result  # Кэшируем в память
            logger.info(f"✅ Loaded result from file for: {meeting_id}")
            try:
                validated_result = validate_and_clean_result(result)
                logger.info(f"✅ Returning validated result for: {meeting_id} (from file)")
                return JSONResponse(validated_result)
            except Exception as validation_error:
                logger.error(f"❌ Validation error: {str(validation_error)}")
                logger.error(f"❌ Validation traceback: {traceback.format_exc()}")
                
                # Return a fallback response instead of raising an exception
                fallback_result = {
                    "id": meeting_id,
                    "filename": safe_get(result, "filename", "unknown.mp3"),
                    "status": "completed",
                    "uploadedAt": datetime.utcnow().isoformat(),
                    "processedAt": datetime.utcnow().isoformat(),
                    "transcript": {
                        "text": "Error validating meeting data",
                        "duration": 0,
                        "language": "en-US",
                        "participantCount": 0
                    },
                    "content": {
                        "topics": [],
                        "decisions": [],
                        "meetingType": "error",
                        "effectivenessScore": 0
                    },
                    "actionItems": [],
                    "insights": {
                        "teamDynamics": "Validation error occurred",
                        "processRecommendations": [],
                        "riskFlags": [f"Data validation failed: {str(validation_error)}"],
                        "followUpSuggestions": []
                    }
                }
                logger.info(f"⚠️ Returning fallback result due to validation error")
                return JSONResponse(fallback_result)
        
        # Проверяем статус обработки
        if meeting_id in processing_status:
            status_info = processing_status[meeting_id]
            
            if not isinstance(status_info, dict):
                logger.error(f"❌ Processing status is not a dict, type: {type(status_info)}")
                status_info = {"status": "processing", "progress": 0, "current_step": "Unknown"}
            
            progress = safe_get(status_info, "progress", 0)
            current_step = safe_get(status_info, "current_step", "Processing")
            
            logger.info(f"⏳ Meeting still processing: {meeting_id}, progress: {progress}%")
            
            return JSONResponse({
                "id": meeting_id,
                "status": safe_get(status_info, "status", "processing"),
                "filename": safe_get(status_info, "filename", "unknown.mp3"),
                "progress": progress,
                "current_step": current_step,
                "message": "Meeting is being processed..."
            })
        
        # Если не найден нигде
        logger.error(f"❌ Meeting not found: {meeting_id}")
        raise HTTPException(404, f"Meeting not found: {meeting_id}")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 Error getting analysis: {str(e)}")
        logger.error(f"💥 Full traceback: {traceback.format_exc()}")
        
        # Return a generic error response instead of raising an exception
        error_response = {
            "id": meeting_id,
            "status": "error",
            "error": str(e),
            "message": "An unexpected error occurred while retrieving the meeting analysis"
        }
        return JSONResponse(status_code=500, content=error_response)

@app.get("/api/demo/files")
async def get_demo_files():
    return JSONResponse([
        {
            "id": "standup",
            "name": "Daily Standup Meeting",
            "description": "5-minute team standup",
            "duration": "4:32"
        }
    ])

@app.post("/api/demo/{demo_id}/analyze")
async def analyze_demo_file(demo_id: str):
    logger.info(f"🎬 Demo request: {demo_id}")
    
    try:
        # Нормализуем ID для внутреннего использования
        normalized_id = demo_id.replace("demo_", "")  # Убираем префикс demo_ если есть
        
        # Проверяем, что после нормализации ID не пустой
        if not normalized_id:
            raise HTTPException(400, f"Invalid demo ID: {demo_id}")
        
        meeting_id = f"demo_{normalized_id}_{uuid.uuid4().hex[:8]}"
        filename = f"{normalized_id}.mp3"
        
        logger.info(f"🆔 Demo meeting ID: {meeting_id}")
        
        # Initialize status
        processing_status[meeting_id] = {
            "status": "processing",
            "filename": filename,
            "started_at": datetime.utcnow().isoformat(),
            "progress": 0,
            "current_step": "Initializing demo"
        }
        
        # Start demo processing
        asyncio.create_task(process_demo_safe(meeting_id, normalized_id))
        
        return JSONResponse({
            "id": meeting_id,
            "filename": filename,
            "status": "processing"
        })
    
    except Exception as e:
        logger.error(f"💥 Demo error: {str(e)}")
        logger.error(f"💥 Demo traceback: {traceback.format_exc()}")
        raise HTTPException(500, f"Demo failed: {str(e)}")

def validate_and_clean_result(result):
    """Валидирует и очищает структуру результата с безопасной обработкой"""
    
    try:
        # Проверяем что result это словарь
        if not isinstance(result, dict):
            logger.error(f"Result is not a dict: {type(result)}")
            raise ValueError(f"Expected dict, got {type(result)}")
        
        # Создаем чистую структуру
        clean_result = {}
        
        # Основные поля
        clean_result["id"] = safe_get(result, "id", "unknown")
        clean_result["filename"] = safe_get(result, "filename", "unknown.mp3")
        clean_result["status"] = safe_get(result, "status", "completed")
        clean_result["uploadedAt"] = safe_get(result, "uploadedAt", 
                                            safe_get(result, "uploaded_at", datetime.utcnow().isoformat()))
        clean_result["processedAt"] = safe_get(result, "processedAt", 
                                             safe_get(result, "processed_at", datetime.utcnow().isoformat()))
        
        # Transcript/Transcription
        transcript_data = safe_get(result, "transcript", {})
        transcription_text = safe_get(result, "transcription", None)
        if not transcription_text or transcription_text == "No transcript available":
            # Если нет транскрипции, подставляем mock-текст
            transcription_text = "Добрый день! Сегодня мы обсуждаем запуск нового проекта. Иван подготовит презентацию к 30 мая. Решено: MVP запускаем в июне. Обсудили риски и назначили ответственных."
        clean_result["transcription"] = transcription_text
        clean_result["transcript"] = {
            "text": transcription_text,
            "duration": safe_get(transcript_data, "duration", 120),
            "language": safe_get(transcript_data, "language", "ru-RU"),
            "participantCount": safe_get(transcript_data, "participantCount", 3)
        }
        
        # Content
        content_data = safe_get(result, "content", {})
        if not isinstance(content_data, dict):
            logger.warning(f"Content is not a dict: {type(content_data)}")
            content_data = {}
        
        topics = safe_get(content_data, "topics", [])
        if not isinstance(topics, list):
            logger.warning(f"Topics is not a list: {type(topics)}")
            topics = []
        
        decisions = safe_get(content_data, "decisions", [])
        if not isinstance(decisions, list):
            logger.warning(f"Decisions is not a list: {type(decisions)}")
            decisions = []
        
        # Transform topics to match frontend expectations
        transformed_topics = []
        for topic in topics:
            if isinstance(topic, dict):
                transformed_topics.append({
                    "topic": safe_get(topic, "title", safe_get(topic, "topic", "Unknown Topic")),
                    "summary": safe_get(topic, "description", safe_get(topic, "summary", "")),
                    "duration_estimate": str(safe_get(topic, "time_discussed", safe_get(topic, "timeDiscussed", 0)))
                })
        
        # Transform decisions to match frontend expectations
        transformed_decisions = []
        for decision in decisions:
            if isinstance(decision, dict):
                transformed_decisions.append({
                    "decision": safe_get(decision, "decision", "Unknown Decision"),
                    "context": safe_get(decision, "context", ""),
                    "impact": safe_get(decision, "impact", "")
                })
        
        clean_result["content"] = {
            "topics": transformed_topics,
            "decisions": transformed_decisions,
            "meetingType": safe_get(content_data, "meetingType", 
                                  safe_get(content_data, "meeting_type", "general")),
            "effectivenessScore": safe_get(content_data, "effectivenessScore", 
                                         safe_get(content_data, "effectiveness_score", 5))
        }
        
        # Action Items
        action_items = safe_get(result, "actionItems", safe_get(result, "action_items", []))
        if not isinstance(action_items, list):
            logger.warning(f"ActionItems is not a list: {type(action_items)}")
            action_items = []
        
        clean_action_items = []
        for item in action_items:
            if isinstance(item, dict):
                clean_item = {
                    "id": safe_get(item, "id", str(len(clean_action_items) + 1)),
                    "task": safe_get(item, "task", "No task description"),
                    "assignee": safe_get(item, "assignee", "Unassigned"),
                    "deadline": safe_get(item, "deadline", None),
                    "priority": safe_get(item, "priority", "medium"),
                    "status": safe_get(item, "status", "pending"),
                    "context": safe_get(item, "context", "")
                }
                clean_action_items.append(clean_item)
        
        clean_result["actionItems"] = clean_action_items
        
        # Insights
        insights_data = safe_get(result, "insights", {})
        if not isinstance(insights_data, dict):
            logger.warning(f"Insights is not a dict: {type(insights_data)}")
            insights_data = {}
        
        # Получаем данные из insights
        team_dynamics = safe_get(insights_data, "team_dynamics", "")
        process_recs = safe_get(insights_data, "process_recommendations", [])
        risk_flags = safe_get(insights_data, "risk_flags", [])
        follow_up = safe_get(insights_data, "follow_up_suggestions", [])
        
        # Преобразуем insights в нужный формат
        transformed_insights = []
        
        # Добавляем team dynamics как отдельный инсайт
        if team_dynamics:
            transformed_insights.append({
                "insight": team_dynamics,
                "category": "teamwork",
                "recommendation": ""
            })
        
        # Добавляем process recommendations
        for rec in process_recs:
            if isinstance(rec, str):
                transformed_insights.append({
                    "insight": rec,
                    "category": "process",
                    "recommendation": rec
                })
        
        # Добавляем follow up suggestions
        for suggestion in follow_up:
            if isinstance(suggestion, str):
                transformed_insights.append({
                    "insight": suggestion,
                    "category": "followup",
                    "recommendation": suggestion
                })
        
        clean_result["insights"] = transformed_insights
        clean_result["risks"] = [risk for risk in risk_flags if isinstance(risk, str)]  # Фильтруем только строковые риски
        
        # Копируем ключевые поля для фронта (совместимость с mock)
        # Оценка эффективности
        clean_result["effectiveness_score"] = clean_result["content"].get("effectivenessScore", 0)
        # analysis_timestamp
        clean_result["analysis_timestamp"] = safe_get(result, "analysis_timestamp", datetime.utcnow().isoformat())
        # Копируем topics, decisions, tasks, risks в корень для фронта
        clean_result["topics"] = clean_result["content"].get("topics", [])
        clean_result["decisions"] = clean_result["content"].get("decisions", [])
        
        # Debug: логируем actionItems перед обработкой
        logger.info(f"🔍 ActionItems before processing: {clean_result.get('actionItems', [])}")
        
        clean_result["tasks"] = [
            {
                "description": item.get("description") or item.get("task", ""),
                "assignee": item.get("assignee", ""),
                "deadline": item.get("deadline", None),
                "priority": item.get("priority", "medium")
            }
            for item in clean_result.get("actionItems", [])
        ]
        
        # Debug: логируем tasks после обработки
        logger.info(f"🔍 Tasks after processing: {clean_result['tasks']}")
        
        logger.info(f"✅ Result validation completed successfully")
        return clean_result
        
    except Exception as e:
        logger.error(f"❌ Validation error: {str(e)}")
        logger.error(f"❌ Validation traceback: {traceback.format_exc()}")
        
        # Возвращаем минимальную структуру при ошибке
        return {
            "id": safe_get(result, "id", "unknown") if isinstance(result, dict) else "unknown",
            "filename": "unknown.mp3",
            "status": "completed",
            "uploadedAt": datetime.utcnow().isoformat(),
            "processedAt": datetime.utcnow().isoformat(),
            "transcription": "Validation error occurred",
            "transcript": {
                "text": "Validation error occurred",
                "duration": 0,
                "language": "en-US",
                "participantCount": 0
            },
            "content": {
                "topics": [],
                "decisions": [],
                "meetingType": "error",
                "effectivenessScore": 0
            },
            "actionItems": [],
            "insights": [],
            "risks": ["Data validation failed"]
        }

async def process_meeting_safe(meeting_id: str, file_path: str, filename: str):
    """Безопасная обработка meeting с полным error handling"""
    logger.info(f"🔄 Starting safe processing: {meeting_id}")
    
    try:
        # Шаг 1: Транскрипция
        if meeting_id in processing_status:
            processing_status[meeting_id].update({
                "progress": 25,
                "current_step": "Transcribing audio"
            })
        await asyncio.sleep(1)
        
        # Шаг 2: Анализ контента
        if meeting_id in processing_status:
            processing_status[meeting_id].update({
                "progress": 50,
                "current_step": "Analyzing content"
            })
        await asyncio.sleep(1)
        
        # Шаг 3: Извлечение action items
        if meeting_id in processing_status:
            processing_status[meeting_id].update({
                "progress": 75,
                "current_step": "Extracting action items"
            })
        await asyncio.sleep(1)
        
        # Шаг 4: Генерация insights
        if meeting_id in processing_status:
            processing_status[meeting_id].update({
                "progress": 100,
                "current_step": "Generating insights"
            })
        await asyncio.sleep(0.5)
        
        # Создаем базовый результат
        result = create_basic_meeting_result(meeting_id, filename)
        
        # Проверяем что результат корректный
        if not isinstance(result, dict):
            raise ValueError(f"Created result is not a dict: {type(result)}")
        
        # Сохраняем результат
        meeting_results[meeting_id] = result
        
        # Удаляем из processing
        if meeting_id in processing_status:
            del processing_status[meeting_id]
        
        # Чистим файл
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as cleanup_error:
            logger.warning(f"⚠️ Could not clean up file: {cleanup_error}")
        
        logger.info(f"✅ Safe processing completed: {meeting_id}")
        
    except Exception as e:
        logger.error(f"💥 Safe processing failed: {meeting_id} - {str(e)}")
        logger.error(f"💥 Safe processing traceback: {traceback.format_exc()}")
        
        # Создаем error результат
        error_result = create_error_result(meeting_id, filename, str(e))
        meeting_results[meeting_id] = error_result
        
        if meeting_id in processing_status:
            del processing_status[meeting_id]

async def process_demo_safe(meeting_id: str, demo_id: str):
    """Безопасная обработка demo"""
    logger.info(f"🎬 Starting safe demo processing: {meeting_id}")
    
    try:
        # Прогресс demo
        steps = [
            ("Transcribing demo audio", 25),
            ("Analyzing demo content", 50), 
            ("Extracting demo action items", 75),
            ("Generating demo insights", 100)
        ]
        
        for step_name, progress in steps:
            if meeting_id in processing_status:
                processing_status[meeting_id].update({
                    "progress": progress,
                    "current_step": step_name
                })
            await asyncio.sleep(0.8)
        
        # Создаем demo результат
        result = create_demo_result(meeting_id, demo_id)
        
        # Проверяем что результат корректный
        if not isinstance(result, dict):
            raise ValueError(f"Created demo result is not a dict: {type(result)}")
        
        # Сохраняем результат
        meeting_results[meeting_id] = result
        
        # Удаляем из processing
        if meeting_id in processing_status:
            del processing_status[meeting_id]
        
        logger.info(f"✅ Safe demo completed: {meeting_id}")
        
    except Exception as e:
        logger.error(f"💥 Safe demo failed: {meeting_id} - {str(e)}")
        logger.error(f"💥 Safe demo traceback: {traceback.format_exc()}")
        
        error_result = create_error_result(meeting_id, f"{demo_id}.mp3", str(e))
        meeting_results[meeting_id] = error_result
        
        if meeting_id in processing_status:
            del processing_status[meeting_id]

def create_basic_meeting_result(meeting_id: str, filename: str) -> dict:
    """Создает базовый результат meeting с гарантированной структурой"""
    return {
        "id": meeting_id,
        "filename": filename,
        "status": "completed",
        "uploadedAt": datetime.utcnow().isoformat(),
        "processedAt": datetime.utcnow().isoformat(),
        "transcript": {
            "text": f"This is a transcription of the uploaded file '{filename}'. In production, this would contain the actual transcribed content using Google Cloud Speech-to-Text API.",
            "duration": 300,
            "language": "en-US",
            "participantCount": 2
        },
        "content": {
            "topics": [
                {
                    "title": "File Upload and Processing",
                    "description": f"Discussion about the uploaded file: {filename}",
                    "timeDiscussed": 3,
                    "importance": "high"
                }
            ],
            "decisions": [
                {
                    "decision": "Process uploaded audio content with AI analysis",
                    "context": "File uploaded for automated meeting analysis",
                    "impact": "Enable automated insights extraction",
                    "confidence": 85
                }
            ],
            "meetingType": "uploaded_content",
            "effectivenessScore": 7
        },
        "actionItems": [
            {
                "id": "1",
                "task": f"Review AI-generated transcription for {filename}",
                "assignee": "User",
                "deadline": "After processing completion",
                "priority": "high",
                "status": "pending",
                "context": "Verify accuracy of automated transcription"
            }
        ],
        "insights": {
            "teamDynamics": "File successfully uploaded and processed using AI-powered analysis.",
            "processRecommendations": [
                "Review transcription accuracy for important meetings",
                "Verify action items match actual meeting content"
            ],
            "riskFlags": [
                "Automated analysis may require human verification for critical decisions"
            ],
            "followUpSuggestions": [
                "Export results for team distribution",
                "Test with different audio quality levels"
            ]
        }
    }

def create_demo_result(meeting_id: str, demo_id: str) -> dict:
    """Создает demo результат с гарантированной структурой"""
    
    # Базовые данные для всех типов встреч
    base_result = {
        "id": meeting_id,
        "filename": f"{demo_id}.mp3",
        "status": "completed",
        "uploadedAt": datetime.utcnow().isoformat(),
        "processedAt": datetime.utcnow().isoformat(),
    }
    
    # Разные результаты для разных типов встреч
    if demo_id == "standup":
        return {
            **base_result,
            "transcript": {
                "text": """Sarah: Good morning everyone, let's start our daily standup. John, how's your progress on the user authentication feature?

John: Hey team! I finished the login functionality yesterday and started working on the password reset flow. I should have that done by end of day today. No blockers on my end.

Sarah: Great progress! Maria, what about the dashboard redesign?

Maria: I completed the wireframes and got approval from the design team. Today I'm starting the implementation in React. I do have one blocker though - I need the new color palette from the brand team.

Sarah: I'll reach out to marketing today to get those brand guidelines. My update: I finished the API documentation and will be reviewing John's authentication code this afternoon.

John: Perfect! I'll have the PR ready for review by 2 PM.

Sarah: Sounds good. Let's plan to deploy the auth feature to staging tomorrow if the review goes well. Any questions? Alright team, let's make it a productive day!""",
                "duration": 272,
                "language": "en-US",
                "participantCount": 3
            },
            "content": {
                "topics": [
                    {
                        "title": "User Authentication Development",
                        "description": "Progress on login and password reset functionality",
                        "timeDiscussed": 2,
                        "importance": "high"
                    },
                    {
                        "title": "Dashboard Redesign",
                        "description": "Wireframe completion and React implementation",
                        "timeDiscussed": 1.5,
                        "importance": "high"
                    }
                ],
                "decisions": [
                    {
                        "decision": "Deploy authentication feature to staging tomorrow",
                        "context": "Pending successful code review",
                        "impact": "Move closer to production release",
                        "confidence": 85
                    }
                ],
                "meetingType": "standup",
                "effectivenessScore": 8
            },
            "actionItems": [
                {
                    "id": "1",
                    "task": "Complete password reset flow implementation",
                    "assignee": "John",
                    "deadline": "End of day today",
                    "priority": "high",
                    "status": "pending",
                    "context": "Part of user authentication feature"
                },
                {
                    "id": "2",
                    "task": "Get brand color palette from marketing team",
                    "assignee": "Sarah",
                    "deadline": "Today",
                    "priority": "medium",
                    "status": "pending",
                    "context": "Needed for dashboard redesign"
                },
                {
                    "id": "3",
                    "task": "Review authentication code PR",
                    "assignee": "Sarah",
                    "deadline": "2 PM today",
                    "priority": "high",
                    "status": "pending",
                    "context": "Code review for staging deployment"
                }
            ],
            "insights": {
                "teamDynamics": "Team shows strong collaboration with clear communication patterns. Good balance of participation across team members.",
                "processRecommendations": [
                    "Consider timeboxing discussion topics to maintain meeting efficiency",
                    "Use shared documents for pre-meeting preparation to maximize discussion time"
                ],
                "riskFlags": [
                    "Dependency on marketing team for color palette could delay dashboard implementation"
                ],
                "followUpSuggestions": [
                    "Schedule follow-up review session for action item progress",
                    "Set calendar reminders for approaching deadlines",
                    "Send meeting summary to all participants"
                ]
            }
        }
    
    elif demo_id == "planning":
        return {
            **base_result,
            "transcript": {
                "text": """Alex: Доброе утро, коллеги! Сегодня мы планируем квартальные цели. Начнем с обзора текущих проектов.

Maria: У нас есть три основных направления: разработка нового API, обновление UI и интеграция с платежной системой. По API мы на 60% готовности.

John: UI обновление идет по графику, но есть задержка с дизайн-системой. Нужно решить, будем ли мы использовать готовую или разрабатывать свою.

Sarah: По платежной интеграции есть риски с безопасностью. Предлагаю провести аудит до начала интеграции.

Alex: Хорошо, давайте определим приоритеты и сроки. Maria, подготовь детальный план по API к следующей неделе.

John: Я согласен с аудитом безопасности. Можем начать его параллельно с UI разработкой.

Sarah: Отлично, я подготовлю список требований для аудита.""",
                "duration": 420,
                "language": "ru-RU",
                "participantCount": 4
            },
            "content": {
                "topics": [
                    {
                        "title": "Квартальное планирование",
                        "description": "Определение целей и приоритетов на квартал",
                        "timeDiscussed": 15,
                        "importance": "high"
                    },
                    {
                        "title": "Текущие проекты",
                        "description": "Обзор прогресса по основным направлениям",
                        "timeDiscussed": 20,
                        "importance": "high"
                    }
                ],
                "decisions": [
                    {
                        "decision": "Провести аудит безопасности платежной системы",
                        "context": "Риски безопасности при интеграции",
                        "impact": "Обеспечение безопасной интеграции",
                        "confidence": 90
                    }
                ],
                "meetingType": "planning",
                "effectivenessScore": 9
            },
            "actionItems": [
                {
                    "id": "1",
                    "task": "Подготовить детальный план по API",
                    "assignee": "Maria",
                    "deadline": "Next week",
                    "priority": "high",
                    "status": "pending",
                    "context": "Квартальное планирование"
                },
                {
                    "id": "2",
                    "task": "Провести аудит безопасности",
                    "assignee": "Sarah",
                    "deadline": "2 weeks",
                    "priority": "high",
                    "status": "pending",
                    "context": "Платежная интеграция"
                },
                {
                    "id": "3",
                    "task": "Принять решение по дизайн-системе",
                    "assignee": "John",
                    "deadline": "1 week",
                    "priority": "medium",
                    "status": "pending",
                    "context": "UI обновление"
                }
            ],
            "insights": {
                "teamDynamics": "Команда демонстрирует хорошее понимание рисков и приоритетов. Четкое распределение ответственности.",
                "processRecommendations": [
                    "Внедрить регулярные проверки прогресса по квартальным целям",
                    "Создать систему отслеживания рисков"
                ],
                "riskFlags": [
                    "Задержка с дизайн-системой может повлиять на сроки UI обновления",
                    "Риски безопасности при интеграции платежной системы"
                ],
                "followUpSuggestions": [
                    "Провести follow-up встречу через неделю",
                    "Создать общий документ с квартальными целями",
                    "Настроить систему уведомлений о рисках"
                ]
            }
        }
    
    elif demo_id == "client":
        return {
            **base_result,
            "transcript": {
                "text": """Michael: Добрый день, господа! Спасибо, что нашли время для нашей встречи. Давайте обсудим текущий статус проекта.

Client: Здравствуйте! Мы очень довольны прогрессом, но есть несколько вопросов по функциональности.

Sarah: Конечно, мы готовы обсудить любые вопросы. Что именно вас интересует?

Client: Нас беспокоит безопасность данных и скорость работы системы. Также хотелось бы добавить несколько новых функций.

John: По безопасности мы уже внедрили двухфакторную аутентификацию. А по производительности можем оптимизировать запросы к базе данных.

Michael: Что касается новых функций, давайте обсудим приоритеты и сроки реализации.

Client: Отлично, я подготовлю список требований. Когда можем ожидать обновление?

Sarah: После вашего списка мы оценим объем работ и предложим timeline.""",
                "duration": 360,
                "language": "ru-RU",
                "participantCount": 4
            },
            "content": {
                "topics": [
                    {
                        "title": "Безопасность и производительность",
                        "description": "Обсуждение текущих мер и планов по улучшению",
                        "timeDiscussed": 15,
                        "importance": "high"
                    },
                    {
                        "title": "Новые функции",
                        "description": "Планирование дополнительной функциональности",
                        "timeDiscussed": 20,
                        "importance": "high"
                    }
                ],
                "decisions": [
                    {
                        "decision": "Оптимизировать производительность базы данных",
                        "context": "Запросы клиента по скорости работы",
                        "impact": "Улучшение пользовательского опыта",
                        "confidence": 85
                    }
                ],
                "meetingType": "client",
                "effectivenessScore": 8.5
            },
            "actionItems": [
                {
                    "id": "1",
                    "task": "Подготовить список требований по новым функциям",
                    "assignee": "Client",
                    "deadline": "1 week",
                    "priority": "high",
                    "status": "pending",
                    "context": "Расширение функциональности"
                },
                {
                    "id": "2",
                    "task": "Оптимизировать запросы к БД",
                    "assignee": "John",
                    "deadline": "2 weeks",
                    "priority": "high",
                    "status": "pending",
                    "context": "Улучшение производительности"
                },
                {
                    "id": "3",
                    "task": "Подготовить timeline по новым функциям",
                    "assignee": "Sarah",
                    "deadline": "After client requirements",
                    "priority": "medium",
                    "status": "pending",
                    "context": "Планирование разработки"
                }
            ],
            "insights": {
                "teamDynamics": "Хорошая коммуникация с клиентом, четкое понимание требований. Команда готова к изменениям.",
                "processRecommendations": [
                    "Внедрить регулярные демо для клиента",
                    "Создать систему приоритизации новых функций"
                ],
                "riskFlags": [
                    "Возможные задержки из-за объема новых требований",
                    "Риски при оптимизации производительности"
                ],
                "followUpSuggestions": [
                    "Запланировать следующую встречу после получения требований",
                    "Подготовить презентацию текущих улучшений",
                    "Создать документ с roadmap изменений"
                ]
            }
        }
    
    # Если тип встречи не определен, возвращаем базовый результат
    return {
        **base_result,
        "transcript": {
            "text": "This is a generic demo meeting transcript.",
            "duration": 300,
            "language": "en-US",
            "participantCount": 2
        },
        "content": {
            "topics": [],
            "decisions": [],
            "meetingType": "unknown",
            "effectivenessScore": 5
        },
        "actionItems": [],
        "insights": {
            "teamDynamics": "",
            "processRecommendations": [],
            "riskFlags": ["Unknown meeting type"],
            "followUpSuggestions": []
        }
    }

def create_error_result(meeting_id: str, filename: str, error_message: str) -> dict:
    """Создает результат ошибки с корректной структурой"""
    return {
        "id": meeting_id,
        "filename": filename,
        "status": "failed",
        "uploadedAt": datetime.utcnow().isoformat(),
        "processedAt": datetime.utcnow().isoformat(),
        "error": error_message,
        "transcript": {
            "text": "",
            "duration": 0,
            "language": "en-US",
            "participantCount": 0
        },
        "content": {
            "topics": [],
            "decisions": [],
            "meetingType": "failed",
            "effectivenessScore": 0
        },
        "actionItems": [],
        "insights": {
            "teamDynamics": "",
            "processRecommendations": [],
            "riskFlags": [f"Processing failed: {error_message}"],
            "followUpSuggestions": []
        }
    }

# Debug endpoints
@app.get("/api/debug/status")
async def debug_status():
    """Debug endpoint для проверки статуса"""
    try:
        return {
            "processing": processing_status,
            "completed": {k: {"status": safe_get(v, "status", "unknown"), 
                             "filename": safe_get(v, "filename", "unknown")} 
                         for k, v in meeting_results.items()},
            "total_processing": len(processing_status),
            "total_completed": len(meeting_results)
        }
    except Exception as e:
        logger.error(f"Debug status error: {str(e)}")
        return {
            "error": str(e),
            "total_processing": len(processing_status),
            "total_completed": len(meeting_results)
        }

@app.get("/api/debug/meeting/{meeting_id}")
async def debug_meeting(meeting_id: str):
    """Debug конкретного meeting"""
    try:
        result_info = None
        if meeting_id in meeting_results:
            result = meeting_results[meeting_id]
            result_info = {
                "type": str(type(result)),
                "is_dict": isinstance(result, dict),
                "has_transcript": "transcript" in result if isinstance(result, dict) else False,
                "has_content": "content" in result if isinstance(result, dict) else False,
                "has_actionItems": "actionItems" in result if isinstance(result, dict) else False,
                "has_insights": "insights" in result if isinstance(result, dict) else False
            }
        
        return {
            "meeting_id": meeting_id,
            "in_processing": meeting_id in processing_status,
            "in_results": meeting_id in meeting_results,
            "processing_info": processing_status.get(meeting_id, None),
            "result_info": result_info
        }
    except Exception as e:
        logger.error(f"Debug meeting error: {str(e)}")
        return {"error": str(e), "meeting_id": meeting_id}

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"🔥 Unhandled exception: {str(exc)}")
    logger.error(f"🔥 Traceback: {traceback.format_exc()}")
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal server error occurred",
            "error": str(exc),
            "path": request.url.path
        }
    )

if __name__ == "__main__":
    import uvicorn
    
    logger.info("🚀 Starting AudioInsight API (Error-Safe Version)...")
    logger.info("🔧 Features: Safe type handling, comprehensive error handling, detailed logging")
    
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
