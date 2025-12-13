# scripts/seed_database.py
"""
Comprehensive database seed script for Kliniq API testing.
Creates sample data for all models with realistic Nigerian data.

Usage:
    python -m scripts.seed_database
    
Options:
    --clear     Clear existing test data before seeding
"""

import asyncio
import argparse
from datetime import date, time, datetime, timedelta
import random
from decimal import Decimal
from typing import List
import uuid

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.database.database import async_session
from src.models.models import (
    User, UserRole, Patient, Clinician, ClinicianRoleType, ClinicianStatus,
    Hospital, HospitalType, SubscriptionPlan, Department, PatientHospital,
    AppointmentRequest, Appointment, AppointmentType, AppointmentStatus,
    RequestStatus, UrgencyLevel, Recording, RecordingStatus,
    MedicalHistory, MedicalHistoryType, TriageCase, TriageStatus, TriageUrgency,
    EscalatedQuery, EscalatedQueryStatus, ClinicianPoints,
    Invoice, InvoiceStatus, Report, ReportType, ReportStatus,
    Conversation, Message, MessageType, Notification, NotificationType,
    PreferredLanguage
)
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


# ============================================================================
# SAMPLE DATA - Nigerian Context
# ============================================================================

NIGERIAN_FIRST_NAMES = [
    "Oluwaseun", "Adaeze", "Chukwuemeka", "Fatima", "Olumide",
    "Ngozi", "Ibrahim", "Folake", "Emeka", "Amina",
    "Tunde", "Chioma", "Yakubu", "Yetunde", "Obinna",
    "Aisha", "Kayode", "Nneka", "Musa", "Blessing"
]

NIGERIAN_LAST_NAMES = [
    "Adeyemi", "Okonkwo", "Bello", "Okafor", "Adeleke",
    "Eze", "Mohammed", "Nnamdi", "Abdullahi", "Ogundimu",
    "Ikenna", "Abubakar", "Olumide", "Okorie", "Suleiman",
    "Ogundipe", "Chukwu", "Yusuf", "Adebayo", "Ugochukwu"
]

NIGERIAN_CITIES = [
    ("Lagos", "Lagos"),
    ("Abuja", "FCT"),
    ("Kano", "Kano"),
    ("Ibadan", "Oyo"),
    ("Port Harcourt", "Rivers"),
    ("Benin City", "Edo"),
    ("Enugu", "Enugu"),
    ("Kaduna", "Kaduna"),
    ("Calabar", "Cross River"),
    ("Jos", "Plateau")
]

HOSPITALS_DATA = [
    ("Lagos University Teaching Hospital", HospitalType.TEACHING, "Idi-Araba, Surulere", "Lagos", "Lagos"),
    ("National Hospital Abuja", HospitalType.FEDERAL, "Plot 132, Central District", "Abuja", "FCT"),
    ("Reddington Hospital", HospitalType.PRIVATE, "12 Idowu Martins Street, VI", "Lagos", "Lagos"),
    ("University of Nigeria Teaching Hospital", HospitalType.TEACHING, "Ituku-Ozalla", "Enugu", "Enugu"),
    ("St. Nicholas Hospital", HospitalType.PRIVATE, "57 Campbell Street, Lagos Island", "Lagos", "Lagos"),
    ("Aminu Kano Teaching Hospital", HospitalType.TEACHING, "Zaria Road", "Kano", "Kano"),
    ("Cedarcrest Hospitals", HospitalType.PRIVATE, "1 Keji Ogundare Street, GRA", "Abuja", "FCT"),
    ("University College Hospital", HospitalType.TEACHING, "Queen Elizabeth Road", "Ibadan", "Oyo"),
    ("EKO Hospital", HospitalType.PRIVATE, "31 Mobolaji Bank Anthony Way", "Lagos", "Lagos"),
    ("Jos University Teaching Hospital", HospitalType.TEACHING, "PMB 2067", "Jos", "Plateau")
]

DEPARTMENTS = [
    "General Medicine",
    "Pediatrics", 
    "Obstetrics & Gynecology",
    "Surgery",
    "Orthopedics",
    "Cardiology",
    "Neurology",
    "Dermatology",
    "Psychiatry",
    "Ophthalmology",
    "ENT",
    "Emergency Medicine"
]

SPECIALTIES = [
    "General Practice",
    "Internal Medicine",
    "Pediatrics",
    "Cardiology",
    "Orthopedics",
    "Obstetrics & Gynecology",
    "Neurology",
    "Dermatology",
    "Psychiatry",
    "Surgery"
]

