# src/models/models.py

from typing import List
import uuid
import enum

from sqlalchemy import (
    ARRAY, JSON, Boolean, CheckConstraint, Column, Date, Float, ForeignKey, 
    Index, Integer, Numeric, String, Text, DateTime, Time,
    Enum as SAEnum, UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base, relationship, backref

Base = declarative_base()


# ============================================================================
# ENUMS
# ============================================================================

class UserRole(enum.Enum):
    PATIENT = "patient"
    CLINICIAN = "clinician"
    ADMIN = "admin"


class ClinicianRoleType(enum.Enum):
    DOCTOR = "doctor"
    NURSE = "nurse"


class ClinicianStatus(enum.Enum):
    ACTIVE = "active"
    BUSY = "busy"
    OFFLINE = "offline"


class HospitalType(enum.Enum):
    TEACHING = "teaching"
    FEDERAL = "federal"
    PRIVATE = "private"
    GENERAL = "general"


class SubscriptionPlan(enum.Enum):
    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class AppointmentType(enum.Enum):
    IN_PERSON = "in-person"
    VIDEO = "video"


class AppointmentStatus(enum.Enum):
    UPCOMING = "upcoming"
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no-show"


class RequestStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class UrgencyLevel(enum.Enum):
    LOW = "low"
    NORMAL = "normal"
    URGENT = "urgent"


class RecordingStatus(enum.Enum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class MedicalHistoryType(enum.Enum):
    CONSULTATION = "consultation"
    PRESCRIPTION = "prescription"
    TEST = "test"
    DIAGNOSIS = "diagnosis"


class TriageStatus(enum.Enum):
    PENDING = "pending"
    IN_REVIEW = "in-review"
    ESCALATED = "escalated"
    RESOLVED = "resolved"


class TriageUrgency(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class EscalatedQueryStatus(enum.Enum):
    PENDING = "pending"
    ANSWERED = "answered"


class InvoiceStatus(enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class ReportType(enum.Enum):
    PERFORMANCE = "performance"
    CLINICIAN = "clinician"
    FINANCIAL = "financial"
    SATISFACTION = "satisfaction"


class ReportStatus(enum.Enum):
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class MessageType(enum.Enum):
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    AUDIO = "audio"


class PreferredLanguage(enum.Enum):
    ENGLISH = "english"
    HAUSA = "hausa"
    IGBO = "igbo"
    YORUBA = "yoruba"


class NotificationType(enum.Enum):
    APPOINTMENT = "appointment"
    PRESCRIPTION = "prescription"
    RESULT = "result"
    SYSTEM = "system"


# ============================================================================
# USER MODELS
# ============================================================================

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(SAEnum(UserRole), nullable=False, default=UserRole.PATIENT)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    email_verified = Column(Boolean, default=False, nullable=False)
    verification_code = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role.value})>"


class Patient(Base):
    __tablename__ = "patients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String(20), nullable=True)
    blood_type = Column(String(5), nullable=True)
    allergies = Column(Text, nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    emergency_contact_name = Column(String(200), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)
    insurance_provider = Column(String(200), nullable=True)
    insurance_number = Column(String(100), nullable=True)
    preferred_language = Column(SAEnum(PreferredLanguage), nullable=True)
    onboarding_completed = Column(Boolean, default=False, nullable=False)
    notification_settings = Column(
        JSONB, 
        nullable=True, 
        default={"appointments": True, "messages": True, "reminders": True, "updates": False},
        server_default='{"appointments": true, "messages": true, "reminders": true, "updates": false}'
    )
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationship
    user = relationship("User", backref=backref("patient", uselist=False, cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<Patient(id={self.id}, user_id={self.user_id})>"


class Clinician(Base):
    __tablename__ = "clinicians"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    hospital_id = Column(UUID(as_uuid=True), ForeignKey("hospitals.id", ondelete="SET NULL"), nullable=True)
    role_type = Column(SAEnum(ClinicianRoleType), nullable=False, default=ClinicianRoleType.DOCTOR)
    specialty = Column(String(100), nullable=True)
    license_number = Column(String(100), unique=True, nullable=True)
    years_of_experience = Column(Integer, nullable=True)
    bio = Column(Text, nullable=True)
    rating = Column(Numeric(2, 1), default=0.0, nullable=False)
    total_consultations = Column(Integer, default=0, nullable=False)
    total_points = Column(Integer, default=0, nullable=False)
    status = Column(SAEnum(ClinicianStatus), default=ClinicianStatus.ACTIVE, nullable=False)
    is_available = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", backref=backref("clinician", uselist=False, cascade="all, delete-orphan"))
    hospital = relationship("Hospital", backref=backref("clinicians", lazy="dynamic"))

    def __repr__(self):
        return f"<Clinician(id={self.id}, role_type={self.role_type.value}, specialty={self.specialty})>"


# ============================================================================
# HOSPITAL MODELS
# ============================================================================

class Hospital(Base):
    __tablename__ = "hospitals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    hospital_code = Column(String(20), unique=True, nullable=False, index=True)  # e.g., HOSP-LUTH-001
    name = Column(String(255), nullable=False)
    type = Column(SAEnum(HospitalType), nullable=False, default=HospitalType.GENERAL)
    address = Column(Text, nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    website = Column(String(500), nullable=True)
    logo_url = Column(String(500), nullable=True)
    rating = Column(Numeric(2, 1), default=0.0, nullable=False)
    subscription_plan = Column(SAEnum(SubscriptionPlan), default=SubscriptionPlan.BASIC, nullable=False)
    subscription_expires = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Hospital(id={self.id}, name={self.name})>"


class Department(Base):
    __tablename__ = "departments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    hospital_id = Column(UUID(as_uuid=True), ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    head_clinician_id = Column(UUID(as_uuid=True), ForeignKey("clinicians.id", ondelete="SET NULL"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    hospital = relationship("Hospital", backref=backref("departments", lazy="dynamic", cascade="all, delete-orphan"))
    head_clinician = relationship("Clinician", backref=backref("headed_departments", lazy="dynamic"))

    __table_args__ = (
        UniqueConstraint("hospital_id", "name", name="uq_department_hospital_name"),
    )

    def __repr__(self):
        return f"<Department(id={self.id}, name={self.name})>"


class PatientHospital(Base):
    """Junction table for Patient-Hospital many-to-many relationship"""
    __tablename__ = "patient_hospitals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    hospital_id = Column(UUID(as_uuid=True), ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False)
    linked_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    total_visits = Column(Integer, default=0, nullable=False)

    # Relationships
    patient = relationship("Patient", backref=backref("linked_hospitals", lazy="dynamic", cascade="all, delete-orphan"))
    hospital = relationship("Hospital", backref=backref("linked_patients", lazy="dynamic"))

    __table_args__ = (
        UniqueConstraint("patient_id", "hospital_id", name="uq_patient_hospital"),
    )


# ============================================================================
# APPOINTMENT MODELS
# ============================================================================

class AppointmentRequest(Base):
    __tablename__ = "appointment_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    hospital_id = Column(UUID(as_uuid=True), ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False)
    department = Column(String(100), nullable=False)
    reason = Column(Text, nullable=False)
    preferred_type = Column(SAEnum(AppointmentType), nullable=False, default=AppointmentType.IN_PERSON)
    urgency = Column(SAEnum(UrgencyLevel), default=UrgencyLevel.NORMAL, nullable=False)
    status = Column(SAEnum(RequestStatus), default=RequestStatus.PENDING, nullable=False)
    rejection_reason = Column(Text, nullable=True)
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("clinicians.id", ondelete="SET NULL"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    patient = relationship("Patient", backref=backref("appointment_requests", lazy="dynamic", cascade="all, delete-orphan"))
    hospital = relationship("Hospital", backref=backref("appointment_requests", lazy="dynamic"))
    reviewer = relationship("Clinician", foreign_keys=[reviewed_by], backref=backref("reviewed_requests", lazy="dynamic"))

    def __repr__(self):
        return f"<AppointmentRequest(id={self.id}, status={self.status.value})>"


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    clinician_id = Column(UUID(as_uuid=True), ForeignKey("clinicians.id", ondelete="SET NULL"), nullable=True)
    hospital_id = Column(UUID(as_uuid=True), ForeignKey("hospitals.id", ondelete="SET NULL"), nullable=True)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    request_id = Column(UUID(as_uuid=True), ForeignKey("appointment_requests.id", ondelete="SET NULL"), nullable=True)
    scheduled_date = Column(Date, nullable=False)
    scheduled_time = Column(Time, nullable=False)
    duration_minutes = Column(Integer, default=30, nullable=False)
    type = Column(SAEnum(AppointmentType), nullable=False, default=AppointmentType.IN_PERSON)
    status = Column(SAEnum(AppointmentStatus), default=AppointmentStatus.UPCOMING, nullable=False)
    location = Column(String(200), nullable=True)
    notes = Column(Text, nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    patient = relationship("Patient", backref=backref("appointments", lazy="dynamic", cascade="all, delete-orphan"))
    clinician = relationship("Clinician", backref=backref("appointments", lazy="dynamic"))
    hospital = relationship("Hospital", backref=backref("appointments", lazy="dynamic"))
    department = relationship("Department", backref=backref("appointments", lazy="dynamic"))
    request = relationship("AppointmentRequest", backref=backref("appointment", uselist=False))

    __table_args__ = (
        Index("idx_appointments_date", "scheduled_date"),
        Index("idx_appointments_status", "status"),
    )

    def __repr__(self):
        return f"<Appointment(id={self.id}, date={self.scheduled_date}, status={self.status.value})>"


# ============================================================================
# MEDICAL RECORDS MODELS
# ============================================================================

class Recording(Base):
    __tablename__ = "recordings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    appointment_id = Column(UUID(as_uuid=True), ForeignKey("appointments.id", ondelete="SET NULL"), nullable=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    clinician_id = Column(UUID(as_uuid=True), ForeignKey("clinicians.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    duration_seconds = Column(Integer, nullable=False, default=0)
    file_size_bytes = Column(Integer, nullable=True)
    file_url = Column(String(500), nullable=True)
    transcript = Column(Text, nullable=True)
    status = Column(SAEnum(RecordingStatus), default=RecordingStatus.PROCESSING, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    appointment = relationship("Appointment", backref=backref("recordings", lazy="dynamic"))
    patient = relationship("Patient", backref=backref("recordings", lazy="dynamic", cascade="all, delete-orphan"))
    clinician = relationship("Clinician", backref=backref("recordings", lazy="dynamic"))

    def __repr__(self):
        return f"<Recording(id={self.id}, title={self.title})>"


class MedicalHistory(Base):
    __tablename__ = "medical_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    clinician_id = Column(UUID(as_uuid=True), ForeignKey("clinicians.id", ondelete="SET NULL"), nullable=True)
    type = Column(SAEnum(MedicalHistoryType), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    date = Column(Date, nullable=False)
    status = Column(String(50), nullable=True)
    attachments = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    patient = relationship("Patient", backref=backref("medical_history", lazy="dynamic", cascade="all, delete-orphan"))
    clinician = relationship("Clinician", backref=backref("medical_records", lazy="dynamic"))

    def __repr__(self):
        return f"<MedicalHistory(id={self.id}, type={self.type.value}, title={self.title})>"


class HealthVitals(Base):
    """Track patient health measurements over time."""
    __tablename__ = "health_vitals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    recorded_by = Column(UUID(as_uuid=True), ForeignKey("clinicians.id", ondelete="SET NULL"), nullable=True)
    heart_rate = Column(Integer, nullable=True)  # bpm
    blood_pressure_systolic = Column(Integer, nullable=True)  # mmHg
    blood_pressure_diastolic = Column(Integer, nullable=True)  # mmHg
    temperature = Column(Float, nullable=True)  # Celsius
    weight = Column(Float, nullable=True)  # kg
    oxygen_saturation = Column(Integer, nullable=True)  # SpO2 %
    notes = Column(Text, nullable=True)
    recorded_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    patient = relationship("Patient", backref=backref("health_vitals", lazy="dynamic", cascade="all, delete-orphan"))
    clinician = relationship("Clinician", backref=backref("recorded_vitals", lazy="dynamic"))

    __table_args__ = (
        Index("idx_health_vitals_patient", "patient_id"),
    )

    def __repr__(self):
        return f"<HealthVitals(id={self.id}, patient_id={self.patient_id})>"


# ============================================================================
# TRIAGE MODELS
# ============================================================================

class TriageCase(Base):
    __tablename__ = "triage_cases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    symptoms = Column(Text, nullable=False)
    duration = Column(String(100), nullable=True)
    urgency = Column(SAEnum(TriageUrgency), nullable=False, default=TriageUrgency.MEDIUM)
    language = Column(SAEnum(PreferredLanguage), nullable=True, default=PreferredLanguage.ENGLISH)
    status = Column(SAEnum(TriageStatus), default=TriageStatus.PENDING, nullable=False)
    ai_summary = Column(Text, nullable=True)
    nurse_notes = Column(Text, nullable=True)
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("clinicians.id", ondelete="SET NULL"), nullable=True)
    escalated_to = Column(UUID(as_uuid=True), ForeignKey("clinicians.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    patient = relationship("Patient", backref=backref("triage_cases", lazy="dynamic", cascade="all, delete-orphan"))
    reviewer = relationship("Clinician", foreign_keys=[reviewed_by], backref=backref("reviewed_triage_cases", lazy="dynamic"))
    escalation_doctor = relationship("Clinician", foreign_keys=[escalated_to], backref=backref("escalated_triage_cases", lazy="dynamic"))

    __table_args__ = (
        Index("idx_triage_status", "status"),
    )

    def __repr__(self):
        return f"<TriageCase(id={self.id}, status={self.status.value})>"


class TriageChat(Base):
    """Stores AI chat conversations for patients."""
    __tablename__ = "triage_chats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    triage_case_id = Column(UUID(as_uuid=True), ForeignKey("triage_cases.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=True)  # Auto-generated from first message
    messages = Column(JSONB, nullable=False, default=list)  # [{role, content, timestamp}]
    language = Column(SAEnum(PreferredLanguage), nullable=True, default=PreferredLanguage.ENGLISH)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    patient = relationship("Patient", backref=backref("triage_chats", lazy="dynamic", cascade="all, delete-orphan"))
    triage_case = relationship("TriageCase", backref=backref("chats", lazy="dynamic"))

    __table_args__ = (
        Index("idx_triage_chat_patient", "patient_id"),
    )

    def __repr__(self):
        return f"<TriageChat(id={self.id}, patient_id={self.patient_id})>"


class EscalatedQuery(Base):
    __tablename__ = "escalated_queries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    triage_case_id = Column(UUID(as_uuid=True), ForeignKey("triage_cases.id", ondelete="CASCADE"), nullable=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    question = Column(Text, nullable=False)
    nurse_note = Column(Text, nullable=True)
    urgency = Column(SAEnum(TriageUrgency), nullable=False, default=TriageUrgency.MEDIUM)
    status = Column(SAEnum(EscalatedQueryStatus), default=EscalatedQueryStatus.PENDING, nullable=False)
    ai_draft = Column(Text, nullable=True)
    doctor_response = Column(Text, nullable=True)
    answered_by = Column(UUID(as_uuid=True), ForeignKey("clinicians.id", ondelete="SET NULL"), nullable=True)
    answered_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    triage_case = relationship("TriageCase", backref=backref("escalated_queries", lazy="dynamic", cascade="all, delete-orphan"))
    patient = relationship("Patient", backref=backref("escalated_queries", lazy="dynamic"))
    answering_doctor = relationship("Clinician", foreign_keys=[answered_by], backref=backref("answered_queries", lazy="dynamic"))

    def __repr__(self):
        return f"<EscalatedQuery(id={self.id}, status={self.status.value})>"


# ============================================================================
# GAMIFICATION MODELS
# ============================================================================

class ClinicianPoints(Base):
    __tablename__ = "clinician_points"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    clinician_id = Column(UUID(as_uuid=True), ForeignKey("clinicians.id", ondelete="CASCADE"), nullable=False)
    action = Column(String(100), nullable=False)
    points = Column(Integer, nullable=False)
    description = Column(String(255), nullable=True)
    month = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationship
    clinician = relationship("Clinician", backref=backref("points_history", lazy="dynamic", cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<ClinicianPoints(id={self.id}, points={self.points})>"


# ============================================================================
# BILLING MODELS
# ============================================================================

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    invoice_number = Column(String(50), unique=True, nullable=False)
    hospital_id = Column(UUID(as_uuid=True), ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="NGN", nullable=False)
    status = Column(SAEnum(InvoiceStatus), default=InvoiceStatus.PENDING, nullable=False)
    due_date = Column(Date, nullable=False)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationship
    hospital = relationship("Hospital", backref=backref("invoices", lazy="dynamic", cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<Invoice(id={self.id}, number={self.invoice_number}, status={self.status.value})>"


# ============================================================================
# REPORTS MODELS
# ============================================================================

class Report(Base):
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    hospital_id = Column(UUID(as_uuid=True), ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    type = Column(SAEnum(ReportType), nullable=False)
    status = Column(SAEnum(ReportStatus), default=ReportStatus.PROCESSING, nullable=False)
    file_url = Column(String(500), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    page_count = Column(Integer, nullable=True)
    summary = Column(Text, nullable=True)
    highlights = Column(JSONB, nullable=True)
    metrics = Column(JSONB, nullable=True)
    generated_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    hospital = relationship("Hospital", backref=backref("reports", lazy="dynamic", cascade="all, delete-orphan"))
    generator = relationship("User", backref=backref("generated_reports", lazy="dynamic"))

    def __repr__(self):
        return f"<Report(id={self.id}, title={self.title}, type={self.type.value})>"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(SAEnum(NotificationType), nullable=True)
    reference_id = Column(UUID(as_uuid=True), nullable=True)
    reference_type = Column(String(50), nullable=True)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationship
    user = relationship("User", backref=backref("notifications", lazy="dynamic", cascade="all, delete-orphan"))

    __table_args__ = (
        Index("idx_notifications_user", "user_id"),
        Index("idx_notifications_unread", "user_id", "is_read"),
    )

    def __repr__(self):
        return f"<Notification(id={self.id}, title={self.title})>"


# ============================================================================
# MESSAGING MODELS
# ============================================================================

class Conversation(Base):
    """
    A conversation between two users (can be patient-clinician, clinician-clinician, etc.).
    Uses User IDs to allow any user type to message any other user type.
    """
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    participant_1_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    participant_2_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    last_message_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships - use explicit foreign_keys to avoid ambiguity
    participant_1 = relationship("User", foreign_keys=[participant_1_id], backref=backref("conversations_as_p1", lazy="dynamic"))
    participant_2 = relationship("User", foreign_keys=[participant_2_id], backref=backref("conversations_as_p2", lazy="dynamic"))

    __table_args__ = (
        Index("idx_conversations_participant_1", "participant_1_id"),
        Index("idx_conversations_participant_2", "participant_2_id"),
        UniqueConstraint("participant_1_id", "participant_2_id", name="uq_conversation_participants"),
        Index("idx_conversations_updated", "updated_at"),
    )

    def __repr__(self):
        return f"<Conversation(id={self.id}, p1={self.participant_1_id}, p2={self.participant_2_id})>"


class Message(Base):
    """A message within a conversation."""
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    message_type = Column(SAEnum(MessageType), default=MessageType.TEXT, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    attachment_url = Column(String(500), nullable=True)
    attachment_name = Column(String(255), nullable=True)
    audio_duration = Column(Integer, nullable=True)  # Duration in seconds for voice messages
    original_language = Column(SAEnum(PreferredLanguage), nullable=True)  # Language the audio was spoken in
    transcripts = Column(JSONB, nullable=True)  # Multi-language transcripts: {"yoruba": "...", "english": "..."}
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    conversation = relationship("Conversation", backref=backref("messages", lazy="dynamic", cascade="all, delete-orphan", order_by="Message.created_at"))
    sender = relationship("User", backref=backref("sent_messages", lazy="dynamic"))

    __table_args__ = (
        Index("idx_messages_conversation", "conversation_id"),
        Index("idx_messages_conversation_created", "conversation_id", "created_at"),
        Index("idx_messages_unread", "conversation_id", "is_read"),
        Index("idx_messages_sender", "sender_id"),
    )

    def __repr__(self):
        return f"<Message(id={self.id}, conversation_id={self.conversation_id}, sender_id={self.sender_id})>"