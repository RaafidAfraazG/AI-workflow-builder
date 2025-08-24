import React, { useState, useRef, useEffect } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card } from '@/components/ui/card'
import { useMutation } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Send, MessageSquare, Loader2 } from 'lucide-react'
import type { Chat, KnowledgeBaseSearchResult } from '@/lib/types'
import useBuilderStore from '@/store/builderStore'

interface Message {
  id: string
  content: string
  role: 'user' | 'assistant'
  timestamp: Date
}

interface ChatWindowProps {
  isOpen: boolean
  onClose: () => void
  workflowId: string | null
}

const ChatWindow: React.FC<ChatWindowProps> = ({ isOpen, onClose, workflowId }) => {
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState('')
  const [chatId, setChatId] = useState<string | null>(null)
  const [isStreaming, setIsStreaming] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const { nodes } = useBuilderStore()
  // Get collection name from first knowledgeBase node in the workflow
  const collectionName =
    nodes.find((n) => n.type === 'knowledgeBase')?.data.config.collection || 'default'

  const createChatMutation = useMutation({
    mutationFn: (workflowId: string) => api.createChat(workflowId),
    onSuccess: (data: Chat) => setChatId(data.id),
  })

  useEffect(() => {
    if (isOpen && workflowId && !chatId) createChatMutation.mutate(workflowId)
  }, [isOpen, workflowId, chatId])

  useEffect(() => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }), [messages])

  const handleSendMessage = async () => {
    if (!inputValue.trim() || !workflowId || !chatId || isStreaming) return

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputValue,
      role: 'user',
      timestamp: new Date(),
    }
    setMessages((prev) => [...prev, userMessage])
    setInputValue('')
    setIsStreaming(true)

    const assistantMessage: Message = {
      id: (Date.now() + 1).toString(),
      content: '',
      role: 'assistant',
      timestamp: new Date(),
    }
    setMessages((prev) => [...prev, assistantMessage])

    try {
      // --- Knowledge Base Search ---
      const kbResults: KnowledgeBaseSearchResult[] = await api.searchKnowledgeBase(
        inputValue,
        collectionName,
        5
      )
      let prompt = inputValue

      if (kbResults.length > 0) {
        const kbContent = kbResults.map((r) => r.content).join('\n\n')
        prompt = `Use the following context from your knowledge base to answer the query:\n${kbContent}\n\nQuestion: ${inputValue}`
      }

      // --- Send to workflow ---
      const stream = api.sendMessage(workflowId, chatId, prompt)

      for await (const token of stream) {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMessage.id ? { ...msg, content: msg.content + token } : msg
          )
        )
      }
    } catch (error) {
      console.error('Error streaming message:', error)
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessage.id
            ? { ...msg, content: 'Error: Failed to get response. Check workflow or collection.' }
            : msg
        )
      )
    } finally {
      setIsStreaming(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const handleClose = () => {
    setMessages([])
    setChatId(null)
    onClose()
  }

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="max-w-4xl h-[700px] flex flex-col">
        <DialogHeader className="pb-2">
          <DialogTitle className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5" />
            Chat with Your Workflow
          </DialogTitle>
        </DialogHeader>

        <div className="flex-1 overflow-y-auto space-y-4 p-1">
          {createChatMutation.isPending ? (
            <div className="flex items-center justify-center h-32 text-gray-500">
              <Loader2 className="h-6 w-6 animate-spin mr-2" />
              Initializing chat session...
            </div>
          ) : messages.length === 0 ? (
            <div className="flex items-center justify-center h-32">
              <div className="text-center">
                <MessageSquare className="h-12 w-12 text-gray-300 mx-auto mb-3" />
                <div className="text-gray-500 text-lg">Start a conversation</div>
                <div className="text-gray-400 text-sm mt-1">
                  Your workflow will use the selected collection "{collectionName}" to answer queries.
                </div>
              </div>
            </div>
          ) : (
            messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <Card
                  className={`max-w-[75%] p-4 ${
                    msg.role === 'user' ? 'bg-blue-600 text-white shadow-md' : 'bg-white border shadow-sm'
                  }`}
                >
                  <div className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</div>
                  <div className={`text-xs mt-2 ${msg.role === 'user' ? 'text-blue-100' : 'text-gray-400'}`}>
                    {msg.timestamp.toLocaleTimeString()}
                  </div>
                </Card>
              </div>
            ))
          )}
          {isStreaming && (
            <div className="flex justify-start">
              <Card className="bg-white border shadow-sm p-4">
                <div className="flex items-center text-gray-500">
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  <span className="text-sm">Processing through workflow...</span>
                </div>
              </Card>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="border-t pt-4">
          <div className="flex space-x-3">
            <Input
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask anything about your knowledge base..."
              disabled={isStreaming || !chatId}
              className="flex-1 h-12"
            />
            <Button
              onClick={handleSendMessage}
              disabled={!inputValue.trim() || isStreaming || !chatId}
              size="lg"
              className="px-6"
            >
              {isStreaming ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
            </Button>
          </div>
          {workflowId && (
            <div className="text-xs text-gray-400 mt-2">
              Workflow ID: {workflowId} | Collection: {collectionName}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}

export default ChatWindow
