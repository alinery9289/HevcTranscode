# encoding:utf-8
import time
from celery.task import task
from ftpConnection import MYFTP
from image_talk import neural_talk
import os 
import subprocess
from datetime import datetime

import redis
import uuid
import shutil
import models
from _mysql import NULL

#----------------------------------------------------------------------
#           start Redis client for publishing messages
#----------------------------------------------------------------------
config = {
        'host': '127.0.0.1', # accpet any connections
#         'host': '172.16.6.157', # Redis server address
        'port': 6379, 
#         'password': 123456,
        'db': 0,
        }

# start redis server
#r = redis.StrictRedis(**config)
r = redis.Redis(**config)

 
hostaddr = '192.168.112.74' # windows ftp地址
# hostaddr = '172.16.6.157' # linux ftp地址
username = 'mediaftp' # 用户名
password = 'medialab313' # 密码
port  =  21   # 端口号 
rootdir_local = 'D:/Work/testFiles/' #linux  本地目录
tooldir_local = 'D:/Work/tools/'
# rootdir_local  = '/home/medialab/deploy/imagecache/' #linux  本地目录
rootdir_remote = '/'          # 远程目录
rootdir_real_remote= 'D:/Work/UploadFiles/'

@task
def image_recognition(images):
    """
    @param images - list of image files to be processed on remote ftp server,
           consists of [filename, org_filename] entries, where org_filename
           is the name when the image is uploaded
    @param csrfvar
    """
    # do the work
    f = MYFTP(hostaddr, username, password, rootdir_remote, port)
    f.login()

    unique_id = str(uuid.uuid1()).replace('-','')
    work_dir = ''.join([rootdir_local, unique_id])
    os.mkdir(work_dir)

    files = []
    
    image_index=1
    for img in images:
        filename, org_filename = img
        print(filename, org_filename)

        src_file = '/'.join([rootdir_remote, filename])
        dst_file = '/'.join([work_dir, filename])
        print ("src %s, dst %s" % (src_file, dst_file))
        f.download_file(dst_file, src_file)
        files.append(filename)
        time.sleep(5)
        image_index+=1

#     description = neural_talk(work_dir, files)
    
    # apped result to redis db
    #r.append(csrfvar, str(org_filename) + ": " + description)
    session_id = filename.split('.')[0]
    print image_index
#     r.append(session_id, description)
    for i in range (1,image_index):
        description = "There are many results."
        r.zadd(session_id,description+str(i)+"\n",i)
    shutil.rmtree(work_dir)
    

@task  
def trascodeTest(authcode,fileid):
    uploadreturnlist = copyFile(authcode,fileid)
    judgeUploadSuc,mediafile,oldfilename=uploadreturnlist[0],uploadreturnlist[1],uploadreturnlist[2]
    if judgeUploadSuc==False:
        r.set(''.join(["transcode_",authcode,fileid]), "Copy media file to workstation...\n Copy file failed! Please try again.")
    r.set(''.join(["transcode_",authcode,fileid]), "Copy media file to workstation...\n Copy file complete!\nStart to transcode...")
    
