import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import BuilderPage from '@/components/builder/BuilderPage'

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
      <div className="App">
        <BuilderPage />
      </div>
    </QueryClientProvider>
  )
}

export default App