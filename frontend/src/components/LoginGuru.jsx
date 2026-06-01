import { useState } from 'react';
import { ArrowLeft, Eye, EyeClosed, Spinner, WarningCircle } from '@phosphor-icons/react';

export default function LoginGuru({ onNavigate, supabase }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    
    if (!email.trim() || !password.trim()) {
      setError('Email dan password harus diisi.');
      return;
    }

    setIsLoading(true);

    try {
      
      const res = await fetch('http://localhost:8000/api/login-guru', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim(), password }),
      });

      const result = await res.json();

      if (!res.ok) {
        throw new Error(result.detail || 'Login gagal');
      }

      
      const { default: useAuthStore } = await import('../stores/useAuthStore');
      useAuthStore.getState().login({
        id: result.user.id,
        email: result.user.email,
        nama: result.user.nama,
        role: result.user.role,
        kelas: result.user.kelas,
        avatar_url: result.user.avatar_url,
      });

    } catch (err) {
      console.error('Login error:', err);
      
      const msg = err.message || '';
      if (msg.includes('salah') || msg.includes('credentials') || msg.includes('401')) {
        setError('Email atau password salah. Coba lagi!');
      } else if (msg.includes('confirmed') || msg.includes('verified')) {
        setError('Email belum diverifikasi. Cek inbox email kamu.');
      } else if (msg.includes('503') || msg.includes('Supabase')) {
        setError('Backend belum siap. Gunakan: anita@sahabataksara.id / guru123');
      } else {
        setError('Terjadi kesalahan. Coba beberapa saat lagi.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="view-section view-active bg-gradient-to-br from-slate-50 via-white to-pastel-lavender/20 flex items-center justify-center">
      {}
      <div className="absolute top-[-10%] right-[-5%] w-96 h-96 bg-pastel-sky/20 rounded-full filter blur-[100px]" />
      <div className="absolute bottom-[-10%] left-[-5%] w-96 h-96 bg-slate-200/30 rounded-full filter blur-[100px]" />

      <div className="relative z-10 w-full max-w-[420px] px-6">
        {}
        <button
          onClick={() => onNavigate('home')}
          className="flex items-center gap-2 text-slate-400 hover:text-slate-600 font-medium mb-8 transition-colors group"
        >
          <ArrowLeft weight="bold" className="group-hover:-translate-x-1 transition-transform" />
          Kembali
        </button>

        {}
        <div className="mb-8">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-slate-700 to-slate-900 flex items-center justify-center shadow-lg mb-5">
            <span className="text-3xl">👩‍🏫</span>
          </div>
          <h1 className="text-3xl font-bold text-slate-800 tracking-tight">
            Portal Guru
          </h1>
          <p className="text-slate-500 mt-1.5 font-medium">
            Masuk ke dashboard untuk memantau perkembangan siswa
          </p>
        </div>

        {}
        <form onSubmit={handleSubmit} className="space-y-4">
          {}
          <div>
            <label className="block text-sm font-bold text-slate-600 mb-1.5 ml-1">
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="guru@sahabataksara.id"
              autoComplete="email"
              disabled={isLoading}
              className="w-full px-4 py-3 rounded-2xl bg-white border-2 border-slate-200 text-slate-800 placeholder:text-slate-300 font-medium outline-none transition-all focus:border-pastel-sky focus:ring-4 focus:ring-pastel-sky/10 disabled:opacity-50"
            />
          </div>

          {}
          <div>
            <label className="block text-sm font-bold text-slate-600 mb-1.5 ml-1">
              Password
            </label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                autoComplete="current-password"
                disabled={isLoading}
                className="w-full px-4 py-3 pr-12 rounded-2xl bg-white border-2 border-slate-200 text-slate-800 placeholder:text-slate-300 font-medium outline-none transition-all focus:border-pastel-sky focus:ring-4 focus:ring-pastel-sky/10 disabled:opacity-50"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors p-1"
                tabIndex={-1}
              >
                {showPassword ? (
                  <EyeClosed weight="bold" className="text-xl" />
                ) : (
                  <Eye weight="bold" className="text-xl" />
                )}
              </button>
            </div>
          </div>

          {}
          {error && (
            <div className="flex items-center gap-2.5 px-4 py-3 rounded-2xl bg-red-50 border border-red-100 text-red-600 text-sm font-medium animate-[shake_0.4s_ease-in-out]">
              <WarningCircle weight="fill" className="text-lg shrink-0" />
              {error}
            </div>
          )}

          {}
          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-3.5 rounded-2xl bg-gradient-to-r from-slate-800 to-slate-900 text-white font-bold text-base shadow-lg shadow-slate-900/20 hover:shadow-xl hover:shadow-slate-900/30 hover:-translate-y-0.5 active:scale-[0.98] transition-all flex items-center justify-center gap-2 disabled:opacity-60 disabled:cursor-not-allowed disabled:hover:translate-y-0 mt-2"
          >
            {isLoading ? (
              <>
                <Spinner weight="bold" className="text-xl animate-spin" />
                Memproses...
              </>
            ) : (
              'Masuk'
            )}
          </button>
        </form>

        {}
        <p className="text-center text-xs text-slate-400 mt-8 font-medium">
          Butuh bantuan? Hubungi admin sekolah
        </p>
      </div>
    </main>
  );
}

