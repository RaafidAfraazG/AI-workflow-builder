import React from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useBuilderStore } from '@/store/builderStore'
import { generateId } from '@/lib/utils'
import { User, Database, Brain, FileOutput } from 'lucide-react'

const nodeTypes = [
  {
    type: 'userQuery' as const,
    label: 'User Query',
    icon: User,
    config: { placeholder: 'Enter your question...' }
  },
  {
    type: 'knowledgeBase' as const,
    label: 'Knowledge Base',
    icon: Database,
    config: { collection: '', top_k: 5 }
  },
  {
    type: 'llmEngine' as const,
    label: 'LLM Engine',
    icon: Brain,
    config: { provider: 'openai', model: 'gpt-3.5-turbo', temperature: 0.7 }
  },
  {
    type: 'output' as const,
    label: 'Output',
    icon: FileOutput,
    config: { format: 'text' }
  }
]

const NodePalette: React.FC = () => {
  const { addNode } = useBuilderStore()

  const handleAddNode = (nodeType: typeof nodeTypes[0]) => {
    const newNode = {
      id: generateId(),
      type: nodeType.type,
      position: { x: Math.random() * 200, y: Math.random() * 200 },
      data: {
        label: nodeType.label,
        config: nodeType.config
      }
    }
    addNode(newNode)
  }

  return (
    <div className="w-64 p-4 border-r bg-gray-50">
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Node Palette</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {nodeTypes.map((nodeType) => {
            const Icon = nodeType.icon
            return (
              <Button
                key={nodeType.type}
                variant="outline"
                className="w-full justify-start"
                onClick={() => handleAddNode(nodeType)}
              >
                <Icon className="mr-2 h-4 w-4" />
                {nodeType.label}
              </Button>
            )
          })}
        </CardContent>
      </Card>
    </div>
  )
}

export default NodePalette