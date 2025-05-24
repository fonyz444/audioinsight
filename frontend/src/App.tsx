import React, { useState, useRef, DragEvent } from 'react'
import { Toaster, toast } from 'react-hot-toast'
import {
	Upload,
	FileAudio,
	Loader2,
	Target,
	Play,
	Pause,
} from 'lucide-react'
import { MeetingHeader } from './components/MeetingHeader'
import { EffectivenessCard } from './components/EffectivenessCard'
import { RisksCard } from './components/RisksCard'
import { ActionItemsCard } from './components/ActionItemsCard'
import { KeyTopicsCard } from './components/KeyTopicsCard'
import { TranscriptCard } from './components/TranscriptCard'

// Типы для результатов анализа
interface RiskObj {
	description: string
	impact: 'High' | 'Medium' | 'Low'
}

interface Task {
	description: string
	assignee?: string
	deadline?: string
	priority?: string
}

interface Decision {
	decision: string
	context?: string
	impact?: string
}

interface Topic {
	topic: string
	summary?: string
	duration_estimate?: string
}

interface Insight {
	insight: string
	category?: string
	recommendation?: string
}

interface AnalysisResults {
	transcription: string
	analysis_timestamp: string
	tasks: Task[]
	decisions: Decision[]
	topics: Topic[]
	insights: Insight[]
	effectiveness_score: number
	risks: (string | RiskObj)[]
	meeting_duration_estimate?: string
	participant_count_estimate?: number
}

// interface ApiResponse {
// 	success: boolean
// 	message: string
// 	filename: string
// 	results_file: string
// 	results: AnalysisResults
// }

const API_BASE_URL = 'http://localhost:8000'

const demoMockData: Record<string, Partial<AnalysisResults>> = {
	demo_standup: {
		effectiveness_score: 7.5,
		tasks: [
			{ description: 'Finalize UI designs for the dashboard', assignee: 'Sarah Johnson', deadline: 'June 20, 2025', priority: 'High' },
			{ description: 'Set up integration tests for the API', assignee: 'Michael Wong', deadline: 'June 22, 2025', priority: 'Medium' },
			{ description: 'Prepare demo for stakeholder meeting', assignee: 'Alex Chen', deadline: 'June 25, 2025', priority: 'High' },
		],
		risks: [
			{ description: 'Potential delay in the API integration due to third-party service issues', impact: 'High' as const },
			{ description: 'Limited testing resources might affect quality assurance', impact: 'Medium' as const },
		] as (string | { description: string; impact: 'High' | 'Medium' | 'Low' })[],
		topics: [
			{ topic: 'UI Design Review', duration_estimate: '15 mins', summary: 'Discussed final UI tweaks and feedback.' },
			{ topic: 'API Development', duration_estimate: '12 mins', summary: 'Reviewed API progress and blockers.' },
			{ topic: 'Testing Strategy', duration_estimate: '10 mins', summary: 'Outlined QA plan and responsibilities.' },
			{ topic: 'Release Planning', duration_estimate: '8 mins', summary: 'Set tentative release dates.' },
		],
		analysis_timestamp: new Date().toISOString(),
		participant_count_estimate: 4,
		meeting_duration_estimate: '45 minutes',
	},
	demo_client: {
		effectiveness_score: 8.2,
		tasks: [
			{ description: 'Send updated proposal to client', assignee: 'Olga Petrova', deadline: 'June 18, 2025', priority: 'High' },
			{ description: 'Schedule follow-up call', assignee: 'Ivan Smirnov', deadline: 'June 19, 2025', priority: 'Medium' },
		],
		risks: [
			{ description: 'Client budget constraints may impact scope', impact: 'High' as const },
		] as (string | { description: string; impact: 'High' | 'Medium' | 'Low' })[],
		topics: [
			{ topic: 'Requirements Discussion', duration_estimate: '20 mins', summary: 'Clarified client needs.' },
			{ topic: 'Timeline Alignment', duration_estimate: '10 mins', summary: 'Agreed on key milestones.' },
		],
		analysis_timestamp: new Date().toISOString(),
		participant_count_estimate: 3,
		meeting_duration_estimate: '35 minutes',
	},
	demo_planning: {
		effectiveness_score: 6.8,
		tasks: [
			{ description: 'Break down sprint stories', assignee: 'Dmitry Ivanov', deadline: 'June 21, 2025', priority: 'Medium' },
			{ description: 'Assign tasks to team members', assignee: 'Elena Volkova', deadline: 'June 21, 2025', priority: 'Low' },
		],
		risks: [
			{ description: 'Unclear requirements for some stories', impact: 'Medium' as const },
			{ description: 'Resource availability during sprint', impact: 'Low' as const },
		] as (string | { description: string; impact: 'High' | 'Medium' | 'Low' })[],
		topics: [
			{ topic: 'Sprint Goals', duration_estimate: '10 mins', summary: 'Defined main objectives.' },
			{ topic: 'Task Assignment', duration_estimate: '15 mins', summary: 'Distributed work among team.' },
		],
		analysis_timestamp: new Date().toISOString(),
		participant_count_estimate: 5,
		meeting_duration_estimate: '40 minutes',
	},
}

