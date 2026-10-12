import pytest

from src.storage.analytics import TopSalary, rank_top_salaries
from src.storage.embed import to_vector_text


# Serializer output format only — the psycopg round-trip is already proven by
# the 1,660 live vectors. Scientific notation is the case DECISIONS: storage
# calls out as verified-against-Python's-str-repr.
@pytest.mark.parametrize(
    ("vec", "expected"),
    [
        ([1.0, 2.5, 3.14], "[1.0,2.5,3.14]"),
        ([1e-05], "[1e-05]"),
        ([-1.5, 0.0], "[-1.5,0.0]"),
    ],
)
def test_to_vector_text(vec: list[float], expected: str) -> None:
    assert to_vector_text(vec) == expected


def _top(raw_posting_id: int, salary_min: int | None, salary_max: int | None) -> TopSalary:
    return TopSalary(raw_posting_id, 0, None, None, None, "unknown", salary_min, salary_max, "RUB")


# Row values are the real snapshot rows behind the salary-ranking bug: 13489
# ("Экосистема тенниса", min-only 500k) ties with 13682 (BASIS, max-only 500k);
# 13611 ("Рекрутер", min-only 410k) must outrank 13857 (Advers, 350-400k).
@pytest.mark.parametrize(
    ("rows", "limit", "expected_ids"),
    [
        # NULL-max rows rank at their stated floor, not dropped or last.
        ([_top(13857, 350000, 400000), _top(13611, 410000, None)], 10, [13611, 13857]),
        # Tie at 500k (one NULL max, one NULL min): stable key breaks it.
        ([_top(13682, None, 500000), _top(13489, 500000, None)], 10, [13489, 13682]),
        # The full snapshot podium, shuffled: tie first, then the 490k ceilings.
        (
            [
                _top(13630, 300000, 490000),
                _top(13611, 410000, None),
                _top(13682, None, 500000),
                _top(13489, 500000, None),
                _top(13590, 300000, 490000),
            ],
            10,
            [13489, 13682, 13590, 13630, 13611],
        ),
        # Limit applies after ranking, not before.
        ([_top(13611, 410000, None), _top(13489, 500000, None)], 1, [13489]),
    ],
)
def test_rank_top_salaries(rows: list[TopSalary], limit: int, expected_ids: list[int]) -> None:
    ranked = rank_top_salaries(rows, limit)
    assert [r.raw_posting_id for r in ranked] == expected_ids