BLOOD_TYPES = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]

COMMON_SYMPTOMS = [
    "Persistent headache for the past 3 days",
    "Fever and body aches",
    "Abdominal pain and nausea",
    "Difficulty breathing",
    "Chest pain during physical activity",
    "Skin rash and itching",
    "Joint pain and stiffness",
    "Persistent cough for over a week",
    "Dizziness and fatigue",
    "Eye irritation and blurred vision"
]


# ============================================================================
# SEED FUNCTIONS
# ============================================================================

async def create_hospitals(session: AsyncSession) -> List[Hospital]:
    """Create sample hospitals"""
    hospitals = []
    for idx, (name, h_type, address, city, state) in enumerate(HOSPITALS_DATA, 1):
        # Generate hospital code like HOSP-LUTH-001
        code_name = ''.join(word[0:4].upper() for word in name.split()[:2])
        hospital_code = f"HOSP-{code_name}-{idx:03d}"
        
        hospital = Hospital(
            hospital_code=hospital_code,
            name=name,
            type=h_type,
            address=address,
            city=city,
            state=state,
            phone=f"+234 {random.randint(700, 909)} {random.randint(100, 999)} {random.randint(1000, 9999)}",
            email=f"info@{name.lower().replace(' ', '').replace('.', '')[:15]}.org.ng",
            rating=Decimal(str(round(random.uniform(3.5, 4.9), 1))),
            subscription_plan=random.choice(list(SubscriptionPlan)),
            subscription_expires=date.today() + timedelta(days=random.randint(30, 365)),
            is_active=True
        )
        session.add(hospital)
        hospitals.append(hospital)
    
    await session.flush()
    print(f"✓ Created {len(hospitals)} hospitals")
    return hospitals


async def create_departments(session: AsyncSession, hospitals: List[Hospital]) -> List[Department]:
    """Create departments for each hospital"""
    departments = []
    for hospital in hospitals:
        # Each hospital gets 4-8 random departments
        hospital_depts = random.sample(DEPARTMENTS, random.randint(4, 8))
        for dept_name in hospital_depts:
            dept = Department(
                hospital_id=hospital.id,
                name=dept_name,
                description=f"{dept_name} department providing comprehensive healthcare services.",
                is_active=True
            )
            session.add(dept)
            departments.append(dept)
    
    await session.flush()
    print(f"✓ Created {len(departments)} departments")
    return departments


async def create_admin_users(session: AsyncSession) -> List[User]:
    """Create admin users"""
    admins = []
    admin_data = [
        ("Admin", "Kliniq", "admin@kliniq.ng"),
        ("System", "Administrator", "system@kliniq.ng"),
    ]
    
    for first_name, last_name, email in admin_data:
        admin = User(
            email=email,
            password_hash=hash_password("Admin@123"),
            role=UserRole.ADMIN,
            first_name=first_name,
            last_name=last_name,
            phone=f"+234 {random.randint(800, 909)} {random.randint(100, 999)} {random.randint(1000, 9999)}",
            email_verified=True,
            is_active=True
        )
        session.add(admin)
        admins.append(admin)
    
    await session.flush()
    print(f"✓ Created {len(admins)} admin users")
    return admins


async def create_clinicians(
    session: AsyncSession, 
    hospitals: List[Hospital]
) -> tuple[List[User], List[Clinician]]:
    """Create clinician users and profiles"""
    users = []
    clinicians = []
    
    # Create 20 doctors and 15 nurses
    for i in range(35):
        first_name = random.choice(NIGERIAN_FIRST_NAMES)
        last_name = random.choice(NIGERIAN_LAST_NAMES)
        role_type = ClinicianRoleType.DOCTOR if i < 20 else ClinicianRoleType.NURSE
        
        # Create user
        user = User(
            email=f"{first_name.lower()}.{last_name.lower()}{i}@kliniq.ng",
            password_hash=hash_password("Clinician@123"),
            role=UserRole.CLINICIAN,
            first_name=first_name,
            last_name=last_name,
            phone=f"+234 {random.randint(700, 909)} {random.randint(100, 999)} {random.randint(1000, 9999)}",
            email_verified=True,
            is_active=True
        )
        session.add(user)
        await session.flush()
        users.append(user)
        
        # Create clinician profile
        clinician = Clinician(
            user_id=user.id,
            hospital_id=random.choice(hospitals).id,
            role_type=role_type,
            specialty=random.choice(SPECIALTIES) if role_type == ClinicianRoleType.DOCTOR else None,
            license_number=f"{'MDC' if role_type == ClinicianRoleType.DOCTOR else 'NRC'}{random.randint(10000, 99999)}",
            years_of_experience=random.randint(2, 25),
            bio=f"Experienced {role_type.value} dedicated to providing quality healthcare.",
            rating=Decimal(str(round(random.uniform(3.5, 5.0), 1))),
            total_consultations=random.randint(50, 500),
            total_points=random.randint(100, 5000),
            status=random.choice(list(ClinicianStatus)),
            is_available=random.choice([True, True, True, False])  # 75% available
        )
        session.add(clinician)
        clinicians.append(clinician)
    
    await session.flush()
    print(f"✓ Created {len(clinicians)} clinicians (20 doctors, 15 nurses)")
    return users, clinicians


