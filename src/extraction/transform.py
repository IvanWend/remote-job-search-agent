from typing import Any

from src.extraction.normalize import (
    currency_enum,
    employment_enum,
    normalize_stack,
    remote_policy_enum,
    seniority_enum,
    to_monthly,
)
from src.extraction.schema import (
    NormalizedPosting,
    NormalizedRole,
    PostingExtraction,
    RoleExtraction,
)


def _inherit(role: RoleExtraction, posting: PostingExtraction, name: str) -> Any:
    # None at role level means inherit, not absent — the whole point of the
    # verbatim layer keeping these Optional.
    value = getattr(role, name)
    return getattr(posting, name) if value is None else value


def _stack(role: RoleExtraction, posting: PostingExtraction) -> list[str]:
    # Union, not replace: a posting states the shared stack once and a role adds
    # its own. Replacing would drop the shared half for exactly the roles that
    # bothered to be specific. This is the one inheritable field that does not
    # behave like the other seven.
    return normalize_stack([*(posting.stack or []), *(role.stack or [])])


_Salary = tuple[int | None, int | None, str | None]


def _salary(role: RoleExtraction, posting: PostingExtraction) -> _Salary:
    low = _inherit(role, posting, "salary_min")
    high = _inherit(role, posting, "salary_max")
    period = _inherit(role, posting, "salary_period")
    if (low is None and high is None) or period is None:
        return None, None, None

    try:
        monthly_low = to_monthly(low, period) if low is not None else None
        monthly_high = to_monthly(high, period) if high is not None else None
    except ValueError:
        # Unparseable amount or unknown period. The verbatim survives in
        # source_quotes["salary"]; a guessed monthly figure would corrupt every
        # downstream aggregate and nothing could catch it.
        return None, None, None

    return monthly_low, monthly_high, currency_enum(_inherit(role, posting, "salary_currency"))


def _quotes(role: RoleExtraction, posting: PostingExtraction) -> dict[str, str]:
    # Same fill-down as the values: a role inheriting remote_policy inherits the
    # quote that grounds it, so the stored row stands on its own.
    return {**posting.source_quotes, **role.source_quotes}


def _role(role: RoleExtraction, posting: PostingExtraction, index: int) -> NormalizedRole:
    salary_min, salary_max, currency = _salary(role, posting)
    return NormalizedRole(
        role_index=index,
        title=role.title,
        seniority=seniority_enum(role.seniority),
        stack=_stack(role, posting),
        location=_inherit(role, posting, "location"),
        remote_policy=remote_policy_enum(_inherit(role, posting, "remote_policy")),
        employment_type=employment_enum(_inherit(role, posting, "employment_type")),
        salary_min=salary_min,
        salary_max=salary_max,
        salary_currency=currency,
        description=_inherit(role, posting, "description"),
        source_quotes=_quotes(role, posting),
    )


def transform(posting: PostingExtraction) -> NormalizedPosting:
    if posting.doc_type != "posting":
        return NormalizedPosting(doc_type=posting.doc_type)

    # A single-role posting often comes back with everything at posting level and
    # roles empty. Without this the row normalizes to nothing at all, and
    # structured_postings is keyed on the role.
    roles = posting.roles or [RoleExtraction()]
    return NormalizedPosting(
        doc_type=posting.doc_type,
        company=posting.company,
        roles=[_role(role, posting, index) for index, role in enumerate(roles)],
    )
