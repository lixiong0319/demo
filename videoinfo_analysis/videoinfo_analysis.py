from datetime import datetime
import hashlib
import json
import os,re
import subprocess
import sys
import time
from collections import Counter
from multiprocessing import Pool
import csv
import numpy as np
import xlwt
import multiprocessing
import platform

if platform.system() == "Windows":
    ffmpegEXE = r"ffmpeg.exe"
    ffprobeEXE = r"ffprobe.exe"
else:
    ffmpegEXE = r"ffmpeg"
    ffprobeEXE = r"ffprobe"

video_formats = ['.mp4','.flv','.avi','.mov','.mkv','.ts','.obu','.hevc','.h264','.265']

#Get performance decorator
def timer_decorator(func):
    def wrapper(*args,**kwargs):
        start_time_test = time.time()
        result = func(*args,**kwargs)
        end_time_test = time.time()
        print(f"Function {func.__name__} took {end_time_test - start_time_test:.2f} seconds to execute.")
        return result 
    return wrapper 


#Get I frame
def get_Iframe(key_frame,pict_type,nums,file_path,get_all_data):
    keyframe_count = 0
    for i in key_frame:
        if i == "1":
            keyframe_count += 1

    pict_type_I_count = 0
    for j in pict_type:
        if j == "I":
            pict_type_I_count += 1
    
    if keyframe_count != pict_type_I_count:
        print("keyframe count is not equal to pict_type I count!\n")

    Save_Keyframe = []  #Save Keyframe List
    frame_number = 0  #Record the position of frame I in pict_type

    for i in key_frame:
        if i == "1":
           Save_Keyframe.append(frame_number)
        frame_number += 1

    keyframe_intervals = []
    for i in range(0, len(Save_Keyframe)-1):
        diff = int(Save_Keyframe[i + 1]) - int(Save_Keyframe[i])
        keyframe_intervals.append(diff)

    if len(Save_Keyframe) == 1:
        keyframe_intervals.append(len(key_frame))
    
    if keyframe_intervals == []:
        max_keyframe_interval = 0
        min_keyframe_interval = 0
        counts_keyframe_interval = 0
    else:   
        max_keyframe_interval = max(keyframe_intervals)
        min_keyframe_interval = min(keyframe_intervals)
        counts_keyframe_interval = Counter(keyframe_intervals)

    get_all_data.update({
        0:nums,
        1:file_path,
        5:len(key_frame),
        6:max_keyframe_interval,
        7:min_keyframe_interval,
        8:max(counts_keyframe_interval.keys(), key=counts_keyframe_interval.get),
        9:len(Save_Keyframe),
        10:pict_type_I_count
    })
    return get_all_data
    

def get_Pframe(pict_type,get_all_data):
    P_num = 0
    for i in pict_type:
        if i == "P":
            P_num += 1

    get_all_data.update({15:P_num})
    return get_all_data

#Get Bframe
def get_Bframe(B_pict_type,get_all_data):
    #print(pict_type)
    BframeNum = []    #Save Bframe List
    continuous_bframes = 0
    bframes_count = 0
    # Get BframeNum
    for b in B_pict_type:
        if b == 'B':
            continuous_bframes += 1
            bframes_count += 1   #Record the number of B frames
        else:
            if continuous_bframes != 0:
                BframeNum.append(continuous_bframes)
            continuous_bframes = 0
    if BframeNum == []:
        print("Bframe is not exist!\n")
        score = 0
        get_all_data.update({
            11:score,
            12:score,
            13:score,
            14:score
        })
    else:
        counts = Counter(BframeNum)
        high_frequency_count = max(counts.keys(), key=counts.get)
        counts = str(counts)
        get_all_data.update({
            11:max(BframeNum),
            12:high_frequency_count,
            13:bframes_count,
            14:counts
        })
    return get_all_data