function App() {
	const [file, setFile] = useState<File | null>(null)
	const [isAnalyzing, setIsAnalyzing] = useState(false)
	const [results, setResults] = useState<AnalysisResults | null>(null)
	const [isDragOver, setIsDragOver] = useState(false)
	const [audioUrl, setAudioUrl] = useState<string | null>(null)
	const [isPlaying, setIsPlaying] = useState(false)
	const fileInputRef = useRef<HTMLInputElement>(null)
	const audioRef = useRef<HTMLAudioElement>(null)

	// Демо файлы
	const demoFiles = [
		{
			name: 'Daily Standup',
			filename: 'demo_standup.mp3',
			description: 'Ежедневная планерка команды',
		},
		{
			name: 'Client Meeting',
			filename: 'demo_client.mp3',
			description: 'Встреча с клиентом',
		},
		{
			name: 'Sprint Planning',
			filename: 'demo_planning.mp3',
			description: 'Планирование спринта',
		},
	]

	const handleFileSelect = (selectedFile: File) => {
		setFile(selectedFile)
		setResults(null)

		// Создаем URL для аудиоплеера
		if (audioUrl) {
			URL.revokeObjectURL(audioUrl)
		}
		const newAudioUrl = URL.createObjectURL(selectedFile)
		setAudioUrl(newAudioUrl)

		toast.success(`Файл выбран: ${selectedFile.name}`)
	}

	const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
		e.preventDefault()
		setIsDragOver(true)
	}

	const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
		e.preventDefault()
		setIsDragOver(false)
	}

	const handleDrop = (e: DragEvent<HTMLDivElement>) => {
		e.preventDefault()
		setIsDragOver(false)

		const droppedFiles = Array.from(e.dataTransfer.files)
		if (droppedFiles.length > 0) {
			const droppedFile = droppedFiles[0]
			if (isAudioOrVideoFile(droppedFile)) {
				handleFileSelect(droppedFile)
			} else {
				toast.error('Пожалуйста, выберите аудио или видео файл')
			}
		}
	}

	const isAudioOrVideoFile = (file: File): boolean => {
		return file.type.startsWith('audio/') || file.type.startsWith('video/')
	}

	const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
		const selectedFile = e.target.files?.[0]
		if (selectedFile) {
			if (isAudioOrVideoFile(selectedFile)) {
				handleFileSelect(selectedFile)
			} else {
				toast.error('Пожалуйста, выберите аудио или видео файл')
			}
		}
	}

	const handleDemoFileSelect = async (demoFile: {
		name: string
		filename: string
		description: string
	}) => {
		try {
			setIsAnalyzing(true)
			toast.loading(`Загружаю демо-файл: ${demoFile.name}...`)

			// Мок-ответ для демо
			const demoId = demoFile.filename.split('.')[0]
			const mock = demoMockData[demoId]
			if (mock) {
				setTimeout(() => {
					setResults({
						transcription: `Demo transcript for ${demoFile.name}.\nSarah: Good morning everyone, let's start our daily standup...`,
						analysis_timestamp: mock.analysis_timestamp || new Date().toISOString(),
						tasks: mock.tasks || [],
						decisions: [],
						topics: mock.topics || [],
						insights: [],
						effectiveness_score: mock.effectiveness_score ?? 0,
						risks: mock.risks || [],
						meeting_duration_estimate: mock.meeting_duration_estimate,
						participant_count_estimate: mock.participant_count_estimate,
					})
					setIsAnalyzing(false)
					toast.dismiss()
					toast.success('Анализ демо-файла завершен!')
				}, 1000)
				return
			}

			// The /api/demo/{demo_id}/analyze endpoint directly starts processing
			const response = await fetch(
				`${API_BASE_URL}/api/demo/${demoFile.filename.split('.')[0]}/analyze`,
				{
					// Use demo_id, e.g., 'standup'
					method: 'POST',
				}
			)

			if (!response.ok) {
				const errorData = await response.json()
				throw new Error(errorData.detail || 'Ошибка запуска демо-анализа')
			}

			const initialResponse: { id: string; status: string; verification: any } =
				await response.json()

			// Set a mock file object for UI consistency if needed, though not strictly necessary for demo
			const mockFile = new File([''], demoFile.filename, { type: 'audio/mpeg' })
			setFile(mockFile)
			if (audioUrl) {
				URL.revokeObjectURL(audioUrl)
			}
			// For demo files, we might not have a direct audio URL for the player unless the backend serves it.
			// If your /results/{id} provides a playable URL, you could use that.
			// For now, let's assume no player for demo files after analysis starts.
			setAudioUrl(null)

			toast.dismiss()
			toast.success(`Демо-файл ${demoFile.name} отправлен на анализ.`)

			if (initialResponse.status === 'processing') {
				await pollForResults(initialResponse.id)
			} else if (initialResponse.status === 'completed') {
				// This path is less likely for async demo processing but handle it
				const meetingResults = await fetch(
					`${API_BASE_URL}/api/meetings/${initialResponse.id}`
				)
				if (!meetingResults.ok) {
					const errorData = await meetingResults.json()
					throw new Error(
						errorData.detail || 'Ошибка получения результатов демо'
					)
				}
				const fullResults: AnalysisResults = await meetingResults.json()
				setResults(fullResults)
				toast.dismiss()
				toast.success('Анализ демо-файла завершен!')
			} else {
				throw new Error(
					initialResponse.status || 'Ошибка после запуска демо-анализа'
				)
			}
		} catch (error) {
			toast.dismiss()
			toast.error(
				`Ошибка демо-анализа: ${
					error instanceof Error ? error.message : 'Неизвестная ошибка'
				}`
			)
			console.error('Demo file error:', error)
		} finally {
			setIsAnalyzing(false)
		}
	}

	const analyzeFile = async (fileToAnalyze: File = file!) => {
		if (!fileToAnalyze) {
			toast.error('Выберите файл для анализа')
			return
		}

		setIsAnalyzing(true)
		toast.loading('Анализирую запись встречи...')

		try {
			const formData = new FormData()
			formData.append('file', fileToAnalyze)

			const response = await fetch(`${API_BASE_URL}/api/meetings/upload`, {
				method: 'POST',
				body: formData,
			})

			if (!response.ok) {
				const errorData = await response.json()
				throw new Error(errorData.detail || 'Ошибка анализа')
			}

			const initialResponse: { id: string; status: string; verification: any } =
				await response.json()

			if (initialResponse.status === 'processing') {
				toast.loading('Файл загружен, идет обработка...')
				await pollForResults(initialResponse.id)
			} else if (initialResponse.status === 'completed') {
				const meetingResults = await fetch(
					`${API_BASE_URL}/api/meetings/${initialResponse.id}`
				)
				if (!meetingResults.ok) {
					const errorData = await meetingResults.json()
					throw new Error(errorData.detail || 'Ошибка получения результатов')
				}
				const fullResults: AnalysisResults = await meetingResults.json()
				setResults(fullResults)
				toast.dismiss()
				toast.success('Анализ завершен!')
			} else {
				throw new Error(initialResponse.status || 'Ошибка после загрузки файла')
			}
		} catch (error) {
			toast.dismiss()
			toast.error(
				`Ошибка анализа: ${
					error instanceof Error ? error.message : 'Неизвестная ошибка'
				}`
			)
			console.error('Analysis error:', error)
		} finally {
			setIsAnalyzing(false)
		}
	}

	const pollForResults = async (meetingId: string) => {
		let attempts = 0
		const maxAttempts = 30 // Poll for 5 minutes (30 attempts * 10 seconds)
		const interval = 10000 // 10 seconds

		while (attempts < maxAttempts) {
			try {
				await new Promise(resolve => setTimeout(resolve, interval)) // Wait
				attempts++
				// ... остальной код опроса
				const response = await fetch(
					`${API_BASE_URL}/api/meetings/${meetingId}`
				)
				if (!response.ok) {
					// If meeting not found yet, or other server error, continue polling
					console.warn(
						`Polling attempt ${attempts} for ${meetingId} failed with status ${response.status}`
					)
					if (response.status === 404 && attempts < 5) {
						// Be more patient for 404 initially
						continue
					} else if (response.status === 404) {
						throw new Error(
							'Результаты анализа не найдены после длительного ожидания.'
						)
					}
					const errorData = await response
						.json()
						.catch(() => ({ detail: 'Ошибка сервера при опросе' }))
					throw new Error(
						errorData.detail ||
							`Ошибка при получении статуса: ${response.status}`
					)
				}

				const data = await response.json()

				if (data.status === 'completed') {
					// Универсальная обработка: поддержка data.transcription и data.results.transcription
					const analysis = data.transcription ? data : data.results
					if (analysis && analysis.transcription) {
						setResults(analysis as AnalysisResults)
						toast.dismiss()
						toast.success('Анализ завершен!')
						return
					} else {
						console.error(
							'Status is completed, but results structure is not as expected.',
							data
						)
						throw new Error('Структура результатов неполная после завершения.')
					}
				} else if (data.status === 'failed') {
					throw new Error('Обработка файла завершилась с ошибкой на сервере.')
				}
				// If status is still 'processing', continue loop
				toast.dismiss()
				toast.loading(`Обработка... (${attempts}/${maxAttempts})`)
			} catch (error) {
				toast.dismiss()
				toast.error(
					`Ошибка получения результатов: ${
						error instanceof Error ? error.message : 'Неизвестная ошибка'
					}`
				)
				console.error('Polling error:', error)
				return // Stop polling on error
			}
		}
		toast.dismiss()
		toast.error(
			'Время ожидания результатов истекло. Пожалуйста, проверьте позже.'
		)
	}

	const copyToClipboard = (text: string, label: string) => {
		navigator.clipboard
			.writeText(text)
			.then(() => {
				toast.success(`${label} скопирован в буфер обмена`)
			})
			.catch(() => {
				toast.error('Ошибка копирования')
			})
	}

	const downloadTextReport = () => {
		if (!results) return

		let report = `ОТЧЕТ ПО АНАЛИЗУ ВСТРЕЧИ\n`
		report += `Дата анализа: ${new Date(
			results.analysis_timestamp
		).toLocaleString('ru-RU')}\n`
		report += `Оценка эффективности: ${typeof results?.effectiveness_score === 'number' ? results.effectiveness_score.toFixed(1) : '—'}/10\n\n`

		if (Array.isArray(results.decisions) && results.decisions.length > 0) {
			report += `КЛЮЧЕВЫЕ РЕШЕНИЯ:\n`
			results.decisions.forEach((decision, index) => {
				report += `${index + 1}. ${decision.decision}\n`
				if (decision.context) report += `   Контекст: ${decision.context}\n`
				if (decision.impact) report += `   Влияние: ${decision.impact}\n`
			})
			report += `\n`
		}

		if (Array.isArray(results.tasks) && results.tasks.length > 0) {
			report += `ПЛАНЫ ДЕЙСТВИЙ:\n`
			results.tasks.forEach((task, index) => {
				report += `${index + 1}. ${task.description}\n`
				if (task.assignee) report += `   Ответственный: ${task.assignee}\n`
				if (task.deadline) report += `   Срок: ${task.deadline}\n`
				if (task.priority) report += `   Приоритет: ${task.priority}\n`
			})
			report += `\n`
		}

		if (Array.isArray(results.topics) && results.topics.length > 0) {
			report += `ОБСУЖДАЕМЫЕ ТЕМЫ:\n`
			results.topics.forEach((topic, index) => {
				report += `${index + 1}. ${topic.topic}\n`
				if (topic.summary) report += `   ${topic.summary}\n`
			})
			report += `\n`
		}

		if (Array.isArray(results.insights) && results.insights.length > 0) {
			report += `ИНСАЙТЫ И РЕКОМЕНДАЦИИ:\n`
			results.insights.forEach((insight, index) => {
				report += `${index + 1}. ${insight.insight}\n`
				if (insight.recommendation)
					report += `   Рекомендация: ${insight.recommendation}\n`
			})
			report += `\n`
		}

		if (Array.isArray(results.risks) && results.risks.length > 0) {
			report += `ПОТЕНЦИАЛЬНЫЕ РИСКИ:\n`
			results.risks.forEach((risk, index) => {
				report += `${index + 1}. ${risk}\n`
			})
			report += `\n`
		}

		report += `ПОЛНАЯ ТРАНСКРИПЦИЯ:\n${results.transcription}`

		const dataBlob = new Blob([report], { type: 'text/plain;charset=utf-8' })
		const url = URL.createObjectURL(dataBlob)

		const link = document.createElement('a')
		link.href = url
		link.download = `meeting-analysis-${
			new Date().toISOString().split('T')[0]
		}.txt`
		document.body.appendChild(link)
		link.click()
		document.body.removeChild(link)
		URL.revokeObjectURL(url)

		toast.success('Текстовый отчет загружен')
	}

	const toggleAudioPlayback = () => {
		if (!audioRef.current) return

		if (isPlaying) {
			audioRef.current.pause()
		} else {
			audioRef.current.play()
		}
		setIsPlaying(!isPlaying)
	}

	return (
		<div className='min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900'>
			<Toaster position='top-right' />

			{/* Заголовок */}
			<div className='container mx-auto px-4 py-8'>
				<div className='text-center mb-12'>
					<h1 className='text-5xl font-bold text-white mb-4'>
						Audio<span className='text-purple-400'>Insight</span>
					</h1>
					<p className='text-xl text-gray-300 max-w-2xl mx-auto'>
						Преобразуйте записи встреч в структурированные планы действий с
						помощью искусственного интеллекта
					</p>
				</div>

				{/* Область загрузки файлов */}
				<div className='max-w-4xl mx-auto mb-8'>
					<div className='card p-8 bg-white/10 backdrop-blur-lg border-white/20'>
						<h2 className='text-2xl font-bold text-white mb-6 flex items-center'>
							<Upload className='mr-3' />
							Загрузка аудиофайла
						</h2>

						{/* Drag & Drop область */}
						{!file && (
							<div
								className={`border-2 border-dashed rounded-xl p-8 text-center transition-all duration-300 ${
									isDragOver
										? 'border-purple-400 bg-purple-400/20'
										: 'border-gray-400 hover:border-purple-400 hover:bg-purple-400/10'
								}`}
								onDragOver={handleDragOver}
								onDragLeave={handleDragLeave}
								onDrop={handleDrop}
							>
								<FileAudio className='mx-auto mb-4 text-gray-400' size={48} />
								<p className='text-lg text-gray-300 mb-4'>
									Перетащите аудио или видео файл сюда
								</p>
								<p className='text-sm text-gray-400 mb-6'>
									Поддерживаемые форматы: MP3, MP4, WAV, M4A, OGG, FLAC, WEBM и
									другие
								</p>
								<button
									onClick={() => fileInputRef.current?.click()}
									className='btn-primary'
									disabled={isAnalyzing}
								>
									Выбрать файл
								</button>
								<input
									ref={fileInputRef}
									type='file'
									accept='audio/*,video/*'
									onChange={handleFileInputChange}
									className='hidden'
								/>
							</div>
						)}

						{/* Выбранный файл */}
						{file && (
							<div className='mt-6 p-4 bg-white/10 rounded-lg'>
								<div className='flex items-center justify-between'>
									<div className='flex items-center'>
										<FileAudio className='mr-3 text-purple-400' size={24} />
										<div>
											<p className='text-white font-medium'>{file.name}</p>
											<p className='text-gray-400 text-sm'>
												{typeof file?.size === 'number' ? (file.size / (1024 * 1024)).toFixed(2) : '—'} МБ
											</p>
										</div>
									</div>

									{!isAnalyzing && (
										<button
											onClick={() => analyzeFile()}
											className='btn-primary flex items-center'
										>
											<Target className='mr-2' size={16} />
											Анализировать
										</button>
									)}
								</div>

								{/* Аудиоплеер */}
								{audioUrl && (
									<div className='mt-4 flex items-center space-x-4'>
										<button
											onClick={toggleAudioPlayback}
											className='p-2 bg-purple-600 hover:bg-purple-700 rounded-full text-white transition-colors'
										>
											{isPlaying ? <Pause size={16} /> : <Play size={16} />}
										</button>
										<audio
											ref={audioRef}
											src={audioUrl}
											onPlay={() => setIsPlaying(true)}
											onPause={() => setIsPlaying(false)}
											onEnded={() => setIsPlaying(false)}
											className='flex-1'
											controls
										/>
									</div>
								)}
							</div>
						)}

						{/* Индикатор загрузки */}
						{isAnalyzing && (
							<div className='mt-6 p-4 bg-blue-500/20 rounded-lg'>
								<div className='flex items-center'>
									<Loader2
										className='animate-spin mr-3 text-blue-400'
										size={24}
									/>
									<div>
										<p className='text-white font-medium'>
											Анализирую запись встречи...
										</p>
										<p className='text-gray-400 text-sm'>
											Это может занять несколько минут в зависимости от длины
											записи
										</p>
									</div>
								</div>
							</div>
						)}
					</div>
				</div>

				{/* Демо-файлы */}
				<div className='max-w-4xl mx-auto mb-8'>
					<div className='card p-6 bg-white/10 backdrop-blur-lg border-white/20'>
						<h3 className='text-xl font-bold text-white mb-4'>
							Быстрый тест с демо-файлами
						</h3>
						<div className='grid md:grid-cols-3 gap-4'>
							{demoFiles.map(demo => (
								<button
									key={demo.filename}
									onClick={() => handleDemoFileSelect(demo)}
									disabled={isAnalyzing}
									className='p-4 bg-white/10 hover:bg-white/20 rounded-lg transition-colors border border-white/20 hover:border-purple-400 disabled:opacity-50 disabled:cursor-not-allowed'
								>
									<h4 className='text-white font-medium mb-2'>{demo.name}</h4>
									<p className='text-gray-400 text-sm'>{demo.description}</p>
								</button>
							))}
						</div>
					</div>
				</div>

				{/* Результаты анализа */}
				{results && (
					<div className='max-w-6xl mx-auto space-y-6 animate-fade-in'>
						<MeetingHeader
							title='Product Team Weekly Sync'
							date={new Date(results.analysis_timestamp).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
							duration={results.meeting_duration_estimate || '—'}
							participants={results.participant_count_estimate || 4}
							onExport={downloadTextReport}
						/>
						<div className='grid md:grid-cols-2 gap-6 mb-6'>
							<EffectivenessCard
								score={results.effectiveness_score}
								duration={results.meeting_duration_estimate}
								participants={results.participant_count_estimate}
							/>
							<RisksCard
								risks={Array.isArray(results.risks)
									? results.risks.map((risk: any) =>
											typeof risk === 'string'
												? { description: risk, impact: 'Medium' as const }
												: {
													description: risk.description,
													impact:
														risk.impact === 'High' || risk.impact === 'Low'
															? risk.impact
															: 'Medium',
												}
									)
									: []}
							/>
						</div>
						<div className='grid md:grid-cols-2 gap-6 mb-6'>
							<ActionItemsCard
								items={Array.isArray(results.tasks)
									? results.tasks.map(task => ({
										...task,
										priority:
											task.priority === 'High' || task.priority === 'Low'
												? task.priority
												: 'Medium',
									}))
									: []}
							/>
							<KeyTopicsCard
								topics={Array.isArray(results.topics) ? results.topics.map(topic => ({
									topic: topic.topic,
									duration: topic.duration_estimate || '—',
									percent: 25 // TODO: вычислять процент по длительности
								})) : []}
							/>
						</div>
						<TranscriptCard
							transcript={results.transcription}
							onCopy={() => copyToClipboard(results.transcription, 'Транскрипция')}
						/>
					</div>
				)}
			</div>
		</div>
	)
}

export default App
