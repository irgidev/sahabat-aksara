

import { useState, useEffect, useCallback, useRef } from 'react';
import {
  ArrowLeft,
  Camera,
  User,
  CheckCircle,
  XCircle,
  Spinner,
  WarningCircle,
  Smiley,
  Sparkle,
} from '@phosphor-icons/react';
import CameraView from './CameraView';
import { loadModels, findBestMatch, parseDescriptor, MATCH_THRESHOLD } from '../lib/face-api';
import API_BASE from '../lib/api';


const DEMO_STUDENT = {
  id: '11111111-1111-1111-1111-111111111111',
  nama: 'Budi Santoso',
  role: 'student',
  kelas: 'TK-A',
  nis: '2024001',
};



const LOAD_PHASES = [
  { label: 'Memuat model deteksi wajah...', icon: '🧠' },
  { label: 'Menyiapkan landmark wajah...', icon: '📍' },
  { label: 'Menginisialisasi pengenalan...', icon: '🔍' },
];

export default function LoginSiswa({ onNavigate, onStudentLogin }) {
  
  const [phase, setPhase] = useState('loading'); 
  const [loadProgress, setLoadProgress] = useState(0);
  const [loadLabel, setLoadLabel] = useState(LOAD_PHASES[0].label);
  const [students, setStudents] = useState([]);
  const [matchedStudent, setMatchedStudent] = useState(null);
  const [confidence, setConfidence] = useState(0);
  const [detectCount, setDetectCount] = useState(0);
  const [errorMsg, setErrorMsg] = useState('');
  const [showDemoBtn, setShowDemoBtn] = useState(false);

  const detectCountRef = useRef(0);
  const matchedRef = useRef(false); 
  const descriptorBufferRef = useRef([]); 
  const BUFFER_SIZE = 5; 

  

  useEffect(() => {
    let cancelled = false;

    async function init() {
      setPhase('loading');
      setLoadProgress(0);

      
      for (let i = 0; i < LOAD_PHASES.length; i++) {
        if (cancelled) return;
        setLoadLabel(LOAD_PHASES[i].label);
        setLoadProgress(Math.round(((i + 0.5) / LOAD_PHASES.length) * 100));
        await new Promise((r) => setTimeout(r, 600));
      }

      if (cancelled) return;

      try {
        await loadModels();
        if (cancelled) return;
        setLoadProgress(100);

        
        await fetchEnrolledStudents();
        if (cancelled) return;

        
        await new Promise((r) => setTimeout(r, 400));
        if (cancelled) return;

        setPhase('camera');

        
        setTimeout(() => {
          if (!cancelled && !matchedRef.current) {
            setShowDemoBtn(true);
          }
        }, 8000);
      } catch (err) {
        console.error('[LoginSiswa] Init failed:', err);
        if (cancelled) return;
        setErrorMsg(err.message || 'Gagal memuat model deteksi wajah');
        setPhase('error');
        setShowDemoBtn(true);
      }
    }

    init();

    return () => {
      cancelled = true;
    };
  }, []);

  

  const fetchEnrolledStudents = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/students/faces`);
      const data = await res.json();

      
      const parsed = data.map((s) => ({
        ...s,
        descriptor: parseDescriptor(s.face_descriptor),
      }));

      console.log(`[LoginSiswa] Loaded ${parsed.length} students, ${parsed.filter((s) => s.descriptor).length} with faces`);
      setStudents(parsed);
    } catch (err) {
      console.warn('[LoginSiswa] Could not fetch students:', err);
      
    }
  }, []);

  

  const handleFaceDetected = useCallback(
    async (detection) => {
      if (matchedRef.current) return null; 

      const count = ++detectCountRef.current;
      setDetectCount(count);

      
      const queryDesc = detection.descriptor;
      const buffer = descriptorBufferRef.current;
      buffer.push(queryDesc);

      
      if (buffer.length > BUFFER_SIZE) {
        buffer.shift();
      }

      
      if (buffer.length < 3) {
        return { student: null, distance: Infinity, confidence: 0 };
      }

      
      const result = findBestMatch(buffer, students);

      if (result.student) {
        
        matchedRef.current = true;
        setMatchedStudent(result.student);
        setConfidence(result.confidence);
        setPhase('matched');

        
        descriptorBufferRef.current = [];

        
        playSound('success');

        
        setTimeout(() => {
          if (onStudentLogin) {
            onStudentLogin(result.student);
          } else {
            onNavigate('menuSiswa');
          }
        }, 2000);

        return result;
      }

      return result; 
    },
    [students, onStudentLogin, onNavigate]
  );

  

  const handleDemoLogin = () => {
    playSound('success');
    if (onStudentLogin) {
      onStudentLogin(DEMO_STUDENT);
    } else {
      onNavigate('menuSisa');
    }
  };

  

  function playSound(type) {
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.connect(gain);
      gain.connect(ctx.destination);

      if (type === 'success') {
        
        osc.frequency.setValueAtTime(523, ctx.currentTime); 
        osc.frequency.setValueAtTime(659, ctx.currentTime + 0.15); 
        osc.frequency.setValueAtTime(784, ctx.currentTime + 0.3); 
        gain.gain.setValueAtTime(0.15, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.5);
        osc.start(ctx.currentTime);
        osc.stop(ctx.currentTime + 0.5);
      } else if (type === 'scan') {
        osc.frequency.setValueAtTime(800, ctx.currentTime);
        gain.gain.setValueAtTime(0.05, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.1);
        osc.start(ctx.currentTime);
        osc.stop(ctx.currentTime + 0.1);
      }
    } catch {
      
    }
  }

  

  return (
    <main className="view-section view-active bg-gradient-to-tr from-pastel-lavender/40 via-white to-pastel-mint/20 flex items-center justify-center min-h-screen">
      {}
      <div className="absolute top-20 right-20 w-72 h-72 bg-pastel-mint/50 rounded-full filter blur-[80px]" />
      <div className="absolute bottom-20 left-20 w-96 h-96 bg-pastel-sky/40 rounded-full filter blur-[100px]" />

      <div className="relative z-10 flex flex-col items-center px-6">
        {}
        <button
          onClick={() => onNavigate('home')}
          className="self-start absolute -top-32 md:-top-40 flex items-center gap-2 text-slate-400 hover:text-slate-600 font-medium transition-colors group"
        >
          <ArrowLeft weight="bold" className="group-hover:-translate-x-1 transition-transform" />
          Kembali
        </button>

        {}
        {phase === 'loading' && (
          <>
            <div className="w-24 h-24 rounded-3xl bg-gradient-to-br from-pastel-lavender to-purple-400 flex items-center justify-center shadow-lg mb-6 animate-pulse">
              <Sparkle weight="bold" className="text-4xl text-white" />
            </div>
            <h2 className="text-2xl md:text-3xl font-bold text-slate-700 mb-3 text-center">
              Menyiapkan Deteksi Wajah...
            </h2>
            <p className="text-slate-500 font-medium mb-8 text-center max-w-sm text-sm">
              {loadLabel}
            </p>

            {}
            <div className="w-64 h-2.5 bg-slate-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-pastel-lavender via-purple-400 to-pastel-sky rounded-full transition-all duration-500 ease-out"
                style={{ width: `${loadProgress}%` }}
              />
            </div>
            <p className="text-xs text-slate-400 mt-2 font-medium">{loadProgress}%</p>
          </>
        )}

        {}
        {phase === 'camera' && (
          <>
            <h2 className="text-2xl md:text-3xl font-bold text-slate-700 mb-2 text-center drop-shadow-sm">
              Tunjukkan Wajahmu! 📸
            </h2>
            <p className="text-slate-500 font-medium mb-6 text-center text-sm max-w-xs">
              Hadapkan wajah ke kamera untuk login otomatis
            </p>

            <CameraView
              active={phase === 'camera'}
              onFaceDetected={handleFaceDetected}
              onError={(err) => setErrorMsg(err.message)}
            />

            {}
            <p className="mt-4 text-xs text-slate-400 font-medium animate-pulse">
              {detectCount === 0
                ? '🔍 Menunggu wajah terdeteksi...'
                : `🔍 Sudah memindai ${detectCount}x...`}
            </p>

            {}
            {showDemoBtn && (
              <button
                onClick={handleDemoLogin}
                className="mt-5 flex items-center gap-2 px-5 py-2.5 rounded-xl bg-white/80 border border-slate-200 text-slate-500 text-sm font-bold hover:bg-slate-50 hover:text-slate-700 transition-all shadow-sm"
              >
                <User weight="bold" /> Mode Demo (Skip)
              </button>
            )}
          </>
        )}

        {}
        {phase === 'matched' && matchedStudent && (
          <div className="animate-fadeInUp text-center">
            {}
            <div className="relative w-32 h-32 mx-auto mb-6">
              {}
              <div className="absolute inset-0 rounded-full bg-emerald-400/20 animate-ping" style={{ animationDuration: '1.5s' }} />
              <div className="absolute inset-2 rounded-full bg-emerald-400/30 animate-ping" style={{ animationDuration: '1.5s', animationDelay: '0.3s' }} />

              {}
              <div className="absolute inset-4 rounded-full bg-gradient-to-br from-emerald-300 to-emerald-500 flex items-center justify-center shadow-lg shadow-emerald-400/40">
                <CheckCircle weight="fill" className="text-5xl text-white" />
              </div>
            </div>

            <h2 className="text-2xl md:text-3xl font-bold text-emerald-600 mb-2">
              Selamat Datang! 🎉
            </h2>
            <p className="text-xl font-bold text-slate-700 mb-1">
              {matchedStudent.nama}
            </p>
            <p className="text-sm text-slate-500 mb-3">
              {matchedStudent.kelas || 'TK-A'}
            </p>

            {}
            <div className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-full bg-emerald-50 text-emerald-600 text-sm font-bold">
              <Smiley weight="bold" />
              Kepercayaan: {confidence}%
            </div>

            <p className="mt-4 text-xs text-slate-400 animate-pulse">
              ✨ Masuk ke Menu Siswa...
            </p>
          </div>
        )}

        {}
        {phase === 'error' && (
          <>
            <div className="w-24 h-24 rounded-3xl bg-red-50 flex items-center justify-center shadow-sm mb-6">
              <WarningCircle weight="fill" className="text-4xl text-red-400" />
            </div>
            <h2 className="text-2xl font-bold text-slate-700 mb-3 text-center">
              Gagal Memuat Kamera 😅
            </h2>
            <p className="text-slate-500 font-medium mb-8 text-center max-w-sm text-sm">
              {errorMsg || 'Pastikan kamera sudah diizinkan dan tidak dipakai aplikasi lain.'}
            </p>

            <div className="flex flex-col gap-3">
              <button
                onClick={() => window.location.reload()}
                className="px-8 py-3 rounded-2xl bg-blue-500 text-white font-bold text-base hover:bg-blue-600 transition-colors shadow-md flex items-center justify-center gap-2"
              >
                <Spinner weight="bold" className="animate-spin" /> Coba Lagi
              </button>
              <button
                onClick={handleDemoLogin}
                className="px-8 py-3 rounded-2xl bg-white border-2 border-slate-200 text-slate-500 font-bold text-base hover:bg-slate-50 transition-colors flex items-center justify-center gap-2"
              >
                <User weight="bold" /> Mode Demo
              </button>
            </div>
          </>
        )}
      </div>
    </main>
  );
}
