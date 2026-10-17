import os
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, Email, EqualTo
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func


def _normalize_database_url(database_url):
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+psycopg://", 1)
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return database_url


app = Flask(__name__)
secret_key = os.environ.get("SECRET_KEY")
debug_enabled = os.environ.get("FLASK_DEBUG") == "1"
if not secret_key and not debug_enabled:
    raise RuntimeError("Set SECRET_KEY before starting the app, or set FLASK_DEBUG=1 for local development.")
app.config["SECRET_KEY"] = secret_key or "local-only-development-secret"
database_url = os.environ.get("DATABASE_URL", "sqlite:///school.db")
app.config["SQLALCHEMY_DATABASE_URI"] = _normalize_database_url(database_url)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("COOKIE_SECURE") == "1"

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message_category = "warning"


# ----------------------------- Database models -----------------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="student")  # admin, teacher, student
    display_name = db.Column(db.String(120), nullable=False)
    active = db.Column(db.Boolean, default=True, nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    admission_no = db.Column(db.String(30), unique=True, nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    gender = db.Column(db.String(20), default="Not specified")
    date_of_birth = db.Column(db.String(20))
    class_name = db.Column(db.String(40), nullable=False)
    section = db.Column(db.String(10), default="A")
    guardian_name = db.Column(db.String(120))
    guardian_phone = db.Column(db.String(30))
    email = db.Column(db.String(120))
    address = db.Column(db.String(250))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship("User", backref=db.backref("student_profile", uselist=False))
    marks = db.relationship("Mark", back_populates="student", cascade="all, delete-orphan")


class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    max_marks = db.Column(db.Integer, nullable=False, default=100)


class Mark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey("subject.id"), nullable=False)
    exam_name = db.Column(db.String(80), nullable=False, default="Final Examination")
    academic_year = db.Column(db.String(20), nullable=False, default="2026")
    marks_obtained = db.Column(db.Float, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    student = db.relationship("Student", back_populates="marks")
    subject = db.relationship("Subject")
    __table_args__ = (db.UniqueConstraint("student_id", "subject_id", "exam_name", "academic_year", name="unique_student_exam_subject"),)


# --------------------------------- Forms -----------------------------------
class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(max=80)])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Sign in")