#     mediafile = "D:\\Work\\UploadFiles\\userupload\\test.flv" 
    aftermediafile= mediafile.split('.')[0]+"_trancodetest.mp4"
    getinfoCmd= "%sffprobe.exe -show_format -i %s" % (tooldir_local,mediafile)
    transcodeCmd= "%sffmpeg.exe -i %s -c:a copy -c:v libx265 -preset fast %s  -x265-params\
     --no-open-gop -x265-params --wpp -x265-params --lft \
    -x265-params --sao  -x265-params keyframeMin=50:keyframeMax=50:vbvMaxBitrate=30000:vbvBufferSize=30000:bitrate=5000"%(tooldir_local,mediafile,aftermediafile )

    process1 = subprocess.Popen(getinfoCmd, shell=True, stdout = subprocess.PIPE, stderr=subprocess.STDOUT,universal_newlines= True)
    while True:
        line = process1.stdout.readline()
        if not line:
            break
        lo = line.find('duration=')
        if lo!=-1:
            videoTime= float(line[int(lo)+9:])

    print videoTime
    
    process2 = subprocess.Popen(transcodeCmd, shell=True, stdout = subprocess.PIPE, stderr=subprocess.STDOUT,universal_newlines= True)        
    #print process1.communicate()[0]
 
    while True:
        line = process2.stdout.readline()
    
        if not line:
            break
        lo = line.find('time=')
        if lo!=-1:
            now_time= line[int(lo)+5:int(lo)+16].split(':')
            now_percent= (float(now_time[0])*3600+float(now_time[1])*60+float(now_time[2]))/videoTime
            print now_percent
            r.set(''.join(["transcode_",authcode,fileid]),"Copy media file to workstation...\n Copy file complete!\nStart to transcode : %.2f%%..."  %(now_percent*100))
    r.set(''.join(["transcode_",authcode,fileid]),"Copy media file to workstation...\n Copy file complete!\nStart to transcode : %.2f%%.\n Start to copy transcoded file back..."  %(100))
    sendbackreturnlist= sendbackFile(aftermediafile, authcode, oldfilename)
    judgeSendSuc,newfileid = sendbackreturnlist[0],sendbackreturnlist[1]
    if judgeSendSuc==False:
        r.set(''.join(["transcode_",authcode,fileid]),"Copy media file to workstation...\n Copy file complete!\nStart to transcode : %.2f%%.\n Start to copy transcoded file back... \nCopy failed."  %(100))
    
    newfilename =  '_'.join([oldfilename.split('.')[0],aftermediafile.split('_')[-1] ]) 
    r.set(''.join(["transcode_",authcode,fileid]),"Copy media file to workstation...\n Copy file complete!\nStart to transcode : %.2f%%.\nStart to copy transcoded file back... \nCopy Complete! \nAll complete. Download %s in fileist"  %(100,newfilename))
    r.expire(''.join(["transcode_",authcode,fileid]), 60)
    this_processlog = models.processlog.objects.filter(fileid = fileid, dealmethod = "transcodetest")
    this_processlog.update(dealstate='succeed', afterfileid=newfileid,completetime= datetime.now())
    this_processlog = models.processlog.objects.filter(fileid = fileid, dealmethod = "transcodetest")
    
    
def copyFile(authcode,fileid):
    try:
        f = MYFTP(hostaddr, username, password, rootdir_remote, port)
        f.login()
        work_dir = ''.join([rootdir_local, fileid])
        os.mkdir(work_dir)
        this_file = models.mediafile.objects.get(fileid = fileid)
        src_file = ''.join([rootdir_remote,'/storage/', fileid,'.',this_file.filename.split('.')[-1] ])
        dst_file = ''.join([work_dir, '/',fileid,'.',this_file.filename.split('.')[-1] ])
        print ("copy: src %s, dst %s" % (src_file, dst_file))
        f.download_file(dst_file, src_file)
        return [True,dst_file,this_file.filename]
    except EOFError:
        return [False,dst_file,this_file.filename]

def sendbackFile(localfile, authcode, oldfilename):
    try:
        
        newfileid = str(uuid.uuid1()).replace('-','')
        f = MYFTP(hostaddr, username, password, rootdir_remote, port)
        f.login()
        remote_file = ''.join([rootdir_remote,'/storage/', newfileid,'.',localfile.split('.')[-1] ]) 
        print ("sendback: dst %s, dst %s" % (remote_file, localfile))
        f.upload_file(localfile, remote_file)
        newfilename =  '_'.join([oldfilename.split('.')[-1],localfile.split('_')[-1] ])  
        newfiletype = newfilename.split('.')[-1]  
        filesize= os.path.getsize(localfile) 
        newlocation = ''.join([rootdir_real_remote,'storage/', '.'.join([newfileid, newfilename.split('.')[-1]])])
        newencodeInfo = getEncodeInfo(localfile)
        oneFile = models.mediafile(fileid=newfileid,filename=newfilename,authcode=authcode,filesize=filesize,location= newlocation,filetype=newfiletype,uploadtime= datetime.now(),encodeinfo= newencodeInfo)
        oneFile.save()
        shutil.rmtree(os.path.dirname(localfile))
        return [True,newfileid]
        
    except EOFError:
        return [False,'']
    
def getEncodeInfo(filename):
    getFileinfoCmd= "%sffprobe.exe -show_format -i %s" % (tooldir_local,filename)

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
    
    
    