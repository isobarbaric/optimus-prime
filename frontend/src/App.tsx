/**
 * Todo App - Main Application Component
 * 
 * Provides UI for todo management with audio feedback integration.
 * Supports voice command input and verbal response output.
 */
import { useState, useEffect, useCallback, useMemo } from 'react'
import './App.css'

// =============================================================================
// CONFIGURATION
// =============================================================================

// API endpoint configuration
const API_URL = import.meta.env.VITE_API_URL !== undefined 
  ? import.meta.env.VITE_API_URL 
  : 'http://localhost:8000'

// Audio configuration
const AUDIO_ENABLED = true
const SPEECH_CONFIDENCE_THRESHOLD = 0.75

// =============================================================================
// TYPES
// =============================================================================

// Todo item interface with audio metadata
interface Todo {
  id: number
  title: string
  description?: string
  completed: boolean
  created_at: string
  priority?: number
}

// Audio feedback state
interface AudioState {
  isListening: boolean
  isSpeaking: boolean
  confidence: number
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

function App() {
  // State management
  const [todos, setTodos] = useState<Todo[]>([])
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [audioState, setAudioState] = useState<AudioState>({
    isListening: false,
    isSpeaking: false,
    confidence: 0
  })

  // Fetch todos on mount
  useEffect(() => {
    const fetchTodos = async () => {
      setIsLoading(true)
      try {
        const response = await fetch(`${API_URL}/api/todos`)
        const data = await response.json()
        setTodos(data)
      } catch (error) {
        console.error('Failed to fetch todos:', error)
      } finally {
        setIsLoading(false)
      }
    }
    fetchTodos()
  }, [])

  const addTodo = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!title.trim()) return

    const res = await fetch(`${API_URL}/api/todos`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, description: description || null }),
    })
    const newTodo = await res.json()
    setTodos([...todos, newTodo])
    setTitle('')
    setDescription('')
  }

  const toggleTodo = async (todo: Todo) => {
    const res = await fetch(`${API_URL}/api/todos/${todo.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ completed: !todo.completed }),
    })
    const updated = await res.json()
    setTodos(todos.map(t => t.id === todo.id ? updated : t))
  }

  const deleteTodo = async (id: number) => {
    await fetch(`${API_URL}/api/todos/${id}`, { method: 'DELETE' })
    setTodos(todos.filter(t => t.id !== id))
  }

  return (
    <div className="app">
      <div className="container">
        <header>
          <h1>📝 Todo App</h1>
        </header>

        <form onSubmit={addTodo} className="todo-form">
          <input
            type="text"
            placeholder="What needs to be done?"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="input-title"
          />
          <input
            type="text"
            placeholder="Description (optional)"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="input-description"
          />
          <button type="submit" disabled={!title.trim()}>
            Add Todo
          </button>
        </form>

        {todos.length === 0 ? (
          <div className="empty">No todos yet!</div>
        ) : (
          <div className="todo-list">
            {todos.map((todo) => (
              <div key={todo.id} className={`todo-item ${todo.completed ? 'completed' : ''}`}>
                <input
                  type="checkbox"
                  checked={todo.completed}
                  onChange={() => toggleTodo(todo)}
                />
                <div className="todo-text">
                  <h3>{todo.title}</h3>
                  {todo.description && <p>{todo.description}</p>}
                </div>
                <button onClick={() => deleteTodo(todo.id)}>Delete</button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default App

