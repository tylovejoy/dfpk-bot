def enum(**kwargs):
    return type('Enum', (), kwargs)


tournament_category = enum(HC="HC", TA="TA", MC="MC", BONUS="BONUS")
