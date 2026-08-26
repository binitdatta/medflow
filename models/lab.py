from extensions import db


class LabOrder(db.Model):
    __tablename__ = "lab_orders"

    lab_order_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    encounter_id = db.Column(db.BigInteger, db.ForeignKey("encounters.encounter_id"), nullable=False)
    ordered_by_staff_id = db.Column(db.BigInteger, db.ForeignKey("staff.staff_id"), nullable=False)
    test_code = db.Column(db.String(20), nullable=False)
    test_name = db.Column(db.String(150), nullable=False)
    status = db.Column(
        db.Enum("ORDERED", "COLLECTED", "IN_LAB", "RESULTED", "CANCELLED"),
        nullable=False,
        default="ORDERED",
    )
    ordered_at = db.Column(db.DateTime, nullable=False)
    resulted_at = db.Column(db.DateTime)
    result_value = db.Column(db.String(100))
    result_units = db.Column(db.String(30))
    abnormal_flag = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            "lab_order_id": self.lab_order_id,
            "encounter_id": self.encounter_id,
            "ordered_by_staff_id": self.ordered_by_staff_id,
            "test_code": self.test_code,
            "test_name": self.test_name,
            "status": self.status,
            "ordered_at": self.ordered_at.isoformat() if self.ordered_at else None,
            "resulted_at": self.resulted_at.isoformat() if self.resulted_at else None,
            "result_value": self.result_value,
            "result_units": self.result_units,
            "abnormal_flag": self.abnormal_flag,
        }
