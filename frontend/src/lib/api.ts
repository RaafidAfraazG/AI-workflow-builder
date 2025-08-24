import { Workflow, Chat, Message, Document, KnowledgeBaseSearchResult } from './types'

const API_BASE = '/api'

class ApiClient {
  async createWorkflow(workflow: Omit<Workflow, 'id' | 'created_at' | 'updated_at'>): Promise<Workflow> {
    const response = await fetch(`${API_BASE}/workflows`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(workflow),
    })
    if (!response.ok) throw new Error('Failed to create workflow')
    return response.json()
  }

  async getWorkflow(id: string): Promise<Workflow> {
    const response = await fetch(`${API_BASE}/workflows/${id}`)
    if (!response.ok) throw new Error('Failed to get workflow')
    return response.json()
  }

  async buildWorkflow(id: string): Promise<{ success: boolean; message: string }> {
    const response = await fetch(`${API_BASE}/workflows/${id}/build`, {
      method: 'POST',
    })
    if (!response.ok) throw new Error('Failed to build workflow')
    return response.json()
  }

  async createChat(workflowId: string): Promise<Chat> {
    const response = await fetch(`${API_BASE}/workflows/${workflowId}/chat`, {
      method: 'POST',
    })
    if (!response.ok) throw new Error('Failed to create chat')
    return response.json()
  }

  async *sendMessage(workflowId: string, chatId: string, message: string): AsyncGenerator<string, void, unknown> {
    const response = await fetch(`${API_BASE}/workflows/${workflowId}/chat/${chatId}/message`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: message }),
    })

    if (!response.ok) throw new Error('Failed to send message')
    
    const reader = response.body?.getReader()
    const decoder = new TextDecoder()

    if (!reader) return

    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            if (data === '[DONE]') return
            try {
              const parsed = JSON.parse(data)
              if (parsed.token) {
                yield parsed.token
              }
            } catch (e) {
              console.warn('Failed to parse SSE data:', data)
            }
          }
        }
      }
    } finally {
      reader.releaseLock()
    }
  }

  // --- Knowledge Base API ---

  async uploadDocument(file: File, collection: string = 'default'): Promise<Document> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('collection', collection)

    const response = await fetch(`${API_BASE}/kb/upload`, {
      method: 'POST',
      body: formData,
    })
    if (!response.ok) {
      const txt = await response.text().catch(() => '')
      throw new Error(`Failed to upload document${txt ? `: ${txt}` : ''}`)
    }
    return response.json()
  }

  async ingestDocument(documentId: string): Promise<{ success: boolean; message: string }> {
    // matches: @router.post("/ingest/{document_id}")
    const response = await fetch(`${API_BASE}/kb/ingest/${documentId}`, {
      method: 'POST',
    })
    if (!response.ok) {
      const txt = await response.text().catch(() => '')
      throw new Error(`Failed to ingest document${txt ? `: ${txt}` : ''}`)
    }
    return response.json()
  }

  async deleteDocument(documentId: string): Promise<{ success: boolean; message: string }> {
    // matches: @router.delete("/{document_id}")
    const response = await fetch(`${API_BASE}/kb/${documentId}`, {
      method: 'DELETE',
    })
    if (!response.ok) {
      const txt = await response.text().catch(() => '')
      throw new Error(`Failed to delete document${txt ? `: ${txt}` : ''}`)
    }
    return response.json()
  }

  async searchKnowledgeBase(
    query: string,
    collection: string = 'default',
    topK: number = 5
  ): Promise<Document[]> {
    // matches: @router.get("/search") -> params: query, collection, top_k
    const url = `${API_BASE}/kb/search?query=${encodeURIComponent(query)}&collection=${encodeURIComponent(
      collection
    )}&top_k=${topK}`

    const response = await fetch(url)
    if (!response.ok) {
      const txt = await response.text().catch(() => '')
      throw new Error(`Failed to search knowledge base${txt ? `: ${txt}` : ''}`)
    }
    return response.json()
  }

  async healthCheck(): Promise<{ status: string }> {
    const response = await fetch(`${API_BASE}/healthz`)
    if (!response.ok) throw new Error('Health check failed')
    return response.json()
  }
}

export const api = new ApiClient()
