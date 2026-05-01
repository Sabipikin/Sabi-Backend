"""Routes for certificate management - user and admin endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
import os
import json
from pathlib import Path

from database import get_db
from models import (
    User, CompletionCertificate, Enrollment, ProgramEnrollment, DiplomaEnrollment,
    Course, Program, Diploma
)
from schemas import CertificateResponse, CertificateDetailResponse
from routes.auth import get_current_user
from auth import decode_access_token
from routes.admin_auth import get_current_admin
from services.certificate_generator import CertificateGenerator

router = APIRouter(prefix="/api/certificates", tags=["certificates"])

# Storage directory for certificates
CERTIFICATES_DIR = Path("storage/certificates")
CERTIFICATES_DIR.mkdir(parents=True, exist_ok=True)


# ==================== USER ENDPOINTS ====================

@router.get("/user/my-certificates", response_model=List[CertificateResponse])
async def get_my_certificates(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all certificates for the current user"""
    try:
        certificates = db.query(CompletionCertificate).filter(
            CompletionCertificate.user_id == current_user.id,
            CompletionCertificate.status == "issued"
        ).order_by(CompletionCertificate.issued_at.desc()).offset(skip).limit(limit).all()
        
        return certificates
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching certificates: {str(e)}"
        )


@router.get("/user/certificate/{certificate_id}", response_model=CertificateDetailResponse)
async def get_certificate_detail(
    certificate_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific certificate"""
    try:
        certificate = db.query(CompletionCertificate).filter(
            CompletionCertificate.id == certificate_id,
            CompletionCertificate.user_id == current_user.id
        ).first()
        
        if not certificate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Certificate not found"
            )
        
        # Get item details
        item_name = None
        if certificate.item_type == "course":
            item = db.query(Course).filter(Course.id == certificate.course_id).first()
            item_name = item.title if item else "Course"
        elif certificate.item_type == "program":
            item = db.query(Program).filter(Program.id == certificate.program_id).first()
            item_name = item.title if item else "Program"
        elif certificate.item_type == "diploma":
            item = db.query(Diploma).filter(Diploma.id == certificate.diploma_id).first()
            item_name = item.title if item else "Diploma"
        
        return {
            **certificate.__dict__,
            "item_name": item_name
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching certificate: {str(e)}"
        )


@router.get("/user/certificate/{certificate_id}/download")
async def download_certificate(
    certificate_id: int,
    format: str = "pdf",  # pdf, jpeg, png
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download certificate in requested format"""
    try:
        certificate = db.query(CompletionCertificate).filter(
            CompletionCertificate.id == certificate_id,
            CompletionCertificate.user_id == current_user.id
        ).first()
        
        if not certificate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Certificate not found"
            )
        
        if format not in ["pdf", "jpeg", "png"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid format. Supported formats: pdf, jpeg, png"
            )
        
        # Get item details
        item_name = None
        if certificate.item_type == "course":
            item = db.query(Course).filter(Course.id == certificate.course_id).first()
            item_name = item.title if item else "Course"
        elif certificate.item_type == "program":
            item = db.query(Program).filter(Program.id == certificate.program_id).first()
            item_name = item.title if item else "Program"
        elif certificate.item_type == "diploma":
            item = db.query(Diploma).filter(Diploma.id == certificate.diploma_id).first()
            item_name = item.title if item else "Diploma"
        
        # Generate or retrieve certificate
        if format == "pdf":
            if certificate.pdf_path and os.path.exists(certificate.pdf_path):
                with open(certificate.pdf_path, 'rb') as f:
                    pdf_bytes = f.read()
            else:
                # Generate new PDF
                pdf_bytes = CertificateGenerator.generate_certificate(
                    student_name=current_user.full_name or current_user.email,
                    item_type=certificate.item_type,
                    item_name=item_name,
                    completion_date=certificate.completed_at,
                    certificate_number=certificate.certificate_number,
                    verification_code=certificate.verification_code
                )
                
                # Save to storage
                cert_path = CERTIFICATES_DIR / f"cert_{certificate.id}.pdf"
                with open(cert_path, 'wb') as f:
                    f.write(pdf_bytes)
                certificate.pdf_path = str(cert_path)
                db.commit()
            
            return {
                "content": pdf_bytes,
                "media_type": "application/pdf",
                "filename": f"{current_user.full_name or 'Certificate'}_{certificate.certificate_number}.pdf"
            }
        
        # For JPEG/PNG, note: requires additional library (Pillow, pdf2image)
        # For now, return error as these require conversion
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Image format download (JPEG, PNG) coming soon. Use PDF format for now."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error downloading certificate: {str(e)}"
        )


