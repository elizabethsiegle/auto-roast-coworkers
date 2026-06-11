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

export async function syncTranscripts() {
  await fetch('/api/sync-transcripts')
}
