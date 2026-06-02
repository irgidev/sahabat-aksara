import { useState, useEffect } from "react";
import {
  House,
  Star,
  Sparkle,
  Trophy,
  Fire,
  CalendarBlank,
  Student,
  CaretRight,
  PencilLine,
} from "@phosphor-icons/react";
import KidNavBar from "./KidNavBar";
import API_BASE, { apiFetch } from "../lib/api";


function getGreeting() {
  const jam = new Date().getHours();
  if (jam < 11) return "Selamat Pagi";
  if (jam < 15) return "Siang yang Ceria";
  if (jam < 18) return "Selamat Sore";
  return "Selamat Malam";
}


const MOTIVATIONS = [
  "Hari ini lebih hebat dari kemarin! 🚀",
  "Setiap huruf adalah langkah kecil menuju prestasi besar! ✨",
  "Kamu sudah luar biasa, terus semangat! 💪",
  "Belajar itu menyenangkan, ayo mulai! 🎨",
  "Kamu pasti bisa menguasai semua huruf! ⭐",
  "Jangan menyerah, setiap goresan berharga! 📝",
];

export default function BerandaSiswa({ onNavigate, student }) {
  const [stats, setStats] = useState({
    totalLatihan: 0,
    rataAkurasi: 0,
    stars: 0,
    streak: 0,
  });
  const [recentActivity, setRecentActivity] = useState([]);
  const [motivation, setMotivation] = useState("");
  const [loading, setLoading] = useState(true);

  
  useEffect(() => {
    
    setMotivation(MOTIVATIONS[Math.floor(Math.random() * MOTIVATIONS.length)]);

    const fetchData = async () => {
      try {
        const [progressRes, chartRes] = await Promise.all([
          apiFetch(`/api/student/${student?.id || "11111111-1111-1111-1111-111111111111"}/progress`),
          apiFetch('/api/dashboard/chart-data?days=7'),
        ]);

        const progressData = await progressRes.json();
        const chartData = await chartRes.json();

        
        const allProgress = progressData || [];
        const totalLatihan = allProgress.length;
        const totalStars = allProgress.reduce((sum, p) => sum + (p.stars || 0), 0);
        const avgAccuracy =
          totalLatihan > 0
            ? Math.round(
                allProgress.reduce((sum, p) => sum + (p.accuracy || 0), 0) / totalLatihan
              )
            : 0;

        
        let streak = 0;
        if (chartData && chartData.length > 0) {
          
          for (let i = chartData.length - 1; i >= 0; i--) {
            if (chartData[i].count > 0) streak++;
            else break;
          }
          
          if (streak === 0 && chartData[chartData.length - 1]?.count === 0) {
            for (let i = chartData.length - 2; i >= 0; i--) {
              if (chartData[i].count > 0) streak++;
              else break;
            }
          }
        }

        setStats({
          totalLatihan,
          rataAkurasi: avgAccuracy,
          stars: totalStars,
          streak,
        });

        
        setRecentActivity(allProgress.slice(0, 5));
      } catch (err) {
        console.warn("[BerandaSiswa] Fetch error:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [student?.id]);

  
  const quickCategories = [
    { id: "besar", label: "Huruf Besar", emoji: "🔤", lessonId: 1 },
    { id: "kecil", label: "Huruf Kecil", emoji: "✏️", lessonId: 27 },
    { id: "angka", label: "Angka", emoji: "🔢", lessonId: 53 },
  ];

  return (
    <main className="view-section view-active bg-gradient-to-br from-slate-50 via-blue-50/30 to-purple-50/20 flex flex-col h-full overflow-hidden ios-no-bounce">
      {}
      <div className="flex-1 overflow-y-auto no-scrollbar">
        {}
        <header className="flex items-center justify-between px-4 md:px-8 lg:px-12 pt-6 md:pt-8 pb-4">
          <div className="flex items-center gap-3 md:gap-4">
            {}
            <div className="w-14 h-14 md:w-18 md:h-18 lg:w-20 lg:h-20 rounded-full bg-gradient-to-br from-pastel-sky to-purple-400 shadow-lg border-4 border-white flex items-center justify-center overflow-hidden">
              {student?.avatar_url ? (
                <img
                  src={student.avatar_url}
                  alt={student?.nama || "Siswa"}
                  className="w-full h-full object-cover"
                />
              ) : (
                <Student weight="fill" className="text-2xl md:text-3xl text-white" />
              )}
            </div>
            <div>
              <p className="text-slate-400 text-xs md:text-sm font-medium">
                {getGreeting()} ✨
              </p>
              <h1 className="text-xl md:text-2xl lg:text-3xl font-bold text-slate-800 leading-tight">
                Halo, {student?.nama || "Kawan"}! 🎨
              </h1>
            </div>
          </div>
        </header>

        {}
        <div className="px-4 md:px-8 lg:px-12 mb-5">
          <div className="bg-gradient-to-r from-yellow-50 via-amber-50 to-orange-50 rounded-2xl border border-yellow-200 px-5 md:px-6 py-3.5 md:py-4 flex items-center gap-3 shadow-sm">
            <Sparkle weight="fill" className="text-yellow-500 text-2xl md:text-3xl shrink-0" />
            <p className="text-sm md:text-base font-semibold text-amber-800">{motivation}</p>
          </div>
        </div>

        {}
        <div className="px-4 md:px-8 lg:px-12 mb-5">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4">
            {}
            <div className="bg-white rounded-2xl border border-blue-100 p-3 md:p-4 shadow-sm flex flex-col items-center gap-1">
              <PencilLine weight="fill" className="text-blue-500 text-xl md:text-2xl" />
              <span className="text-2xl md:text-3xl font-black text-slate-800">
                {loading ? "..." : stats.totalLatihan}
              </span>
              <span className="text-[10px] md:text-xs text-slate-400 font-medium">Total Latihan</span>
            </div>

            {}
            <div className="bg-white rounded-2xl border border-green-100 p-3 md:p-4 shadow-sm flex flex-col items-center gap-1">
              <Trophy weight="fill" className="text-green-500 text-xl md:text-2xl" />
              <span className="text-2xl md:text-3xl font-black text-slate-800">
                {loading ? "..." : `${stats.rataAkurasi}%`}
              </span>
              <span className="text-[10px] md:text-xs text-slate-400 font-medium">Akurasi</span>
            </div>

            {}
            <div className="bg-white rounded-2xl border border-yellow-100 p-3 md:p-4 shadow-sm flex flex-col items-center gap-1">
              <Star weight="fill" className="text-yellow-500 text-xl md:text-2xl" />
              <span className="text-2xl md:text-3xl font-black text-slate-800">
                {loading ? "..." : stats.stars}
              </span>
              <span className="text-[10px] md:text-xs text-slate-400 font-medium">Total Bintang</span>
            </div>

            {}
            <div className="bg-white rounded-2xl border border-orange-100 p-3 md:p-4 shadow-sm flex flex-col items-center gap-1 col-span-2 md:col-span-1">
              <Fire weight="fill" className="text-orange-500 text-xl md:text-2xl" />
              <span className="text-2xl md:text-3xl font-black text-slate-800">
                {loading ? "..." : stats.streak}
              </span>
              <span className="text-[10px] md:text-xs text-slate-400 font-medium">Hari Berturut</span>
            </div>
          </div>
        </div>

        {}
        <div className="px-4 md:px-8 lg:px-12 mb-5">
          <h2 className="text-base md:text-lg font-bold text-slate-700 mb-3 flex items-center gap-2">
            <PencilLine weight="bold" className="text-emerald-500" />
            Mulai Belajar
          </h2>
          <div className="grid grid-cols-3 gap-3">
            {quickCategories.map((cat) => (
              <button
                key={cat.id}
                onClick={() =>
                  onNavigate("menuSiswa", { initialCategory: cat.id })
                }
                className="group bg-white rounded-2xl border border-slate-100 p-4 flex flex-col items-center gap-2 hover:shadow-lg hover:-translate-y-1 transition-all duration-200 active:scale-[0.98]"
              >
                <span className="text-3xl md:text-4xl group-hover:scale-110 transition-transform">
                  {cat.emoji}
                </span>
                <span className="text-xs md:text-sm font-bold text-slate-600 text-center">
                  {cat.label}
                </span>
                <CaretRight weight="bold" className="text-slate-300 group-hover:text-emerald-500 transition-colors text-sm" />
              </button>
            ))}
          </div>
        </div>

        {}
        <div className="px-4 md:px-8 lg:px-12 pb-8">
          <h2 className="text-base md:text-lg font-bold text-slate-700 mb-3 flex items-center gap-2">
            <CalendarBlank weight="bold" className="text-purple-500" />
            Latihan Terakhir
          </h2>

          {loading ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin w-8 h-8 border-3 border-purple-200 border-t-purple-500 rounded-full" />
            </div>
          ) : recentActivity.length > 0 ? (
            <div className="space-y-2">
              {recentActivity.map((item, idx) => {
                const charTarget = item.char_target || (item.lessons?.char_target) || "?";
                const acc = item.accuracy || 0;
                const s = item.stars || 0;

                return (
                  <div
                    key={idx}
                    className="bg-white rounded-xl border border-slate-100 px-4 py-3 flex items-center justify-between shadow-sm"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-100 to-purple-100 flex items-center justify-center">
                        <span className="text-lg font-bold text-slate-700">{charTarget}</span>
                      </div>
                      <div>
                        <p className="text-sm font-semibold text-slate-700">
                          Huruf {charTarget}
                        </p>
                        <p className="text-xs text-slate-400">
                          Akurasi:{" "}
                          <span className={`font-bold ${acc >= 70 ? "text-green-500" : acc >= 40 ? "text-yellow-500" : "text-orange-500"}`}>
                            {acc}%
                          </span>
                        </p>
                      </div>
                    </div>
                    <div className="flex gap-0.5">
                      {[1, 2, 3].map((star) => (
                        <Star
                          key={star}
                          weight={star <= s ? "fill" : "duotone"}
                          className={`text-base ${star <= s ? "text-yellow-400" : "text-slate-200"}`}
                        />
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="bg-white rounded-2xl border border-dashed border-slate-200 px-6 py-8 text-center">
              <House weight="duotone" className="text-4xl text-slate-200 mx-auto mb-2" />
              <p className="text-sm text-slate-400 font-medium">
                Belum ada latihan nih. Ayo mulai belajar! 🎯
              </p>
              <button
                onClick={() => onNavigate("menuSiswa")}
                className="mt-3 bg-emerald-500 text-white px-5 py-2 rounded-xl text-sm font-bold hover:bg-emerald-600 transition-colors"
              >
                Mulai Latihan →
              </button>
            </div>
          )}
        </div>
      </div>

      {}
      <KidNavBar activePage="home" onNavigate={onNavigate} student={student} />
    </main>
  );
}
