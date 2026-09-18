from typing import Iterable, Optional, Tuple

def lz77_decode(tokens: Iterable[Tuple[int, int, Optional[int]]]) -> bytes:
    out = bytearray()

    for offset, length, next_char in tokens:
        if length > 0:
            if offset <= 0 or offset > len(out):
                raise ValueError(f"Некорректный offset={offset} при длине вывода {len(out)}")

            for _ in range(length):
                out.append(out[-offset])

        if next_char is not None:
            out.append(next_char)

    return bytes(out)