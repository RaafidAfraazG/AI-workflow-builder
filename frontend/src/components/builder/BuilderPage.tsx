import React, { useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { useBuilderStore } from '@/store/builderStore'
import TopBar from './TopBar'
import WorkflowCanvas from './WorkflowCanvas'
import NodePalette from './NodePalette'
import ConfigPanel from './ConfigPanel'

const BuilderPage: React.FC = () => {
  const [searchParams] = useSearchParams()
  const workflowId = searchParams.get('id')
  
  const { 
    setWorkflow, 
    clearWorkflow, 
    setCurrentWorkflowId,
    currentWorkflowId 
  } = useBuilderStore()

  // Load existing workflow if ID is provided
  const { data: workflow, isLoading, error } = useQuery({
    queryKey: ['workflow', workflowId],
    queryFn: () => workflowId ? api.getWorkflow(workflowId) : null,
    enabled: !!workflowId,
    staleTime: 0, // Always fetch fresh data
  })

  useEffect(() => {
    if (workflowId && workflow) {
      // Loading existing workflow
      console.log('Loading workflow:', workflowId, workflow)
      setWorkflow(workflow.nodes, workflow.edges)
      setCurrentWorkflowId(workflowId)
    } else if (!workflowId) {
      // Starting fresh - clear everything
      console.log('Starting fresh workflow')
      clearWorkflow()
    }
  }, [workflowId, workflow, setWorkflow, clearWorkflow, setCurrentWorkflowId])

  // Clear workflow when leaving the page or when workflowId changes
  useEffect(() => {
    return () => {
      if (!workflowId) {
        // Only clear if we're not loading a specific workflow
        clearWorkflow()
      }
    }
  }, [workflowId, clearWorkflow])

  if (workflowId && isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <div className="mt-4 text-gray-600">Loading workflow...</div>
        </div>
      </div>
    )
  }

  if (workflowId && error) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="text-red-600 text-xl mb-2">Error Loading Workflow</div>
          <div className="text-gray-600">
            {error instanceof Error ? error.message : 'Failed to load workflow'}
          </div>
          <button 
            onClick={() => window.location.href = '/builder'}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Start New Workflow
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      <TopBar />
      <div className="flex flex-1">
        <div className="w-80 border-r border-gray-200 bg-white">
          <NodePalette />
        </div>
        <div className="flex-1">
          <WorkflowCanvas />
        </div>
        <div className="w-80 border-l border-gray-200 bg-white">
          <ConfigPanel />
        </div>
      </div>
    </div>
  )
}

export default BuilderPage