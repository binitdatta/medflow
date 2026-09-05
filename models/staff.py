from extensions import db

ROLE_VALUES = (
    "PHYSICIAN", "NURSE", "PHARMACIST", "ADMISSIONS",
    "FINANCE", "MANAGEMENT", "LEGAL", "ADMIN","HIPAA_ADMIN"
)


class Staff(db.Model):
    __tablename__ = "staff"

    staff_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    keycloak_user_id = db.Column(db.String(64), nullable=False, unique=True)
    hospital_id = db.Column(db.BigInteger, db.ForeignKey("hospitals.hospital_id"), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.Enum(*ROLE_VALUES), nullable=False)
    npi_number = db.Column(db.String(20))
    license_number = db.Column(db.String(50))
    active = db.Column(db.Boolean, nullable=False, default=True)

    def to_dict(self):
        return {
            "staff_id": self.staff_id,
            "keycloak_user_id": self.keycloak_user_id,
            "hospital_id": self.hospital_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "role": self.role,
            "active": self.active,
        }
