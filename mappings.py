STAT_MAPPING: dict[str, list[str]] = {
    # Attribute-ish
    "AGILITY_BOOST": ["Agility Boost"],
    "STRENGTH_BOOST": ["Strength Boost"],
    "WILL_BOOST": ["Will Boost"],
    "INTELLECT_BOOST": ["Intellect Boost"],
    "MAIN_ATTRIBUTE_BOOST": ["Main Attribute Boost"],

    # Numeric / damage
    "ATTACK_BOOST": ["ATK Boost", "Attack Boost"],
    "HP_BOOST": ["HP Boost"],
    "PHYSICAL_DMG_BOOST": ["Physical DMG Boost"],
    "HEAT_DMG_BOOST": ["Heat DMG Boost"],
    "ELECTRIC_DMG_BOOST": ["Electric DMG Boost", "Electric DMG"],
    "CRYO_DMG_BOOST": ["Cryo DMG Boost"],
    "NATURE_DMG_BOOST": ["Nature DMG Boost"],
    "CRITICAL_RATE_BOOST": ["Critical Rate Boost"],
    "ORIGINIUM_ARTS_BOOST": ["Originium Arts Boost"],
    "ULTIMATE_GAIN_BOOST": ["Ultimate Gain Boost"],
    "ARTS_DMG_BOOST": ["Arts DMG Boost", "Arts Intensity Boost"],
    "TREATMENT_EFFICIENCY_BOOST": ["Treatment Efficiency Boost"],

    # Passive / keyword
    "ASSAULT": ["Assault"],
    "SUPPRESSION": ["Suppression"],
    "PURSUIT": ["Pursuit"],
    "CRUSHER": ["Crusher"],
    "INSPIRING": ["Inspiring"],
    "COMBATIVE": ["Combative"],
    "BRUTALITY": ["Brutality"],
    "INFLICTION": ["Infliction"],
    "MEDICANT": ["Medicant"],
    "FRACTURE": ["Fracture"],
    "DETONATE": ["Detonate"],
    "TWILIGHT": ["Twilight"],
    "FLOW": ["Flow"],
    "EFFICACY": ["Efficacy"],
}

# All stat slots now share the same mapping
STAT1_MAPPING = STAT_MAPPING
STAT2_MAPPING = STAT_MAPPING
STAT3_MAPPING = STAT_MAPPING
