# scripts/seed_test_data.py
"""
Creative seed script for Kliniq testing.
Creates one patient, one nurse, one doctor with rich, interconnected data.

Characters:
- PATIENT: Adebayo "Dayo" Ogundimu - A 34-year-old Lagos businessman dealing with hypertension
- NURSE: Ngozi Eze - A dedicated triage nurse at Lagos Teaching Hospital  
- DOCTOR: Dr. Chukwuemeka "Emeka" Adeyemi - Cardiologist specializing in hypertension

Run: python -m scripts.seed_test_data
"""

import asyncio
import uuid
from datetime import datetime, date, time, timedelta, timezone
from decimal import Decimal

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.database.database import get_db_session, async_session
from src.auth.auth_service import hash_password
from src.models.models import (
    User, Patient, Clinician, Hospital, Department, PatientHospital,
    Appointment, AppointmentRequest, Recording, MedicalHistory, HealthVitals,
    TriageCase, TriageChat, EscalatedQuery, ClinicianPoints, Notification,
    UserRole, ClinicianRoleType, ClinicianStatus, HospitalType, SubscriptionPlan,
    AppointmentType, AppointmentStatus, RequestStatus, RecordingStatus,
    MedicalHistoryType, TriageStatus, TriageUrgency, EscalatedQueryStatus,
    PreferredLanguage, NotificationType, UrgencyLevel
)


# =============================================================================
# CONSTANTS - Test Credentials
# =============================================================================

TEST_PASSWORD = "Test1234!"  # Same password for all test users
HASHED_PASSWORD = None  # Will be set in main()


# =============================================================================
# CHARACTER BACKSTORIES
# =============================================================================

"""
ADEBAYO "DAYO" OGUNDIMU (Patient)
- 34 years old, Lagos businessman running an import/export company
- Discovered high blood pressure during routine checkup 3 months ago
- Speaks Yoruba primarily, English as second language
- Worried about his health affecting his business
- His father died of heart disease at 52, so he's taking this seriously
- Started using Kliniq to track his condition and stay connected with doctors

NGOZI EZE (Nurse)
- 28 years old, from Enugu, trained at LUTH
- 5 years of nursing experience, specializes in triage
- Known for her calm demeanor with anxious patients
- Uses traditional wisdom alongside modern medicine
- Working toward becoming a nurse practitioner

DR. CHUKWUEMEKA "EMEKA" ADEYEMI (Doctor)
- 42 years old, cardiologist trained in London
- 15 years of experience, consultant at LUTH
- Passionate about preventive cardiology in Nigeria
- Believes in patient education and lifestyle changes
- Has a reputation for thorough, patient-centered care
"""


async def clear_existing_data(db: AsyncSession):
    """Clear all test data (if needed for re-seeding)."""
    print("🧹 Clearing existing data...")
    
    # Delete in reverse order of dependencies
    tables_to_clear = [
        ClinicianPoints,
        Notification,
        EscalatedQuery,
        TriageChat,
        TriageCase,
        HealthVitals,
        MedicalHistory,
        Recording,
        Appointment,
        AppointmentRequest,
        PatientHospital,
        Department,
        Clinician,
        Patient,
        Hospital,
        User,
    ]
    
    for table in tables_to_clear:
        await db.execute(delete(table))
    
    await db.commit()
    print("✅ Data cleared")


