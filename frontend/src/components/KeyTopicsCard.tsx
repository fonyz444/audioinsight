import { FileText } from 'lucide-react'

interface KeyTopic {
  topic: string
  duration: string
  percent: number
}

interface KeyTopicsCardProps {
  topics: KeyTopic[]
}

export function KeyTopicsCard({ topics }: KeyTopicsCardProps) {
  return (
    <div className='card p-6 bg-white/10 backdrop-blur-lg border-white/20 h-full'>
      <h3 className='text-lg font-bold text-white mb-4 flex items-center'>
        <FileText className='mr-2 text-purple-400' />
        Key Topics
      </h3>
      <div className='space-y-4'>
        {topics.map((topic, idx) => (
          <div key={idx} className='mb-2'>
            <div className='flex justify-between items-center mb-1'>
              <span className='text-white font-medium'>{topic.topic}</span>
              <span className='text-gray-400 text-xs'>{topic.duration} • {topic.percent}%</span>
            </div>
            <div className='w-full h-2 bg-purple-900 rounded-full'>
              <div
                className='h-2 bg-purple-400 rounded-full transition-all'
                style={{ width: `${topic.percent}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
} 