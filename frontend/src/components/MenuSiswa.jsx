import { useState, useEffect } from "react";
import API_BASE from "../lib/api";
import {
  PencilCircle,
  SignOut,
  Student,
  CaretRight,
  Star,
  Sparkle,
  NumberCircleOne,
  TextB,
  TextAa,
  House,
  Trophy,
  ArrowLeft,
} from "@phosphor-icons/react";
import KidNavBar from "./KidNavBar";


const CATEGORIES = [
  {
    id: "besar",
    title: "Huruf Besar",
    subtitle: "A sampai Z",
    icon: TextB,
    color: "from-pastel-sky to-blue-400",
    bgColor: "bg-blue-50",
    borderColor: "border-blue-200",
    textColor: "text-blue-600",
    charRange: Array.from({ length: 26 }, (_, i) => ({
      char: String.fromCharCode(65 + i),
      label: `Huruf ${String.fromCharCode(65 + i)}`,
      lessonId: i + 1,
    })),
  },
  {
    id: "kecil",
    title: "Huruf Kecil",
    subtitle: "a sampai z",
    icon: TextAa,
    color: "from-pastel-mint to-emerald-400",
    bgColor: "bg-emerald-50",
    borderColor: "border-emerald-200",
    textColor: "text-emerald-600",
    charRange: Array.from({ length: 26 }, (_, i) => ({
      char: String.fromCharCode(97 + i),
      label: `Huruf ${String.fromCharCode(97 + i)}`,
      lessonId: 27 + i,
    })),
  },
  {
    id: "angka",
    title: "Angka",
    subtitle: "0 sampai 9",
    icon: NumberCircleOne,
    color: "from-pastel-peach to-orange-400",
    bgColor: "bg-orange-50",
    borderColor: "border-orange-200",
    textColor: "text-orange-600",
    charRange: Array.from({ length: 10 }, (_, i) => ({
      char: String(i),
      label: `Angka ${i}`,
      lessonId: 53 + i,
    })),
  },
];


function getGreeting() {
  const jam = new Date().getHours();
  if (jam < 11) return "Selamat Pagi";
  if (jam < 15) return "Siang yang Ceria";
  if (jam < 18) return "Selamat Sore";
  return "Selamat Malam";
}

