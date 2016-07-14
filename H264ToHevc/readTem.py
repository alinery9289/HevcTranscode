# encoding= utf-8
import os
import re
import shutil 
import jinja2
import uuid
import subprocess
import MyConfig
import ftptool
import sqltool
import datetime
import logtool
import parse_state
import redistool

from collections import OrderedDict
from sqlalchemy.orm import sessionmaker

conf_dic = MyConfig.conf_dic

def getEncodeInfo(filename):
    getFileinfoCmd= "%s -show_format -i %s" % (conf_dic['4k_tool']['ffprobe'],filename)

    process1 = subprocess.Popen(getFileinfoCmd, shell=True, stdout = subprocess.PIPE, stderr=subprocess.STDOUT,universal_newlines= True)
    encodeInfo=""
    while True:
        line = process1.stdout.readline()
        if not line:
            break
        lo = line.find('Duration:')
        if lo!=-1:
            encodeInfo+=line
        lo = line.find('Stream #0:')
        if lo!=-1:
            encodeInfo+=line
    return encodeInfo

def hd_to_4k_uploader(param_data,localfile,nametag):
    try:
        
#         remotefile = ''.join(['storage/', newfileid,'.',localfile.split('.')[-1] ]) 
        
        reg = re.compile(r'file://(((?P<remoteuser>[^ ]*):(?P<remotepasswod>[^ ]*)@){0,1}(?P<remoteip>(?<![0-9.])((2[0-4][0-9]|25[0-5]|[01]?[0-9]{1,2})\.){3}(2[0-4][0-9]|25[0-5]|[01]?[0-9]{1,2})(?![0-9.])):(?P<remoteport>[\d]{1,5})/){0,1}(.*?:.*?/){0,1}(?P<location>[\s\S]*)')
        regMatch = reg.match(param_data['before_file']['location'])
        linebits = regMatch.groupdict()       
        username = linebits['remoteuser'] if linebits['remoteuser']!=None else MyConfig.conf_dic['remoteftp']['username']
        password = linebits['remotepasswod'] if linebits['remotepasswod']!=None else MyConfig.conf_dic['remoteftp']['password']
        hostaddr = linebits['remoteip'] if linebits['remoteip']!=None else MyConfig.conf_dic['remoteftp']['hostaddr']
        port  =  linebits['remoteport'] if linebits['remoteport']!=None else MyConfig.conf_dic['remoteftp']['port']
        remotefile  =  linebits['location'] 
        newfilepath =  ''.join([ ''.join(remotefile.split('.')[:-1]),nametag, '.',localfile.split('.')[-1] ]) 
        newfilename = ''.join([remotefile.split('/')[-1].split('.')[-2], nametag, '.',localfile.split('.')[-1] ]) 
        
        f = ftptool.MYFTP(hostaddr, username, password, ftptool.rootdir_remote, port)
        f.login()    
        f.upload_file(''.join([ftptool.rootdir_local,localfile]), ''.join([ftptool.rootdir_remote,newfilepath])) 
#         ftptool.upload_file(localfile, remotefile)
        
        Session = sessionmaker(bind=sqltool.engine)
        session = Session()       
        newfileid = str(uuid.uuid1()).replace('-','')
        newfiletype = newfilename.split('.')[-1]  
        filesize= os.path.getsize(''.join([conf_dic['all']['work_path'],'\\',localfile]))  
        newencodeInfo = getEncodeInfo(''.join([conf_dic['all']['work_path'],'\\',localfile]))
        newlocation =  ''.join([ ''.join(param_data['before_file']['location'].split('.')[:-1]),nametag, '.',localfile.split('.')[-1] ]) 
        oneFile = sqltool.Media_File(fileid=newfileid,filename=newfilename,authcode=param_data['before_file']['authcode'],filesize=filesize,\
                                     location= newlocation,filetype=newfiletype,uploadtime= datetime.datetime.now(),encodeinfo= newencodeInfo)
        
        session.add(oneFile)
#         oneusers = session.query(sqltool.User).filter( sqltool.User.authcode == param_data['before_file']['authcode'])
#         for oneuser in oneusers:
#             now_storage = oneuser.userstorage +filesize
#         oneusers.update({sqltool.User.userstorage : now_storage})
        session.commit()
        session.close()
        return [True,newfileid]
        
    except EOFError:
        return [False,'']

def hd_to_4k_downloader(param_data, file_tmp_name):
    try:
        file_work_basepath = ''.join([conf_dic['all']['work_path'],'\\',param_data['taskid']])
        if (os.path.exists(file_work_basepath)== False):    
            os.mkdir(file_work_basepath)
        
        reg = re.compile(r'file://(((?P<remoteuser>[^ ]*):(?P<remotepasswod>[^ ]*)@){0,1}(?P<remoteip>(?<![0-9.])((2[0-4][0-9]|25[0-5]|[01]?[0-9]{1,2})\.){3}(2[0-4][0-9]|25[0-5]|[01]?[0-9]{1,2})(?![0-9.])):(?P<remoteport>[\d]{1,5})/){0,1}(.*?:.*?/){0,1}(?P<location>[\s\S]*)')
        regMatch = reg.match(param_data['before_file']['location'])
        linebits = regMatch.groupdict()       
        username = linebits['remoteuser'] if linebits['remoteuser']!=None else MyConfig.conf_dic['remoteftp']['username']
        password = linebits['remotepasswod'] if linebits['remotepasswod']!=None else MyConfig.conf_dic['remoteftp']['password']
        hostaddr = linebits['remoteip'] if linebits['remoteip']!=None else MyConfig.conf_dic['remoteftp']['hostaddr']
        port  =  linebits['remoteport'] if linebits['remoteport']!=None else MyConfig.conf_dic['remoteftp']['port']
        remotefile  =  linebits['location'] 
