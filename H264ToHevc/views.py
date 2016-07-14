#-*- coding:utf-8 -*-
import tasks 
import json
import uuid
import redistool
import time

from django.shortcuts import *
from django.http import *
from forms import *
from models import *
from methods import *
from datetime import datetime

# httpstr = "http://localhost:8000/mediafile/fileid/"
# userftp = "G:/BlueRay/user/"

httpstr = MainConf.main_conf_dic['all']['httpstr']
userftp = MainConf.main_conf_dic['all']['userftp']

def tctcreate(request):
#     form = ftpFileForm(request.POST)
    if (request.method!='POST' ):
        return HttpResponse()
#     filterparam = str( form.cleaned_data['filterparam'])
    filterparam_json = json.loads(request.body.encode("utf-8"), encoding="utf-8")
    print filterparam_json
    #new var
    filePath = filterparam_json["task"]["in_uri"]
    #new method add to file system
    
    #add media file
    fileid = str(uuid.uuid1()).replace('-','')
    filename = filePath.split('/')[-1] #filename in oursystem
    filetype = filterparam_json["task"]["in_format"].split('.')[-1]
    authcode = "38a43f8070e811e5ad0c90b11c94ab4d"
    oneFile = models.mediafile(fileid=fileid,filename=filename,authcode=authcode,filesize=0,location= filePath,filetype=filetype,uploadtime= datetime.now(),encodeinfo= ' ' )
    oneFile.save()
    
    #add task log
    taskid = filterparam_json["task"]["task_id"] #filterparam_json["task"]["task_id"]?or our own taskid
    hevc_param = {'keyframemin':'50','keyframemax':'50','vbvmaxbitrate':'30000' ,
                  'vbvbuffersize':'15000','bitrate':'15000'}
    json_tmp = {}
    json_tmp['taskid']=taskid
    json_tmp['before_file']={}
    json_tmp['before_file']['fileid']=fileid
    json_tmp['before_file']['authcode']=authcode
    json_tmp['before_file']['filetype']=filetype
    json_tmp['before_file']['location']=str(filePath)
    json_tmp['filters']={}
    json_tmp['filters']['ffmpeg']={}
    json_tmp['filters']['ffmpeg']['hevc_param']=hevc_param
    json_tmp['after_file']={}
    json_tmp['after_file']['out_path']='file://'+str(filterparam_json["task"]["out_list"][0]["out_path"])
    
    oneProcesslog = processlog(taskid=taskid, fileid=fileid,dealmethod="transcode",
                               controljson=json_tmp, dealstate="processing",dealtime= datetime.now())
    oneProcesslog.save()
    redistool.redis_set('_'.join(["task","status",taskid]), "Waiting to be processed...")
    send_processlog(taskid,filterparam_json["task"]["out_list"][0])
    tasks.ffmpeg_transcode.delay(json_tmp)
    json_ret = {}
    for name in ['cmd_code','from','to','timestamp']:
        json_ret[name] = filterparam_json[name]
    ts = datetime.now()
    timeStr=ts.strftime("%Y%m%d_%H%M%S")
    json_ret['re_timestamp'] = timeStr
    json_ret['err_code'] = "0"
    json_ret["err_info"] = ""
    return HttpResponse(json.dumps(json_ret))


def transcodePage(request):
    return render(request, 'transcode.html')

def filelistPage(request):
    return render(request, 'filelist.html')

def userProc(request):
    if request.method == 'POST':# 当提交表单时
     
        form = UserLoginForm(request.POST) # form 包含提交的数据
         
        if form.is_valid():# 如果提交的数据合法
            username =str( form.cleaned_data['userid'])
            password = str( form.cleaned_data['password'])
            #print authcode1+" "+username1+" "+password1+" "+email1
            this_users = models.user.objects.filter(userid = username)
            if this_users.count() > 0 :
                for this_user in list(this_users):
                    if this_user.password == md5(password):
                        response =HttpResponseRedirect(request.META['HTTP_REFERER'])
                        
                        response.set_cookie("authcode",this_user.authcode, 24*60*60)
                        return response
                    else : return HttpResponse('Error: The password is wrong! <a href="/">Click to login again!</a>')
                    break
            else : return HttpResponse('Error: Don\'t have this user ! <a href="/">Click to register first!</a>')
        else: return HttpResponse('Error: Can\'t login! <a href="/">Click to login again.</a>')

def userAuthProc(request,authcode):
    if request.method == 'GET':# 当提交表单时
        
        this_users = models.user.objects.filter(authcode = authcode)
        
        if this_users.count() > 0 :
            for this_user in list(this_users):
                response_data = {}
                response_data['username'] = this_user.userid
                response_data['storage'] = filesizeChange(this_user.userstorage)
                return HttpResponse(json.dumps(response_data), content_type="application/json")
        else : return HttpResponse('Error: Something wrong! <a href="/">Click to login again!</a>')

