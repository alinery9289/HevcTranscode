#encoding:utf-8
import os
import ConfigParser

#conf_file = os.getenv('DISTRIBUTED_TRANSCODER_CONF') + '\\conf.conf'
conf_file = 'D:\\Work\\workspace\\hd_4k_filter\\Conf' + '\\conf.conf'
conf = ConfigParser.ConfigParser()
conf.read(conf_file)

sections = conf.sections() 
conf_dic = {}
for section in sections:
    one_conf_dic={}
    for oneitem in conf.items(section):
        one_conf_dic[oneitem[0]]=oneitem[1]
    conf_dic[section]=one_conf_dic