#Get resolution and average bit rate
def get_video_baseInfo(input_file,file_path,base_filename,get_all_data):
    Savedata=[]
    get_video_dict = {}
    data_path = file_path + "/" + base_filename + "_data.info"
    if os.path.exists(data_path) == True:
        os.remove(data_path)
    cmd = ffprobeEXE + " -hide_banner -show_streams -select_streams v " + input_file + " > " + data_path
    os.system(cmd)
    with open(data_path) as files:
        text = files.readlines()

    for i in text:
        if i[0:5] == "width" or i[0:6] == "height" or i[0:5] == "level" or i[0:8] == "bit_rate" or i[0:7] == "profile":
            Savedata.append(i)

    profile = Savedata[0][8:].replace('\n', '')
    width = Savedata[1][6:].replace('\n', '')
    height = Savedata[2][7:].replace('\n', '')
    level = float(Savedata[3][6:].replace('\n',''))
    bit_rate = Savedata[4][9:].replace('\n', '')
    if bit_rate == "N/A":
        cmd = ffprobeEXE + " -hide_banner -v error -show_entries format=bit_rate -of default=noprint_wrappers=1:nokey=1 " + input_file + " > " + data_path
        os.system(cmd)
        with open(data_path) as files:
            video_bitrate_only = files.readlines()
            try:
                video_bitrate_new = float(video_bitrate_only[0].replace('\n',''))/1000.0
            except ValueError:
                video_bitrate_new = video_bitrate_only[0]
            bit_rate = video_bitrate_new
        get_all_data.update({4:video_bitrate_new})
    else:
        average_bit_rate = float(bit_rate)/ 1000.0
        get_all_data.update({4:average_bit_rate})

    resolution = width + 'x' + height
    if level >= 63:
        level = level / 30
    elif level >= 10:
        level = level / 10

    get_all_data.update({
        2:resolution,
        20:level,
        21:profile
    })
    if os.path.exists(data_path) == True:
        os.remove(data_path)
        
    return [bit_rate,get_all_data]

def get_md5_value(file_basedir):
    with open(file_basedir, 'rb') as fd:
        data = fd.read()
    return hashlib.md5(data).hexdigest()

def get_no_duplicate(file_path):
    save_md5 = []
    duplicate_md5 = []
    no_duplicate = []
    all_video = []
    for root, ds, fs in os.walk(file_path):
        # Only files in the current folder are processed, and subfolders are not recursively entered
        if root == file_path:
            for f in fs:
                file_basedir = file_path + "/" + f
                #print(file_basedir)
                fdata = ("." + f.split(".")[-1])
                if fdata.lower() in video_formats:
                    all_video.append(f)
                    md5_value = get_md5_value(file_basedir)
                    if md5_value not in save_md5:
                        save_md5.append(md5_value)
                        no_duplicate.append(f)
                    else:
                        duplicate_md5.append(f)

    save_list = [all_video, no_duplicate, duplicate_md5]   
    return save_list

def get_frame_info(video_path):
    ffprobe_cmd = ffprobeEXE + f' -hide_banner -select_streams v:0 -show_frames -select_streams v -of json -show_entries frame=pkt_size,pict_type,pkt_pos,key_frame "{video_path}"'
    result = subprocess.check_output(
        ffprobe_cmd, shell=True, text=True, stderr=subprocess.PIPE)
    frame_info = json.loads(result)
    return frame_info['frames']

def get_packet_info(video_path):
    ffprobe_cmd = ffprobeEXE + f' -hide_banner -select_streams v:0 -show_packets -select_streams v -of json -show_entries packet=size,pos,pts,dts "{video_path}"'
    result = subprocess.check_output(
        ffprobe_cmd, shell=True, text=True, stderr=subprocess.PIPE)
    packet_info = json.loads(result)
    return packet_info['packets']