def userRegistrationProc(request):
    if request.method == 'POST':# 当提交表单时
     
        form = AddUserForm(request.POST) # form 包含提交的数据
         
        if form.is_valid():# 如果提交的数据合法
            authcode1=str(uuid.uuid1()).replace('-','')
            username1 =str( form.cleaned_data['userid'])
            password1 = str( form.cleaned_data['password'])
            password2 = str( form.cleaned_data['check_password'])
            email1 = str( form.cleaned_data['email'])
            #print authcode1+" "+username1+" "+password1+" "+email1
            if usernameExist(username1) > 0 :
                return HttpResponse('The username already exist! <a href="/">Click to register again.</a>')
            if emailExist(email1) > 0 :
                return HttpResponse('The email already exist! <a href="/">Click to register again.</a>')
            
            if password1==password2:
                oneUser = user(authcode=authcode1,userid=username1,password=md5(password1),email=email1,userstorage=0)
                oneUser.save()
                return HttpResponse('Register ok! <a href="/">Click to back.</a>')
            else : return HttpResponse('Error: The two password are different! <a href="/">Click to register again.</a>')
        else: return HttpResponse('Error: Can\'t register! <a href="/">Click to register again.</a>')
        
def mediaFileProc(request):
    if request.method == 'POST':
        form = AuthUploadForm(request.POST, request.FILES)
        if form.is_valid():
            authcode =str( form.cleaned_data['authcode'])
            saveResult=handleAllUploadedFile(request.FILES.getlist("fileList"),authcode)
            updateAuthStorage(authcode)
            return HttpResponse(saveResult)
    return HttpResponse("Error")

def ftpMediaFileName(request,authcode):
    if request.method == 'GET':
        response_data ={}
        list1= []
        list2= os.listdir(userftp+'upload')
        for a in list2:
            b= a.decode('gbk')
            list1.append(b)
        response_data["fileList"]=list1
        return HttpResponse(json.dumps(response_data,ensure_ascii=False,encoding='utf-8'), content_type="application/json")
    return HttpResponse("Error")
    
def ftpMediaFileProc(request):
    if request.method == 'POST':
        form = ftpFileForm(request.POST)
        if form.is_valid():
            authcode =str( form.cleaned_data['authcode'])
            filename =str( form.cleaned_data['filename'])
            saveResult=handleFtpFile(authcode,filename)
            updateAuthStorage(authcode)
            return HttpResponse(saveResult)
    return HttpResponse("Error")

def ftpMediaFileByIdProc(request, fileid, authcode):
    if  request.method == 'GET':
        onefile = models.mediafile.objects.get(fileid = fileid)
        if onefile.authcode==authcode:
            try:
                copyfiletoUser(onefile.location,onefile.filename)
                return HttpResponse("succeed")
            except EOFError:
                return HttpResponse("error")  
    return HttpResponse("error")  

def H264toHevcProc(request):
    if request.method == 'POST':
        form = ftpFileForm(request.POST)
        if form.is_valid():
            filterparam = str( form.cleaned_data['filterparam'])
            filterparam_json = json.loads(filterparam)
            authcode = filterparam_json['before_file']['authcode']
            filename = filterparam_json['before_file']['filename']
            #add to file manage system
            fileid=handleFtpFile(authcode,filename)            
            if (fileid=="error"):
                return HttpResponse("Error")
            #update user table
            updateAuthStorage(authcode)
            #add process(task) log  
            taskid= str(uuid.uuid1()).replace('-','')
            filterparam_json['taskid'] = taskid
            filterparam_json['before_file']['fileid'] = fileid
            filterparam_json['before_file']['filetype'] = filename.split('.')[-1]
            oneProcesslog = processlog(taskid=taskid, fileid=fileid,dealmethod="transcode",controljson=filterparam_json, dealstate="processing",dealtime= datetime.now())
            oneProcesslog.save()
            #add Redis state
#             r.set('_'.join(["task","status",taskid]), "Copying file to workstation...")
            redistool.redis_set('_'.join(["task","status",taskid]), "Waiting to be processed...")
#            tasks.hd_to_4k.delay(filterparam_json)
            tasks.ffmpeg_transcode.delay(filterparam_json)
#             handleTranscodeTest(authcode, fileid)
            return HttpResponse(taskid)
    return HttpResponse("Error")

def H264toHevcInfoProc(request,taskid):
    if request.method == 'GET':
#         processlog=r.get('_'.join(["task","status",taskid]))
        processlog=redistool.redis_get('_'.join(["task","status",taskid]))
        if processlog == '':
            return HttpResponse("Error")
        else :
            return HttpResponse(processlog)
    return HttpResponse("Error")

