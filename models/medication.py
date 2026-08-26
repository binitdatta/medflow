from extensions import db


class MedicationRequest(db.Model):
    __tablename__ = "medication_requests"

    medication_request_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    encounter_id = db.Column(db.BigInteger, db.ForeignKey("encounters.encounter_id"), nullable=False)
    patient_id = db.Column(db.BigInteger, db.ForeignKey("patients.patient_id"), nullable=False)
    prescribed_by_staff_id = db.Column(db.BigInteger, db.ForeignKey("staff.staff_id"), nullable=False)
    drug_name = db.Column(db.String(150), nullable=False)
    ndc_code = db.Column(db.String(20))
    dose = db.Column(db.String(50))
    route = db.Column(db.String(30))
    frequency = db.Column(db.String(50))
    status = db.Column(
        db.Enum("DRAFT", "ACTIVE", "COMPLETED", "CANCELLED", "ON_HOLD"),
        nullable=False,
        default="DRAFT",
    )
    controlled_substance_flag = db.Column(db.Boolean, default=False)
    start_datetime = db.Column(db.DateTime)
    end_datetime = db.Column(db.DateTime)

    def to_dict(self):
        return {
            "medication_request_id": self.medication_request_id,
            "encounter_id": self.encounter_id,
            "patient_id": self.patient_id,
            "prescribed_by_staff_id": self.prescribed_by_staff_id,
            "drug_name": self.drug_name,
            "ndc_code": self.ndc_code,
            "dose": self.dose,
            "route": self.route,
            "frequency": self.frequency,
            "status": self.status,
            "controlled_substance_flag": self.controlled_substance_flag,
            "start_datetime": self.start_datetime.isoformat() if self.start_datetime else None,
            "end_datetime": self.end_datetime.isoformat() if self.end_datetime else None,
        }


class MedicationAdministration(db.Model):
    __tablename__ = "medication_administrations"

    administration_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    medication_request_id = db.Column(
        db.BigInteger, db.ForeignKey("medication_requests.medication_request_id"), nullable=False
    )
    administered_by_staff_id = db.Column(db.BigInteger, db.ForeignKey("staff.staff_id"), nullable=False)
    administered_at = db.Column(db.DateTime, nullable=False)
    dose_given = db.Column(db.String(50))
    notes = db.Column(db.String(255))

    def to_dict(self):
        return {
            "administration_id": self.administration_id,
            "medication_request_id": self.medication_request_id,
            "administered_by_staff_id": self.administered_by_staff_id,
            "administered_at": self.administered_at.isoformat() if self.administered_at else None,
            "dose_given": self.dose_given,
            "notes": self.notes,
        }
