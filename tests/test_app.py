import os

os.environ["SECRET_KEY"] = "test-only-secret-key"
os.environ["FLASK_DEBUG"] = "1"
os.environ["SEED_DEMO_DATA"] = "1"
os.environ["DATABASE_URL"] = "sqlite://"

import pytest

from app import Mark, Student, Subject, User, app, db, grade_for, seed_demo_data, student_result

app.config["WTF_CSRF_ENABLED"] = False


@pytest.fixture
def client():
    with app.app_context():
        db.drop_all()
        db.create_all()
        seed_demo_data()

    with app.test_client() as test_client:
        yield test_client

    with app.app_context():
        db.session.remove()
        db.drop_all()


def login(client, username, password):
    return client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=True,
    )


def test_staff_can_sign_in_and_view_dashboard(client):
    response = login(client, "admin", "Admin@12345")

    assert response.status_code == 200
    assert b"Dashboard overview" in response.data
    assert b"Total students" in response.data


def test_student_cannot_view_another_students_profile(client):
    with app.app_context():
        other_user = User(username="other", role="student", display_name="Other Student")
        other_user.set_password("other-password")
        db.session.add(other_user)
        db.session.flush()
        other_student = Student(
            admission_no="TEST-002",
            full_name="Other Student",
            class_name="11",
            user_id=other_user.id,
        )
        db.session.add(other_student)
        db.session.commit()
        other_student_id = other_student.id

    login(client, "student", "Student@123")

    assert client.get(f"/students/{other_student_id}").status_code == 403


def test_student_results_are_limited_to_their_own_records(client):
    with app.app_context():
        other_user = User(username="other", role="student", display_name="Other Student")
        other_user.set_password("other-password")
        db.session.add(other_user)
        db.session.flush()
        db.session.add(
            Student(
                admission_no="TEST-002",
                full_name="Other Student",
                class_name="11",
                user_id=other_user.id,
            )
        )
        db.session.commit()

    login(client, "student", "Student@123")
    response = client.get("/results")

    assert response.status_code == 200
    assert b"Aarav Sharma" in response.data
    assert b"Other Student" not in response.data


def test_teacher_can_view_students_but_not_user_accounts(client):
    login(client, "teacher", "Teacher@123")

    assert client.get("/students").status_code == 200
    assert client.get("/users").status_code == 403


def test_marks_above_subject_maximum_are_rejected(client):
    login(client, "admin", "Admin@12345")
    with app.app_context():
        student_id = Student.query.filter_by(admission_no="DEMO-2026-001").one().id
        subject_id = Subject.query.filter_by(code="ENG").one().id

    response = client.post(
        "/results/marks",
        data={
            "student_id": student_id,
            "subject_id": subject_id,
            "exam_name": "First Terminal",
            "academic_year": "2026-27",
            "marks_obtained": 101,
        },
    )

    assert response.status_code == 200
    assert b"Marks cannot exceed 100" in response.data
    with app.app_context():
        assert (
            Mark.query.filter_by(
                student_id=student_id,
                subject_id=subject_id,
                exam_name="First Terminal",
                academic_year="2026-27",
            ).first()
            is None
        )


def test_saving_same_assessment_updates_existing_mark(client):
    login(client, "admin", "Admin@12345")
    with app.app_context():
        student_id = Student.query.filter_by(admission_no="DEMO-2026-001").one().id
        subject_id = Subject.query.filter_by(code="ENG").one().id

    form_data = {
        "student_id": student_id,
        "subject_id": subject_id,
        "exam_name": "First Terminal",
        "academic_year": "2026-27",
    }
    assert client.post(
        "/results/marks", data={**form_data, "marks_obtained": 75}
    ).status_code == 302
    assert client.post(
        "/results/marks", data={**form_data, "marks_obtained": 91}
    ).status_code == 302

    with app.app_context():
        records = Mark.query.filter_by(
            student_id=student_id,
            subject_id=subject_id,
            exam_name="First Terminal",
            academic_year="2026-27",
        ).all()
        assert len(records) == 1
        assert records[0].marks_obtained == 91


def test_demo_result_percentage_and_grade_are_calculated(client):
    with app.app_context():
        student = Student.query.filter_by(admission_no="DEMO-2026-001").one()
        _, maximum, obtained, percentage, grade = student_result(
            student, "Final Examination", "2026-27"
        )

    assert maximum == 500
    assert obtained == 448
    assert percentage == pytest.approx(89.6)
    assert grade == "A"


@pytest.mark.parametrize(
    ("percentage", "expected"),
    [
        (90, "A+"),
        (89.99, "A"),
        (80, "A"),
        (70, "B+"),
        (60, "B"),
        (50, "C"),
        (40, "D"),
        (39.99, "F"),
    ],
)
def test_grade_boundaries(percentage, expected):
    assert grade_for(percentage) == expected
