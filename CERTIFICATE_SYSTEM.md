# Certificate System Documentation

## Overview

The Sabikin Certificate System provides automated generation and management of certificates for course, program, and diploma completions. Students can download certificates in PDF format and request changes (name corrections, physical copies). Administrators have full control over certificate verification, approval, and revocation.

## Features

### 🎓 Student Features
- **View Certificates**: Browse all earned certificates from dashboard
- **Download Certificates**: Download as PDF (PNG/JPEG coming soon)
- **Verify Certificates**: Public verification via unique verification codes
- **Request Changes**: Request name corrections or physical copies
- **Certificate Details**: View completion dates, issuer info, and certificate numbers

### 👨‍💼 Admin Features
- **View All Certificates**: Browse all student certificates with filters
- **Student Profiles**: View individual student certificates and details
- **Approve Requests**: Review and approve certificate change requests
- **Revoke Certificates**: Revoke certificates with documented reasons
- **Change Requests**: Track pending certificate modification requests

## Certificate Types

### 1. **Course Certificates**
- **Title**: Certificate of Participation
- **Issued**: Upon course completion
- **Format**: "Certificate of Participation in [Course Name]"

### 2. **Program Certifications**
- **Title**: Certification
- **Issued**: Upon program completion
- **Format**: "Certification in [Program Name]"

### 3. **Diploma**
- **Title**: Diploma
- **Issued**: Upon diploma completion
- **Format**: "Diploma in [Diploma Name]"

## Certificate Content

Each certificate includes:
- **Organization**: Sabikin (A subsidiary of Celgroup)
- **Student Name**: Full legal name of the graduate
- **Achievement**: Certificate type and course/program/diploma name
- **Completion Date**: Date when course/program/diploma was completed
- **Issue Date**: Date certificate was generated
- **Certificate Number**: Unique identifier (SABIKIN-CERT-YYYYMMDDHHMMSS-XXXXXXXX)
- **Verification Code**: QR/text code for public verification
- **CEO Signature**: Caleb Ezidi Leo, Chief Executive Officer

## API Endpoints

### User Endpoints

#### Get My Certificates
```
GET /api/certificates/user/my-certificates?skip=0&limit=20
Authorization: Bearer {userToken}
```

Response:
```json
[
  {
    "id": 1,
    "user_id": 123,
    "item_type": "course",
    "certificate_number": "SABIKIN-CERT-20240501120000-ABC12345",
    "completed_at": "2024-05-01T10:30:00Z",
    "issued_at": "2024-05-01T12:00:00Z",
    "status": "issued"
  }
]
```

#### Get Certificate Details
```
GET /api/certificates/user/certificate/{certificateId}
Authorization: Bearer {userToken}
```

#### Download Certificate
```
GET /api/certificates/user/certificate/{certificateId}/download?format=pdf
Authorization: Bearer {userToken}

Supported formats:
- pdf (available)
- png (coming soon)
- jpeg (coming soon)
```

#### Request Certificate Change
```
POST /api/certificates/user/certificate/{certificateId}/request-change
Authorization: Bearer {userToken}

Body:
{
  "change_type": "name_correction" | "physical_copy" | "duplicate",
  "reason": "Name was misspelled",
  "details": "Should be 'John Doe' not 'Jon Doe'"
}
```

#### Verify Certificate (Public)
```
GET /api/certificates/verify/{verificationCode}
```

Response:
```json
{
  "valid": true,
  "certificate_number": "SABIKIN-CERT-20240501120000-ABC12345",
  "student_name": "John Doe",
  "student_email": "john@example.com",
  "item_type": "course",
  "item_name": "Python Fundamentals",
  "completed_at": "2024-05-01T10:30:00Z",
  "issued_at": "2024-05-01T12:00:00Z"
}
```

### Admin Endpoints

#### Get All Certificates
```
GET /api/certificates/admin/all?skip=0&limit=50&status_filter=issued
Authorization: Bearer {adminToken}
```

#### Get Student Certificates
```
GET /api/certificates/admin/student/{userId}/all
Authorization: Bearer {adminToken}
```

Returns student details and all their certificates including change requests.

#### Approve Certificate Change
```
POST /api/certificates/admin/certificate/{certificateId}/approve-change
Authorization: Bearer {adminToken}
```

#### Revoke Certificate
```
POST /api/certificates/admin/certificate/{certificateId}/revoke
Authorization: Bearer {adminToken}

Body:
{
  "reason": "Student failed to meet program requirements"
}
```

## Database Schema

### CompletionCertificate Model

