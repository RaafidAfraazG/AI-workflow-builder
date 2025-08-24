import { useEffect, useState } from "react"
import useBuilderStore from "@/store/builderStore"
import { Upload, FileText, Trash2, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { api } from "@/lib/api"

const ConfigPanel = () => {
  const { selectedNode, updateNode } = useBuilderStore()
  const config = selectedNode?.data?.config || {}

  const [localPrompt, setLocalPrompt] = useState("")
  const [isUploading, setIsUploading] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)

  // Sync when node changes
  useEffect(() => {
    if (selectedNode?.type === "llmEngine") {
      setLocalPrompt(config.customPrompt || "")
    } else if (selectedNode?.type === "userQuery") {
      setLocalPrompt(config.queryText || "")
    } else {
      setLocalPrompt("")
    }
  }, [selectedNode?.id])

  if (!selectedNode) {
    return (
      <div className="p-4 text-gray-500 text-sm">
        Select a node to edit its configuration.
      </div>
    )
  }

  const handleConfigChange = (field: string, value: any) => {
    updateNode(selectedNode.id, {
      data: {
        ...selectedNode.data,
        config: {
          ...config,
          [field]: value,
        },
      },
    })
  }

  // File upload logic (real API call)
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    if (file.type !== "application/pdf") {
      alert("Please upload PDF files only")
      return
    }

    setIsUploading(true)
    setUploadError(null)

    try {
      // Call backend upload
      const newDoc = await api.uploadDocument(file)

      // Add to config
      handleConfigChange("documents", [...(config.documents || []), newDoc])

      // Immediately trigger ingestion
      await api.ingestDocument(newDoc.id)
    } catch (err: any) {
      console.error("Upload failed:", err)
      setUploadError(err.message || "Upload failed. Please try again.")
    } finally {
      setIsUploading(false)
      e.target.value = "" // reset input
    }
  }

  const removeDocument = async (docId: string) => {
    try {
      await fetch(`/api/kb/${docId}`, { method: "DELETE" })
      const updated = (config.documents || []).filter((doc: any) => doc.id !== docId)
      handleConfigChange("documents", updated)
    } catch (err) {
      console.error("Delete failed:", err)
      alert("Failed to delete document. Check backend logs.")
    }
  }

  // Render fields based on node type
  const renderFields = () => {
    switch (selectedNode.type) {
      case "userQuery":
        return (
          <div>
            <label className="text-xs font-medium">User Input</label>
            <textarea
              value={localPrompt}
              onChange={(e) => {
                setLocalPrompt(e.target.value)
                handleConfigChange("queryText", e.target.value)
              }}
              placeholder="Enter your question..."
              rows={2}
              className="w-full p-2 border rounded-md resize-none text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        )

      case "knowledgeBase":
        return (
          <div className="space-y-4">
            {/* Collection */}
            <div>
              <label className="text-xs font-medium">Collection</label>
              <input
                type="text"
                value={config.collection || "default"}
                onChange={(e) =>
                  handleConfigChange("collection", e.target.value)
                }
                className="w-full p-2 border rounded-md text-sm"
              />
            </div>

            {/* Top K */}
            <div>
              <label className="text-xs font-medium">Top K</label>
              <input
                type="number"
                value={config.topK ?? 5}
                onChange={(e) =>
                  handleConfigChange("topK", parseInt(e.target.value))
                }
                className="w-full p-2 border rounded-md text-sm"
              />
            </div>

            {/* File Upload */}
            <div>
              <label className="text-xs font-medium mb-2 block">
                Upload Documents
              </label>
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-4">
                <input
                  type="file"
                  accept=".pdf"
                  onChange={handleFileUpload}
                  disabled={isUploading}
                  className="hidden"
                  id="pdf-upload"
                />
                <label
                  htmlFor="pdf-upload"
                  className="flex flex-col items-center justify-center cursor-pointer"
                >
                  {isUploading ? (
                    <Loader2 className="h-8 w-8 animate-spin text-gray-400 mb-2" />
                  ) : (
                    <Upload className="h-8 w-8 text-gray-400 mb-2" />
                  )}
                  <span className="text-sm text-gray-600">
                    {isUploading ? "Uploading..." : "Click to upload PDF"}
                  </span>
                </label>
              </div>
              {uploadError && (
                <p className="text-xs text-red-500 mt-1">{uploadError}</p>
              )}
            </div>

            {/* Uploaded Documents */}
            {config.documents && config.documents.length > 0 && (
              <div>
                <label className="text-xs font-medium mb-2 block">
                  Uploaded Documents
                </label>
                <div className="space-y-2 max-h-32 overflow-y-auto">
                  {config.documents.map((doc: any) => (
                    <div
                      key={doc.id}
                      className="flex items-center justify-between p-2 bg-white rounded border"
                    >
                      <div className="flex items-center space-x-2 flex-1 min-w-0">
                        <FileText className="h-4 w-4 text-red-500 flex-shrink-0" />
                        <span className="text-xs truncate">{doc.file_name || doc.filename}</span>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => removeDocument(doc.id)}
                        className="p-1 h-6 w-6"
                      >
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )

      case "llmEngine":
        return (
          <>
            {/* Provider */}
            <div>
              <label className="text-xs font-medium">Provider</label>
              <input
                type="text"
                value={config.provider || ""}
                onChange={(e) => handleConfigChange("provider", e.target.value)}
                className="w-full p-2 border rounded-md text-sm"
              />
            </div>

            {/* Model */}
            <div>
              <label className="text-xs font-medium">Model</label>
              <input
                type="text"
                value={config.model || ""}
                onChange={(e) => handleConfigChange("model", e.target.value)}
                className="w-full p-2 border rounded-md text-sm"
              />
            </div>

            {/* Temperature */}
            <div>
              <label className="text-xs font-medium">Temperature</label>
              <input
                type="number"
                min={0}
                max={1}
                step={0.1}
                value={config.temperature ?? 0.7}
                onChange={(e) =>
                  handleConfigChange("temperature", parseFloat(e.target.value))
                }
                className="w-full p-2 border rounded-md text-sm"
              />
            </div>

            {/* Custom Prompt */}
            <div>
              <label className="text-xs font-medium">Custom Prompt</label>
              <textarea
                value={localPrompt}
                onChange={(e) => {
                  setLocalPrompt(e.target.value)
                  handleConfigChange("customPrompt", e.target.value)
                }}
                placeholder="Enter custom prompt template..."
                rows={4}
                className="w-full p-2 border rounded-md resize-none text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                style={{ fontFamily: "inherit" }}
              />
            </div>
          </>
        )

      case "output":
        return (
          <div>
            <label className="text-xs font-medium">Format</label>
            <input
              type="text"
              value={config.format || "text"}
              onChange={(e) => handleConfigChange("format", e.target.value)}
              className="w-full p-2 border rounded-md text-sm"
            />
          </div>
        )

      default:
        return <div className="text-gray-500 text-sm">No config available</div>
    }
  }

  return (
    <div className="p-4 space-y-4">
      <h3 className="text-lg font-semibold mb-2">
        {selectedNode.data.label} Config
      </h3>
      {renderFields()}
    </div>
  )
}

export default ConfigPanel
