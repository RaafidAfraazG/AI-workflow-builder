import { create } from 'zustand'
import { Node, Edge } from '@/lib/types'

interface BuilderState {
  nodes: Node[]
  edges: Edge[]
  selectedNode: Node | null
  setNodes: (nodes: Node[]) => void
  setEdges: (edges: Edge[]) => void
  addNode: (node: Node) => void
  updateNode: (id: string, updates: Partial<Node>) => void
  removeNode: (id: string) => void
  addEdge: (edge: Edge) => void
  updateEdge: (id: string, updates: Partial<Edge>) => void
  removeEdge: (id: string) => void
  resetNodes: () => void
  resetEdges: () => void
  setSelectedNode: (node: Node | null) => void
}

export const useBuilderStore = create<BuilderState>((set, get) => ({
  nodes: [],
  edges: [],
  selectedNode: null,

  setNodes: (nodes) => set({ nodes }),
  setEdges: (edges) => set({ edges }),

  addNode: (node) => set((state) => ({ nodes: [...state.nodes, node] })),

  updateNode: (id, updates) =>
    set((state) => ({
      nodes: state.nodes.map((node) =>
        node.id === id ? { ...node, ...updates } : node
      ),
    })),

  removeNode: (id) =>
    set((state) => ({
      nodes: state.nodes.filter((node) => node.id !== id),
      edges: state.edges.filter(
        (edge) => edge.source !== id && edge.target !== id
      ),
    })),

  addEdge: (edge) => set((state) => ({ edges: [...state.edges, edge] })),

  updateEdge: (id, updates) =>
    set((state) => ({
      edges: state.edges.map((edge) =>
        edge.id === id ? { ...edge, ...updates } : edge
      ),
    })),

  removeEdge: (id) =>
    set((state) => ({
      edges: state.edges.filter((edge) => edge.id !== id),
    })),

  resetNodes: () => set({ nodes: [] }),
  resetEdges: () => set({ edges: [] }),

  setSelectedNode: (selectedNode) => set({ selectedNode }),
}))

export default useBuilderStore