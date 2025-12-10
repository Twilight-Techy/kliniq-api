"""
Database seed script for e-learning platform
Populates database with comprehensive test data
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import List
import random
from passlib.context import CryptContext

from sqlalchemy import text, delete
from sqlalchemy.ext.asyncio import AsyncSession

# Import your models and database setup
from src.models.models import (
    Base, User, UserRole, UserLogin, Track, Course, CourseLevel,
    TrackCourse, Module, Lesson, UserCourse, UserLesson,
    Quiz, QuizQuestion, UserQuiz, CourseQuiz,
    Resource, ResourceType, UserResource,
    Achievement, UserAchievement,
    Notification, NotificationType,
    Discussion, DiscussionReply,
    LearningPath, Skill, UserSkill, Deadline
)
from src.common.database.database import async_session, engine

# Password hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

class DatabaseSeeder:
    def __init__(self):
        self.main_user_id = None
        self.user_ids = []
        self.track_ids = []
        self.course_ids = []
        self.module_ids = []
        self.lesson_ids = []
        self.quiz_ids = []
        self.resource_ids = []
        self.achievement_ids = []
        self.skill_ids = []
        
    async def clear_database(self, session: AsyncSession):
        """Clear all tables in reverse order of dependencies"""
        print("🗑️  Clearing existing data...")
        
        tables_to_clear = [
            "user_skills",
            "skills",
            "deadlines",
            "learning_paths",
            "discussion_replies",
            "discussions",
            "notifications",
            "user_achievements",
            "achievements",
            "user_resources",
            "resources",
            "course_quizzes",
            "user_quizzes",
            "quiz_questions",
            "quizzes",
            "user_lessons",
            "user_courses",
            "lessons",
            "modules",
            "track_courses",
            "courses",
            "tracks",
            "user_logins",
            "users"
        ]
        
        for table in tables_to_clear:
            await session.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
        
        await session.commit()
        print("✅ Database cleared successfully")

    async def seed_users(self, session: AsyncSession):
        """Create users with different roles"""
        print("👥 Seeding users...")
        
        # Main test user (student)
        main_user = User(
            id=uuid.uuid4(),
            username="testuser",
            email="test@example.com",
            password_hash=hash_password("password123"),
            first_name="John",
            last_name="Doe",
            bio="Passionate learner exploring web development and data science.",
            avatar_url="https://api.dicebear.com/7.x/avataaars/svg?seed=testuser",
            xp=1250,
            role=UserRole.STUDENT,
            is_verified=True
        )
        self.main_user_id = main_user.id
        session.add(main_user)
        self.user_ids.append(main_user.id)
        
        # Additional students
        student_data = [
            ("alice_smith", "alice@example.com", "Alice", "Smith", 2300),
            ("bob_jones", "bob@example.com", "Bob", "Jones", 890),
            ("carol_white", "carol@example.com", "Carol", "White", 3450),
            ("david_brown", "david@example.com", "David", "Brown", 1670),
            ("emma_davis", "emma@example.com", "Emma", "Davis", 4200),
            ("frank_miller", "frank@example.com", "Frank", "Miller", 560),
            ("grace_wilson", "grace@example.com", "Grace", "Wilson", 2890),
            ("henry_moore", "henry@example.com", "Henry", "Moore", 1340),
            ("iris_taylor", "iris@example.com", "Iris", "Taylor", 3100)
        ]
        
        for username, email, first, last, xp in student_data:
            user = User(
                id=uuid.uuid4(),
                username=username,
                email=email,
                password_hash=hash_password("password123"),
                first_name=first,
                last_name=last,
                bio=f"{first} is an enthusiastic learner focused on technology.",
                avatar_url=f"https://api.dicebear.com/7.x/avataaars/svg?seed={username}",
                xp=xp,
                role=UserRole.STUDENT,
                is_verified=True
            )
            session.add(user)
            self.user_ids.append(user.id)
        
        # Tutors
        tutor_data = [
            ("prof_anderson", "anderson@example.com", "Professor", "Anderson", "Expert in Web Development"),
            ("dr_chen", "chen@example.com", "Dr.", "Chen", "Data Science Specialist"),
            ("coach_martinez", "martinez@example.com", "Coach", "Martinez", "Mobile Development Expert")
        ]
        
        for username, email, first, last, bio in tutor_data:
            tutor = User(
                id=uuid.uuid4(),
                username=username,
                email=email,
                password_hash=hash_password("tutor123"),
                first_name=first,
                last_name=last,
                bio=bio,
                avatar_url=f"https://api.dicebear.com/7.x/avataaars/svg?seed={username}",
                xp=0,
                role=UserRole.TUTOR,
                is_verified=True
            )
            session.add(tutor)
            self.user_ids.append(tutor.id)
        
        # Admin
        admin = User(
            id=uuid.uuid4(),
            username="admin",
            email="admin@example.com",
            password_hash=hash_password("admin123"),
            first_name="Admin",
            last_name="User",
            bio="Platform Administrator",
            avatar_url="https://api.dicebear.com/7.x/avataaars/svg?seed=admin",
            xp=0,
            role=UserRole.ADMIN,
            is_verified=True
        )
        session.add(admin)
        
        await session.commit()
        print(f"✅ Created {len(self.user_ids) + 1} users")

    async def seed_user_logins(self, session: AsyncSession):
        """Create login history for users"""
        print("🔐 Seeding user logins...")
        
        # Create multiple logins for main user
        base_date = datetime.now() - timedelta(days=30)
        for i in range(15):
            login = UserLogin(
                id=uuid.uuid4(),
                user_id=self.main_user_id,
                login_at=base_date + timedelta(days=i*2, hours=random.randint(8, 20))
            )
            session.add(login)
        
        # Add some logins for other users
        for user_id in self.user_ids[1:6]:
            for i in range(random.randint(3, 8)):
                login = UserLogin(
                    id=uuid.uuid4(),
                    user_id=user_id,
                    login_at=base_date + timedelta(days=random.randint(0, 30), hours=random.randint(6, 23))
                )
                session.add(login)
        
        await session.commit()
        print("✅ Created login history")

    async def seed_tracks(self, session: AsyncSession):
        """Create learning tracks"""
        print("🛤️  Seeding tracks...")
        
        tracks_data = [
            {
                "slug": "web-development",
                "title": "Full Stack Web Development",
                "description": "Master modern web development from frontend to backend. Learn HTML, CSS, JavaScript, React, Node.js, and databases.",
                "image_url": "https://images.unsplash.com/photo-1498050108023-c5249f4df085",
                "level": "Beginner to Advanced",
                "duration": "6 months",
                "prerequisites": ["Basic computer skills", "Problem-solving mindset"]
            },
            {
                "slug": "data-science",
                "title": "Data Science & Machine Learning",
                "description": "Dive into data analysis, visualization, and machine learning with Python. Cover statistics, ML algorithms, and real-world projects.",
                "image_url": "https://images.unsplash.com/photo-1551288049-bebda4e38f71",
                "level": "Intermediate to Advanced",
                "duration": "8 months",
                "prerequisites": ["Basic Python", "High school mathematics"]
            },
            {
                "slug": "mobile-development",
                "title": "Mobile App Development",
                "description": "Build native and cross-platform mobile applications. Learn React Native, Flutter, and mobile UI/UX principles.",
                "image_url": "https://images.unsplash.com/photo-1512941937669-90a1b58e7e9c",
                "level": "Intermediate",
                "duration": "5 months",
                "prerequisites": ["JavaScript fundamentals", "Basic programming concepts"]
            },
            {
                "slug": "cloud-computing",
                "title": "Cloud Computing & DevOps",
                "description": "Master cloud platforms, containerization, and CI/CD pipelines. Work with AWS, Docker, Kubernetes, and automation tools.",
                "image_url": "https://images.unsplash.com/photo-1451187580459-43490279c0fa",
                "level": "Intermediate to Advanced",
                "duration": "4 months",
                "prerequisites": ["Linux basics", "Networking fundamentals"]
            }
        ]
        
        for track_data in tracks_data:
            track = Track(
                id=uuid.uuid4(),
                **track_data
            )
            session.add(track)
            self.track_ids.append(track.id)
        
        await session.commit()
        print(f"✅ Created {len(self.track_ids)} tracks")

    async def seed_courses(self, session: AsyncSession):
        """Create courses"""
        print("📚 Seeding courses...")
        
        courses_data = [
            # Web Development Courses
            ("HTML & CSS Fundamentals", "Learn the building blocks of web development", CourseLevel.BEGINNER, "4 weeks", 0),
            ("JavaScript Mastery", "Deep dive into JavaScript programming", CourseLevel.INTERMEDIATE, "6 weeks", 49.99),
            ("React.js Complete Guide", "Build modern web apps with React", CourseLevel.INTERMEDIATE, "8 weeks", 79.99),
            ("Node.js Backend Development", "Create robust server-side applications", CourseLevel.ADVANCED, "6 weeks", 89.99),
            
            # Data Science Courses
            ("Python for Data Science", "Python programming for data analysis", CourseLevel.BEGINNER, "5 weeks", 0),
            ("Statistical Analysis", "Statistics fundamentals for data science", CourseLevel.INTERMEDIATE, "4 weeks", 59.99),
            ("Machine Learning Basics", "Introduction to ML algorithms", CourseLevel.INTERMEDIATE, "8 weeks", 99.99),
            ("Deep Learning with TensorFlow", "Neural networks and deep learning", CourseLevel.ADVANCED, "10 weeks", 129.99),
            
            # Mobile Development Courses
            ("React Native Fundamentals", "Cross-platform mobile development", CourseLevel.INTERMEDIATE, "6 weeks", 69.99),
            ("Flutter Development", "Build beautiful native apps", CourseLevel.INTERMEDIATE, "7 weeks", 79.99),
            ("Mobile UI/UX Design", "Design principles for mobile apps", CourseLevel.BEGINNER, "3 weeks", 39.99),
            
            # Cloud Computing Courses
            ("AWS Essentials", "Amazon Web Services fundamentals", CourseLevel.BEGINNER, "4 weeks", 0),
            ("Docker & Containerization", "Container technology mastery", CourseLevel.INTERMEDIATE, "5 weeks", 69.99),
            ("Kubernetes Orchestration", "Container orchestration at scale", CourseLevel.ADVANCED, "6 weeks", 89.99),
            ("CI/CD Pipeline Design", "Automated deployment workflows", CourseLevel.ADVANCED, "4 weeks", 79.99)
        ]
        
        for title, desc, level, duration, price in courses_data:
            course = Course(
                id=uuid.uuid4(),
                title=title,
                description=desc,
                image_url=f"https://images.unsplash.com/photo-{random.randint(1500000000000, 1600000000000)}",
                level=level,
                duration=duration,
                price=price
            )
            session.add(course)
            self.course_ids.append(course.id)
        
        await session.commit()
        print(f"✅ Created {len(self.course_ids)} courses")

    async def seed_track_courses(self, session: AsyncSession):
        """Link courses to tracks"""
        print("🔗 Linking courses to tracks...")
        
        # Web Development Track
        web_courses = self.course_ids[0:4]
        for i, course_id in enumerate(web_courses):
            tc = TrackCourse(
                track_id=self.track_ids[0],
                course_id=course_id,
                order=i + 1
            )
            session.add(tc)
        
        # Data Science Track
        ds_courses = self.course_ids[4:8]
        for i, course_id in enumerate(ds_courses):
            tc = TrackCourse(
                track_id=self.track_ids[1],
                course_id=course_id,
                order=i + 1
            )
            session.add(tc)
        
        # Mobile Development Track
        mobile_courses = self.course_ids[8:11]
        for i, course_id in enumerate(mobile_courses):
            tc = TrackCourse(
                track_id=self.track_ids[2],
                course_id=course_id,
                order=i + 1
            )
            session.add(tc)
        
        # Cloud Computing Track
        cloud_courses = self.course_ids[11:15]
        for i, course_id in enumerate(cloud_courses):
            tc = TrackCourse(
                track_id=self.track_ids[3],
                course_id=course_id,
                order=i + 1
            )
            session.add(tc)
        
        await session.commit()
        print("✅ Linked courses to tracks")

    async def seed_modules_and_lessons(self, session: AsyncSession):
        """Create modules and lessons for courses"""
        print("📖 Seeding modules and lessons...")
        
        # Create 3-5 modules per course
        for course_id in self.course_ids[:8]:  # Focus on first 8 courses for detailed content
            num_modules = random.randint(3, 5)
            
            for mod_num in range(1, num_modules + 1):
                module = Module(
                    id=uuid.uuid4(),
                    course_id=course_id,
                    title=f"Module {mod_num}: Core Concepts Part {mod_num}",
                    order=mod_num
                )
                session.add(module)
                self.module_ids.append(module.id)
                
                # Create 3-6 lessons per module
                num_lessons = random.randint(3, 6)
                for lesson_num in range(1, num_lessons + 1):
                    lesson = Lesson(
                        id=uuid.uuid4(),
                        module_id=module.id,
                        title=f"Lesson {mod_num}.{lesson_num}: Topic Overview",
                        content=f"This is the detailed content for lesson {lesson_num} in module {mod_num}. It covers important concepts and includes examples, exercises, and best practices.",
                        video_url=f"https://example.com/videos/lesson_{mod_num}_{lesson_num}.mp4",
                        order=lesson_num
                    )
                    session.add(lesson)
                    self.lesson_ids.append(lesson.id)
        
        await session.commit()
        print(f"✅ Created {len(self.module_ids)} modules and {len(self.lesson_ids)} lessons")

    async def seed_user_courses(self, session: AsyncSession):
        """Enroll users in courses"""
        print("📝 Enrolling users in courses...")
        
        # Main user enrolled in multiple courses with varying progress
        enrollments = [
            (self.course_ids[0], 100.0, True),  # Completed HTML/CSS
            (self.course_ids[1], 75.5, False),  # In progress JavaScript
            (self.course_ids[4], 45.0, False),  # In progress Python
            (self.course_ids[11], 30.0, False), # Started AWS
        ]
        
        for course_id, progress, completed in enrollments:
            uc = UserCourse(
                id=uuid.uuid4(),
                user_id=self.main_user_id,
                course_id=course_id,
                progress=progress,
                enrolled_at=datetime.now() - timedelta(days=random.randint(30, 90)),
                completed_at=datetime.now() - timedelta(days=random.randint(1, 15)) if completed else None
            )
            session.add(uc)
        
        # Other users with random enrollments
        for user_id in self.user_ids[1:6]:
            num_courses = random.randint(1, 4)
            selected_courses = random.sample(self.course_ids, num_courses)
            
            for course_id in selected_courses:
                uc = UserCourse(
                    id=uuid.uuid4(),
                    user_id=user_id,
                    course_id=course_id,
                    progress=random.uniform(10.0, 95.0),
                    enrolled_at=datetime.now() - timedelta(days=random.randint(20, 100))
                )
                session.add(uc)
        
        await session.commit()
        print("✅ Created course enrollments")

    async def seed_user_lessons(self, session: AsyncSession):
        """Mark lessons as completed for users"""
        print("✅ Seeding completed lessons...")
        
        # Main user has completed some lessons
        completed_lessons = random.sample(self.lesson_ids, min(20, len(self.lesson_ids)))
        for lesson_id in completed_lessons:
            ul = UserLesson(
                id=uuid.uuid4(),
                user_id=self.main_user_id,
                lesson_id=lesson_id,
                completed_at=datetime.now() - timedelta(days=random.randint(1, 30))
            )
            session.add(ul)
        
        await session.commit()
        print("✅ Created lesson completion records")

    async def seed_quizzes(self, session: AsyncSession):
        """Create quizzes with questions"""
        print("❓ Seeding quizzes...")
        
        # Create 2 quizzes per course (for first 6 courses)
        for course_id in self.course_ids[:6]:
            for quiz_num in range(1, 3):
                quiz = Quiz(
                    id=uuid.uuid4(),
                    course_id=course_id,
                    title=f"Quiz {quiz_num}: Knowledge Check",
                    description=f"Test your understanding of the concepts covered in this section.",
                    time_limit=30  # 30 minutes
                )
                session.add(quiz)
                self.quiz_ids.append(quiz.id)
                
                # Create 5-10 questions per quiz
                num_questions = random.randint(5, 10)
                for q_num in range(1, num_questions + 1):
                    question = QuizQuestion(
                        id=uuid.uuid4(),
                        quiz_id=quiz.id,
                        question=f"Question {q_num}: What is the correct answer to this sample question?",
                        options=["Option A", "Option B", "Option C", "Option D"],
                        correct_answer=random.randint(0, 3),
                        order=q_num
                    )
                    session.add(question)
        
        await session.commit()
        print(f"✅ Created {len(self.quiz_ids)} quizzes with questions")

    async def seed_user_quizzes(self, session: AsyncSession):
        """Create quiz attempts"""
        print("📊 Seeding quiz attempts...")
        
        # Main user has attempted several quizzes
        for quiz_id in random.sample(self.quiz_ids, min(5, len(self.quiz_ids))):
            uq = UserQuiz(
                id=uuid.uuid4(),
                user_id=self.main_user_id,
                quiz_id=quiz_id,
                score=random.uniform(60.0, 95.0),
                completed_at=datetime.now() - timedelta(days=random.randint(1, 20))
            )
            session.add(uq)
        
        await session.commit()
        print("✅ Created quiz attempts")

    async def seed_resources(self, session: AsyncSession):
        """Create learning resources"""
        print("📄 Seeding resources...")
        
        resources_data = [
            ("MDN Web Docs", "Comprehensive web development documentation", ResourceType.ARTICLE, "https://developer.mozilla.org", self.track_ids[0]),
            ("JavaScript Tutorial", "Interactive JavaScript learning", ResourceType.TUTORIAL, "https://javascript.info", self.track_ids[0]),
            ("Python Data Science Handbook", "Essential tools for data science", ResourceType.EBOOK, "https://jakevdp.github.io/PythonDataScienceHandbook", self.track_ids[1]),
            ("Machine Learning Course", "Stanford's ML course videos", ResourceType.VIDEO, "https://www.coursera.org/learn/machine-learning", self.track_ids[1]),
            ("React Native Docs", "Official React Native documentation", ResourceType.ARTICLE, "https://reactnative.dev", self.track_ids[2]),
            ("AWS Training", "Free AWS training videos", ResourceType.VIDEO, "https://aws.amazon.com/training", self.track_ids[3]),
            ("Docker Getting Started", "Docker fundamentals tutorial", ResourceType.TUTORIAL, "https://docs.docker.com/get-started", self.track_ids[3]),
            ("Clean Code", "Software craftsmanship guide", ResourceType.EBOOK, "https://example.com/clean-code", None),
        ]
        
        for title, desc, res_type, url, track_id in resources_data:
            resource = Resource(
                id=uuid.uuid4(),
                title=title,
                description=desc,
                type=res_type,
                url=url,
                track_id=track_id
            )
            session.add(resource)
            self.resource_ids.append(resource.id)
        
        await session.commit()
        print(f"✅ Created {len(self.resource_ids)} resources")

    async def seed_user_resources(self, session: AsyncSession):
        """Track resource access"""
        print("📑 Seeding user resource access...")
        
        # Main user has accessed several resources
        for resource_id in random.sample(self.resource_ids, min(5, len(self.resource_ids))):
            ur = UserResource(
                id=uuid.uuid4(),
                user_id=self.main_user_id,
                resource_id=resource_id,
                last_accessed=datetime.now() - timedelta(days=random.randint(0, 10))
            )
            session.add(ur)
        
        await session.commit()
        print("✅ Created resource access records")

    async def seed_achievements(self, session: AsyncSession):
        """Create achievements"""
        print("🏆 Seeding achievements...")
        
        achievements_data = [
            ("First Steps", "Complete your first lesson", "🎯"),
            ("Course Champion", "Complete an entire course", "🏅"),
            ("Quiz Master", "Score 90% or higher on 5 quizzes", "🧠"),
            ("Dedicated Learner", "Log in for 7 consecutive days", "📅"),
            ("Knowledge Seeker", "Enroll in 5 courses", "📚"),
            ("Fast Learner", "Complete 10 lessons in one day", "⚡"),
            ("Perfect Score", "Get 100% on a quiz", "💯"),
            ("Discussion Starter", "Create your first discussion topic", "💬"),
            ("Helper", "Reply to 10 discussions", "🤝"),
            ("Milestone", "Reach 1000 XP", "🎖️"),
        ]
        
        for title, desc, icon in achievements_data:
            achievement = Achievement(
                id=uuid.uuid4(),
                title=title,
                description=desc,
                icon_url=icon
            )
            session.add(achievement)
            self.achievement_ids.append(achievement.id)
        
        await session.commit()
        print(f"✅ Created {len(self.achievement_ids)} achievements")

    async def seed_user_achievements(self, session: AsyncSession):
        """Award achievements to users"""
        print("🎖️  Seeding user achievements...")
        
        # Main user has earned several achievements
        earned = random.sample(self.achievement_ids, min(6, len(self.achievement_ids)))
        for achievement_id in earned:
            ua = UserAchievement(
                id=uuid.uuid4(),
                user_id=self.main_user_id,
                achievement_id=achievement_id,
                earned_at=datetime.now() - timedelta(days=random.randint(1, 60))
            )
            session.add(ua)
        
        # Other users with random achievements
        for user_id in self.user_ids[1:4]:
            num_achievements = random.randint(2, 5)
            earned = random.sample(self.achievement_ids, min(num_achievements, len(self.achievement_ids)))
            for achievement_id in earned:
                ua = UserAchievement(
                    id=uuid.uuid4(),
                    user_id=user_id,
                    achievement_id=achievement_id,
                    earned_at=datetime.now() - timedelta(days=random.randint(1, 90))
                )
                session.add(ua)
        
        await session.commit()
        print("✅ Awarded achievements to users")

    async def seed_notifications(self, session: AsyncSession):
        """Create notifications"""
        print("🔔 Seeding notifications...")
        
        notifications_data = [
            (NotificationType.SUCCESS, "Congratulations! You've completed the HTML & CSS course!", False),
            (NotificationType.INFO, "New course available: Advanced React Patterns", False),
            (NotificationType.WARNING, "Your quiz attempt expires in 2 days", True),
            (NotificationType.SUCCESS, "Achievement unlocked: Quiz Master!", False),
            (NotificationType.INFO, "Your instructor replied to your discussion", True),
            (NotificationType.INFO, "Weekend challenge: Complete 3 lessons for bonus XP", True),
        ]
        
        for notif_type, message, is_read in notifications_data:
            notification = Notification(
                id=uuid.uuid4(),
                user_id=self.main_user_id,
                type=notif_type,
                message=message,
                read=is_read,
                created_at=datetime.now() - timedelta(days=random.randint(0, 7))
            )
            session.add(notification)
        
        await session.commit()
        print("✅ Created notifications")

    async def seed_discussions(self, session: AsyncSession):
        """Create discussion topics and replies"""
        print("💬 Seeding discussions...")
        
        discussions_data = [
            ("Help with React Hooks", "I'm having trouble understanding useEffect. Can someone explain when to use it?"),
            ("Best practices for API design", "What are your favorite patterns for designing RESTful APIs?"),
            ("Python vs JavaScript for beginners", "Which language would you recommend for someone just starting?"),
            ("Study group for AWS certification", "Anyone interested in forming a study group for AWS Solutions Architect?"),
        ]
        
        # Create discussions from different users
        for i, (title, content) in enumerate(discussions_data):
            user_id = self.main_user_id if i == 0 else random.choice(self.user_ids[1:5])
            discussion = Discussion(
                id=uuid.uuid4(),
                course_id=random.choice(self.course_ids[:8]),
                user_id=user_id,
                title=title,
                content=content
            )
            session.add(discussion)
            
            # Add 2-5 replies to each discussion
            num_replies = random.randint(2, 5)
            for j in range(num_replies):
                reply_user_id = random.choice(self.user_ids[:6])
                reply = DiscussionReply(
                    id=uuid.uuid4(),
                    discussion_id=discussion.id,
                    user_id=reply_user_id,
                    content=f"This is a helpful reply with insights and suggestions regarding the topic. Reply #{j+1}"
                )
                session.add(reply)
        
        await session.commit()
        print("✅ Created discussions and replies")

    async def seed_learning_paths(self, session: AsyncSession):
        """Create learning paths"""
        print("🗺️  Seeding learning paths...")
        
        # Main user's learning path
        lp = LearningPath(
            id=uuid.uuid4(),
            user_id=self.main_user_id,
            track_id=self.track_ids[0],  # Web Development track
            current_course_id=self.course_ids[1],  # JavaScript course
            progress=35.5
        )
        session.add(lp)
        
        # Other users' learning paths
        for i, user_id in enumerate(self.user_ids[1:4]):
            lp = LearningPath(
                id=uuid.uuid4(),
                user_id=user_id,
                track_id=self.track_ids[i % len(self.track_ids)],
                current_course_id=random.choice(self.course_ids),
                progress=random.uniform(10.0, 75.0)
            )
            session.add(lp)
        
        await session.commit()
        print("✅ Created learning paths")

    async def seed_skills(self, session: AsyncSession):
        """Create skills and (basic) mapping data."""
        print("🎯 Seeding skills...")
        skills_data = [
            ("JavaScript", "JavaScript programming language"),
            ("Python", "Python programming language"),
            ("React", "React.js framework"),
            ("Node.js", "Node.js runtime"),
            ("SQL", "SQL database queries"),
            ("Git", "Version control with Git"),
            ("Docker", "Containerization with Docker"),
            ("Kubernetes", "Container orchestration"),
            ("AWS", "Amazon Web Services fundamentals"),
            ("Data Analysis", "Data wrangling and visualization"),
            ("Machine Learning", "ML algorithms and workflows"),
            ("TensorFlow", "Deep learning with TensorFlow"),
            ("Leadership", "Teamwork and leadership skills"),
            ("UI/UX", "User interface and experience design"),
            ("Testing", "Unit and integration testing"),
        ]

        for name, desc in skills_data:
            skill = Skill(
                id=uuid.uuid4(),
                name=name,
                description=desc
            )
            session.add(skill)
            self.skill_ids.append(skill.id)

        await session.commit()
        print(f"✅ Created {len(self.skill_ids)} skills")

    async def seed_user_skills(self, session: AsyncSession):
        """Attach skills to users with proficiency values."""
        print("🧩 Seeding user skills...")
        # Give main user a set of core skills with higher proficiencies
        main_skills = random.sample(self.skill_ids, min(6, len(self.skill_ids)))
        for idx, skill_id in enumerate(main_skills):
            us = UserSkill(
                id=uuid.uuid4(),
                user_id=self.main_user_id,
                skill_id=skill_id,
                proficiency=round(random.uniform(40.0 + idx * 5, 90.0), 2)  # ramp up proficiency
            )
            session.add(us)

        # Give other users some random skills
        for user_id in self.user_ids[1:8]:
            chosen = random.sample(self.skill_ids, random.randint(1, min(5, len(self.skill_ids))))
            for skill_id in chosen:
                us = UserSkill(
                    id=uuid.uuid4(),
                    user_id=user_id,
                    skill_id=skill_id,
                    proficiency=round(random.uniform(10.0, 85.0), 2)
                )
                session.add(us)

        await session.commit()
        print("✅ Created user-skills mappings")

    async def seed_deadlines(self, session: AsyncSession):
        """Create some deadlines (past and future) associated with courses."""
        print("⏰ Seeding deadlines...")
        if not self.course_ids:
            print("⚠️  No courses available to attach deadlines to. Skipping deadlines.")
            return

        now = datetime.utcnow()
        for i in range(8):
            course_id = random.choice(self.course_ids)
            # Mix of past and future due dates
            days_offset = random.randint(-30, 60)
            due_date = now + timedelta(days=days_offset)
            dl = Deadline(
                id=uuid.uuid4(),
                title=f"Assignment {i+1}",
                description=f"Assignment {i+1} for course {course_id}",
                due_date=due_date,
                course_id=course_id
            )
            session.add(dl)

        await session.commit()
        print("✅ Created deadlines")

    async def run_all(self, session: AsyncSession):
        """Run the full seeding pipeline in order."""
        # The methods below are assumed defined earlier in the script (Claude's output).
        # If you pasted the earlier chunk exactly, these will exist. If not, add them.
        await self.clear_database(session)
        await self.seed_users(session)
        await self.seed_user_logins(session)
        await self.seed_tracks(session)
        await self.seed_courses(session)
        await self.seed_track_courses(session)
        await self.seed_modules_and_lessons(session)
        await self.seed_user_courses(session)
        await self.seed_user_lessons(session)
        await self.seed_quizzes(session)
        await self.seed_user_quizzes(session)
        await self.seed_resources(session)
        await self.seed_user_resources(session)
        await self.seed_achievements(session)
        await self.seed_user_achievements(session)
        await self.seed_notifications(session)
        await self.seed_discussions(session)
        await self.seed_learning_paths(session)

        # Newly completed parts:
        await self.seed_skills(session)
        await self.seed_user_skills(session)
        await self.seed_deadlines(session)

        print("🎉 Seeding complete!")

# --- Runner ---
async def main():
    seeder = DatabaseSeeder()

    # Use sessionmaker from your database module (the compatibility shim above)
    # Note: async_session is a sessionmaker factory (e.g. sessionmaker(engine, class_=AsyncSession, ...))
    async with async_session() as session:
        try:
            await seeder.run_all(session)
        except Exception as exc:
            print("❌ Error during seeding:", exc)
            await session.rollback()
            raise
        finally:
            # best-effort connection cleanup
            try:
                await engine.dispose()
            except Exception:
                pass

if __name__ == "__main__":
    asyncio.run(main())