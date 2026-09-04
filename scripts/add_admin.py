"""
Create (or promote) a hospital administrator, without touching anything else.

seed_test_data.py deletes every row from sixteen tables before it inserts, so
it must never be pointed at a database with real data in it. This script only
adds what the /admin portal needs and is safe to re-run.

Usage:
    # DATABASE_URL is read from the environment or .env, as the app does
    python -m scripts.add_admin

    # optional overrides
    ADMIN_EMAIL=admin@yourhospital.ng ADMIN_PASSWORD='...' python -m scripts.add_admin

If the user already exists it is promoted to ADMIN and linked to a hospital;
its password is only changed when ADMIN_PASSWORD is explicitly set.
"""

import asyncio
import os
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.auth_service import hash_password
from src.common.database.database import async_session
from src.models.models import (
    Clinician,
    ClinicianRoleType,
    ClinicianStatus,
    Hospital,
    User,
    UserRole,
)

EMAIL = os.environ.get("ADMIN_EMAIL", "admin@test.com")
PASSWORD = os.environ.get("ADMIN_PASSWORD")  # None means "leave existing password alone"
FIRST_NAME = os.environ.get("ADMIN_FIRST_NAME", "Folake")
LAST_NAME = os.environ.get("ADMIN_LAST_NAME", "Adewale")


async def run(db: AsyncSession) -> None:
    hospital = (await db.execute(select(Hospital).limit(1))).scalars().first()
    if hospital is None:
        raise SystemExit(
            "No hospital exists yet. The admin endpoints report on a hospital, "
            "so create one before running this."
        )

    user = (await db.execute(select(User).where(User.email == EMAIL))).scalars().first()

    if user is None:
        if not PASSWORD:
            raise SystemExit(
                f"{EMAIL} does not exist yet, so ADMIN_PASSWORD must be set to create it."
            )
        user = User(
            email=EMAIL,
            password_hash=hash_password(PASSWORD),
            role=UserRole.ADMIN,
            first_name=FIRST_NAME,
            last_name=LAST_NAME,
            email_verified=True,
            is_active=True,
        )
        db.add(user)
        await db.flush()
        print(f"created {EMAIL}")
    else:
        user.role = UserRole.ADMIN
        user.is_active = True
        user.email_verified = True
        if PASSWORD:
            user.password_hash = hash_password(PASSWORD)
            print(f"promoted {EMAIL} to ADMIN and reset its password")
        else:
            print(f"promoted {EMAIL} to ADMIN (password unchanged)")

    # The admin endpoints resolve which hospital to report on through the
    # Clinician row, so make sure one exists and points somewhere.
    clinician = (
        await db.execute(select(Clinician).where(Clinician.user_id == user.id))
    ).scalars().first()

    if clinician is None:
        db.add(
            Clinician(
                user_id=user.id,
                hospital_id=hospital.id,
                role_type=ClinicianRoleType.DOCTOR,
                specialty="Hospital Administration",
                bio="Hospital administrator overseeing clinical operations.",
                rating=Decimal("0.0"),
                total_consultations=0,
                total_points=0,
                status=ClinicianStatus.ACTIVE,
                is_available=False,
            )
        )
        print(f"linked to hospital: {hospital.name}")
    elif clinician.hospital_id is None:
        clinician.hospital_id = hospital.id
        print(f"linked existing clinician record to: {hospital.name}")
    else:
        print(f"already linked to hospital: {hospital.name}")

    await db.commit()
    print("done. Nothing else in the database was modified.")


async def main() -> None:
    async with async_session() as db:
        await run(db)


if __name__ == "__main__":
    asyncio.run(main())
