'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

export default function Home() {
  const router = useRouter()

  useEffect(() => {
    router.replace('/world-model')
  }, [router])

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-zinc-500">Redirecting to World Model...</div>
    </div>
  )
}