def process_frame_type(frame_list, packet_list):
    frames = len(frame_list)

    if frames <= 1:
        return

    have_p_frame = False
    current_p_interval = 0
    max_p_interval = 0

    for frame in frame_list[:min(128, frames)]:
        if frame['pict_type'] == 'P':
            have_p_frame = True
            current_p_interval = 0
        else:
            current_p_interval += 1
        if current_p_interval > max_p_interval:
            max_p_interval = current_p_interval

    if have_p_frame == False or max_p_interval > 31:
        b_to_p_positions = set()
        last_pframe_pts = int(packet_list[0]['pts'])
        for pkt_idx in range(1, len(packet_list)):
            if (int(packet_list[pkt_idx]['pts']) > last_pframe_pts):
                last_pframe_pts = int(packet_list[pkt_idx]['pts'])
                b_to_p_positions.add(packet_list[pkt_idx]['pos'])
        pos_to_frame = {frame['pkt_pos']: frame for frame in frame_list}
        for pos in b_to_p_positions:
            if pos in pos_to_frame:
                frame = pos_to_frame[pos]
                if frame['pict_type'] == 'B':
                    frame['pict_type'] = 'P'

#Get video data
#file_path,no_duplicate_video,worksheet,workbook
def get_data(video_all_info):
    get_all_data = dict()
    this_file, file_path, worksheet, workbook, excel_name, nums = video_all_info
    input_file = file_path + "/" + this_file
    (base_filename,extension) = os.path.splitext(this_file)

    if (extension.lower() in video_formats):
        log_file = file_path + "/" + base_filename + ".info"
        if os.path.isfile(log_file) == False:
            commands = ffprobeEXE + " -hide_banner -show_frames -select_streams v -of xml " + input_file + " > " + log_file
            os.system(commands)
        else:
            print(log_file + " already exists! \n")

        key_frame = []
        pict_type = []
        get_all_data = add_useLR_function(input_file,file_path,base_filename,get_all_data)

        bmq = get_all_data[23]

        if bmq == 265:
            frame_info_list = get_frame_info(input_file)
            packet_info_list = get_packet_info(input_file)
            process_frame_type(frame_info_list, packet_info_list)
            for process_frame in frame_info_list:
                key_frame.append(str(process_frame['key_frame']))
                pict_type.append(process_frame['pict_type'])
            
        else:         
            with open(log_file) as files:
                text = files.readlines()
            
            for i in text:
                if "stream_index" in i:
                    getkey_frame = re.findall('<.*?key_frame="(.*?)" ', i, re.S)
                    getpict_type = re.findall('<.*?pict_type="(.*?)" ', i, re.S)
                    key_frame.append(getkey_frame[0])
                    pict_type.append(getpict_type[0])

        get_all_data = get_Iframe(key_frame,pict_type,nums,this_file,get_all_data)
        B_pict_type = pict_type + ['x'] #Virtual frames are added at the end to determine the end of gop     
        get_all_data = get_Bframe(B_pict_type,get_all_data)
        get_all_data = get_Pframe(pict_type,get_all_data)
        video_bitrate_all = get_video_baseInfo(input_file,file_path,base_filename,get_all_data)
        video_bitrate = video_bitrate_all[0]
        get_all_data = video_bitrate_all[1]
        get_all_data = clacBitrateFlactuation(input_file,video_bitrate,base_filename,get_all_data,level=1)
        #get_all_data = add_useLR_function(input_file,file_path,base_filename,get_all_data)     
        os.remove(log_file)

        nums += 1
        return get_all_data

    else:
        print(input_file + " is not valid! \n")

