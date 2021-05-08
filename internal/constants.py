TYPES_OF_MAP = [
    "SINGLE",
    "MULTILEVEL",
    "PIONEER",
    "TIME-ATTACK",
    "MEGAMAP",
    "MULTIMAP",
    "TUTORIAL",
    "HARDCORE",
    "MILDCORE",
    "OUT-OF-MAP",
    "ABLOCK",
    "NOSTALGIA",
    "FRAMEWORK",
]

# The amount of servers required for a bot to be eligible for verification.
VERIFICATION_GUILD_COUNT_TRESHOLD = 75

# The % of bot accounts in a server in order for the server to be considered low quality
BAD_BOT_PERCENTAGE_TRESHOLD = 35

CONFIRM_REACTION_EMOJI = "🟢"  # Reaction emoji used to confirm actions
CANCEL_REACTION_EMOJI = "🟥"  # Reaction emoji used to cancel actions

# Message sent at the bottom of every reaction confirmaation
CONFIRMATION_TEXT = f"*Please react to this message with {CONFIRM_REACTION_EMOJI} to continue, or react with {CANCEL_REACTION_EMOJI} to cancel. Waiting for two minutes will cancel the process automatically.*"

LEFT_REACTION_EMOJI = "◀"  # Reaction emoji used to turn page left
RIGHT_REACTION_EMOJI = "▶"  # Reaction emoji used to turn page left

NEW_LINE = "\n"

# Verification
VERIFIED_EMOJI = "✅"
NOT_VERIFIED_EMOJI = "❌"

# Prettytable page size
PT_PAGE_SIZE = 10

# creator / desc max_lengths
CREATOR_MAX_LENGTH = 35
DESC_MAX_LENGTH = 35
TYPE_MAX_LENGTH = 20

# limit for latest maps command
NEWEST_MAPS_LIMIT = 10

# Map names | CUSTOMIZE ACCEPTABLE NAMES
AYUTTHAYA = ["ayutthaya", "ayutt"]
BLACKFOREST = ["blackforest", "bf"]
BLIZZARDWORLD = ["blizzardworld", "bw", "blizz", "blizzworld", "blizzard"]
BUSAN = ["busan"]
CASTILLO = ["castillo"]
CHATEAUGUILLARD = ["chateauguillard", "chateau", "guillard"]
DORADO = ["dorado"]
EICHENWALDE = ["eichenwalde", "eich", "eichen", "eichenwald"]
HANAMURA = ["hanamura", "hana"]
HAVANA = ["havana"]
HOLLYWOOD = ["hollywood", "holly"]
HORIZONLUNARCOLONY = ["horizonlunarcolony", "hlc", "horizon"]
ILIOS = ["ilios"]
JUNKERTOWN = ["junkertown"]
LIJIANGTOWER = ["lijiangtower", "lijiang"]
NECROPOLIS = ["necropolis"]
NEPAL = ["nepal"]
NUMBANI = ["numbani"]
OASIS = ["oasis"]
PARIS = ["paris"]
RIALTO = ["rialto"]
ROUTE66 = ["route66", "r66"]
TEMPLEOFANUBIS = ["templeofanubis", "anubis"]
VOLSKAYAINDUSTRIES = ["volskayaindustries", "volskaya"]
WATCHPOINTGIBRALTAR = ["watchpointgibraltar", "gibraltar", "wpg"]
KINGSROW = ["kingsrow", "kr"]
PETRA = ["petra"]
ECOPOINTANTARCTICA = ["ecopointantarctica", "ecopoint", "antarctica"]
KANEZAKA = ["kanezaka", "kz", "kane", "zaka"]
WORKSHOPCHAMBER = ["workshopchamber", "chamber"]
WORKSHOPEXPANSE = ["workshopexpanse", "expanse"]
WORKSHOPGREENSCREEN = ["workshopgreenscreen", "green", "greenscreen"]
WORKSHOPISLAND = ["workshopisland", "island"]
PRACTICERANGE = ["practicerange", "practice", "pr"]
FRAMEWORK = ["framework", "fw"]

# combined map names
ALL_MAP_NAMES = [
    AYUTTHAYA,
    BLACKFOREST,
    BLIZZARDWORLD,
    BUSAN,
    CASTILLO,
    CHATEAUGUILLARD,
    DORADO,
    ECOPOINTANTARCTICA,
    EICHENWALDE,
    HANAMURA,
    HAVANA,
    HOLLYWOOD,
    HORIZONLUNARCOLONY,
    ILIOS,
    JUNKERTOWN,
    KANEZAKA,
    KINGSROW,
    LIJIANGTOWER,
    NECROPOLIS,
    NEPAL,
    NUMBANI,
    OASIS,
    PARIS,
    PETRA,
    PRACTICERANGE,
    RIALTO,
    ROUTE66,
    TEMPLEOFANUBIS,
    VOLSKAYAINDUSTRIES,
    WATCHPOINTGIBRALTAR,
    WORKSHOPCHAMBER,
    WORKSHOPEXPANSE,
    WORKSHOPGREENSCREEN,
    WORKSHOPISLAND,
    FRAMEWORK,
]

PRETTY_NAMES = {
    "ayutthaya": "Ayutthaya",
    "blackforest": "Black Forest",
    "blizzardworld": "Blizzard World",
    "busan": "Busan",
    "castillo": "Castillo",
    "chateauguillard": "Chateau Guillard",
    "dorado": "Dorado",
    "eichenwalde": "Eichenwalde",
    "hanamura": "Hanamura",
    "havana": "Havana",
    "hollywood": "Hollywood",
    "horizonlunarcolony": "Horizon Lunar Colony",
    "ilios": "Ilios",
    "junkertown": "Junkertown",
    "lijiangtower": "Lijiang Tower",
    "necropolis": "Necropolis",
    "nepal": "Nepal",
    "numbani": "Numbani",
    "oasis": "Oasis",
    "paris": "Paris",
    "rialto": "Rialto",
    "route66": "Route 66",
    "templeofanubis": "Temple of Anubis",
    "volskayaindustries": "Volskaya Industries",
    "watchpointgibraltar": "Watchpoint Gibraltar",
    "kingsrow": "King's Row",
    "petra": "Petra",
    "ecopointantarctica": "Ecopoint Antarctica",
    "kanezaka": "Kanezaka",
    "workshopchamber": "Workshop Chamber",
    "workshopexpanse": "Workshop Expanse",
    "workshopgreenscreen": "Workshop Greenscreen",
    "workshopisland": "Workshop Island",
    "practicerange": "Practice Range",
    "framework": "Framework",
}