#         remotefile = ''.join(['storage/', param_data['before_file']['fileid'],'.',param_data['before_file']['filetype'] ])
        localfile = ''.join([param_data['taskid'], '\\',file_tmp_name,'.',param_data['before_file']['filetype'] ])
        #download file
        f = ftptool.MYFTP(hostaddr, username, password, ftptool.rootdir_remote, port)
        f.login()    
        f.download_file(''.join([ftptool.rootdir_local,localfile]), ''.join([ftptool.rootdir_remote,remotefile]))
        
        #update file sql
        Session = sessionmaker(bind=sqltool.engine)
        session = Session()
        onefiles = session.query(sqltool.Media_File).filter( sqltool.Media_File.fileid == param_data['before_file']['fileid'])
        newfilesize = os.path.getsize(''.join([ftptool.rootdir_local,localfile]))
        newencodeInfo = getEncodeInfo(''.join([ftptool.rootdir_local,localfile]))[:800]
        onefiles.update({sqltool.Media_File.filesize : newfilesize,sqltool.Media_File.encodeinfo : newencodeInfo })
        session.commit()
        session.close()
        
        return True
    except EOFError:
        return False
    
def ffmpeg_transcode(param_data): 
    try: 
        #begin
        redistool.redis_set('_'.join(["task","status",param_data['taskid']]), "Copying file to workstation...")
        
        # initializtion 1.14
        parse_state.dic.clear()
        parse_state.prev_dic.clear()
        parse_state.process_step = "unprocessed"
        
        # file path and name
        file_work_basepath = ''.join([conf_dic['all']['work_path'],'\\',param_data['taskid']])
        file_tmp_name = '1'
        file_work_path =''.join([file_work_basepath,'\\'])
        before_file = ''.join([file_work_path, file_tmp_name, '.', param_data['before_file']['filetype']])
        after_file = ''.join([file_work_path, file_tmp_name, '_out.mp4'])
        
        hd_to_4k_downloader(param_data, file_tmp_name)
        bat_file_name = file_work_path + file_tmp_name + '_ffmpeg.bat'
        
        #load the control file template,set the parameter
        template_env = jinja2.Environment(loader = jinja2.FileSystemLoader(conf_dic['all']['template_path']))
        
        bat_file_tmp_param = {'before_file_name':before_file ,'after_file_name':after_file}
        bat_file_tmp_param.update(conf_dic['4k_tool'])
        bat_file_tmp_param.update(param_data['filters']['ffmpeg']['hevc_param'])
        bat_file_tmp = template_env.get_template('ffmpeg_bat_template.bat').render(bat_file_tmp_param)
        
        #write the new control file
        if (os.path.exists(file_work_basepath)== False):    
            os.mkdir(file_work_basepath)    
        lines = "\r\n".join(bat_file_tmp.split('\n'))
        bat_file = open(bat_file_name,'w+')
        bat_file.writelines(lines)
        bat_file.close()
        
        #download file and process and upload result
        process2 = subprocess.Popen(bat_file_name, shell=True, stdout = subprocess.PIPE, stderr=subprocess.STDOUT,universal_newlines= True)
        logtool.logger_main.info("Begin to Trancode, task: %s..."%param_data['taskid'])
        one_log = logtool.Pro_log(param_data['taskid'])
        while True:
            line = process2.stdout.readline()
            print line
            parse_state.add_ffmpeg_state_to_redis(param_data['taskid'],line)
            one_log.info(line)
            if not line:
                break
        
        logtool.logger_main.info("Trancode task: %s ok!"%param_data['taskid'])
        hd_to_4k_uploader(param_data,''.join([ param_data['taskid'],'\\',file_tmp_name, '_out.mp4']),"_265")
        shutil.rmtree(file_work_basepath)
        
        #update processlog
        Session = sessionmaker(bind=sqltool.engine)
        session = Session()
        oneprocesslog = session.query(sqltool.Web_Task).filter( sqltool.Web_Task.taskid == param_data['taskid'])
        oneprocesslog.update({sqltool.Web_Task.dealstate : 'succeed', sqltool.Web_Task.completetime : datetime.datetime.now()})
            
        session.commit()
        session.close()
        parse_state.add_ffmpeg_state_to_redis(param_data['taskid'],'all_complete\n')  
    except EOFError:
        redistool.redis_set('_'.join(["task","status",param_data['taskid']]), "Error, please try again or connect to sdzhangxusheng@163.com!")
