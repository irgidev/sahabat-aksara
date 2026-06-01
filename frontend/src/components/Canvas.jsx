import { useState, useRef, useEffect, useCallback } from "react";
import {
  ArrowLeft,
  Star,
  Sparkle,
  CheckCircle,
  ArrowCounterClockwise,
  Trash,
  CaretRight,
  SpeakerHigh,
  Confetti,
  PaintBucket,
} from "@phosphor-icons/react";
import confetti from "canvas-confetti";


const COLORS = [
  { name: "Hitam", value: "#1e293b", ring: "ring-slate-400" },
  { name: "Merah", value: "#ef4444", ring: "ring-red-300" },
  { name: "Biru", value: "#3b82f6", ring: "ring-blue-300" },
  { name: "Hijau", value: "#22c55e", ring: "ring-green-300" },
  { name: "Ungu", value: "#a855f7", ring: "ring-purple-300" },
  { name: "Orange", value: "#f97316", ring: "ring-orange-300" },
  { name: "Pink", value: "#ec4899", ring: "ring-pink-300" },
];





let _cachedBestVoice = null;
let _voicesLoaded = false;
let _ttsKeepAlive = null;

function startTTSKeepAlive() {
  if (_ttsKeepAlive) return;
  if (!("speechSynthesis" in window)) return;
  _ttsKeepAlive = setInterval(() => {
    try {
      window.speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance("");
      u.volume = 0;
      window.speechSynthesis.speak(u);
    } catch {
      
    }
  }, 9000);
}

function stopTTSKeepAlive() {
  if (_ttsKeepAlive) {
    clearInterval(_ttsKeepAlive);
    _ttsKeepAlive = null;
  }
}

function findBestKidVoice() {
  if (_cachedBestVoice) return _cachedBestVoice;

  const voices = window.speechSynthesis.getVoices();
  if (!voices.length) return null;

  let best = null;
  let bestScore = -1;

  for (const v of voices) {
    let score = 0;
    const name = (v.name || "").toLowerCase();
    const lang = (v.lang || "").toLowerCase();

    if (lang.startsWith("id")) score += 50;
    else if (lang.startsWith("en")) score += 20;

    if (name.includes("female") || name.includes("woman") || name.includes("girl"))
      score += 30;
    if (name.includes("samantha") || name.includes("karen") || name.includes("zira") ||
        name.includes("serena") || name.includes("moira") || name.includes("tessa"))
      score += 25;
    if (name.includes("neural") || name.includes("natural") || name.includes("online"))
      score += 15;
    if (name.includes("microsoft")) {
      if (name.includes("irina") || name.includes("heera") || name.includes("bella") ||
          name.includes("jenny") || name.includes("sara") || name.includes("amanda"))
        score += 35;
      else if (name.includes("david") || name.includes("mark") || name.includes("george"))
        score -= 10;
    }
    if (name.includes("robot") || name.includes("synthetic")) score -= 50;

    if (score > bestScore) {
      bestScore = score;
      best = v;
    }
  }

  _cachedBestVoice = best;
  return best;
}

function speak(text, opts = {}) {
  if (!("speechSynthesis" in window)) return;
  window.speechSynthesis.cancel();
  const maxLen = 60;
  const shortText = text.length > maxLen ? text.slice(0, maxLen).trim() + "..." : text;
  const u = new SpeechSynthesisUtterance(shortText);
  u.lang = "id-ID";
  u.rate = opts.rate ?? 0.95;
  u.pitch = opts.pitch ?? 1.08;
  u.volume = opts.volume ?? 1.0;
  const voice = findBestKidVoice();
  if (voice) u.voice = voice;
  u.onerror = (event) => {
    console.warn("[TTS] Speech error:", event.error);
  };
  window.speechSynthesis.speak(u);
}

function speakExcited(text) {
  speak(text, { rate: 1.05, pitch: 1.12 });
}
function speakGentle(text) {
  speak(text, { rate: 0.88, pitch: 1.04 });
}

