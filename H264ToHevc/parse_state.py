import re
from collections import OrderedDict
import copy
import redistool

dic = OrderedDict()
prev_dic = OrderedDict()
process_step = "unprocessed"

def add_state_to_redis(taskid, line):
	# pdb.set_trace()
	global process_step  
	global prev_dic
	global dic
	# state line
	if line=='demux_audio\n':
		dic['demux_audio'] = 'Extracting Audio...'
		process_step = 'demux_audio'
	elif line == 'demux_sub\n':
		dic['demux_sub'] = 'Extracting Subtitles...'
		process_step = 'demux_sub'
	elif line == 'h264_to_hevc\n':
		dic['h264_to_hevc'] = 'Running h264_to_hevc...'
		process_step = 'h264_to_hevc'
	elif line == 'audio_speedup\n':
		dic['audio_speedup'] = 'Audio speeding up...'
		process_step = 'audio_speedup'
	elif line == 'ac3_to_eac3\n':
		dic['ac3_to_eac3'] = 'Turning ac3 to eac3...'
		process_step = 'ac3_to_eac3'
	elif line == 'get_audio_file\n':
		dic['get_audio_file'] = 'Getting audio file...'
		process_step = 'get_audio_file'
	elif line == 'synthetic_mp4_file\n':
		dic['synthetic_mp4_file'] = 'Synthetic mp4 file...'
		process_step = 'synthetic_mp4_file'
	elif line == 'synthetic_buffer_ts_file\n':
		dic['synthetic_buffer_ts_file'] = 'Synthetic buffer ts file...'
		process_step = 'synthetic_buffer_ts_file'
	elif line == 'synthetic_ts_file\n':
		dic['synthetic_ts_file'] = 'Synthetic ts file...'
		process_step = 'synthetic_ts_file'
	elif line =='all_complete\n':
		dic['all_complete'] = 'all_complete! Please download file in file list!'
		process_step = 'all_complete'
	

	#get line content
	if process_step == 'demux_audio' or process_step == 'ac3_to_eac3' or process_step == 'get_audio_file' or process_step == 'synthetic_ts_file':
		global process_total_time
		
		reobj = re.compile(r'.*?Duration:.*?start.*?bitrate.*?')
		if reobj.match(line):
			head = line.find('Duration:')
			process_time_list = line[int(head)+10:int(head)+20].split(':')
			process_total_time = (float(process_time_list[0])*3600+float(process_time_list[1])*60+float(process_time_list[2]))

		reobj = re.compile(r'size.*?time.*?bitrate.*?')
		if reobj.match(line):	
			present = line.find('time')
			process_now_list = line[int(present)+5:int(present)+15].split(':')
			process_now_time = (float(process_now_list[0])*3600+float(process_now_list[1])*60+float(process_now_list[2]))
			dic[process_step] = 'Running '+process_step+' :' + str(line[:-1]) + ' schedule: %0.1f %% ...'% (float(process_now_time/process_total_time)*100)

	elif process_step == 'demux_sub':
		pass

	elif process_step == 'h264_to_hevc':
		reobj = re.compile(r".*?frames.*?fps.*?kb/s.*?eta.*?")
		if reobj.match(line):
			dic['h264_to_hevc'] = 'Running h264_to_hevc: %s...' %str(line[:-1])

	elif process_step == 'audio_speedup':
		pass

	elif process_step == 'synthetic_mp4_file':
		reobj = re.compile('Importing HEVC:.*?|Importing ISO File:.*?|ISO File Writing:.*?')
		if reobj.match(line):
			dic['synthetic_mp4_file'] = 'Synthetic mp4 file: %s...' %str(line[:-1])

	elif process_step == 'synthetic_buffer_ts_file':
		reobj = re.compile(r'Converting to MPEG-2 TS:.*?')
		if reobj.match(line):
			dic['synthetic_buffer_ts_file'] = 'Synthetic buffer ts file: %s...' %str(line[:-1])
			
	elif process_step == 'all_complete':
		pass
	if dic != prev_dic:
		redistool.redis_set('_'.join(["task","status",taskid]), "Copying file to workstation...\n" + '\n'.join(dic.values()))	
	prev_dic = copy.deepcopy(dic)

def add_ffmpeg_state_to_redis(taskid, line):	
	# pdb.set_trace()
	global process_step  
	global prev_dic
	global dic
	# state line
	if line =='all_complete\n':
		dic['all_complete'] = 'all_complete! Please download file in file list!'
		process_step = 'all_complete'
	

	#get line content
	if process_step == 'unprocessed':
		global process_total_time
		
		reobj = re.compile(r'.*?Duration:.*?start.*?bitrate.*?')
		if reobj.match(line):
			head = line.find('Duration:')
			process_time_list = line[int(head)+10:int(head)+20].split(':')
			process_total_time = (float(process_time_list[0])*3600+float(process_time_list[1])*60+float(process_time_list[2]))

		reobj = re.compile(r'.*?size.*?time.*?bitrate.*?')
		if reobj.match(line):	
			present = line.find('time')
			process_now_list = line[int(present)+5:int(present)+15].split(':')
			process_now_time = (float(process_now_list[0])*3600+float(process_now_list[1])*60+float(process_now_list[2]))
			dic[process_step] = 'Transcoding :' + str(line[:-1]) + ' schedule: %0.1f %% ...'% (float(process_now_time/process_total_time)*100)
			
	elif process_step == 'all_complete':
		pass
	if dic != prev_dic:
		redistool.redis_set('_'.join(["task","status",taskid]), "Copying file to workstation...\n" + '\n'.join(dic.values()))	
	prev_dic = copy.deepcopy(dic)
	