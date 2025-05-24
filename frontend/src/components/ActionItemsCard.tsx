import { CheckCircle } from 'lucide-react'

interface ActionItem {
  description: string
  assignee?: string
  deadline?: string
  priority?: 'High' | 'Medium' | 'Low'
}

interface ActionItemsCardProps {
  items: ActionItem[]
}

const priorityColors = {
  High: 'bg-red-500 text-white',
  Medium: 'bg-yellow-400 text-gray-900',
  Low: 'bg-green-400 text-gray-900',
}

export function ActionItemsCard({ items }: ActionItemsCardProps) {
  return (
    <div className='card p-6 bg-white/10 backdrop-blur-lg border-white/20 h-full'>
      <h3 className='text-lg font-bold text-white mb-4 flex items-center'>
        <CheckCircle className='mr-2 text-green-400' />
        Action Items
      </h3>
      <div className='space-y-3'>
        {items.map((item, idx) => (
          <div key={idx} className='p-3 bg-white/10 rounded-lg flex flex-col md:flex-row md:items-center md:justify-between'>
            <div>
              <span className='text-white font-medium'>{item.description}</span>
              {item.assignee && (
                <span className='ml-2 text-gray-300 text-sm'>({item.assignee})</span>
              )}
            </div>
            <div className='flex items-center space-x-2 mt-2 md:mt-0'>
              {item.deadline && (
                <span className='text-gray-400 text-xs'>{item.deadline}</span>
              )}
              {item.priority && (
                <span className={`px-2 py-1 rounded text-xs font-semibold ${priorityColors[item.priority]}`}>{item.priority}</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
} 