import MyConfig
import redis
config = {
        'host': MyConfig.conf_dic['redis']['ip'], 
        'port': MyConfig.conf_dic['redis']['port'],
        'db': 0,
        }

r = redis.Redis(**config)
def redis_set(name, value):
    r.set(name, value)
def redis_get(name):
    return r.get(name)