async def seed_all_data(db: AsyncSession):
    """Main seeding function."""
    global HASHED_PASSWORD
    HASHED_PASSWORD = hash_password(TEST_PASSWORD)
    
    print("\n🌱 Starting Kliniq Test Data Seed")
    print("=" * 50)
    
    # Create all entities
    hospital = await create_hospital(db)
    department = await create_department(db, hospital)
    
    patient_user, patient = await create_patient(db)
    nurse_user, nurse = await create_nurse(db, hospital)
    doctor_user, doctor = await create_doctor(db, hospital, department)
    
    await link_patient_to_hospital(db, patient, hospital)
    
    # Create interconnected data
    await create_appointments(db, patient, doctor, hospital)
    await create_recordings(db, patient, doctor)
    await create_medical_history(db, patient, doctor)
    await create_health_vitals(db, patient, nurse)
    await create_triage_cases(db, patient, nurse, doctor)
    await create_escalated_queries(db, patient, nurse, doctor)
    await create_clinician_points(db, nurse, doctor)
    await create_notifications(db, patient_user, nurse_user, doctor_user)
    
    await db.commit()
    
    print("\n" + "=" * 50)
    print("✅ Seed complete! Test credentials:")
    print(f"   Patient: dayo@test.com / {TEST_PASSWORD}")
    print(f"   Nurse:   ngozi@test.com / {TEST_PASSWORD}")
    print(f"   Doctor:  emeka@test.com / {TEST_PASSWORD}")
    print("=" * 50 + "\n")


# =============================================================================
# HOSPITAL & DEPARTMENTS
# =============================================================================

async def create_hospital(db: AsyncSession) -> Hospital:
    """Lagos University Teaching Hospital."""
    print("🏥 Creating hospital...")
    
    hospital = Hospital(
        hospital_code="LUTH-001",
        name="Lagos University Teaching Hospital",
        type=HospitalType.TEACHING,
        address="Ishaga Road, Idi-Araba",
        city="Lagos",
        state="Lagos",
        phone="+234 812 345 6789",
        email="info@luth.gov.ng",
        website="https://luth.gov.ng",
        rating=Decimal("4.5"),
        subscription_plan=SubscriptionPlan.ENTERPRISE,
        subscription_expires=date.today() + timedelta(days=365),
        is_active=True
    )
    db.add(hospital)
    await db.flush()
    return hospital


async def create_department(db: AsyncSession, hospital: Hospital) -> Department:
    """Cardiology department."""
    print("🏢 Creating department...")
    
    dept = Department(
        hospital_id=hospital.id,
        name="Cardiology",
        description="Heart and cardiovascular disease treatment and prevention",
        is_active=True
    )
    db.add(dept)
    await db.flush()
    return dept


# =============================================================================
# USERS & PROFILES
# =============================================================================

async def create_patient(db: AsyncSession) -> tuple[User, Patient]:
    """Create Adebayo 'Dayo' Ogundimu - our test patient."""
    print("👤 Creating patient: Adebayo Ogundimu...")
    
    user = User(
        email="dayo@test.com",
        password_hash=HASHED_PASSWORD,
        role=UserRole.PATIENT,
        first_name="Adebayo",
        last_name="Ogundimu",
        phone="+234 803 456 7890",
        email_verified=True,
        is_active=True,
        last_login=datetime.now(timezone.utc)
    )
    db.add(user)
    await db.flush()
    
    patient = Patient(
        user_id=user.id,
        date_of_birth=date(1990, 3, 15),
        gender="Male",
        blood_type="O+",
        allergies="Penicillin",
        address="15 Admiralty Way, Lekki Phase 1",
        city="Lagos",
        state="Lagos",
        emergency_contact_name="Folake Ogundimu",
        emergency_contact_phone="+234 805 123 4567",
        preferred_language=PreferredLanguage.YORUBA,
        onboarding_completed=True
    )
    db.add(patient)
    await db.flush()
    
    return user, patient


async def create_nurse(db: AsyncSession, hospital: Hospital) -> tuple[User, Clinician]:
    """Create Ngozi Eze - our test nurse."""
    print("👩‍⚕️ Creating nurse: Ngozi Eze...")
    
    user = User(
        email="ngozi@test.com",
        password_hash=HASHED_PASSWORD,
        role=UserRole.CLINICIAN,
        first_name="Ngozi",
        last_name="Eze",
        phone="+234 806 789 0123",
        email_verified=True,
        is_active=True,
        last_login=datetime.now(timezone.utc)
    )
    db.add(user)
    await db.flush()
    
    clinician = Clinician(
        user_id=user.id,
        hospital_id=hospital.id,
        role_type=ClinicianRoleType.NURSE,
        license_number="NMC-LAG-2019-0456",
        years_of_experience=5,
        bio="Dedicated triage nurse with 5 years experience at LUTH. Certified in emergency nursing and cardiac care. Known for my patient, thorough approach to symptom assessment. I believe in combining modern medicine with our cultural understanding of health. Working toward becoming a certified nurse practitioner.",
        rating=Decimal("4.8"),
        total_consultations=892,
        total_points=4250,
        status=ClinicianStatus.ACTIVE,
        is_available=True
    )
    db.add(clinician)
    await db.flush()
    
    return user, clinician


