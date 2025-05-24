import { AlertTriangle } from 'lucide-react'

interface Risk {
  description: string
  impact: 'High' | 'Medium' | 'Low'
}

interface RisksCardProps {
  risks: Risk[]
}

const impactColors = {
  High: 'bg-red-500 text-white',
  Medium: 'bg-yellow-400 text-gray-900',
  Low: 'bg-green-400 text-gray-900',
}

export function RisksCard({ risks }: RisksCardProps) {
  return (
    <div className='card p-6 bg-white/10 backdrop-blur-lg border-white/20 h-full'>
      <h3 className='text-lg font-bold text-white mb-4 flex items-center'>
        <AlertTriangle className='mr-2 text-red-400' />
        Identified Risks
      </h3>
      <div className='space-y-3'>
        {risks.map((risk, idx) => (
          <div key={idx} className='p-3 bg-white/10 rounded-lg flex items-center justify-between'>
            <span className='text-white'>{risk.description}</span>
            <span className={`ml-4 px-2 py-1 rounded text-xs font-semibold ${impactColors[risk.impact]}`}>{risk.impact} Impact</span>
          </div>
        ))}
      </div>
    </div>
  )
} 