import { FileText, Copy } from 'lucide-react'

interface TranscriptCardProps {
  transcript: string
  onCopy: () => void
}

export function TranscriptCard({ transcript, onCopy }: TranscriptCardProps) {
  return (
    <div className='card p-6 bg-white/10 backdrop-blur-lg border-white/20'>
      <div className='flex items-center justify-between mb-4'>
        <h3 className='text-lg font-bold text-white flex items-center'>
          <FileText className='mr-2' />
          Full Transcript
        </h3>
        <button
          onClick={onCopy}
          className='p-2 hover:bg-white/20 rounded-lg transition-colors'
        >
          <Copy className='text-gray-400' size={16} />
        </button>
      </div>
      <div className='bg-white/10 rounded-lg p-4 max-h-96 overflow-y-auto custom-scrollbar'>
        <p className='text-gray-300 whitespace-pre-wrap leading-relaxed'>{transcript}</p>
      </div>
    </div>
  )
} 