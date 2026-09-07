"""Maps a provider's free-text "area" name to one of our ``Continent``
values. This is geographic reference data (which continent a country is
on), not a list of competitions or teams — the set of competitions itself
always comes from the provider via ``CompetitionDiscoveryService``, never
from a static list here.

Unrecognized areas fall back to ``INTERNATIONAL`` rather than raising, so
discovery never breaks on a country we forgot to list.
"""
from __future__ import annotations

from ..models.enums import Continent

# Area names football-data.org (and similar providers) use for continent-level
# competitions (e.g. CAF Champions League is filed directly under "Africa").
_CONTINENT_LEVEL_AREAS: dict[str, Continent] = {
    "africa": Continent.AFRICA,
    "europe": Continent.EUROPE,
    "south america": Continent.SOUTH_AMERICA,
    "north america": Continent.NORTH_AMERICA,
    "north & central america": Continent.NORTH_AMERICA,
    "asia": Continent.ASIA,
    "oceania": Continent.OCEANIA,
    "world": Continent.INTERNATIONAL,
    "international": Continent.INTERNATIONAL,
}

_COUNTRY_TO_CONTINENT: dict[str, Continent] = {
    # Africa
    "senegal": Continent.AFRICA, "morocco": Continent.AFRICA, "algeria": Continent.AFRICA,
    "tunisia": Continent.AFRICA, "egypt": Continent.AFRICA, "south africa": Continent.AFRICA,
    "ivory coast": Continent.AFRICA, "cote d'ivoire": Continent.AFRICA, "mali": Continent.AFRICA,
    "ghana": Continent.AFRICA, "nigeria": Continent.AFRICA, "cameroon": Continent.AFRICA,
    "dr congo": Continent.AFRICA, "congo dr": Continent.AFRICA, "congo": Continent.AFRICA,
    "tanzania": Continent.AFRICA, "kenya": Continent.AFRICA, "angola": Continent.AFRICA,
    "zambia": Continent.AFRICA, "zimbabwe": Continent.AFRICA, "uganda": Continent.AFRICA,
    "ethiopia": Continent.AFRICA, "libya": Continent.AFRICA, "sudan": Continent.AFRICA,
    "guinea": Continent.AFRICA, "benin": Continent.AFRICA, "togo": Continent.AFRICA,
    "burkina faso": Continent.AFRICA, "gabon": Continent.AFRICA, "mozambique": Continent.AFRICA,
    "namibia": Continent.AFRICA, "botswana": Continent.AFRICA, "rwanda": Continent.AFRICA,
    "mauritania": Continent.AFRICA, "niger": Continent.AFRICA, "chad": Continent.AFRICA,
    "madagascar": Continent.AFRICA, "gambia": Continent.AFRICA, "sierra leone": Continent.AFRICA,
    "liberia": Continent.AFRICA, "eswatini": Continent.AFRICA, "lesotho": Continent.AFRICA,
    "burundi": Continent.AFRICA, "comoros": Continent.AFRICA, "djibouti": Continent.AFRICA,
    "eritrea": Continent.AFRICA, "somalia": Continent.AFRICA, "cape verde": Continent.AFRICA,
    "equatorial guinea": Continent.AFRICA, "central african republic": Continent.AFRICA,
    "guinea-bissau": Continent.AFRICA, "malawi": Continent.AFRICA,

    # Europe
    "england": Continent.EUROPE, "france": Continent.EUROPE, "spain": Continent.EUROPE,
    "germany": Continent.EUROPE, "italy": Continent.EUROPE, "portugal": Continent.EUROPE,
    "netherlands": Continent.EUROPE, "belgium": Continent.EUROPE, "turkey": Continent.EUROPE,
    "scotland": Continent.EUROPE, "switzerland": Continent.EUROPE, "austria": Continent.EUROPE,
    "greece": Continent.EUROPE, "denmark": Continent.EUROPE, "sweden": Continent.EUROPE,
    "norway": Continent.EUROPE, "finland": Continent.EUROPE, "poland": Continent.EUROPE,
    "czech republic": Continent.EUROPE, "croatia": Continent.EUROPE, "serbia": Continent.EUROPE,
    "romania": Continent.EUROPE, "ukraine": Continent.EUROPE, "russia": Continent.EUROPE,
    "wales": Continent.EUROPE, "northern ireland": Continent.EUROPE,
    "republic of ireland": Continent.EUROPE, "ireland": Continent.EUROPE,
    "hungary": Continent.EUROPE, "bulgaria": Continent.EUROPE, "slovenia": Continent.EUROPE,
    "slovakia": Continent.EUROPE, "iceland": Continent.EUROPE, "bosnia and herzegovina": Continent.EUROPE,
    "north macedonia": Continent.EUROPE, "albania": Continent.EUROPE, "montenegro": Continent.EUROPE,
    "estonia": Continent.EUROPE, "latvia": Continent.EUROPE, "lithuania": Continent.EUROPE,
    "malta": Continent.EUROPE, "cyprus": Continent.EUROPE, "luxembourg": Continent.EUROPE,
    "kosovo": Continent.EUROPE, "moldova": Continent.EUROPE, "belarus": Continent.EUROPE,
    "georgia": Continent.EUROPE, "armenia": Continent.EUROPE, "azerbaijan": Continent.EUROPE,
    "andorra": Continent.EUROPE, "san marino": Continent.EUROPE, "gibraltar": Continent.EUROPE,
    "faroe islands": Continent.EUROPE, "liechtenstein": Continent.EUROPE, "monaco": Continent.EUROPE,

    # South America
    "brazil": Continent.SOUTH_AMERICA, "argentina": Continent.SOUTH_AMERICA,
    "colombia": Continent.SOUTH_AMERICA, "chile": Continent.SOUTH_AMERICA,
    "uruguay": Continent.SOUTH_AMERICA, "paraguay": Continent.SOUTH_AMERICA,
    "peru": Continent.SOUTH_AMERICA, "ecuador": Continent.SOUTH_AMERICA,
    "bolivia": Continent.SOUTH_AMERICA, "venezuela": Continent.SOUTH_AMERICA,

    # North & Central America
    "united states": Continent.NORTH_AMERICA, "usa": Continent.NORTH_AMERICA,
    "canada": Continent.NORTH_AMERICA, "mexico": Continent.NORTH_AMERICA,
    "costa rica": Continent.NORTH_AMERICA, "honduras": Continent.NORTH_AMERICA,
    "panama": Continent.NORTH_AMERICA, "jamaica": Continent.NORTH_AMERICA,
    "guatemala": Continent.NORTH_AMERICA, "el salvador": Continent.NORTH_AMERICA,

    # Asia
    "saudi arabia": Continent.ASIA, "japan": Continent.ASIA, "south korea": Continent.ASIA,
    "korea republic": Continent.ASIA, "china": Continent.ASIA, "china pr": Continent.ASIA,
    "qatar": Continent.ASIA, "united arab emirates": Continent.ASIA, "uae": Continent.ASIA,
    "india": Continent.ASIA, "thailand": Continent.ASIA, "indonesia": Continent.ASIA,
    "vietnam": Continent.ASIA, "iran": Continent.ASIA, "iraq": Continent.ASIA,
    "israel": Continent.ASIA, "jordan": Continent.ASIA, "uzbekistan": Continent.ASIA,
    "malaysia": Continent.ASIA, "singapore": Continent.ASIA, "philippines": Continent.ASIA,
    "kuwait": Continent.ASIA, "bahrain": Continent.ASIA, "oman": Continent.ASIA,

    # Oceania
    "australia": Continent.OCEANIA, "new zealand": Continent.OCEANIA,
    "fiji": Continent.OCEANIA, "papua new guinea": Continent.OCEANIA,
}


def continent_for_area(area_name: str) -> Continent:
    key = area_name.strip().lower()
    if key in _CONTINENT_LEVEL_AREAS:
        return _CONTINENT_LEVEL_AREAS[key]
    if key in _COUNTRY_TO_CONTINENT:
        return _COUNTRY_TO_CONTINENT[key]
    return Continent.INTERNATIONAL
