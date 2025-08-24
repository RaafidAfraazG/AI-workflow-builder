import React, { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useBuilderStore } from '@/store/builderStore'
import { useMutation } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Play, MessageSquare, Save } from 'lucide-react'
import ChatWindow from './ChatWindow'

const TopBar: React.FC = () => {
  const { nodes, edges } = useBuilderStore()
  const [workflowName, setWorkflowName] = useState('Untitled Workflow')
  const [workflowId, setWorkflowId] = useState<string | null>(null)
  const [isChatOpen, setIsChatOpen] = useState(false)
  const [isWorkflowBuilt, setIsWorkflowBuilt] = useState(false)

  const createWorkflowMutation = useMutation({
    mutationFn: () => api.createWorkflow({
      name: workflowName,
      nodes,
      edges,
    }),
    onSuccess: (data) => {
      setWorkflowId(data.id)
      console.log('Workflow saved successfully:', data.id)
    },
  })

  const buildWorkflowMutation = useMutation({
    mutationFn: (id: string) => api.buildWorkflow(id),
    onSuccess: (data) => {
      setIsWorkflowBuilt(true)
      console.log('Workflow built successfully:', data.message)
    },
  })

  const handleSaveWorkflow = () => {
    createWorkflowMutation.mutate()
  }

  const handleBuildWorkflow = () => {
    if (!workflowId) {
      // Save first, then build
      createWorkflowMutation.mutate(undefined, {
        onSuccess: (data) => {
          buildWorkflowMutation.mutate(data.id)
        }
      })
    } else {
      buildWorkflowMutation.mutate(workflowId)
    }
  }

  const handleOpenChat = () => {
    if (workflowId && isWorkflowBuilt) {
      setIsChatOpen(true)
    }
  }

  const canChat = workflowId && isWorkflowBuilt && !buildWorkflowMutation.isPending

  return (
    <>
      <div className="h-16 border-b bg-white px-4 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Input
            value={workflowName}
            onChange={(e) => setWorkflowName(e.target.value)}
            className="w-64"
            placeholder="Workflow name"
          />
          <Button
            variant="outline"
            onClick={handleSaveWorkflow}
            disabled={createWorkflowMutation.isPending}
          >
            <Save className="mr-2 h-4 w-4" />
            {createWorkflowMutation.isPending ? 'Saving...' : 'Save'}
          </Button>
        </div>

        <div className="flex items-center space-x-2">
          <Button
            onClick={handleBuildWorkflow}
            disabled={buildWorkflowMutation.isPending}
          >
            <Play className="mr-2 h-4 w-4" />
            {buildWorkflowMutation.isPending ? 'Building...' : 'Build'}
          </Button>
          <Button
            variant="outline"
            onClick={handleOpenChat}
            disabled={!canChat}
            title={
              !workflowId 
                ? 'Save workflow first' 
                : !isWorkflowBuilt 
                ? 'Build workflow first' 
                : 'Chat with your workflow'
            }
          >
            <MessageSquare className="mr-2 h-4 w-4" />
            Chat
          </Button>
        </div>
      </div>

      {/* Chat Window */}
      <ChatWindow 
        isOpen={isChatOpen} 
        onClose={() => setIsChatOpen(false)} 
        workflowId={workflowId} 
      />
    </>
  )
}

export default TopBar