from extensions import db


class BedAssignment(db.Model):
    __tablename__ = "bed_assignments"

    assignment_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    bed_id = db.Column(db.BigInteger, db.ForeignKey("beds.bed_id"), nullable=False)
    encounter_id = db.Column(db.BigInteger, db.ForeignKey("encounters.encounter_id"), nullable=False)
    assigned_at = db.Column(db.DateTime, nullable=False)
    released_at = db.Column(db.DateTime)

    def to_dict(self):
        return {
            "assignment_id": self.assignment_id,
            "bed_id": self.bed_id,
            "encounter_id": self.encounter_id,
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "released_at": self.released_at.isoformat() if self.released_at else None,
        }
