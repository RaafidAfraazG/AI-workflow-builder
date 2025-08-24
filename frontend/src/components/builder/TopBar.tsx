import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Save, Play, MessageSquare, Loader2, List } from 'lucide-react'
import { useMutation } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { useBuilderStore } from '@/store/builderStore'
import ChatWindow from './ChatWindow'
import type { Workflow } from '@/lib/types'

const TopBar: React.FC = () => {
  const [workflowName, setWorkflowName] = useState('My Workflow')
  const [isChatOpen, setIsChatOpen] = useState(false)
  const [isWorkflowBuilt, setIsWorkflowBuilt] = useState(false) // Track build status
  const navigate = useNavigate()
  
  const { 
    nodes, 
    edges, 
    currentWorkflowId, 
    setCurrentWorkflowId 
  } = useBuilderStore()

  // Debug logging to track state changes
  useEffect(() => {
    console.log('TopBar state changed:', {
      currentWorkflowId,
      nodesLength: nodes.length,
      isWorkflowBuilt,
      canTest: Boolean(currentWorkflowId && nodes.length > 0)
    })
  }, [currentWorkflowId, nodes.length, isWorkflowBuilt])

  const createWorkflowMutation = useMutation({
    mutationFn: (workflow: Omit<Workflow, 'id' | 'created_at' | 'updated_at'>) => api.createWorkflow(workflow),
    onSuccess: (data) => {
      console.log('Workflow created successfully:', data.id)
      setCurrentWorkflowId(data.id)
      setIsWorkflowBuilt(false) // Reset build status
    },
    onError: (error) => {
      console.error('Failed to create workflow:', error)
    },
  })

  const updateWorkflowMutation = useMutation({
    mutationFn: ({ id, workflow }: { id: string; workflow: Omit<Workflow, 'id' | 'created_at' | 'updated_at'> }) => 
      api.updateWorkflow(id, workflow),
    onSuccess: (data) => {
      console.log('Workflow updated successfully:', data.id)
      // Ensure the workflow ID is maintained after update
      if (data.id !== currentWorkflowId) {
        setCurrentWorkflowId(data.id)
      }
      setIsWorkflowBuilt(false) // Reset build status after update
    },
    onError: (error) => {
      console.error('Failed to update workflow:', error)
    },
  })

  const buildWorkflowMutation = useMutation({
    mutationFn: (id: string) => api.buildWorkflow(id),
    onSuccess: (data) => {
      console.log('Workflow built successfully:', data)
      setIsWorkflowBuilt(true) // Mark as built
      // Ensure workflow ID is still available after build
      console.log('Workflow ID after build:', currentWorkflowId)
    },
    onError: (error) => {
      console.error('Failed to build workflow:', error)
      setIsWorkflowBuilt(false)
    },
  })

  const handleSaveWorkflow = async () => {
    if (nodes.length === 0) {
      alert('Please add at least one node to save the workflow')
      return
    }

    const workflow: Omit<Workflow, 'id' | 'created_at' | 'updated_at'> = {
      name: workflowName,
      nodes,
      edges,
    }

    try {
      if (currentWorkflowId) {
        // Update existing workflow
        updateWorkflowMutation.mutate({ id: currentWorkflowId, workflow })
      } else {
        // Create new workflow
        createWorkflowMutation.mutate(workflow)
      }
    } catch (error) {
      console.error('Error saving workflow:', error)
    }
  }

  const handleBuildWorkflow = async () => {
    if (!currentWorkflowId) {
      alert('Please save the workflow first')
      return
    }

    if (nodes.length === 0) {
      alert('Please add at least one node to build the workflow')
      return
    }

    console.log('Building workflow with ID:', currentWorkflowId)
    buildWorkflowMutation.mutate(currentWorkflowId)
  }

  const handleTestWorkflow = () => {
    console.log('Test button clicked - Current state:', {
      currentWorkflowId,
      nodesLength: nodes.length,
      isWorkflowBuilt
    })
    
    if (!currentWorkflowId) {
      alert('Please save the workflow first before testing')
      return
    }
    
    if (nodes.length === 0) {
      alert('Please add nodes to the workflow before testing')
      return
    }
    
    setIsChatOpen(true)
  }

  const handleViewAllWorkflows = () => {
    navigate('/')
  }

  const isLoading = createWorkflowMutation.isPending || 
                   updateWorkflowMutation.isPending || 
                   buildWorkflowMutation.isPending

  // More lenient condition for test button - remove build requirement if not needed
  const canTestWorkflow = Boolean(currentWorkflowId && nodes.length > 0)
  
  // Alternative: If you want to require build before test, use this instead:
  // const canTestWorkflow = Boolean(currentWorkflowId && nodes.length > 0 && isWorkflowBuilt)

  return (
    <>
      <div className="flex items-center justify-between p-4 bg-white border-b border-gray-200">
        <div className="flex items-center space-x-4">
          <Button
            onClick={handleViewAllWorkflows}
            variant="ghost"
            size="sm"
            className="text-gray-600 hover:text-gray-900"
          >
            <List className="h-4 w-4 mr-2" />
            All Workflows
          </Button>
          <Input
            value={workflowName}
            onChange={(e) => setWorkflowName(e.target.value)}
            className="w-64"
            placeholder="Workflow Name"
          />
        </div>
        
        <div className="flex items-center space-x-2">
          <Button
            onClick={handleSaveWorkflow}
            disabled={isLoading || nodes.length === 0}
            variant="outline"
            size="sm"
          >
            {(createWorkflowMutation.isPending || updateWorkflowMutation.isPending) ? (
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
            ) : (
              <Save className="h-4 w-4 mr-2" />
            )}
            {currentWorkflowId ? 'Update' : 'Save'}
          </Button>
          
          <Button
            onClick={handleBuildWorkflow}
            disabled={isLoading || !currentWorkflowId || nodes.length === 0}
            variant="outline"
            size="sm"
          >
            {buildWorkflowMutation.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
            ) : (
              <Play className="h-4 w-4 mr-2" />
            )}
            Build
          </Button>
          
          <Button
            onClick={handleTestWorkflow}
            disabled={!canTestWorkflow}
            size="sm"
            className={canTestWorkflow ? '' : 'opacity-50 cursor-not-allowed'}
          >
            <MessageSquare className="h-4 w-4 mr-2" />
            Test Workflow
            {/* Debug indicator */}
            {process.env.NODE_ENV === 'development' && (
              <span className="ml-1 text-xs">
                ({currentWorkflowId ? '✓' : '✗'})
              </span>
            )}
          </Button>
        </div>
      </div>

      <ChatWindow
        isOpen={isChatOpen}
        onClose={() => setIsChatOpen(false)}
        workflowId={currentWorkflowId}
      />
    </>
  )
}

export default TopBar