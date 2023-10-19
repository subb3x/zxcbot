settings = {
    'token': 'token',
    'prefix': 'prefix'
}

voice_channel = {
    'channel_id': None,  # id of the channel from which users will be moved
    'category_id': None  # id of the category in which new private channels will appear
}

fields_main = {
    "Создание кастомных каналов пользователями": "- При заходе пользователем в специальный канал, создается его личный голосовой канал",
    "Модерация": "- Использование специальных команд (/mute, /warn, /report и т.д.) для упрощения модерации на сервере",
    "Система репортов": "- Возможность для каждого участника сервера, отправить жалобу на другого участника, которая будет рассмотрена модераторами",
    "Система тикетов": "- Возможность пользователя задать любой вопрос, касающийся сервера и получить ответ от модераторов"
}

fields_additional = {
    "Автор бота:": "- Данный бот был создан subb3x (tg: @suptrix)",
    "Цель создания бота:": "- Данный бот был создан для портфолио и опубликован в GitHub: github.com/subb3x",
    "Канал автора:": "- Первоначальное расположение бота и по совместительству канал автора - дискорд канал floppaнцы: https://discord.gg/55Kwbs7FYb"
}

roles = {
    'autorole_id': None,  # id of the role, that will be given to every newbie on the server

    'moderators_role': None,  # id of the moderators role

    'muted_role_id': None  # id of the muted role
}

warns = {
    'max_warns': 3,  # Max number of warns before user gets banned
    'warns_duration': 7  # Duration of every single warn (in days)
}

report_channel = None  # id of the channel where reports will be sent to moderators

deleted_log_channel = None  # id of the channel where deleted messages will be sent

mute_reconnect = None  # id of the channel where muted users will be moved to be moved back in prefious channel but with updated permissions
