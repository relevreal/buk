from enum import Enum


sports = [
    ('ALPINE_SKIING', 'Narciarstwo alpejskie'),
    ('BADMINTON', 'Badminton'),
    ('BASEBALL', 'Baseball'),
    ('BASKETBALL', 'Koszykówka'),
    ('BEACH_VOLLEYBALL', 'Siatkowka plażowa'),
    ('BIATHLON', 'Biatlon'),
    ('COUNTER_STRIKE', 'Counter Strike'),
    ('CRICKET', 'Krykiet'),
    ('CROSS_COUNTRY_SKIING', 'Biegi Narciarskie'),
    ('DARTS', 'Lotki'),
    ('DOTA_2', 'Dota 2'),
    ('ESPORT', 'Esport'),
    ('FIFA', 'Fifa'),
    ('FIELD_HOCKEY', 'Hokey na trawie'),
    ('FOOTBALL', 'Piłka nożna'),
    ('FORMULA_1', 'Formuła 1'),
    ('FUTSAL', 'Futsal'),
    ('GOLF', 'Golf'),
    ('HANDBALL', 'Piłka ręczna'),
    ('ICE_HOCKEY', 'Hokej na lodzie'),
    ('LEAGUE_OF_LEGENDS', 'League of Legends'),
    ('LUGE', 'Saneczkarstwo'),
    ('RUGBY', 'Rugby'),
    ('SKI_JUMPING', 'Skoki Narciarskie'),
    ('SLAG', 'Żużel'),
    ('SNOOKER', 'Snooker'),
    ('TABLE_TENNIS', 'Tenis stołowy'),
    ('TENNIS', 'Tenis'),
    ('UNIHOCKEY', 'Unihokej'),
    ('WATERBALL', 'Piłka wodna'),
    ('VALORANT', 'Valorant'),
    ('VOLLEYBALL', 'Siatkówka'),
]

SPORTS = {
    v[1]: i
    for i, v in enumerate(sports, 1)
}

SPORT = Enum('Sport', sports)