async def create_doctor(db: AsyncSession, hospital: Hospital, department: Department) -> tuple[User, Clinician]:
    """Create Dr. Chukwuemeka 'Emeka' Adeyemi - our test doctor."""
    print("👨‍⚕️ Creating doctor: Dr. Emeka Adeyemi...")
    
    user = User(
        email="emeka@test.com",
        password_hash=HASHED_PASSWORD,
        role=UserRole.CLINICIAN,
        first_name="Chukwuemeka",
        last_name="Adeyemi",
        phone="+234 809 012 3456",
        email_verified=True,
        is_active=True,
        last_login=datetime.now(timezone.utc)
    )
    db.add(user)
    await db.flush()
    
    clinician = Clinician(
        user_id=user.id,
        hospital_id=hospital.id,
        role_type=ClinicianRoleType.DOCTOR,
        specialty="Cardiology",
        license_number="MDCN-2009-08234",
        years_of_experience=15,
        bio="Consultant Cardiologist trained at King's College London. I specialize in hypertension management and preventive cardiology. My philosophy is that the best heart disease treatment is prevention through education, lifestyle modification, and early intervention. I've treated over 5,000 patients and published research on hypertension in Nigerian populations.",
        rating=Decimal("4.9"),
        total_consultations=5234,
        total_points=12800,
        status=ClinicianStatus.ACTIVE,
        is_available=True
    )
    db.add(clinician)
    await db.flush()
    
    # Link department head
    department.head_clinician_id = clinician.id
    
    return user, clinician


async def link_patient_to_hospital(db: AsyncSession, patient: Patient, hospital: Hospital):
    """Link patient Dayo to LUTH."""
    print("🔗 Linking patient to hospital...")
    
    link = PatientHospital(
        patient_id=patient.id,
        hospital_id=hospital.id,
        linked_at=datetime.now(timezone.utc) - timedelta(days=90),
        total_visits=4
    )
    db.add(link)
    await db.flush()


# =============================================================================
# APPOINTMENTS
# =============================================================================

async def create_appointments(db: AsyncSession, patient: Patient, doctor: Clinician, hospital: Hospital):
    """Create appointment history and upcoming appointment."""
    print("📅 Creating appointments...")
    
    now = datetime.now(timezone.utc)
    
    # Past completed appointment - Initial consultation
    apt1 = Appointment(
        patient_id=patient.id,
        clinician_id=doctor.id,
        hospital_id=hospital.id,
        type=AppointmentType.IN_PERSON,
        status=AppointmentStatus.COMPLETED,
        scheduled_date=date.today() - timedelta(days=60),
        scheduled_time=time(10, 0),
        duration_minutes=45,
        notes="Initial consultation for elevated blood pressure. Patient presented with BP 150/95. Started on Amlodipine 5mg. Discussed lifestyle modifications including DASH diet, regular exercise, and stress management. Will follow up in 4 weeks."
    )
    db.add(apt1)
    
    # Past completed appointment - Follow-up
    apt2 = Appointment(
        patient_id=patient.id,
        clinician_id=doctor.id,
        hospital_id=hospital.id,
        type=AppointmentType.VIDEO,
        status=AppointmentStatus.COMPLETED,
        scheduled_date=date.today() - timedelta(days=30),
        scheduled_time=time(14, 30),
        duration_minutes=30,
        notes="4-week follow-up. BP improved to 142/90. Patient reports good medication compliance. Experiencing mild ankle swelling - monitored. Continue current regimen. Diet compliance improving. Next appointment in 4 weeks."
    )
    db.add(apt2)
    
    # Upcoming appointment
    apt3 = Appointment(
        patient_id=patient.id,
        clinician_id=doctor.id,
        hospital_id=hospital.id,
        type=AppointmentType.IN_PERSON,
        status=AppointmentStatus.UPCOMING,
        scheduled_date=date.today() + timedelta(days=5),
        scheduled_time=time(11, 0),
        duration_minutes=30,
        notes="8-week follow-up and medication review"
    )
    db.add(apt3)
    
    await db.flush()


