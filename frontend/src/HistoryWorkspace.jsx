import React, { useState, useEffect } from 'react'
import {
  History,
  Trash2,
  ExternalLink,
  Filter,
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

  const fetchHistory = async () => {
    setLoading(true)
    try {
      const res = await fetch(`${apiBaseUrl}/api/v1/history`)
      if (res.ok) {
        const data = await res.json()
        setItems(data)
      }
    } catch (err) {
      console.error('Failed to fetch history:', err)
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
    <div className="workspace-container">
      {/* Header Banner */}
      <div className="workspace-header">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-emerald-100 rounded-xl text-emerald-800">
                <History className="w-6 h-6" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Analysis & Intelligence History</h1>
                <p className="text-sm text-gray-600">
                  Review, audit, or safely delete previously recorded food analyses, freshness assessments, and recipes.
                </p>
              </div>
            </div>
          </div>
          <button
            onClick={fetchHistory}
            className="btn btn-secondary flex items-center gap-2 text-sm"
            title="Refresh history"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>

        {/* Feedback alert */}
        {feedbackMsg && (
          <div className="mt-4 p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 flex items-center gap-2 text-sm">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            {feedbackMsg.text}
          </div>
        )}

        {/* Filter & Search Bar */}
        <div className="mt-6 flex flex-wrap gap-3 items-center justify-between">
          <div className="flex flex-wrap gap-2">
            {[
              { id: 'all', label: 'All Activities' },
              { id: 'food', label: 'Food Recognition' },
              { id: 'freshness', label: 'Freshness' },
              { id: 'hygiene', label: 'Kitchen Hygiene' },
              { id: 'recipe', label: 'Recipes' },
              { id: 'meal_plan', label: 'Meal Plans' },
            ].map((f) => (
              <button
                key={f.id}
                onClick={() => setFilterType(f.id)}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                  filterType === f.id
                    ? 'bg-emerald-700 text-white shadow-sm'
                    : 'bg-white border border-gray-200 text-gray-700 hover:bg-gray-50'
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>

          <div className="relative min-w-[260px]">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search past analyses..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 bg-white border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600"
            />
          </div>
        </div>
      </div>

      {/* Content Area */}
      <div className="mt-6">
        {loading ? (
          <div className="py-20 text-center text-gray-500">
            <Loader2 className="w-8 h-8 animate-spin mx-auto text-emerald-600 mb-3" />
            <p className="text-sm">Loading historical records...</p>
          </div>
        ) : filteredItems.length === 0 ? (
          <div className="py-16 text-center bg-white rounded-2xl border border-gray-100 shadow-sm p-8">
            <div className="w-16 h-16 mx-auto mb-4 bg-gray-50 rounded-full flex items-center justify-center text-gray-400">
              <History className="w-8 h-8" />
            </div>
            <h3 className="text-lg font-semibold text-gray-800">No Analysis Records Found</h3>
            <p className="text-sm text-gray-500 max-w-md mx-auto mt-1">
              {searchQuery || filterType !== 'all'
                ? 'No records match your selected filter. Try clearing the search query or selecting All Activities.'
                : 'Run a Food Analysis, Freshness Check, Kitchen Inspection, or generate a Recipe to see your persistent records here.'}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredItems.map((item) => (
              <div
                key={item.id}
                onClick={() => setSelectedItem(item)}
                className="bg-white rounded-xl p-5 border border-gray-200 hover:border-emerald-500 hover:shadow-md transition-all cursor-pointer flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <div className="p-2 bg-gray-50 rounded-lg">{getTypeIcon(item.type)}</div>
                      <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">
                        {item.type.replace('_', ' ')}
                      </span>
                    </div>
                    <span
                      className={`text-xs px-2.5 py-1 rounded-full font-medium ${
                        item.execution_mode === 'demo'
                          ? 'bg-amber-100 text-amber-800 border border-amber-200'
                          : 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                      }`}
                    >
                      {item.execution_mode.toUpperCase()}
                    </span>
                  </div>

                  <h3 className="font-semibold text-gray-900 text-base line-clamp-1 mb-1">{item.title}</h3>
                  <p className="text-sm text-gray-600 line-clamp-2 mb-4">{item.summary}</p>
                </div>

                <div className="flex items-center justify-between pt-3 border-t border-gray-100 text-xs text-gray-400">
                  <div className="flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5" />
                    <span>{new Date(item.created_at * 1000).toLocaleDateString()}</span>
                  </div>
                  <button
                    onClick={(e) => handleDelete(item.id, e)}
                    disabled={deletingId === item.id}
                    className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                    title="Delete record"
                  >
                    {deletingId === item.id ? (
                      <Loader2 className="w-4 h-4 animate-spin text-red-600" />
                    ) : (
                      <Trash2 className="w-4 h-4" />
                    )}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Details Modal */}
      {selectedItem && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-xl border border-gray-100">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                {getTypeIcon(selectedItem.type)}
                <span className="font-semibold text-gray-800 uppercase text-xs tracking-wider">
                  {selectedItem.type.replace('_', ' ')} Details
                </span>
              </div>
              <button
                onClick={() => setSelectedItem(null)}
                className="text-gray-400 hover:text-gray-600 text-lg font-bold"
              >
                &times;
              </button>
            </div>

            <h2 className="text-xl font-bold text-gray-900 mb-2">{selectedItem.title}</h2>
            <div className="p-3 bg-gray-50 rounded-xl text-sm text-gray-700 mb-4 whitespace-pre-wrap">
              {selectedItem.summary}
            </div>

            <div className="space-y-2 text-xs text-gray-500 mb-6">
              <div className="flex justify-between">
                <span>Record ID:</span>
                <span className="font-mono">{selectedItem.id}</span>
              </div>
              <div className="flex justify-between">
                <span>Execution Mode:</span>
                <span className="font-semibold text-gray-700 uppercase">{selectedItem.execution_mode}</span>
              </div>
              <div className="flex justify-between">
                <span>Recorded At:</span>
                <span>{new Date(selectedItem.created_at * 1000).toLocaleString()}</span>
              </div>
            </div>

            <div className="flex justify-end gap-3">
              <button
                onClick={() => setSelectedItem(null)}
                className="btn btn-secondary text-sm px-4 py-2"
              >
                Close
              </button>
              <button
                onClick={(e) => handleDelete(selectedItem.id, e)}
                className="btn btn-danger text-sm px-4 py-2 flex items-center gap-1.5"
              >
                <Trash2 className="w-4 h-4" />
                Delete Record
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
