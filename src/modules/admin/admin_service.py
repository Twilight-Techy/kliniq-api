# src/modules/admin/admin_service.py
"""
Hospital administration data.

Every figure returned here is computed from the database. Where the schema
holds no source for something the UI used to display, this returns null and
the frontend renders it as unavailable rather than inventing a number.
"""

from datetime import date, datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.models import (
    Appointment,
    AppointmentStatus,
    Clinician,
    ClinicianRoleType,
    ClinicianStatus,
    Department,
    EscalatedQuery,
    Hospital,
    Invoice,
    InvoiceStatus,
    Patient,
    PatientHospital,
    Report,
    User,
    UserRole,
)


async def _resolve_hospital(db: AsyncSession, admin: User) -> Hospital:
    """
    The hospital this administrator manages.

    Admins are linked through their Clinician record; if there is exactly one
    hospital on the instance we fall back to it so a single-tenant deployment
    works without extra setup.
    """
    result = await db.execute(select(Clinician).where(Clinician.user_id == admin.id))
    clinician = result.scalars().first()
    if clinician is not None and clinician.hospital_id is not None:
        result = await db.execute(select(Hospital).where(Hospital.id == clinician.hospital_id))
        hospital = result.scalars().first()
        if hospital is not None:
            return hospital

    result = await db.execute(select(Hospital).limit(2))
    hospitals = result.scalars().all()
    if len(hospitals) == 1:
        return hospitals[0]

    raise ValueError(
        "No hospital is associated with this administrator account."
    )


def _percent_change(current: int, previous: int) -> Optional[float]:
    """Month-over-month change, or null when there is no baseline to compare to."""
    if previous == 0:
        return None
    return round(((current - previous) / previous) * 100, 1)


async def _count_between(db: AsyncSession, hospital_id: UUID, start, end) -> int:
    result = await db.execute(
        select(func.count(Appointment.id)).where(
            Appointment.hospital_id == hospital_id,
            Appointment.created_at >= start,
            Appointment.created_at < end,
        )
    )
    return int(result.scalar() or 0)


