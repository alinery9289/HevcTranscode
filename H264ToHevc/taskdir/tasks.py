import readTem
import MyConfig

from celery import Celery

app = Celery('tasks', broker='amqp://'+MyConfig.conf_dic['rabbitmq']['user']+':'+MyConfig.conf_dic['rabbitmq']['password']+'@'+MyConfig.conf_dic['rabbitmq']['ip']+':'+MyConfig.conf_dic['rabbitmq']['port'])

@app.task
def hd_to_4k(param_data):
    readTem.hd_to_4k(param_data)