# =============================================================================
# RECORDINGS
# =============================================================================

async def create_recordings(db: AsyncSession, patient: Patient, doctor: Clinician):
    """Create consultation recordings."""
    print("🎙️ Creating recordings...")
    
    rec1 = Recording(
        patient_id=patient.id,
        clinician_id=doctor.id,
        title="Initial Hypertension Consultation",
        file_url="https://storage.kliniq.ng/recordings/dayo-initial-consult.wav",
        duration_seconds=1620,  # 27 minutes
        status=RecordingStatus.COMPLETED,
        transcript=(
            "Dr. Adeyemi: Good morning Mr. Ogundimu. I've reviewed your test results. "
            "Your blood pressure reading of 150/95 confirms Stage 1 hypertension. "
            "But please don't worry - this is very manageable, especially since we've caught it early.\n\n"
            "Dayo: Doctor, I'm concerned because my father... he had heart problems.\n\n"
            "Dr. Adeyemi: Yes, I understand. Family history is a risk factor, but it's not destiny. "
            "The fact that you're here, taking action - that already puts you ahead. "
            "We're going to start you on a medication called Amlodipine, just 5mg once daily. "
            "But more importantly, we need to talk about lifestyle changes. How's your diet?\n\n"
            "Dayo: Honestly doctor, I eat a lot of business lunches. Plenty of fried rice, suya...\n\n"
            "Dr. Adeyemi: I understand. Let me tell you about the DASH diet..."
        )
    )
    db.add(rec1)
    
    rec2 = Recording(
        patient_id=patient.id,
        clinician_id=doctor.id,
        title="Video Follow-up Consultation",
        file_url="https://storage.kliniq.ng/recordings/dayo-followup-1.wav",
        duration_seconds=1080,  # 18 minutes
        status=RecordingStatus.COMPLETED,
        transcript=(
            "Dr. Adeyemi: Mr. Ogundimu, how are you feeling today?\n\n"
            "Dayo: Much better doctor. I've been taking the medication every morning. "
            "My wife has been helping me with the diet. Less salt, more vegetables.\n\n"
            "Dr. Adeyemi: That's excellent to hear. Your BP today is 142/90 - showing improvement. "
            "Any side effects from the medication?\n\n"
            "Dayo: My ankles swell a bit in the evening, is that normal?\n\n"
            "Dr. Adeyemi: That can happen with Amlodipine. It's usually mild. "
            "Elevating your legs in the evening can help. If it gets worse, let me know. "
            "Have you been able to exercise?\n\n"
            "Dayo: I've started walking for 30 minutes in the morning before work.\n\n"
            "Dr. Adeyemi: Wonderful! That's exactly what I recommend..."
        )
    )
    db.add(rec2)
    
    await db.flush()


# =============================================================================
# MEDICAL HISTORY
# =============================================================================

