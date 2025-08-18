import dynamic from 'next/dynamic'

// Dynamically import the dashboard component with no SSR
const DashboardComponent = dynamic(() => import('./DashboardComponent'), {
  ssr: false,
  loading: () => (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
        <p className="text-gray-600">Loading...</p>
      </div>
    </div>
  )
})

export default function Dashboard() {
  return <DashboardComponent />
}
