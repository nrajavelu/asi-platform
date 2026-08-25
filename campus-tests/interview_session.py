"""
Assigns a random set of Technical Discussion questions to a candidate's
Attempt the first time an interviewer opens their session, pinning the
selection so re-opening the link never reshuffles mid-discussion.
"""

import random

from models import InterviewAttemptQuestion, InterviewQuestion


def assign_interview_questions(session, attempt, count: int, areas: list[str] | None = None):
    """Idempotent: if this attempt already has assigned questions, returns
    them unchanged instead of re-rolling."""
    existing = (
        session.query(InterviewAttemptQuestion)
        .filter_by(attempt_id=attempt.id)
        .order_by(InterviewAttemptQuestion.assigned_order)
        .all()
    )
    if existing:
        return existing

    query = session.query(InterviewQuestion)
    if areas:
        query = query.filter(InterviewQuestion.area.in_(areas))
    pool = query.all()
    if len(pool) < count:
        raise ValueError(
            f"Only {len(pool)} interview question(s) available "
            f"(areas={areas or 'all'}); requested {count}."
        )

    chosen = random.sample(pool, count)
    assigned = []
    for order, question in enumerate(chosen, start=1):
        row = InterviewAttemptQuestion(
            attempt_id=attempt.id,
            question_id=question.id,
            assigned_order=order,
        )
        session.add(row)
        assigned.append(row)
    session.commit()
    return assigned
