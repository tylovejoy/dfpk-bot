"""
This file contains constants that the bot works with.
If you wish to add or edit a constant, please make sure to comment the meaning of the constant and the reason for the edit (if applicable).
"""
# Customize the following

TYPES_OF_MAP = [
    "SINGLE",
    "MULTI",
    "PIO",
    "TIME-ATTACK",
    "MEGAMAP",
    "MULTIMAP",
    "TUTORIAL",
    "HARDCORE",
    "MILDCORE",
    "OUT-OF-MAP",
    "ABLOCK",
    "NOSTALGIA"
]

ROLE_WHITELIST = [
    195542852518805504,  # TEST - Mod
    801645674617634886,  # TEST - Tester
]
MAP_CHANNEL_ID = 802362144506511400
RECORD_CHANNEL_ID = 801496775390527548
MAP_SUBMIT_CHANNEL_ID = 802624308726726707
HIDDEN_VERIFICATION_CHANNEL = 811467249100652586

GUILD_ID = 195387617972322306

BOT_ID = 808340225460928552

# The amount of servers required for a bot to be eligible for verification.
VERIFICATION_GUILD_COUNT_TRESHOLD = 75

BAD_BOT_PERCENTAGE_TRESHOLD = 35  # The % of bot accounts in a server in order for the server to be considered low quality

CONFIRM_REACTION_EMOJI = "🟢"  # Reaction emoji used to confirm actions
CANCEL_REACTION_EMOJI = "🟥"  # Reaction emoji used to cancel actions

CONFIRMATION_TEXT = f"*Please react to this message with {CONFIRM_REACTION_EMOJI} to continue, or react with {CANCEL_REACTION_EMOJI} to cancel. Waiting for two minutes will cancel the process automatically.*"  # Message sent at the bottom of every reaction confirmaation

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
NEWEST_MAPS_LIMIT = 7

# Map names | CUSTOMIZE ACCEPTABLE NAMES
AYUTTHAYA = ["ayutthaya", "ayutt"]
BLACKFOREST = ["blackforest", "bf"]
BLIZZARDWORLD = ["blizzardworld", "bw", "blizz", "blizzworld"]
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
WATCHPOINTGIBRALTAR = ["watchpointgibraltar", "gibraltar"]
KINGSROW = ["kingsrow", "kr"]
PETRA = ["petra"]
ECOPOINTANTARCTICA = ["ecopointantarctica", "ecopoint", "antarctica"]
KANEZAKA = ["kanezaka", "kz", "kane", "zaka"]
WORKSHOPCHAMBER = ["workshopchamber", "chamber"]
WORKSHOPEXPANSE = ["workshopexpanse", "expanse"]
WORKSHOPGREENSCREEN = ["workshopgreenscreen", "green", "greenscreen"]
WORKSHOPISLAND = ["workshopisland", "island"]
PRACTICERANGE = ["practicerange", "practice", "pr"]

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
}