export default function MenuSiswa({ onNavigate, student, initialCategory }) {
  const [view, setView] = useState("main"); 
  const [selectedCategory, setSelectedCategory] = useState(null);

  
  useEffect(() => {
    if (initialCategory) {
      const cat = CATEGORIES.find((c) => c.id === initialCategory);
      if (cat) {
        setSelectedCategory(cat);
        setView("characters");
      }
    }
  }, [initialCategory]);
  const [progressMap, setProgressMap] = useState({});

  
  useEffect(() => {
    if (student?.id) {
      fetch(`${API_BASE}/api/student/${student.id}/progress`)
        .then((res) => res.json())
        .then((data) => {
          const map = {};
          (data || []).forEach((p) => {
            const lid = p.lesson_id;
            if (!map[lid] || p.stars > map[lid]) {
              map[lid] = p.stars;
            }
          });
          setProgressMap(map);
        })
        .catch(() => {});
    }
  }, [student?.id]);

  const handleCategoryClick = (cat) => {
    setSelectedCategory(cat);
    setView("characters");
  };

  const handleCharSelect = (charInfo) => {
    onNavigate("canvas", { lesson: charInfo });
  };

  const handleBackToCategories = () => {
    setView("category");
    setSelectedCategory(null);
  };

  const handleBackToMain = () => {
    setView("main");
    setSelectedCategory(null);
  };

  const handleLogout = () => {
    if (onNavigate) onNavigate("home");
  };

  
  const renderStars = (lessonId) => {
    const stars = progressMap[lessonId] || 0;
    return (
      <div className="flex gap-0.5">
        {[1, 2, 3].map((s) => (
          <Star
            key={s}
            weight={s <= stars ? "fill" : "duotone"}
            className={`text-sm md:text-base ${
              s <= stars ? "text-yellow-400" : "text-slate-200"
            }`}
          />
        ))}
      </div>
    );
  };

  
  if (view === "main") {
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

            {}
            <button
              onClick={handleLogout}
              className="w-11 h-11 md:w-13 md:h-13 rounded-full glass-panel flex items-center justify-center text-slate-400 hover:text-red-400 hover:bg-red-50 active:scale-95 transition-all"
              title="Keluar"
            >
              <SignOut weight="bold" className="text-lg md:text-xl" />
            </button>
          </header>

          {}
          <div className="px-4 md:px-8 lg:px-12 mb-4 md:mb-6">
            <div className="glass-panel rounded-2xl px-4 md:px-6 py-2.5 md:py-3 inline-flex items-center gap-2">
              <Sparkle weight="fill" className="text-pastel-yellow text-base md:text-lg" />
              <span className="text-slate-600 font-medium text-sm md:text-base">
                Apa yang ingin kamu pelajari hari ini?
              </span>
              <Sparkle weight="fill" className="text-pastel-sky text-base md:text-lg" />
            </div>
          </div>

          {}
          <div className="px-4 md:px-8 lg:px-12 pb-8">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 md:gap-6 max-w-4xl lg:max-w-5xl mx-auto">
              {CATEGORIES.map((cat) => {
                const Icon = cat.icon;
                const completed = cat.charRange.filter(
                  (c) => (progressMap[c.lessonId] || 0) > 0
                ).length;
                const total = cat.charRange.length;

                return (
                  <button
                    key={cat.id}
                    onClick={() => handleCategoryClick(cat)}
                    className={`group relative ${cat.bgColor} rounded-2xl md:rounded-3xl border-2 ${cat.borderColor} p-5 md:p-8 flex flex-col items-center gap-3 md:gap-4 hover:shadow-xl hover:-translate-y-2 transition-all duration-300 cursor-pointer active:scale-[0.98]`}
                  >
                    {}
                    <div
                      className={`w-16 h-16 md:w-22 md:h-22 lg:w-24 lg:h-24 rounded-2xl bg-gradient-to-br ${cat.color} shadow-lg flex items-center justify-center group-hover:scale-110 group-hover:rotate-3 transition-all duration-300`}
                    >
                      <Icon weight="fill" className="text-3xl md:text-4xl lg:text-5xl text-white" />
                    </div>

                    {}
                    <h2 className={`text-lg md:text-xl lg:text-2xl font-bold ${cat.textColor}`}>
                      {cat.title}
                    </h2>
                    <p className="text-slate-400 text-sm">{cat.subtitle}</p>

                    {}
                    <div className="w-full mt-1">
                      <div className="flex justify-between text-xs text-slate-400 mb-1">
                        <span>Progress</span>
                        <span className="font-semibold">{completed}/{total}</span>
                      </div>
                      <div className="w-full h-2 md:h-2.5 bg-white/60 rounded-full overflow-hidden">
                        <div
                          className={`h-full bg-gradient-to-r ${cat.color} rounded-full transition-all duration-500`}
                          style={{ width: `${(completed / total) * 100}%` }}
                        />
                      </div>
                    </div>

                    {}
                    <div
                      className={`absolute bottom-3 md:bottom-4 right-3 md:right-4 w-7 h-7 md:w-9 md:h-9 rounded-full ${cat.bgColor} border ${cat.borderColor} flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all`}
                    >
                      <CaretRight
                        weight="bold"
                        className={`text-xs md:text-sm ${cat.textColor}`}
                      />
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {}
        <KidNavBar activePage="menu" onNavigate={onNavigate} student={student} />
      </main>
    );
  }

  
  if (view === "characters" && selectedCategory) {
    const cat = selectedCategory;
    const Icon = cat.icon;

    return (
      <main className="view-section view-active bg-gradient-to-br from-slate-50 via-blue-50/30 to-purple-50/20 flex flex-col h-full overflow-hidden ios-no-bounce">
        {}
        <div className="flex-1 overflow-y-auto no-scrollbar">
          {}
          <header className="flex items-center justify-between px-4 md:px-8 lg:px-12 pt-6 md:pt-8 pb-3 md:pb-4">
            <div className="flex items-center gap-2 md:gap-3">
              <button
                onClick={handleBackToMain}
                className="w-10 h-10 md:w-12 md:h-12 rounded-full glass-panel flex items-center justify-center text-slate-500 hover:text-slate-700 hover:bg-white active:scale-95 transition-all"
              >
                <ArrowLeft weight="bold" className="text-lg md:text-xl" />
              </button>
              <div
                className={`w-10 h-10 md:w-12 md:h-12 rounded-xl bg-gradient-to-br ${cat.color} flex items-center justify-center shadow-md`}
              >
                <Icon weight="fill" className="text-xl md:text-2xl text-white" />
              </div>
              <div>
                <h1 className="text-lg md:text-xl lg:text-2xl font-bold text-slate-800">
                  {cat.title}
                </h1>
                <p className="text-slate-400 text-xs md:text-sm">Pilih huruf yang ingin dilatih</p>
              </div>
            </div>

            {}
            <div className="w-9 h-9 md:w-11 md:h-11 rounded-full bg-gradient-to-br from-pastel-sky to-purple-400 border-2 border-white flex items-center justify-center overflow-hidden">
              {student?.avatar_url ? (
                <img
                  src={student.avatar_url}
                  alt={student?.nama}
                  className="w-full h-full object-cover"
                />
              ) : (
                <Student weight="fill" className="text-base md:text-lg text-white" />
              )}
            </div>
          </header>

          {}
          <div className="px-4 md:px-8 lg:px-12 pb-8">
            <div className="grid grid-cols-5 sm:grid-cols-6 md:grid-cols-7 lg:grid-cols-9 gap-2 md:gap-3 max-w-4xl lg:max-w-5xl mx-auto">
              {cat.charRange.map((charInfo) => {
                const stars = progressMap[charInfo.lessonId] || 0;
                const hasAttempted = stars > 0;

                return (
                  <button
                    key={charInfo.char}
                    onClick={() => handleCharSelect(charInfo)}
                    className={`group relative aspect-square rounded-xl md:rounded-2xl border-2 ${
                      hasAttempted
                        ? `${cat.borderColor} ${cat.bgColor}`
                        : "border-slate-200 bg-white hover:border-slate-300"
                    } flex flex-col items-center justify-center gap-0.5 md:gap-1 hover:shadow-lg hover:-translate-y-1 transition-all duration-200 cursor-pointer active:scale-95`}
                  >
                    {}
                    <span
                      className={`text-2xl md:text-3xl lg:text-4xl font-bold ${
                        hasAttempted ? cat.textColor : "text-slate-400"
                      } group-hover:${cat.textColor} transition-colors`}
                    >
                      {charInfo.char}
                    </span>

                    {}
                    <div className="flex gap-px">
                      {[1, 2, 3].map((s) => (
                        <Star
                          key={s}
                          weight={s <= stars ? "fill" : "duotone"}
                          className={`text-[10px] md:text-xs ${
                            s <= stars ? "text-yellow-400" : "text-slate-200"
                          }`}
                        />
                      ))}
                    </div>

                    {}
                    <div
                      className={`absolute -bottom-0.5 left-1/2 -translate-x-1/2 w-6 h-1 md:w-8 md:h-1.5 rounded-full bg-gradient-to-r ${cat.color} opacity-0 group-hover:opacity-100 transition-opacity`}
                    />
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {}
        <div className="shrink-0 px-4 md:px-8 lg:px-12 py-3 md:py-4">
          <div className="glass-panel rounded-2xl px-4 md:px-6 py-2.5 md:py-3 flex items-center justify-between max-w-4xl lg:max-w-5xl mx-auto">
            <div className="flex items-center gap-2">
              <Trophy
                weight="fill"
                className="text-pastel-yellow text-base md:text-lg"
              />
              <span className="text-xs md:text-sm text-slate-600">
                <strong className={cat.textColor}>
                  {
                    cat.charRange.filter(
                      (c) => (progressMap[c.lessonId] || 0) >= 3
                    ).length
                  }
                </strong>{" "}
                dari {cat.charRange.length} sudah sempurna! ⭐⭐⭐
              </span>
            </div>
          </div>
        </div>

        {}
        <KidNavBar activePage="menu" onNavigate={onNavigate} student={student} />
      </main>
    );
  }

  return null;
}