def writer_excel(file_path,no_duplicate_video):
    excel_name = get_datetime() + '_Getdata.xls'
    # creat excel and write to data
    workbook = xlwt.Workbook(encoding="utf-8")
    worksheet = workbook.add_sheet("Data")
    worksheet.write(0, 0, label='序号')
    worksheet.write(0, 1, label='文件名')
    worksheet.write(0, 2, label='分辨率')
    worksheet.write(0, 3, label='视频帧率')
    worksheet.write(0, 4, label='视频平均码率kbps')
    worksheet.write(0, 5, label='视频总帧数')
    worksheet.write(0, 6, label='最长关键帧间隔')
    worksheet.write(0, 7, label='最短关键帧间隔')
    worksheet.write(0, 8, label='最多出现关键帧间隔')
    worksheet.write(0, 9, label='关键帧总数')
    worksheet.write(0, 10, label='I帧总数')
    worksheet.write(0, 11, label='最长连续B帧数')
    worksheet.write(0, 12, label='最常用的连续B帧数')
    worksheet.write(0, 13, label='B帧总数')
    worksheet.write(0, 14, label='连续B帧数分布')
    worksheet.write(0, 15, label='P帧总数')
    worksheet.write(0, 16, label='单位时间内峰值码率kbps')
    worksheet.write(0, 17, label='出现峰值码率的时间s')   
    worksheet.write(0, 18, label='单位时间内谷值码率kbps')
    worksheet.write(0, 19, label='是否为动态帧率')
    worksheet.write(0, 20, label='Level')
    worksheet.write(0, 21, label='Profile')
    worksheet.write(0, 22, label='是否存在长期参考帧')
    worksheet.write(0, 23, label='编码器')
    #workbook.save(file_path + "/" + excel_name)
    # Todo: 
    # 1. calculate bitrate flaction for variable framerate input
    # 2. support get right bframes for hevc bitstreames when general-b is open
    # 3. support get right video information for AV1 bistreames

    # Use multiple processes for video processing 
    num_processes = 8  # Set the number of processes according to the performance of your machine
    num_cores = os.cpu_count() #The number of CPU cores on the local computer
    if num_cores <= num_processes:
        num_processes = num_cores

    file_list = [file_num for file_num in range(1,len(no_duplicate_video)+1)]
    tasks = [(this_file, file_path, worksheet, workbook, excel_name) for this_file in no_duplicate_video]
    new_tasks = [(t[0],t[1],t[2],t[3],t[4],np) for t, np in zip(tasks,file_list)]
    results = process_videos_with_multiprocessing(num_processes,new_tasks)
    result_num = 1
    for result in results:       
        sorted_keys = sorted(result)
        for key in sorted_keys:
            #print(key,result[key])
            worksheet.write(result_num, key, result[key])
        result_num += 1
    workbook.save(file_path + "/" + excel_name)

def process_videos_with_multiprocessing(num_processes,new_tasks):  
    with multiprocessing.Pool(processes=num_processes) as pool:  
        # Use the map method to process the video list and return the resulting list 
        results_end = pool.map(get_data, new_tasks)  
    return results_end  
    
@timer_decorator
def run(file_path):
    no_duplicate_video = get_no_duplicate(file_path)[0]
    writer_excel(file_path,no_duplicate_video)

@timer_decorator
def run1(file_path):
    no_duplicate_video = get_no_duplicate(file_path)[1] 
    writer_excel(file_path,no_duplicate_video)

@timer_decorator
def only_file(file_path):   
    file_name = os.path.basename(file_path)
    directory_path = os.path.dirname(file_path)
    file_list = [file_name]
    writer_excel(directory_path,file_list)

#Get data through multiple processes
def main(file_path):
    file_all = os.listdir(file_path)
    print(file_all)
    with Pool(processes=4) as pool:
        tasks = [(video_file,file_path) for video_file in file_all]
        print(tasks)
        pool.map(run,tasks)

def isplit_by_n(ls, n):
    for i in range(0, len(ls), n):
        yield ls[i:i + n]

def split_by_n(ls, n):
    return list(isplit_by_n(ls, n))

def getYuvFilesList(yuvlist):
    yuvfileslist = []
    for item in yuvlist:
        if os.path.isdir(item):
            for ifile in os.listdir(item):
                yuvfileslist.append(os.path.join(item, ifile))
        elif os.path.isfile(item):
            yuvfileslist.append(item)
        else:
            continue
    return yuvfileslist

