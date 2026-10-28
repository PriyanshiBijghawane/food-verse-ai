import React, { useState, useRef, useEffect } from 'react'
import {
  LayoutDashboard,
  UtensilsCrossed,
  ScanLine,
  Leaf,
  Store,
  ChefHat,
  CalendarDays,
  Search,
  Bell,
  Menu,
  X,
  ArrowRight,
  ArrowLeft,
  Sparkles,
  Flame,
  Activity,
  HeartPulse,
  Settings,
  HelpCircle,
  Server,
  History,
  Upload,
  Trash2,
  Image as ImageIcon,
  AlertCircle,
  CheckCircle2,
  Loader2,
  User,
  Scale
} from 'lucide-react'
import FreshnessWorkspace from './FreshnessWorkspace'
import HistoryWorkspace from './HistoryWorkspace'
import HygieneWorkspace from './HygieneWorkspace'
import CookingAssistantWorkspace from './CookingWorkspace'
import MealPlannerWorkspace from './MealPlannerWorkspace'
import ProfileWorkspace from './ProfileWorkspace'
import SettingsWorkspace from './SettingsWorkspace'
import DocumentationWorkspace from './DocumentationWorkspace'

const navItems = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'food-recognition', label: 'Food Recognition', icon: ScanLine },
  { id: 'freshness-detection', label: 'Freshness Detection', icon: Leaf },
  { id: 'restaurant-hygiene', label: 'Restaurant Hygiene', icon: Store },
  { id: 'smart-cooking', label: 'Cooking Assistant', icon: ChefHat },
  { id: 'meal-planner', label: 'Meal Planner', icon: CalendarDays },
  { id: 'history', label: 'History', icon: History },
]

const modules = [
  {
    id: 'food-recognition',
    title: 'Food Recognition & Nutrition',
    tag: 'Food-101 Vision',
    badgeClass: 'badge-blue',
    icon: ScanLine,
    description:
      'Classify prepared dishes with Food-101 and review ranked classes using uncalibrated model scores.',
    features: ['Food-101 Classification', 'Top Predictions', 'Nutrition Reference Estimates'],
    actionText: 'Analyze Dish',
    endpoint: 'POST /api/v1/food/recognize',
    details:
      'Returns the model prediction and uncalibrated class scores, not probabilities of correctness. Nutrition is a separate reference estimate; Food-101 does not detect ingredients or estimate portion size.',
  },
  {
    id: 'freshness-detection',
    title: 'Freshness Detection',
    tag: 'Quality Control',
    badgeClass: 'badge-emerald',
    icon: Leaf,
    description:
      'Review visible color and texture cues with transparent computer-vision heuristics and conservative food-safety guidance.',
    features: ['Visible Spoilage Cues', 'Freshness Assessment', 'Safety Limitations'],
    actionText: 'Check Freshness',
    endpoint: 'POST /api/v1/food/freshness',
    details:
      'This endpoint measures visible image features and reports its active analysis mode. A visual assessment cannot determine microbial safety or guarantee an item is safe to eat.',
  },
  {
    id: 'restaurant-hygiene',
    title: 'Restaurant Hygiene',
    tag: 'Inspection & Safety',
    badgeClass: 'badge-amber',
    icon: Store,
    description:
      'Review visible kitchen conditions with the configured inspection engine, including local visual heuristics when no vision model is available.',
    features: ['Visible Condition Review', 'Inspection Findings', 'Human Review Guidance'],
    actionText: 'Inspect Space',
    endpoint: 'POST /api/v1/hygiene/audit',
    details:
      'This endpoint assesses observable conditions in the uploaded image or sampled video frames. It does not measure temperatures or certify regulatory compliance; the active inspection engine is shown in results.',
  },
  {
    id: 'smart-cooking',
    title: 'Smart Cooking Assistant',
    tag: 'Recipe Guidance',
    badgeClass: 'badge-orange',
    icon: ChefHat,
    description:
      'Generate structured recipe guidance from ingredients you enter, with the active recipe engine and fallback mode disclosed.',
    features: ['Step-by-Step Cooking', 'Smart Substitutions', 'Technique Guide'],
    actionText: 'Start Cooking',
    endpoint: 'POST /api/v1/cooking/assistant',
    details:
      'Generates structured recipes from text ingredients. The optional Food-101 image model classifies prepared dishes and is not an ingredient detector; rule-based recipe output is identified as such.',
  },
  {
    id: 'meal-planner',
    title: 'Personalized Meal Planner',
    tag: 'Dietary Intelligence',
    badgeClass: 'badge-purple',
    icon: CalendarDays,
    description:
      'Generate deterministic weekly schedules from biometric targets, dietary preferences, and food restrictions.',
    features: ['Seven-Day Schedule', 'Nutrition Targets', 'Dietary Restrictions'],
    actionText: 'Generate Plan',
    endpoint: 'POST /api/v1/meal-plan/generate',
    details:
      'Calculates nutrition targets and builds a seven-day schedule from the supplied profile and dietary restrictions. The planner is rule-based, not a generative AI model.',
  },
]