function warmUpVoices() {
  if (!("speechSynthesis" in window)) return;
  startTTSKeepAlive();
  const tryLoad = () => {
    const voices = window.speechSynthesis.getVoices();
    if (voices.length > 0) {
      _voicesLoaded = true;
      findBestKidVoice();
      console.log(`[TTS] ${voices.length} voices loaded. Best: ${_cachedBestVoice?.name || 'none'}`);
    }
    return voices;
  };
  const voices = tryLoad();
  if (!voices.length) {
    window.speechSynthesis.addEventListener("voiceschanged", tryLoad, { once: true });
    setTimeout(tryLoad, 2000);
  }
}


function getFeedbackMessage(stars, charTarget) {
  switch (stars) {
    case 3:
      return `Mantap! Huruf ${charTarget} sempurna!`;
    case 2:
      return `Bagus banget huruf ${charTarget}!`;
    case 1:
      return `Lumayan! Ayo coba lagi ya!`;
    default:
      return `Yuk, coba tulis ${charTarget} lagi!`;
  }
}

function getEncouragement() {
  const msgs = [
    "Kamu pasti bisa!",
    "Ayo sedikit lagi!",
    "Percaya diri!",
    "Kamu hebat!",
    "Terus semangat!",
    "Hampir sempurna!",
    "Saya yakin kamu bisa!",
  ];
  return msgs[Math.floor(Math.random() * msgs.length)];
}







function getStarsFromAccuracy(accuracy) {
  if (accuracy >= 70) return 3;   
  if (accuracy >= 45) return 2;   
  if (accuracy >= 20) return 1;   
  return 0;                     
}


function detectDeviceType() {
  const ua = navigator.userAgent || "";
  if (/tablet|ipad|playbook|silk/i.test(ua)) return "tablet";
  if (/mobile|android|iphone|ipod|blackberry|opera mini|opera mobi/i.test(ua)) return "mobile";
  if (/win|mac|linux/i.test(navigator.platform)) return "desktop";
  return "unknown";
}

function getCanvasSize() {
  return typeof window !== "undefined"
    ? { w: window.innerWidth, h: window.innerHeight }
    : { w: 600, h: 400 };
}

