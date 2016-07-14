"""HevcTranscode URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import include, url
from django.contrib import admin

urlpatterns = [
    url(r'^$', 'H264ToHevc.views.transcodePage', name='transcodePage'), 
    url(r'^transcode$', 'H264ToHevc.views.transcodePage', name='transcodePage'), 
    url(r'^filelist$', 'H264ToHevc.views.filelistPage', name='filelistPage'), 
#     user Proc
    url(r'^user$', 'H264ToHevc.views.userProc', name='userProc'),
    url(r'^user/authcode/([a-zA-Z0-9]{32})$', 'H264ToHevc.views.userAuthProc', name='userProc'),
    url(r'^user/Registration$', 'H264ToHevc.views.userRegistrationProc', name='userRegistrationProc'),
#     file Proc
    url(r'^mediafile$', 'H264ToHevc.views.mediaFileProc', name='mediaFileProc'),
    url(r'^mediafile/fileid/([a-zA-Z0-9]{32})/authcode/([a-zA-Z0-9]{32})$', 'H264ToHevc.views.mediaFileByIdProc', name='mediaFileByIdProc'),
    url(r'^mediafile/info/fileid/([a-zA-Z0-9]{32})$', 'H264ToHevc.views.mediaFileInfoByIdProc', name='mediaFileInfoByIdProc'),    
    url(r'^mediafile/info/authcode/([a-zA-Z0-9]{32})$', 'H264ToHevc.views.mediaFileInfoByAuthProc', name='mediaFileInfoByAuthProc'),
    
    url(r'^ftpmediafilename/authcode/([a-zA-Z0-9]{32})$', 'H264ToHevc.views.ftpMediaFileName', name='ftpMediaFileName'),
    url(r'^ftpmediafile$', 'H264ToHevc.views.ftpMediaFileProc', name='ftpMediaFileProc'),
    url(r'^ftpmediafile/fileid/([a-zA-Z0-9]{32})/authcode/([a-zA-Z0-9]{32})$', 'H264ToHevc.views.ftpMediaFileByIdProc', name='ftpMediaFileByIdProc'),
    
    url(r'^TCT_CREATE$', 'H264ToHevc.views.tctcreate', name='TCT_CREATEProc'), 
    
    url(r'^h264tohevc$', 'H264ToHevc.views.H264toHevcProc', name='H264toHevcProc'), 
    url(r'^h264tohevc/allinfo/authcode/([a-zA-Z0-9]{32})$', 'H264ToHevc.views.H264toHevcInfoByAuthProc', name='H264toHevcInfoByAuthProc'),
    url(r'^h264tohevc/info/taskid/([a-zA-Z0-9]{32})$', 'H264ToHevc.views.H264toHevcInfoProc', name='H264toHevcInfoProc'),
    
    url(r'^mediafile/imagerec$', 'H264ToHevc.views.mediaFileImagerecProc', name='mediaFileImagerecProc'),
    url(r'^imagerecstate/([a-zA-Z0-9]{32})$', 'H264ToHevc.views.getImageRec', name='getImageRec'),
]
