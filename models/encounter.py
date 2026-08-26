from extensions import db


class Encounter(db.Model):
    __tablename__ = "encounters"

    encounter_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    patient_id = db.Column(db.BigInteger, db.ForeignKey("patients.patient_id"), nullable=False)
    hospital_id = db.Column(db.BigInteger, db.ForeignKey("hospitals.hospital_id"), nullable=False)
    encounter_type = db.Column(db.Enum("INPATIENT", "OUTPATIENT", "ER"), nullable=False)
    status = db.Column(
        db.Enum("PLANNED", "ARRIVED", "IN_PROGRESS", "DISCHARGED", "CANCELLED"),
        nullable=False,
        default="PLANNED",
    )
    admit_datetime = db.Column(db.DateTime)
    discharge_datetime = db.Column(db.DateTime)
    attending_physician_id = db.Column(db.BigInteger, db.ForeignKey("staff.staff_id"))
    chief_complaint = db.Column(db.String(255))
    bed_id = db.Column(db.BigInteger, db.ForeignKey("beds.bed_id"))

    def to_dict(self):
        return {
            "encounter_id": self.encounter_id,
            "patient_id": self.patient_id,
            "hospital_id": self.hospital_id,
            "encounter_type": self.encounter_type,
            "status": self.status,
            "admit_datetime": self.admit_datetime.isoformat() if self.admit_datetime else None,
            "discharge_datetime": self.discharge_datetime.isoformat() if self.discharge_datetime else None,
            "attending_physician_id": self.attending_physician_id,
            "chief_complaint": self.chief_complaint,
            "bed_id": self.bed_id,
        }


class Diagnosis(db.Model):
    __tablename__ = "diagnoses"

    diagnosis_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    encounter_id = db.Column(db.BigInteger, db.ForeignKey("encounters.encounter_id"), nullable=False)
    icd10_code = db.Column(db.String(10), nullable=False)
    description = db.Column(db.String(255))
    diagnosed_by_staff_id = db.Column(db.BigInteger, db.ForeignKey("staff.staff_id"), nullable=False)
    diagnosed_at = db.Column(db.DateTime, nullable=False)

    def to_dict(self):
        return {
            "diagnosis_id": self.diagnosis_id,
            "encounter_id": self.encounter_id,
            "icd10_code": self.icd10_code,
            "description": self.description,
            "diagnosed_by_staff_id": self.diagnosed_by_staff_id,
            "diagnosed_at": self.diagnosed_at.isoformat() if self.diagnosed_at else None,
        }