async def create_medical_history(db: AsyncSession, patient: Patient, doctor: Clinician):
    """Create medical history records."""
    print("📋 Creating medical history...")
    
    # Diagnosis
    mh1 = MedicalHistory(
        patient_id=patient.id,
        clinician_id=doctor.id,
        type=MedicalHistoryType.DIAGNOSIS,
        date=date.today() - timedelta(days=60),
        title="Essential Hypertension (Stage 1)",
        description="Initial diagnosis of Stage 1 essential hypertension following routine health screening. BP 150/95 mmHg confirmed on multiple readings. No evidence of secondary causes. Risk factors: Family history, sedentary lifestyle, high sodium diet."
    )
    db.add(mh1)
    
    # Prescription
    mh2 = MedicalHistory(
        patient_id=patient.id,
        clinician_id=doctor.id,
        type=MedicalHistoryType.PRESCRIPTION,
        date=date.today() - timedelta(days=60),
        title="Amlodipine 5mg",
        description="Calcium channel blocker for hypertension management. Take once daily in the morning with or without food. Duration: Ongoing. Refills: 5."
    )
    db.add(mh2)
    
    # Test results
    mh3 = MedicalHistory(
        patient_id=patient.id,
        clinician_id=doctor.id,
        type=MedicalHistoryType.TEST,
        date=date.today() - timedelta(days=62),
        title="Comprehensive Metabolic Panel",
        description="Baseline blood work shows normal kidney function, no diabetes, mild hyperlipidemia. Glucose: 95 mg/dL (normal), Creatinine: 0.9 mg/dL (normal), Total cholesterol: 215 mg/dL (borderline), LDL: 142 mg/dL (borderline high)."
    )
    db.add(mh3)
    
    await db.flush()


# =============================================================================
# HEALTH VITALS
# =============================================================================

async def create_health_vitals(db: AsyncSession, patient: Patient, nurse: Clinician):
    """Create health vitals tracking data."""
    print("💓 Creating health vitals...")
    
    # Series of BP readings showing improvement over time
    vitals_data = [
        {"days_ago": 60, "bp": "150/95", "hr": 82, "weight": 89.5},
        {"days_ago": 45, "bp": "146/92", "hr": 80, "weight": 88.8},
        {"days_ago": 30, "bp": "142/90", "hr": 78, "weight": 88.0},
        {"days_ago": 14, "bp": "140/88", "hr": 76, "weight": 87.2},
        {"days_ago": 7, "bp": "138/88", "hr": 75, "weight": 86.5},
        {"days_ago": 0, "bp": "136/85", "hr": 74, "weight": 86.0},
    ]
    
    for v in vitals_data:
        sys, dia = map(int, v["bp"].split("/"))
        vitals = HealthVitals(
            patient_id=patient.id,
            recorded_by=nurse.id,
            heart_rate=v["hr"],
            blood_pressure_systolic=sys,
            blood_pressure_diastolic=dia,
            temperature=36.6,
            weight=v["weight"],
            oxygen_saturation=98,
            recorded_at=datetime.now(timezone.utc) - timedelta(days=v["days_ago"])
        )
        db.add(vitals)
    
    await db.flush()


# =============================================================================
# TRIAGE CASES
# =============================================================================

