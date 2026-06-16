from slowapi import Limiter, get_remote_address

limiter = Limiter(key_func=get_remote_address)
