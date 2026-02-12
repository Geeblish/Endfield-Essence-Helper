# essence_helper.py
from enum import Enum, auto
from typing import Dict, Set, List, overload


# ----------------------
# Unified Stat Enum
# ----------------------
class Stat(Enum):
    # Attribute-ish
    AGILITY_BOOST = auto()
    STRENGTH_BOOST = auto()
    WILL_BOOST = auto()
    INTELLECT_BOOST = auto()
    MAIN_ATTRIBUTE_BOOST = auto()

    # Numeric / damage
    ATTACK_BOOST = auto()
    HP_BOOST = auto()
    PHYSICAL_DMG_BOOST = auto()
    HEAT_DMG_BOOST = auto()
    ELECTRIC_DMG_BOOST = auto()
    CRYO_DMG_BOOST = auto()
    NATURE_DMG_BOOST = auto()
    CRITICAL_RATE_BOOST = auto()
    ORIGINIUM_ARTS_BOOST = auto()
    ULTIMATE_GAIN_BOOST = auto()
    ARTS_DMG_BOOST = auto()
    TREATMENT_EFFICIENCY_BOOST = auto()

    # Passive / keyword
    ASSAULT = auto()
    SUPPRESSION = auto()
    PURSUIT = auto()
    CRUSHER = auto()
    INSPIRING = auto()
    COMBATIVE = auto()
    BRUTALITY = auto()
    INFLICTION = auto()
    MEDICANT = auto()
    FRACTURE = auto()
    DETONATE = auto()
    TWILIGHT = auto()
    FLOW = auto()
    EFFICACY = auto()


# ----------------------
# Weapon Index
# ----------------------
class WeaponIndex:
    def __init__(self):
        # weapon name -> frozenset of required stats
        self.weapons: Dict[str, frozenset[Stat]] = {}

        # stat -> set of weapon names that require it
        self.index_stat: Dict[Stat, Set[str]] = {}

    # ----------------------
    # Add weapon
    # ----------------------
    def add_weapon(self, name: str, *stats: Stat):
        stat_set = frozenset(stats)
        
        if len(stat_set) not in (2, 3):
            raise ValueError("Weapon must have either 2 or 3 unique stats")

        self.weapons[name] = stat_set

        for s in stat_set:
            self.index_stat.setdefault(s, set()).add(name)

    # ----------------------
    # Lookup essence
    # ----------------------
    # def lookup(self, s1: Stat, s2: Stat, s3: Stat) -> List[str]:
    #     # progressive intersection with early exit
    #     result = self.index_stat.get(s1, set()).copy()
    #     if not result:
    #         return []

    #     result &= self.index_stat.get(s2, set())
    #     if not result:
    #         return []

    #     result &= self.index_stat.get(s3, set())
    #     return list(result)

    # # ----------------------
    # # Partial / debug lookup -> Now overloaded
    # # ----------------------
    # def lookup_partial(self, *stats: Stat) -> List[str]:
    #     if not stats:
    #         return list(self.weapons.keys())

    #     result = None
    #     for s in stats:
    #         s_set = self.index_stat.get(s, set())
    #         result = s_set if result is None else result & s_set
    #         if not result:
    #             return []

    #     return list(result) if result is not None else []

    @overload
    def lookup(self, s1: Stat, s2: Stat) -> List[str]: ...
    @overload
    def lookup(self, s1: Stat, s2: Stat, s3: Stat) -> List[str]: ...

    def lookup(
        self,
        s1: Stat,
        s2: Stat,
        s3: Stat | None = None,
    ) -> List[str]:
        result = self.index_stat.get(s1, set()).copy()
        if not result:
            return []

        result &= self.index_stat.get(s2, set())
        if not result:
            return []

        if s3 is not None:
            result &= self.index_stat.get(s3, set())
            if not result:
                return []

        return list(result)
