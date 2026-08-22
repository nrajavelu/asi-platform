"""
Assigns a set of coding questions to a candidate's Attempt the first time
they access their coding session, pinning the selection so it never
reshuffles on reload.

Two assignment modes:
  - Flat random (default): `count` questions randomly drawn from the whole
    bank (optionally topic-filtered), in random order - the original
    behavior, unchanged for any round that doesn't set a section_plan.
  - Sectioned (when the round has a section_plan): an ordered list of
    (topic, count) pairs - each section's questions are randomly sampled
    from just that topic, then sections are concatenated in the plan's
    order, so every candidate sees the same section sequence (e.g. all
    DSA questions, then all SQL questions) while the specific questions
    within each section are still randomized per candidate.
"""

import random

from models import CodingAttemptQuestion, CodingQuestion


def _assign(session, attempt, chosen: list[CodingQuestion]):
    assigned = []
    for order, question in enumerate(chosen, start=1):
        row = CodingAttemptQuestion(
            attempt_id=attempt.id,
            question_id=question.id,
            assigned_order=order,
        )
        session.add(row)
        assigned.append(row)
    session.commit()
    return assigned


def assign_coding_questions(session, attempt, count: int, topics: list[str] | None = None):
    """Idempotent: if this attempt already has assigned questions, returns
    them unchanged instead of re-rolling."""
    existing = (
        session.query(CodingAttemptQuestion)
        .filter_by(attempt_id=attempt.id)
        .order_by(CodingAttemptQuestion.assigned_order)
        .all()
    )
    if existing:
        return existing

    query = session.query(CodingQuestion)
    if topics:
        query = query.filter(CodingQuestion.topic.in_(topics))
    pool = query.all()
    if len(pool) < count:
        raise SystemExit(
            f"Only {len(pool)} coding question(s) available "
            f"(topics={topics or 'all'}); requested {count}."
        )

    chosen = random.sample(pool, count)
    return _assign(session, attempt, chosen)


def assign_sectioned_coding_questions(session, attempt, section_plan: list[tuple[str, int]]):
    """section_plan: ordered [(topic, count), ...] pairs, e.g.
    [("dsa", 7), ("sql", 3), ("prompt_assembly", 2), ("api_handling", 3)].
    Idempotent, same as assign_coding_questions."""
    existing = (
        session.query(CodingAttemptQuestion)
        .filter_by(attempt_id=attempt.id)
        .order_by(CodingAttemptQuestion.assigned_order)
        .all()
    )
    if existing:
        return existing

    chosen = []
    for topic, count in section_plan:
        pool = session.query(CodingQuestion).filter_by(topic=topic).all()
        if len(pool) < count:
            raise SystemExit(
                f"Only {len(pool)} coding question(s) available for topic '{topic}'; requested {count}."
            )
        chosen.extend(random.sample(pool, count))

    return _assign(session, attempt, chosen)
