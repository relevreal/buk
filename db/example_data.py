EXAMPLE_DATA = {
    'name': 'Liban - Chiny',
    'competition': 'AFC Puchar Azji',
    'country': 'ZY',
    'sport': 'Piłka nożna',
    'date': '2024-01-17T11:30:00Z',
    'score': ('0', '0'),
    'is_live': True,
    'markets': [
        {
            'name': 'Wynik meczu (z wyłączeniem dogrywki)',
            'odds': [
                ('Liban', 6.5),
                ('Remis', 1.6),
                ('Chiny', 3.65),
            ],
        },
        {
            'name': 'Liczba goli',
            'odds': [
                ('1', 777.5),
                ('2', 111.6),
                ('3', 333.6),
                ('4', 444.6),
            ],
        },
    ],
    'open_market_count': 10,
}

EXAMPLE_DATA_MOD = {
    'name': 'Liban - Chiny',
    'competition': 'AFC Puchar Azji',
    'country': 'ZY',
    'sport': 'Piłka nożna',
    'date': '2024-01-17T11:30:00Z',
    'score': ('2', '1'),
    'is_live': True,
    'markets': [
        {
            'name': 'Wynik meczu (z wyłączeniem dogrywki)',
            'odds': [
                ('Liban', 777.5),
                ('Remis', 111.6),
                ('Chiny', 333.6),
            ],
        },
    ],
    'open_market_count': 999,
}