@router.post("/user/certificate/{certificate_id}/request-change")
async def request_certificate_change(
    certificate_id: int,
    request_body: dict,  # {reason: str, change_type: str, details: str}
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Request a change to certificate (name correction, physical copy request, etc.)"""
    try:
        certificate = db.query(CompletionCertificate).filter(
            CompletionCertificate.id == certificate_id,
            CompletionCertificate.user_id == current_user.id
        ).first()
        
        if not certificate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Certificate not found"
            )
        
        # Store change request
        change_request = {
            "requested_at": datetime.now().isoformat(),
            "change_type": request_body.get("change_type"),  # name_correction, physical_copy, etc.
            "reason": request_body.get("reason"),
            "details": request_body.get("details"),
            "status": "pending",
            "requester_email": current_user.email
        }
        
        certificate.change_request = json.dumps(change_request)
        certificate.status = "reissue_requested"
        db.commit()
        
        return {
            "message": "Certificate change request submitted",
            "request_id": certificate.id,
            "status": "pending"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error submitting change request: {str(e)}"
        )


@router.get("/verify/{verification_code}")
async def verify_certificate(
    verification_code: str,
    db: Session = Depends(get_db)
):
    """Public endpoint to verify a certificate by its verification code"""
    try:
        certificate = db.query(CompletionCertificate).filter(
            CompletionCertificate.verification_code == verification_code,
            CompletionCertificate.status == "issued"
        ).first()
        
        if not certificate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Certificate not found or invalid verification code"
            )
        
        # Get user and item details
        user = db.query(User).filter(User.id == certificate.user_id).first()
        
        item_name = None
        if certificate.item_type == "course":
            item = db.query(Course).filter(Course.id == certificate.course_id).first()
            item_name = item.title if item else "Course"
        elif certificate.item_type == "program":
            item = db.query(Program).filter(Program.id == certificate.program_id).first()
            item_name = item.title if item else "Program"
        elif certificate.item_type == "diploma":
            item = db.query(Diploma).filter(Diploma.id == certificate.diploma_id).first()
            item_name = item.title if item else "Diploma"
        
        return {
            "valid": True,
            "certificate_number": certificate.certificate_number,
            "student_name": user.full_name if user else "Unknown",
            "student_email": user.email if user else "Unknown",
            "item_type": certificate.item_type,
            "item_name": item_name,
            "completed_at": certificate.completed_at,
            "issued_at": certificate.issued_at
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error verifying certificate: {str(e)}"
        )


# ==================== ADMIN ENDPOINTS ====================

@router.get("/admin/all", response_model=dict)
async def admin_get_all_certificates(
    skip: int = 0,
    limit: int = 50,
    user_search: Optional[str] = None,
    status_filter: Optional[str] = None,
    admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Admin: Get all certificates with optional filters"""
    try:
        query = db.query(CompletionCertificate)
        
        if user_search:
            query = query.join(User).filter(
                (User.email.ilike(f"%{user_search}%")) |
                (User.full_name.ilike(f"%{user_search}%"))
            )
        
        if status_filter:
            query = query.filter(CompletionCertificate.status == status_filter)
        
        total = query.count()
        certificates = query.order_by(CompletionCertificate.issued_at.desc()).offset(skip).limit(limit).all()
        
        # Get user details for each certificate
        result = []
        for cert in certificates:
            user = db.query(User).filter(User.id == cert.user_id).first()
            result.append({
                "id": cert.id,
                "user_email": user.email if user else "Unknown",
                "user_name": user.full_name if user else "Unknown",
                "certificate_number": cert.certificate_number,
                "item_type": cert.item_type,
                "status": cert.status,
                "issued_at": cert.issued_at,
                "completed_at": cert.completed_at,
                "has_change_request": cert.status == "reissue_requested"
            })
        
        return {
            "certificates": result,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching certificates: {str(e)}"
        )


@router.get("/admin/student/{user_id}/all")
async def admin_get_student_certificates(
    user_id: int,
    admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Admin: Get all certificates for a specific student"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )
        
        certificates = db.query(CompletionCertificate).filter(
            CompletionCertificate.user_id == user_id
        ).order_by(CompletionCertificate.issued_at.desc()).all()
        
        return {
            "student": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "region": user.region,
                "joined_at": user.created_at
            },
            "certificates": [
                {
                    "id": cert.id,
                    "certificate_number": cert.certificate_number,
                    "item_type": cert.item_type,
                    "status": cert.status,
                    "issued_at": cert.issued_at,
                    "completed_at": cert.completed_at,
                    "has_change_request": cert.status == "reissue_requested",
                    "change_request": json.loads(cert.change_request) if cert.change_request else None
                }
                for cert in certificates
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching student certificates: {str(e)}"
        )


@router.post("/admin/certificate/{certificate_id}/approve-change")
async def admin_approve_certificate_change(
    certificate_id: int,
    admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Admin: Approve and process a certificate change request"""
    try:
        certificate = db.query(CompletionCertificate).filter(
            CompletionCertificate.id == certificate_id
        ).first()
        
        if not certificate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Certificate not found"
            )
        
        if certificate.status != "reissue_requested":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Certificate is not pending a change request"
            )
        
        # Update certificate status
        certificate.status = "issued"
        
        # Update change request status
        if certificate.change_request:
            change_data = json.loads(certificate.change_request)
            change_data["status"] = "approved"
            change_data["approved_at"] = datetime.now().isoformat()
            change_data["approved_by"] = admin.username
            certificate.change_request = json.dumps(change_data)
        
        db.commit()
        
        return {
            "message": "Certificate change request approved",
            "certificate_id": certificate.id,
            "status": "issued"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error approving change request: {str(e)}"
        )


@router.post("/admin/certificate/{certificate_id}/revoke")
async def admin_revoke_certificate(
    certificate_id: int,
    reason: dict,  # {reason: str}
    admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Admin: Revoke a certificate"""
    try:
        certificate = db.query(CompletionCertificate).filter(
            CompletionCertificate.id == certificate_id
        ).first()
        
        if not certificate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Certificate not found"
            )
        
        certificate.status = "revoked"
        certificate.change_request = json.dumps({
            "revocation_reason": reason.get("reason"),
            "revoked_at": datetime.now().isoformat(),
            "revoked_by": admin.username
        })
        
        db.commit()
        
        return {
            "message": "Certificate revoked successfully",
            "certificate_id": certificate.id,
            "status": "revoked"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error revoking certificate: {str(e)}"
        )
