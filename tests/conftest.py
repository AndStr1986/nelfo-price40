from typing import cast


def cast_and_split(sample: str) -> list[str]:
    """Split a sample line into fields for from_line().

    sample.split(";") alone is inferred by the type checker as
    list[LiteralString] when sample is a string literal constant - and
    list[LiteralString] isn't assignable to a list[str] parameter (lists
    are invariant), even though every LiteralString is a str. cast()
    sidesteps that without changing anything at runtime.
    """
    return cast(list[str], sample.split(";"))