async def get_overview(db: AsyncSession, admin: User) -> dict:
    hospital = await _resolve_hospital(db, admin)
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    prev_month_start = (month_start - timedelta(days=1)).replace(day=1)

    # --- patients linked to this hospital
    total_patients = int(
        (
            await db.execute(
                select(func.count(func.distinct(PatientHospital.patient_id))).where(
                    PatientHospital.hospital_id == hospital.id
                )
            )
        ).scalar()
        or 0
    )
    patients_prev = int(
        (
            await db.execute(
                select(func.count(func.distinct(PatientHospital.patient_id))).where(
                    PatientHospital.hospital_id == hospital.id,
                    PatientHospital.created_at < month_start,
                )
            )
        ).scalar()
        or 0
    )

    # --- clinicians
    active_clinicians = int(
        (
            await db.execute(
                select(func.count(Clinician.id)).where(
                    Clinician.hospital_id == hospital.id,
                    Clinician.status == ClinicianStatus.ACTIVE,
                )
            )
        ).scalar()
        or 0
    )
    total_clinicians = int(
        (
            await db.execute(
                select(func.count(Clinician.id)).where(Clinician.hospital_id == hospital.id)
            )
        ).scalar()
        or 0
    )

    # --- consultations
    consultations_this_month = await _count_between(db, hospital.id, month_start, now)
    consultations_prev_month = await _count_between(db, hospital.id, prev_month_start, month_start)

    # --- revenue, from paid invoices only
    revenue_row = await db.execute(
        select(func.coalesce(func.sum(Invoice.amount), 0)).where(
            Invoice.hospital_id == hospital.id,
            Invoice.status == InvoiceStatus.PAID,
            Invoice.paid_at >= month_start,
        )
    )
    revenue_this_month = float(revenue_row.scalar() or 0)
    revenue_prev_row = await db.execute(
        select(func.coalesce(func.sum(Invoice.amount), 0)).where(
            Invoice.hospital_id == hospital.id,
            Invoice.status == InvoiceStatus.PAID,
            Invoice.paid_at >= prev_month_start,
            Invoice.paid_at < month_start,
        )
    )
    revenue_prev_month = float(revenue_prev_row.scalar() or 0)

    # --- consultations per weekday, current week
    week_start = (now - timedelta(days=now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    weekly = []
    for offset in range(7):
        day_start = week_start + timedelta(days=offset)
        day_end = day_start + timedelta(days=1)
        weekly.append(
            {
                "day": day_start.strftime("%a"),
                "count": await _count_between(db, hospital.id, day_start, day_end),
            }
        )

    # --- consultations by department
    dept_rows = await db.execute(
        select(Department.name, func.count(Appointment.id))
        .select_from(Department)
        .outerjoin(Appointment, Appointment.department_id == Department.id)
        .where(Department.hospital_id == hospital.id)
        .group_by(Department.name)
        .order_by(func.count(Appointment.id).desc())
    )
    dept_counts = [{"name": n, "count": int(c or 0)} for n, c in dept_rows.all()]
    dept_total = sum(d["count"] for d in dept_counts) or 1
    departments = [
        {**d, "percentage": round((d["count"] / dept_total) * 100, 1)} for d in dept_counts
    ]

    return {
        "hospital": {
            "id": str(hospital.id),
            "name": hospital.name,
            "code": hospital.hospital_code,
            "city": hospital.city,
            "state": hospital.state,
            "rating": float(hospital.rating) if hospital.rating is not None else None,
            "subscription_plan": hospital.subscription_plan.value
            if hospital.subscription_plan
            else None,
            "subscription_expires": hospital.subscription_expires.isoformat()
            if hospital.subscription_expires
            else None,
            "days_until_renewal": (
                (hospital.subscription_expires - date.today()).days
                if hospital.subscription_expires
                else None
            ),
        },
        "stats": {
            "total_patients": total_patients,
            "total_patients_change": _percent_change(total_patients, patients_prev),
            "active_clinicians": active_clinicians,
            "total_clinicians": total_clinicians,
            "consultations": consultations_this_month,
            "consultations_change": _percent_change(
                consultations_this_month, consultations_prev_month
            ),
            "revenue": revenue_this_month,
            "revenue_change": _percent_change(int(revenue_this_month), int(revenue_prev_month)),
            "currency": "NGN",
        },
        "weekly_consultations": weekly,
        "departments": departments,
    }


async def list_clinicians(
    db: AsyncSession, admin: User, role: Optional[str] = None, search: Optional[str] = None
) -> dict:
    hospital = await _resolve_hospital(db, admin)
    stmt = (
        select(Clinician, User)
        .join(User, User.id == Clinician.user_id)
        .where(Clinician.hospital_id == hospital.id)
    )
    if role and role.lower() in ("doctor", "nurse"):
        stmt = stmt.where(
            Clinician.role_type
            == (
                ClinicianRoleType.DOCTOR
                if role.lower() == "doctor"
                else ClinicianRoleType.NURSE
            )
        )
    if search:
        like = f"%{search}%"
        stmt = stmt.where(
            (User.first_name.ilike(like))
            | (User.last_name.ilike(like))
            | (User.email.ilike(like))
            | (Clinician.specialty.ilike(like))
        )

    rows = (await db.execute(stmt.order_by(Clinician.total_points.desc()))).all()
    return {
        "clinicians": [
            {
                "id": str(c.id),
                "name": f"{u.first_name} {u.last_name}".strip(),
                "email": u.email,
                "phone": u.phone,
                "role": c.role_type.value if c.role_type else None,
                "specialty": c.specialty,
                "years_of_experience": c.years_of_experience,
                "rating": float(c.rating) if c.rating is not None else None,
                "total_consultations": c.total_consultations,
                "points": c.total_points,
                "status": c.status.value if c.status else None,
                "is_available": c.is_available,
                "avatar_url": u.avatar_url,
            }
            for c, u in rows
        ],
        "total": len(rows),
    }


async def list_patients(
    db: AsyncSession, admin: User, search: Optional[str] = None, limit: int = 50, offset: int = 0
) -> dict:
    hospital = await _resolve_hospital(db, admin)
    base = (
        select(Patient, User)
        .join(User, User.id == Patient.user_id)
        .join(PatientHospital, PatientHospital.patient_id == Patient.id)
        .where(PatientHospital.hospital_id == hospital.id)
    )
    if search:
        like = f"%{search}%"
        base = base.where(
            (User.first_name.ilike(like))
            | (User.last_name.ilike(like))
            | (User.email.ilike(like))
        )

    total = int(
        (await db.execute(select(func.count()).select_from(base.subquery()))).scalar() or 0
    )
    rows = (
        await db.execute(base.order_by(User.first_name).limit(limit).offset(offset))
    ).all()

    return {
        "patients": [
            {
                "id": str(p.id),
                "name": f"{u.first_name} {u.last_name}".strip(),
                "email": u.email,
                "phone": u.phone,
                "gender": p.gender,
                "date_of_birth": p.date_of_birth.isoformat() if p.date_of_birth else None,
                "blood_type": p.blood_type,
                "city": p.city,
                "state": p.state,
                "preferred_language": p.preferred_language.value
                if p.preferred_language
                else None,
                "onboarding_completed": p.onboarding_completed,
                "joined": p.created_at.isoformat() if p.created_at else None,
            }
            for p, u in rows
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


async def list_appointments(
    db: AsyncSession, admin: User, status_filter: Optional[str] = None, limit: int = 50
) -> dict:
    hospital = await _resolve_hospital(db, admin)
    PatientUser = User.__table__.alias("patient_user")
    stmt = (
        select(Appointment, Patient, User)
        .join(Patient, Patient.id == Appointment.patient_id)
        .join(User, User.id == Patient.user_id)
        .where(Appointment.hospital_id == hospital.id)
    )
    if status_filter and status_filter.lower() != "all":
        try:
            stmt = stmt.where(Appointment.status == AppointmentStatus(status_filter.lower()))
        except ValueError:
            pass

    rows = (
        await db.execute(stmt.order_by(Appointment.scheduled_date.desc()).limit(limit))
    ).all()
    return {
        "appointments": [
            {
                "id": str(a.id),
                "patient_name": f"{u.first_name} {u.last_name}".strip(),
                "scheduled_date": a.scheduled_date.isoformat() if a.scheduled_date else None,
                "scheduled_time": str(a.scheduled_time) if a.scheduled_time else None,
                "duration_minutes": a.duration_minutes,
                "type": a.type.value if a.type else None,
                "status": a.status.value if a.status else None,
                "location": a.location,
                "notes": a.notes,
            }
            for a, p, u in rows
        ],
        "total": len(rows),
    }


async def get_analytics(db: AsyncSession, admin: User) -> dict:
    """Twelve months of consultation volume, plus appointment status mix."""
    hospital = await _resolve_hospital(db, admin)
    now = datetime.now(timezone.utc)

    months = []
    cursor = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    for _ in range(12):
        nxt = (cursor + timedelta(days=32)).replace(day=1)
        months.append(
            {
                "month": cursor.strftime("%b %Y"),
                "count": await _count_between(db, hospital.id, cursor, nxt),
            }
        )
        cursor = (cursor - timedelta(days=1)).replace(day=1)
    months.reverse()

    status_rows = await db.execute(
        select(Appointment.status, func.count(Appointment.id))
        .where(Appointment.hospital_id == hospital.id)
        .group_by(Appointment.status)
    )
    escalated = int(
        (
            await db.execute(
                select(func.count(EscalatedQuery.id)).where(
                    EscalatedQuery.created_at >= now - timedelta(days=30)
                )
            )
        ).scalar()
        or 0
    )

    return {
        "monthly_consultations": months,
        "appointment_status": [
            {"status": s.value if s else "unknown", "count": int(c or 0)}
            for s, c in status_rows.all()
        ],
        "escalated_queries_30d": escalated,
    }


async def list_invoices(db: AsyncSession, admin: User) -> dict:
    hospital = await _resolve_hospital(db, admin)
    rows = (
        await db.execute(
            select(Invoice)
            .where(Invoice.hospital_id == hospital.id)
            .order_by(Invoice.created_at.desc())
        )
    ).scalars().all()

    def total_for(status: InvoiceStatus) -> float:
        return float(sum(float(i.amount) for i in rows if i.status == status))

    return {
        "invoices": [
            {
                "id": str(i.id),
                "invoice_number": i.invoice_number,
                "amount": float(i.amount),
                "currency": i.currency,
                "status": i.status.value if i.status else None,
                "due_date": i.due_date.isoformat() if i.due_date else None,
                "paid_at": i.paid_at.isoformat() if i.paid_at else None,
                "description": i.description,
            }
            for i in rows
        ],
        "totals": {
            "paid": total_for(InvoiceStatus.PAID),
            "pending": total_for(InvoiceStatus.PENDING),
            "count": len(rows),
        },
    }


async def list_reports(db: AsyncSession, admin: User) -> dict:
    hospital = await _resolve_hospital(db, admin)
    rows = (
        await db.execute(
            select(Report)
            .where(Report.hospital_id == hospital.id)
            .order_by(Report.created_at.desc())
        )
    ).scalars().all()
    return {
        "reports": [
            {
                "id": str(r.id),
                "title": r.title,
                "description": r.description,
                "type": r.type.value if r.type else None,
                "status": r.status.value if r.status else None,
                "file_url": r.file_url,
                "file_size_bytes": r.file_size_bytes,
                "page_count": r.page_count,
                "summary": r.summary,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ],
        "total": len(rows),
    }


async def get_settings(db: AsyncSession, admin: User) -> dict:
    hospital = await _resolve_hospital(db, admin)
    return {
        "id": str(hospital.id),
        "name": hospital.name,
        "hospital_code": hospital.hospital_code,
        "type": hospital.type.value if hospital.type else None,
        "address": hospital.address,
        "city": hospital.city,
        "state": hospital.state,
        "phone": hospital.phone,
        "email": hospital.email,
        "website": hospital.website,
        "logo_url": hospital.logo_url,
        "is_active": hospital.is_active,
        "subscription_plan": hospital.subscription_plan.value
        if hospital.subscription_plan
        else None,
        "subscription_expires": hospital.subscription_expires.isoformat()
        if hospital.subscription_expires
        else None,
    }


async def update_settings(db: AsyncSession, admin: User, payload: dict) -> dict:
    hospital = await _resolve_hospital(db, admin)
    editable = {"name", "address", "city", "state", "phone", "email", "website", "logo_url"}
    for field, value in payload.items():
        if field in editable and value is not None:
            setattr(hospital, field, value)
    await db.commit()
    await db.refresh(hospital)
    return await get_settings(db, admin)