async def create_patients(session: AsyncSession) -> tuple[List[User], List[Patient]]:
    """Create patient users and profiles"""
    users = []
    patients = []
    
    for i in range(30):
        # First patient has fixed name for predictable test credentials
        if i == 0:
            first_name = "Test"
            last_name = "Patient"
        else:
            first_name = random.choice(NIGERIAN_FIRST_NAMES)
            last_name = random.choice(NIGERIAN_LAST_NAMES)
        city, state = random.choice(NIGERIAN_CITIES)
        
        # Create user
        user = User(
            email=f"{first_name.lower()}.{last_name.lower()}{i}@gmail.com",
            password_hash=hash_password("Patient@123"),
            role=UserRole.PATIENT,
            first_name=first_name,
            last_name=last_name,
            phone=f"+234 {random.randint(700, 909)} {random.randint(100, 999)} {random.randint(1000, 9999)}",
            email_verified=True,
            is_active=True
        )
        session.add(user)
        await session.flush()
        users.append(user)
        
        # Create patient profile
        patient = Patient(
            user_id=user.id,
            date_of_birth=date.today() - timedelta(days=365 * random.randint(18, 65)),
            gender=random.choice(["Male", "Female"]),
            blood_type=random.choice(BLOOD_TYPES),
            allergies=random.choice([None, "Penicillin", "Peanuts", "Dust", "None known"]),
            address=f"{random.randint(1, 100)} {random.choice(['Adeleke', 'Ahmadu Bello', 'Obafemi Awolowo', 'Herbert Macaulay'])} Street",
            city=city,
            state=state,
            emergency_contact_name=f"{random.choice(NIGERIAN_FIRST_NAMES)} {random.choice(NIGERIAN_LAST_NAMES)}",
            emergency_contact_phone=f"+234 {random.randint(700, 909)} {random.randint(100, 999)} {random.randint(1000, 9999)}",
            preferred_language=random.choice(list(PreferredLanguage)),
            onboarding_completed=random.choice([True, True, True, False])  # 75% completed
        )
        session.add(patient)
        patients.append(patient)
    
    await session.flush()
    print(f"✓ Created {len(patients)} patients")
    return users, patients


async def link_patients_to_hospitals(
    session: AsyncSession, 
    patients: List[Patient], 
    hospitals: List[Hospital]
) -> List[PatientHospital]:
    """Link patients to hospitals"""
    links = []
    for patient in patients:
        # Each patient linked to 1-3 hospitals
        patient_hospitals = random.sample(hospitals, random.randint(1, 3))
        for hospital in patient_hospitals:
            link = PatientHospital(
                patient_id=patient.id,
                hospital_id=hospital.id,
                total_visits=random.randint(0, 20)
            )
            session.add(link)
            links.append(link)
    
    await session.flush()
    print(f"✓ Created {len(links)} patient-hospital links")
    return links


