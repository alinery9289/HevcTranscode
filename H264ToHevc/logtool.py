import os
import MyConfig
import logging
import logging.handlers

log_path = MyConfig.conf_dic['all']['log_path']  
  
handler_main = logging.handlers.RotatingFileHandler(log_path+'\\log_main.log')  
fmt = '%(asctime)s [%(levelname)s] %(message)s' 
datefmt='%a, %d %b %Y %H:%M:%S' 
  
formatter = logging.Formatter(fmt= fmt, datefmt= datefmt)   
handler_main.setFormatter(formatter)       
  
logger_main = logging.getLogger('main_log')    
logger_main.addHandler(handler_main)           
logger_main.setLevel(logging.DEBUG)   

class Pro_log():
    
    def __init__(self,fileid):
        self.fileid = fileid
        self.this_log = logging.getLogger(fileid+'_log')
        if (os.path.exists(log_path + '\\transcode_log')== False):    
            os.mkdir(log_path + '\\transcode_log')
        self.this_handler= logging.handlers.RotatingFileHandler(log_path + '\\transcode_log\\'+fileid+'_log.log')
        self.this_handler.setFormatter(formatter)
        self.this_log.addHandler(self.this_handler)
        self.this_log.setLevel(logging.DEBUG) 
        
    def debug(self, msg):
        self.this_log.debug(msg)
        
    def info(self, msg):
        self.this_log.info(msg)
        
    def warning(self, msg):
        self.this_log.warning(msg)
        
    def error(self, msg):
        self.this_log.error(msg)