export default function Canvas({ onNavigate, lesson, student }) {
  const canvasRef = useRef(null);
  const containerRef = useRef(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [strokeCoordinates, setStrokeCoordinates] = useState([]);
  const [strokeHistory, setStrokeHistory] = useState([]);
  const [stars, setStars] = useState(0);
  const [isShaking, setIsShaking] = useState(false);
  const [showClearConfirm, setShowClearConfirm] = useState(false);
  const [selectedColor, setSelectedColor] = useState(COLORS[0].value);
  const [isEvaluated, setIsEvaluated] = useState(false);
  const [lastAccuracy, setLastAccuracy] = useState(0);
  const drawStartTimeRef = useRef(null);

  useEffect(() => {
    warmUpVoices();
    return () => {
      stopTTSKeepAlive();
      if ("speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  const charTarget = lesson?.char || "A";
  const lessonId = lesson?.lessonId || 1;

  
  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    const resize = () => {
      const tmp = document.createElement("canvas");
      tmp.width = canvas.width || 1;
      tmp.height = canvas.height || 1;
      tmp.getContext("2d").drawImage(canvas, 0, 0);
      canvas.width = container.clientWidth;
      canvas.height = container.clientHeight;
      canvas.getContext("2d").drawImage(tmp, 0, 0);
    };
    resize();
    window.addEventListener("resize", resize);
    return () => window.removeEventListener("resize", resize);
  }, []);

  
  const getCoords = useCallback((e) => {
    const c = canvasRef.current;
    const r = c.getBoundingClientRect();
    const cx = e.touches ? e.touches[0].clientX : e.clientX;
    const cy = e.touches ? e.touches[0].clientY : e.clientY;
    return {
      x: ((cx - r.left) / r.width) * c.width,
      y: ((cy - r.top) / r.height) * c.height,
      rawX: cx - r.left,
      rawY: cy - r.top,
    };
  }, []);

  
  const startDraw = useCallback((e) => {
    if (e.cancelable) e.preventDefault();
    const { x, y, rawX, rawY } = getCoords(e);
    setIsDrawing(true);
    const ctx = canvasRef.current.getContext("2d");
    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.lineWidth = 14;
    ctx.strokeStyle = selectedColor;
    setStrokeCoordinates((p) => [...p, { x: rawX, y: rawY }]);
  }, [getCoords, selectedColor]);

  const drawing = useCallback((e) => {
    if (e.cancelable) e.preventDefault();
    if (!isDrawing) return;
    const { x, y, rawX, rawY } = getCoords(e);
    const ctx = canvasRef.current.getContext("2d");
    ctx.lineTo(x, y);
    ctx.stroke();
    setStrokeCoordinates((p) => [...p, { x: rawX, y: rawY }]);
  }, [isDrawing, getCoords]);

  const stopDraw = useCallback(() => {
    if (!isDrawing) return;
    canvasRef.current.getContext("2d").closePath();
    setIsDrawing(false);
    setStrokeHistory((h) => [...h, canvasRef.current.toDataURL()]);
  }, [isDrawing]);

  
  const handleUndo = () => {
    if (strokeHistory.length === 0) return;
    const h = [...strokeHistory];
    h.pop();
    const c = canvasRef.current;
    const ctx = c.getContext("2d");
    ctx.clearRect(0, 0, c.width, c.height);
    if (h.length > 0) {
      const img = new Image();
      img.onload = () => ctx.drawImage(img, 0, 0);
      img.src = h[h.length - 1];
    }
    setStrokeHistory(h);
    setIsEvaluated(false);
    setStars(0);
  };

  
  const handleClear = () => {
    if (showClearConfirm) {
      const c = canvasRef.current;
      c.getContext("2d").clearRect(0, 0, c.width, c.height);
      setStrokeCoordinates([]);
      setStrokeHistory([]);
      setStars(0);
      setIsEvaluated(false);
      setShowClearConfirm(false);
      drawStartTimeRef.current = null;
    } else {
      setShowClearConfirm(true);
      setTimeout(() => setShowClearConfirm(false), 3000);
    }
  };

  
  const fireConfetti = () => {
    const end = Date.now() + 2000;
    const colors = ["#FFD700", "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4"];
    (function frame() {
      confetti({ particleCount: 4, angle: 60, spread: 55, origin: { x: 0 }, colors });
      confetti({ particleCount: 4, angle: 120, spread: 55, origin: { x: 1 }, colors });
      if (Date.now() < end) requestAnimationFrame(frame);
    })();
  };

  
  const handleEvaluate = async () => {
    if (strokeCoordinates.length < 5) {
      speakGentle("Hmm, gambarnya belum kelihatan. Yuk tulis dulu!");
      setIsShaking(true);
      setTimeout(() => setIsShaking(false), 400);
      return;
    }

    const evalStartTime = Date.now();
    const durationMs = drawStartTimeRef.current
      ? Math.round(Date.now() - drawStartTimeRef.current)
      : null;
    const canvasSize = getCanvasSize();
    const deviceType = detectDeviceType();

    const xs = strokeCoordinates.map((p) => p.x);
    const ys = strokeCoordinates.map((p) => p.y);
    const bbMinX = Math.min(...xs), bbMaxX = Math.max(xs);
    const bbMinY = Math.min(...ys), bbMaxY = Math.max(ys);

    const strokeMetadata = {
      point_count: strokeCoordinates.length,
      bounding_box: {
        width: Math.round(bbMaxX - bbMinX),
        height: Math.round(bbMaxY - bbMinY),
      },
      canvas_size: canvasSize,
      duration_ms: durationMs,
      color_used: selectedColor,
      device_type: deviceType,
      evaluated_at: new Date().toISOString(),
    };

    try {
      const res = await fetch("http://localhost:8000/api/evaluate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          strokeCoordinates,
          student_id: student?.id || "11111111-1111-1111-1111-111111111111",
          lesson_id: lessonId,
          char_target: charTarget,
          metadata: strokeMetadata,
        }),
      });

      const data = await res.json();
      const acc = data.accuracy || 0;
      const s = getStarsFromAccuracy(acc);

      setStars(s);
      setLastAccuracy(acc);
      setIsEvaluated(true);

      if (s === 0) {
        setIsShaking(true);
        setTimeout(() => setIsShaking(false), 500);
        setTimeout(() => speakGentle(getEncouragement()), 400);
        setTimeout(() => {
          const c = canvasRef.current;
          c.getContext("2d").clearRect(0, 0, c.width, c.height);
          setStrokeCoordinates([]);
          setStrokeHistory([]);
          setIsEvaluated(false);
          drawStartTimeRef.current = null;
        }, 2000);

      } else if (s === 3) {
        fireConfetti();
        setTimeout(() => speakExcited(getFeedbackMessage(s, charTarget)), 500);

      } else if (s === 2 || s === 1) {
        setTimeout(() => speak(getFeedbackMessage(s, charTarget)), 400);
      }
    } catch {
      speakGentle("Oops, coba lagi ya!");
    }
  };

  
  const handleNextChar = () => {
    if (!lesson) return;
    const nid = lesson.lessonId + 1;
    let next = null;

    if (lesson.lessonId >= 1 && lesson.lessonId <= 25)
      next = { char: String.fromCharCode(65 + lesson.lessonId), label: `Huruf ${String.fromCharCode(65 + lesson.lessonId)}`, lessonId: nid };
    else if (lesson.lessonId >= 27 && lesson.lessonId <= 51)
      next = { char: String.fromCharCode(97 + (lesson.lessonId - 27)), label: `Huruf ${String.fromCharCode(97 + (lesson.lessonId - 27))}`, lessonId: nid };
    else if (lesson.lessonId >= 53 && lesson.lessonId <= 61)
      next = { char: String(lesson.lessonId - 53), label: `Angka ${lesson.lessonId - 53}`, lessonId: nid };

    if (next) {
      const c = canvasRef.current;
      c.getContext("2d").clearRect(0, 0, c.width, c.height);
      setStrokeCoordinates([]);
      setStrokeHistory([]);
      setStars(0);
      setIsEvaluated(false);
      setLastAccuracy(0);
      drawStartTimeRef.current = null;
      onNavigate("canvas", { lesson: next });
    } else {
        speakExcited("Wah, kamu hebat banget! Semua sudah selesai!");
        onNavigate("menuSiswa");
    }
  };

  
  const handleRetry = () => {
    const c = canvasRef.current;
    c.getContext("2d").clearRect(0, 0, c.width, c.height);
    setStrokeCoordinates([]);
    setStrokeHistory([]);
    setIsEvaluated(false);
    setStars(0);
    drawStartTimeRef.current = null;
    speak(getEncouragement());
  };

  
  
  

  return (
    <main className="view-section view-active bg-gradient-to-b from-slate-100 to-white flex flex-col h-full overflow-hidden ios-no-bounce">

      {}
      <div className="flex items-center justify-between px-4 md:px-8 lg:px-12 py-2 md:py-3 shrink-0">
        <div className="flex items-center gap-2 md:gap-3">
          <button
            onClick={() => onNavigate("menuSiswa")}
            className="w-11 h-11 md:w-13 md:h-13 lg:w-14 lg:h-14 rounded-full bg-white shadow-sm border border-slate-100 flex items-center justify-center text-slate-400 hover:text-slate-600 hover:shadow-md active:scale-95 transition-all"
          >
            <ArrowLeft weight="bold" className="text-xl md:text-2xl" />
          </button>

          <div className="flex items-center gap-2 md:gap-3">
            <span className="text-lg md:text-xl lg:text-2xl font-bold text-slate-500">Tulis</span>
            <span className="text-3xl md:text-5xl lg:text-6xl font-black text-transparent bg-clip-text bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 drop-shadow-sm">
              {charTarget}
            </span>
          </div>

          <button
            onClick={() => speak(`Tulis huruf ${charTarget}!`)}
            className="w-10 h-10 md:w-12 md:h-12 rounded-full bg-purple-100 hover:bg-purple-200 flex items-center justify-center text-purple-500 transition-colors active:scale-95"
          >
            <SpeakerHigh weight="bold" className="text-lg md:text-xl lg:text-2xl" />
          </button>
        </div>

        {}
        <div className={`flex items-center gap-1 md:gap-2 px-3 md:px-4 py-1.5 md:py-2 rounded-full transition-all duration-300 ${
          stars >= 3
            ? "bg-yellow-100 border-2 border-yellow-400 shadow-md"
            : stars >= 1
            ? "bg-blue-50 border border-blue-200"
            : "bg-white/60 border border-slate-200"
        }`}>
          {[1, 2, 3].map((s) => (
            <Star
              key={s}
              weight={stars >= s ? "fill" : "duotone"}
              className={`text-2xl md:text-3xl transition-all ${
                stars >= s ? "text-yellow-400 drop-shadow star-pop" : "text-slate-200"
              }`}
              style={stars >= s ? { animationDelay: `${s * 0.15}s` } : undefined}
            />
          ))}
          {isEvaluated && (
            <span className="text-sm md:text-base font-bold text-slate-500 ml-1 md:ml-2">{lastAccuracy}%</span>
          )}
        </div>
      </div>

      {}
      <div className="flex-1 px-3 md:px-6 lg:px-10 pb-2 min-h-0">
        <div
          ref={containerRef}
          className={`w-full h-full bg-white rounded-2xl md:rounded-3xl shadow-lg border-[3px] md:border-[4] border-blue-100 relative overflow-hidden cursor-crosshair canvas-ipad-landscape ${
            isShaking ? "animate-shake" : ""
          }`}
        >
          {}
          <canvas
            ref={canvasRef}
            className="absolute inset-0 z-20 touch-none"
            onMouseDown={startDraw}
            onMouseMove={drawing}
            onMouseUp={stopDraw}
            onMouseOut={stopDraw}
            onTouchStart={startDraw}
            onTouchMove={drawing}
            onTouchEnd={stopDraw}
            onTouchCancel={stopDraw}
          />

          {}
          <div className="absolute inset-0 flex items-center justify-center z-10 pointer-events-none">
            <div className="relative w-[50%] md:w-[55%] max-w-[280px] md:max-w-[360px] aspect-[3/4] flex items-center justify-center">
              <div className="absolute inset-0 border-[3px] md:border-4 border-dashed border-blue-100 rounded-2xl md:rounded-3xl" />
              <span
                className="text-[10rem] md:text-[16rem] lg:text-[20rem] font-bold leading-none select-none text-blue-50/80"
                style={{ WebkitTextStroke: "2px #bfdbfe" }}
              >
                {charTarget}
              </span>
            </div>
          </div>

          {}
          <Sparkle weight="fill" className="absolute top-3 left-3 md:top-5 md:left-5 text-xl md:text-3xl text-yellow-300/60 z-10 pointer-events-none" />
          <Sparkle weight="fill" className="absolute bottom-16 right-3 md:bottom-20 md:right-5 text-2xl md:text-4xl text-blue-300/40 z-10 pointer-events-none" />

          {}
          {isEvaluated && stars > 0 && (
            <div className="absolute bottom-4 md:bottom-6 left-1/2 -translate-x-1/2 z-30 animate-gentle-bounce w-[88%] md:w-[92%] max-w-lg">
              <div className={`flex flex-col md:flex-row items-center gap-2 md:gap-3 px-4 md:px-6 py-3 md:py-3.5 rounded-xl md:rounded-2xl border-2 shadow-lg ${
                stars === 3
                  ? "bg-gradient-to-r from-yellow-50 to-amber-50 border-yellow-300"
                  : stars === 2
                  ? "bg-blue-50 border-blue-200"
                  : "bg-orange-50 border-orange-200"
              }`}>
                <div className="flex items-center gap-2 min-w-0">
                  {stars === 3 && (
                    <Confetti weight="fill" className="text-2xl md:text-3xl text-yellow-500 shrink-0" />
                  )}
                  <span className="font-bold text-sm md:text-lg text-slate-700 truncate text-center md:text-left">
                    {getFeedbackMessage(stars, charTarget)}
                  </span>
                </div>
                <button
                  onClick={handleNextChar}
                  className="shrink-0 w-full md:w-auto bg-green-500 hover:bg-green-600 text-white px-4 md:px-6 py-2.5 md:py-3 rounded-xl text-sm md:text-xl font-black transition-all hover:scale-105 active:scale-95"
                >
                  Selanjutnya →
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {}
      <div className="shrink-0 px-3 md:px-6 lg:px-10 pb-3 md:pb-4 pt-1">
        <div className="flex items-center justify-between gap-2 md:gap-4">

          {}
          <div className="flex items-center gap-1.5 md:gap-2.5">
            <button
              onClick={handleUndo}
              disabled={strokeHistory.length === 0}
              className="w-12 h-12 md:w-14 md:h-14 lg:w-16 lg:h-16 rounded-xl bg-white shadow-sm border border-slate-100 flex items-center justify-center text-slate-400 hover:text-slate-600 hover:border-slate-200 active:scale-90 disabled:opacity-25 disabled:cursor-not-allowed transition-all"
              title="Urungkan"
            >
              <ArrowCounterClockwise weight="bold" className="text-xl md:text-2xl" />
            </button>

            <button
              onClick={handleClear}
              className={`relative w-12 h-12 md:w-14 md:h-14 lg:w-16 lg:h-16 rounded-xl flex items-center justify-center active:scale-90 transition-all ${
                showClearConfirm
                  ? "bg-red-100 border-2 border-red-400 text-red-500 animate-pulse"
                  : "bg-white shadow-sm border border-slate-100 text-slate-400 hover:text-red-400 hover:bg-red-50"
              }`}
              title={showClearConfirm ? "Klik lagi!" : "Hapus"}
            >
              <Trash weight={showClearConfirm ? "fill" : "bold"} className="text-xl md:text-2xl" />
              {showClearConfirm && (
                <div className="absolute -top-8 md:-top-9 left-1/2 -translate-x-1/2 bg-red-500 text-white text-[10px] md:text-xs font-bold px-2.5 py-1 rounded-lg whitespace-nowrap animate-bounce z-50">
                  Klik lagi!
                </div>
              )}
            </button>

            <div className="w-px h-8 md:h-10 bg-slate-200 mx-0.5 md:mx-1"></div>

            {}
            <div className="hidden sm:flex items-center gap-1.5 md:gap-2">
              {COLORS.map((color) => (
                <button
                  key={color.value}
                  onClick={() => setSelectedColor(color.value)}
                  className={`w-8 h-8 md:w-9 md:h-9 lg:w-10 lg:h-10 rounded-full border-2 border-white shadow-sm transition-all ${
                    selectedColor === color.value
                      ? `ring-2 ${color.ring} scale-110`
                      : "hover:scale-110"
                  }`}
                  style={{ backgroundColor: color.value }}
                  title={color.name}
                />
              ))}
            </div>

            <button
              onClick={() => {
                const idx = COLORS.findIndex((c) => c.value === selectedColor);
                setSelectedColor(COLORS[(idx + 1) % COLORS.length].value);
              }}
              className="sm:hidden w-10 h-10 md:w-11 md:h-11 rounded-full border-2 border-white shadow-md"
              style={{ backgroundColor: selectedColor }}
              title="Ganti warna"
            >
              <PaintBucket weight="bold" className="white text-xs absolute" />
            </button>
          </div>

          {}
          {!isEvaluated ? (
            <button
              onClick={handleEvaluate}
              className="group relative flex items-center gap-2 md:gap-3 bg-gradient-to-r from-green-400 to-emerald-500 text-white pl-6 md:pl-8 pr-8 md:pr-10 py-3.5 md:py-4 lg:py-5 rounded-2xl font-black text-xl md:text-2xl lg:text-3xl shadow-lg shadow-green-300/50 hover:shadow-xl hover:shadow-green-400/60 hover:scale-[1.03] active:scale-95 transition-all cursor-pointer animate-kid-pulse"
            >
              <CheckCircle weight="bold" className="text-2xl md:text-3xl group-hover:animate-bounce" />
              <span>CEK!</span>
            </button>
          ) : stars === 0 ? (
            <button
              onClick={handleRetry}
              className="flex items-center gap-2 md:gap-3 bg-gradient-to-r from-orange-400 to-amber-500 text-white px-6 md:px-8 py-3.5 md:py-4 rounded-2xl font-black text-lg md:text-2xl shadow-lg hover:scale-105 active:scale-95 transition-all"
            >
              <Trash weight="bold" className="text-xl md:text-2xl" />
              Ulangi
            </button>
          ) : (
            <button
              onClick={handleNextChar}
              className="group flex items-center gap-2 md:gap-3 bg-gradient-to-r from-green-400 to-emerald-500 text-white pl-6 md:pl-8 pr-8 md:pr-10 py-3.5 md:py-4 lg:py-5 rounded-2xl font-black text-xl md:text-2xl lg:text-3xl shadow-lg shadow-green-300/50 hover:shadow-xl hover:scale-105 active:scale-95 transition-all"
            >
              <span>Selanjutnya</span>
              <CaretRight weight="bold" className="text-2xl md:text-3xl group-hover:translate-x-1 transition-transform" />
            </button>
          )}

        </div>
      </div>

    </main>
  );
}
