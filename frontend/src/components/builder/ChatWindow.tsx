import React, { useState, useRef, useEffect } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card } from '@/components/ui/card'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Send, MessageSquare, Loader2, Plus, Trash, Edit2 } from 'lucide-react'
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
  const [selectedChatId, setSelectedChatId] = useState<string | null>(null)
  const [isStreaming, setIsStreaming] = useState(false)
  const [editingChatId, setEditingChatId] = useState<string | null>(null)
  const [editTitle, setEditTitle] = useState('')
  
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const queryClient = useQueryClient()

  const { nodes } = useBuilderStore()
  const collectionName = nodes.find((n) => n.type === 'knowledgeBase')?.data.config.collection || 'default'

  // Fetch chats list
  const { data: chats, isLoading: isChatsLoading } = useQuery({
    queryKey: ['chats', workflowId],
    queryFn: () => workflowId ? api.getChats(workflowId) : Promise.resolve([]),
    enabled: isOpen && !!workflowId,
  })

  // Auto-select latest chat or create new if empty
  useEffect(() => {
    if (isOpen && workflowId && chats !== undefined) {
      if (chats.length > 0 && !selectedChatId) {
        setSelectedChatId(chats[0].id)
      } else if (chats.length === 0 && !selectedChatId && !createChatMutation.isPending) {
        createChatMutation.mutate()
      }
    }
  }, [isOpen, workflowId, chats, selectedChatId])

  // Fetch selected chat messages
  useQuery({
    queryKey: ['chat', workflowId, selectedChatId],
    queryFn: async () => {
      if (!workflowId || !selectedChatId) return null
      const chatWithMessages = await api.getChat(workflowId, selectedChatId)
      const formattedMessages = chatWithMessages.messages.map(m => ({
        id: m.id,
        content: m.content,
        role: m.role as 'user' | 'assistant',
        timestamp: new Date(m.created_at)
      }))
      setMessages(formattedMessages)
      return chatWithMessages
    },
    enabled: !!workflowId && !!selectedChatId,
  })

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const createChatMutation = useMutation({
    mutationFn: () => api.createChat(workflowId!),
    onSuccess: (data: Chat) => {
      queryClient.invalidateQueries({ queryKey: ['chats', workflowId] })
      setSelectedChatId(data.id)
    },
  })

  const updateChatMutation = useMutation({
    mutationFn: ({ chatId, title }: { chatId: string, title: string }) => api.updateChat(workflowId!, chatId, title),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chats', workflowId] })
      setEditingChatId(null)
    },
  })

  const deleteChatMutation = useMutation({
    mutationFn: (chatId: string) => api.deleteChat(workflowId!, chatId),
    onSuccess: (_, deletedChatId) => {
      queryClient.invalidateQueries({ queryKey: ['chats', workflowId] })
      if (selectedChatId === deletedChatId) {
        setSelectedChatId(null)
      }
    },
  })

  const handleSendMessage = async () => {
    if (!inputValue.trim() || !workflowId || !selectedChatId || isStreaming) return

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

      const stream = api.sendMessage(workflowId, selectedChatId, prompt)

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
            ? { ...msg, content: 'Error: Failed to get response.' }
            : msg
        )
      )
    } finally {
      setIsStreaming(false)
      queryClient.invalidateQueries({ queryKey: ['chat', workflowId, selectedChatId] })
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const handleClose = () => {
    setSelectedChatId(null)
    setMessages([])
    onClose()
  }

  const startEditing = (chat: Chat, e: React.MouseEvent) => {
    e.stopPropagation()
    setEditingChatId(chat.id)
    setEditTitle(chat.title || 'New Chat')
  }

  const handleRenameSubmit = (chatId: string) => {
    if (editTitle.trim()) {
      updateChatMutation.mutate({ chatId, title: editTitle.trim() })
    } else {
      setEditingChatId(null)
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent aria-describedby={undefined} className="max-w-6xl h-[800px] flex flex-col p-0 overflow-hidden">
        <DialogHeader className="p-4 border-b">
          <DialogTitle className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5" />
            Chat with Your Workflow
          </DialogTitle>
        </DialogHeader>

        <div className="flex flex-1 overflow-hidden">
          {/* Sidebar */}
          <div className="w-64 border-r bg-gray-50 flex flex-col">
            <div className="p-4 border-b">
              <Button 
                onClick={() => createChatMutation.mutate()} 
                className="w-full flex items-center gap-2"
                disabled={createChatMutation.isPending}
              >
                {createChatMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
                New Chat
              </Button>
            </div>
            <div className="flex-1 overflow-y-auto p-2 space-y-2">
              {isChatsLoading ? (
                <div className="flex justify-center p-4">
                  <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
                </div>
              ) : chats?.map((chat) => (
                <div 
                  key={chat.id} 
                  className={`group flex items-center justify-between p-2 rounded-md cursor-pointer text-sm ${selectedChatId === chat.id ? 'bg-blue-100 text-blue-900' : 'hover:bg-gray-200 text-gray-700'}`}
                  onClick={() => setSelectedChatId(chat.id)}
                >
                  {editingChatId === chat.id ? (
                    <Input
                      autoFocus
                      value={editTitle}
                      onChange={(e) => setEditTitle(e.target.value)}
                      onBlur={() => handleRenameSubmit(chat.id)}
                      onKeyDown={(e) => e.key === 'Enter' && handleRenameSubmit(chat.id)}
                      className="h-7 text-sm px-2 py-1"
                      onClick={(e) => e.stopPropagation()}
                    />
                  ) : (
                    <span className="truncate flex-1">{chat.title || 'New Chat'}</span>
                  )}
                  
                  {editingChatId !== chat.id && (
                    <div className="flex gap-1 opacity-0 group-hover:opacity-100">
                      <Button 
                        variant="ghost" 
                        size="icon" 
                        className="h-6 w-6 text-gray-500 hover:text-blue-600"
                        onClick={(e) => startEditing(chat, e)}
                        title="Rename"
                      >
                        <Edit2 className="h-3 w-3" />
                      </Button>
                      <Button 
                        variant="ghost" 
                        size="icon" 
                        className="h-6 w-6 text-gray-500 hover:text-red-600"
                        onClick={(e) => {
                          e.stopPropagation();
                          if (confirm('Are you sure you want to delete this chat?')) {
                            deleteChatMutation.mutate(chat.id);
                          }
                        }}
                        title="Delete"
                      >
                        <Trash className="h-3 w-3" />
                      </Button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Main Chat Area */}
          <div className="flex-1 flex flex-col bg-white">
            <div className="flex-1 overflow-y-auto space-y-4 p-4">
              {messages.length === 0 ? (
                <div className="flex items-center justify-center h-full">
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
                        msg.role === 'user' ? 'bg-blue-600 text-white shadow-md' : 'bg-gray-100 border-none shadow-sm'
                      }`}
                    >
                      <div className={`text-sm leading-relaxed whitespace-pre-wrap ${msg.role === 'user' ? 'text-white' : 'text-gray-800'}`}>
                        {msg.content}
                      </div>
                      <div className={`text-xs mt-2 ${msg.role === 'user' ? 'text-blue-100' : 'text-gray-400'}`}>
                        {msg.timestamp.toLocaleTimeString()}
                      </div>
                    </Card>
                  </div>
                ))
              )}
              {isStreaming && (
                <div className="flex justify-start">
                  <Card className="bg-gray-100 border-none shadow-sm p-4">
                    <div className="flex items-center text-gray-500">
                      <Loader2 className="h-4 w-4 animate-spin mr-2" />
                      <span className="text-sm">Processing through workflow...</span>
                    </div>
                  </Card>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            <div className="p-4 border-t bg-gray-50">
              <div className="flex space-x-3">
                <Input
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask anything about your knowledge base..."
                  disabled={isStreaming || !selectedChatId}
                  className="flex-1 h-12 bg-white"
                />
                <Button
                  onClick={handleSendMessage}
                  disabled={!inputValue.trim() || isStreaming || !selectedChatId}
                  size="lg"
                  className="px-6"
                >
                  {isStreaming ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                </Button>
              </div>
              {workflowId && (
                <div className="text-xs text-gray-400 mt-2 text-center">
                  Workflow ID: {workflowId} | Collection: {collectionName}
                </div>
              )}
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}

export default ChatWindow
