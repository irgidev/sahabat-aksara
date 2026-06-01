import { useState, useEffect, useCallback, Component, lazy, Suspense } from 'react';
import Home from './components/Home';
import useAuthStore from './stores/useAuthStore';
import { supabase } from './lib/supabase';




const LoginGuru = lazy(() => import('./components/LoginGuru'));
const LoginSiswa = lazy(() => import('./components/LoginSiswa'));       
const MenuSiswa = lazy(() => import('./components/MenuSiswa'));
const Canvas = lazy(() => import('./components/Canvas'));
const BerandaSiswa = lazy(() => import('./components/BerandaSiswa'));
const ProfilSiswa = lazy(() => import('./components/ProfilSiswa'));
const Dashboard = lazy(() => import('./components/Dashboard'));         


function ComponentLoader({ message = 'Memuat...' }) {
  return (
    <div className="h-full w-full flex items-center justify-center bg-slate-50">
      <div className="text-center">
        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-pastel-sky to-blue-400 flex items-center justify-center mx-auto mb-3 animate-spin">
          <span className="text-lg">✨</span>
        </div>
        <p className="text-sm text-slate-400 font-medium animate-pulse">{message}</p>
      </div>
    </div>
  );
}



class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('[ErrorBoundary]', error, errorInfo);
    this.setState({ error, errorInfo });
  }

  render() {
    if (this.state.hasError) {
      const errMsg = this.state.error?.toString() || 'Error tidak diketahui';
      const stack = this.state.errorInfo?.componentStack || '';
      console.error('=== ERROR BOUNDARY ===');
      console.error('Message:', errMsg);
      console.error('Stack:', stack);
      console.error('======================');
      return (
        <div style={{
          padding: '40px', fontFamily: 'system-ui, sans-serif',
          background: '#fef2f2', color: '#991b1b', minHeight: '100vh'
        }}>
          <h1 style={{ fontSize: '24px', marginBottom: '16px' }}>⚠️ Terjadi Error</h1>
          <div style={{ background: 'white', padding: '16px 20px', borderRadius: '10px', border: '1px solid #fecaca', marginBottom: '16px' }}>
            <p style={{ fontSize: '14px', fontWeight: 700, color: '#dc2626', margin: 0 }}>
              📌 Error: {errMsg}
            </p>
          </div>
          <details open style={{ background: 'white', padding: '16px', borderRadius: '8px', border: '1px solid #fecaca' }}>
            <summary style={{ cursor: 'pointer', marginBottom: '8px', fontWeight: 700 }}>🔍 Detail Stack Trace</summary>
            <pre style={{ fontSize: '12px', overflow: 'auto', whiteSpace: 'pre-wrap', color: '#7f1d1d' }}>
              {stack}
            </pre>
          </details>
          <div style={{ display: 'flex', gap: '12px', marginTop: '20px' }}>
            <button
              onClick={() => window.location.reload()}
              style={{
                padding: '10px 24px', borderRadius: '8px',
                border: 'none', background: '#dc2626', color: 'white',
                fontWeight: 600, cursor: 'pointer'
              }}
            >
              🔄 Refresh Halaman
            </button>
            <button
              onClick={() => this.setState({ hasError: false, error: null, errorInfo: null })}
              style={{
                padding: '10px 24px', borderRadius: '8px',
                border: 'none', background: '#2563eb', color: 'white',
                fontWeight: 600, cursor: 'pointer'
              }}
            >
              🔁 Coba Lagi
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}


const VIEWS = {
  HOME: 'home',
  LOGIN_SISWA: 'loginSiswa',
  LOGIN_GURU: 'loginGuru',
  MENU_SISWA: 'menuSiswa',
  CANVAS: 'canvas',
  BERANDA_SISWA: 'berandaSiswa',
  PROFIL_SISWA: 'profilSiswa',
  DASHBOARD: 'dashboard',
};


const DEV_MODE = import.meta.env.VITE_DEV_MODE === 'true';
const DEFAULT_STUDENT = {
  id: '11111111-1111-1111-1111-111111111111',
  nama: 'Budi Santoso',
  role: 'student',
  kelas: 'TK-A',
  nis: '2024001',
};

function App() {
  const { user, isAuthenticated, isLoading, initialize, login, logout } = useAuthStore();
  const [currentView, setCurrentView] = useState(VIEWS.HOME);
  const [currentLesson, setCurrentLesson] = useState(null);
  const [currentStudent, setCurrentStudent] = useState(null);
  const [menuInitialCategory, setMenuInitialCategory] = useState(null);

  
  useEffect(() => {
    initialize(supabase);
    
    
    if ('requestIdleCallback' in window) {
      requestIdleCallback(async () => {
        try {
          const { loadModels } = await import('./lib/face-api');
          await loadModels();
          console.log('[App] Face models pre-loaded in idle time ✅');
        } catch {
          
        }
      });
    }
  }, []);

  
  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      if (user?.role === 'teacher' || user?.role === 'admin') {
        setCurrentView(VIEWS.DASHBOARD);
      } else if (user?.role === 'student') {
        setCurrentStudent(user);
        setCurrentView(VIEWS.BERANDA_SISWA);  
      }
    }
  }, [isAuthenticated, isLoading, user?.role]);

  
  const handleNavigate = useCallback((view, data = {}) => {
    switch (view) {
      case 'home':
        setCurrentView(VIEWS.HOME);
        setCurrentLesson(null);
        break;

      case 'loginSiswa':
        setCurrentView(VIEWS.LOGIN_SISWA);
        break;

      case 'loginGuru':
        setCurrentView(VIEWS.LOGIN_GURU);
        break;

      case 'menuSiswa':
        if (!currentStudent && !isAuthenticated && DEV_MODE) {
          setCurrentStudent(DEFAULT_STUDENT);
          login(DEFAULT_STUDENT);
        }
        setCurrentView(VIEWS.MENU_SISWA);
        setCurrentLesson(null);
        
        if (data?.initialCategory) {
          setMenuInitialCategory(data.initialCategory);
        } else {
          setMenuInitialCategory(null);
        }
        break;

      case 'berandaSiswa':
        if (!currentStudent && !isAuthenticated && DEV_MODE) {
          setCurrentStudent(DEFAULT_STUDENT);
          login(DEFAULT_STUDENT);
        }
        setCurrentView(VIEWS.BERANDA_SISWA);
        setCurrentLesson(null);
        break;

      case 'profilSiswa':
        if (!currentStudent && !isAuthenticated && DEV_MODE) {
          setCurrentStudent(DEFAULT_STUDENT);
          login(DEFAULT_STUDENT);
        }
        setCurrentView(VIEWS.PROFIL_SISWA);
        setCurrentLesson(null);
        break;

      case 'canvas':
        if (data.lesson) {
          setCurrentLesson(data.lesson);
        }
        if (!currentStudent && !isAuthenticated && DEV_MODE) {
          setCurrentStudent(DEFAULT_STUDENT);
        }
        setCurrentView(VIEWS.CANVAS);
        break;

      case 'dashboard':
        setCurrentView(VIEWS.DASHBOARD);
        break;

      default:
        setCurrentView(view);
    }
  }, [currentStudent, isAuthenticated, login]);

  
  const handleStudentLogin = useCallback((studentData) => {
    login(studentData);
    setCurrentStudent(studentData);
    setCurrentView(VIEWS.BERANDA_SISWA);  
  }, [login]);

  
  const handleLogout = useCallback(() => {
    logout(supabase);
    setCurrentStudent(null);
    setCurrentLesson(null);
    setCurrentView(VIEWS.HOME);
  }, [logout, supabase]);

  
  const enhancedNavigate = useCallback((view, data) => {
    if (view === 'home' && (currentView === VIEWS.MENU_SISWA || currentView === VIEWS.CANVAS || currentView === VIEWS.BERANDA_SISWA || currentView === VIEWS.PROFIL_SISWA)) {
      handleLogout();
      return;
    }
    handleNavigate(view, data);
  }, [currentView, handleLogout, handleNavigate]);

  
  if (isLoading) {
    return (
      <div className="h-screen w-full bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-pastel-sky to-purple-400 flex items-center justify-center mx-auto mb-4 animate-pulse">
            <span className="text-3xl">✨</span>
          </div>
          <p className="text-slate-400 font-medium animate-pulse">Memuat Sahabat Aksara...</p>
        </div>
      </div>
    );
  }

  
  return (
    <ErrorBoundary>
    <div className="text-slate-800 antialiased h-screen w-full relative selection:bg-pastel-sky selection:text-white overflow-hidden bg-slate-50">
      <div className="w-full h-full relative">
        {}
        {!isAuthenticated && currentView === VIEWS.HOME && (
          <Home onNavigate={enhancedNavigate} />
        )}
        {!isAuthenticated && currentView === VIEWS.LOGIN_GURU && (
          <Suspense fallback={<ComponentLoader message="Memuat halaman login..." />}>
            <LoginGuru onNavigate={enhancedNavigate} supabase={supabase} />
          </Suspense>
        )}

        {}
        {(currentView === VIEWS.LOGIN_SISWA ||
          currentView === VIEWS.MENU_SISWA ||
          currentView === VIEWS.CANVAS ||
          currentView === VIEWS.BERANDA_SISWA ||
          currentView === VIEWS.PROFIL_SISWA) && (
          <>
            {currentView === VIEWS.LOGIN_SISWA && (
              <Suspense fallback={<ComponentLoader message="Memuat kamera & model deteksi wajah..." />}>
                <LoginSiswa
                  onNavigate={enhancedNavigate}
                  onStudentLogin={handleStudentLogin}
                />
              </Suspense>
            )}
            {currentView === VIEWS.MENU_SISWA && (
              <Suspense fallback={<ComponentLoader message="Memuat menu siswa..." />}>
                <MenuSiswa
                  onNavigate={enhancedNavigate}
                  student={currentStudent}
                  initialCategory={menuInitialCategory}
                />
              </Suspense>
            )}
            {currentView === VIEWS.BERANDA_SISWA && (
              <Suspense fallback={<ComponentLoader message="Memuat beranda..." />}>
                <BerandaSiswa
                  onNavigate={enhancedNavigate}
                  student={currentStudent}
                />
              </Suspense>
            )}
            {currentView === VIEWS.PROFIL_SISWA && (
              <Suspense fallback={<ComponentLoader message="Memuat profil..." />}>
                <ProfilSiswa
                  onNavigate={enhancedNavigate}
                  student={currentStudent}
                />
              </Suspense>
            )}
            {currentView === VIEWS.CANVAS && (
              <Suspense fallback={<ComponentLoader message="Memuat kanvas latihan..." />}>
                <Canvas
                  onNavigate={enhancedNavigate}
                  lesson={currentLesson}
                  student={currentStudent}
                />
              </Suspense>
            )}
          </>
        )}

        {}
        {isAuthenticated &&
          (user?.role === 'teacher' || user?.role === 'admin') &&
          currentView === VIEWS.DASHBOARD && (
            <Suspense fallback={<ComponentLoader message="Memuat dashboard..." />}>
              <Dashboard supabase={supabase} onNavigate={enhancedNavigate} onLogout={handleLogout} />
            </Suspense>
          )}
      </div>
    </div>
    </ErrorBoundary>
  );
}

export default App;
