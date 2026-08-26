from extensions import db


class BillingClaim(db.Model):
    """Phase 2 (Finance subgraph) uses this table; defined in Phase 1 so the full
    schema is present and FK-consistent from the start."""
    __tablename__ = "billing_claims"

    claim_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    encounter_id = db.Column(db.BigInteger, db.ForeignKey("encounters.encounter_id"), nullable=False)
    hospital_id = db.Column(db.BigInteger, db.ForeignKey("hospitals.hospital_id"), nullable=False)
    payer_name = db.Column(db.String(150))
    claim_amount = db.Column(db.Numeric(12, 2), nullable=False)
    status = db.Column(db.Enum("SUBMITTED", "PAID", "DENIED", "APPEALED"), nullable=False, default="SUBMITTED")
    submitted_at = db.Column(db.DateTime)
    adjudicated_at = db.Column(db.DateTime)
    denial_reason = db.Column(db.String(255))

    def to_dict(self):
        return {
            "claim_id": self.claim_id,
            "encounter_id": self.encounter_id,
            "hospital_id": self.hospital_id,
            "payer_name": self.payer_name,
            "claim_amount": float(self.claim_amount) if self.claim_amount is not None else None,
            "status": self.status,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
            "adjudicated_at": self.adjudicated_at.isoformat() if self.adjudicated_at else None,
            "denial_reason": self.denial_reason,
        }
