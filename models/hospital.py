from datetime import datetime
from extensions import db


class Hospital(db.Model):
    __tablename__ = "hospitals"

    hospital_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    name = db.Column(db.String(150), nullable=False)
    address = db.Column(db.String(255))
    timezone = db.Column(db.String(50), nullable=False, default="America/Chicago")
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)

    departments = db.relationship("Department", backref="hospital", lazy=True)

    def to_dict(self):
        return {
            "hospital_id": self.hospital_id,
            "name": self.name,
            "address": self.address,
            "timezone": self.timezone,
        }


class Department(db.Model):
    __tablename__ = "departments"

    department_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    hospital_id = db.Column(db.BigInteger, db.ForeignKey("hospitals.hospital_id"), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    dept_type = db.Column(
        db.Enum("INPATIENT", "OUTPATIENT", "PHARMACY", "INVENTORY", "ADMISSIONS", "ER"),
        nullable=False,
    )

    units = db.relationship("Unit", backref="department", lazy=True)

    def to_dict(self):
        return {
            "department_id": self.department_id,
            "hospital_id": self.hospital_id,
            "name": self.name,
            "dept_type": self.dept_type,
        }


class Unit(db.Model):
    __tablename__ = "units"

    unit_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    department_id = db.Column(db.BigInteger, db.ForeignKey("departments.department_id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    floor = db.Column(db.String(20))
    capacity = db.Column(db.Integer, nullable=False, default=0)

    beds = db.relationship("Bed", backref="unit", lazy=True)

    def to_dict(self):
        return {
            "unit_id": self.unit_id,
            "department_id": self.department_id,
            "name": self.name,
            "floor": self.floor,
            "capacity": self.capacity,
        }


class Bed(db.Model):
    __tablename__ = "beds"

    bed_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    unit_id = db.Column(db.BigInteger, db.ForeignKey("units.unit_id"), nullable=False)
    bed_number = db.Column(db.String(20), nullable=False)
    status = db.Column(
        db.Enum("AVAILABLE", "OCCUPIED", "CLEANING", "OUT_OF_SERVICE"),
        nullable=False,
        default="AVAILABLE",
    )

    def to_dict(self):
        return {
            "bed_id": self.bed_id,
            "unit_id": self.unit_id,
            "bed_number": self.bed_number,
            "status": self.status,
        }
