import { ReactNode, useEffect } from 'react'
import Sidebar from './Sidebar'
import Navbar from './Navbar'
import { useWebSocketStore } from '../../store/useWebSocketStore'

interface LayoutProps {
  children: ReactNode
}

const Layout = ({ children }: LayoutProps) => {
  const { connect, disconnect } = useWebSocketStore()

  useEffect(() => {
    connect()
    return () => {
      disconnect()
    }
  }, [])

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="flex">
        <Sidebar />
        <main className="flex-1 p-6 mt-20 ml-64">
          {children}
        </main>
      </div>
    </div>
  )
}

export default Layout
