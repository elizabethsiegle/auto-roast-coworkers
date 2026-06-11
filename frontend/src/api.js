export async function fetchCoworkers() {
  const res = await fetch('/api/coworkers')
  if (!res.ok) throw new Error('Failed to fetch coworkers')
  const data = await res.json()
  return data.coworkers
}

export async function fetchRoast(name) {
  const res = await fetch('/api/roast', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  })
  if (!res.ok) throw new Error('Failed to generate roast')
  return res.json()
}

export async function uploadTranscript(name, file) {
  const formData = new FormData()
  formData.append('name', name)
  formData.append('file', file)
  const res = await fetch('/api/upload-transcript', {
    method: 'POST',
    body: formData,
  })
  if (!res.ok) throw new Error('Failed to upload transcript')
  return res.json()
}
