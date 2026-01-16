import re

from app.infrastructure.db.models import Category
from app.infrastructure.repositories.categories import CategoriesRepo
from app.domain.enums import CategoryKind


_slug_re = re.compile(r"[^a-z0-9]+")

_ru_map = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
    "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "h", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sch",
    "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
}


def _translit_ru(s: str) -> str:
    out = []
    for ch in s:
        low = ch.lower()
        if low in _ru_map:
            out.append(_ru_map[low])
        else:
            out.append(low)
    return "".join(out)


def make_slug(name: str) -> str:
    s = name.strip().lower()
    s = _translit_ru(s)
    s = _slug_re.sub("-", s).strip("-")
    return s or "category"


def create_category(repo: CategoriesRepo, kind: str, name: str, slug: str | None = None) -> Category:
    kind = kind or CategoryKind.EXPENSE.value
    base_slug = slug or make_slug(name)

    # делаем slug уникальным (если такой уже есть — добавим -2, -3, ...)
    candidate = base_slug
    i = 2
    while repo.get_by_slug(candidate) is not None:
        candidate = f"{base_slug}-{i}"
        i += 1

    cat = Category(kind=kind, name=name, slug=candidate)
    repo.add(cat)
    repo.session.commit()
    return cat