async def create_triage_cases(db: AsyncSession, patient: Patient, nurse: Clinician, doctor: Clinician):
    """Create triage cases."""
    print("🏥 Creating triage cases...")
    
    # Resolved triage case
    triage1 = TriageCase(
        patient_id=patient.id,
        symptoms="Mild headache at the back of my head, feeling a bit dizzy when I stand up too fast. Started yesterday evening.",
        duration="1 day",
        urgency=TriageUrgency.MEDIUM,
        language=PreferredLanguage.ENGLISH,
        status=TriageStatus.RESOLVED,
        ai_summary="Patient reports posterior headache with orthostatic dizziness. In context of hypertension treatment, could indicate BP fluctuation. No red flags. Recommend BP monitoring and hydration.",
        nurse_notes="Advised patient to check BP at home. Readings were 132/84 - actually improved. Headache likely tension-related from work stress. Recommended rest and proper hydration. Patient satisfied with response.",
        reviewed_by=nurse.id,
        created_at=datetime.now(timezone.utc) - timedelta(days=10)
    )
    db.add(triage1)
    
    # Pending triage case (for nurse to action)
    triage2 = TriageCase(
        patient_id=patient.id,
        symptoms="Noticing that my ankles are more swollen than usual, especially in the evenings. It's been getting worse over the past 3 days. No pain, just swelling.",
        duration="3 days",
        urgency=TriageUrgency.MEDIUM,
        language=PreferredLanguage.YORUBA,
        status=TriageStatus.PENDING,
        ai_summary="Bilateral ankle edema, progressive over 3 days. Patient on Amlodipine for hypertension - peripheral edema is a known side effect. However, need to rule out worsening cardiac function. Recommend clinical assessment.",
        created_at=datetime.now(timezone.utc) - timedelta(hours=4)
    )
    db.add(triage2)
    
    # Triage chat
    chat = TriageChat(
        patient_id=patient.id,
        triage_case_id=None,  # Standalone chat
        title="Questions about my medication",
        messages=[
            {"role": "user", "content": "Good morning. Can I take my blood pressure medicine at night instead of morning?", "timestamp": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()},
            {"role": "assistant", "content": "Good morning! Many patients take Amlodipine at bedtime and this is perfectly acceptable. Some research even suggests evening dosing may be more effective for blood pressure control during sleep. However, you should discuss this change with Dr. Adeyemi to ensure it fits your treatment plan.", "timestamp": (datetime.now(timezone.utc) - timedelta(hours=2, minutes=-1)).isoformat()},
            {"role": "user", "content": "Okay thank you. Also, is it okay to eat grapefruit? I heard something about medications.", "timestamp": (datetime.now(timezone.utc) - timedelta(hours=1, minutes=50)).isoformat()},
            {"role": "assistant", "content": "Great question! Grapefruit can interact with many medications, but Amlodipine is one of the calcium channel blockers where the interaction is generally considered minor. Occasional grapefruit is likely fine, but I'd recommend not consuming large amounts daily. If you enjoy grapefruit regularly, let Dr. Adeyemi know so he can monitor your response to the medication.", "timestamp": (datetime.now(timezone.utc) - timedelta(hours=1, minutes=49)).isoformat()}
        ],
        language=PreferredLanguage.ENGLISH,
        is_active=True,
        created_at=datetime.now(timezone.utc) - timedelta(hours=2)
    )
    db.add(chat)
    
    await db.flush()


# =============================================================================
# ESCALATED QUERIES
# =============================================================================

async def create_escalated_queries(db: AsyncSession, patient: Patient, nurse: Clinician, doctor: Clinician):
    """Create escalated queries for doctor."""
    print("📨 Creating escalated queries...")
    
    # Answered query
    eq1 = EscalatedQuery(
        patient_id=patient.id,
        question="Can I stop taking my medication if my blood pressure is normal now? It's been 136/85 for the past week.",
        nurse_note="Patient has good BP control on Amlodipine 5mg. He's asking about discontinuing medication. BP trend shows consistent improvement. Please advise.",
        urgency=TriageUrgency.MEDIUM,
        status=EscalatedQueryStatus.ANSWERED,
        ai_draft="While your BP improvement is excellent, blood pressure medications typically need to be continued long-term. Stopping suddenly could cause a rebound increase. Discuss with your doctor about your options.",
        doctor_response="Mr. Ogundimu, I'm very pleased with your progress! Your BP of 136/85 is wonderful. However, this good reading is BECAUSE of the medication, not despite it. If we stop, the BP will likely rise again. The goal now is to maintain this control. At your next appointment, we can discuss whether dose reduction might be possible in the future, but for now, please continue as prescribed. You're doing great!",
        answered_by=doctor.id,
        answered_at=datetime.now(timezone.utc) - timedelta(days=3),
        created_at=datetime.now(timezone.utc) - timedelta(days=4)
    )
    db.add(eq1)
    
    # Pending query (for doctor to answer)
    eq2 = EscalatedQuery(
        patient_id=patient.id,
        question="I have a business trip to London next week. Will the cold weather affect my blood pressure? Should I bring extra medication?",
        nurse_note="Patient traveling internationally. Concerned about cold weather impact on BP and medication supply for 2-week trip. Currently well-controlled on Amlodipine 5mg.",
        urgency=TriageUrgency.LOW,
        status=EscalatedQueryStatus.PENDING,
        ai_draft="Cold weather can temporarily increase blood pressure due to vasoconstriction. For a 2-week trip, ensure you have adequate medication supply. Keep medications in carry-on luggage. Consider monitoring BP more frequently during the trip.",
        created_at=datetime.now(timezone.utc) - timedelta(hours=6)
    )
    db.add(eq2)
    
    await db.flush()


