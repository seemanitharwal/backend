#!/usr/bin/env python3
"""
Seed script to populate the database with sample data for testing
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models import Employee, Project, Task
from app.models.project import project_employees
from app.core.security import create_verification_token

def create_sample_data():
    """Create sample employees, projects, and tasks"""
    db = SessionLocal()
    
    try:
        # Create employees
        employees_data = [
            {"name": "John Doe", "email": "john.doe@example.com"},
            {"name": "Jane Smith", "email": "jane.smith@example.com"},
            {"name": "Mike Johnson", "email": "mike.johnson@example.com"},
            {"name": "Sarah Wilson", "email": "sarah.wilson@example.com"},
        ]
        
        employees = []
        for emp_data in employees_data:
            employee = Employee(
                name=emp_data["name"],
                email=emp_data["email"],
                is_active=True,
                is_verified=True,  # Pre-verified for testing
            )
            db.add(employee)
            employees.append(employee)
        
        db.commit()
        
        # Refresh to get IDs
        for emp in employees:
            db.refresh(emp)
        
        print(f"Created {len(employees)} employees")
        
        # Create projects
        projects_data = [
            {
                "name": "E-Commerce Platform",
                "description": "Building a modern e-commerce platform with React and Node.js",
                "employee_ids": [employees[0].id, employees[1].id]
            },
            {
                "name": "Mobile App Development",
                "description": "Developing a cross-platform mobile application using React Native",
                "employee_ids": [employees[1].id, employees[2].id]
            },
            {
                "name": "Data Analytics Dashboard",
                "description": "Creating an analytics dashboard for business intelligence",
                "employee_ids": [employees[2].id, employees[3].id]
            },
            {
                "name": "API Integration Project",
                "description": "Integrating multiple third-party APIs for client requirements",
                "employee_ids": [employees[0].id, employees[3].id]
            }
        ]
        
        projects = []
        for proj_data in projects_data:
            project = Project(
                name=proj_data["name"],
                description=proj_data["description"]
            )
            
            # Add assigned employees
            assigned_employees = [emp for emp in employees if emp.id in proj_data["employee_ids"]]
            project.employees = assigned_employees
            
            db.add(project)
            projects.append(project)
        
        db.commit()
        
        # Refresh to get IDs
        for proj in projects:
            db.refresh(proj)
        
        print(f"Created {len(projects)} projects")
        
        # Create tasks (one default task per project)
        tasks_data = [
            {"name": "Frontend Development", "project_id": projects[0].id},
            {"name": "Backend API Development", "project_id": projects[0].id},
            {"name": "UI/UX Design", "project_id": projects[1].id},
            {"name": "Mobile App Core Features", "project_id": projects[1].id},
            {"name": "Dashboard Implementation", "project_id": projects[2].id},
            {"name": "Data Visualization", "project_id": projects[2].id},
            {"name": "API Integration", "project_id": projects[3].id},
            {"name": "Testing & Documentation", "project_id": projects[3].id},
        ]
        
        tasks = []
        for task_data in tasks_data:
            task = Task(
                name=task_data["name"],
                project_id=task_data["project_id"]
            )
            db.add(task)
            tasks.append(task)
        
        db.commit()
        
        print(f"Created {len(tasks)} tasks")
        
        # Print summary
        print("\n" + "="*50)
        print("SAMPLE DATA CREATED SUCCESSFULLY")
        print("="*50)
        
        print("\nEmployees:")
        for emp in employees:
            print(f"  ID: {emp.id} | {emp.name} ({emp.email})")
        
        print("\nProjects:")
        for proj in projects:
            employee_names = [emp.name for emp in proj.employees]
            print(f"  ID: {proj.id} | {proj.name}")
            print(f"    Assigned to: {', '.join(employee_names)}")
        
        print("\nTasks:")
        for task in tasks:
            print(f"  ID: {task.id} | {task.name} (Project: {task.project.name})")
        
        print("\n" + "="*50)
        print("You can now use these IDs for API testing!")
        print("="*50)
        
    except Exception as e:
        print(f"Error creating sample data: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Creating sample data...")
    create_sample_data()