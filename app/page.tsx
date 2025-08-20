import dynamic from 'next/dynamic'

// Dynamically import the landing page component with no SSR
const LandingPage = dynamic(() => import('../components/LandingPage'), {
  ssr: false,
  loading: () => (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-green-50 flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-600">Welcome to Dr. Sigmund Spend's Financial Therapy...</p>
      </div>
    </div>
  )
})

export default function Home() {
  return <LandingPage />
}
