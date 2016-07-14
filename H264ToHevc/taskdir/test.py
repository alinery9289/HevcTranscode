import tasks

param_data = {
                'taskid' : 'fdcec6a198ce11e588fa90b11c94ab4d', 
                'before_file':{
                    'fileid':'fd56895e98ce11e596d890b11c94ab4d',
                    'authcode':'38a43f8070e811e5ad0c90b11c94ab4d',
                    'filetype':'m2ts',
                    'audiotype':'ac3'
                },
                'filters':{
                    'hd_to_4k':{
                        'demux':{'audio_num':'1','sub_num':'2','after_sub':'25'},
                        'hd_to_4k_avs':{'resolution':'3840,2160'},
                        'hd_to_4k_bat':{'preset':'slower','keyint':'50' , 'scenecut':'50','bitrate':'15000'},
                    }
                    
                }
            }

tasks.hd_to_4k.delay(param_data)
print "do the task"