# =============================================================================
# CLINICIAN POINTS
# =============================================================================

async def create_clinician_points(db: AsyncSession, nurse: Clinician, doctor: Clinician):
    """Create points history for gamification."""
    print("🏆 Creating clinician points...")
    
    current_month = date.today().replace(day=1)
    last_month = (current_month - timedelta(days=1)).replace(day=1)
    
    # Nurse points
    nurse_actions = [
        ("Triage Verification", 5, "Verified triage for Adebayo O."),
        ("Triage Verification", 5, "Completed triage assessment"),
        ("Patient Guidance", 10, "Provided guidance on medication timing"),
        ("Note Update", 5, "Updated patient care notes"),
        ("Vital Recording", 5, "Recorded patient vitals"),
        ("Triage Verification", 5, "Quick response to patient concern"),
    ]
    
    for action, points, desc in nurse_actions:
        cp = ClinicianPoints(
            clinician_id=nurse.id,
            action=action,
            points=points,
            description=desc,
            month=current_month,
            created_at=datetime.now(timezone.utc) - timedelta(hours=len(nurse_actions) * 2)
        )
        db.add(cp)
    
    # Doctor points
    doctor_actions = [
        ("Query Response", 10, "Answered medication continuation question"),
        ("Consultation", 15, "Completed follow-up consultation"),
        ("Prescription Review", 5, "Reviewed ongoing prescriptions"),
        ("Query Response", 10, "Provided travel health guidance"),
    ]
    
    for action, points, desc in doctor_actions:
        cp = ClinicianPoints(
            clinician_id=doctor.id,
            action=action,
            points=points,
            description=desc,
            month=current_month,
            created_at=datetime.now(timezone.utc) - timedelta(hours=len(doctor_actions) * 3)
        )
        db.add(cp)
    
    await db.flush()


# =============================================================================
# NOTIFICATIONS
# =============================================================================

async def create_notifications(db: AsyncSession, patient_user: User, nurse_user: User, doctor_user: User):
    """Create notifications."""
    print("🔔 Creating notifications...")
    
    # Patient notifications
    notif1 = Notification(
        user_id=patient_user.id,
        type=NotificationType.APPOINTMENT,
        title="Upcoming Appointment",
        message="Reminder: You have an appointment with Dr. Adeyemi in 5 days at 11:00 AM.",
        is_read=False,
        created_at=datetime.now(timezone.utc) - timedelta(hours=1)
    )
    db.add(notif1)
    
    notif2 = Notification(
        user_id=patient_user.id,
        type=NotificationType.RESULT,
        title="Doctor's Response",
        message="Dr. Adeyemi has responded to your question about medication.",
        is_read=True,
        created_at=datetime.now(timezone.utc) - timedelta(days=3)
    )
    db.add(notif2)
    
    # Nurse notifications
    notif3 = Notification(
        user_id=nurse_user.id,
        type=NotificationType.SYSTEM,
        title="New Triage Case",
        message="New triage case submitted by Adebayo Ogundimu requires your attention.",
        is_read=False,
        created_at=datetime.now(timezone.utc) - timedelta(hours=4)
    )
    db.add(notif3)
    
    # Doctor notifications
    notif4 = Notification(
        user_id=doctor_user.id,
        type=NotificationType.SYSTEM,
        title="Pending Query",
        message="A patient query about travel and blood pressure is awaiting your response.",
        is_read=False,
        created_at=datetime.now(timezone.utc) - timedelta(hours=6)
    )
    db.add(notif4)
    
    await db.flush()


# =============================================================================
# MAIN
# =============================================================================

async def main():
    """Run the seed script."""
    async with async_session() as db:
        try:
            await seed_all_data(db)
        except Exception as e:
            await db.rollback()
            print(f"\n❌ Error during seeding: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