```python
class CompletionCertificate(Base):
    __tablename__ = "completion_certificates"
    
    id: int (PK)
    user_id: int (FK -> User)
    item_type: str  # 'course', 'program', 'diploma'
    course_id: int (FK -> Course, nullable)
    program_id: int (FK -> Program, nullable)
    diploma_id: int (FK -> Diploma, nullable)
    enrollment_id: int  # Reference to enrollment record
    certificate_number: str (UNIQUE)  # SABIKIN-CERT-YYYYMMDDHHMMSS-XXXXXXXX
    verification_code: str (UNIQUE)  # For public verification
    completed_at: datetime  # When course/program/diploma was completed
    issued_at: datetime  # When certificate was generated
    pdf_path: str (nullable)  # Storage path for PDF
    status: str  # 'issued', 'revoked', 'expired', 'reissue_requested'
    change_request: JSON (nullable)  # Stores change request details
    created_at: datetime
    updated_at: datetime
```

## Frontend Pages

### Student Pages

#### `/certificates` - My Certificates
- Displays all earned certificates
- Shows certificate details (number, dates, type)
- Download buttons for each format
- View details link

#### `/certificates/[id]` - Certificate Details
- Full certificate information
- Download options
- Request change form
- Verification code

### Admin Pages

#### `/admin/certificates` - All Certificates
- List of all certificates
- Filters: Status, Student search
- Mobile-responsive table/cards
- Links to student details

#### `/admin/certificates/[userId]` - Student Profile
- Student information
- All their certificates
- Change request management
- Revocation controls

## Certificate Generation

### Automatic Generation Triggers

Certificates are generated automatically when:
1. Course enrollment status changed to "completed"
2. Program enrollment status changed to "completed"  
3. Diploma enrollment status changed to "completed"

### Manual Generation (if needed)

Use the certificate utility functions:

```python
from services.certificate_utils import generate_course_certificate

# In your completion endpoint:
certificate = generate_course_certificate(
    user_id=user_id,
    enrollment_id=enrollment_id,
    db=db
)
```

## PDF Generation Details

The certificate PDF is generated using ReportLab with:
- **Size**: A4 Landscape
- **Layout**: Professional certificate format
- **Colors**: Brand colors (Blue primary, Gray accents)
- **Font**: Helvetica for clean, professional look
- **Elements**:
  - Company branding at top
  - Certificate type and student name prominently displayed
  - Achievement description
  - Completion and issue dates
  - CEO signature area
  - Certificate and verification numbers
  - Footer with issuer info

## Change Requests Workflow

### Student Perspective
1. View certificate
2. Click "Request Change"
3. Select change type (name_correction, physical_copy, duplicate)
4. Provide reason and details
5. Submit request
6. Status changes to "reissue_requested"

### Admin Perspective
1. See certificate with change request indicator
2. Review change request details
3. Verify student information
4. Approve or deny request
5. If approved, certificate is marked "issued" with changes applied

## Change Request Types

### Name Correction
- **Use Case**: Name misspelled on certificate
- **Admin Action**: Verify with student, reissue with correct name
- **Require**: Email confirmation

### Physical Copy
- **Use Case**: Student wants physical printed certificate
- **Admin Action**: Prepare for printing, send physical mail
- **Note**: Admin should note address in system

### Duplicate
- **Use Case**: Original lost or damaged
- **Admin Action**: Reissue identical certificate with same number
- **Note**: Rare - only if genuinely lost

## Verification System

### How It Works
1. Each certificate has unique `verification_code`
2. Public can verify by visiting: `/api/certificates/verify/{code}`
3. Returns certificate details without student contact info
4. Useful for employers checking credentials

### Use Cases
- Employer verification of credentials
- Third-party validation
- Credential portals (LinkedIn, etc.)

## Security Considerations

1. **Certificate Numbers**: Unique per certificate, sequential with timestamp
2. **Verification Codes**: UUID-based, impossible to guess
3. **Access Control**: Only student or admin can view/download
4. **Revocation**: Revoked certificates cannot be re-verified
5. **Change Trail**: All modifications tracked in `change_request` JSON
6. **Storage**: PDFs stored server-side, not sent to untrusted systems

## Troubleshooting

### Certificate Not Generated
- Check enrollment status (must be "completed")
- Verify user and enrollment records exist
- Check database for existing certificate

### PDF Download Fails
- Verify file permissions on storage directory
- Check storage/certificates directory exists
- Review server logs for errors

### Verification Code Invalid
- Code is case-sensitive
- Certificate may be revoked
- Check certificate status in admin

### Change Request Not Showing
- Ensure request was submitted successfully
- Check database for change_request JSON
- Admin page may need refresh

## Future Enhancements

- [ ] PNG/JPEG export with watermark
- [ ] Digital signature verification
- [ ] Blockchain certificate integration
- [ ] Email delivery of certificates
- [ ] Batch certificate generation
- [ ] QR code on PDF for instant verification
- [ ] Certificate templates customization
- [ ] Multi-language support
- [ ] Physical mail integration
- [ ] Certificate wallet app support

## Compliance

- **Data Privacy**: GDPR compliant - student data stored securely
- **Accessibility**: PDF certificates accessible to screen readers
- **Authenticity**: Unique numbers prevent forgery
- **Auditability**: Full change trail for all certificates
