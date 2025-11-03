# FIDPS React Dashboard

React.js dashboard for the Formation Integrity Damage Prevention System (FIDPS).

## Features

- ✅ **Real-time Monitoring** - Live updates via WebSocket
- ✅ **Damage Diagnostics** - Formation damage type classification (DT-01 to DT-10)
- ✅ **RTO Control** - Real-Time Optimization recommendations with approval workflow
- ✅ **Dashboard Overview** - Key metrics and KPIs
- ✅ **Modern UI** - Built with React 18, TypeScript, and Tailwind CSS
- ✅ **Responsive Design** - Works on desktop, tablet, and mobile

## Technology Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Styling
- **React Router** - Navigation
- **React Query** - Data fetching and caching
- **Zustand** - State management
- **Chart.js / Recharts** - Data visualization
- **Socket.io Client** - WebSocket integration
- **date-fns** - Date utilities
- **React Hot Toast** - Notifications

## Installation

```bash
cd frontend-react
npm install
```

## Development

```bash
npm run dev
```

The app will be available at `http://localhost:5173`

## Build for Production

```bash
npm run build
```

## Project Structure

```
frontend-react/
├── src/
│   ├── components/
│   │   ├── Dashboard/       # Dashboard components
│   │   └── Layout/          # Layout components (Navbar, Sidebar)
│   ├── pages/               # Page components
│   ├── services/            # API services
│   ├── store/               # State management (Zustand)
│   ├── App.tsx              # Main app component
│   └── main.tsx             # Entry point
├── public/                  # Static assets
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

## API Integration

The dashboard connects to the FastAPI backend at `http://localhost:8000`. WebSocket connections use Socket.io protocol.

## Environment Variables

Create a `.env` file:

```env
VITE_API_URL=http://localhost:8000/api/v1
```

## License

Proprietary - FIDPS Project

