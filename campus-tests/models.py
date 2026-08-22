from pathlib import Path

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, create_engine, text
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True)
    round_type = Column(String, nullable=False)  # "aptitude" | "programming"
    topic = Column(String, nullable=False)
    difficulty = Column(String, nullable=False)  # "easy" | "medium" | "hard"
    text = Column(Text, nullable=False)
    option_a = Column(String, nullable=False)
    option_b = Column(String, nullable=False)
    option_c = Column(String, nullable=False)
    option_d = Column(String, nullable=False)
    correct_option = Column(String, nullable=False)  # "A" | "B" | "C" | "D"
    points = Column(Integer, nullable=False, default=1)


class Drive(Base):
    __tablename__ = "drives"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    campus = Column(String, nullable=False)


class Round(Base):
    __tablename__ = "rounds"

    id = Column(Integer, primary_key=True)
    drive_id = Column(Integer, ForeignKey("drives.id"), nullable=False)
    round_type = Column(String, nullable=False)
    form_id = Column(String)
    responder_uri = Column(String)
    cutoff_high = Column(Integer, nullable=False, default=75)
    cutoff_low = Column(Integer, nullable=False, default=60)
    duration_minutes = Column(Integer, nullable=False, default=45)
    coding_question_count = Column(Integer, nullable=False, default=2)  # coding rounds only, used when section_plan is not set
    section_plan = Column(Text)  # coding rounds only: JSON list of [topic, count] pairs, in display order - overrides coding_question_count when set
    interview_question_count = Column(Integer, nullable=False, default=4)  # technical_discussion rounds only

    drive = relationship("Drive")


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True)
    drive_id = Column(Integer, ForeignKey("drives.id"), nullable=False)
    email = Column(String, nullable=False)
    name = Column(String, nullable=False)

    drive = relationship("Drive")


class Attempt(Base):
    __tablename__ = "attempts"

    id = Column(Integer, primary_key=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    round_id = Column(Integer, ForeignKey("rounds.id"), nullable=False)
    token = Column(String, unique=True)
    status = Column(String, nullable=False, default="invited")  # invited|started|submitted
    started_at = Column(String)
    session_started_at = Column(String)  # coding rounds only: server-side timer anchor
    score = Column(Integer)
    max_score = Column(Integer)
    percent = Column(Integer)
    band = Column(String)  # shortlisted|borderline|rejected
    submitted_at = Column(String)
    decision = Column(String)  # technical_discussion rounds only: selected|hold|rejected
    decision_by = Column(String)  # interviewer/admin name who last set the decision
    decision_at = Column(String)

    candidate = relationship("Candidate")
    round = relationship("Round")


class CodingQuestion(Base):
    __tablename__ = "coding_questions"

    id = Column(Integer, primary_key=True)
    external_id = Column(String, unique=True, nullable=False)  # authoring reference, e.g. "PY-01"
    topic = Column(String, nullable=False)
    difficulty = Column(String, nullable=False)
    title = Column(String, nullable=False)
    statement = Column(Text, nullable=False)
    starter_code = Column(Text)
    language_id = Column(Integer, nullable=False)  # Judge0 language id, e.g. 71 = Python 3.8.1
    hints = Column(Text)  # newline-separated
    points = Column(Integer, nullable=False, default=10)
    question_type = Column(String, nullable=False, default="code")  # code|sql|react|css
    harness_fixture = Column(Text)  # test-side, not shown to candidate: sql schema+seed DDL, css HTML scaffold
    suggested_minutes = Column(Integer, nullable=False, default=5)  # used to derive a round's total suggested duration


class CodingTestCase(Base):
    __tablename__ = "coding_test_cases"

    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey("coding_questions.id"), nullable=False)
    stdin = Column(Text, default="")
    expected_output = Column(Text, nullable=False)
    is_sample = Column(Boolean, nullable=False, default=False)  # sample: shown to candidate for "Run"; hidden: used only for "Submit" grading
    weight = Column(Integer, nullable=False, default=1)
    assertion_script = Column(Text)  # react|css only: script that asserts against rendered output
    ordered = Column(Boolean, nullable=False, default=False)  # sql only: whether row order matters for the diff

    question = relationship("CodingQuestion")


