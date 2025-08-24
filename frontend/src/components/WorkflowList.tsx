import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Calendar, Search, Play, Eye, Trash2, Plus, Activity, MessageSquare, Settings } from 'lucide-react'
import { api } from '@/lib/api'
import { Workflow } from '@/lib/types'

const WorkflowList: React.FC = () => {
  const [workflows, setWorkflows] = useState<Workflow[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [workflowToDelete, setWorkflowToDelete] = useState<Workflow | null>(null)
  const [deleting, setDeleting] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    loadWorkflows()
  }, [])

  const loadWorkflows = async () => {
    try {
      setLoading(true)
      const data = await api.getAllWorkflows()
      setWorkflows(data)
    } catch (error) {
      console.error('Failed to load workflows:', error)
    } finally {
      setLoading(false)
    }
  }

  const filteredWorkflows = workflows.filter(workflow =>
    workflow.name.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getNodeTypeIcon = (type: string) => {
    switch (type) {
      case 'userQuery': return <MessageSquare className="w-4 h-4" />
      case 'knowledgeBase': return <Activity className="w-4 h-4" />
      case 'llmEngine': return <Settings className="w-4 h-4" />
      case 'output': return <Eye className="w-4 h-4" />
      default: return <Activity className="w-4 h-4" />
    }
  }

  const getNodeTypeName = (type: string) => {
    switch (type) {
      case 'userQuery': return 'User Query'
      case 'knowledgeBase': return 'Knowledge Base'
      case 'llmEngine': return 'LLM Engine'
      case 'output': return 'Output'
      default: return type
    }
  }

  const handleDeleteClick = (workflow: Workflow) => {
    setWorkflowToDelete(workflow)
    setDeleteDialogOpen(true)
  }

  const handleDeleteConfirm = async () => {
    if (!workflowToDelete) return
    
    setDeleting(true)
    try {
      await api.deleteWorkflow(workflowToDelete.id)
      setWorkflows(workflows.filter(w => w.id !== workflowToDelete.id))
      setDeleteDialogOpen(false)
      setWorkflowToDelete(null)
    } catch (error) {
      console.error('Failed to delete workflow:', error)
      alert('Failed to delete workflow')
    } finally {
      setDeleting(false)
    }
  }

  const handleDeleteCancel = () => {
    setDeleteDialogOpen(false)
    setWorkflowToDelete(null)
  }

  const openWorkflowEditor = (workflowId: string) => {
    navigate(`/builder/${workflowId}`)
  }

  const createNewWorkflow = () => {
    navigate('/builder')
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Activity className="w-8 h-8 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading workflows...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">My Workflows</h1>
              <p className="text-gray-600">Manage and run your AI workflows</p>
            </div>
            <Button onClick={createNewWorkflow} className="bg-blue-600 hover:bg-blue-700">
              <Plus className="w-4 h-4 mr-2" />
              Create Workflow
            </Button>
          </div>

          {/* Search */}
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <Input
              placeholder="Search workflows..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>

        {/* Workflow Grid */}
        {filteredWorkflows.length === 0 ? (
          <div className="text-center py-12">
            <Activity className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-xl font-medium text-gray-900 mb-2">
              {searchTerm ? 'No workflows found' : 'No workflows yet'}
            </h3>
            <p className="text-gray-500 mb-4">
              {searchTerm 
                ? `No workflows match "${searchTerm}"`
                : 'Create your first AI workflow to get started'
              }
            </p>
            {!searchTerm && (
              <Button onClick={createNewWorkflow} className="bg-blue-600 hover:bg-blue-700">
                <Plus className="w-4 h-4 mr-2" />
                Create Your First Workflow
              </Button>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredWorkflows.map((workflow) => (
              <Card key={workflow.id} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span className="truncate">{workflow.name}</span>
                  </CardTitle>
                  <CardDescription className="flex items-center text-sm text-gray-500">
                    <Calendar className="w-4 h-4 mr-1" />
                    Updated {formatDate(workflow.updated_at)}
                  </CardDescription>
                </CardHeader>

                <CardContent>
                  <div className="space-y-2">
                    <div className="text-sm text-gray-600">
                      <strong>{workflow.nodes.length}</strong> nodes, 
                      <strong className="ml-1">{workflow.edges.length}</strong> connections
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {workflow.nodes.slice(0, 4).map((node) => (
                        <div
                          key={node.id}
                          className="flex items-center gap-1 text-xs bg-gray-100 px-2 py-1 rounded-full"
                        >
                          {getNodeTypeIcon(node.type)}
                          {getNodeTypeName(node.type)}
                        </div>
                      ))}
                      {workflow.nodes.length > 4 && (
                        <div className="text-xs bg-gray-100 px-2 py-1 rounded-full">
                          +{workflow.nodes.length - 4} more
                        </div>
                      )}
                    </div>
                  </div>
                </CardContent>

                <CardFooter className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => openWorkflowEditor(workflow.id)}
                    className="flex-1"
                  >
                    <Settings className="w-4 h-4 mr-1" />
                    Edit
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleDeleteClick(workflow)}
                    className="text-red-600 hover:text-red-700"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </CardFooter>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Workflow</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete "{workflowToDelete?.name}"? This action cannot be undone and will also delete all associated chats and messages.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={handleDeleteCancel} disabled={deleting}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleDeleteConfirm} disabled={deleting}>
              {deleting ? 'Deleting...' : 'Delete'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default WorkflowList