#Get the maximum bit rate per unit time
def get_frame_time(text):
    all_size = []
    all_time = []
    # Get pkt_size and pkt_pts_time
    for line in text:
        if "size=" in line and len(line) < 20:
            all_size.append(int(line[5:]))
        elif "pts_time" in line:
            if "N/A" not in line:
                all_time.append(float(line[9:]))

    # Generate a dict for pkt_size and pts_time
    data_dict = dict(zip(all_time, all_size))

    if not data_dict:
        print("Couldn't get pts info!!!")
        return None

    max_time = int(max(all_time))
    all_data = []
    frame_rate = []

    # Calculate whole frame count and size per time step
    step_length = 1
    arrange_list = sorted(data_dict.keys())

    for i in range(0, max_time + 1, step_length):
        total_size = sum(data_dict[j] for j in arrange_list if i <= j < i + step_length)
        num_frames = len([j for j in arrange_list if i <= j < i + step_length])

        if num_frames > 0:
            all_data.append(total_size)
            frame_rate.append(num_frames)

    #Get the maximum peak code rate from data * 8
    all_data = [(x * 8) for x in all_data]
    always_frame = frame_rate[1] if len(frame_rate) > 1 else 0

    #To determine whether the last frame is a full second or not, if it is not, it will be excluded in the dynamic frame rate calculation.
    if frame_rate[-1] == always_frame:
        is_dtrate_list = frame_rate
    else:
        is_dtrate_list = frame_rate[:-1]

    get_data = "no" if all(frame == always_frame for frame in is_dtrate_list) else "yes"
    
    
    time_maximum_rate = max(all_data)
    time_miniumu_rate = min(all_data)
    maxiumn_data = int(time_maximum_rate) / 1000
    miniumn_data = int(time_miniumu_rate)/1000

    maximu_rate_time = 0
    for m in all_data:
        maximu_rate_time += 1
        if m == time_maximum_rate:
            break        

    save_data = [maxiumn_data, maximu_rate_time, miniumn_data, get_data ]
    return save_data

#Determines whether to use a long-term reference frame
def add_useLR_function(input_file,file_path,base_filename,get_all_data):
    save_paths = file_path + "/" + base_filename + "_nals_test.log"

    cmd = ffmpegEXE + ' -hide_banner -i {video_path} -c copy -bsf:v trace_headers -f null - >{save_path} 2>&1'.format(video_path=input_file,save_path=save_paths)
    os.system(cmd)
    #Handle bytecode exceptions
    time.sleep(2)

    try:
        logfile = open(save_paths,encoding="utf-8")
    except:
        logfile = open(save_paths,encoding="gbk")

    logcont = logfile.readlines()

    logfile.close()

    sum = 0
    save_num = []
    video_type = 0
    for i in logcont:
        if 'long_term_reference_flag' in i:
            video_type = 264
            #data = re.findall("long_term_reference_flag(.*?)",str(i),re.S)
            sum += 1
            save_num.append(int(i[-6]))
            save_num.append(int(i[-2]))
        
        elif 'long_term_ref_pics_present_flag' in i:
            video_type = 265
            sum += 1
            save_num.append(int(i[-6]))
            save_num.append(int(i[-2]))

    if video_type == 0:
        cmd = ffprobeEXE + " -hide_banner -v error -show_streams -print_format json " + input_file + " > " + save_paths
        os.system(cmd)
        with open(save_paths) as files:
            bmq_test = files.readlines()
            for bmq in bmq_test:
                if "codec_name" in bmq:
                    codec_last_name = re.findall('codec_name.*?: "(.*?)"',bmq,re.S)
                    video_type = codec_last_name[0]
                    break

    useLR = 0
    for i in save_num:
        if i == 0:
            useLR = 0
        else:
            useLR = 1
            break
    
    get_all_data.update({
        22:useLR,
        23:video_type
    })
    os.remove(save_paths)
    return get_all_data
    

