from .base import *  # noqa: F401,F403

from decouple import config

DEBUG = config('DEBUG', default=False, cast=bool)

if DEBUG:
    from .dev import *  # noqa: F401,F403
else:
    from .production import *  # noqa: F401,F403
