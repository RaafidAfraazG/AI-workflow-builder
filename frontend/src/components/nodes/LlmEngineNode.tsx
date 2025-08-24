import React from "react"
import { Handle, Position, useReactFlow } from "reactflow"
import { Card, CardContent } from "@/components/ui/card"
import { Brain } from "lucide-react"
import { Input } from "@/components/ui/input"

const LlmEngineNode: React.FC<any> = ({ id, data }) => {
  const { setNodes } = useReactFlow()

  const provider = data?.config?.provider || "openai"
  const model = data?.config?.model || "gpt-3.5-turbo"
  const temperature = data?.config?.temperature || 0.7
  const customPrompt = data?.config?.customPrompt || ""

  const handlePromptChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value
    setNodes((nds) =>
      nds.map((node) =>
        node.id === id
          ? {
              ...node,
              data: {
                ...node.data,
                config: {
                  ...node.data.config,
                  customPrompt: value,
                },
              },
            }
          : node
      )
    )
  }

  return (
    <Card className="w-56">
      <CardContent className="p-4">
        <div className="flex items-center space-x-2 mb-2">
          <Brain className="h-4 w-4" />
          <span className="font-medium text-sm">{data.label}</span>
        </div>

        <div className="text-xs text-gray-600 mb-1">
          {provider} / {model}
        </div>
        <div className="text-xs text-gray-600 mb-2">
          Temp: {temperature}
        </div>

        {/* Editable custom prompt input (small, inline) */}
        <Input
          placeholder="Custom prompt..."
          value={customPrompt}
          onChange={handlePromptChange}
          className="text-xs"
        />

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
