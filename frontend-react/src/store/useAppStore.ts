import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'

interface AppState {
  theme: 'light' | 'dark'
  selectedWell: string | null
  selectedTab: string
  refreshInterval: number
  // Actions
  setTheme: (theme: 'light' | 'dark') => void
  setSelectedWell: (wellId: string | null) => void
  setSelectedTab: (tab: string) => void
  setRefreshInterval: (interval: number) => void
  toggleTheme: () => void
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      theme: 'light',
      selectedWell: null,
      selectedTab: 'overview',
      refreshInterval: 30,
      
      setTheme: (theme) => set({ theme }),
      setSelectedWell: (wellId) => set({ selectedWell: wellId }),
      setSelectedTab: (tab) => set({ selectedTab: tab }),
      setRefreshInterval: (interval) => set({ refreshInterval: interval }),
      toggleTheme: () => set((state) => ({ theme: state.theme === 'light' ? 'dark' : 'light' })),
    }),
    {
      name: 'fidps-storage',
      storage: createJSONStorage(() => localStorage),
    }
  )
)

