import pytest

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
