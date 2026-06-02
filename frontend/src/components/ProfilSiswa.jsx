import { useState, useEffect } from "react";
import API_BASE from "../lib/api";
import {
  UserCircle,
  Star,
  Trophy,
  Student,
  GraduationCap,
  BookOpen,
  Target,
  CheckCircle,
  Circle,
  SignOut,
  Camera,
  PencilSimple,
} from "@phosphor-icons/react";
import KidNavBar from "./KidNavBar";

export default function ProfilSiswa({ onNavigate, student }) {
  const [stats, setStats] = useState({
    totalLatihan: 0,
    avgAccuracy: 0,
    totalStars: 0,
    perfectLessons: 0,
    totalLessons: 63, 
  });
  const [lessonProgress, setLessonProgress] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingName, setEditingName] = useState(false);
  const [tempName, setTempName] = useState("");

  
  useEffect(() => {
    if (student?.id) {
      fetch(`${API_BASE}/api/student/${student.id}/progress`)
        .then((res) => res.json())
        .then((data) => {
          const allProgress = data || [];
          const totalLatihan = allProgress.length;
          const totalStars = allProgress.reduce((sum, p) => sum + (p.stars || 0), 0);
          const avgAccuracy =
            totalLatihan > 0
              ? Math.round(
                  allProgress.reduce((sum, p) => sum + (p.accuracy || 0), 0) / totalLatihan
                )
              : 0;

          
          const lessonBest = {};
          allProgress.forEach((p) => {
            const lid = p.lesson_id;
            if (!lessonBest[lid] || p.stars > lessonBest[lid]) {
              lessonBest[lid] = p.stars;
            }
          });
          const perfectCount = Object.values(lessonBest).filter((s) => s >= 3).length;

          setStats((prev) => ({
            ...prev,
            totalLatihan,
            avgAccuracy,
            totalStars,
            perfectLessons: perfectCount,
          }));

          
          const categories = [
            { id: "besar", label: "Huruf Besar", startId: 1, endId: 26 },
            { id: "kecil", label: "Huruf Kecil", startId: 27, endId: 52 },
            { id: "angka", label: "Angka", startId: 53, endId: 62 },
          ];

          const grouped = categories.map((cat) => {
            const lessons = [];
            for (let i = cat.startId; i <= cat.endId; i++) {
              let charLabel;
              if (cat.id === "besar") charLabel = String.fromCharCode(65 + (i - 1));
              else if (cat.id === "kecil") charLabel = String.fromCharCode(97 + (i - 27));
              else charLabel = String(i - 53);

              lessons.push({
                lessonId: i,
                char: charLabel,
                bestStars: lessonBest[i] || 0,
              });
            }
            return { ...cat, lessons };
          });

          setLessonProgress(grouped);
        })
        .catch(() => {})
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, [student?.id]);

  
  const progressPct =
    stats.totalLessons > 0
      ? Math.round(
          (lessonProgress.reduce(
            (sum, cat) =>
              sum + cat.lessons.filter((l) => l.bestStars > 0).length,
            0
          ) /
            stats.totalLessons) *
            100
        )
      : 0;

  return (
    <main className="view-section view-active bg-gradient-to-br from-slate-50 via-purple-50/20 to-blue-50/30 flex flex-col h-full overflow-hidden ios-no-bounce">
      {}
      <div className="flex-1 overflow-y-auto no-scrollbar">
        {}
        <div className="bg-gradient-to-br from-purple-500 via-violet-500 to-indigo-600 px-4 md:px-8 lg:px-12 pt-6 md:pt-8 pb-8 rounded-b-[2rem]">
          <div className="flex items-center gap-4 md:gap-5">
            {}
            <div className="relative">
              <div className="w-20 h-20 md:w-24 md:h-24 lg:w-28 lg:h-28 rounded-full bg-white/20 backdrop-blur-sm border-4 border-white/40 flex items-center justify-center overflow-hidden shadow-xl">
                {student?.avatar_url ? (
                  <img
                    src={student.avatar_url}
                    alt={student?.nama || "Siswa"}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <Student weight="fill" className="text-4xl md:text-5xl text-white" />
                )}
              </div>
              {}
              <button className="absolute bottom-0 right-0 w-7 h-7 md:w-8 md:h-8 bg-white rounded-full shadow-lg flex items-center justify-center text-purple-500 hover:bg-purple-50 active:scale-90 transition-all">
                <Camera weight="bold" className="text-xs md:text-sm" />
              </button>
            </div>

            {}
            <div className="flex-1 min-w-0">
              {editingName ? (
                <div className="flex items-center gap-2 mb-1">
                  <input
                    type="text"
                    value={tempName}
                    onChange={(e) => setTempName(e.target.value)}
                    className="px-2 py-1 rounded-lg text-base md:text-lg font-bold text-slate-800 bg-white/95 border-0 outline-none w-full max-w-[200px]"
                    autoFocus
                    onKeyDown={(e) => {
                      if (e.key === "Enter") setEditingName(false);
                      if (e.key === "Escape") {
                        setTempName(student?.nama || "");
                        setEditingName(false);
                      }
                    }}
                    onBlur={() => setEditingName(false)}
                  />
                </div>
              ) : (
                <h1
                  onClick={() => {
                    setTempName(student?.nama || "");
                    setEditingName(true);
                  }}
                  className="text-xl md:text-2xl lg:text-3xl font-bold text-white leading-tight cursor-pointer hover:text-yellow-200 transition-colors flex items-center gap-2"
                >
                  {student?.nama || "Kawan"}
                  <PencilSimple weight="bold" className="text-sm text-white/60" />
                </h1>
              )}

              <div className="flex flex-wrap items-center gap-2 mt-1.5">
                {student?.kelas && (
                  <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-white/20 text-white/90 text-xs font-medium backdrop-blur-sm">
                    <GraduationCap weight="fill" className="text-[10px]" />
                    {student.kelas}
                  </span>
                )}
                {student?.nis && (
                  <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-white/20 text-white/90 text-xs font-medium backdrop-blur-sm">
                    NIS: {student.nis}
                  </span>
                )}
              </div>

              {}
              <div className="mt-3">
                <div className="flex justify-between text-xs text-white/70 mb-1">
                  <span>Progres Belajar</span>
                  <span className="font-bold">{progressPct}%</span>
                </div>
                <div className="w-full h-2.5 bg-white/20 rounded-full overflow-hidden backdrop-blur-sm">
                  <div
                    className="h-full bg-gradient-to-r from-yellow-300 to-amber-400 rounded-full transition-all duration-700"
                    style={{ width: `${progressPct}%` }}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        {}
        <div className="px-4 md:px-8 lg:px-12 -mt-4 mb-5">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="bg-white rounded-2xl p-3 md:p-4 shadow-md border border-slate-100 flex flex-col items-center gap-1">
              <BookOpen weight="fill" className="text-blue-500 text-xl md:text-2xl" />
              <span className="text-2xl md:text-3xl font-black text-slate-800">
                {loading ? "..." : stats.totalLatihan}
              </span>
              <span className="text-[10px] md:text-xs text-slate-400 font-medium">Latihan</span>
            </div>

            <div className="bg-white rounded-2xl p-3 md:p-4 shadow-md border border-slate-100 flex flex-col items-center gap-1">
              <Target weight="fill" className="text-green-500 text-xl md:text-2xl" />
              <span className="text-2xl md:text-3xl font-black text-slate-800">
                {loading ? "..." : `${stats.avgAccuracy}%`}
              </span>
              <span className="text-[10px] md:text-xs text-slate-400 font-medium">Akurasi Rata</span>
            </div>

            <div className="bg-white rounded-2xl p-3 md:p-4 shadow-md border border-slate-100 flex flex-col items-center gap-1">
              <Star weight="fill" className="text-yellow-500 text-xl md:text-2xl" />
              <span className="text-2xl md:text-3xl font-black text-slate-800">
                {loading ? "..." : stats.totalStars}
              </span>
              <span className="text-[10px] md:text-xs text-slate-400 font-medium">Bintang</span>
            </div>

            <div className="bg-white rounded-2xl p-3 md:p-4 shadow-md border border-slate-100 flex flex-col items-center gap-1">
              <Trophy weight="fill" className="text-amber-500 text-xl md:text-2xl" />
              <span className="text-2xl md:text-3xl font-black text-slate-800">
                {loading ? "..." : stats.perfectLessons}
              </span>
              <span className="text-[10px] md:text-xs text-slate-400 font-medium">Sempurna ⭐⭐⭐</span>
            </div>
          </div>
        </div>

        {}
        <div className="px-4 md:px-8 lg:px-12 pb-8">
          <h2 className="text-base md:text-lg font-bold text-slate-700 mb-3 flex items-center gap-2">
            <Trophy weight="bold" className="text-amber-500" />
            Progres Per Karakter
          </h2>

          {loading ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin w-8 h-8 border-3 border-purple-200 border-t-purple-500 rounded-full" />
            </div>
          ) : (
            <div className="space-y-4">
              {lessonProgress.map((cat) => {
                const completed = cat.lessons.filter((l) => l.bestStars > 0).length;
                const perfect = cat.lessons.filter((l) => l.bestStars >= 3).length;
                const pct = Math.round((completed / cat.lessons.length) * 100);

                return (
                  <div key={cat.id} className="bg-white rounded-2xl border border-slate-100 p-4 shadow-sm">
                    {}
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="font-bold text-slate-700 text-sm md:text-base">
                        {cat.label}
                      </h3>
                      <span className="text-xs text-slate-400 font-medium">
                        {completed}/{cat.lessons.length} ({pct}%)
                      </span>
                    </div>

                    {}
                    <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden mb-3">
                      <div
                        className={`h-full rounded-full transition-all duration-500 ${
                          cat.id === "besar"
                            ? "bg-gradient-to-r from-blue-400 to-blue-500"
                            : cat.id === "kecil"
                            ? "bg-gradient-to-r from-emerald-400 to-emerald-500"
                            : "bg-gradient-to-r from-orange-400 to-orange-500"
                        }`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>

                    {}
                    <div className="flex flex-wrap gap-1.5">
                      {cat.lessons.map((l) => (
                        <div
                          key={l.lessonId}
                          className={`w-8 h-8 md:w-9 md:h-9 rounded-lg flex items-center justify-center text-sm md:text-base font-bold transition-colors ${
                            l.bestStars >= 3
                              ? "bg-yellow-100 text-yellow-700 border border-yellow-300"
                              : l.bestStars > 0
                              ? "bg-blue-50 text-blue-600 border border-blue-200"
                              : "bg-slate-50 text-slate-300 border border-slate-200"
                          }`}
                          title={`${l.char}: ${l.bestStars}/3 bintang`}
                        >
                          {l.char}
                          {l.bestStars > 0 && (
                            <Star
                              weight="fill"
                              className={`absolute text-[6px] ${
                                l.bestStars >= 3 ? "text-yellow-500" : "text-blue-400"
                              }`}
                              style={{
                                position: "absolute",
                                top: "-2px",
                                right: "-2px",
                                fontSize: "6px",
                              }}
                            />
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {}
          <div className="mt-6 pt-4 border-t border-slate-100">
            <button
              onClick={() => onNavigate("home")}
              className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-red-50 hover:bg-red-100 text-red-500 font-semibold text-sm md:text-base transition-colors active:scale-[0.98]"
            >
              <SignOut weight="bold" className="text-lg" />
              Keluar dari Akun
            </button>
          </div>
        </div>
      </div>

      {}
      <KidNavBar activePage="profile" onNavigate={onNavigate} student={student} />
    </main>
  );
}
