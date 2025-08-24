export interface Node {
  id: string
  type: 'userQuery' | 'knowledgeBase' | 'llmEngine' | 'output'
  position: { x: number; y: number }
  data: {
    label: string
    config: Record<string, any>
  }
}

export interface Edge {
  id: string
  source: string
  target: string
  type: string
}

export interface Workflow {
  id: string
  name: string
  nodes: Node[]
  edges: Edge[]
  created_at: string
  updated_at: string
}

export interface Chat {
  id: string
  workflow_id: string
  created_at: string
}

export interface Message {
  id: string
  chat_id: string
  content: string
  role: 'user' | 'assistant'
  created_at: string
}

export interface Document {
  id: string
  filename: string
  file_path: string
  content_type: string
  created_at: string
  is_ingested: boolean
}

export interface KnowledgeBaseSearchResult {
  id: string
  content: string
  metadata: Record<string, any>
  score: number
}