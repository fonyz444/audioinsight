import { Target, Clock, Users } from 'lucide-react'

interface EffectivenessCardProps {
  score?: number
  duration?: string
  participants?: number
}

function getScoreLabel(score: number | undefined) {
  if (typeof score !== 'number') return { text: 'Нет данных', color: 'text-gray-400' }
  if (score >= 8) return { text: 'Отлично', color: 'text-green-400' }
  if (score >= 6) return { text: 'Хорошо', color: 'text-blue-400' }
  if (score >= 4) return { text: 'Удовлетворительно', color: 'text-yellow-400' }
  return { text: 'Требует улучшения', color: 'text-red-400' }
}

export function EffectivenessCard({ score, duration, participants }: EffectivenessCardProps) {
  const label = getScoreLabel(score)
  return (
    <div className='card p-6 bg-white/10 backdrop-blur-lg border-white/20 h-full'>
      <h3 className='text-lg font-bold text-white mb-4 flex items-center'>
        <Target className='mr-2' />
        Meeting Effectiveness
      </h3>
      <div className='text-5xl font-bold mb-2 text-purple-400'>
        {typeof score === 'number' ? score.toFixed(1) : '—'}
        <span className='text-xl text-gray-300'>/10</span>
      </div>
      <div className={`text-lg font-medium ${label.color}`}>{label.text}</div>
      <div className='flex justify-center space-x-6 mt-6 text-gray-300'>
        {duration && (
          <div className='flex items-center'>
            <Clock className='mr-2' size={16} />
            <span>{duration}</span>
          </div>
        )}
        {participants && (
          <div className='flex items-center'>
            <Users className='mr-2' size={16} />
            <span>~{participants} участников</span>
          </div>
        )}
      </div>
    </div>
  )
} 