import tasks

param_data = {
                'taskid' : 'f92a30b0df8e11e59e1214187749d0b1', 
                'before_file':{
                    'fileid':'50322fdee05011e5b87914187749d0b1',
                    'authcode':'38a43f8070e811e5ad0c90b11c94ab4d',
                    'filetype':'m2ts',
                    'audiotype':'ac3'
                },
                'filters':{
                    'hd_to_4k':{
                        'demux':{'audio_num':'1','sub_num':'1','after_sub':'25'},
                        'hd_to_4k_avs':{'resolution':'3840,2160'},
                        'hd_to_4k_bat':{'preset':'slow','keyint':'50' , 'scenecut':'50','bitrate':'15000'},
                    }
                    
                }
            }

param_data1 = {
                'taskid' : 'f92a30b0df8e11e59e1214187749d0b1', 
                'before_file':{
                    'fileid':'d7718840be9311e5982490b11c94ab4d',
                    'location':'ftp://user/upload/1.mp4',
                    'authcode':'38a43f8070e811e5ad0c90b11c94ab4d',
                    'filetype':'m2ts'
                },
                'filters':{
                    'ffmpeg':{
                        'hevc_param':{'keyfraemin':'50','keyframemax':'50','vbvmaxbitrate':'30000' , 'vbvbuffersize':'15000','bitrate':'15000'},
                    }
                    
                },
               'after_file':{
                    'out_path' : 'ftp://user/upload/1_265.mp4',
                }
            }

# tasks.hd_to_4k(param_data)
# tasks.ffmpeg_transcode(param_data1)
print "do the transcode task"