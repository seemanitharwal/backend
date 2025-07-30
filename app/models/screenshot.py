from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, BigInteger, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Screenshot(Base):
    __tablename__ = "screenshots"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    time_entry_id = Column(Integer, ForeignKey("time_entries.id"), nullable=True, index=True)
    
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    permission_granted = Column(Boolean, default=False)
    
    # Image metadata
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    format = Column(String(10), nullable=True)
    
    # Device info
    device_info = Column(Text, nullable=True)  # JSON string
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    employee = relationship("Employee", back_populates="screenshots")
    time_entry = relationship("TimeEntry", back_populates="screenshots")
    
    def __repr__(self):
        return f"<Screenshot(id={self.id}, employee_id={self.employee_id}, filename='{self.filename}')>"