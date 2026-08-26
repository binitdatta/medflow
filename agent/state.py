from typing import Literal, Optional, TypedDict


Role = Literal[
    "PHYSICIAN", "NURSE", "PHARMACIST", "ADMISSIONS",
    "FINANCE", "MANAGEMENT", "LEGAL", "ADMIN",
]


class ToolResult(TypedDict, total=False):
    tool_name: str
    action: str            # READ | CREATE | UPDATE | DELETE
    resource_type: str
    resource_id: Optional[int]
    phi_accessed: bool
    data: object


class MedFlowState(TypedDict, total=False):
    user_query: str
    staff_id: int
    role: Role
    hospital_scope: Optional[int]
    intent: Optional[str]
    tool_results: list
    response: Optional[str]
