from extensions import db


class InventoryItem(db.Model):
    __tablename__ = "inventory_items"

    inventory_item_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    hospital_id = db.Column(db.BigInteger, db.ForeignKey("hospitals.hospital_id"), nullable=False)
    sku = db.Column(db.String(50), nullable=False)
    item_name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.Enum("DRUG", "MEDICAL_SUPPLY", "EQUIPMENT"), nullable=False)
    unit_of_measure = db.Column(db.String(20))
    quantity_on_hand = db.Column(db.Integer, nullable=False, default=0)
    reorder_threshold = db.Column(db.Integer, nullable=False, default=0)
    is_controlled_substance = db.Column(db.Boolean, default=False)

    __table_args__ = (db.UniqueConstraint("hospital_id", "sku", name="uq_sku_per_hospital"),)

    def to_dict(self):
        return {
            "inventory_item_id": self.inventory_item_id,
            "hospital_id": self.hospital_id,
            "sku": self.sku,
            "item_name": self.item_name,
            "category": self.category,
            "unit_of_measure": self.unit_of_measure,
            "quantity_on_hand": self.quantity_on_hand,
            "reorder_threshold": self.reorder_threshold,
            "is_controlled_substance": self.is_controlled_substance,
            "low_stock": self.quantity_on_hand <= self.reorder_threshold,
        }


class InventoryTransaction(db.Model):
    __tablename__ = "inventory_transactions"

    transaction_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    inventory_item_id = db.Column(
        db.BigInteger, db.ForeignKey("inventory_items.inventory_item_id"), nullable=False
    )
    transaction_type = db.Column(db.Enum("RECEIPT", "DISPENSE", "ADJUSTMENT", "TRANSFER"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    related_medication_request_id = db.Column(
        db.BigInteger, db.ForeignKey("medication_requests.medication_request_id")
    )
    performed_by_staff_id = db.Column(db.BigInteger, db.ForeignKey("staff.staff_id"), nullable=False)
    transaction_at = db.Column(db.DateTime, nullable=False)

    def to_dict(self):
        return {
            "transaction_id": self.transaction_id,
            "inventory_item_id": self.inventory_item_id,
            "transaction_type": self.transaction_type,
            "quantity": self.quantity,
            "related_medication_request_id": self.related_medication_request_id,
            "performed_by_staff_id": self.performed_by_staff_id,
            "transaction_at": self.transaction_at.isoformat() if self.transaction_at else None,
        }
