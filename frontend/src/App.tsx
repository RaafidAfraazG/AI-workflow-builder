import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import BuilderPage from '@/components/builder/BuilderPage'
import WorkflowList from '@/components/WorkflowList'

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="App">
          <Routes>
            <Route path="/" element={<WorkflowList />} />
            <Route path="/builder" element={<BuilderPage />} />
            <Route path="/builder/:id" element={<BuilderPage />} />
          </Routes>
        </div>
      </Router>
    </QueryClientProvider>
  )
}

export default App