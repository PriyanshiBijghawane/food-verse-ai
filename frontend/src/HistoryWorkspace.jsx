import React, { useState, useEffect } from 'react'
import {
  History,
  Trash2,
  Search,
  ScanLine,
  Leaf,
  Store,
  ChefHat,
  CalendarDays,
  AlertCircle,
  CheckCircle2,
  Loader2,
  RefreshCw,
  Clock
} from 'lucide-react'

export default function HistoryWorkspace({ apiBaseUrl }) {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [filterType, setFilterType] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [deletingId, setDeletingId] = useState(null)
  const [selectedItem, setSelectedItem] = useState(null)
  const [feedbackMsg, setFeedbackMsg] = useState(null)
  const [loadError, setLoadError] = useState(null)

  const fetchHistory = async () => {
    setLoading(true)
    setLoadError(null)
    try {
      const res = await fetch(`${apiBaseUrl}/api/v1/history`)
      const data = await res.json().catch(() => null)
      if (!res.ok) {
        throw new Error(data?.detail || `History request failed (HTTP ${res.status}).`)
      }
      if (!Array.isArray(data)) {
        throw new Error('The history API returned an unexpected response.')
      }
      setItems(data)
    } catch (err) {
      setLoadError(err instanceof TypeError
        ? `Cannot reach the Food Verse API at ${apiBaseUrl}.`
        : err.message || 'Failed to load analysis history.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchHistory()
  }, [apiBaseUrl])

  const handleDelete = async (id, e) => {
    e.stopPropagation()
    if (!window.confirm('Are you sure you want to delete this analysis record and associated media?')) return

    setDeletingId(id)
    try {
      const res = await fetch(`${apiBaseUrl}/api/v1/history/${id}`, {
        method: 'DELETE',
      })
      if (res.ok) {
        setItems((prev) => prev.filter((item) => item.id !== id))
        if (selectedItem?.id === id) setSelectedItem(null)
        setFeedbackMsg({ type: 'success', text: 'Record deleted successfully.' })
        setTimeout(() => setFeedbackMsg(null), 3000)
      } else {
        const err = await res.json()
        alert(`Failed to delete record: ${err.detail || 'Unknown error'}`)
      }
    } catch (err) {
      alert(`Deletion network error: ${err.message}`)
    } finally {
      setDeletingId(null)
    }
  }

  const getTypeIcon = (type) => {
    switch (type) {
      case 'food':
        return <ScanLine className="w-5 h-5 text-emerald-600" />
      case 'freshness':
        return <Leaf className="w-5 h-5 text-green-600" />
      case 'hygiene':
        return <Store className="w-5 h-5 text-amber-600" />
      case 'recipe':
        return <ChefHat className="w-5 h-5 text-orange-600" />
      case 'meal_plan':
        return <CalendarDays className="w-5 h-5 text-purple-600" />
      default:
        return <History className="w-5 h-5 text-gray-500" />
    }
  }

  const filteredItems = items.filter((item) => {
    const matchesType = filterType === 'all' || item.type === filterType
    const matchesSearch =
      !searchQuery.trim() ||
      item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.summary.toLowerCase().includes(searchQuery.toLowerCase())
    return matchesType && matchesSearch
  })

  return (
    <div className="history-page">
      {/* Header Banner */}
      <header className="history-header">
        <div className="history-header-row">
          <div className="history-heading">
            <div className="history-heading-icon">
              <History size={24} aria-hidden="true" />
            </div>
            <div>
              <h1>Analysis &amp; Intelligence History</h1>
              <p>
                Review or delete previously recorded food analyses, freshness assessments, inspections, and recipes.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={fetchHistory}
            className="history-refresh"
            title="Refresh history"
          >
            <RefreshCw size={16} aria-hidden="true" />
            <span>Refresh</span>
          </button>
        </div>

        {feedbackMsg && (
          <div className="history-feedback" role="status">
            <CheckCircle2 size={17} aria-hidden="true" />
            <span>{feedbackMsg.text}</span>
          </div>
        )}

        <div className="history-toolbar">
          <div className="history-filters" aria-label="Filter history">
            {[
              { id: 'all', label: 'All Activities' },
              { id: 'food', label: 'Food Recognition' },
              { id: 'freshness', label: 'Freshness' },
              { id: 'hygiene', label: 'Kitchen Hygiene' },
              { id: 'recipe', label: 'Recipes' },
              { id: 'meal_plan', label: 'Meal Plans' },
            ].map((f) => (
              <button
                type="button"
                key={f.id}
                onClick={() => setFilterType(f.id)}
                className={`history-filter ${filterType === f.id ? 'history-filter-active' : ''}`}
                aria-pressed={filterType === f.id}
              >
                {f.label}
              </button>
            ))}
          </div>

          <label className="history-search">
            <Search size={16} aria-hidden="true" />
            <input
              type="search"
              placeholder="Search past analyses..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </label>
        </div>
      </header>

      <main className="history-content">
        {loading ? (
          <div className="history-state">
            <Loader2 className="history-spinner" size={30} aria-hidden="true" />
            <p>Loading historical records...</p>
          </div>
        ) : loadError ? (
          <div className="history-state history-state-error" role="alert">
            <AlertCircle size={30} aria-hidden="true" />
            <h2>History Could Not Be Loaded</h2>
            <p>{loadError}</p>
            <button type="button" onClick={fetchHistory} className="history-refresh">
              <RefreshCw size={16} aria-hidden="true" />
              Retry
            </button>
          </div>
        ) : filteredItems.length === 0 ? (
          <div className="history-state">
            <History size={34} aria-hidden="true" />
            <h2>No Analysis Records Found</h2>
            <p>
              {searchQuery || filterType !== 'all'
                ? 'No records match these filters. Try another search or select All Activities.'
                : 'Run a food analysis, freshness check, kitchen inspection, or generate a recipe to see records here.'}
            </p>
          </div>
        ) : (
          <div className="history-grid">
            {filteredItems.map((item) => (
              <article
                key={item.id}
                onClick={() => setSelectedItem(item)}
                onKeyDown={(event) => {
                  if (event.target !== event.currentTarget) return
                  if (event.key === 'Enter' || event.key === ' ') {
                    event.preventDefault()
                    setSelectedItem(item)
                  }
                }}
                role="button"
                tabIndex={0}
                className="history-card"
              >
                <div className="history-card-top">
                  <div className="history-type">
                    <span className={`history-type-icon history-type-${item.type}`}>
                      {getTypeIcon(item.type)}
                    </span>
                    <span>{item.type.replace('_', ' ')}</span>
                  </div>
                  <span className={`history-mode ${item.execution_mode === 'demo' ? 'history-mode-demo' : ''}`}>
                    {item.execution_mode}
                  </span>
                </div>

                <div className="history-card-body">
                  <h2>{item.title}</h2>
                  <p>{item.summary}</p>
                </div>

                <div className="history-card-footer">
                  <span className="history-date">
                    <Clock size={14} aria-hidden="true" />
                    {new Date(item.created_at * 1000).toLocaleDateString()}
                  </span>
                  <button
                    type="button"
                    onClick={(e) => handleDelete(item.id, e)}
                    disabled={deletingId === item.id}
                    className="history-delete"
                    title="Delete record"
                    aria-label={`Delete ${item.title}`}
                  >
                    {deletingId === item.id ? (
                      <Loader2 className="history-spinner" size={17} aria-hidden="true" />
                    ) : (
                      <Trash2 size={17} aria-hidden="true" />
                    )}
                  </button>
                </div>
              </article>
            ))}
          </div>
        )}
      </main>

      {selectedItem && (
        <div className="history-modal-backdrop" onClick={() => setSelectedItem(null)}>
          <section
            className="history-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="history-modal-title"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="history-modal-header">
              <div className="history-type">
                <span className={`history-type-icon history-type-${selectedItem.type}`}>
                  {getTypeIcon(selectedItem.type)}
                </span>
                <span>{selectedItem.type.replace('_', ' ')} details</span>
              </div>
              <button type="button" className="history-modal-close" onClick={() => setSelectedItem(null)} aria-label="Close details">
                &times;
              </button>
            </div>

            <h2 id="history-modal-title">{selectedItem.title}</h2>
            <p className="history-modal-summary">{selectedItem.summary}</p>
            <dl className="history-details">
              <div><dt>Record ID</dt><dd>{selectedItem.id}</dd></div>
              <div><dt>Execution mode</dt><dd>{selectedItem.execution_mode}</dd></div>
              <div><dt>Recorded at</dt><dd>{new Date(selectedItem.created_at * 1000).toLocaleString()}</dd></div>
            </dl>

            <div className="history-modal-actions">
              <button type="button" className="history-refresh" onClick={() => setSelectedItem(null)}>Close</button>
              <button
                type="button"
                onClick={(event) => handleDelete(selectedItem.id, event)}
                disabled={deletingId === selectedItem.id}
                className="history-delete-confirm"
              >
                <Trash2 size={16} aria-hidden="true" />
                Delete Record
              </button>
            </div>
          </section>
        </div>
      )}
    </div>
  )
}