async def create_appointments(
    session: AsyncSession,
    patients: List[Patient],
    clinicians: List[Clinician],
    hospitals: List[Hospital],
    departments: List[Department]
) -> List[Appointment]:
    """Create sample appointments"""
    appointments = []
    doctors = [c for c in clinicians if c.role_type == ClinicianRoleType.DOCTOR]
    
    for patient in patients:
        # Each patient has 1-5 appointments
        for _ in range(random.randint(1, 5)):
            doctor = random.choice(doctors)
            hospital = random.choice(hospitals)
            hospital_depts = [d for d in departments if d.hospital_id == hospital.id]
            dept = random.choice(hospital_depts) if hospital_depts else None
            
            # Random date between 30 days ago and 30 days ahead
            days_offset = random.randint(-30, 30)
            scheduled_date = date.today() + timedelta(days=days_offset)
            
            # Determine status based on date
            if days_offset < -7:
                status = random.choice([AppointmentStatus.COMPLETED, AppointmentStatus.NO_SHOW])
            elif days_offset < 0:
                status = AppointmentStatus.COMPLETED
            elif days_offset == 0:
                status = random.choice([AppointmentStatus.IN_PROGRESS, AppointmentStatus.UPCOMING])
            else:
                status = AppointmentStatus.UPCOMING
            
            appointment = Appointment(
                patient_id=patient.id,
                clinician_id=doctor.id,
                hospital_id=hospital.id,
                department_id=dept.id if dept else None,
                scheduled_date=scheduled_date,
                scheduled_time=time(random.randint(8, 17), random.choice([0, 30])),
                duration_minutes=random.choice([15, 30, 45, 60]),
                type=random.choice(list(AppointmentType)),
                status=status,
                notes="Routine consultation" if random.random() > 0.5 else None
            )
            session.add(appointment)
            appointments.append(appointment)
    
    await session.flush()
    print(f"✓ Created {len(appointments)} appointments")
    return appointments


async def create_medical_history(
    session: AsyncSession,
    patients: List[Patient],
    clinicians: List[Clinician]
) -> List[MedicalHistory]:
    """Create medical history records"""
    records = []
    doctors = [c for c in clinicians if c.role_type == ClinicianRoleType.DOCTOR]
    
    medical_titles = {
        MedicalHistoryType.CONSULTATION: ["General Checkup", "Follow-up Visit", "Specialist Consultation"],
        MedicalHistoryType.PRESCRIPTION: ["Antibiotics Prescription", "Pain Management", "Chronic Condition Medication"],
        MedicalHistoryType.TEST: ["Blood Test Results", "X-Ray Report", "MRI Scan", "ECG Results"],
        MedicalHistoryType.DIAGNOSIS: ["Hypertension Diagnosis", "Diabetes Type 2", "Allergic Rhinitis"]
    }
    
    for patient in patients[:20]:  # First 20 patients have history
        for _ in range(random.randint(2, 6)):
            record_type = random.choice(list(MedicalHistoryType))
            record = MedicalHistory(
                patient_id=patient.id,
                clinician_id=random.choice(doctors).id,
                type=record_type,
                title=random.choice(medical_titles[record_type]),
                description="Medical record details and notes.",
                date=date.today() - timedelta(days=random.randint(1, 365)),
                status=random.choice(["Active", "Resolved", "Ongoing"])
            )
            session.add(record)
            records.append(record)
    
    await session.flush()
    print(f"✓ Created {len(records)} medical history records")
    return records


async def create_triage_cases(
    session: AsyncSession,
    patients: List[Patient],
    clinicians: List[Clinician]
) -> List[TriageCase]:
    """Create triage cases"""
    cases = []
    nurses = [c for c in clinicians if c.role_type == ClinicianRoleType.NURSE]
    doctors = [c for c in clinicians if c.role_type == ClinicianRoleType.DOCTOR]
    
    for patient in patients[:15]:  # First 15 patients have triage cases
        triage = TriageCase(
            patient_id=patient.id,
            symptoms=random.choice(COMMON_SYMPTOMS),
            duration=random.choice(["1-2 days", "3-5 days", "1 week", "Over a week"]),
            urgency=random.choice(list(TriageUrgency)),
            language=random.choice(list(PreferredLanguage)),
            status=random.choice(list(TriageStatus)),
            ai_summary="AI-generated symptom analysis and recommendations.",
            nurse_notes="Initial assessment completed." if random.random() > 0.5 else None,
            reviewed_by=random.choice(nurses).id if random.random() > 0.3 else None,
            escalated_to=random.choice(doctors).id if random.random() > 0.7 else None
        )
        session.add(triage)
        cases.append(triage)
    
    await session.flush()
    print(f"✓ Created {len(cases)} triage cases")
    return cases


