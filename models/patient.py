from datetime import datetime
from extensions import db


class Patient(db.Model):
    """PHI-bearing table. Never returned directly by an endpoint without a role check."""
    __tablename__ = "patients"

    patient_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    mrn = db.Column(db.String(20), nullable=False, unique=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    sex = db.Column(db.Enum("M", "F", "O", "U"), nullable=False, default="U")
    ssn_last4 = db.Column(db.String(4))
    address = db.Column(db.String(255))
    phone = db.Column(db.String(30))
    primary_hospital_id = db.Column(db.BigInteger, db.ForeignKey("hospitals.hospital_id"), nullable=False)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)

    def to_dict(self, full=True):
        base = {
            "patient_id": self.patient_id,
            "mrn": self.mrn,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "dob": self.dob.isoformat() if self.dob else None,
            "sex": self.sex,
        }
        if full:
            base.update({
                "ssn_last4": self.ssn_last4,
                "address": self.address,
                "phone": self.phone,
                "primary_hospital_id": self.primary_hospital_id,
            })
        return base
