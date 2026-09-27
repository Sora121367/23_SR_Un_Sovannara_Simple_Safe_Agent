
from pydantic import BaseModel, Field, field_validator


class SearchCourseInput(BaseModel):
    """Input schema for search_course."""
    query: str = Field(..., description="Course name, code, or keyword to search for, e.g. 'Algorithms' or 'CS201'.")

    @field_validator("query")
    @classmethod
    def query_not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("query must not be empty")
        return v.strip()


class CheckScheduleInput(BaseModel):
    """Input schema for check_schedule."""
    course_id: int = Field(..., description="Numeric ID of the course to check the schedule for.")

    @field_validator("course_id")
    @classmethod
    def course_id_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("course_id must be a positive integer")
        return v


class RegisterCourseInput(BaseModel):
    """Input schema for register_course."""
    course_id: int = Field(..., description="Numeric ID of the course to register the student into.")
    student_name: str = Field(..., description="Name of the student to register for the course.")

    @field_validator("course_id")
    @classmethod
    def course_id_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("course_id must be a positive integer")
        return v

    @field_validator("student_name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("student_name must not be empty")
        return v.strip()


# Registry mapping tool name -> Pydantic schema class.
TOOL_SCHEMAS = {
    "search_course": SearchCourseInput,
    "check_schedule": CheckScheduleInput,
    "register_course": RegisterCourseInput,
}


def tool_schemas_for_llm() -> list[dict]:
    """
    Build the JSON-schema tool definitions the LLM needs to propose
    structured tool calls ('tools' format).
    """
    return [
        {
            "name": "search_course",
            "description": "Search for courses by name, code, or keyword. Returns a list of matching courses with their IDs.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Course name, code, or keyword, e.g. 'Algorithms' or 'CS201'."}
                },
                "required": ["query"],
            },
        },
        {
            "name": "check_schedule",
            "description": "Check the schedule (day, time, seats available) for a specific course by its ID.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "course_id": {"type": "integer", "description": "Numeric ID of the course, must be positive."}
                },
                "required": ["course_id"],
            },
        },
        {
            "name": "register_course",
            "description": "Register a student into a course by course ID. This is a sensitive/write action restricted by role.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "course_id": {"type": "integer", "description": "Numeric ID of the course, must be positive."},
                    "student_name": {"type": "string", "description": "Name of the student being registered."},
                },
                "required": ["course_id", "student_name"],
            },
        },
    ]