async def create_invoices(
    session: AsyncSession,
    hospitals: List[Hospital]
) -> List[Invoice]:
    """Create sample invoices"""
    invoices = []
    
    for hospital in hospitals:
        # Each hospital has 2-5 invoices
        for i in range(random.randint(2, 5)):
            days_ago = random.randint(-60, 30)
            invoice_date = date.today() + timedelta(days=days_ago)
            
            if days_ago < -30:
                status = random.choice([InvoiceStatus.PAID, InvoiceStatus.OVERDUE])
            elif days_ago < 0:
                status = random.choice([InvoiceStatus.PAID, InvoiceStatus.PENDING])
            else:
                status = InvoiceStatus.PENDING
            
            invoice = Invoice(
                invoice_number=f"INV-{hospital.name[:3].upper()}-{datetime.now().year}-{random.randint(1000, 9999)}",
                hospital_id=hospital.id,
                amount=Decimal(str(random.randint(50000, 500000))),
                currency="NGN",
                status=status,
                due_date=invoice_date + timedelta(days=30),
                paid_at=datetime.now() if status == InvoiceStatus.PAID else None,
                description=f"Monthly subscription - {random.choice(['Basic', 'Professional', 'Enterprise'])} Plan"
            )
            session.add(invoice)
            invoices.append(invoice)
    
    await session.flush()
    print(f"✓ Created {len(invoices)} invoices")
    return invoices


async def create_notifications(
    session: AsyncSession,
    patient_users: List[User],
    clinician_users: List[User]
) -> List[Notification]:
    """Create sample notifications"""
    notifications = []
    
    notification_templates = [
        (NotificationType.APPOINTMENT, "Appointment Reminder", "Your appointment is scheduled for tomorrow at 10:00 AM"),
        (NotificationType.PRESCRIPTION, "Prescription Ready", "Your prescription has been prepared and is ready for pickup"),
        (NotificationType.RESULT, "Test Results Available", "Your recent test results are now available for review"),
        (NotificationType.SYSTEM, "Profile Update", "Please complete your profile to access all features"),
    ]
    
    all_users = patient_users + clinician_users
    for user in all_users:
        # Each user has 1-4 notifications
        for _ in range(random.randint(1, 4)):
            n_type, title, message = random.choice(notification_templates)
            notification = Notification(
                user_id=user.id,
                title=title,
                message=message,
                type=n_type,
                is_read=random.choice([True, False])
            )
            session.add(notification)
            notifications.append(notification)
    
    await session.flush()
    print(f"✓ Created {len(notifications)} notifications")
    return notifications


async def clear_database(session: AsyncSession):
    """Clear all test data from database"""
    print("\n🗑️  Clearing existing data...")
    
    # Delete in reverse order of dependencies
    tables = [
        Notification, Message, Conversation,
        Report, Invoice, ClinicianPoints,
        EscalatedQuery, TriageCase,
        MedicalHistory, Recording,
        Appointment, AppointmentRequest,
        PatientHospital, Department,
        Clinician, Patient,
        Hospital, User
    ]
    
    for table in tables:
        await session.execute(delete(table))
    
    await session.commit()
    print("✓ Database cleared")


async def seed_database(clear: bool = False):
    """Main seeding function"""
    print("\n" + "=" * 60)
    print("🌱 KLINIQ DATABASE SEEDER")
    print("=" * 60 + "\n")
    
    async with async_session() as session:
        try:
            if clear:
                await clear_database(session)
            
            print("📦 Creating seed data...\n")
            
            # Create in order of dependencies
            hospitals = await create_hospitals(session)
            departments = await create_departments(session, hospitals)
            admins = await create_admin_users(session)
            clinician_users, clinicians = await create_clinicians(session, hospitals)
            patient_users, patients = await create_patients(session)
            await link_patients_to_hospitals(session, patients, hospitals)
            appointments = await create_appointments(session, patients, clinicians, hospitals, departments)
            await create_medical_history(session, patients, clinicians)
            await create_triage_cases(session, patients, clinicians)
            await create_invoices(session, hospitals)
            await create_notifications(session, patient_users, clinician_users)
            
            await session.commit()
            
            print("\n" + "=" * 60)
            print("✅ DATABASE SEEDING COMPLETE!")
            print("=" * 60)
            print("\n📋 Test Credentials:")
            print("-" * 40)
            print("Admin:     admin@kliniq.ng / Admin@123")
            print("Clinician: oluwaseun.adeyemi0@kliniq.ng / Clinician@123")
            print("Patient:   test.patient0@gmail.com / Patient@123")
            print("-" * 40 + "\n")
            
        except Exception as e:
            await session.rollback()
            print(f"\n❌ Error during seeding: {e}")
            raise


def main():
    parser = argparse.ArgumentParser(description="Seed Kliniq database with test data")
    parser.add_argument("--clear", action="store_true", help="Clear existing data before seeding")
    args = parser.parse_args()
    
    asyncio.run(seed_database(clear=args.clear))


if __name__ == "__main__":
    main()
