"""Formas irregulares muy comunes -> lema (parche-55). Las deduce mal el lematizador de la escuela ("duerme" -> "duermar");
con esto la base es correcta desde el principio y ENTENDI solo tiene que corregir lo raro."""
_V = {
    "dormir": "duermo duermes duerme dormimos duermen durmio durmieron dormia",
    "poder": "puedo puedes puede podemos pueden pudo pudieron podia",
    "querer": "quiero quieres quiere queremos quieren quiso quisieron queria",
    "venir": "vengo vienes viene venimos vienen vino vinieron venia",
    "hacer": "hago haces hace hacemos hacen hizo hicieron hacia",
    "decir": "digo dices dice decimos dicen dijo dijeron decia",
    "tener": "tengo tienes tiene tenemos tienen tuvo tuvieron tenia",
    "saber": "se sabes sabe sabemos saben supo supieron sabia",
    "ver": "veo ves ve vemos ven vio vieron veia",
    "dar": "doy das da damos dan dio dieron daba",
    "poner": "pongo pones pone ponemos ponen puso pusieron ponia",
    "salir": "salgo sales sale salimos salen salio salieron salia",
    "volver": "vuelvo vuelves vuelve volvemos vuelven volvio volvieron volvia",
    "jugar": "juego juegas juega jugamos juegan jugo jugaron jugaba",
    "morir": "muero mueres muere morimos mueren murio murieron moria",
    "pedir": "pido pides pide pedimos piden pidio pidieron pedia",
    "seguir": "sigo sigues sigue seguimos siguen siguio siguieron seguia",
    "sentir": "siento sientes siente sentimos sienten sintio sintieron sentia",
    "empezar": "empiezo empiezas empieza empezamos empiezan empezo empezaron",
    "encontrar": "encuentro encuentras encuentra encontramos encuentran",
    "pensar": "pienso piensas piensa pensamos piensan",
    "contar": "cuento cuentas cuenta contamos cuentan",
    "recordar": "recuerdo recuerdas recuerda recordamos recuerdan",
    "cerrar": "cierro cierras cierra cerramos cierran",
    "abrir": "abro abres abre abrimos abren abrio abrieron",
    "correr": "corro corres corre corremos corren corrio corrieron",
    "comer": "como comes come comemos comen comio comieron",
    "vivir": "vivo vives vive vivimos viven vivio vivieron",
    "ir": "voy vas va vamos van fue fueron iba",
    "llegar": "llego llegas llega llegamos llegan llego llegaron",
    "nadar": "nado nadas nada nadamos nadan nado nadaron",
    "llover": "llueve llovio",
    "cenar": "ceno cenas cena cenamos cenan ceno cenaron",
    "sonreir": "sonrio sonries sonrie sonreimos sonrien sonrio sonrieron",
    "volar": "vuelo vuelas vuela volamos vuelan volo volaron volaba",
    "oler": "huele huelen olio",
    "llorar": "lloro lloras llora lloramos lloran",
    "caer": "caigo caes cae caemos caen cayo cayeron",
    "oir": "oigo oyes oye oimos oyen oyo oyeron",
    "traer": "traigo traes trae traemos traen trajo trajeron",
    "conocer": "conozco conoces conoce conocemos conocen conocio",
    "producir": "produzco produces produce producimos producen produjo",
}
IRREG = {}
for _lemma, _forms in _V.items():
    for _f in _forms.split():
        IRREG.setdefault(_f, _lemma)
IRREG.pop("se", None)          # "se" es casi siempre pronombre
IRREG.pop("como", None)        # "como" casi siempre es adverbio/conjuncion
IRREG.pop("nada", None)        # "nada" es pronombre en la mayoria de los casos
IRREG.pop("va", None) if False else None
