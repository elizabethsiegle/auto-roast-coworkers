export default function Sidebar({ coworkers, selected, onSelect }) {
  return (
    <aside style={{
      width: '240px',
      minWidth: '240px',
      background: '#1a1a1a',
      borderRight: '1px solid #2a2a2a',
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden',
    }}>
      <div style={{
        padding: '20px 16px 12px',
        fontSize: '11px',
        fontWeight: '600',
        letterSpacing: '0.08em',
        textTransform: 'uppercase',
        color: '#555',
      }}>
        Your Coworkers
      </div>
      <div style={{ overflowY: 'auto', flex: 1 }}>
        {coworkers.length === 0 && (
          <div style={{ padding: '12px 16px', color: '#444', fontSize: '13px' }}>
            Loading...
          </div>
        )}
        {coworkers.map(name => (
          <button
            key={name}
            onClick={() => onSelect(name)}
            style={{
              display: 'block',
              width: '100%',
              textAlign: 'left',
              padding: '10px 16px',
              background: selected === name ? '#252525' : 'transparent',
              color: selected === name ? '#fff' : '#aaa',
              border: 'none',
              borderLeft: selected === name ? '3px solid #e63946' : '3px solid transparent',
              cursor: 'pointer',
              fontSize: '14px',
              transition: 'all 0.1s',
            }}
          >
            {name}
          </button>
        ))}
      </div>
    </aside>
  )
}
