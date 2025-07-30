from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Employee(Base):
    __tablename__ = "employees"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    status = Column(String(20), default="inactive")  # active, inactive
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Device information
    last_mac_address = Column(String(17), nullable=True)
    last_ip_address = Column(String(45), nullable=True)
    device_info = Column(Text, nullable=True)  # JSON string
    
    # Relationships
    time_entries = relationship("TimeEntry", back_populates="employee")
    screenshots = relationship("Screenshot", back_populates="employee")
    
    def __repr__(self):
        return f"<Employee(id={self.id}, name='{self.name}', email='{self.email}')>"