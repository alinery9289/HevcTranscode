var nowprocessing_taskid ="";
$(window).load(function() {
	authcode= getCookie("authcode");
	refreshProcesslog(authcode);
	refreshFilelist(authcode);
});
var unprocessed_filename=""
function refreshFilelist(authcode){
	$.ajax({
        type : "GET",  
        url : "/ftpmediafilename/authcode/"+authcode,
        dataType: "json",  
        success : function(data) { 
        	htmlvalue='';
        	var list = [];
        	htmlvalue += '<p style="float: left;top: 4px;margin-top: 6px;margin-right: 3px;">Please select the file in your ftp server:</p>'
            htmlvalue += '<select class="dropdown"> '
            list = data.fileList;
        	if (list==""){htmlvalue += '<option value="">Don\'t have any file</option>';}
        	else {
        		$.each(list,function(idx,item){ 
                    var fileid_value=item;
                    var filename_value=item; 
                    htmlvalue += '<option value="'+fileid_value+'">'+filename_value+'</option>';
                    if (idx == 0 ){unprocessed_filename= fileid_value;}
            	});
        	} 
            htmlvalue += '</select>';
        	document.getElementById("ftpfileselect").innerHTML= htmlvalue;
        	
        	var $selects = $('#ftpfileselect select');
			
    		$selects.easyDropDown({
    			cutOff: 8,
    			wrapperClass: 'dropdown',
    			onChange: function(selected){
    	        	unprocessed_filename= selected.value;
    			}
    		});  	
        },
		error :  function() {   
        }
	});	
}

function refreshProcesslog(authcode){
	$.ajax({
        type : "GET",  
        url : "/h264tohevc/allinfo/authcode/"+authcode,
        dataType: "json",  
        success : function(data) { 
        	htmlvalue='';
        	firstfileid='';
        	if (data==''){
        		
        		//getTrancodetestLog(authcode,fileid);
        	}
        	else {
        		htmlvalue += '<p style="float: left;top: 4px;margin-top: 6px;margin-right: 3px;">Select one processing file :</p>'
            	htmlvalue += '<select class="dropdown"> '
            	$.each(data,function(idx,item){ 
                	var taskid_value=item.taskid;
                	var filename_value=item.filename; 
                	htmlvalue += '<option value="'+taskid_value+'">'+filename_value+'</option>';
        	    });
            	htmlvalue += '</select>';
        	}
        	document.getElementById("processlogselect").innerHTML=htmlvalue;
        	var $selects = $('#processlogselect select');
			
    		$selects.easyDropDown({
    			cutOff: 8,
    			wrapperClass: 'dropdown',
    			onChange: function(selected){
    	        	nowprocessing_taskid= selected.value;
    				getTrancodetestLog(selected.value);
    			}
    		});

        	
        },
		error :  function() {  
           //do something 
        }
	});	
}
function transcode_begin(){
	var authcode = getCookie("authcode");

	var json_obj = {
        before_file:{
        	filename: unprocessed_filename,
        	authcode: authcode
        },
        filters:{
            ffmpeg:{
                hevc_param:{preset:$("#preset").val(), keyframemin:$("#keyframemin").val(),keyframemax: $("#keyframemax").val(), vbvbuffersize:$("#vbvbuffersize").val(), bitrate:$("#bitrate").val()},
            }      
        }
    }
	var json_str = JSON.stringify(json_obj);
	document.getElementById("processlogp").innerHTML="Submiting";
	$.ajax({
        type : "POST",  
        url : "/h264tohevc",
        data:{filterparam:json_str},
        dataType: "text",  
        success : function(taskid) { 
        	if (taskid=="Error"){
        		document.getElementById("processlogp").innerHTML="Move File Error!";
        		return ;
        	}
        	refreshProcesslog(authcode);
        	refreshFilelist(authcode);
        	nowprocessing_taskid= taskid;
        	getTrancodetestLog(taskid);
        },
		error :  function() {  
           //do something 
        }
	});	
}

var transcodetest_timer;
function getTrancodetestLog(taskid){
	$.ajax({
        type : "GET",  
        url : "/h264tohevc/info/taskid/"+taskid,
        dataType: "text",  
        success : function(data) {      	
    		if ( nowprocessing_taskid!=taskid){
        		clearTimeout(transcodetest_timer);
        		transcodetest_timer=setTimeout("getTrancodetestLog('" +nowprocessing_taskid+"')",3000);
    		}
    		else{
    			document.getElementById("processlogp").innerHTML=""
    	        	var trancode_state=[];
    	    		trancode_state=data.split("\n");
    	    		for (var i=0;i<trancode_state.length;i++){
    	    			$('#processlogp').append($('<li>').text(trancode_state[i]));
    	    		}
    			if (data.substring(data.length-3)!="..." ){
            		clearTimeout(transcodetest_timer);
            	}
            	else {
            		transcodetest_timer=setTimeout("getTrancodetestLog('"+ taskid+"')",3000);
            	}
    		}
    		
        },
		error :  function() {  
        }
   });
}