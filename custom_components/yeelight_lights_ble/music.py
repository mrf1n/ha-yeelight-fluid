"""Music mode (device microphone): rhythm effects and colour schemes.

Values match the official app. Each scheme is five ARGB colours; the device
gets them spread over a 16-colour palette (see protocol.music_palette).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

# Rhythm effect -> firmware effect id
RHYTHM_EFFECTS: Final = {
    "breath": 84,
    "shine": 85,
    "spectrum": 86,
    "converge": 83,
}
DEFAULT_RHYTHM_EFFECT: Final = "breath"

# effect ids the device can report while music mode runs (incl. styles of other products)
MUSIC_EFFECT_IDS: Final = frozenset({44, 83, 84, 85, 86, 87, 88})

MUSIC_CATEGORIES: Final = ("mood", "landscape", "music", "holiday")
CUSTOM_SCHEME: Final = "custom"
MAX_CUSTOM_COLORS: Final = 16


@dataclass(frozen=True)
class MusicScheme:
    """Predefined colour scheme."""

    key: str
    category: str
    colors: tuple[int, ...]


MUSIC_SCHEMES: Final[tuple[MusicScheme, ...]] = (
    MusicScheme("happy", "mood", (0xFFEA047E, 0xFFFF8861, 0xFFFFE75F, 0xFF8DD852, 0xFF00F5FF)),
    MusicScheme("surprised", "mood", (0xFF19467A, 0xFF2C7FA6, 0xFFB1FDF9, 0xFF77FFA5, 0xFF06965E)),
    MusicScheme("excited", "mood", (0xFFEAE2B7, 0xFFFCBF49, 0xFFF77F00, 0xFFD62828, 0xFF003B59)),
    MusicScheme("romantic", "mood", (0xFFFFBE7C, 0xFFFFF4CB, 0xFFE8B8FF, 0xFFFF8FB1, 0xFFE45887)),
    MusicScheme("relaxed", "mood", (0xFFF79256, 0xFFFBD1A2, 0xFF7DCFB6, 0xFF00B2CA, 0xFF1D4E89)),
    MusicScheme("joyful", "mood", (0xFFFFEB3B, 0xFF00C853, 0xFF009688, 0xFF3F51B5, 0xFFF44336)),
    MusicScheme("warm", "mood", (0xFFFF577F, 0xFFFFCDD2, 0xFFFFD180, 0xFFFF884B, 0xFFF44336)),
    MusicScheme("calm", "mood", (0xFFB5FFFF, 0xFF40DFFF, 0xFF00BBFF, 0xFF0088CC, 0xFF0055AA)),
    MusicScheme("tranquil", "mood", (0xFF1B7A69, 0xFF66AF56, 0xFF6FB18D, 0xFFFFECCF, 0xFF424242)),
    MusicScheme(
        "tropical_island", "landscape", (0xFF00FFFF, 0xFFF9EF1A, 0xFFFF8C38, 0xFF8BC83D, 0xFF338650)
    ),
    MusicScheme(
        "purple_jungle", "landscape", (0xFF730073, 0xFFD125A1, 0xFFFFC0E6, 0xFFD125A1, 0xFF730073)
    ),
    MusicScheme(
        "sunset_desert", "landscape", (0xFFACF5FF, 0xFFFFF1C6, 0xFFFFB51C, 0xFFDD7B43, 0xFFB7391E)
    ),
    MusicScheme(
        "tropical_rainforest",
        "landscape",
        (0xFFFF1493, 0xFFFFD700, 0xFF32CD32, 0xFF1AA774, 0xFF007D76),
    ),
    MusicScheme(
        "heart_of_ocean", "landscape", (0xFF1E90FF, 0xFF00BFFF, 0xFF87CEFA, 0xFFFFCFCF, 0xFFFF6868)
    ),
    MusicScheme(
        "violet_seas", "landscape", (0xFFFF47BF, 0xFFFF77D0, 0xFFFFA7E4, 0xFFBE7DFF, 0xFFA449FF)
    ),
    MusicScheme(
        "blue_glacier", "landscape", (0xFF8180D1, 0xFFE6CCF8, 0xFFA5DCFF, 0xFF02A8DC, 0xFF0059C1)
    ),
    MusicScheme(
        "sunrise_sea", "landscape", (0xFFFFD700, 0xFFFF893E, 0xFFFB5C46, 0xFF5D3486, 0xFF282D97)
    ),
    MusicScheme(
        "green_meadow", "landscape", (0xFF00A3E9, 0xFFB5E1F4, 0xFFE7EA4C, 0xFF83AA1A, 0xFF2C7908)
    ),
    MusicScheme(
        "golden_forest", "landscape", (0xFFFFFF00, 0xFFFFD700, 0xFFFFA500, 0xFFF38600, 0xFFFF4500)
    ),
    MusicScheme(
        "blue_mountains", "landscape", (0xFF06FFFF, 0xFFB4DEFF, 0xFF3F92FF, 0xFF0046AF, 0xFFEDAC49)
    ),
    MusicScheme(
        "pink_garden", "landscape", (0xFF00FFFF, 0xFFC0FFFF, 0xFFFFC0CB, 0xFFFF69B4, 0xFFFF1493)
    ),
    MusicScheme(
        "volcano_cave", "landscape", (0xFF8F0045, 0xFFEB1120, 0xFFFF833E, 0xFFEB1120, 0xFF8F0045)
    ),
    MusicScheme(
        "golden_leaves", "landscape", (0xFFFFD700, 0xFFFF8C00, 0xFFFF4500, 0xFFB47130, 0xFF498A15)
    ),
    MusicScheme(
        "sunset_lake", "landscape", (0xFFFF6E40, 0xFFEB6C7B, 0xFFFC9BCF, 0xFF9A51E3, 0xFF524FEB)
    ),
    MusicScheme("classical", "music", (0xFF264653, 0xFF2A9D8F, 0xFFE9C46A, 0xFFF4A261, 0xFFE76F51)),
    MusicScheme("pop", "music", (0xFFFFBE0B, 0xFFFB5607, 0xFFFF006E, 0xFF8338EC, 0xFF3A86FF)),
    MusicScheme("rock", "music", (0xFF444444, 0xFFDADADA, 0xFFE31A1A, 0xFFF8D500, 0xFFA5A5A5)),
    MusicScheme(
        "electronic", "music", (0xFF1BE7FF, 0xFF6EEB83, 0xFFFFF61A, 0xFFDE14FF, 0xFF7B14FF)
    ),
    MusicScheme("antique", "music", (0xFFC5B56C, 0xFF98623C, 0xFFDBD6B3, 0xFFF1F0EA, 0xFFB9A882)),
    MusicScheme("rap", "music", (0xFF120CCA, 0xFFC801D0, 0xFFF63C31, 0xFFC801D0, 0xFF120CCA)),
    MusicScheme("jazz", "music", (0xFFFFCC00, 0xFFFFDE5C, 0xFFFFEB99, 0xFFA486D5, 0xFF54318C)),
    MusicScheme("country", "music", (0xFFEE6055, 0xFFFF9B85, 0xFFFFD97D, 0xFFAAF683, 0xFF60D394)),
    MusicScheme("metal", "music", (0xFF558A78, 0xFF853512, 0xFFEEAA23, 0xFF614433, 0xFF4A834C)),
    MusicScheme(
        "alternative", "music", (0xFFCC2936, 0xFFFFE000, 0xFF50C7C7, 0xFFE5E5E5, 0xFFF9A71F)
    ),
    MusicScheme(
        "new_year", "holiday", (0xFF2A745A, 0xFF9A1616, 0xFFCC433A, 0xFFED7744, 0xFFFFBF7B)
    ),
    MusicScheme(
        "valentine", "holiday", (0xFFFFE5ED, 0xFFFFBAD8, 0xFFFF71A3, 0xFFFF3369, 0xFFFF103B)
    ),
    MusicScheme(
        "carnival", "holiday", (0xFF973EFF, 0xFFFF479A, 0xFFFFE651, 0xFF08DABB, 0xFF4D69FF)
    ),
    MusicScheme(
        "april_fool", "holiday", (0xFF055FBE, 0xFFFFCA0D, 0xFFFF4040, 0xFFFFCA0D, 0xFF055FBE)
    ),
    MusicScheme("mother", "holiday", (0xFF390E80, 0xFFB3005E, 0xFFE90064, 0xFFFF5F9E, 0xFFFFACAC)),
    MusicScheme("father", "holiday", (0xFF0584DB, 0xFF77DFFF, 0xFFFFE7A8, 0xFF9BD95C, 0xFF00997C)),
    MusicScheme(
        "children", "holiday", (0xFFB2A4FF, 0xFFFF8DAF, 0xFFFFD095, 0xFFA8E7FF, 0xFF9EFFB4)
    ),
    MusicScheme(
        "halloween", "holiday", (0xFF530095, 0xFFCD113B, 0xFFFF7600, 0xFFFFA900, 0xFFFFF966)
    ),
    MusicScheme(
        "world_cup", "holiday", (0xFFFFF966, 0xFFDDF7E3, 0xFF81BC87, 0xFF196616, 0xFF0052A8)
    ),
    MusicScheme(
        "thanksgiving", "holiday", (0xFFFFD199, 0xFFFFDC83, 0xFFFF9A61, 0xFFFF6636, 0xFFF7373F)
    ),
    MusicScheme(
        "christmas", "holiday", (0xFFF8D500, 0xFFFD5E53, 0xFFF9FCFB, 0xFFB0EACD, 0xFF21BF73)
    ),
)
SCHEMES_BY_KEY: Final = {s.key: s for s in MUSIC_SCHEMES}
DEFAULT_MUSIC_SCHEME: Final = "happy"
