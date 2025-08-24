import React, { useCallback, useEffect } from 'react'
import type { Node as RFNode, Edge as RFEdge, Connection } from 'reactflow'
import ReactFlow, {
  MiniMap,
  Controls,
  Background,
  BackgroundVariant,
  useNodesState,
  useEdgesState,
  addEdge,
} from 'reactflow'
import 'reactflow/dist/style.css'

import UserQueryNode from '../nodes/UserQueryNode'
import KnowledgeBaseNode from '../nodes/KnowledgeBaseNode'
import LlmEngineNode from '../nodes/LlmEngineNode'
import OutputNode from '../nodes/OutputNode'
import { useBuilderStore } from '@/store/builderStore'
import type { Node, Edge } from '@/lib/types'

const nodeTypes = {
  userQuery: UserQueryNode,
  knowledgeBase: KnowledgeBaseNode,
  llmEngine: LlmEngineNode,
  output: OutputNode,
}

const WorkflowCanvas: React.FC = () => {
  const { nodes, edges, setNodes, setEdges, addEdge: addStoreEdge, setSelectedNode } =
    useBuilderStore()

  // React Flow states
  const [reactFlowNodes, setReactFlowNodes, onNodesChange] = useNodesState<RFNode>(nodes as RFNode[])
  const [reactFlowEdges, setReactFlowEdges, onEdgesChange] = useEdgesState<RFEdge>(edges as RFEdge[])

  // Sync Zustand -> ReactFlow (FIXED: Force re-render with new data)
  useEffect(() => {
    const updatedNodes = nodes.map(node => ({
      ...node,
      // Force re-render by creating new data object
      data: { ...node.data }
    })) as RFNode[]
    
    setReactFlowNodes(updatedNodes)
  }, [nodes, setReactFlowNodes])

  useEffect(() => {
    setReactFlowEdges(edges as RFEdge[])
  }, [edges, setReactFlowEdges])

  // Sync ReactFlow -> Zustand when nodes change position
  const handleNodesChange = useCallback((changes: any) => {
    onNodesChange(changes)
    
    // Update store when nodes are moved
    changes.forEach((change: any) => {
      if (change.type === 'position' && change.position) {
        const nodeIndex = nodes.findIndex(n => n.id === change.id)
        if (nodeIndex !== -1) {
          const updatedNodes = [...nodes]
          updatedNodes[nodeIndex] = {
            ...updatedNodes[nodeIndex],
            position: change.position
          }
          setNodes(updatedNodes)
        }
      }
    })
  }, [nodes, setNodes, onNodesChange])

  const onConnect = useCallback(
    (params: RFEdge | Connection) => {
      const newEdge: RFEdge = {
        ...params,
        id: `e${params.source}-${params.target}`,
        type: 'default',
      } as RFEdge

      setReactFlowEdges((eds) => addEdge(newEdge, eds))
      addStoreEdge(newEdge as unknown as Edge)
    },
    [setReactFlowEdges, addStoreEdge]
  )

  const onNodeClick = useCallback(
    (event: React.MouseEvent, node: RFNode) => {
      const storeNode = nodes.find((n) => n.id === node.id)
      setSelectedNode(storeNode || null)
    },
    [nodes, setSelectedNode]
  )

  return (
    <div className="w-full h-full min-h-0 flex-1">
      <ReactFlow
        nodes={reactFlowNodes}
        edges={reactFlowEdges}
        onNodesChange={handleNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={onNodeClick}
        nodeTypes={nodeTypes}
        fitView
        className="w-full h-full"
      >
        <Controls />
        <MiniMap />
        <Background variant={BackgroundVariant.Lines} gap={12} size={1} />
      </ReactFlow>
    </div>
  )
}

export default WorkflowCanvas