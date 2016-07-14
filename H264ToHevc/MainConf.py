#encoding:utf-8
import os
import ConfigParser

#conf_file = os.getenv('DISTRIBUTED_TRANSCODER_CONF') + '\\conf.conf'
conf_file = 'C:\\Transcode\\Main\\HevcTranscode\\H264ToHevc\\Conf' + '\\mainConf.conf'
conf = ConfigParser.ConfigParser()
conf.read(conf_file)

sections = conf.sections() 
main_conf_dic = {}
for section in sections:
    one_conf_dic={}
    for oneitem in conf.items(section):
        one_conf_dic[oneitem[0]]=oneitem[1]
    main_conf_dic[section]=one_conf_dic
