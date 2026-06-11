import { useRef } from 'react'

export default function RoastPanel({ selected, report, loading, error, onUpload }) {
  const fileInputRef = useRef(null)

  function handleDrop(e) {
    e.preventDefault()
    const file = e.dataTransfer.files[0]
    if (file) onUpload(file)
  }

  return (
    <main style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <div style={{ flex: 1, overflowY: 'auto', padding: '40px' }}>
        {!selected && <EmptyState />}
        {selected && loading && <Spinner name={selected} />}
        {selected && error && <ErrorMessage message={error} />}
        {selected && report && !loading && <Report report={report} />}
      </div>

      {selected && (
        <UploadZone
          selectedName={selected}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".vtt,.txt"
            style={{ display: 'none' }}
            onChange={e => { const f = e.target.files[0]; if (f) onUpload(f) }}
          />
        </UploadZone>
      )}
    </main>
  )
}

function EmptyState() {
  return (
    <div style={{ color: '#444', fontSize: '15px', marginTop: '80px', textAlign: 'center' }}>
      Select a coworker to generate their roast report.
    </div>
  )
}

function Spinner({ name }) {
  return (
    <div style={{ textAlign: 'center', marginTop: '80px' }}>
      <div style={{ fontSize: '32px', marginBottom: '16px' }}>⚙️</div>
      <div style={{ color: '#777', fontSize: '14px' }}>Digging up dirt on {name}...</div>
    </div>
  )
}

function ErrorMessage({ message }) {
  return (
    <div style={{
      background: '#1e0a0a',
      border: '1px solid #4a1a1a',
      borderRadius: '8px',
      padding: '16px',
      color: '#ff6b6b',
      fontSize: '14px',
      marginTop: '40px',
    }}>
      {message}
    </div>
  )
}

function Report({ report }) {
  return (
    <div>
      <h1 style={{ fontSize: '22px', fontWeight: '700', marginBottom: '32px', color: '#fff', lineHeight: 1.3 }}>
        {report.title}
      </h1>
      {(report.sections || []).map(section => (
        <div key={section.heading} style={{
          background: '#1a1a1a',
          border: '1px solid #2a2a2a',
          borderRadius: '10px',
          padding: '24px',
          marginBottom: '16px',
        }}>
          <div style={{
            fontSize: '11px',
            fontWeight: '600',
            letterSpacing: '0.08em',
            textTransform: 'uppercase',
            color: '#e63946',
            marginBottom: '10px',
          }}>
            {section.heading}
          </div>
          <p style={{ fontSize: '15px', lineHeight: 1.65, color: '#ddd' }}>
            {section.content}
          </p>
        </div>
      ))}
    </div>
  )
}

function UploadZone({ selectedName, onDrop, onClick, children }) {
  return (
    <div
      onDrop={onDrop}
      onDragOver={e => e.preventDefault()}
      onClick={onClick}
      style={{
        borderTop: '1px solid #2a2a2a',
        padding: '14px 40px',
        display: 'flex',
        alignItems: 'center',
        gap: '10px',
        color: '#555',
        fontSize: '13px',
        cursor: 'pointer',
      }}
      onMouseEnter={e => e.currentTarget.style.background = '#141414'}
      onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
    >
      <span style={{ fontSize: '16px' }}>📎</span>
      Drop a meeting transcript (.vtt or .txt) to add evidence for {selectedName}
      {children}
    </div>
  )
}
