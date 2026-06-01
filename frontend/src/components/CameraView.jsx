

import { useRef, useEffect, useState, useCallback, useCallback as unused1 } from 'react';
import Webcam from 'react-webcam';
import { detectFace } from '../lib/face-api';

const VIDEO_CONSTRAINTS = {
  width: 480,
  height: 480,
  facingMode: 'user',
};

const DETECTION_INTERVAL_MS = 600; 

export default function CameraView({
  onFaceDetected,
  onNoFace,
  onError,
  active = true,
}) {
  const webcamRef = useRef(null);
  const canvasRef = useRef(null);
  const intervalRef = useRef(null);
  const [cameraReady, setCameraReady] = useState(false);
  const [status, setStatus] = useState('initializing'); 
  const [hint, setHint] = useState('');
  const noFaceCountRef = useRef(0);

  

  const drawOverlay = useCallback((detection, matchResult) => {
    const canvas = canvasRef.current;
    const video = webcamRef.current?.video;
    if (!canvas || !video) return;

    const ctx = canvas.getContext('2d');
    const { videoWidth, videoHeight } = video;

    
    if (canvas.width !== videoWidth || canvas.height !== videoHeight) {
      canvas.width = videoWidth;
      canvas.height = videoHeight;
    }

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (!detection) return;

    const box = detection.detection.box;
    const isMatch = !!matchResult?.student;

    
    const x = box.x;
    const y = box.y;
    const w = box.width;
    const h = box.height;
    const r = Math.min(w, h) * 0.15;

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

    
    if (isMatch) {
      ctx.strokeStyle = '#34d399'; 
      ctx.lineWidth = 4;
      ctx.shadowColor = '#34d399';
      ctx.shadowBlur = 15;
    } else {
      ctx.strokeStyle = '#60a5fa'; 
      ctx.lineWidth = 3;
      ctx.shadowColor = '#60a5fa';
      ctx.shadowBlur = 10;
    }

    ctx.stroke();

    
    ctx.shadowColor = 'transparent';
    ctx.shadowBlur = 0;

    
    const label = isMatch
      ? `✓ ${matchResult.student.nama}`
      : 'Mengenali...';
    ctx.font = 'bold 14px system-ui, sans-serif';
    ctx.fillStyle = isMatch ? '#34d399' : '#60a5fa';
    ctx.textAlign = 'center';
    ctx.fillText(label, x + w / 2, y + h + 22);

    
    const cornerLen = Math.min(w, h) * 0.2;
    ctx.strokeStyle = isMatch ? '#34d399' : '#60a5fa';
    ctx.lineWidth = 3;

    
    ctx.beginPath();
    ctx.moveTo(x, y + cornerLen);
    ctx.lineTo(x, y);
    ctx.lineTo(x + cornerLen, y);
    ctx.stroke();

    
    ctx.beginPath();
    ctx.moveTo(x + w - cornerLen, y);
    ctx.lineTo(x + w, y);
    ctx.lineTo(x + w, y + cornerLen);
    ctx.stroke();

    
    ctx.beginPath();
    ctx.moveTo(x, y + h - cornerLen);
    ctx.lineTo(x, y + h);
    ctx.lineTo(x + cornerLen, y + h);
    ctx.stroke();

    
    ctx.beginPath();
    ctx.moveTo(x + w - cornerLen, y + h);
    ctx.lineTo(x + w, y + h);
    ctx.lineTo(x + w, y + h - cornerLen);
    ctx.stroke();
  }, []);

  

  const runDetection = useCallback(async () => {
    const video = webcamRef.current?.video;
    if (!video || video.readyState !== 4) return; 

    try {
      setStatus('scanning');
      const detection = await detectFace(video);

      if (detection) {
        noFaceCountRef.current = 0;
        setHint('');
        setStatus('detected');
        if (onFaceDetected) {
          const result = await onFaceDetected(detection);
          drawOverlay(detection, result);
        }
      } else {
        noFaceCountRef.current += 1;
        setStatus('ready');
        drawOverlay(null, null);

        
        const fails = noFaceCountRef.current;
        if (fails >= 10) {
          setHint('💡 Pastikan wajah terang & tidak tertutup');
        } else if (fails >= 6) {
          setHint('📸 Dekatkan wajah sedikit ke kamera');
        } else if (fails >= 3) {
          setHint('🔍 Hadapkan wajah langsung ke kamera...');
        }

        if (onNoFace) onNoFace();
      }
    } catch (err) {
      console.warn('[CameraView] Detection error:', err.message);
      
    }
  }, [onFaceDetected, onNoFace, drawOverlay]);

  

  useEffect(() => {
    if (!active || !cameraReady) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      return;
    }

    intervalRef.current = setInterval(runDetection, DETECTION_INTERVAL_MS);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [active, cameraReady, runDetection]);

  

  const handleUserMedia = useCallback(() => {
    console.log('[CameraView] Camera ready');
    setCameraReady(true);
    setStatus('ready');
  }, []);

  const handleCameraError = useCallback((err) => {
    console.error('[CameraView] Camera error:', err);
    setStatus('error');
    if (onError) onError(err);
  }, [onError]);

  

  return (
    <div className="relative w-80 h-80 md:w-[380px] md:h-[380px] rounded-[2.5rem] overflow-hidden bg-slate-900 shadow-2xl">
      {}
      <Webcam
        ref={webcamRef}
        audio={false}
        screenshotFormat="image/jpeg"
        videoConstraints={VIDEO_CONSTRAINTS}
        onUserMedia={handleUserMedia}
        onUserMediaError={handleCameraError}
        mirrored
        className="w-full h-full object-cover"
        style={{ transform: 'scaleX(-1)' }}
      />

      {}
      <canvas
        ref={canvasRef}
        className="absolute inset-0 w-full h-full"
        style={{ transform: 'scaleX(-1)', pointerEvents: 'none' }}
      />

      {}
      <div
        className="absolute inset-0 rounded-[2.5rem] pointer-events-none"
        style={{
          boxShadow: 'inset 0 0 0 3px rgba(255,255,255,0.15)',
        }}
      />

      {}
      <div className="absolute top-4 left-1/2 -translate-x-1/2 flex flex-col items-center gap-1.5">
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-black/40 backdrop-blur-sm">
          <span
            className={`w-2 h-2 rounded-full ${
              status === 'ready'
                ? 'bg-emerald-400 animate-pulse'
                : status === 'scanning'
                ? 'bg-blue-400 animate-pulse'
                : status === 'detected'
                ? 'bg-emerald-400'
                : status === 'error'
                ? 'bg-red-400'
                : 'bg-yellow-400 animate-pulse'
            }`}
          />
          <span className="text-[11px] font-bold text-white tracking-wide">
            {status === 'initializing' && 'Memuat kamera...'}
            {status === 'ready' && 'Hadapkan wajah ke kamera'}
            {status === 'scanning' && 'Mendeteksi...'}
            {status === 'detected' && 'Wajah terdeteksi! ✅'}
            {status === 'error' && 'Kamera tidak bisa diakses'}
          </span>
        </div>

        {}
        {hint && (
          <span className="text-[10px] font-medium text-amber-300 bg-black/30 px-3 py-0.5 rounded-full animate-pulse">
            {hint}
          </span>
        )}
      </div>

      {}
      {status === 'scanning' && (
        <div className="absolute inset-6 md:inset-8 pointer-events-none">
          {}
          <div
            className="absolute top-0 left-0 w-8 h-8 border-t-2 border-l-2 border-blue-400 rounded-tl-lg animate-pulse"
            style={{ animationDuration: '1s' }}
          />
          {}
          <div
            className="absolute top-0 right-0 w-8 h-8 border-t-2 border-r-2 border-blue-400 rounded-tr-lg animate-pulse"
            style={{ animationDuration: '1s', animationDelay: '0.25s' }}
          />
          {}
          <div
            className="absolute bottom-0 left-0 w-8 h-8 border-b-2 border-l-2 border-blue-400 rounded-bl-lg animate-pulse"
            style={{ animationDuration: '1s', animationDelay: '0.5s' }}
          />
          {}
          <div
            className="absolute bottom-0 right-0 w-8 h-8 border-b-2 border-r-2 border-blue-400 rounded-br-lg animate-pulse"
            style={{ animationDuration: '1s', animationDelay: '0.75s' }}
          />
        </div>
      )}
    </div>
  );
}