# now,only support ippp cfr
# level = 0 ,Calculate the variance of bits per frame               计算每帧位的方差
# level > 0 ,Calculate the variance of bits per 'level' seconds     计算每“级”秒的比特方差
def clacBitrateFlactuation(dir,video_bitrate,base_filename,get_all_data,level=1):
    file = dir
    cmd = '{ffprobe_path} -hide_banner -v error -select_streams v -show_entries stream=r_frame_rate -of json {video_path}'.format(
        ffprobe_path=ffprobeEXE,
        video_path=file)
    value = subprocess.check_output(cmd, shell=True)
    data = json.loads(value)
    frameRate = eval(data.get('streams')[0].get('r_frame_rate'))
    cmd = ffprobeEXE + " -hide_banner -show_packets -select_streams v " + file + " > " + base_filename + "_frameSize.dat 2>&1 "
    os.system(cmd)
    #Handle bytecode exceptions
    try:
        logfile = open(base_filename + "_frameSize.dat",encoding="utf-8")
    except:
        logfile = open(base_filename + "_frameSize.dat",encoding="gbk")
    logcont = logfile.readlines()
    time_maximum_rates = get_frame_time(logcont)
    if video_bitrate == "N/A" or time_maximum_rates is None:
        get_all_data.update({
            16: "null",
            17: "null",
            18: "null",
            19: "null"
        })
    else:
        if isinstance(time_maximum_rates, list) and len(time_maximum_rates) >= 4:
            get_all_data.update({
                16: time_maximum_rates[0],
                17: time_maximum_rates[1],
                18: time_maximum_rates[2],
                19: time_maximum_rates[3]
            })
        else:
            print("The length of time_maximum_rates is insufficient or it is not a list.")
        
    logfile.close()
    
    frameBitsList = re.findall(r"size=\s*(\d*)\s*", str(logcont), re.S)
    frameBitsList = list(map(int, frameBitsList))

    #The old version of peak bitrate had some problems.
    
    # if level == 0:
    #     frameBitsVar = np.std(frameBitsList) / np.average(frameBitsList)
    # else:
    #     groupSize = frameRate * level
    #     groupSize = int(groupSize)
    #     secBitsList = split_by_n(frameBitsList, groupSize)
    #     secBitsList = [(np.sum(x) * 8) for x in secBitsList]
    #     max_num = 0
    #     get_num = 0
    #     time = []
    #     for i in secBitsList:
    #         if i > max_num:
    #             max_num = i
    #             time.append(get_num)
    #         get_num += 1

    #     secBitsVar = np.max(secBitsList)
    #     secBitsVar = float(secBitsVar) / 1000
    #     get_all_data.update({15:secBitsVar})
    #     get_all_data.update({16:time[-1]})
    get_all_data.update({3:frameRate})
    os.remove(base_filename + "_frameSize.dat")
    return get_all_data

def get_datetime():
    # Gets the current date and time 
    now = datetime.now()     
    # Format date and time as strings
    formatted_datetime = now.strftime("%Y%m%d%H%M%S")     
    return formatted_datetime

def dupicate_video(file_path,md5_video):
    dupicate_video_name = "dupicate_video.info"
    file_path_with_name = os.path.join(file_path,dupicate_video_name)
    if os.path.isfile(file_path_with_name):
        os.remove(file_path_with_name)
    with open(file_path_with_name,"a") as f:
        for video in md5_video:
            f.write(video + "\n")

if __name__ == "__main__":
    print(sys.argv)
    if len(sys.argv) < 2:
        print("please enter dir")
        exit()
    elif len(sys.argv) < 3:
        file_path = str(sys.argv[1])
        if os.path.isdir(file_path) == True:
            run(file_path)
        elif os.path.isfile(file_path) == True:
            print("This is a file!!!")
            only_file(file_path)
    elif str(sys.argv[2]) == "-q":
            file_path = str(sys.argv[1])
            run1(file_path)
            md5_video = get_no_duplicate(file_path)[2]
            dupicate_video(file_path,md5_video)





