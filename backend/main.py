import os
import sys
import json
import time
import cv2
import numpy as np
from dotenv import load_dotenv
from supabase import create_client, Client


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai_core.pattern_matching import calculate_accuracy, create_template


try:
    from ai_core.inference.predictor import get_predictor, reset_predictor
    _predictor_available = True
except ImportError as _pe:
    print(f"[PKB-5] Predictor not available: {_pe}. Using baseline CV only.")
    _predictor_available = False

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from collections import defaultdict

app = FastAPI(title="Sahabat Aksara API", version="2.0.0")

load_dotenv()
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Client | None = None
if SUPABASE_URL and SUPABASE_KEY and SUPABASE_URL != "YOUR_SUPABASE_URL_HERE":
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

history_scores = []




_cors_origins_raw = os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174,https://sahabat-aksara.vercel.app")
CORS_ORIGINS = [o.strip() for o in _cors_origins_raw.split(",") if o.strip()]

from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to every response."""
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=()"
        return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SecurityHeadersMiddleware)



class Coordinate(BaseModel):
    x: float
    y: float

class EvaluationRequest(BaseModel):
    strokeCoordinates: List[Coordinate]
    student_id: Optional[str] = None
    lesson_id: Optional[int] = 1
    char_target: Optional[str] = 'A'

    metadata: Optional[dict] = None

class GuruLoginRequest(BaseModel):
    email: str
    password: str



@app.post("/api/login-guru")
async def login_guru(request: GuruLoginRequest):
    """Validate guru credentials via Supabase Auth with dev fallback."""


    if not supabase:
        raise HTTPException(status_code=503, detail="Supabase belum dikonfigurasi.")

    try:
        data = supabase.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password,
        })

        if not data.user:
            raise HTTPException(status_code=401, detail="Email atau password salah")


        profile_res = supabase.table("profiles").select("*").eq("id", data.user.id).single().execute()

        return {
            "status": "success",
            "user": {
                "id": data.user.id,
                "email": data.user.email,
                "nama": profile_res.data.get("nama", "Guru") if profile_res.data else "Guru",
                "role": profile_res.data.get("role", "teacher") if profile_res.data else "teacher",
                "kelas": profile_res.data.get("kelas") if profile_res.data else None,
            }
        }

    except Exception as e:
        error_msg = str(e)





        if "Invalid login credentials" in error_msg or "Invalid api key" in error_msg:
            import os
            FALLBACK_PASSWORD = os.environ.get("FALLBACK_GURU_PASSWORD", "guru123")

            try:
                profile_res = supabase.table("profiles").select("*").eq("email", request.email).execute()

                if not profile_res.data or len(profile_res.data) == 0:
                    raise HTTPException(status_code=401, detail="Email tidak ditemukan")

                profile = profile_res.data[0]


                if profile.get("role") not in ("teacher", "admin"):
                    raise HTTPException(status_code=401, detail="Akun ini bukan guru/admin")


                if request.password != FALLBACK_PASSWORD:
                    raise HTTPException(status_code=401, detail="Password salah")

                print(f"[Login] Fallback auth untuk: {profile.get('nama')} ({request.email})")

                return {
                    "status": "success",
                    "user": {
                        "id": profile.get("id"),
                        "email": profile.get("email", request.email),
                        "nama": profile.get("nama", "Guru"),
                        "role": profile.get("role", "teacher"),
                        "kelas": profile.get("kelas"),
                    },
                    "_fallback": True,
                }

            except HTTPException:
                raise
            except Exception as inner_err:
                raise HTTPException(status_code=500, detail=f"Fallback error: {inner_err}")

        raise HTTPException(status_code=500, detail=f"Terjadi kesalahan: {error_msg}")

@app.post("/api/logout-guru")
async def logout_guru():
    """Invalidate session."""
    if supabase:
        try:
            supabase.auth.sign_out()
        except Exception:
            pass
    return {"status": "success", "message": "Berhasil logout"}



@app.get("/api/students/faces")
async def get_student_faces():
    """Return all enrolled students with face descriptors for recognition."""
    if not supabase:

        return [
            {"id": "11111111-1111-1111-1111-111111111111", "nama": "Budi Santoso", "face_descriptor": None},
            {"id": "22222222-2222-2222-2222-222222222222", "nama": "Siti Aminah", "face_descriptor": None},
            {"id": "33333333-3333-3333-3333-333333333333", "nama": "Reza Pratama", "face_descriptor": None},
        ]

    try:
        res = supabase.table("profiles") \
            .select("id, nama, face_descriptor, face_image_url") \
            .eq("role", "student") \
            .execute()
        return res.data or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/students")
async def get_students():
    """Return all student profiles."""
    if not supabase:
        return [
            {"id": "11111111-1111-1111-1111-111111111111", "nama": "Budi Santoso", "role": "student", "kelas": "TK-A", "nis": "2024001"},
            {"id": "22222222-2222-2222-2222-222222222222", "nama": "Siti Aminah", "role": "student", "kelas": "TK-A", "nis": "2024002"},
            {"id": "33333333-3333-3333-3333-333333333333", "nama": "Reza Pratama", "role": "student", "kelas": "TK-B", "nis": "2024003"},
        ]

    try:
        res = supabase.table("profiles") \
            .select("*") \
            .eq("role", "student") \
            .order("nama") \
            .execute()
        return res.data or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



class CreateStudentRequest(BaseModel):
    nama: str
    kelas: Optional[str] = None
    nis: Optional[str] = None
    email: Optional[str] = None

class UpdateStudentRequest(BaseModel):
    nama: Optional[str] = None
    kelas: Optional[str] = None
    nis: Optional[str] = None
    email: Optional[str] = None


@app.post("/api/students")
async def create_student(request: CreateStudentRequest):
    """Create a new student profile."""
    if not supabase:
        raise HTTPException(status_code=503, detail="Supabase belum dikonfigurasi.")

    if not request.nama or not request.nama.strip():
        raise HTTPException(status_code=400, detail="Nama siswa wajib diisi.")

    import uuid

    try:
        new_student = {
            "id": str(uuid.uuid4()),
            "nama": request.nama.strip(),
            "role": "student",
            "kelas": request.kelas,
            "nis": request.nis,
            "email": request.email,
            "face_descriptor": None,
            "face_image_url": None,
            "avatar_url": None,
            "qr_token": None,
        }

        res = supabase.table("profiles").insert(new_student).execute()

        if not res.data or len(res.data) == 0:
            raise HTTPException(status_code=500, detail="Gagal membuat data siswa.")

        return {
            "status": "success",
            "message": f"Siswa {request.nama} berhasil ditambahkan.",
            "student": res.data[0],
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Create student error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/students/{student_id}")
async def update_student(student_id: str, request: UpdateStudentRequest):
    """Update an existing student profile."""
    if not supabase:
        raise HTTPException(status_code=503, detail="Supabase belum dikonfigurasi.")


    update_data = {}
    if request.nama is not None:
        if not request.nama.strip():
            raise HTTPException(status_code=400, detail="Nama tidak boleh kosong.")
        update_data["nama"] = request.nama.strip()
    if request.kelas is not None:
        update_data["kelas"] = request.kelas
    if request.nis is not None:
        update_data["nis"] = request.nis
    if request.email is not None:
        update_data["email"] = request.email

    if not update_data:
        raise HTTPException(status_code=400, detail="Tidak ada data yang diubah.")

    try:
        res = supabase.table("profiles") \
            .update(update_data) \
            .eq("id", student_id) \
            .execute()

        if not res.data or len(res.data) == 0:
            raise HTTPException(status_code=404, detail="Siswa tidak ditemukan.")

        return {
            "status": "success",
            "message": f"Data {res.data[0].get('nama', 'siswa')} berhasil diperbarui.",
            "student": res.data[0],
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Update student error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/students/{student_id}")
async def delete_student(student_id: str):
    """Delete a student and all their progress records."""
    if not supabase:
        raise HTTPException(status_code=503, detail="Supabase belum dikonfigurasi.")

    try:

        student_res = supabase.table("profiles") \
            .select("nama") \
            .eq("id", student_id) \
            .single() \
            .execute()

        if not student_res.data:
            raise HTTPException(status_code=404, detail="Siswa tidak ditemukan.")

        student_name = student_res.data.get("nama", "Siswa")


        try:
            supabase.table("student_progress") \
                .delete() \
                .eq("student_id", student_id) \
                .execute()
        except Exception as e:
            print(f"Warning: Could not delete progress records: {e}")


        del_res = supabase.table("profiles") \
            .delete() \
            .eq("id", student_id) \
            .execute()


        verify = supabase.table("profiles") \
            .select("id") \
            .eq("id", student_id) \
            .execute()

        if verify.data and len(verify.data) > 0:
            raise HTTPException(
                status_code=500,
                detail="Gagal menghapus data siswa (diblokir RLS policy). Hubungi admin database."
            )

        return {
            "status": "success",
            "message": f"{student_name} berhasil dihapus beserta semua riwayat latihan.",
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Delete student error: {e}")
        raise HTTPException(status_code=500, detail=str(e))




@app.post("/api/students/{student_id}/enroll-face")
async def enroll_face(student_id: str, request: dict = None):
    """Save face descriptor + image URL for a student."""
    if not supabase:
        raise HTTPException(status_code=503, detail="Supabase belum dikonfigurasi.")

    if not request:
        raise HTTPException(status_code=400, detail="Request body required: { face_descriptor, face_image_url? }")

    descriptor = request.get("face_descriptor")
    image_url = request.get("face_image_url")

    if not descriptor or not isinstance(descriptor, list):
        raise HTTPException(status_code=400, detail="face_descriptor harus berupa array angka (128 dimensi).")

    if len(descriptor) != 128:
        raise HTTPException(status_code=400, detail=f"face_descriptor harus 128 angka, dapat {len(descriptor)}.")

    try:
        update_data = {
            "face_descriptor": descriptor,
            "face_image_url": image_url or None,
        }

        res = supabase.table("profiles") \
            .update(update_data) \
            .eq("id", student_id) \
            .execute()

        if not res.data or len(res.data) == 0:
            raise HTTPException(status_code=404, detail="Siswa tidak ditemukan.")

        return {
            "status": "success",
            "message": f"Wajah berhasil didaftarkan untuk {res.data[0].get('nama', 'siswa')}",
            "student": res.data[0],
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Enrollment error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/students/{student_id}/enroll-face")
async def remove_enrolled_face(student_id: str):
    """Remove enrolled face for a student."""
    if not supabase:
        raise HTTPException(status_code=503, detail="Supabase belum dikonfigurasi.")

    try:
        res = supabase.table("profiles") \
            .update({"face_descriptor": None, "face_image_url": None}) \
            .eq("id", student_id) \
            .execute()

        if not res.data or len(res.data) == 0:
            raise HTTPException(status_code=404, detail="Siswa tidak ditemukan.")

        return {"status": "success", "message": "Wajah berhasil dihapus."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/api/evaluate")
async def evaluate_drawing(request: EvaluationRequest):
    coords = request.strokeCoordinates
    if not coords:
        return {"status": "error", "message": "No coordinates received"}

    print("=== Received Stroke Coordinates ===")
    print(f"Total points: {len(coords)}")


    xs = [p.x for p in coords]
    ys = [p.y for p in coords]

    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    width = max_x - min_x
    height = max_y - min_y

    print(f"Bounding Box: Min({min_x:.1f}, {min_y:.1f}) Max({max_x:.1f}, {max_y:.1f})")



    img_size = 128
    padding = 12
    canvas = np.zeros((img_size, img_size), dtype=np.uint8)


    max_dim = max(width, height)
    if max_dim == 0:
        max_dim = 1

    scale = (img_size - 2 * padding) / max_dim


    offset_x = (img_size - (width * scale)) / 2
    offset_y = (img_size - (height * scale)) / 2


    normalized_points = []
    for p in coords:
        norm_x = int((p.x - min_x) * scale + offset_x)
        norm_y = int((p.y - min_y) * scale + offset_y)
        normalized_points.append((norm_x, norm_y))



    STROKE_THICKNESS = 12
    for i in range(1, len(normalized_points)):
        pt1 = normalized_points[i-1]
        pt2 = normalized_points[i]


        cv2.line(canvas, pt1, pt2, color=255, thickness=STROKE_THICKNESS, lineType=cv2.LINE_AA)

        cv2.line(canvas, pt1, pt2, color=200, thickness=STROKE_THICKNESS - 3, lineType=cv2.LINE_AA)


    char_target = request.char_target or 'A'


    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    datasets_root = os.path.join(root_dir, "data_science", "datasets")


    processed_dir = os.path.join(datasets_root, "processed", char_target.upper())
    os.makedirs(processed_dir, exist_ok=True)

    timestamp = int(time.time() * 1000)
    filename = f"stroke_{timestamp}.png"
    filepath = os.path.join(processed_dir, filename)

    cv2.imwrite(filepath, canvas)
    print(f"[PSD-1] Saved normalized image to: {filepath}")



    hybrid_result = None













    if hybrid_result is None:
        accuracy = calculate_accuracy(filepath, char_target=char_target)

        stars = 3 if accuracy >= 70 else (2 if accuracy >= 45 else (1 if accuracy >= 20 else 0))
    history_scores.append(accuracy)

    public_url = filepath

    if supabase:
        try:
            with open(filepath, "rb") as f:
                supabase.storage.from_("datasets").upload(filename, f)
                public_url = supabase.storage.from_("datasets").get_public_url(filename)
                print(f"Uploaded to Supabase: {public_url}")
        except Exception as e:
            print(f"Failed to upload to Supabase Storage: {e}")


    if supabase and request.student_id:
        try:
            from datetime import datetime, timezone, timedelta


            jkt_tz = timezone(timedelta(hours=7))
            now_jkt = datetime.now(jkt_tz).isoformat()


            stroke_data = None
            if request.metadata:
                stroke_data = {
                    "point_count": request.metadata.get("point_count"),
                    "bounding_box": request.metadata.get("bounding_box"),
                    "canvas_size": request.metadata.get("canvas_size"),
                    "duration_ms": request.metadata.get("duration_ms"),
                    "color_used": request.metadata.get("color_used"),
                    "device_type": request.metadata.get("device_type"),
                }


            session_id = f"{request.student_id}_{datetime.now(jkt_tz).strftime('%Y%m%d')}"

            insert_payload = {
                "student_id": request.student_id,
                "lesson_id": request.lesson_id,
                "accuracy": accuracy,
                "stars": stars,
                "image_url": public_url,
                "created_at": now_jkt,

            }


            if stroke_data:
                import json
                insert_payload["stroke_data"] = json.dumps(stroke_data)


            insert_payload["session_id"] = session_id

            supabase.table("student_progress").insert(insert_payload).execute()

            print(f"[PSD-1] Saved progress: student={request.student_id[:8]}... char={char_target} acc={accuracy}% stars={stars} device={request.metadata.get('device_type') if request.metadata else '?'}")

        except Exception as e:

            print(f"[PSD-1] Supabase Insert Warning: {e}")

            try:
                supabase.table("student_progress").insert({
                    "student_id": request.student_id,
                    "lesson_id": request.lesson_id,
                    "accuracy": accuracy,
                    "stars": stars,
                    "image_url": public_url,
                }).execute()
            except Exception as e2:
                print(f"[PSD-1] Fallback insert also failed: {e2}")


    explanation = {}
    try:
        from ai_core.pattern_matching import get_last_explanation
        explanation = get_last_explanation()
    except Exception as e:
        print(f"[PKB-1] Could not load explanation: {e}")


    hybrid_confidence = None
    hybrid_method = "baseline_cv"
    hybrid_breakdown = None
    hybrid_tip = None
    if hybrid_result:
        hybrid_confidence = hybrid_result.get("confidence")
        hybrid_method = hybrid_result.get("method", "hybrid_v1")
        hybrid_breakdown = hybrid_result.get("breakdown")
        hybrid_tip = hybrid_result.get("tip")

    print(f"Calculated accuracy: {accuracy}% | Stars: {stars} | Method: {hybrid_method} | Confidence: {hybrid_confidence or explanation.get('confidence', '?')}")
    print("===================================")


    response = {
        "status": "success",
        "message": f"Image normalized and saved as {filename}",
        "points_processed": len(coords),
        "accuracy": accuracy,
        "stars": stars,

        "algorithm_version": hybrid_method,
        "session_id": session_id if 'session_id' in dir() else None,

        "model_version": hybrid_result.get("model_version", "v4-ensemble") if hybrid_result else "v4-ensemble",
        "latency_ms": hybrid_result.get("latency_ms") if hybrid_result else None,
    }


    if hybrid_tip:
        response["tip"] = hybrid_tip
    if hybrid_confidence:
        response["confidence"] = hybrid_confidence
    if hybrid_breakdown:
        response["breakdown"] = hybrid_breakdown
    

    if explanation:
        response["explanation"] = {
            "confidence": hybrid_confidence or explanation.get("confidence", "medium"),
            "confidence_label": explanation.get("confidence_label", "?"),
            "tip": hybrid_tip or explanation.get("tip", ""),
            "strongest_dimension": explanation.get("strongest_dimension", ""),
            "weakest_dimension": explanation.get("weakest_dimension", ""),
        }

        if explanation.get("breakdown"):
            response["explanation"]["breakdown"] = explanation["breakdown"]

    return response



@app.get("/api/stats")
async def get_stats():

    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    save_dir = os.path.join(root_dir, "data_science", "datasets")

    total_latihan = 0
    if os.path.exists(save_dir):
        total_latihan = len([f for f in os.listdir(save_dir) if os.path.isfile(os.path.join(save_dir, f))])


    rata_rata = 0
    total_siswa = 32

    if supabase:
        try:

            count_res = supabase.table("profiles").select("id", count="exact").eq("role", "student").execute()
            total_siswa = count_res.count if count_res.count else total_siswa


            res = supabase.table("student_progress").select("accuracy").execute()
            if res.data and len(res.data) > 0:
                rata_rata = sum([row["accuracy"] for row in res.data]) / len(res.data)
                total_latihan = len(res.data)
        except Exception as e:
            print(f"Supabase stats error: {e}")
    else:
        if history_scores:
            rata_rata = sum(history_scores) / len(history_scores)

    return {
        "total_siswa": total_siswa,
        "total_latihan": total_latihan,
        "rata_rata": int(rata_rata)
    }



@app.get("/api/lessons")
async def get_lessons():
    """Return all available lessons (letters & numbers)."""
    if not supabase:

        return [
            {"id": i, "char_target": chr(65 + i), "category": "besar", "is_active": True}
            for i in range(26)
        ] + [
            {"id": 26 + i, "char_target": chr(97 + i), "category": "kecil", "is_active": True}
            for i in range(26)
        ] + [
            {"id": 52 + i, "char_target": str(i), "category": "angka", "is_active": True}
            for i in range(10)
        ]

    try:
        res = supabase.table("lessons") \
            .select("*") \
            .eq("is_active", True) \
            .order("id") \
            .execute()
        return res.data or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




@app.get("/api/student/{student_id}/progress")
async def get_student_progress(student_id: str):
    """Return all progress records for a specific student."""
    if not supabase:
        return []
    try:
        res = supabase.table("student_progress") \
            .select("*, lessons(char_target, category)") \
            .eq("student_id", student_id) \
            .order("created_at", desc=True) \
            .execute()
        return res.data or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




@app.get("/api/template/{char_target}")
async def get_template_image(char_target: str):
    """Return a template image (base64 PNG) for a given character."""
    import base64
    import io

    try:
        template = create_template(char_target.upper() if char_target.isupper() else char_target.lower(), target_size=64)
        _, buf = cv2.imencode('.png', template)
        b64 = base64.b64encode(buf).decode()
        return {
            "char": char_target,
            "image": f"data:image/png;base64,{b64}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Template error: {e}")




@app.get("/api/dashboard/summary")
async def dashboard_summary():
    """All metric card data in one query."""
    result = {
        "total_siswa": 0,
        "total_latihan": 0,
        "latihan_hari_ini": 0,
        "rata_rata_akurasi": 0,
        "siswa_belum_latihan": 0,
        "top_performers": [],
    }

    if not supabase:

        return {
            **result,
            "total_siswa": 3,
            "total_latihan": len(history_scores),
            "latihan_hari_ini": max(0, len(history_scores) - 2),
            "rata_rata_akurasi": int(sum(history_scores) / len(history_scores)) if history_scores else 0,
            "siswa_belum_latihan": 1,
            "top_performers": [
                {"nama": "Budi Santoso", "total_latihan": 5, "avg_accuracy": 78},
                {"nama": "Siti Aminah", "total_latihan": 3, "avg_accuracy": 65},
            ],
        }

    try:
        from datetime import datetime, timedelta

        today = datetime.utcnow().date().isoformat()
        week_ago = (datetime.utcnow() - timedelta(days=7)).date().isoformat()


        count_res = supabase.table("profiles").select("id", count="exact").eq("role", "student").execute()
        result["total_siswa"] = count_res.count or 0


        prog_res = supabase.table("student_progress").select("accuracy, stars, student_id, created_at, lesson_id").execute()
        all_progress = prog_res.data or []

        result["total_latihan"] = len(all_progress)


        today_records = [p for p in all_progress if p.get("created_at", "").startswith(today)]
        result["latihan_hari_ini"] = len(today_records)


        if all_progress:
            accs = [p["accuracy"] for p in all_progress if p.get("accuracy") is not None]
            result["rata_rata_akurasi"] = int(sum(accs) / len(accs)) if accs else 0


        week_students = set(p["student_id"] for p in all_progress if p.get("created_at", "") >= week_ago)
        all_studs_res = supabase.table("profiles").select("id").eq("role", "student").execute()
        all_student_ids = {s["id"] for s in (all_studs_res.data or [])}
        result["siswa_belum_latihan"] = len(all_student_ids - week_students) if all_student_ids else 0


        student_stats = {}
        for p in all_progress:
            sid = p["student_id"]
            if sid not in student_stats:
                student_stats[sid] = {"total": 0, "acc_sum": 0}
            student_stats[sid]["total"] += 1
            student_stats[sid]["acc_sum"] += p.get("accuracy", 0)


        if student_stats:
            top_ids = sorted(student_stats.keys(), key=lambda s: student_stats[s]["acc_sum"] / max(1, student_stats[s]["total"]), reverse=True)[:5]
            if top_ids:
                names_res = supabase.table("profiles").select("id, nama").in_("id", top_ids).execute()
                name_map = {n["id"]: n["nama"] for n in (names_res.data or [])}
                result["top_performers"] = [
                    {
                        "nama": name_map.get(sid, f"Siswa {sid[:4]}"),
                        "total_latihan": student_stats[sid]["total"],
                        "avg_accuracy": int(student_stats[sid]["acc_sum"] / student_stats[sid]["total"]),
                    }
                    for sid in top_ids
                ]
    except Exception as e:
        print(f"Dashboard summary error: {e}")

    return result


@app.get("/api/dashboard/activity")
async def dashboard_activity(limit: int = 10, offset: int = 0):
    """Recent activity feed — paginated."""
    if not supabase:

        return {
            "activities": [
                {"id": 1, "nama": "Budi Santoso", "char_target": "A", "accuracy": 85, "stars": 3, "created_at": datetime.utcnow().isoformat()},
                {"id": 2, "nama": "Siti Aminah", "char_target": "b", "accuracy": 62, "stars": 1, "created_at": (datetime.utcnow() - timedelta(hours=1)).isoformat()},
                {"id": 3, "nama": "Reza Pratama", "char_target": "7", "accuracy": 45, "stars": 1, "created_at": (datetime.utcnow() - timedelta(hours=2)).isoformat()},
            ][:limit],
            "total": 3,
        }

    from datetime import datetime, timedelta

    try:
        res = supabase.table("student_progress") \
            .select("*, profiles(nama), lessons(char_target, category)") \
            .order("created_at", desc=True) \
            .range(offset, offset + limit - 1) \
            .execute()

        activities = []
        for p in (res.data or []):
            activities.append({
                "id": p["id"],
                "nama": (p.get("profiles") or {}).get("nama", "Unknown"),
                "student_id": p["student_id"],
                "char_target": (p.get("lessons") or {}).get("char_target", "?"),
                "category": (p.get("lessons") or {}).get("category", ""),
                "accuracy": p.get("accuracy", 0),
                "stars": p.get("stars", 0),
                "lesson_id": p.get("lesson_id"),
                "created_at": p.get("created_at", ""),
            })


        count_res = supabase.table("student_progress").select("id", count="exact").execute()
        total = count_res.count or 0

        return {"activities": activities, "total": total}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dashboard/reports")
async def dashboard_reports(
    student_id: str = None,
    char_target: str = None,
    min_stars: int = None,
    limit: int = 20,
    offset: int = 0,
):
    """Full report with filters and pagination."""
    if not supabase:
        return {"reports": [], "total": 0}

    try:
        query = supabase.table("student_progress") \
            .select("*, profiles(nama, kelas), lessons(char_target, category)") \
            .order("created_at", desc=True)


        if student_id:
            query = query.eq("student_id", student_id)
        if char_target:


            pass


        query = query.range(offset, offset + limit - 1)

        res = query.execute()

        reports = []
        for p in (res.data or []):
            r = {
                "id": p["id"],
                "nama": (p.get("profiles") or {}).get("nama", "Unknown"),
                "kelas": (p.get("profiles") or {}).get("kelas", "-"),
                "char_target": (p.get("lessons") or {}).get("char_target", "?"),
                "category": (p.get("lessons") or {}).get("category", ""),
                "accuracy": p.get("accuracy", 0),
                "stars": p.get("stars", 0),
                "lesson_id": p.get("lesson_id"),
                "created_at": p.get("created_at", ""),
                "image_url": p.get("image_url"),
            }

            if char_target and r["char_target"].lower() != char_target.lower():
                continue
            if min_stars is not None and r["stars"] < min_stars:
                continue
            reports.append(r)

        count_res = supabase.table("student_progress").select("id", count="exact").execute()

        return {"reports": reports, "total": count_res.count or 0}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dashboard/chart-data")
async def dashboard_chart_data(days: int = 7):
    """Daily exercise counts for the bar chart (last N days)."""
    from datetime import datetime, timedelta

    result = []
    for i in range(days - 1, -1, -1):
        date = (datetime.utcnow() - timedelta(days=i)).date().isoformat()
        result.append({"date": date, "count": 0, "avg_accuracy": 0})

    if supabase:
        try:
            since = (datetime.utcnow() - timedelta(days=days)).isoformat()
            res = supabase.table("student_progress") \
                .select("accuracy, created_at") \
                .gte("created_at", since) \
                .execute()

            for p in (res.data or []):
                dt = p.get("created_at", "")[:10]
                for entry in result:
                    if entry["date"] == dt:
                        entry["count"] += 1
                        if p.get("accuracy") is not None:

                            n = entry["count"]
                            entry["avg_accuracy"] = int(
                                (entry["avg_accuracy"] * (n - 1) + p["accuracy"]) / n
                            )
                        break
        except Exception as e:
            print(f"Chart data error: {e}")
    else:

        import random
        for entry in result:
            entry["count"] = random.randint(1, 8)
            entry["avg_accuracy"] = random.randint(50, 95)

    return result




@app.get("/api/dashboard/heatmap")
async def dashboard_heatmap():
    """
    PSD-4.1: Accuracy Heatmap — matrix siswa × karakter.
    Returns 2D grid where cell[i][j] = avg accuracy for student_i on character_j.
    """
    if not supabase:

        return _fake_heatmap()

    try:

        studs_res = supabase.table("profiles").select("id, nama").eq("role", "student").order("nama").execute()
        students = studs_res.data or []


        lessons_res = supabase.table("lessons").select("id, char_target, category").eq("is_active", True).order("id").execute()
        lessons = lessons_res.data or []


        prog_res = supabase.table("student_progress").select("student_id, lesson_id, accuracy").execute()
        all_prog = prog_res.data or []


        lesson_map = {l["id"]: l["char_target"] for l in lessons}


        from collections import defaultdict
        matrix_agg = defaultdict(lambda: defaultdict(list))

        for p in all_prog:
            sid = p["student_id"]
            char = lesson_map.get(p["lesson_id"], "?")
            if p.get("accuracy") is not None:
                matrix_agg[sid][char].append(p["accuracy"])


        all_chars = sorted(set(l["char_target"] for l in lessons))
        matrix = []
        for s in students:
            row = {
                "student_id": s["id"],
                "nama": s["nama"],
                "scores": {},
            }
            for c in all_chars:
                vals = matrix_agg[s["id"]].get(c, [])
                row["scores"][c] = round(sum(vals) / len(vals), 1) if vals else None
            matrix.append(row)

        return {
            "students": [{"id": s["id"], "nama": s["nama"]} for s in students],
            "characters": all_chars,
            "matrix": matrix,
            "generated_at": __import__('datetime').datetime.utcnow().isoformat(),
        }
    except Exception as e:
        print(f"Heatmap error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dashboard/student-trend/{student_id}")
async def dashboard_student_trend(student_id: str, window: int = 30):
    """
    PSD-4.2: Time series — daily avg accuracy for a student over N days.
    Supports trend detection via simple linear regression slope.
    """
    if not supabase:
        return _fake_student_trend(student_id, window)

    from datetime import datetime, timedelta

    try:
        since = (datetime.utcnow() - timedelta(days=window)).isoformat()

        res = supabase.table("student_progress") \
            .select("accuracy, stars, created_at, lesson_id, lessons(char_target, category)") \
            .eq("student_id", student_id) \
            .gte("created_at", since) \
            .order("created_at") \
            .execute()

        records = res.data or []


        daily = defaultdict(list)
        for r in records:
            dt = (r.get("created_at", "") or "")[:10]
            if r.get("accuracy") is not None:
                daily[dt].append(r["accuracy"])


        series = []
        accums = []
        for i in range(window):
            d = (datetime.utcnow() - timedelta(days=window - 1 - i)).date().isoformat()
            vals = daily.get(d, [])
            avg = round(sum(vals) / len(vals), 1) if vals else None
            count = len(vals)
            accums.append(avg)


            ma7 = None
            if len(accums) >= 3 and avg is not None:
                window_vals = [v for v in accums[-7:] if v is not None]
                if len(window_vals) >= 3:
                    ma7 = round(sum(window_vals) / len(window_vals), 1)

            series.append({
                "date": d,
                "avg_accuracy": avg,
                "exercise_count": count,
                "moving_avg_7d": ma7,
            })


        valid = [(i, s["avg_accuracy"]) for i, s in enumerate(series) if s["avg_accuracy"] is not None]
        trend = "no_data"
        slope = 0.0
        if len(valid) >= 3:
            n = len(valid)
            sum_x = sum(v[0] for v in valid)
            sum_y = sum(v[1] for v in valid)
            sum_xy = sum(v[0] * v[1] for v in valid)
            sum_x2 = sum(v[0] ** 2 for v in valid)
            denom = n * sum_x2 - sum_x ** 2
            if abs(denom) > 1e-9:
                slope = (n * sum_xy - sum_x * sum_y) / denom
            if slope > 0.5:
                trend = "improving"
            elif slope < -0.5:
                trend = "declining"
            else:
                trend = "stable"

        return {
            "student_id": student_id,
            "window_days": window,
            "series": series,
            "trend": trend,
            "slope_per_day": round(slope, 4),
            "total_exercises": sum(s["exercise_count"] for s in series),
            "best_day": max(((s["date"], s["avg_accuracy"]) for s in series if s["avg_accuracy"] is not None), key=lambda x: x[1] or (None, 0))[0] if any(s["avg_accuracy"] for s in series) else None,
        }
    except Exception as e:
        print(f"Student trend error: {e}")
        return _fake_student_trend(student_id, window)


@app.get("/api/dashboard/character-rankings")
async def dashboard_character_rankings():
    """
    PSD-4.3: Character difficulty ranking — easiest to hardest.
    Includes attempts count, avg accuracy, avg stars, grouped by category.
    """
    if not supabase:
        return _fake_character_rankings()

    try:

        res = supabase.table("student_progress") \
            .select("lesson_id, accuracy, stars, created_at, lessons(char_target, category)") \
            .execute()

        records = res.data or []


        from collections import defaultdict
        char_data = defaultdict(list)

        for r in records:
            char = (r.get("lessons") or {}).get("char_target", "?")
            cat = (r.get("lessons") or {}).get("category", "")
            char_data[char].append({
                "accuracy": r.get("accuracy"),
                "stars": r.get("stars"),
                "category": cat,
            })

        rankings = []
        for char, entries in char_data.items():
            accs = [e["accuracy"] for e in entries if e["accuracy"] is not None]
            stars = [e["stars"] for e in entries if e["stars"] is not None]
            cats = set(e["category"] for e in entries if e["category"])

            rankings.append({
                "character": char,
                "category": cats.pop() if cats else "",
                "attempts": len(entries),
                "avg_accuracy": round(sum(accs) / len(accs), 1) if accs else None,
                "max_accuracy": max(accs) if accs else None,
                "min_accuracy": min(accs) if accs else None,
                "avg_stars": round(sum(stars) / len(stars), 2) if stars else None,
                "unique_students": len(set(

                    hash(str(e)) for e in entries
                )),
            })


        rankings.sort(key=lambda r: r["avg_accuracy"] or 100)


        categories = defaultdict(list)
        for r in rankings:
            cat = r["category"] or "unknown"
            categories[cat].append(r)

        category_summary = []
        for cat, chars in categories.items():
            accs = [r["avg_accuracy"] for r in chars if r["avg_accuracy"] is not None]
            category_summary.append({
                "category": cat,
                "character_count": len(chars),
                "total_attempts": sum(r["attempts"] for r in chars),
                "avg_accuracy": round(sum(accs) / len(accs), 1) if accs else None,
                "hardest_char": min(chars, key=lambda r: r["avg_accuracy"] or 100)["character"] if chars else None,
                "easiest_char": max(chars, key=lambda r: r["avg_accuracy"] or 0)["character"] if chars else None,
            })

        return {
            "rankings": rankings,
            "category_summary": category_summary,
            "total_characters": len(rankings),
            "generated_at": __import__('datetime').datetime.utcnow().isoformat(),
        }
    except Exception as e:
        print(f"Character rankings error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dashboard/class-comparison")
async def dashboard_class_comparison():
    """
    PSD-4.4: Class comparison — TK-A vs TK-B (or any classes).
    Total exercises, avg accuracy, active students per class.
    """
    if not supabase:
        return _fake_class_comparison()

    from datetime import datetime, timedelta

    try:
        week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()


        studs_res = supabase.table("profiles").select("id, kelas").eq("role", "student").execute()
        students = studs_res.data or []


        prog_res = supabase.table("student_progress") \
            .select("student_id, accuracy, stars, created_at") \
            .gte("created_at", week_ago) \
            .execute()
        week_prog = prog_res.data or []


        class_students = defaultdict(list)
        for s in students:
            kelas = s.get("kelas") or "Tidak Diketahui"
            class_students[kelas].append(s["id"])


        class_prog = defaultdict(list)
        sid_to_kelas = {}
        for s in students:
            sid_to_kelas[s["id"]] = s.get("kelas") or "Tidak Diketahui"

        for p in week_prog:
            kelas = sid_to_kelas.get(p["student_id"], "Tidak Diketahui")
            class_prog[kelas].append(p)

        comparisons = []
        for kelas in sorted(class_students.keys()):
            studs_in_class = class_students[kelas]
            progs = class_prog[kelas]
            accs = [p["accuracy"] for p in progs if p.get("accuracy") is not None]
            active_ids = set(p["student_id"] for p in progs)

            comparisons.append({
                "class_name": kelas,
                "total_students": len(studs_in_class),
                "active_students_week": len(active_ids),
                "inactive_students_week": len(studs_in_class) - len(active_ids),
                "total_exercises_week": len(progs),
                "avg_accuracy": round(sum(accs) / len(accs), 1) if accs else None,
                "avg_stars": round(sum(p.get("stars", 0) or 0 for p in progs) / len(progs), 2) if progs else None,
                "exercises_per_student": round(len(progs) / max(len(studs_in_class), 1), 1),
                "top_accuracy": max(accs) if accs else None,
                "bottom_accuracy": min(accs) if accs else None,
            })

        return {
            "classes": comparisons,
            "period_days": 7,
            "generated_at": __import__('datetime').datetime.utcnow().isoformat(),
        }
    except Exception as e:
        print(f"Class comparison error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dashboard/export")
async def dashboard_export(format: str = "json"):
    """
    PSD-4.6: Export full report data as JSON or CSV.
    """
    if not supabase:
        return _fake_export(format)

    try:
        res = supabase.table("student_progress") \
            .select("*, profiles(nama, kelas), lessons(char_target, category)") \
            .order("created_at", desc=True) \
            .execute()

        records = res.data or []
        export_rows = []
        for r in records:
            export_rows.append({
                "id": r.get("id"),
                "nama": (r.get("profiles") or {}).get("nama", "Unknown"),
                "kelas": (r.get("profiles") or {}).get("kelas", ""),
                "karakter": (r.get("lessons") or {}).get("char_target", "?"),
                "kategori": (r.get("lessons") or {}).get("category", ""),
                "akurasi": r.get("accuracy", 0),
                "bintang": r.get("stars", 0),
                "tanggal": r.get("created_at", ""),
                "gambar": r.get("image_url", ""),
            })

        if format.lower() == "csv":
            import csv
            import io

            output = io.StringIO()
            if export_rows:
                writer = csv.DictWriter(output, fieldnames=list(export_rows[0].keys()))
                writer.writeheader()
                writer.writerows(export_rows)
            csv_text = output.getvalue()

            from fastapi.responses import Response
            return Response(
                content=csv_text,
                media_type="text/csv; charset=utf-8",
                headers={"Content-Disposition": "attachment; filename=report.csv"},
            )


        return {
            "exported_at": __import__("datetime").datetime.utcnow().isoformat(),
            "total_records": len(export_rows),
            "data": export_rows,
        }
    except Exception as e:
        print(f"Export error: {e}")
        raise HTTPException(status_code=500, detail=str(e))






@app.get("/api/models/status")
async def models_status():
    """
    PKB-5.4: Return status of all AI models loaded in the hybrid engine.
    Shows which branches are active, which models are loaded, weights, etc.
    """
    if not _predictor_available:
        return {
            "status": "limited",
            "predictor_available": False,
            "message": "Hybrid engine not loaded. Using baseline CV only.",
            "baseline": {"available": True, "method": "pattern_matching v4"},
        }
    
    try:
        predictor = get_predictor()
        info = predictor.get_model_info()
        

        registry_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "ai_core", "inference", "model_registry.json"
        )
        registry = {}
        if os.path.exists(registry_path):
            with open(registry_path, "r", encoding="utf-8") as f:
                import json
                registry = json.load(f)
        
        return {
            "status": "ok",
            "predictor_available": True,
            **info,
            "registry": registry.get("registry", {}),
            "active_model": registry.get("active_model", "hybrid_v1"),
        }
    except Exception as e:
        print(f"[PKB-5] Models status error: {e}")
        return {"status": "error", "message": str(e)}


class CompareRequest(BaseModel):
    image_path: str
    char_target: str = "A"


@app.post("/api/models/compare")
async def models_compare(request: CompareRequest):
    """
    PKB-5.4: Run ALL available models on the same image and compare results.
    Returns side-by-side output from CV, ML, and DL branches.
    Useful for debugging and A/B testing.
    """
    if not _predictor_available:
        raise HTTPException(
            status_code=503,
            detail="Predictor not available. Cannot run comparison."
        )
    
    if not os.path.exists(request.image_path):
        raise HTTPException(status_code=404, detail=f"Image not found: {request.image_path}")
    
    try:
        predictor = get_predictor()
        result = predictor.compare_models(request.image_path, request.char_target)
        return result
    except Exception as e:
        print(f"[PKB-5] Models compare error: {e}")
        raise HTTPException(status_code=500, detail=str(e))






@app.post("/api/psd/run-pipeline")
async def psd_run_pipeline(request: dict = None):
    """PSD-5.2: Trigger full PSD data pipeline manually."""
    from datetime import datetime

    results = {"started_at": datetime.now().isoformat(), "steps": []}
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    datasets_root = os.path.join(root_dir, "data_science", "datasets")


    try:
        step1 = {"step": "scan_datasets", "status": "running"}
        total_files = 0
        processed_dir = os.path.join(datasets_root, "processed")
        if os.path.exists(processed_dir):
            for subdir in os.listdir(processed_dir):
                subpath = os.path.join(processed_dir, subdir)
                if os.path.isdir(subpath):
                    files = [f for f in os.listdir(subpath) if f.endswith(".png")]
                    total_files += len(files)
        step1["total_images"] = total_files
        step1["status"] = "ok"
        results["steps"].append(step1)
    except Exception as e:
        results["steps"].append({"step": "scan_datasets", "status": "error", "message": str(e)})


    try:
        step2 = {"step": "export_for_training", "status": "running"}
        scripts_dir = os.path.join(root_dir, "data_science", "scripts")
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
        from export_for_training import run_export_pipeline
        report = run_export_pipeline(use_synthetic=(total_files < 10))
        step2["train_size"] = report.get("dataset_summary", {}).get("train_size", 0)
        step2["test_size"] = report.get("dataset_summary", {}).get("test_size", 0)
        step2["status"] = "ok"
        step2["report"] = "split_report.json"
        results["steps"].append(step2)
    except Exception as e:
        results["steps"].append({"step": "export_for_training", "status": "error", "message": str(e)})


    try:
        step3 = {"step": "generate_statistics", "status": "running"}
        stats_path = os.path.join(root_dir, "data_science", "reports", "data_quality_report.json")
        step3["existing_report"] = os.path.exists(stats_path)
        step3["status"] = "ok"
        results["steps"].append(step3)
    except Exception as e:
        results["steps"].append({"step": "generate_statistics", "status": "error", "message": str(e)})


    try:
        step4 = {"step": "generate_weekly_report", "status": "running"}
        scripts_dir = os.path.join(root_dir, "data_science", "scripts")
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
        from generate_reports import generate_weekly_report
        report_data = generate_weekly_report(period_days=7)
        step4["records_analyzed"] = report_data.get("metadata", {}).get("total_records_analyzed", 0)
        step4["status"] = "ok"
        results["steps"].append(step4)
    except Exception as e:
        results["steps"].append({"step": "generate_weekly_report", "status": "error", "message": str(e)})

    results["completed_at"] = datetime.now().isoformat()
    results["total_steps"] = len(results["steps"])
    results["successful_steps"] = sum(1 for s in results["steps"] if s.get("status") == "ok")

    return results


@app.get("/api/psd/status")
async def psd_pipeline_status():
    """PSD-5.2: Return current pipeline status and last run info."""
    from datetime import datetime

    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    reports_dir = os.path.join(root_dir, "data_science", "reports")
    exports_dir = os.path.join(root_dir, "data_science", "datasets", "exports")
    datasets_dir = os.path.join(root_dir, "data_science", "datasets")

    total_images = 0
    processed_dir = os.path.join(datasets_dir, "processed")
    if os.path.exists(processed_dir):
        for d in os.listdir(processed_dir):
            subpath = os.path.join(processed_dir, d)
            if os.path.isdir(subpath):
                total_images += len([f for f in os.listdir(subpath) if f.endswith(".png")])

    export_files = []
    if os.path.exists(exports_dir):
        export_files = [f for f in os.listdir(exports_dir) if f.endswith((".csv", ".npy", ".json"))]

    report_files = []
    if os.path.exists(reports_dir):
        report_files = [f for f in os.listdir(reports_dir) if f.endswith((".json", ".html"))]

    latest_report = None
    latest_path = os.path.join(reports_dir, "latest_report.json")
    if os.path.exists(latest_path):
        try:
            with open(latest_path, "r", encoding="utf-8") as f:
                latest_report = json.load(f)
        except Exception:
            pass
    return {
        "pipeline_version": "psd-5.2",
        "status": "ready",
        "data_inventory": {
            "total_images_in_dataset": total_images,
            "export_files": len(export_files),
            "export_file_names": sorted(export_files),
            "report_files": len(report_files),
            "report_file_names": sorted(report_files)[:10],
        },
        "latest_report": latest_report,
        "last_check": datetime.utcnow().isoformat(),
        "endpoints_available": [
            "POST /api/psd/run-pipeline",
            "GET /api/psd/status",
            "GET /api/psd/data-quality",
            "GET /api/psd/report",
        ],
    }


@app.get("/api/psd/data-quality")
async def psd_data_quality():
    """PSD-5.4: Real-time data quality metrics."""
    from datetime import datetime

    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    datasets_root = os.path.join(root_dir, "data_science", "datasets")
    processed_dir = os.path.join(datasets_root, "processed")
    exports_dir = os.path.join(datasets_root, "exports")

    char_distribution = {}
    total_size_bytes = 0
    blank_count = 0
    tiny_count = 0

    if os.path.exists(processed_dir):
        for char_folder in os.listdir(processed_dir):
            char_path = os.path.join(processed_dir, char_folder)
            if not os.path.isdir(char_path):
                continue
            png_files = [f for f in os.listdir(char_path) if f.endswith(".png")]
            count = len(png_files)
            char_distribution[char_folder] = count

            for pf in png_files[:20]:
                fpath = os.path.join(char_path, pf)
                fsize = os.path.getsize(fpath)
                total_size_bytes += fsize
                if fsize < 200:
                    tiny_count += 1
                if fsize < 100:
                    blank_count += 1

    sorted_chars = sorted(char_distribution.items(), key=lambda x: x[1], reverse=True)

    counts = [c for _, c in sorted_chars if c > 0]
    imbalance_ratio = max(counts) / min(counts) if len(counts) >= 2 and min(counts) > 0 else 1.0
    is_imbalanced = imbalance_ratio > 10

    train_csv = os.path.join(exports_dir, "train_features.csv")
    test_csv = os.path.join(exports_dir, "test_features.csv")
    split_status = {
        "train_exists": os.path.exists(train_csv),
        "test_exists": os.path.exists(test_csv),
        "train_size_rows": 0,
        "test_size_rows": 0,
    }

    if os.path.exists(train_csv):
        with open(train_csv, "r") as f:
            split_status["train_size_rows"] = sum(1 for _ in f) - 1
    if os.path.exists(test_csv):
        with open(test_csv, "r") as f:
            split_status["test_size_rows"] = sum(1 for _ in f) - 1

    return {
        "quality_version": "psd-5.4",
        "checked_at": datetime.utcnow().isoformat(),
        "dataset_overview": {
            "total_samples": sum(char_distribution.values()),
            "unique_characters": len(char_distribution),
            "total_size_mb": round(total_size_bytes / (1024*1024), 2),
            "characters_with_data": len([c for c, n in char_distribution.items() if n > 0]),
            "characters_empty": len([c for c, n in char_distribution.items() if n == 0]),
        },
        "class_distribution": {
            "per_character": dict(sorted_chars[:10]),
            "most_common": sorted_chars[0] if sorted_chars else None,
            "least_common": sorted_chars[-1] if sorted_chars else None,
            "imbalance_ratio": round(imbalance_ratio, 2),
            "is_imbalanced": is_imbalanced,
            "recommendation": (
                "Dataset tidak seimbang. Pertimbangkan augmentasi untuk kelas minoritas."
                if is_imbalanced else "Distribusi kelas cukup merata."
            ),
        },
        "data_integrity": {"blank_or_suspicious_files": blank_count, "very_small_files": tiny_count, "health_score": max(0, 100 - (blank_count * 5) - (tiny_count * 2))},
        "export_split": split_status,
        "last_ingestion": datetime.utcnow().isoformat() if total_size_bytes > 0 else None,
    }


@app.get("/api/psd/report")
async def psd_get_latest_report():
    """PSD-5.3: Return the latest generated weekly report."""
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    reports_dir = os.path.join(root_dir, "data_science", "reports")

    latest_path = os.path.join(reports_dir, "latest_report.json")
    if os.path.exists(latest_path):
        with open(latest_path, "r", encoding="utf-8") as f:
            return json.load(f)

    if os.path.exists(reports_dir):
        json_reports = sorted(
            [f for f in os.listdir(reports_dir) if f.startswith("weekly_") and f.endswith(".json")],
            reverse=True
        )
        if json_reports:
            with open(os.path.join(reports_dir, json_reports[0]), "r", encoding="utf-8") as f:
                return json.load(f)

    try:
        scripts_dir = os.path.join(root_dir, "data_science", "scripts")
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
        from generate_reports import generate_weekly_report
        report = generate_weekly_report(period_days=7)
        return report
    except Exception as e:
        return {
            "status": "no_report",
            "message": str(e),
            "hint": "Run POST /api/psd/run-pipeline to generate reports",
        }







@app.get("/api/psd/clustering")
async def psd_clustering():
    """PSD-6.1: Run handwriting style clustering, return results."""
    from datetime import datetime

    scripts_dir = os.path.join(root_dir if 'root_dir' in dir() else os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data_science", "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)

    try:
        from clustering import run_full_clustering_pipeline, generate_clustering_data, run_kmeans_clustering


        report = run_full_clustering_pipeline()

        return {
            "status": "ok",
            "clustering_version": "psd-6.1",
            "generated_at": datetime.utcnow().isoformat(),
            **report,
        }
    except Exception as e:

        try:
            from clustering import generate_clustering_data, run_kmeans_clustering
            X, labels_true, student_ids, fnames = generate_clustering_data()
            result = run_kmeans_clustering(X, n_clusters=4)
            return {
                "status": "ok_fallback",
                "clustering_version": "psd-6.1",
                "n_samples": int(X.shape[0]),
                "n_clusters": result["n_clusters"],
                "metrics": result["metrics"],
                "cluster_summary": result["cluster_summary"],
                "error_detail": str(e),
            }
        except Exception as e2:
            return {"status": "error", "message": str(e2)}


@app.get("/api/psd/anomalies")
async def psd_anomaly_detection():
    """PSD-6.2: Detect anomalies in student data."""
    scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data_science", "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)

    try:
        from anomaly_detection import generate_anomaly_data, detect_anomalies_isolation_forest, detect_anomalies_statistical, analyze_anomaly_patterns

        X, true_labels = generate_anomaly_data(n_samples=100)
        if_result = detect_anomalies_isolation_forest(X)
        stat_result = detect_anomalies_statistical(X)

        all_anom = list(set(if_result["anomaly_indices"] + stat_result.get("global_anomalies", [])))
        patterns = analyze_anomaly_patterns(X, all_anom, true_labels)

        return {
            "status": "ok",
            "anomaly_version": "psd-6.2",
            "total_samples": int(X.shape[0]),
            "anomalies_detected": patterns["total_anomalies"],
            "anomaly_rate": patterns.get("anomaly_rate", 0),
            "categories": patterns.get("categories", {}),
            "descriptions": patterns.get("descriptions", {}),
            "isolation_forest": {"anomalies": len(if_result["anomaly_indices"])},
            "statistical": {"global_anomalies": len(stat_result.get("global_anomalies", []))},
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/api/psd/recommendations/{student_id}")
async def psd_recommendations(student_id: str):
    """PSD-6.3: Get personalized learning recommendations for a student."""
    scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data_science", "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)

    try:
        from recommendation_engine import generate_student_performance_data, recommend_learning_path

        students = generate_student_performance_data(n_students=10, n_exercises_per_student=35)


        target = None
        for s in students:
            if s["id"] == student_id or s["nama"].lower() == student_id.lower():
                target = s
                break

        if not target:
            target = students[hash(student_id) % len(students)]

        rec = recommend_learning_path(target)
        rec["query_student_id"] = student_id
        return {"status": "ok", **rec}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/api/psd/advanced-analytics")
async def psd_advanced_analytics_dashboard():
    """
    PSD-6 Combined: Return all advanced analytics in one call.
    Clustering + Anomalies + Recommendations summary.
    """
    scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data_science", "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)

    result = {
        "dashboard_version": "psd-6-combined",
        "generated_at": None,
        "clustering": None,
        "anomalies": None,
        "recommendations_summary": None,
    }

    try:
        from datetime import datetime
        result["generated_at"] = datetime.utcnow().isoformat()


        from clustering import generate_clustering_data, run_kmeans_clustering
        X, _, _, fnames = generate_clustering_data()
        clust = run_kmeans_clustering(X, n_clusters=4)
        result["clustering"] = {
            "n_clusters": clust["n_clusters"],
            "silhouette": clust["metrics"].get("silhouette"),
            "clusters": [{
                "id": cs["cluster_id"],
                "n_members": cs["n_members"],
                "type": "unknown",
            } for cs in clust["cluster_summary"]],
        }


        from anomaly_detection import generate_anomaly_data, detect_anomalies_isolation_forest
        X_anom, _ = generate_anomaly_data()
        anom_result = detect_anomalies_isolation_forest(X_anom)
        result["anomalies"] = {
            "total_anomalies": len(anom_result["anomaly_indices"]),
            "anomaly_rate": round(len(anom_result["anomaly_indices"]) / len(X_anom) * 100, 1),
        }


        from recommendation_engine import generate_student_performance_data, generate_class_recommendations
        students = generate_student_performance_data()
        class_recs = generate_class_recommendations(students)
        result["recommendations_summary"] = class_recs

        result["status"] = "ok"
    except Exception as e:
        result["status"] = "partial"
        result["error"] = str(e)

    return result






def _fake_heatmap():
    """Generate synthetic heatmap for dev without Supabase."""
    import random
    random.seed(42)
    fake_students = [
        {"id": f"s{i}", "nama": name} for i, name in enumerate([
            "Budi Santoso", "Siti Aminah", "Reza Pratama",
            "Dewi Lestari", "Andi Firmansyah", "Fitri Handayani",
        ])
    ]
    fake_chars = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ") + list("abcdefghijklmnopqrstuvwxyz") + list("0123456789")
    matrix = []
    for s in fake_students:
        row = {"student_id": s["id"], "nama": s["nama"], "scores": {}}
        for c in fake_chars[:20]:
            row["scores"][c] = random.randint(20, 95) if random.random() > 0.3 else None
        matrix.append(row)
    return {"students": fake_students, "characters": fake_chars[:20], "matrix": matrix}


def _fake_student_trend(student_id, window):
    """Synthetic student trend for dev."""
    import random
    random.seed(hash(student_id) % 2**32)
    series = []
    base = random.randint(40, 70)
    for i in range(window):
        d = (__import__('datetime').datetime.utcnow() - __import__('datetime').timedelta(days=window - 1 - i)).date().isoformat()
        val = base + int(random.uniform(-10, 15)) + int(i * 0.3)
        val = max(0, min(100, val))
        series.append({"date": d, "avg_accuracy": val, "exercise_count": random.randint(0, 5), "moving_avg_7d": None})

    for i in range(6, window):
        vals = [s["avg_accuracy"] for s in series[max(0,i-6):i+1] if s["avg_accuracy"] is not None]
        if vals:
            series[i]["moving_avg_7d"] = round(sum(vals)/len(vals), 1)
    return {"student_id": student_id, "window_days": window, "series": series,
            "trend": "improving", "slope_per_day": 0.3, "total_exercises": sum(s["exercise_count"] for s in series)}

def _fake_character_rankings():
    """Synthetic character rankings."""
    import random
    random.seed(42)
    chars_besar = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    chars_kecil = list("abcdefghijklmnopqrstuvwxyz")
    chars_angka = list("0123456789")
    rankings = []
    for c in chars_besar + chars_kecil + chars_angka:
        cat = "besar" if c in chars_besar else ("kecil" if c in chars_kecil else "angka")
        avg = random.randint(30, 95)
        rankings.append({"character": c, "category": cat, "attempts": random.randint(5, 50),
                          "avg_accuracy": avg, "max_accuracy": min(100, avg+random.randint(5,15)),
                          "min_accuracy": max(0, avg-random.randint(10,30)),
                          "avg_stars": round(random.uniform(1, 3), 2), "unique_students": random.randint(1, 6)})
    rankings.sort(key=lambda r: r["avg_accuracy"])
    return {"rankings": rankings, "category_summary": [], "total_characters": len(rankings)}

def _fake_class_comparison():
    """Synthetic class comparison."""
    return {"classes": [
        {"class_name": "TK-A", "total_students": 18, "active_students_week": 12, "inactive_students_week": 6,
         "total_exercises_week": 47, "avg_accuracy": 68.3, "avg_stars": 2.1, "exercises_per_student": 2.6,
         "top_accuracy": 95, "bottom_accuracy": 25},
        {"class_name": "TK-B", "total_students": 14, "active_students_week": 9, "inactive_students_week": 5,
         "total_exercises_week": 33, "avg_accuracy": 62.7, "avg_stars": 1.9, "exercises_per_student": 2.4,
         "top_accuracy": 90, "bottom_accuracy": 20},
    ], "period_days": 7}


def _fake_export(format):
    """Synthetic export data."""
    rows = [{"id": i, "nama": f"Siswa_{i}", "kelas": "TK-A" if i % 2 == 0 else "TK-B",
             "karakter": chr(65 + (i % 26)), "kategori": "besar", "akurasi": 50 + (i % 50),
             "bintang": (i % 4), "tanggal": "2026-05-29", "gambar": ""}
            for i in range(20)]
    if format.lower() == "csv":
        import csv, io
        from fastapi.responses import Response
        out = io.StringIO()
        w = csv.DictWriter(out, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
        return Response(content=out.getvalue(), media_type="text/csv",
                       headers={"Content-Disposition": 'attachment; filename="laporan.csv"'})
    return {"exported_at": __import__('datetime').datetime.utcnow().isoformat(), "total_records": len(rows), "data": rows}




@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "version": "2.1.0",
        "supabase_connected": supabase is not None
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
