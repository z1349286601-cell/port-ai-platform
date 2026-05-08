function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-port-blue text-white p-4 shadow-md">
        <h1 className="text-xl font-bold">港口AI智能平台</h1>
        <p className="text-sm text-gray-300">Phase 1 MVP</p>
      </header>
      <main className="max-w-4xl mx-auto p-4">
        <div className="bg-white rounded-lg shadow p-8 mt-8 text-center">
          <h2 className="text-lg text-gray-600 mb-4">系统已就绪</h2>
          <p className="text-gray-400">
            后端 API: <a href="/api/v1/health" className="text-port-sky underline">健康检查</a>
            {' | '}
            <a href="/docs" className="text-port-sky underline">Swagger 文档</a>
          </p>
        </div>
      </main>
    </div>
  )
}

export default App
