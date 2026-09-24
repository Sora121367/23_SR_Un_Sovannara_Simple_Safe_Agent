

COURSES = [
    {"id": 1, "code": "CS201", "name": "Algorithms",         "day": "Mon/Wed", "time": "10:00-11:30", "seats": 5},
    {"id": 2, "code": "CS305", "name": "Operating Systems",  "day": "Tue/Thu", "time": "13:00-14:30", "seats": 0},
    {"id": 3, "code": "MA110", "name": "Linear Algebra",     "day": "Mon/Wed/Fri", "time": "09:00-10:00", "seats": 12},
    {"id": 4, "code": "CS410", "name": "Advanced Algorithms","day": "Fri", "time": "14:00-17:00", "seats": 2},
]

# Tracks registrations made during run
REGISTRATIONS: dict[str, list[int]] = {}


def _find_course(course_id: int) -> dict | None:
    return next((c for c in COURSES if c["id"] == course_id), None)


# Tool implementations 

def search_course(query: str) -> dict:
    """
    Search courses by name or course code (case-insensitive substring match).
    Returns a controlled result dict; never raises to the caller.
    """
    q = query.lower()
    matches = [c for c in COURSES if q in c["name"].lower() or q in c["code"].lower()]

    if not matches:
        return {"status": "ok", "count": 0, "results": [], "message": f"No courses found matching '{query}'."}

    return {"status": "ok", "count": len(matches), "results": matches}


def check_schedule(course_id: int) -> dict:
    """
    Look up the schedule and seat availability for a given course_id.
    Returns a structured error (not a raw exception) if the course doesn't exist.
    """
    course = _find_course(course_id)
    if course is None:
        return {"status": "error", "error_code": "COURSE_NOT_FOUND",
                "message": f"No course exists with id={course_id}."}

    return {
        "status": "ok",
        "course_id": course["id"],
        "code": course["code"],
        "name": course["name"],
        "day": course["day"],
        "time": course["time"],
        "seats_available": course["seats"],
    }


def register_course(course_id: int, student_name: str) -> dict:
    """
    Register a student into a course. Sensitive/write action -- permission
    for this is checked separately in harness.py before this function runs.
    """
    course = _find_course(course_id)
    if course is None:
        return {"status": "error", "error_code": "COURSE_NOT_FOUND",
                "message": f"No course exists with id={course_id}."}

    if course["seats"] <= 0:
        return {"status": "error", "error_code": "OUT_OF_SEATS",
                "message": f"Course '{course['name']}' ({course['code']}) has no seats available."}

    already = REGISTRATIONS.get(student_name, [])
    if course_id in already:
        return {"status": "error", "error_code": "ALREADY_REGISTERED",
                "message": f"{student_name} is already registered in '{course['name']}'."}

    # Commit the "write"
    course["seats"] -= 1
    REGISTRATIONS.setdefault(student_name, []).append(course_id)

    return {
        "status": "ok",
        "message": f"{student_name} successfully registered in '{course['name']}' ({course['code']}).",
        "course_id": course_id,
        "seats_remaining": course["seats"],
    }


# Registry mapping tool name -> callable implementation.
TOOL_IMPLEMENTATIONS = {
    "search_course": search_course,
    "check_schedule": check_schedule,
    "register_course": register_course,
}