

import { useState, useRef, useCallback, useEffect } from 'react';
import Webcam from 'react-webcam';
import {
  Camera,
  CheckCircle,
  XCircle,
  Spinner,
  ArrowRight,
  ArrowLeft,
  User,
  Trash,
  WarningCircle,
} from '@phosphor-icons/react';
import * as faceapi from 'face-api.js';
import { loadModels } from '../lib/face-api';
import API_BASE, { apiFetch } from '../lib/api';

const VIDEO_CONSTRAINTS = {
  width: 320,
  height: 320,
  facingMode: 'user',
};

export default function FaceEnrollmentForm({ student, students, onEnrolled, onCancel }) {
  
  const [step, setStep] = useState('select'); 
  const [selectedStudent, setSelectedStudent] = useState(student || null);
  const [modelsReady, setModelsReady] = useState(false);
  const [loadingModels, setLoadingModels] = useState(false);
  const [webcamReady, setWebcamReady] = useState(false);
  const [snapshot, setSnapshot] = useState(null); 
  const [detection, setDetection] = useState(null); 
  const [descriptor, setDescriptor] = useState(null); 
  const [saving, setSaving] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  const webcamRef = useRef(null);
  const canvasRef = useRef(null);

  

  useEffect(() => {
    async function init() {
      if (faceapi.nets.ssdMobilenetv1.isLoaded) {
        setModelsReady(true);
        return;
      }
      setLoadingModels(true);
      try {
        await loadModels();
        setModelsReady(true);
      } catch (err) {
        console.error('[Enrollment] Model load failed:', err);
        setErrorMsg('Gagal memuat model deteksi wajah.');
        setStep('error');
      } finally {
        setLoadingModels(false);
      }
    }
    init();
  }, []);

  

  const handleCapture = useCallback(async () => {
    const video = webcamRef.current?.video;
    if (!video || video.readyState !== 4) return;

    try {
      
      const detectResult = await faceapi
        .detectSingleFace(video)
        .withFaceLandmarks()
        .withFaceDescriptor();

      if (!detectResult) {
        setErrorMsg('Wajah tidak terdeteksi. Pastikan wajah terlihat jelas di kamera.');
        return;
      }

      
      const imgSrc = webcamRef.current.getScreenshot();
      setSnapshot(imgSrc);
      setDetection(detectResult);
      setDescriptor(detectResult.descriptor);
      setStep('preview');
      setErrorMsg('');

      
      drawFaceBox(detectResult);
    } catch (err) {
      console.error('[Enrollment] Capture error:', err);
      setErrorMsg('Gagal menangkap wajah: ' + err.message);
    }
  }, []);

  

  const drawFaceBox = useCallback((detection) => {
    const canvas = canvasRef.current;
    const video = webcamRef.current?.video;
    if (!canvas || !video) return;

    const ctx = canvas.getContext('2d');
    canvas.width = video.videoWidth || 320;
    canvas.height = video.videoHeight || 320;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const box = detection.detection.box;
    const x = box.x;
    const y = box.y;
    const w = box.width;
    const h = box.height;
    const r = Math.min(w, h) * 0.12;

    
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.lineTo(x + w - r, y);
    ctx.quadraticCurveTo(x + w, y, x + w, y + r);
    ctx.lineTo(x + w, y + h - r);
    ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
    ctx.lineTo(x + r, y + h);
    ctx.quadraticCurveTo(x, y + h, x, y + h - r);
    ctx.lineTo(x, y + r);
    ctx.quadraticCurveTo(x, y, x + r, y);
    ctx.closePath();

    ctx.strokeStyle = '#34d399';
    ctx.lineWidth = 4;
    ctx.shadowColor = '#34d399';
    ctx.shadowBlur = 15;
    ctx.stroke();

    
    const cl = Math.min(w, h) * 0.18;
    ctx.lineWidth = 3;
    ctx.shadowBlur = 0;

    [[x, y, 1, 1], [x + w - cl, y, 1, -1], [x, y + h - cl, -1, 1], [x + w - cl, y + h - cl, -1, -1]].forEach(
      ([cx, cy, dx, dy]) => {
        ctx.beginPath();
        ctx.moveTo(cx, cy + cl * dy);
        ctx.lineTo(cx, cy);
        ctx.lineTo(cx + cl * dx, cy);
        ctx.stroke();
      }
    );
  }, []);

  

  const handleSubmit = useCallback(async () => {
    if (!selectedStudent || !descriptor) return;

    setSaving(true);
    setErrorMsg('');

    try {
      
      const descArray = Array.from(descriptor);

      
      let imageUrl = null;
      if (snapshot) {
        
        
        imageUrl = `enrolled-${selectedStudent.id}-${Date.now()}`;
      }

      const res = await apiFetch(`/api/students/${selectedStudent.id}/enroll-face`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          face_descriptor: descArray,
          face_image_url: imageUrl,
        }),
      });

      const result = await res.json();

      if (!res.ok) {
        throw new Error(result.detail || 'Gagal menyimpan data wajah');
      }

      setSuccessMsg(result.message || 'Wajah berhasil didaftarkan!');
      setStep('done');

      
      playSound('success');

      
      setTimeout(() => {
        if (onEnrolled) onEnrolled(selectedStudent.id);
      }, 2000);

    } catch (err) {
      console.error('[Enrollment] Submit error:', err);
      setErrorMsg(err.message || 'Terjadi kesalahan saat menyimpan.');
      setSaving(false);
    }
  }, [selectedStudent, descriptor, snapshot, onEnrolled]);

  

  const handleReset = () => {
    setStep(selectedStudent ? 'capturing' : 'select');
    setSnapshot(null);
    setDetection(null);
    setDescriptor(null);
    setErrorMsg('');
    setSuccessMsg('');
    setSaving(false);
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
        osc.frequency.setValueAtTime(784, ctx.currentTime + 0.15);
        gain.gain.setValueAtTime(0.12, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.4);
        osc.start(ctx.currentTime);
        osc.stop(ctx.currentTime + 0.4);
      }
    } catch {  }
  }

  

  const unenrolledStudents = (students || []).filter(
    (s) => s.role === 'student' && !s.face_descriptor
  );

  const enrolledStudents = (students || []).filter(
    (s) => s.role === 'student' && s.face_descriptor
  );

  

  return (
    <div className="max-w-lg mx-auto">
      {}
      {step === 'select' && (
        <div>
          <h3 className="text-xl font-bold text-slate-800 mb-1">Pilih Siswa</h3>
          <p className="text-sm text-slate-500 mb-6">Pilih siswa yang akan didaftarkan wajahnya</p>

          {}
          {unenrolledStudents.length > 0 ? (
            <div className="space-y-2">
              {unenrolledStudents.map((s) => (
                <button
                  key={s.id}
                  onClick={() => { setSelectedStudent(s); setStep('capturing'); }}
                  className="w-full flex items-center gap-3 p-4 rounded-2xl border border-slate-200 bg-white hover:bg-blue-50 hover:border-blue-200 transition-all text-left group"
                >
                  <img
                    src={`https://api.dicebear.com/7.x/adventurer/svg?seed=${s.nama}`}
                    className="w-12 h-12 rounded-full bg-slate-100"
                    alt={s.nama}
                  />
                  <div className="flex-1 min-w-0">
                    <p className="font-bold text-slate-700 group-hover:text-blue-600">{s.nama}</p>
                    <p className="text-xs text-slate-400">{s.kelas || '-'} · NIS: {s.nis || '-'}</p>
                  </div>
                  <ArrowRight weight="bold" className="text-slate-300 group-hover:text-blue-400 transition-colors" />
                </button>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 bg-white rounded-2xl border border-emerald-100">
              <CheckCircle weight="fill" className="text-4xl text-emerald-400 mx-auto mb-3" />
              <p className="font-bold text-slate-700">Semua siswa sudah terdaftar! 🎉</p>
              <p className="text-xs text-slate-400 mt-1">Tidak ada siswa yang perlu enrollment</p>
            </div>
          )}

          {}
          {enrolledStudents.length > 0 && (
            <div className="mt-6">
              <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Sudah Terdaftar ({enrolledStudents.length})</p>
              <div className="space-y-2">
                {enrolledStudents.map((s) => (
                  <div key={s.id} className="flex items-center gap-3 p-3 rounded-xl bg-emerald-50/50 border border-emerald-100">
                    <img
                      src={`https://api.dicebear.com/7.x/adventurer/svg?seed=${s.nama}`}
                      className="w-9 h-9 rounded-full bg-slate-100"
                      alt={s.nama}
                    />
                    <div className="flex-1 min-w-0">
                      <p className="font-bold text-sm text-slate-700">{s.nama}</p>
                      <p className="text-[10px] text-emerald-600 font-medium">✓ Wajah terdaftar</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {}
      {step === 'capturing' && selectedStudent && (
        <div>
          {}
          <button
            onClick={() => { setSelectedStudent(null); setStep('select'); }}
            className="flex items-center gap-2 text-sm font-bold text-slate-400 hover:text-slate-600 mb-4 transition-colors"
          >
            <ArrowLeft weight="bold" /> Pilih siswa lain
          </button>

          <div className="flex items-center gap-3 p-4 rounded-2xl bg-white border border-slate-100 shadow-sm mb-5">
            <img
              src={`https://api.dicebear.com/7.x/adventurer/svg?seed=${selectedStudent.nama}`}
              className="w-14 h-14 rounded-full bg-slate-100"
              alt={selectedStudent.nama}
            />
            <div>
              <p className="font-bold text-slate-800">{selectedStudent.nama}</p>
              <p className="text-xs text-slate-500">{selectedStudent.kelas || 'TK-A'} · NIS: {selectedStudent.nis || '-'}</p>
            </div>
          </div>

          {!modelsReady || loadingModels ? (
            <div className="bg-white rounded-2xl p-10 border border-slate-100 text-center">
              <Spinner weight="bold" className="text-3xl text-blue-400 animate-spin mx-auto mb-3" />
              <p className="text-sm font-medium text-slate-500">Memuat model deteksi...</p>
            </div>
          ) : (
            <>
              {}
              <div className="relative w-72 h-72 md:w-80 md:h-80 mx-auto rounded-[2rem] overflow-hidden bg-slate-900 shadow-xl mb-4">
                <Webcam
                  ref={webcamRef}
                  audio={false}
                  screenshotFormat="image/jpeg"
                  videoConstraints={VIDEO_CONSTRAINTS}
                  onUserMedia={() => setWebcamReady(true)}
                  onUserMediaError={(e) => setErrorMsg('Kamera tidak bisa diakses: ' + e.message)}
                  mirrored
                  className="w-full h-full object-cover"
                />

                {}
                <canvas
                  ref={canvasRef}
                  className="absolute inset-0 w-full h-full pointer-events-none"
                  style={{ transform: 'scaleX(-1)' }}
                />

                {}
                <div
                  className="absolute inset-0 rounded-[2rem] pointer-events-none"
                  style={{ boxShadow: 'inset 0 0 0 3px rgba(255,255,255,0.15)' }}
                />

                {}
                <div className="absolute top-3 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full bg-black/40 backdrop-blur-sm">
                  <span className="text-[11px] font-bold text-white">
                    {webcamReady ? '📷 Hadapkan wajah ke kamera' : '⏳ Menyalakan kamera...'}
                  </span>
                </div>

                {}
                {webcamReady && (
                  <div className="absolute inset-5 pointer-events-none">
                    {[['top-0 left-0', 'tl'], ['top-0 right-0', 'tr'], ['bottom-0 left-0', 'bl'], ['bottom-0 right-0', 'br']].map(
                      ([pos, _]) => (
                        <div
                          key={pos}
                          className={`absolute ${pos} w-6 h-6 border-2 border-emerald-400/60 rounded-sm animate-pulse`}
                          style={{ animationDuration: '1.5s' }}
                        />
                      )
                    )}
                  </div>
                )}
              </div>

              {}
              <div className="flex justify-center">
                <button
                  onClick={handleCapture}
                  disabled={!webcamReady}
                  className="w-20 h-20 rounded-full bg-gradient-to-br from-pastel-sky to-blue-500 text-white shadow-lg shadow-blue-300/50 hover:shadow-xl hover:scale-105 active:scale-95 transition-all flex items-center justify-center disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <Camera weight="fill" className="text-3xl" />
                </button>
              </div>
              <p className="text-center text-xs text-slate-400 mt-3 font-medium">
                Tombol untuk ambil foto wajah
              </p>
            </>
          )}

          {}
          {errorMsg && step === 'capturing' && (
            <div className="mt-4 flex items-center gap-2 px-4 py-2.5 rounded-xl bg-red-50 border border-red-100 text-red-600 text-sm">
              <WarningCircle weight="bold" className="shrink-0" />
              {errorMsg}
            </div>
          )}
        </div>
      )}

      {}
      {step === 'preview' && selectedStudent && snapshot && (
        <div>
          <button
            onClick={handleReset}
            className="flex items-center gap-2 text-sm font-bold text-slate-400 hover:text-slate-600 mb-4 transition-colors"
          >
            <ArrowLeft weight="bold" /> Foto ulang
          </button>

          <h3 className="text-lg font-bold text-slate-800 mb-1">Preview Wajah</h3>
          <p className="text-sm text-slate-500 mb-4">Periksa foto wajah {selectedStudent.nama}, lalu konfirmasi</p>

          {}
          <div className="relative w-64 h-64 mx-auto rounded-2xl overflow-hidden border-4 border-emerald-200 shadow-lg mb-5">
            <img src={snapshot} alt="Captured face" className="w-full h-full object-cover" />
            <div className="absolute bottom-2 right-2 px-2 py-1 rounded-lg bg-emerald-500 text-white text-[10px] font-bold flex items-center gap-1">
              <CheckCircle weight="bold" /> Terdeteksi
            </div>
          </div>

          {}
          <div className="grid grid-cols-2 gap-3 mb-5">
            <div className="bg-blue-50 rounded-xl p-3 text-center">
              <p className="text-[10px] text-blue-400 font-bold uppercase">Deskriptor</p>
              <p className="text-lg font-bold text-blue-600">{descriptor?.length || 0} dim</p>
            </div>
            <div className="bg-purple-50 rounded-xl p-3 text-center">
              <p className="text-[10px] text-purple-400 font-bold uppercase">Siswa</p>
              <p className="text-sm font-bold text-purple-600 truncate">{selectedStudent.nama}</p>
            </div>
          </div>

          {}
          <button
            onClick={handleSubmit}
            disabled={saving}
            className="w-full py-3.5 rounded-2xl bg-gradient-to-r from-emerald-500 to-green-500 text-white font-bold text-base shadow-lg shadow-emerald-300/30 hover:shadow-xl active:scale-[0.98] transition-all flex items-center justify-center gap-2 disabled:opacity-60"
          >
            {saving ? (
              <>
                <Spinner weight="bold" className="animate-spin" /> Menyimpan...
              </>
            ) : (
              <>
                <CheckCircle weight="bold" /> Daftarkan Wajah ✅
              </>
            )}
          </button>

          {errorMsg && (
            <div className="mt-3 flex items-center gap-2 px-4 py-2.5 rounded-xl bg-red-50 border border-red-100 text-red-600 text-sm">
              <WarningCircle weight="bold" className="shrink-0" />
              {errorMsg}
            </div>
          )}
        </div>
      )}

      {}
      {step === 'done' && (
        <div className="text-center py-8 animate-fadeInUp">
          <div className="w-24 h-24 mx-auto mb-6 relative">
            <div className="absolute inset-0 rounded-full bg-emerald-400/20 animate-ping" style={{ animationDuration: '1.5s' }} />
            <div className="absolute inset-2 rounded-full bg-emerald-400/30 animate-ping" style={{ animationDuration: '1.5s', animationDelay: '0.3s' }} />
            <div className="absolute inset-4 rounded-full bg-gradient-to-br from-emerald-300 to-emerald-500 flex items-center justify-center shadow-lg">
              <CheckCircle weight="fill" className="text-4xl text-white" />
            </div>
          </div>
          <h3 className="text-2xl font-bold text-emerald-600 mb-2">Berhasil! 🎉</h3>
          <p className="text-slate-600 font-medium mb-1">{successMsg}</p>
          <p className="text-sm text-slate-400">
            {selectedStudent?.nama} sekarang bisa login dengan wajah
          </p>

          <button
            onClick={handleReset}
            className="mt-6 px-6 py-2.5 rounded-xl bg-white border-2 border-slate-200 text-slate-500 font-bold text-sm hover:bg-slate-50 transition-colors"
          >
            Daftarkan Siswa Lainnya
          </button>
        </div>
      )}

      {}
      {step === 'error' && (
        <div className="text-center py-10">
          <WarningCircle weight="fill" className="text-5xl text-red-300 mx-auto mb-4" />
          <h3 className="text-xl font-bold text-slate-700 mb-2">Terjadi Kesalahan</h3>
          <p className="text-sm text-slate-500 mb-6">{errorMsg || 'Gagal memuat model deteksi wajah.'}</p>
          <div className="flex gap-3 justify-center">
            <button
              onClick={() => { setErrorMsg(''); setStep('select'); }}
              className="px-5 py-2.5 rounded-xl bg-blue-500 text-white font-bold text-sm hover:bg-blue-600 transition-colors"
            >
              Coba Lagi
            </button>
            {onCancel && (
              <button
                onClick={onCancel}
                className="px-5 py-2.5 rounded-xl bg-white border border-slate-200 text-slate-500 font-bold text-sm hover:bg-slate-50 transition-colors"
              >
                Batal
              </button>
            )}
          </div>
        </div>
      )}

      {}
      {step !== 'done' && step !== 'error' && onCancel && (
        <button
          onClick={onCancel}
          className="mt-6 w-full py-2.5 rounded-xl text-slate-400 text-sm font-medium hover:text-slate-600 transition-colors"
        >
          Tutup
        </button>
      )}
    </div>
  );
}
