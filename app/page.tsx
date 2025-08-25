import dynamic from 'next/dynamic'

// Dynamically import the landing page component with no SSR
const LandingPage = dynamic(() => import('../components/LandingPage'), {
  ssr: false,
  loading: () => (
    <div className="min-h-screen bg-white flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-primary mx-auto mb-4"></div>
        <p className="text-gray-600">Welcome to Dr. Sigmund Spend's Financial Therapy...</p>
      </div>
    </div>
  )
})

export default function Home() {
  return <LandingPage />
}
