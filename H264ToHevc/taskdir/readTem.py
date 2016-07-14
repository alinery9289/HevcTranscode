# encoding= utf-8
import os
import jinja2
import uuid
import subprocess
import MyConfig
import ftptool
import sqltool
import datetime

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
        
        newfileid = str(uuid.uuid1()).replace('-','')
        remotefile = ''.join(['storage/', newfileid,'.',localfile.split('.')[-1] ]) 
        ftptool.upload_file(localfile, remotefile)
        
        Session = sessionmaker(bind=sqltool.engine)
        session = Session()
        
        onefiles = session.query(sqltool.Media_File).filter( sqltool.Media_File.fileid == param_data['before_file']['fileid'])
        for onefile in onefiles:
            oldfilename = onefile.filename
        
        newfilename =  ''.join([oldfilename.split('.')[-2], nametag, '.',localfile.split('.')[-1] ])  
        newfiletype = newfilename.split('.')[-1]  
        filesize= os.path.getsize(''.join([conf_dic['all']['work_path'],'\\',localfile]))  
        
        newlocation = ''.join([conf_dic['ftp']['rootdir_real_remote'],'/storage/', '.'.join([newfileid, newfilename.split('.')[-1]])])
        newencodeInfo = getEncodeInfo(localfile)
        
        oneFile = sqltool.Media_File(fileid=newfileid,filename=newfilename,authcode=param_data['before_file']['authcode'],filesize=filesize,\
                                     location= newlocation,filetype=newfiletype,uploadtime= datetime.datetime.now(),encodeinfo= newencodeInfo)
        
        session.add(oneFile)
        oneusers = session.query(sqltool.User).filter( sqltool.User.authcode == param_data['before_file']['authcode'])
        for oneuser in oneusers:
            now_storage = oneuser.userstorage +filesize
        oneusers.update({sqltool.User.userstorage : now_storage})
        
        session.commit()
        session.close()
        return [True,newfileid]
        
    except EOFError:
        return [False,'']

def hd_to_4k_downloader(param_data, file_tmp_name):
    try:
        file_work_basepath = ''.join([conf_dic['all']['work_path'],'\\',param_data['before_file']['fileid']])
        if (os.path.exists(file_work_basepath)== False):    
            os.mkdir(file_work_basepath)

        remotefile = ''.join(['storage/', param_data['before_file']['fileid'],'.',param_data['before_file']['filetype'] ])
        localfile = ''.join([param_data['before_file']['fileid'], '\\',file_tmp_name,'.',param_data['before_file']['filetype'] ])
        ftptool.get_file(localfile, remotefile)
        return True
    except EOFError:
        return False

def hd_to_4k(param_data):
    # file path and name
    file_work_basepath = ''.join([conf_dic['all']['work_path'],'\\',param_data['before_file']['fileid']])
    file_tmp_name = '1'
    file_work_path =''.join([file_work_basepath,'\\'])
    h264_file = ''.join([file_work_path, file_tmp_name, '.', param_data['before_file']['filetype']])
    sub_speedup_file = ''.join([file_work_path, file_tmp_name, '_exp.sub'])
    hevc_file = ''.join([file_work_path, file_tmp_name, '.hevc'])
    
    combination_param = {'audio_file' : ''.join([file_work_path, file_tmp_name, '.',param_data['before_file']['audiotype']]),
                         'audio_speedup_file' :  ''.join([file_work_path, file_tmp_name, '_speedup.',param_data['before_file']['audiotype']]),
                         'audio_speedup_dd6_file' :  ''.join([file_work_path, file_tmp_name, '_speedup_dd6.',param_data['before_file']['audiotype']]),
                         'audio_com_file' : ''.join([file_work_path, file_tmp_name, '_audio.mp4']),
                         'mp4_output_uncut_file' : ''.join([file_work_path, file_tmp_name, '_uncut.mp4']),
                         'ts_output_uncut_file' : ''.join([file_work_path, file_tmp_name, '_uncut.ts']),
                         'ts_output_uncut_ff_file' : ''.join([file_work_path, file_tmp_name, '_uncut_ff.ts'])
    }
    
    avs_file_name = file_work_path + file_tmp_name + '_hd_to_4k.avs'
    bat_file_name = file_work_path + file_tmp_name + '_hd_to_4k.bat'
    
    #load the control file template,set the parameter
    template_env = jinja2.Environment(loader = jinja2.FileSystemLoader(conf_dic['all']['config_path']+'\\templates'))
    
    avs_file_tmp_param = {'h264_file_name':h264_file ,'add_h264_sub_file':sub_speedup_file}
    avs_file_tmp_param.update(conf_dic['avs_tool'])
    avs_file_tmp_param.update(param_data['filters']['hd_to_4k']['hd_to_4k_avs'])
    avs_file_tmp = template_env.get_template('hd_to_4k_avs_template.avs').render(avs_file_tmp_param)
    
    bat_file_tmp_param = {'h264_file_name':h264_file ,'hd_to_4k_avs_file':avs_file_name ,'hevc_output_file':hevc_file}
    bat_file_tmp_param.update(conf_dic['4k_tool'])
    bat_file_tmp_param.update(combination_param)
    bat_file_tmp_param.update(param_data['filters']['hd_to_4k']['demux'])
    bat_file_tmp_param.update(param_data['filters']['hd_to_4k']['hd_to_4k_bat'])
    bat_file_tmp = template_env.get_template('hd_to_4k_bat_template.bat').render(bat_file_tmp_param)
    
    #write the new control file
    if (os.path.exists(file_work_basepath)== False):    
        os.mkdir(file_work_basepath)
    lines = "\r\n".join(avs_file_tmp.split('\n'))
    avs_file = open( avs_file_name,'w+')
    avs_file.writelines(lines)
    avs_file.close()
    
    lines = "\r\n".join(bat_file_tmp.split('\n'))
    bat_file = open(bat_file_name,'w+')
    bat_file.writelines(lines)
    bat_file.close()
    
    #download file and process and upload result
    hd_to_4k_downloader(param_data, file_tmp_name)
    process2 = subprocess.Popen(bat_file_name, shell=True, stdout = subprocess.PIPE, stderr=subprocess.STDOUT,universal_newlines= True)       
    while True:
        line = process2.stdout.readline()
        print line
        if not line:        
            break
    hd_to_4k_uploader(param_data,''.join([ param_data['before_file']['fileid'],'\\',file_tmp_name, '_uncut.mp4']),"_4k")
    hd_to_4k_uploader(param_data,''.join([ param_data['before_file']['fileid'],'\\',file_tmp_name, '_uncut_ff.ts']),"_4k")
    
# if __name__=='__main__':
#     hd_to_4k(param_data)    
