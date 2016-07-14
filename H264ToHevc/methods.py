#-*- coding:utf-8 -*-
'''
Created on 2015年7月22日

@author: Zhangxusheng
'''
import uuid
import models
import shutil
import os
import re
import time
import json
import httplib
import MainConf
import redistool
import subprocess
import threading
from datetime import datetime

storageftp= MainConf.main_conf_dic['all']['storageftp']
userftp = MainConf.main_conf_dic['all']['userftp']
# tooldir_local = MainConf.main_conf_dic['all']['tooldir_local']

def handleUploadedFile(files):
    images = []
    for f in files:
        print(f.name)
        unique_id = str(uuid.uuid1()).replace('-','')
        file_ext  = f.name.split('.')[-1]
        filename  = '.'.join([unique_id, file_ext])
        print(filename)       
        dst_file  = ''.join([storageftp, filename])
        with open(dst_file, 'wb+') as fd:
            for chunk in f.chunks():
                fd.write(chunk)
  
        images.append([filename, f.name])
  
    return unique_id

def send_processlog(taskid, out_list_param):
    t = threading.Thread(target=send_processlog_proc,args=(taskid,out_list_param))
    t.setDaemon(True)
    t.start()
    print 'add get_process ok'
    
def send_processlog_proc(taskid, out_list_param):
    try : 
        res_schedule= re.compile(r"[\s\S]*schedule: (?P<status_percent>[\.0-9]*) %[\s\S]*")
        res_error= re.compile(r"[\s\S]*Please try again[\s\S]*")
        res_complete= re.compile(r"[\s\S]*all complete[\s\S]*")
        status_json ={'cmd_code':'0x06010002','from':'MCU','to':'VML',
            'timestamp':datetime.now().strftime("%Y%m%d_%H%M%S"),
            'task_list':{'task_id':taskid,
                         'out_list':{"output_id": out_list_param["output_id"], 'progress_percent':'0.0%'}
                    },
            }
        while True:
            processlog=str(redistool.redis_get('_'.join(["task","status",taskid])))
            if res_complete.match(processlog):
                reg_percent ='100.0%'
                break
            elif res_schedule.match(processlog):
                regMatch = res_schedule.match(processlog)
                linebits = regMatch.groupdict()    
                reg_percent = linebits['status_percent'] +'%' if linebits['status_percent']!='100.0' else '99.9%'
            elif res_error.match(processlog):
                reg_percent ='-1.0%'
                break
            else :
                reg_percent ='0.1%'
            status_json['task_list']['out_list']['progress_percent']= reg_percent
            http_post(status_json)
            time.sleep(1)
        status_json['task_list']['out_list']['progress_percent']= reg_percent
        http_post(status_json)
    except Exception, e:
        print e
def http_post(json_data):
    client = None
    try:
        client = httplib.HTTPConnection(MainConf.main_conf_dic['vml']['ip'],MainConf.main_conf_dic['vml']['port'])
        headers = {"Content-type": "application/json" , "Accept": "text/json"}
        json_data = json.JSONEncoder().encode(json_data)
        #params = urllib.urlencode({"filterparam": json_data}) 
        client.request('POST','/TCT_REPORT',json_data, headers)
        response = client.getresponse()
        result = response.read()
        print result
#         f = file('result.html','w')
#         f.write(str(result))
#         f.close()
    except Exception, e:
        print e


def handleAllUploadedFile(files,authcode):
    for f in files:
        import hashlib
        m = hashlib.md5() 
        print(f.name)
        fileid = str(uuid.uuid1()).replace('-','')
        if f.content_type:
            filetype = f.content_type
        else : filetype = f.name.split('.')[-1]   
        dst_file  = ''.join([storageftp, '.'.join([fileid, f.name.split('.')[-1]])])
        with open(dst_file, 'wb+') as fd:
            for chunk in f.chunks():
                fd.write(chunk)
                m.update(chunk)    
        try:
            oneFile = models.mediafile(fileid=fileid,filename=f.name,authcode=authcode,filesize=f.size,location= dst_file,filetype=filetype,md5=m.hexdigest(),uploadtime= datetime.now())
            oneFile.save()
        except EOFError: 
            return "Error! Please try again."
    
    return "save OK!"

def handleFtpFile(authcode,filename):
    upFolder= ''.join([userftp,'upload/',filename.decode('utf-8')])
    fileid = str(uuid.uuid1()).replace('-','')
    filetype = filename.split('.')[-1]   
    dst_file  = ''.join([ storageftp, '.'.join([fileid, filename.split('.')[-1]])])
    if os.path.isfile(upFolder):
        shutil.copyfile(str(upFolder),dst_file)
#         shutil.move(str(upFolder),dst_file)
        pass
    else :
        return "error"   
    encodeInfo = getEncodeInfo(dst_file)[:800]
    if os.path.isfile(dst_file):
        filesize= os.path.getsize(dst_file)
        oneFile = models.mediafile(fileid=fileid,filename=filename,authcode=authcode,filesize=filesize,location= dst_file,filetype=filetype,uploadtime= datetime.now(),encodeinfo= encodeInfo)
        oneFile.save()
        return fileid
    else :return "error"

def copyfiletoUser(sourcefile,targetfilename):
    targetfile = userftp+'download/'+ targetfilename
    shutil.copy(sourcefile,  targetfile)
      
def md5(beforestr):
    import hashlib
    m = hashlib.md5()   
    m.update(beforestr)
    return m.hexdigest()

def usernameExist(username):
    return models.user.objects.filter(userid = username).count()

def emailExist(email):
    return models.user.objects.filter(email = email).count()

def filesizeChange(filesize):
    if (filesize<1024):
        return str(round(filesize,2))+"B"
    elif (filesize>=1024 and filesize<1024*1024):
        return str(round(filesize/1024.0,2))+"KB"
    elif (filesize>=1024*1024):
        return str(round(filesize/1024.0/1024,2))+"MB"
    else :return str(round(filesize,2))+"B"

def file_iterator(file_name, chunk_size=1024*1024):
        with open(file_name,'rb+') as f:
            while True:
                c = f.read(chunk_size)
                if c:
                    yield c
                else:
                    break
                
def updateAuthStorage(authcode):
    storage_now =0
    this_files = models.mediafile.objects.filter(authcode = authcode)
    if this_files.count() > 0 :
        for this_file in list(this_files):
            storage_now+=this_file.filesize
    this_user = models.user.objects.filter(authcode = authcode)
    this_user.update(userstorage=storage_now)
    
def getEncodeInfo(filename):
    getFileinfoCmd= "%s -show_format -i %s" % (MainConf.main_conf_dic['tools']['ffprobe'],filename)

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
            
            