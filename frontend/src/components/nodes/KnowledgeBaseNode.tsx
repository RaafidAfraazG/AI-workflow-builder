import React from 'react'
import { Handle, Position } from 'reactflow'
import { Card, CardContent } from '@/components/ui/card'
import { Database, FileText } from 'lucide-react'

const KnowledgeBaseNode: React.FC<any> = ({ data }) => {
  const collection = data?.config?.collection || 'default'
  const topK = data?.config?.top_k || 5
  const uploadedDocs = data?.config?.documents || []
  
  return (
    <Card className="w-48">
      <CardContent className="p-4">
        <div className="flex items-center space-x-2 mb-2">
          <Database className="h-4 w-4" />
          <span className="font-medium text-sm">{data.label}</span>
        </div>
        <div className="text-xs text-gray-600 mb-1">
          Collection: {collection}
        </div>
        <div className="text-xs text-gray-600 mb-1">
          Top K: {topK}
        </div>
        {uploadedDocs.length > 0 && (
          <div className="text-xs text-green-600 flex items-center gap-1">
            <FileText className="h-3 w-3" />
            {uploadedDocs.length} document(s)
          </div>
        )}
        <Handle
          type="target"
          position={Position.Left}
          className="w-2 h-2 bg-green-500"
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

export default KnowledgeBaseNode