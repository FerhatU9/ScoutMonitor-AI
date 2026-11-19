
def review_report(
    connection,
    report_id,
    decision,
    reviewer_name,
    review_notes=None,
):
    # 1. Check the reviewer's decision
    if not isinstance(decision, str):
        raise ValueError("Invalid review decision.")

    decision = decision.strip().upper()

    if decision not in ("APPROVED", "REJECTED"):
        raise ValueError(
            "Decision must be APPROVED or REJECTED."
        )

    # 2. Check who is reviewing
    if not isinstance(reviewer_name, str):
        raise ValueError("Reviewer name is required.")

    reviewer_name = reviewer_name.strip()

    if not reviewer_name:
        raise ValueError("Reviewer name is required.")

    # 3. Require a reason for rejection
    if decision == "REJECTED":
        if not review_notes or not review_notes.strip():
            raise ValueError(
                "A rejection reason is required."
            )

    # 4. Update the report only if review is allowed
    sql = """
        UPDATE ai_reports
        SET
            review_status = %s,
            reviewer_name = %s,
            review_notes = %s,
            reviewed_at = CURRENT_TIMESTAMP
        WHERE report_id = %s
          AND review_status = 'PENDING'
          AND (
              %s = 'REJECTED'
              OR validation_status = 'PASS'
          )
        RETURNING
            report_id,
            review_status,
            reviewer_name;
    """

    with connection.cursor() as cursor:
        cursor.execute(
            sql,
            (
                decision,
                reviewer_name,
                review_notes,
                report_id,
                decision,
            ),
        )

        result = cursor.fetchone()

    if result is None:
        raise ValueError(
            "Review not allowed. Report may be missing, "
            "already reviewed, or not validated."
        )

    # The calling program controls commit or rollback
    return {
        "report_id": result[0],
        "review_status": result[1],
        "reviewer_name": result[2],
    }
