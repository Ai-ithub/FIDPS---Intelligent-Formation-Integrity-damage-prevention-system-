import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  Gauge,
  Droplets,
  Wrench,
  AlertTriangle,
  Database,
  Settings,
  Package,
  CheckCircle,
} from 'lucide-react'

const Sidebar = () => {
  const navItems = [
    { path: '/', icon: LayoutDashboard, label: 'Overview' },
    { path: '/kpis', icon: Gauge, label: 'Critical KPIs' },
    { path: '/mud-parameters', icon: Droplets, label: 'Mud Parameters' },
    { path: '/drilling-formation', icon: Wrench, label: 'Drilling & Formation' },
    { path: '/wells', icon: Package, label: 'Wells Management' },
    { path: '/anomalies', icon: AlertTriangle, label: 'Anomalies' },
    { path: '/alerts', icon: AlertTriangle, label: 'Alerts' },
    { path: '/data', icon: Database, label: 'Data' },
    { path: '/data-quality', icon: CheckCircle, label: 'Data Quality' },
    { path: '/system', icon: Settings, label: 'System' },
  ]

  return (
    <aside className="fixed left-0 top-20 h-[calc(100vh-5rem)] w-64 bg-white border-r border-gray-200 shadow-sm z-10">
      <nav className="p-4">
        <ul className="space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon
            return (
              <li key={item.path}>
                <NavLink
                  to={item.path}
                  className={({ isActive }) =>
                    `flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors duration-200 ${
                      isActive
                        ? 'bg-primary-600 text-white shadow-md'
                        : 'text-gray-700 hover:bg-gray-100'
                    }`
                  }
                >
                  <Icon className="h-5 w-5" />
                  <span className="font-medium">{item.label}</span>
                </NavLink>
              </li>
            )
          })}
        </ul>
      </nav>
    </aside>
  )
}

export default Sidebar