class StudentForm(FlaskForm):
    admission_no = StringField("Admission number", validators=[DataRequired(), Length(max=30)])
    full_name = StringField("Full name", validators=[DataRequired(), Length(max=120)])
    gender = SelectField("Gender", choices=[("Not specified", "Not specified"), ("Female", "Female"), ("Male", "Male"), ("Other", "Other")])
    date_of_birth = StringField("Date of birth", validators=[Optional()])
    class_name = SelectField("Class", choices=[(str(x), f"Grade {x}") for x in range(1, 13)], validators=[DataRequired()])
    section = SelectField("Section", choices=[("A", "A"), ("B", "B"), ("C", "C"), ("D", "D")])
    guardian_name = StringField("Guardian name", validators=[Optional(), Length(max=120)])
    guardian_phone = StringField("Guardian phone", validators=[Optional(), Length(max=30)])
    email = StringField("Email", validators=[Optional(), Email(), Length(max=120)])
    address = StringField("Address", validators=[Optional(), Length(max=250)])
    username = StringField("Student login username", validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField("Student login password", validators=[Optional(), Length(min=8, message="Use at least 8 characters.")])
    submit = SubmitField("Save student")


class SubjectForm(FlaskForm):
    name = StringField("Subject name", validators=[DataRequired(), Length(max=100)])
    code = StringField("Subject code", validators=[DataRequired(), Length(max=20)])
    max_marks = IntegerField("Maximum marks", validators=[DataRequired(), NumberRange(min=1, max=1000)], default=100)
    submit = SubmitField("Add subject")


class MarkForm(FlaskForm):
    student_id = SelectField("Student", coerce=int, validators=[DataRequired()])
    subject_id = SelectField("Subject", coerce=int, validators=[DataRequired()])
    exam_name = SelectField("Examination", choices=[("First Terminal", "First Terminal"), ("Second Terminal", "Second Terminal"), ("Final Examination", "Final Examination")])
    academic_year = SelectField("Academic year", choices=[("2025-26", "2025–26"), ("2026-27", "2026–27"), ("2027-28", "2027–28")])
    marks_obtained = IntegerField("Marks obtained", validators=[DataRequired(), NumberRange(min=0, max=1000)])
    submit = SubmitField("Save result")


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def roles_required(*roles):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            if current_user.role not in roles:
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator


def grade_for(percentage):
    if percentage >= 90: return "A+"
    if percentage >= 80: return "A"
    if percentage >= 70: return "B+"
    if percentage >= 60: return "B"
    if percentage >= 50: return "C"
    if percentage >= 40: return "D"
    return "F"


def student_result(student, exam_name=None, academic_year=None):
    query = Mark.query.filter_by(student_id=student.id)
    if exam_name:
        query = query.filter_by(exam_name=exam_name)
    if academic_year:
        query = query.filter_by(academic_year=academic_year)
    marks = query.join(Subject).order_by(Subject.name).all()
    max_total = sum(m.subject.max_marks for m in marks)
    obtained = sum(m.marks_obtained for m in marks)
    percentage = (obtained / max_total * 100) if max_total else 0
    return marks, max_total, obtained, percentage, grade_for(percentage) if marks else "—"


# ---------------------------------- Routes ---------------------------------
@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/healthz")
def health_check():
    return {"status": "ok"}, 200


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data.strip()).first()
        if user and user.active and user.check_password(form.password.data):
            login_user(user)
            flash(f"Welcome back, {user.display_name}!", "success")
            return redirect(url_for("dashboard"))
        flash("Invalid username or password.", "danger")
    return render_template("login.html", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been signed out.", "info")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    if current_user.role == "student":
        student = Student.query.filter_by(user_id=current_user.id).first()
        if not student:
            abort(404)
        marks, max_total, obtained, percentage, grade = student_result(student)
        recent_marks = Mark.query.filter_by(student_id=student.id).order_by(Mark.updated_at.desc()).limit(5).all()
        return render_template("dashboard_student.html", student=student, marks=marks, max_total=max_total,
                               obtained=obtained, percentage=percentage, grade=grade, recent_marks=recent_marks)
    student_count = Student.query.count()
    subject_count = Subject.query.count()
    mark_count = Mark.query.count()
    class_count = db.session.query(Student.class_name).distinct().count()
    latest_students = Student.query.order_by(Student.created_at.desc()).limit(6).all()
    recent_marks = Mark.query.order_by(Mark.updated_at.desc()).limit(6).all()
    grade_stats = db.session.query(Student.class_name, func.count(Student.id)).group_by(Student.class_name).order_by(Student.class_name).all()
    return render_template("dashboard.html", student_count=student_count, subject_count=subject_count,
                           mark_count=mark_count, class_count=class_count, latest_students=latest_students,
                           recent_marks=recent_marks, grade_stats=grade_stats)


@app.route("/students")
@roles_required("admin", "teacher")
def students():
    search = request.args.get("q", "").strip()
    class_filter = request.args.get("class", "").strip()
    query = Student.query
    if search:
        query = query.filter(db.or_(Student.full_name.ilike(f"%{search}%"), Student.admission_no.ilike(f"%{search}%")))
    if class_filter:
        query = query.filter_by(class_name=class_filter)
    records = query.order_by(Student.class_name, Student.full_name).all()
    return render_template("students.html", students=records, search=search, class_filter=class_filter)


@app.route("/students/new", methods=["GET", "POST"])
@roles_required("admin")
def student_new():
    form = StudentForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        if User.query.filter_by(username=username).first():
            flash("That username is already in use.", "danger")
        elif Student.query.filter_by(admission_no=form.admission_no.data.strip()).first():
            flash("That admission number already exists.", "danger")
        elif not form.password.data:
            flash("Set a password for the student's account.", "danger")
        else:
            user = User(username=username, role="student", display_name=form.full_name.data.strip())
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.flush()
            student = Student(
                admission_no=form.admission_no.data.strip(), full_name=form.full_name.data.strip(),
                gender=form.gender.data, date_of_birth=form.date_of_birth.data,
                class_name=form.class_name.data, section=form.section.data,
                guardian_name=form.guardian_name.data, guardian_phone=form.guardian_phone.data,
                email=form.email.data, address=form.address.data, user_id=user.id
            )
            db.session.add(student)
            db.session.commit()
            flash("Student and login account created successfully.", "success")
            return redirect(url_for("students"))
    return render_template("student_form.html", form=form, title="Add student")


@app.route("/students/<int:student_id>")
@login_required
def student_detail(student_id):
    student = db.get_or_404(Student, student_id)
    if current_user.role == "student" and student.user_id != current_user.id:
        abort(403)
    if current_user.role not in ("admin", "teacher", "student"):
        abort(403)
    exams = db.session.query(Mark.exam_name, Mark.academic_year).filter_by(student_id=student.id).distinct().all()
    results = []
    for exam_name, year in exams:
        marks, maximum, obtained, percentage, grade = student_result(student, exam_name, year)
        results.append({"exam_name": exam_name, "academic_year": year, "marks": marks, "maximum": maximum,
                        "obtained": obtained, "percentage": percentage, "grade": grade})
    return render_template("student_detail.html", student=student, results=results)


@app.route("/subjects", methods=["GET", "POST"])
@roles_required("admin", "teacher")
def subjects():
    form = SubjectForm()
    if current_user.role == "admin" and form.validate_on_submit():
        if Subject.query.filter(db.or_(Subject.name.ilike(form.name.data.strip()), Subject.code.ilike(form.code.data.strip()))).first():
            flash("A subject with that name or code already exists.", "danger")
        else:
            db.session.add(Subject(name=form.name.data.strip(), code=form.code.data.strip().upper(), max_marks=form.max_marks.data))
            db.session.commit()
            flash("Subject added.", "success")
            return redirect(url_for("subjects"))
    return render_template("subjects.html", subjects=Subject.query.order_by(Subject.name).all(), form=form)


@app.route("/results")
@login_required
def results():
    if current_user.role == "student":
        student = Student.query.filter_by(user_id=current_user.id).first_or_404()
        students_list = [student]
    elif current_user.role in ("admin", "teacher"):
        students_list = Student.query.order_by(Student.class_name, Student.full_name).all()
    else:
        abort(403)
    exam_filter = request.args.get("exam", "").strip()
    year_filter = request.args.get("year", "").strip()
    class_filter = request.args.get("class", "").strip()
    rows = []
    for student in students_list:
        if class_filter and student.class_name != class_filter:
            continue
        exams = db.session.query(Mark.exam_name, Mark.academic_year).filter_by(student_id=student.id).distinct().all()
        for exam_name, year in exams:
            if exam_filter and exam_name != exam_filter: continue
            if year_filter and year != year_filter: continue
            _, maximum, obtained, percentage, grade = student_result(student, exam_name, year)
            rows.append({"student": student, "exam": exam_name, "year": year, "maximum": maximum,
                         "obtained": obtained, "percentage": percentage, "grade": grade})
    rows.sort(key=lambda r: (int(r["student"].class_name), r["student"].full_name, r["exam"]))
    return render_template("results.html", rows=rows, exam_filter=exam_filter, year_filter=year_filter,
                           class_filter=class_filter)


@app.route("/results/marks", methods=["GET", "POST"])
@roles_required("admin", "teacher")
def marks_entry():
    form = MarkForm()
    form.student_id.choices = [(s.id, f"{s.full_name} — Grade {s.class_name}{s.section} ({s.admission_no})") for s in Student.query.order_by(Student.full_name).all()]
    form.subject_id.choices = [(s.id, f"{s.name} (max {s.max_marks})") for s in Subject.query.order_by(Subject.name).all()]
    if form.validate_on_submit():
        student = db.get_or_404(Student, form.student_id.data)
        subject = db.get_or_404(Subject, form.subject_id.data)
        if form.marks_obtained.data > subject.max_marks:
            flash(f"Marks cannot exceed {subject.max_marks} for {subject.name}.", "danger")
        else:
            mark = Mark.query.filter_by(student_id=student.id, subject_id=subject.id,
                                        exam_name=form.exam_name.data, academic_year=form.academic_year.data).first()
            if mark:
                mark.marks_obtained = form.marks_obtained.data
            else:
                db.session.add(Mark(student_id=student.id, subject_id=subject.id, exam_name=form.exam_name.data,
                                    academic_year=form.academic_year.data, marks_obtained=form.marks_obtained.data))
            db.session.commit()
            flash("Marks saved successfully.", "success")
            return redirect(url_for("results"))
    return render_template("marks_form.html", form=form)


@app.route("/users")
@roles_required("admin")
def users():
    all_users = User.query.order_by(User.role, User.username).all()
    return render_template("users.html", users=all_users)


@app.route("/users/<int:user_id>/toggle", methods=["POST"])
@roles_required("admin")
def toggle_user(user_id):
    user = db.get_or_404(User, user_id)
    if user.id == current_user.id:
        flash("You cannot deactivate your own account.", "warning")
    else:
        user.active = not user.active
        db.session.commit()
        flash(f"Account {'activated' if user.active else 'deactivated'}.", "success")
    return redirect(url_for("users"))


@app.errorhandler(403)
def forbidden(_error):
    return render_template("error.html", code=403, message="You do not have permission to view this page."), 403


@app.errorhandler(404)
def not_found(_error):
    return render_template("error.html", code=404, message="The requested page could not be found."), 404


def seed_demo_data():
    """Create demo data only when explicitly enabled, or bootstrap an initial admin."""
    if User.query.first():
        return
    if os.environ.get("SEED_DEMO_DATA") != "1":
        initial_password = os.environ.get("INITIAL_ADMIN_PASSWORD")
        if not initial_password:
            app.logger.warning(
                "Database is empty. Set INITIAL_ADMIN_PASSWORD to create the first administrator."
            )
            return
        if len(initial_password) < 12:
            raise RuntimeError("INITIAL_ADMIN_PASSWORD must contain at least 12 characters.")
        admin = User(username="admin", role="admin", display_name="School Administrator")
        admin.set_password(initial_password)
        db.session.add(admin)
        db.session.commit()
        app.logger.info("Created the initial administrator account.")
        return

    admin = User(username="admin", role="admin", display_name="School Administrator")
    admin.set_password(os.environ.get("DEMO_ADMIN_PASSWORD", "Admin@12345"))
    teacher = User(username="teacher", role="teacher", display_name="Demo Teacher")
    teacher.set_password("Teacher@123")
    student_user = User(username="student", role="student", display_name="Aarav Sharma")
    student_user.set_password("Student@123")
    db.session.add_all([admin, teacher, student_user])
    db.session.flush()
    student = Student(admission_no="DEMO-2026-001", full_name="Aarav Sharma", gender="Male",
                      date_of_birth="2010-05-14", class_name="10", section="A",
                      guardian_name="Ramesh Sharma", guardian_phone="9800000000",
                      email="aarav@example.com", address="Sample City", user_id=student_user.id)
    db.session.add(student)
    db.session.add_all([
        Subject(name="English", code="ENG", max_marks=100),
        Subject(name="Mathematics", code="MATH", max_marks=100),
        Subject(name="Science", code="SCI", max_marks=100),
        Subject(name="Social Studies", code="SOC", max_marks=100),
        Subject(name="Computer Science", code="CS", max_marks=100),
    ])
    db.session.flush()
    for subject, score in zip(Subject.query.order_by(Subject.id).all(), [86, 94, 89, 82, 97]):
        db.session.add(Mark(student_id=student.id, subject_id=subject.id, exam_name="Final Examination",
                            academic_year="2026-27", marks_obtained=score))
    db.session.commit()


with app.app_context():
    db.create_all()
    seed_demo_data()


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "0") == "1")
