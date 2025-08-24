import React, { useEffect, useState } from "react"
import { Handle, Position, useReactFlow } from "reactflow"
import { Card, CardContent } from "@/components/ui/card"
import { User } from "lucide-react"
import { Input } from "@/components/ui/input"

const UserQueryNode: React.FC<any> = ({ id, data }) => {
  const { setNodes } = useReactFlow()
  const [localQuery, setLocalQuery] = useState("")

  // Sync local state with node data
  useEffect(() => {
    setLocalQuery(data?.config?.queryText || "")
  }, [data?.config?.queryText])

  const handleQueryChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value
    setLocalQuery(value)

    // Update React Flow node
    setNodes((nds) =>
      nds.map((node) =>
        node.id === id
          ? {
              ...node,
              data: {
                ...node.data,
                config: {
                  ...node.data.config,
                  queryText: value,
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
          <User className="h-4 w-4" />
          <span className="font-medium text-sm">{data.label}</span>
        </div>

        {/* Editable user query input */}
        <Input
          placeholder="Enter your question..."
          value={localQuery}
          onChange={handleQueryChange}
          className="text-xs"
        />

        <Handle
          type="source"
          position={Position.Right}
          className="w-2 h-2 bg-green-500"
        />
      </CardContent>
    </Card>
  )
}

export default UserQueryNode
