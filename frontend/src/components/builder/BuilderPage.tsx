import React from 'react'
import NodePalette from './NodePalette'
import WorkflowCanvas from './WorkflowCanvas'
import ConfigPanel from './ConfigPanel'
import TopBar from './TopBar'

const BuilderPage: React.FC = () => {
  return (
    <div className="h-screen flex flex-col">
      <TopBar />
      <div className="flex-1 flex">
        <NodePalette />
        <div className="flex-1 flex">
          <WorkflowCanvas />
          <ConfigPanel />
        </div>
      </div>
    </div>
  )
}

export default BuilderPage