import React from 'react'
import { Handle, Position } from 'reactflow'
import { Card, CardContent } from '@/components/ui/card'
import { Brain } from 'lucide-react'

const LlmEngineNode: React.FC<any> = ({ data }) => {
  return (
    <Card className="w-48">
      <CardContent className="p-4">
        <div className="flex items-center space-x-2 mb-2">
          <Brain className="h-4 w-4" />
          <span className="font-medium text-sm">{data.label}</span>
        </div>
        <div className="text-xs text-gray-600">
          {data.config.provider || 'openai'} / {data.config.model || 'gpt-3.5-turbo'}
        </div>
        <div className="text-xs text-gray-600">
          Temp: {data.config.temperature || 0.7}
        </div>
        <Handle
          type="target"
          position={Position.Left}
          className="w-2 h-2 bg-purple-500"
        />
        <Handle
          type="source"
          position={Position.Right}
          className="w-2 h-2 bg-purple-500"
        />
      </CardContent>
    </Card>
  )
}

export default LlmEngineNode