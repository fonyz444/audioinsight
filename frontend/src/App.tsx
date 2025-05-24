import React, { useState, useRef, DragEvent } from 'react'
import { Toaster, toast } from 'react-hot-toast'
import {
	Upload,
	FileAudio,
	Loader2,
	CheckCircle,
	Download,
	Copy,
	Clock,
	Users,
	Target,
	Lightbulb,
	AlertTriangle,
	FileText,
	Play,
	Pause,
} from 'lucide-react'

// Типы для результатов анализа
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
	risks: string[]
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

	const downloadJSON = () => {
		if (!results) return

		const dataStr = JSON.stringify(results, null, 2)
		const dataBlob = new Blob([dataStr], { type: 'application/json' })
		const url = URL.createObjectURL(dataBlob)

		const link = document.createElement('a')
		link.href = url
		link.download = `meeting-analysis-${
			new Date().toISOString().split('T')[0]
		}.json`
		document.body.appendChild(link)
		link.click()
		document.body.removeChild(link)
		URL.revokeObjectURL(url)

		toast.success('JSON файл загружен')
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

	const formatScore = (score: number) => {
		if (score >= 8) return { text: 'Отлично', color: 'text-green-600' }
		if (score >= 6) return { text: 'Хорошо', color: 'text-blue-600' }
		if (score >= 4)
			return { text: 'Удовлетворительно', color: 'text-yellow-600' }
		return { text: 'Требует улучшения', color: 'text-red-600' }
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
						{/* Заголовок результатов */}
						<div className='text-center mb-8'>
							<CheckCircle className='mx-auto mb-4 text-green-400' size={48} />
							<h2 className='text-3xl font-bold text-white mb-2'>
								Анализ завершен
							</h2>
							<p className='text-gray-300'>
								Встреча проанализирована{' '}
								{new Date(results.analysis_timestamp).toLocaleString('ru-RU')}
							</p>
						</div>

						{/* Оценка эффективности */}
						<div className='card p-6 bg-white/10 backdrop-blur-lg border-white/20'>
							<div className='text-center'>
								<h3 className='text-xl font-bold text-white mb-4 flex items-center justify-center'>
									<Target className='mr-2' />
									Оценка эффективности встречи
								</h3>
								<div className='text-6xl font-bold mb-2 text-purple-400'>
									{typeof results?.effectiveness_score === 'number' ? results.effectiveness_score.toFixed(1) : '—'}/10
								</div>
								<div
									className={`text-xl font-medium ${
										formatScore(results.effectiveness_score).color
									}`}
								>
									{formatScore(results.effectiveness_score).text}
								</div>

								{/* Дополнительная информация */}
								<div className='flex justify-center space-x-8 mt-6 text-gray-300'>
									{results.meeting_duration_estimate && (
										<div className='flex items-center'>
											<Clock className='mr-2' size={16} />
											<span>{results.meeting_duration_estimate}</span>
										</div>
									)}
									{results.participant_count_estimate && (
										<div className='flex items-center'>
											<Users className='mr-2' size={16} />
											<span>
												~{results.participant_count_estimate} участников
											</span>
										</div>
									)}
								</div>
							</div>
						</div>

						{/* Сетка результатов */}
						<div className='grid lg:grid-cols-2 gap-6'>
							{/* Ключевые решения */}
							{Array.isArray(results.decisions) && results.decisions.length > 0 && (
								<div className='card p-6 bg-white/10 backdrop-blur-lg border-white/20'>
									<div className='flex items-center justify-between mb-4'>
										<h3 className='text-xl font-bold text-white flex items-center'>
											<CheckCircle className='mr-2 text-green-400' />
											Ключевые решения
										</h3>
										<button
											onClick={() =>
												copyToClipboard(
													results.decisions
														.map((d, i) => `${i + 1}. ${d.decision}`)
														.join('\n'),
													'Решения'
												)
											}
											className='p-2 hover:bg-white/20 rounded-lg transition-colors'
										>
											<Copy className='text-gray-400' size={16} />
										</button>
									</div>
									<div className='space-y-3'>
										{results.decisions.map((decision, index) => (
											<div key={index} className='p-3 bg-white/10 rounded-lg'>
												<p className='text-white font-medium'>
													{decision.decision}
												</p>
												{decision.context && (
													<p className='text-gray-400 text-sm mt-1'>
														Контекст: {decision.context}
													</p>
												)}
												{decision.impact && (
													<p className='text-blue-300 text-sm mt-1'>
														Влияние: {decision.impact}
													</p>
												)}
											</div>
										))}
									</div>
								</div>
							)}

							{/* Планы действий */}
							{Array.isArray(results.tasks) && results.tasks.length > 0 && (
								<div className='card p-6 bg-white/10 backdrop-blur-lg border-white/20'>
									<div className='flex items-center justify-between mb-4'>
										<h3 className='text-xl font-bold text-white flex items-center'>
											<Target className='mr-2 text-blue-400' />
											Планы действий
										</h3>
										<button
											onClick={() =>
												copyToClipboard(
													results.tasks
														.map(
															(t, i) =>
																`${i + 1}. ${t.description}${
																	t.assignee ? ` (${t.assignee})` : ''
																}${t.deadline ? ` - до ${t.deadline}` : ''}`
														)
														.join('\n'),
													'Задачи'
												)
											}
											className='p-2 hover:bg-white/20 rounded-lg transition-colors'
										>
											<Copy className='text-gray-400' size={16} />
										</button>
									</div>
									<div className='space-y-3'>
										{results.tasks.map((task, index) => (
											<div key={index} className='p-3 bg-white/10 rounded-lg'>
												<p className='text-white font-medium'>
													{task.description}
												</p>
												<div className='flex justify-between items-center mt-2 text-sm'>
													<span className='text-gray-400'>
														{task.assignee && `Ответственный: ${task.assignee}`}
													</span>
													<div className='flex space-x-2'>
														{task.deadline && (
															<span className='text-orange-300'>
																до {task.deadline}
															</span>
														)}
														{task.priority && (
															<span
																className={`px-2 py-1 rounded text-xs ${
																	task.priority === 'high'
																		? 'bg-red-500'
																		: task.priority === 'medium'
																		? 'bg-yellow-500'
																		: 'bg-green-500'
																}`}
															>
																{task.priority}
															</span>
														)}
													</div>
												</div>
											</div>
										))}
									</div>
								</div>
							)}

							{/* Обсуждаемые темы */}
							{Array.isArray(results.topics) && results.topics.length > 0 && (
								<div className='card p-6 bg-white/10 backdrop-blur-lg border-white/20'>
									<div className='flex items-center justify-between mb-4'>
										<h3 className='text-xl font-bold text-white flex items-center'>
											<FileText className='mr-2 text-purple-400' />
											Обсуждаемые темы
										</h3>
										<button
											onClick={() =>
												copyToClipboard(
													results.topics
														.map(
															(t, i) =>
																`${i + 1}. ${t.topic}${
																	t.summary ? `: ${t.summary}` : ''
																}`
														)
														.join('\n'),
													'Темы'
												)
											}
											className='p-2 hover:bg-white/20 rounded-lg transition-colors'
										>
											<Copy className='text-gray-400' size={16} />
										</button>
									</div>
									<div className='space-y-3'>
										{results.topics.map((topic, index) => (
											<div key={index} className='p-3 bg-white/10 rounded-lg'>
												<p className='text-white font-medium'>{topic.topic}</p>
												{topic.summary && (
													<p className='text-gray-400 text-sm mt-1'>
														{topic.summary}
													</p>
												)}
												{topic.duration_estimate && (
													<p className='text-blue-300 text-xs mt-1'>
														Длительность: {topic.duration_estimate}
													</p>
												)}
											</div>
										))}
									</div>
								</div>
							)}

							{/* Инсайты и рекомендации */}
							{Array.isArray(results.insights) && results.insights.length > 0 && (
								<div className='card p-6 bg-white/10 backdrop-blur-lg border-white/20'>
									<div className='flex items-center justify-between mb-4'>
										<h3 className='text-xl font-bold text-white flex items-center'>
											<Lightbulb className='mr-2 text-yellow-400' />
											Инсайты и рекомендации
										</h3>
										<button
											onClick={() =>
												copyToClipboard(
													results.insights
														.map(
															(i, idx) =>
																`${idx + 1}. ${i.insight}${
																	i.recommendation
																		? `\nРекомендация: ${i.recommendation}`
																		: ''
																}`
														)
														.join('\n\n'),
													'Инсайты'
												)
											}
											className='p-2 hover:bg-white/20 rounded-lg transition-colors'
										>
											<Copy className='text-gray-400' size={16} />
										</button>
									</div>
									<div className='space-y-3'>
										{results.insights.map((insight, index) => (
											<div key={index} className='p-3 bg-white/10 rounded-lg'>
												<p className='text-white font-medium'>
													{insight.insight}
												</p>
												{insight.recommendation && (
													<p className='text-green-300 text-sm mt-1'>
														Рекомендация: {insight.recommendation}
													</p>
												)}
												{insight.category && (
													<span className='inline-block mt-2 px-2 py-1 bg-blue-500/30 text-blue-300 text-xs rounded'>
														{insight.category}
													</span>
												)}
											</div>
										))}
									</div>
								</div>
							)}
						</div>

						{/* Потенциальные риски */}
						{Array.isArray(results.risks) && results.risks.length > 0 && (
							<div className='card p-6 bg-white/10 backdrop-blur-lg border-white/20'>
								<div className='flex items-center justify-between mb-4'>
									<h3 className='text-xl font-bold text-white flex items-center'>
										<AlertTriangle className='mr-2 text-red-400' />
										Потенциальные риски
									</h3>
									<button
										onClick={() =>
											copyToClipboard(
												results.risks
													.map((r, i) => `${i + 1}. ${r}`)
													.join('\n'),
												'Риски'
											)
										}
										className='p-2 hover:bg-white/20 rounded-lg transition-colors'
									>
										<Copy className='text-gray-400' size={16} />
									</button>
								</div>
								<div className='grid md:grid-cols-2 gap-3'>
									{results.risks.map((risk, index) => (
										<div
											key={index}
											className='p-3 bg-red-500/10 border border-red-500/30 rounded-lg'
										>
											<p className='text-red-300'>{risk}</p>
										</div>
									))}
								</div>
							</div>
						)}

						{/* Полная транскрипция */}
						<div className='card p-6 bg-white/10 backdrop-blur-lg border-white/20'>
							<div className='flex items-center justify-between mb-4'>
								<h3 className='text-xl font-bold text-white flex items-center'>
									<FileText className='mr-2' />
									Полная транскрипция
								</h3>
								<button
									onClick={() =>
										copyToClipboard(results.transcription, 'Транскрипция')
									}
									className='p-2 hover:bg-white/20 rounded-lg transition-colors'
								>
									<Copy className='text-gray-400' size={16} />
								</button>
							</div>
							<div className='bg-white/10 rounded-lg p-4 max-h-96 overflow-y-auto custom-scrollbar'>
								<p className='text-gray-300 whitespace-pre-wrap leading-relaxed'>
									{results.transcription}
								</p>
							</div>
						</div>

						{/* Кнопки скачивания */}
						<div className='card p-6 bg-white/10 backdrop-blur-lg border-white/20'>
							<h3 className='text-xl font-bold text-white mb-4 flex items-center'>
								<Download className='mr-2' />
								Экспорт результатов
							</h3>
							<div className='flex space-x-4'>
								<button
									onClick={downloadJSON}
									className='btn-primary flex items-center'
								>
									<Download className='mr-2' size={16} />
									Скачать JSON
								</button>
								<button
									onClick={downloadTextReport}
									className='btn-secondary flex items-center'
								>
									<FileText className='mr-2' size={16} />
									Скачать отчет (TXT)
								</button>
							</div>
							<p className='text-gray-400 text-sm mt-3'>
								JSON содержит все структурированные данные. Текстовый отчет
								удобен для печати или отправки по email.
							</p>
						</div>
					</div>
				)}
			</div>
		</div>
	)
}

export default App