export default function App() {
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001'

  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [activeTab, setActiveTab] = useState('dashboard')
  const [searchQuery, setSearchQuery] = useState('')

  // User Profile State with local storage fallback
  const [userProfile, setUserProfile] = useState(() => {
    try {
      const saved = localStorage.getItem('foodverse_profile')
      if (saved) return JSON.parse(saved)
    } catch {}
    return {
      name: 'Jane Doe',
      email: 'jane.doe@example.com',
      age: 28,
      gender: 'female',
      height_cm: 168,
      weight_kg: 65,
      activity_level: 'moderately_active',
      primary_goal: 'weight_loss',
      diet_type: 'balanced',
      allergies: [],
      food_restrictions: [],
      cuisine_preferences: ['Mediterranean', 'Balanced']
    }
  })

  // Application Settings State with local storage fallback
  const [userSettings, setUserSettings] = useState(() => {
    try {
      const saved = localStorage.getItem('foodverse_settings')
      if (saved) return JSON.parse(saved)
    } catch {}
    return {
      units: 'metric',
      default_diet: 'balanced',
      default_cuisine: 'Any',
      default_cooking_time: 30,
      vision_confidence_threshold: 0.20,
      in_app_notifications: true
    }
  })

  // Notifications State
  const [notifications, setNotifications] = useState(() => {
    try {
      const saved = localStorage.getItem('foodverse_notifications')
      if (saved) return JSON.parse(saved)
    } catch {}
    return []
  })
  const [notificationsOpen, setNotificationsOpen] = useState(false)
  const [backendConnected, setBackendConnected] = useState(false)
  const notifDropdownRef = useRef(null)

  // Initial Sync from Backend
  useEffect(() => {
    // Health check
    fetch(`${apiBaseUrl}/health`)
      .then((res) => {
        if (res.ok) setBackendConnected(true)
      })
      .catch(() => setBackendConnected(false))

    // Profile sync
    fetch(`${apiBaseUrl}/api/v1/user/profile`)
      .then((res) => res.ok && res.json())
      .then((data) => {
        if (data?.profile) {
          setUserProfile(data.profile)
          localStorage.setItem('foodverse_profile', JSON.stringify(data.profile))
        }
      })
      .catch(() => {})

    // Settings sync
    fetch(`${apiBaseUrl}/api/v1/user/settings`)
      .then((res) => res.ok && res.json())
      .then((data) => {
        if (data?.settings) {
          setUserSettings(data.settings)
          localStorage.setItem('foodverse_settings', JSON.stringify(data.settings))
        }
      })
      .catch(() => {})

    // Notifications sync
    fetch(`${apiBaseUrl}/api/v1/notifications`)
      .then((res) => res.ok && res.json())
      .then((data) => {
        if (data?.notifications) {
          setNotifications(data.notifications)
          localStorage.setItem('foodverse_notifications', JSON.stringify(data.notifications))
        }
      })
      .catch(() => {})
  }, [apiBaseUrl])

  // Close notifications on outside click
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (notifDropdownRef.current && !notifDropdownRef.current.contains(e.target)) {
        setNotificationsOpen(false)
      }
    }
    if (notificationsOpen) {
      document.addEventListener('mousedown', handleClickOutside)
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [notificationsOpen])

  // Notification actions
  const addNotification = (notif) => {
    if (userSettings?.in_app_notifications === false) return
    const newNotif = {
      id: notif.id || `notif-${Date.now()}`,
      title: notif.title,
      message: notif.message,
      type: notif.type || 'info',
      timestamp: Date.now(),
      read: false,
      module: notif.module || null
    }

    setNotifications((prev) => {
      const updated = [newNotif, ...prev.filter(n => n.id !== newNotif.id)].slice(0, 50)
      localStorage.setItem('foodverse_notifications', JSON.stringify(updated))
      return updated
    })

    fetch(`${apiBaseUrl}/api/v1/notifications`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newNotif)
    }).catch(() => {})
  }

  const markAllRead = () => {
    setNotifications((prev) => {
      const updated = prev.map((n) => ({ ...n, read: true }))
      localStorage.setItem('foodverse_notifications', JSON.stringify(updated))
      return updated
    })
    fetch(`${apiBaseUrl}/api/v1/notifications/mark-read`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({})
    }).catch(() => {})
  }

  const clearAllNotifications = () => {
    setNotifications([])
    localStorage.setItem('foodverse_notifications', JSON.stringify([]))
    fetch(`${apiBaseUrl}/api/v1/notifications/clear`, {
      method: 'POST'
    }).catch(() => {})
  }

  const unreadCount = notifications.filter((n) => !n.read).length

  const getInitials = (n) => {
    if (!n || !n.trim()) return 'FV'
    const parts = n.trim().split(' ')
    if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
  }

  // Food Recognition Image Upload & API State
  const [selectedImage, setSelectedImage] = useState(null)
  const [isDragging, setIsDragging] = useState(false)
  const [imageError, setImageError] = useState(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysisResult, setAnalysisResult] = useState(null)
  const [analysisError, setAnalysisError] = useState(null)
  const fileInputRef = useRef(null)

  const filteredModules = modules.filter((m) =>
    m.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    m.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
    m.tag.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const selectedModule = modules.find((m) => m.id === activeTab)

  const handleSearchChange = (e) => {
    setSearchQuery(e.target.value)
    if (activeTab !== 'dashboard') {
      setActiveTab('dashboard')
    }
  }

  const handleImageFile = (file) => {
    if (!file) return
    let validationMessage = null
    if (!file.type.startsWith('image/')) {
      validationMessage = 'Please select a valid image file (PNG, JPG, JPEG, or WEBP).'
    } else if (file.size === 0) {
      validationMessage = 'The selected image is empty. Choose another image.'
    } else if (file.size > 25 * 1024 * 1024) {
      validationMessage = 'Image size exceeds the 25 MB upload limit.'
    }

    if (validationMessage) {
      if (selectedImage?.previewUrl) URL.revokeObjectURL(selectedImage.previewUrl)
      setSelectedImage(null)
      setImageError(validationMessage)
      setAnalysisResult(null)
      setAnalysisError(null)
      if (fileInputRef.current) fileInputRef.current.value = ''
      return
    }

    if (selectedImage?.previewUrl) URL.revokeObjectURL(selectedImage.previewUrl)
    setImageError(null)
    setAnalysisResult(null)
    setAnalysisError(null)
    const previewUrl = URL.createObjectURL(file)
    setSelectedImage({
      file,
      previewUrl,
      name: file.name,
      size: (file.size / (1024 * 1024)).toFixed(2) + ' MB',
    })
  }

  const handleFileInputChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleImageFile(e.target.files[0])
    }
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (e) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setIsDragging(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleImageFile(e.dataTransfer.files[0])
    }
  }

  const handleRemoveImage = () => {
    if (selectedImage?.previewUrl) {
      URL.revokeObjectURL(selectedImage.previewUrl)
    }
    setSelectedImage(null)
    setImageError(null)
    setAnalysisResult(null)
    setAnalysisError(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const handleAnalyze = async () => {
    if (!selectedImage?.file) return
    setIsAnalyzing(true)
    setAnalysisError(null)
    setAnalysisResult(null)

    try {
      const formData = new FormData()
      formData.append('file', selectedImage.file)

      const response = await fetch(`${apiBaseUrl}/api/v1/food/recognize`, {
        method: 'POST',
        body: formData,
      })

      let data
      try {
        data = await response.json()
      } catch {
        data = null
      }

      if (!response.ok) {
        const detail = Array.isArray(data?.detail)
          ? data.detail.map((issue) => issue.msg || JSON.stringify(issue)).join('; ')
          : data?.detail
        throw new Error(detail || `Food analysis failed (HTTP ${response.status}).`)
      }

      const validPredictions =
        Array.isArray(data?.top_5) &&
        data.top_5.length > 0 &&
        data.top_5.every(
          (prediction) =>
            typeof prediction?.label === 'string' &&
            Number.isFinite(prediction.confidence) &&
            prediction.confidence >= 0 &&
            prediction.confidence <= 1
        )
      if (
        data?.status !== 'success' ||
        typeof data.predicted_label !== 'string' ||
        !Number.isFinite(data.confidence) ||
        data.confidence < 0 ||
        data.confidence > 1 ||
        !validPredictions
      ) {
        throw new Error('The food recognition API returned an unexpected response. Please try again or check the backend version.')
      }

      setAnalysisResult(data)
      const resultMessage = data.is_uncertain
        ? `The model is uncertain. Its best candidate is "${data.candidate_label}" (uncalibrated score ${(data.confidence * 100).toFixed(1)}%).`
        : `Predicted "${data.predicted_label}" (uncalibrated score ${(data.confidence * 100).toFixed(1)}%).`
      addNotification({
        id: `food-${Date.now()}`,
        title: 'Food Recognition Complete',
        message: resultMessage,
        type: 'success',
        module: 'food-recognition'
      })
    } catch (err) {
      const errMsg = err instanceof TypeError
        ? `Cannot reach the Food Verse API at ${apiBaseUrl}. Confirm the backend is running and allows requests from ${window.location.origin}.`
        : err.message || 'Food analysis failed unexpectedly.'
      setAnalysisError(errMsg)
      addNotification({
        id: `food-err-${Date.now()}`,
        title: 'Food Recognition Failed',
        message: errMsg,
        type: 'error',
        module: 'food-recognition'
      })
    } finally {
      setIsAnalyzing(false)
    }
  }

  return (
    <div className="app-container">
      {/* Keyframe animation for spinner */}
      <style>{`
        @keyframes spinLoader {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>

      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div
          className="sidebar-overlay"
          onClick={() => setSidebarOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Sidebar Navigation */}
      <aside className={`sidebar ${sidebarOpen ? 'sidebar-open' : ''}`}>
        <div className="sidebar-header">
          <div className="brand-logo" onClick={() => setActiveTab('dashboard')} style={{ cursor: 'pointer' }}>
            <div className="brand-icon-wrapper">
              <UtensilsCrossed className="brand-icon" />
            </div>
            <div className="brand-text">
              <span className="brand-title">Food Verse</span>
              <span className="brand-subtitle">AI Intelligence</span>
            </div>
          </div>
          <button
            className="sidebar-close-btn"
            onClick={() => setSidebarOpen(false)}
            aria-label="Close sidebar"
          >
            <X size={20} />
          </button>
        </div>

        <nav className="sidebar-nav">
          <span className="nav-group-title">Main Menu</span>
          <ul className="nav-list">
            {navItems.map((item) => {
              const Icon = item.icon
              const isActive = activeTab === item.id
              return (
                <li key={item.id}>
                  <button
                    className={`nav-button ${isActive ? 'nav-button-active' : ''}`}
                    onClick={() => {
                      setActiveTab(item.id)
                      setSidebarOpen(false)
                    }}
                  >
                    <Icon size={18} className="nav-button-icon" />
                    <span>{item.label}</span>
                  </button>
                </li>
              )
            })}
          </ul>

          <span className="nav-group-title">Preferences</span>
          <ul className="nav-list">
            <li>
              <button
                className={`nav-button ${activeTab === 'profile' ? 'nav-button-active' : ''}`}
                onClick={() => {
                  setActiveTab('profile')
                  setSidebarOpen(false)
                }}
              >
                <User size={18} className="nav-button-icon" />
                <span>Profile</span>
              </button>
            </li>
            <li>
              <button
                className={`nav-button ${activeTab === 'settings' ? 'nav-button-active' : ''}`}
                onClick={() => {
                  setActiveTab('settings')
                  setSidebarOpen(false)
                }}
              >
                <Settings size={18} className="nav-button-icon" />
                <span>Settings</span>
              </button>
            </li>
            <li>
              <button
                className={`nav-button ${activeTab === 'documentation' ? 'nav-button-active' : ''}`}
                onClick={() => {
                  setActiveTab('documentation')
                  setSidebarOpen(false)
                }}
              >
                <HelpCircle size={18} className="nav-button-icon" />
                <span>Documentation</span>
              </button>
            </li>
          </ul>
        </nav>

        {/* Sidebar Status / Info Card */}
        <div className="sidebar-footer">
          <div className="ai-status-card">
            <div className="ai-status-indicator">
              <span
                className="status-dot"
                style={{
                  backgroundColor: backendConnected ? '#10b981' : '#f59e0b',
                  boxShadow: backendConnected ? '0 0 8px rgba(16, 185, 129, 0.6)' : 'none',
                }}
              ></span>
              <span className="status-label">
                {backendConnected ? 'AI Engine Connected' : 'Checking Engine...'}
              </span>
            </div>
            <p className="ai-status-desc">
              {backendConnected
                ? 'ViT & Nutrition APIs Online'
                : 'Connecting to local FastAPI server'}
            </p>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="main-wrapper">
        {/* Top Header */}
        <header className="top-header">
          <div className="header-left">
            <button
              className="menu-toggle-btn"
              onClick={() => setSidebarOpen(true)}
              aria-label="Open sidebar"
            >
              <Menu size={22} />
            </button>
            <div className="search-box">
              <Search size={18} className="search-icon" />
              <input
                type="text"
                placeholder="Search modules, nutrients, recipes..."
                value={searchQuery}
                onChange={handleSearchChange}
                className="search-input"
              />
            </div>
          </div>

          <div className="header-right">
            {/* Notification Bell & Dropdown */}
            <div className="notifications-wrapper" ref={notifDropdownRef}>
              <button
                className="icon-btn"
                aria-label="Notifications"
                onClick={() => setNotificationsOpen(!notificationsOpen)}
                title="Notifications"
              >
                <Bell size={20} />
                {unreadCount > 0 && (
                  <span className="notification-badge-count">{unreadCount > 9 ? '9+' : unreadCount}</span>
                )}
              </button>

              {notificationsOpen && (
                <div className="notifications-panel">
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '12px 16px',
                      background: 'rgba(244, 237, 227, 0.65)',
                      borderBottom: '1px solid rgba(22, 62, 48, 0.08)',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontWeight: 700, fontSize: '0.88rem', color: 'var(--color-primary-900)' }}>
                        Notifications
                      </span>
                      {unreadCount > 0 && (
                        <span
                          style={{
                            fontSize: '0.68rem',
                            padding: '2px 6px',
                            background: 'var(--color-primary-600)',
                            color: '#ffffff',
                            borderRadius: '10px',
                            fontWeight: 700,
                          }}
                        >
                          {unreadCount} new
                        </span>
                      )}
                    </div>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      {unreadCount > 0 && (
                        <button
                          onClick={markAllRead}
                          style={{ fontSize: '0.74rem', color: 'var(--color-primary-600)', fontWeight: 600 }}
                        >
                          Mark all read
                        </button>
                      )}
                      {notifications.length > 0 && (
                        <button
                          onClick={clearAllNotifications}
                          style={{ fontSize: '0.74rem', color: '#dc2626', fontWeight: 600 }}
                        >
                          Clear
                        </button>
                      )}
                    </div>
                  </div>

                  <div style={{ maxHeight: '340px', overflowY: 'auto' }}>
                    {notifications.length === 0 ? (
                      <div style={{ padding: '32px 20px', textAlign: 'center', color: 'var(--color-text-muted)' }}>
                        <Bell size={28} style={{ opacity: 0.3, margin: '0 auto 8px' }} />
                        <p style={{ fontSize: '0.82rem', fontWeight: 600 }}>No notifications yet</p>
                        <p style={{ fontSize: '0.74rem', marginTop: '2px' }}>
                          Activity from meal planning, cooking, and vision scans will appear here.
                        </p>
                      </div>
                    ) : (
                      notifications.map((notif) => (
                        <div
                          key={notif.id}
                          style={{
                            padding: '12px 16px',
                            borderBottom: '1px solid rgba(22, 62, 48, 0.06)',
                            background: notif.read ? '#ffffff' : 'rgba(240, 248, 245, 0.6)',
                            display: 'flex',
                            gap: '10px',
                            alignItems: 'flex-start',
                          }}
                        >
                          <div
                            style={{
                              width: '8px',
                              height: '8px',
                              borderRadius: '50%',
                              background: notif.read
                                ? 'transparent'
                                : notif.type === 'error'
                                ? '#ef4444'
                                : notif.type === 'success'
                                ? '#10b981'
                                : '#3b82f6',
                              marginTop: '5px',
                              flexShrink: 0,
                            }}
                          />
                          <div style={{ flex: 1 }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                              <strong style={{ fontSize: '0.82rem', color: 'var(--color-primary-900)' }}>
                                {notif.title}
                              </strong>
                              <span style={{ fontSize: '0.68rem', color: 'var(--color-text-muted)' }}>
                                {notif.timestamp ? new Date(notif.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}
                              </span>
                            </div>
                            <p style={{ fontSize: '0.78rem', color: 'var(--color-text-secondary)', marginTop: '2px', lineHeight: 1.4 }}>
                              {notif.message}
                            </p>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Clickable Real User Profile */}
            <div
              className="user-profile"
              onClick={() => {
                setActiveTab('profile')
                setSidebarOpen(false)
              }}
              title="Click to view and edit profile"
            >
              <div className="user-avatar">{getInitials(userProfile.name)}</div>
              <div className="user-info">
                <span className="user-name">{userProfile.name || 'Guest User'}</span>
                <span className="user-role">{userProfile.diet_type ? userProfile.diet_type.toUpperCase() : 'GUEST'}</span>
              </div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="main-content">
          {activeTab === 'dashboard' ? (
            <>
              {/* Welcome Banner */}
              <section className="welcome-section">
                <div className="welcome-content">
                  <div className="welcome-tag">
                    <Sparkles size={14} />
                    <span>Next-Gen Culinary Intelligence</span>
                  </div>
                  <h1 className="welcome-title">Welcome to Food Verse AI</h1>
                  <p className="welcome-description">
                    Elevate your culinary journey with cutting-edge visual recognition, real-time freshness tracking, hygiene compliance audits, and tailored nutrient planning.
                  </p>
                </div>

                {/* Quick Metrics */}
                <div className="metrics-grid">
                  <div className="metric-card">
                    <div className="metric-icon-box bg-orange">
                      <Flame size={20} />
                    </div>
                    <div className="metric-data">
                      <span className="metric-value">
                        {Math.round(
                          (userProfile.gender === 'male'
                            ? 10 * (userProfile.weight_kg || 65) + 6.25 * (userProfile.height_cm || 168) - 5 * (userProfile.age || 28) + 5
                            : 10 * (userProfile.weight_kg || 65) + 6.25 * (userProfile.height_cm || 168) - 5 * (userProfile.age || 28) - 161) * 1.55
                        ).toLocaleString()} kcal
                      </span>
                      <span className="metric-label">Target Energy</span>
                    </div>
                  </div>

                  <div className="metric-card">
                    <div className="metric-icon-box bg-emerald">
                      <Activity size={20} />
                    </div>
                    <div className="metric-data">
                      <span className="metric-value">Ready</span>
                      <span className="metric-label">Multi-Spectral Sensor</span>
                    </div>
                  </div>

                  <div className="metric-card">
                    <div className="metric-icon-box bg-purple">
                      <HeartPulse size={20} />
                    </div>
                    <div className="metric-data">
                      <span className="metric-value">5 / 5</span>
                      <span className="metric-label">Active Modules</span>
                    </div>
                  </div>
                </div>
              </section>

              {/* Module Cards Grid */}
              <section className="modules-section">
                <div className="modules-header">
                  <div>
                    <h2 className="section-title">Core AI Modules</h2>
                    <p className="section-subtitle">
                      Select a module to initiate real-time analysis, automation, or custom culinary generation.
                    </p>
                  </div>
                  <span className="modules-count">
                    Showing {filteredModules.length} of {modules.length} modules
                  </span>
                </div>

                <div className="cards-grid">
                  {filteredModules.length === 0 ? (
                    <div
                      className="module-card"
                      style={{
                        gridColumn: '1 / -1',
                        textAlign: 'center',
                        padding: '48px 24px',
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}
                    >
                      <div className="card-icon-container" style={{ marginBottom: '16px' }}>
                        <Search size={24} />
                      </div>
                      <h3 className="card-title">No matching modules found</h3>
                      <p
                        className="card-description"
                        style={{ maxWidth: '440px', margin: '0 auto 20px', textAlign: 'center' }}
                      >
                        No AI modules matched &ldquo;{searchQuery}&rdquo;. Try searching for &ldquo;nutrition&rdquo;, &ldquo;freshness&rdquo;, &ldquo;hygiene&rdquo;, or &ldquo;cooking&rdquo;.
                      </p>
                      <button
                        className="card-action-btn"
                        style={{ maxWidth: '180px' }}
                        onClick={() => setSearchQuery('')}
                      >
                        <span>Clear Search</span>
                      </button>
                    </div>
                  ) : (
                    filteredModules.map((module) => {
                      const IconComponent = module.icon
                      return (
                        <div key={module.id} className="module-card">
                          <div className="card-top">
                            <div className="card-icon-container">
                              <IconComponent size={24} className="card-icon" />
                            </div>
                            <span className={`card-badge ${module.badgeClass}`}>
                              {module.tag}
                            </span>
                          </div>

                          <h3 className="card-title">{module.title}</h3>
                          <p className="card-description">{module.description}</p>

                          <div className="card-features">
                            {module.features.map((feature, idx) => (
                              <span key={idx} className="feature-pill">
                                {feature}
                              </span>
                            ))}
                          </div>

                          <div className="card-footer">
                            <button
                              className="card-action-btn"
                              onClick={() => setActiveTab(module.id)}
                            >
                              <span>{module.actionText}</span>
                              <ArrowRight size={16} />
                            </button>
                          </div>
                        </div>
                      )
                    })
                  )}
                </div>
              </section>
            </>
          ) : activeTab === 'food-recognition' ? (
            /* Dedicated Food Recognition Module View with Upload, Preview, and API Call */
            <div className="module-view">
              <section className="welcome-section">
                <div className="welcome-content">
                  <button
                    onClick={() => setActiveTab('dashboard')}
                    className="card-action-btn"
                    style={{
                      display: 'inline-flex',
                      width: 'auto',
                      marginBottom: '16px',
                      padding: '6px 14px',
                      background: 'rgba(255, 255, 255, 0.12)',
                      color: '#ffffff',
                      borderColor: 'rgba(255, 255, 255, 0.2)',
                    }}
                  >
                    <ArrowLeft size={16} />
                    <span>Back to Dashboard</span>
                  </button>

                  <div className="welcome-tag">
                    <Sparkles size={14} />
                    <span>Vision AI Scanner</span>
                  </div>

                  <h1 className="welcome-title">Food Recognition & Nutrition</h1>
                  <p className="welcome-description">
                    Upload a high-resolution food photo to detect dish components, portion estimates, and nutrient profiles.
                  </p>
                </div>

                <div className="metrics-grid">
                  <div className="metric-card">
                    <div className="metric-icon-box bg-emerald">
                      <ScanLine size={20} />
                    </div>
                    <div className="metric-data">
                      <span className="metric-value">
                        {isAnalyzing
                          ? 'Analyzing...'
                          : analysisResult
                          ? 'Analysis Received'
                          : selectedImage
                          ? 'Image Ready'
                          : 'Awaiting Image'}
                      </span>
                      <span className="metric-label">Upload State</span>
                    </div>
                  </div>

                  <div className="metric-card">
                    <div className="metric-icon-box bg-orange">
                      <Server size={20} />
                    </div>
                    <div className="metric-data">
                      <span className="metric-value">Endpoint</span>
                      <span className="metric-label" style={{ textTransform: 'none' }}>
                        POST /api/v1/food/recognize
                      </span>
                    </div>
                  </div>
                </div>
              </section>

              <section className="modules-section">
                <div className="modules-header">
                  <div>
                    <h2 className="section-title">Dish Photo Upload</h2>
                    <p className="section-subtitle">
                      Drag and drop your food picture or select a file to preview and trigger recognition.
                    </p>
                  </div>
                  <span className="card-badge badge-blue">Vision AI</span>
                </div>

                <div className="module-card" style={{ padding: '32px 28px' }}>
                  {/* Hidden File Input */}
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    onChange={handleFileInputChange}
                    style={{ display: 'none' }}
                  />

                  {/* Dropzone or Image Preview */}
                  {!selectedImage ? (
                    <div
                      onDragOver={handleDragOver}
                      onDragLeave={handleDragLeave}
                      onDrop={handleDrop}
                      onClick={() => fileInputRef.current?.click()}
                      style={{
                        border: isDragging
                          ? '2px dashed #10b981'
                          : '2px dashed rgba(22, 62, 48, 0.2)',
                        background: isDragging ? 'var(--color-primary-50)' : 'var(--color-cream-50)',
                        borderRadius: 'var(--radius-lg)',
                        padding: '48px 24px',
                        textAlign: 'center',
                        cursor: 'pointer',
                        transition: 'all 0.2s ease',
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        justifyContent: 'center',
                        marginBottom: '24px',
                      }}
                    >
                      <div
                        className="card-icon-container"
                        style={{
                          width: '56px',
                          height: '56px',
                          marginBottom: '16px',
                          background: isDragging ? '#10b981' : 'var(--color-surface)',
                          color: isDragging ? '#ffffff' : 'var(--color-primary-700)',
                        }}
                      >
                        <Upload size={26} />
                      </div>
                      <h3
                        className="card-title"
                        style={{ fontSize: '1.15rem', marginBottom: '8px' }}
                      >
                        {isDragging ? 'Drop food image here' : 'Click to select or drag & drop a photo'}
                      </h3>
                      <p
                        className="card-description"
                        style={{ maxWidth: '380px', margin: '0 auto 16px', fontSize: '0.84rem' }}
                      >
                        Supports JPG, PNG, WEBP, or JPEG food photos. Crisp overhead shots yield highest accuracy.
                      </p>
                      <button
                        type="button"
                        className="card-action-btn"
                        style={{ width: 'auto', padding: '8px 20px' }}
                        onClick={(e) => {
                          e.stopPropagation()
                          fileInputRef.current?.click()
                        }}
                      >
                        <ImageIcon size={16} />
                        <span>Browse Image</span>
                      </button>
                    </div>
                  ) : (
                    /* Selected Image Preview & Action Controls */
                    <div
                      style={{
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        gap: '20px',
                        padding: '24px',
                        background: 'var(--color-cream-50)',
                        borderRadius: 'var(--radius-lg)',
                        border: '1px solid rgba(22, 62, 48, 0.1)',
                        marginBottom: '24px',
                      }}
                    >
                      <div
                        style={{
                          position: 'relative',
                          maxWidth: '100%',
                          maxHeight: '340px',
                          overflow: 'hidden',
                          borderRadius: 'var(--radius-md)',
                          boxShadow: 'var(--shadow-md)',
                        }}
                      >
                        <img
                          src={selectedImage.previewUrl}
                          alt="Food Preview"
                          style={{
                            maxWidth: '100%',
                            maxHeight: '340px',
                            objectFit: 'cover',
                            display: 'block',
                          }}
                        />
                      </div>

                      {/* File Details bar */}
                      <div
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          width: '100%',
                          maxWidth: '620px',
                          flexWrap: 'wrap',
                          gap: '12px',
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                          <CheckCircle2 size={18} color="#059669" />
                          <span style={{ fontSize: '0.86rem', fontWeight: 600, color: 'var(--color-text-main)' }}>
                            {selectedImage.name}
                          </span>
                          <span className="feature-pill" style={{ padding: '2px 8px', fontSize: '0.72rem' }}>
                            {selectedImage.size}
                          </span>
                        </div>

                        {/* Action buttons: Analyze and Remove */}
                        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                          <button
                            type="button"
                            className="card-action-btn"
                            style={{
                              width: 'auto',
                              padding: '8px 20px',
                              background: isAnalyzing ? 'var(--color-primary-600)' : 'var(--color-primary-700)',
                              color: '#ffffff',
                              borderColor: 'var(--color-primary-700)',
                              cursor: isAnalyzing ? 'not-allowed' : 'pointer',
                            }}
                            onClick={handleAnalyze}
                            disabled={isAnalyzing}
                          >
                            {isAnalyzing ? (
                              <>
                                <Loader2 size={16} style={{ animation: 'spinLoader 1s linear infinite' }} />
                                <span>Analyzing Food...</span>
                              </>
                            ) : (
                              <>
                                <Sparkles size={16} />
                                <span>Analyze Food</span>
                              </>
                            )}
                          </button>

                          <button
                            type="button"
                            className="card-action-btn"
                            style={{
                              width: 'auto',
                              padding: '8px 16px',
                              background: '#fee2e2',
                              color: '#b91c1c',
                              borderColor: '#fca5a5',
                            }}
                            onClick={handleRemoveImage}
                            disabled={isAnalyzing}
                          >
                            <Trash2 size={15} />
                            <span>Remove</span>
                          </button>
                        </div>
                      </div>

                      {/* Recognition Result Display */}
                      {analysisResult && analysisResult.status === 'success' && (
                        <div
                          style={{
                            width: '100%',
                            maxWidth: '620px',
                            padding: '24px 24px 20px',
                            background: 'var(--color-surface)',
                            border: analysisResult.is_uncertain
                              ? '1px solid rgba(217, 119, 6, 0.35)'
                              : '1px solid rgba(16, 185, 129, 0.35)',
                            borderRadius: 'var(--radius-md)',
                            boxShadow: 'var(--shadow-md)',
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '16px',
                          }}
                        >
                          {/* Header row */}
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                              {analysisResult.is_uncertain
                                ? <AlertCircle size={20} color="#b45309" />
                                : <CheckCircle2 size={20} color="#059669" />}
                              <span style={{ fontWeight: 700, fontSize: '0.92rem', color: 'var(--color-primary-800)' }}>
                                {analysisResult.is_uncertain
                                  ? 'Uncertain Prediction'
                                  : analysisResult.is_multi_item
                                  ? 'Multi-Region Candidates'
                                  : 'Recognition Result'}
                              </span>
                            </div>
                            <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                              {analysisResult.is_multi_item && (
                                <span className="card-badge badge-blue">
                                  {analysisResult.detected_items.length} Region Candidates
                                </span>
                              )}
                              <span className={`card-badge ${analysisResult.is_uncertain ? 'badge-amber' : 'badge-emerald'}`}>
                                {analysisResult.confidence_tier} uncalibrated score
                              </span>
                            </div>
                          </div>

                          {/* Complex Food Arrangement Multi-Item Breakdown */}
                          {analysisResult.is_multi_item && analysisResult.detected_items?.length > 0 && (
                            <div
                              style={{
                                background: '#f8fafc',
                                border: '1px solid #cbd5e1',
                                borderRadius: 'var(--radius-sm)',
                                padding: '16px',
                                display: 'flex',
                                flexDirection: 'column',
                                gap: '12px',
                              }}
                            >
                              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '6px' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                  <UtensilsCrossed size={16} color="var(--color-primary-700)" />
                                  <span style={{ fontWeight: 700, fontSize: '0.88rem', color: 'var(--color-primary-900)' }}>
                                    Additional Model Candidates ({analysisResult.detected_items.length})
                                  </span>
                                </div>
                                <span style={{ fontSize: '0.72rem', color: 'var(--color-text-secondary)', fontStyle: 'italic' }}>
                                  Crop-level classifications, not object detections
                                </span>
                              </div>

                              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                {analysisResult.detected_items.map((item) => (
                                  <div
                                    key={item.item_id}
                                    style={{
                                      background: '#ffffff',
                                      border: '1px solid rgba(22, 62, 48, 0.1)',
                                      borderRadius: '8px',
                                      padding: '10px 12px',
                                      display: 'flex',
                                      flexDirection: 'column',
                                      gap: '6px',
                                    }}
                                  >
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '6px' }}>
                                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                        <span style={{ fontWeight: 700, fontSize: '0.92rem', color: 'var(--color-primary-800)' }}>
                                          {item.label}
                                        </span>
                                        <span className="feature-pill" style={{ fontSize: '0.68rem', padding: '1px 6px' }}>
                                          {item.region}
                                        </span>
                                      </div>
                                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                        {item.nutrition?.health_score !== undefined && (
                                          <span
                                            className={`card-badge ${
                                              item.nutrition.health_label === 'Healthy'
                                                ? 'badge-emerald'
                                                : item.nutrition.health_label === 'Moderate'
                                                ? 'badge-amber'
                                                : 'badge-orange'
                                            }`}
                                            style={{ fontSize: '0.64rem', padding: '2px 8px' }}
                                          >
                                            {item.nutrition.health_label} ({item.nutrition.health_score})
                                          </span>
                                        )}
                                        <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#059669' }}>
                                          {(item.confidence * 100).toFixed(1)}% uncalibrated score
                                        </span>
                                      </div>
                                    </div>

                                    {item.nutrition && (
                                      <div
                                        style={{
                                          display: 'flex',
                                          alignItems: 'center',
                                          justifyContent: 'space-between',
                                          flexWrap: 'wrap',
                                          gap: '6px',
                                          fontSize: '0.74rem',
                                          color: 'var(--color-text-secondary)',
                                          background: 'rgba(240, 248, 245, 0.65)',
                                          padding: '5px 8px',
                                          borderRadius: '6px',
                                        }}
                                      >
                                        <span>Serving: {item.nutrition.serving_size}</span>
                                        <span style={{ fontWeight: 700, color: 'var(--color-primary-900)' }}>
                                          {item.nutrition.calories} kcal | P: {item.nutrition.protein_g}g | C: {item.nutrition.carbs_g}g | F: {item.nutrition.fat_g}g
                                        </span>
                                      </div>
                                    )}
                                  </div>
                                ))}
                              </div>

                              <div style={{ fontSize: '0.70rem', color: 'var(--color-text-muted)', lineHeight: 1.4 }}>
                                * Overlapping image regions are classified independently. These uncalibrated class scores do not verify separate objects or count dishes.
                              </div>
                            </div>
                          )}

                          {/* Primary prediction */}
                          <div style={{ textAlign: 'center', padding: '12px 0 4px' }}>
                            <span style={{
                              display: 'block',
                              fontSize: '1.75rem',
                              fontWeight: 800,
                              color: 'var(--color-primary-800)',
                              lineHeight: 1.2,
                              marginBottom: '8px',
                            }}>
                              {analysisResult.predicted_label}
                            </span>
                            {analysisResult.is_uncertain && analysisResult.candidate_label && (
                              <div style={{ marginTop: '6px', fontSize: '0.82rem', color: 'var(--color-text-secondary)' }}>
                                Best model candidate: <strong>{analysisResult.candidate_label}</strong>
                              </div>
                            )}
                            <span style={{
                              display: 'inline-block',
                              fontSize: '1rem',
                              fontWeight: 600,
                              color: analysisResult.is_uncertain ? '#b45309' : '#059669',
                            }}>
                              {(analysisResult.confidence * 100).toFixed(1)}% model score
                            </span>
                            <p style={{
                              maxWidth: '520px',
                              margin: '5px auto 0',
                              fontSize: '0.72rem',
                              color: 'var(--color-text-muted)',
                              lineHeight: 1.4,
                            }}>
                              Uncalibrated Food-101 class score, not a probability of correctness. The model selects among its 101 trained dish classes.
                            </p>
                            {analysisResult.confidence_note && (
                              <p style={{
                                maxWidth: '520px',
                                margin: '8px auto 0',
                                fontSize: '0.78rem',
                                color: analysisResult.is_uncertain ? '#92400e' : 'var(--color-text-secondary)',
                                lineHeight: 1.45,
                              }}>
                                {analysisResult.confidence_note}
                              </p>
                            )}
                            {/* Confidence bar */}
                            <div style={{
                              marginTop: '10px',
                              width: '100%',
                              maxWidth: '360px',
                              height: '8px',
                              background: 'rgba(16, 185, 129, 0.12)',
                              borderRadius: '4px',
                              overflow: 'hidden',
                              marginLeft: 'auto',
                              marginRight: 'auto',
                            }}>
                              <div style={{
                                width: `${(analysisResult.confidence * 100).toFixed(1)}%`,
                                height: '100%',
                                background: 'linear-gradient(90deg, #10b981, #059669)',
                                borderRadius: '4px',
                                transition: 'width 0.6s ease',
                              }} />
                            </div>
                          </div>

                          {/* Top-5 predictions */}
                          {analysisResult.top_5?.length > 0 && (
                            <div>
                              <span style={{
                                display: 'block',
                                fontSize: '0.75rem',
                                fontWeight: 700,
                                color: 'var(--color-text-secondary)',
                                textTransform: 'uppercase',
                                letterSpacing: '0.04em',
                                marginBottom: '10px',
                              }}>
                                {analysisResult.top_5.length > 1 ? 'Top Food-Class Scores' : 'Food-Class Score'}
                              </span>
                              <p style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)', marginBottom: '8px' }}>
                                Uncalibrated model scores; candidates are not verified ingredients or separate food-object detections.
                              </p>
                              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                                {analysisResult.top_5.map((pred, idx) => (
                                  <div key={idx} style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '10px',
                                    fontSize: '0.84rem',
                                  }}>
                                    <span style={{
                                      fontWeight: idx === 0 ? 700 : 500,
                                      color: idx === 0 ? 'var(--color-primary-800)' : 'var(--color-text-main)',
                                      minWidth: '140px',
                                    }}>
                                      {pred.label}
                                    </span>
                                    <div style={{
                                      flex: 1,
                                      height: '6px',
                                      background: 'rgba(16, 185, 129, 0.1)',
                                      borderRadius: '3px',
                                      overflow: 'hidden',
                                    }}>
                                      <div style={{
                                        width: `${Math.max((pred.confidence * 100), 0.5)}%`,
                                        height: '100%',
                                        background: idx === 0
                                          ? 'linear-gradient(90deg, #10b981, #059669)'
                                          : 'rgba(16, 185, 129, 0.45)',
                                        borderRadius: '3px',
                                        transition: 'width 0.4s ease',
                                      }} />
                                    </div>
                                    <span style={{
                                      fontSize: '0.78rem',
                                      fontWeight: 600,
                                      color: idx === 0 ? '#059669' : 'var(--color-text-secondary)',
                                      minWidth: '48px',
                                      textAlign: 'right',
                                    }}>
                                      {(pred.confidence * 100).toFixed(1)}%
                                    </span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Nutrition Estimation Panel */}
                          {analysisResult.nutrition && (
                            <div
                              style={{
                                marginTop: '4px',
                                padding: '16px',
                                background: 'rgba(240, 248, 245, 0.75)',
                                border: '1px solid rgba(16, 185, 129, 0.25)',
                                borderRadius: 'var(--radius-sm)',
                                display: 'flex',
                                flexDirection: 'column',
                                gap: '12px',
                              }}
                            >
                              {analysisResult.nutrition.reliability_warning && (
                                <div style={{
                                  padding: '9px 11px',
                                  background: '#fffbeb',
                                  border: '1px solid #fcd34d',
                                  borderRadius: '6px',
                                  color: '#92400e',
                                  fontSize: '0.78rem',
                                  lineHeight: 1.45,
                                }}>
                                  {analysisResult.nutrition.reliability_warning}
                                </div>
                              )}
                              {/* Nutrition Header */}
                              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                  <Flame size={18} color="#ea580c" />
                                  <span style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--color-primary-800)' }}>
                                    Estimated Nutrition Facts
                                  </span>
                                </div>
                                <span
                                  style={{
                                    fontSize: '0.68rem',
                                    fontWeight: 700,
                                    textTransform: 'uppercase',
                                    letterSpacing: '0.04em',
                                    padding: '2px 8px',
                                    borderRadius: '999px',
                                    background: 'rgba(217, 119, 6, 0.12)',
                                    color: '#b45309',
                                    border: '1px solid rgba(217, 119, 6, 0.25)',
                                  }}
                                >
                                  Standard Estimate
                                </span>
                              </div>

                              {/* Serving Size callout */}
                              <div style={{
                                fontSize: '0.82rem',
                                color: 'var(--color-text-secondary)',
                                background: '#ffffff',
                                padding: '8px 12px',
                                borderRadius: '6px',
                                border: '1px solid rgba(22, 62, 48, 0.08)',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'space-between',
                                flexWrap: 'wrap',
                                gap: '6px',
                              }}>
                                <span style={{ fontWeight: 600 }}>Assumed Serving Size:</span>
                                <span style={{ fontWeight: 700, color: 'var(--color-primary-800)' }}>
                                  {analysisResult.nutrition.serving_size}
                                </span>
                              </div>

                              {/* Macro Cards Grid */}
                              <div style={{
                                display: 'grid',
                                gridTemplateColumns: 'repeat(auto-fit, minmax(110px, 1fr))',
                                gap: '8px',
                              }}>
                                {/* Calories */}
                                <div style={{
                                  background: '#ffffff',
                                  padding: '10px 8px',
                                  borderRadius: '6px',
                                  border: '1px solid rgba(234, 88, 12, 0.25)',
                                  textAlign: 'center',
                                }}>
                                  <span style={{ display: 'block', fontSize: '0.68rem', fontWeight: 700, color: '#c2410c', textTransform: 'uppercase', letterSpacing: '0.03em' }}>
                                    Calories
                                  </span>
                                  <span style={{ display: 'block', fontSize: '1.3rem', fontWeight: 800, color: 'var(--color-primary-900)', marginTop: '2px', lineHeight: 1.1 }}>
                                    {analysisResult.nutrition.calories}
                                  </span>
                                  <span style={{ fontSize: '0.68rem', color: 'var(--color-text-muted)' }}>kcal</span>
                                </div>

                                {/* Protein */}
                                <div style={{
                                  background: '#ffffff',
                                  padding: '10px 8px',
                                  borderRadius: '6px',
                                  border: '1px solid rgba(37, 99, 235, 0.25)',
                                  textAlign: 'center',
                                }}>
                                  <span style={{ display: 'block', fontSize: '0.68rem', fontWeight: 700, color: '#1d4ed8', textTransform: 'uppercase', letterSpacing: '0.03em' }}>
                                    Protein
                                  </span>
                                  <span style={{ display: 'block', fontSize: '1.3rem', fontWeight: 800, color: 'var(--color-primary-900)', marginTop: '2px', lineHeight: 1.1 }}>
                                    {analysisResult.nutrition.protein_g}
                                  </span>
                                  <span style={{ fontSize: '0.68rem', color: 'var(--color-text-muted)' }}>grams</span>
                                </div>

                                {/* Carbs */}
                                <div style={{
                                  background: '#ffffff',
                                  padding: '10px 8px',
                                  borderRadius: '6px',
                                  border: '1px solid rgba(217, 119, 6, 0.25)',
                                  textAlign: 'center',
                                }}>
                                  <span style={{ display: 'block', fontSize: '0.68rem', fontWeight: 700, color: '#b45309', textTransform: 'uppercase', letterSpacing: '0.03em' }}>
                                    Carbs
                                  </span>
                                  <span style={{ display: 'block', fontSize: '1.3rem', fontWeight: 800, color: 'var(--color-primary-900)', marginTop: '2px', lineHeight: 1.1 }}>
                                    {analysisResult.nutrition.carbs_g}
                                  </span>
                                  <span style={{ fontSize: '0.68rem', color: 'var(--color-text-muted)' }}>grams</span>
                                </div>

                                {/* Fat */}
                                <div style={{
                                  background: '#ffffff',
                                  padding: '10px 8px',
                                  borderRadius: '6px',
                                  border: '1px solid rgba(220, 38, 38, 0.25)',
                                  textAlign: 'center',
                                }}>
                                  <span style={{ display: 'block', fontSize: '0.68rem', fontWeight: 700, color: '#b91c1c', textTransform: 'uppercase', letterSpacing: '0.03em' }}>
                                    Total Fat
                                  </span>
                                  <span style={{ display: 'block', fontSize: '1.3rem', fontWeight: 800, color: 'var(--color-primary-900)', marginTop: '2px', lineHeight: 1.1 }}>
                                    {analysisResult.nutrition.fat_g}
                                  </span>
                                  <span style={{ fontSize: '0.68rem', color: 'var(--color-text-muted)' }}>grams</span>
                                </div>
                              </div>

                              {/* Dietary fiber note */}
                              {analysisResult.nutrition.fiber_g !== undefined && (
                                <div style={{
                                  display: 'flex',
                                  justifyContent: 'space-between',
                                  fontSize: '0.76rem',
                                  color: 'var(--color-text-secondary)',
                                  padding: '0 4px',
                                }}>
                                  <span>Dietary Fiber (estimated):</span>
                                  <span style={{ fontWeight: 600, color: 'var(--color-primary-800)' }}>
                                    {analysisResult.nutrition.fiber_g}g
                                  </span>
                                </div>
                              )}

                              {/* Health Score & Explainable Logic (Activity 2.2) */}
                              {analysisResult.nutrition.health_score !== undefined && (
                                <div
                                  style={{
                                    background: '#ffffff',
                                    border: '1px solid rgba(22, 62, 48, 0.1)',
                                    borderRadius: 'var(--radius-sm)',
                                    padding: '14px',
                                    display: 'flex',
                                    flexDirection: 'column',
                                    gap: '10px',
                                  }}
                                >
                                  {/* Score header */}
                                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                      <Activity size={17} color="var(--color-primary-700)" />
                                      <span style={{ fontWeight: 700, fontSize: '0.88rem', color: 'var(--color-primary-900)' }}>
                                        Nutritional Health Score
                                      </span>
                                    </div>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                      <span
                                        className={`card-badge ${
                                          analysisResult.nutrition.health_label === 'Healthy'
                                            ? 'badge-emerald'
                                            : analysisResult.nutrition.health_label === 'Moderate'
                                            ? 'badge-amber'
                                            : 'badge-orange'
                                        }`}
                                      >
                                        {analysisResult.nutrition.health_label}
                                      </span>
                                      <span style={{ fontWeight: 800, fontSize: '1.15rem', color: 'var(--color-primary-900)' }}>
                                        {analysisResult.nutrition.health_score}<span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-muted)' }}>/100</span>
                                      </span>
                                    </div>
                                  </div>

                                  {/* Score bar */}
                                  <div style={{
                                    width: '100%',
                                    height: '7px',
                                    background: '#f1f5f9',
                                    borderRadius: '4px',
                                    overflow: 'hidden',
                                  }}>
                                    <div style={{
                                      width: `${Math.max(analysisResult.nutrition.health_score, 5)}%`,
                                      height: '100%',
                                      background:
                                        analysisResult.nutrition.health_label === 'Healthy'
                                          ? 'linear-gradient(90deg, #10b981, #059669)'
                                          : analysisResult.nutrition.health_label === 'Moderate'
                                          ? 'linear-gradient(90deg, #f59e0b, #d97706)'
                                          : 'linear-gradient(90deg, #f87171, #dc2626)',
                                      borderRadius: '4px',
                                      transition: 'width 0.5s ease',
                                    }} />
                                  </div>

                                  {/* Reasoning */}
                                  {analysisResult.nutrition.health_reasoning && (
                                    <div style={{ fontSize: '0.78rem', color: 'var(--color-text-secondary)', lineHeight: 1.45 }}>
                                      <strong>Scoring Analysis:</strong> {analysisResult.nutrition.health_reasoning}
                                    </div>
                                  )}

                                  {/* Suggestions */}
                                  {analysisResult.nutrition.health_suggestions && analysisResult.nutrition.health_suggestions.length > 0 && (
                                    <div style={{
                                      marginTop: '2px',
                                      background: 'rgba(244, 237, 227, 0.45)',
                                      border: '1px solid rgba(22, 62, 48, 0.08)',
                                      borderRadius: '6px',
                                      padding: '10px 12px',
                                    }}>
                                      <div style={{
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '6px',
                                        fontSize: '0.74rem',
                                        fontWeight: 700,
                                        color: 'var(--color-primary-800)',
                                        textTransform: 'uppercase',
                                        letterSpacing: '0.03em',
                                        marginBottom: '6px',
                                      }}>
                                        <Sparkles size={14} color="#d97706" />
                                        <span>Dietary Insights & Suggestions</span>
                                      </div>
                                      <ul style={{ margin: 0, paddingLeft: '16px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                                        {analysisResult.nutrition.health_suggestions.map((suggestion, idx) => (
                                          <li key={idx} style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', lineHeight: 1.4 }}>
                                            {suggestion}
                                          </li>
                                        ))}
                                      </ul>
                                    </div>
                                  )}
                                </div>
                              )}

                              {/* Disclaimer / Transparency note */}
                              <div style={{
                                fontSize: '0.71rem',
                                color: 'var(--color-text-muted)',
                                lineHeight: 1.45,
                                background: 'rgba(255, 255, 255, 0.75)',
                                padding: '8px 10px',
                                borderRadius: '6px',
                                borderLeft: '3px solid var(--color-accent-amber)',
                              }}>
                                <strong>Estimate Notice:</strong> {analysisResult.nutrition.disclaimer}
                              </div>

                              {/* Source attribution */}
                              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.72rem', color: 'var(--color-text-secondary)' }}>
                                <span>Data Source:</span>
                                <span style={{ fontWeight: 600, color: 'var(--color-primary-700)' }}>
                                  {analysisResult.nutrition.source}
                                </span>
                              </div>
                            </div>
                          )}

                          {/* Footer meta */}
                          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginTop: '4px' }}>
                            <span className="feature-pill" style={{ fontSize: '0.72rem' }}>
                              File: {analysisResult.filename}
                            </span>
                            {analysisResult.model_id && (
                              <span className="feature-pill" style={{ fontSize: '0.72rem' }}>
                                Model: {analysisResult.model_id}
                              </span>
                            )}
                            {analysisResult.preprocessing?.original_resolution && (
                              <span className="feature-pill" style={{ fontSize: '0.72rem' }}>
                                Res: {analysisResult.preprocessing.original_resolution}
                              </span>
                            )}
                            {analysisResult.preprocessing?.contrast_enhanced && (
                              <span className="feature-pill" style={{ fontSize: '0.72rem', color: '#b45309' }}>
                                Lighting: Contrast Enhanced
                              </span>
                            )}
                          </div>
                        </div>
                      )}

                      {/* Error Display */}
                      {analysisError && (
                        <div
                          style={{
                            width: '100%',
                            maxWidth: '620px',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px',
                            padding: '12px 16px',
                            background: '#fef2f2',
                            border: '1px solid #fecaca',
                            borderRadius: 'var(--radius-md)',
                            color: '#991b1b',
                            fontSize: '0.84rem',
                          }}
                        >
                          <AlertCircle size={18} />
                          <span>{analysisError}</span>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Validation Error Message */}
                  {imageError && (
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        padding: '10px 14px',
                        background: '#fef2f2',
                        border: '1px solid #fecaca',
                        borderRadius: 'var(--radius-sm)',
                        color: '#991b1b',
                        fontSize: '0.82rem',
                        marginBottom: '20px',
                      }}
                    >
                      <AlertCircle size={16} />
                      <span>{imageError}</span>
                    </div>
                  )}

                  {/* Capabilities Group */}
                  <div style={{ marginBottom: '24px' }}>
                    <span
                      style={{
                        display: 'block',
                        fontSize: '0.78rem',
                        fontWeight: 700,
                        color: 'var(--color-text-secondary)',
                        marginBottom: '10px',
                        textTransform: 'uppercase',
                        letterSpacing: '0.04em',
                      }}
                    >
                      Available Results
                    </span>
                    <div className="card-features">
                      <span className="feature-pill" style={{ padding: '6px 12px' }}>
                        ✓ Food-101 dish classification
                      </span>
                      <span className="feature-pill" style={{ padding: '6px 12px' }}>
                        ✓ Ranked class predictions with uncalibrated scores
                      </span>
                      <span className="feature-pill" style={{ padding: '6px 12px' }}>
                        ✓ Reference nutrition estimate (not portion detection)
                      </span>
                    </div>
                  </div>

                  <div className="card-footer" style={{ display: 'flex', gap: '14px', flexWrap: 'wrap' }}>
                    <button
                      className="card-action-btn"
                      style={{ maxWidth: '220px' }}
                      onClick={() => setActiveTab('dashboard')}
                    >
                      <ArrowLeft size={16} />
                      <span>Return to Dashboard</span>
                    </button>
                  </div>
                </div>
              </section>
            </div>
          ) : activeTab === 'freshness-detection' ? (
            <FreshnessWorkspace apiBaseUrl={apiBaseUrl} />
          ) : activeTab === 'restaurant-hygiene' ? (
            <HygieneWorkspace apiBaseUrl={apiBaseUrl} />
          ) : activeTab === 'smart-cooking' ? (
            <CookingAssistantWorkspace
              apiBaseUrl={apiBaseUrl}
              userSettings={userSettings}
              onNotification={addNotification}
            />
          ) : activeTab === 'meal-planner' ? (
            <MealPlannerWorkspace
              apiBaseUrl={apiBaseUrl}
              userProfile={userProfile}
              userSettings={userSettings}
              onNotification={addNotification}
            />
          ) : activeTab === 'history' ? (
            <HistoryWorkspace apiBaseUrl={apiBaseUrl} />
          ) : activeTab === 'profile' ? (
            <ProfileWorkspace
              apiBaseUrl={apiBaseUrl}
              currentProfile={userProfile}
              userSettings={userSettings}
              onProfileUpdated={(p) => setUserProfile(p)}
              onNotification={addNotification}
            />
          ) : activeTab === 'settings' ? (
            <SettingsWorkspace
              apiBaseUrl={apiBaseUrl}
              currentSettings={userSettings}
              onSettingsUpdated={(s) => setUserSettings(s)}
              onNotification={addNotification}
            />
          ) : activeTab === 'documentation' ? (
            <DocumentationWorkspace />
          ) : null}
        </main>
      </div>
    </div>
  )
}
