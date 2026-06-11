import { useState, useEffect } from 'react'
import Sidebar from './components/Sidebar'
import RoastPanel from './components/RoastPanel'
import { fetchCoworkers, fetchRoast, uploadTranscript } from './api'

export default function App() {
  const [coworkers, setCoworkers] = useState([])
  const [selected, setSelected] = useState(null)
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchCoworkers()
      .then(setCoworkers)
      .catch(() => setError('Failed to load coworkers — is the backend running?'))
  }, [])

  async function handleSelect(name) {
    setSelected(name)
    setReport(null)
    setError(null)
    setLoading(true)
    try {
      const result = await fetchRoast(name)
      setReport(result)
    } catch {
      setError('Failed to generate roast. Check the backend logs.')
    } finally {
      setLoading(false)
    }
  }

  async function handleUpload(file) {
    if (!selected) return
    try {
      await uploadTranscript(selected, file)
    } catch {
      setError('Failed to upload transcript.')
    }
  }

  return (
    <div className="app">
      <Sidebar coworkers={coworkers} selected={selected} onSelect={handleSelect} />
      <RoastPanel
        selected={selected}
        report={report}
        loading={loading}
        error={error}
        onUpload={handleUpload}
      />
    </div>
  )
}
