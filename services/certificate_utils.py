"""Utility functions for certificate management"""

from sqlalchemy.orm import Session
from datetime import datetime
from models import CompletionCertificate, Enrollment, ProgramEnrollment, DiplomaEnrollment
from services.certificate_generator import CertificateGenerator


def generate_course_certificate(user_id: int, enrollment_id: int, db: Session) -> CompletionCertificate:
    """Generate certificate when a course is completed"""
    enrollment = db.query(Enrollment).filter(Enrollment.id == enrollment_id).first()
    if not enrollment:
        raise ValueError("Enrollment not found")
    
    # Check if certificate already exists
    existing_cert = db.query(CompletionCertificate).filter(
        CompletionCertificate.user_id == user_id,
        CompletionCertificate.course_id == enrollment.course_id,
        CompletionCertificate.item_type == "course"
    ).first()
    
    if existing_cert:
        return existing_cert
    
    # Generate certificate number and verification code
    cert_number = CertificateGenerator.generate_certificate_number()
    verification_code = CertificateGenerator.generate_verification_code()
    
    # Create certificate record
    certificate = CompletionCertificate(
        user_id=user_id,
        item_type="course",
        course_id=enrollment.course_id,
        enrollment_id=enrollment_id,
        certificate_number=cert_number,
        verification_code=verification_code,
        completed_at=enrollment.completed_at or datetime.utcnow(),
        status="issued"
    )
    
    db.add(certificate)
    db.commit()
    db.refresh(certificate)
    
    return certificate


def generate_program_certificate(user_id: int, program_enrollment_id: int, db: Session) -> CompletionCertificate:
    """Generate certificate when a program is completed"""
    enrollment = db.query(ProgramEnrollment).filter(ProgramEnrollment.id == program_enrollment_id).first()
    if not enrollment:
        raise ValueError("Program enrollment not found")
    
    # Check if certificate already exists
    existing_cert = db.query(CompletionCertificate).filter(
        CompletionCertificate.user_id == user_id,
        CompletionCertificate.program_id == enrollment.program_id,
        CompletionCertificate.item_type == "program"
    ).first()
    
    if existing_cert:
        return existing_cert
    
    # Generate certificate number and verification code
    cert_number = CertificateGenerator.generate_certificate_number()
    verification_code = CertificateGenerator.generate_verification_code()
    
    # Create certificate record
    certificate = CompletionCertificate(
        user_id=user_id,
        item_type="program",
        program_id=enrollment.program_id,
        enrollment_id=program_enrollment_id,
        certificate_number=cert_number,
        verification_code=verification_code,
        completed_at=enrollment.completed_at or datetime.utcnow(),
        status="issued"
    )
    
    db.add(certificate)
    db.commit()
    db.refresh(certificate)
    
    return certificate


def generate_diploma_certificate(user_id: int, diploma_enrollment_id: int, db: Session) -> CompletionCertificate:
    """Generate certificate when a diploma is completed"""
    enrollment = db.query(DiplomaEnrollment).filter(DiplomaEnrollment.id == diploma_enrollment_id).first()
    if not enrollment:
        raise ValueError("Diploma enrollment not found")
    
    # Check if certificate already exists
    existing_cert = db.query(CompletionCertificate).filter(
        CompletionCertificate.user_id == user_id,
        CompletionCertificate.diploma_id == enrollment.diploma_id,
        CompletionCertificate.item_type == "diploma"
    ).first()
    
    if existing_cert:
        return existing_cert
    
    # Generate certificate number and verification code
    cert_number = CertificateGenerator.generate_certificate_number()
    verification_code = CertificateGenerator.generate_verification_code()
    
    # Create certificate record
    certificate = CompletionCertificate(
        user_id=user_id,
        item_type="diploma",
        diploma_id=enrollment.diploma_id,
        enrollment_id=diploma_enrollment_id,
        certificate_number=cert_number,
        verification_code=verification_code,
        completed_at=enrollment.completed_at or datetime.utcnow(),
        status="issued"
    )
    
    db.add(certificate)
    db.commit()
    db.refresh(certificate)
    
    return certificate