def H264toHevcInfoByAuthProc(request,authcode):
    if request.method == 'GET':
        dealfiles = models.mediafile.objects.filter(authcode = authcode)
        response_datas = []
        if dealfiles.count() >0:
            dict={}
            fileids = []
            for dealfile in list(dealfiles):
                fileids.append(dealfile.fileid)
                dict[dealfile.fileid] = dealfile.filename
            processlogs = models.processlog.objects.filter(fileid__in = fileids, dealmethod = 'transcode', dealstate__in = ['raw','pending','processing']).order_by('-dealtime')
            if processlogs.count()>0:
                for oneprocesslog in list(processlogs):
                    response_data ={}
                    response_data["taskid"]=oneprocesslog.taskid
                    response_data["fileid"]=oneprocesslog.fileid
                    response_data["filename"]=dict[oneprocesslog.fileid]
                    response_datas.append(response_data)
            return HttpResponse(json.dumps(response_datas), content_type="application/json")
        return HttpResponse(json.dumps(response_datas), content_type="application/json")
    return HttpResponse('error')
    
def mediaFileByIdProc(request, fileid, authcode):
    if request.method == 'GET':
        this_files = models.mediafile.objects.filter(fileid = fileid)
        if this_files.count() > 0 :
            for this_file in list(this_files):
                if (authcode != this_file.authcode):
                    return HttpResponse("the file and the user don't match!")
                response = StreamingHttpResponse(file_iterator(this_file.location))
                response['Content-Type'] = 'application/octet-stream;charset=UTF-8'
                response['Content-Disposition'] = 'attachment; filename=%s' % this_file.filename
            return response
        else: return HttpResponse("Don't have this file!")
    elif request.method == 'DELETE':
        this_files = models.mediafile.objects.filter(fileid = fileid)
        filename = ""
        if this_files.count() > 0 :
            for this_file in list(this_files):
                if (authcode != this_file.authcode):
                    return HttpResponse("the file and the user don't match!")
                filename= this_file.filename
                this_file.delete()
                if os.path.exists(this_file.location):
                    os.remove(this_file.location)
            updateAuthStorage(authcode)
        this_logs = models.processlog.objects.filter(fileid = fileid)
        if this_logs.count()>0 :
            for this_log in list(this_logs):
                this_log.delete()
        this_logs = models.processlog.objects.filter(afterfileid = fileid)
        if this_logs.count()>0 :
            for this_log in list(this_logs):
                this_log.delete()
        return HttpResponse('File '+ filename +' delete ok!')

def mediaFileInfoByIdProc(request, fileid, authcode):
    if request.method == 'GET':
        this_files = models.mediafile.objects.filter(fileid = fileid)
        if this_files.count() > 0 :
            for this_file in list(this_files):
                if (authcode != this_file.authcode):
                    return HttpResponse("the file and the user don't match!")
                response_data ={}
                response_data["fileid"]=fileid
                response_data["filename"]=this_file.filename
                response_data["authcode"]=this_file.authcode
                response_data["location"]=''.join([httpstr,this_file.fileid,'/authcode/',this_file.authcode])
                response_data["filesize"]=filesizeChange(this_file.filesize)
                response_data["filetype"]=this_file.filetype
                response_data["uploadtime"]=this_file.uploadtime.strftime("%Y-%m-%d %H:%M:%S")
                response_data["encodeinfo"]=this_file.encodeinfo
            return HttpResponse(json.dumps(response_data), content_type="application/json")
        
def mediaFileInfoByAuthProc(request,authcode):
    if request.method == 'GET':
        this_files = models.mediafile.objects.filter(authcode = authcode).order_by("-uploadtime")
        response_datas = []
        if this_files.count() > 0 :
            for this_file in list(this_files):
                response_data ={}
                response_data["fileid"]=this_file.fileid
                response_data["filename"]=this_file.filename
                response_data["location"]=''.join([httpstr,this_file.fileid,'/authcode/',this_file.authcode])
                response_data["filesize"]=filesizeChange(this_file.filesize)
                response_data["filetype"]=this_file.filetype
                response_data["uploadtime"]=this_file.uploadtime.strftime("%Y-%m-%d %H:%M:%S")
                response_data["encodeinfo"]=this_file.encodeinfo
                response_datas.append(response_data)
            return HttpResponse(json.dumps(response_datas), content_type="application/json")
        else : return HttpResponse(json.dumps(response_datas), content_type="application/json")
        
def mediaFileImagerecProc(request):
    if request.method == 'POST':
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            mySession=handleUploadedFile(request.FILES.getlist("fileList"))
            return HttpResponse(mySession)
    return HttpResponse("Error")
