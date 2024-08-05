LOGGING_CONFIG = {
    'version': 1,
    'formatters': {
        'info': {
            'format': '%(asctime)s %(levelname)s %(module)s: %(message)s'
        },
        'error': {
            'format': '%(asctime)s %(levelname)s %(name)s %(process)d::%(module)s|%(lineno)s:: %(message)s'
        },
    },
    'handlers': {
        'console_handler': {
            'level': 'INFO',
            'formatter': 'info',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
        },
    },
    'loggers': {
        '': {  # root logger
            'level': 'NOTSET',
            'handlers': ['console_handler'],
        },
    },
}
