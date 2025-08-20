import dynamic from 'next/dynamic'

// Dynamically import the cabinet component with no SSR
const CabinetLayout = dynamic(() => import('../../components/CabinetLayout'), {
  ssr: false,
  loading: () => (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-600">Preparing your therapy session...</p>
      </div>
    </div>
  )
})

export default function Cabinet() {
  return <CabinetLayout />
}