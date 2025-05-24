import React from 'react'
import { Download } from 'lucide-react'

interface MeetingHeaderProps {
  title: string
  date: string
  duration: string
  participants: number
  onExport: () => void
}

export function MeetingHeader({ title, date, duration, participants, onExport }: MeetingHeaderProps) {
  return (
    <div className='flex flex-col md:flex-row md:items-center md:justify-between mb-8'>
      <div>
        <h2 className='text-2xl md:text-3xl font-bold text-white mb-1'>{title}</h2>
        <div className='flex flex-wrap items-center text-gray-400 text-sm space-x-4'>
          <span>{date}</span>
          <span>•</span>
          <span>{duration}</span>
          <span>•</span>
          <span>{participants} участников</span>
        </div>
      </div>
      <button
        onClick={onExport}
        className='mt-4 md:mt-0 flex items-center px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition-colors shadow-lg'
      >
        <Download className='mr-2' size={18} />
        Экспорт отчета
      </button>
    </div>
  )
} 