class CodingAttemptQuestion(Base):
    """One row per (Attempt, CodingQuestion) assigned to that candidate's
    session - pinned at assignment time so reloading never reshuffles."""

    __tablename__ = "coding_attempt_questions"

    id = Column(Integer, primary_key=True)
    attempt_id = Column(Integer, ForeignKey("attempts.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("coding_questions.id"), nullable=False)
    assigned_order = Column(Integer, nullable=False)
    status = Column(String, nullable=False, default="not_attempted")  # not_attempted|attempted|passed|partial|failed
    best_score = Column(Integer, nullable=False, default=0)
    last_submitted_code = Column(Text)
    submitted_at = Column(String)

    attempt = relationship("Attempt")
    question = relationship("CodingQuestion")


class InterviewQuestion(Base):
    """Bank of Technical Discussion questions - one interviewer-facing
    prompt plus a rubric_guide (what to listen for, scored 1-5) shown
    alongside it as an evaluation aid."""

    __tablename__ = "interview_questions"

    id = Column(Integer, primary_key=True)
    external_id = Column(String, unique=True, nullable=False)  # e.g. "TD-01"
    area = Column(String, nullable=False)  # e.g. llm_api_experience|prompt_quality|git_workflow|vibe_coding
    question = Column(Text, nullable=False)
    rubric_guide = Column(Text, nullable=False)  # what a strong/weak answer looks like - interviewer aid
    max_score = Column(Integer, nullable=False, default=5)


class InterviewAttemptQuestion(Base):
    """One row per (Attempt, InterviewQuestion) assigned to that candidate's
    technical discussion - pinned at assignment time, same idempotent
    pattern as CodingAttemptQuestion. score/notes are entered live by the
    interviewer during the discussion, not by the candidate."""

    __tablename__ = "interview_attempt_questions"

    id = Column(Integer, primary_key=True)
    attempt_id = Column(Integer, ForeignKey("attempts.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("interview_questions.id"), nullable=False)
    assigned_order = Column(Integer, nullable=False)
    score = Column(Integer)  # interviewer-entered, 1..max_score
    notes = Column(Text)

    attempt = relationship("Attempt")
    question = relationship("InterviewQuestion")


class FormAnswer(Base):
    """One row per (Attempt, question) for a Google Forms MCQ round -
    captured at ingest time so results can show a real per-question review
    (selected vs. correct answer), not just an aggregate score. Replaced
    wholesale on every re-ingest for a given attempt, same idempotent
    pattern as CodingTestCase."""

    __tablename__ = "form_answers"

    id = Column(Integer, primary_key=True)
    attempt_id = Column(Integer, ForeignKey("attempts.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    selected_answer = Column(Text)
    correct_answer = Column(Text)
    is_correct = Column(Boolean, nullable=False, default=False)

    attempt = relationship("Attempt")


DB_PATH = Path(__file__).parent / "data" / "campus.db"
engine = create_engine(f"sqlite:///{DB_PATH}")
SessionLocal = sessionmaker(bind=engine)


def _add_column_if_missing(conn, table: str, column: str, ddl_type: str, default_sql: str) -> None:
    existing = {row[1] for row in conn.execute(text(f"PRAGMA table_info({table})"))}
    if column not in existing:
        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl_type} DEFAULT {default_sql}"))


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(engine)

    # create_all() only creates missing tables, not missing columns on existing
    # tables - these columns were added after coding_questions/coding_test_cases
    # already existed in deployed DBs, so they need an explicit migration.
    with engine.begin() as conn:
        _add_column_if_missing(conn, "coding_questions", "question_type", "VARCHAR", "'code'")
        _add_column_if_missing(conn, "coding_questions", "harness_fixture", "TEXT", "NULL")
        _add_column_if_missing(conn, "coding_test_cases", "assertion_script", "TEXT", "NULL")
        _add_column_if_missing(conn, "coding_test_cases", "ordered", "BOOLEAN", "0")
        _add_column_if_missing(conn, "rounds", "interview_question_count", "INTEGER", "4")
        _add_column_if_missing(conn, "attempts", "decision", "VARCHAR", "NULL")
        _add_column_if_missing(conn, "attempts", "decision_by", "VARCHAR", "NULL")
        _add_column_if_missing(conn, "attempts", "decision_at", "VARCHAR", "NULL")
        _add_column_if_missing(conn, "rounds", "section_plan", "TEXT", "NULL")
        _add_column_if_missing(conn, "coding_questions", "suggested_minutes", "INTEGER", "5")
