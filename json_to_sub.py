import json
import re
import requests
import time
import sys
from tqdm import tqdm
#import youdao cert, youdao need
from AuthV3Util import addAuthParams
#import google_cloud, google need
from google.cloud import translate
import os

def doCall(url, header, params, method):
    if 'get' == method:
        return requests.get(url, params)
    elif 'post' == method:
        return requests.post(url, params, header)
    
def youdao(tran_need):
    '''
    note: 将下列变量替换为需要请求的参数
    '''
    # 您的应用ID
    APP_KEY = '67639578ee8ac3dc'
    # 您的应用密钥
    APP_SECRET = '##'
    lang_from = 'auto'
    lang_to = 'zh-CHS'
    vocab_id = '###'
    domain = 'computers'

    data = {'q': tran_need, 'from': lang_from, 'to': lang_to, 'vocabId': vocab_id, 'domain':domain}

    addAuthParams(APP_KEY, APP_SECRET, data)

    header = {'Content-Type': 'application/x-www-form-urlencoded'}
    res = doCall('https://openapi.youdao.com/api', header, data, 'post')
    #print(str(res.content, 'utf-8'))
    data = json.loads(str(res.content, 'utf-8'))
    trans = data['translation']
    return trans[0]

def google(trans_need):
    cert_json = r"E:\google\translate-398408-9ad5ce643d16.json"
    os.environ['GOOGLE_APPLICATION_CREDENTIALS']=str(cert_json)

    project_id="translate-398408"
    client = translate.TranslationServiceClient()
    location = "global"
    parent = f"projects/{project_id}/locations/{location}"

    response = client.translate_text(
        request={
            "parent": parent,
            "contents": [trans_need],
            "mime_type": "text/plain",
            "source_language_code": "en-US",
            "target_language_code": "zh",
        }
    )

    for translation in response.translations:
        #print("Translated text: {}".format(translation.translated_text))
        return (format(translation.translated_text))

def time_switch(value):
    hours = int(value / 3600)
    minutes = int((value % 3600) / 60)
    seconds = int(value % 60)
    milliseconds = int((value % 1) * 1000)

    # 格式化为字符串
    formatted_time = '{:02d}:{:02d}:{:02d},{:03d}'.format(hours, minutes, seconds, milliseconds)

    return formatted_time


def text_split(input_file):
    with open(input_file, 'r') as file:
        json_content = file.read()
        data = json.loads(json_content)

    # 获取完整的文本值
    value = data["text"]
    text_list = []
    j = 1

    for i in re.split("(?<=\.|\?)\s", value):
        text_list.append(i)
        #print(str(j) + " " + i)
        j += 1

    # 获取句子的开始和结束位置
    start_list = []
    end_list = []

    # 获取段落
    seg_value = data["segments"]
    start_list.append(seg_value[0]["words"][0]["start"])
    j = 0

    for index_seg, value_seg in enumerate(seg_value):
        # 以.作为一句的分隔确定一句话的时间开始和结束
        word_list = value_seg["words"]
        pattern = r'\?|\.$'
        j += 1

        for index, value in enumerate(word_list):
            if re.findall(pattern, value["word"]):
                end_list.append(value["end"])
                try:
                    start_list.append(word_list[index+1]["start"])
                except IndexError:
                    if (index_seg+1) < len(seg_value):
                        if len(seg_value[index_seg+1]["words"]) > 0:
                            start_list.append(seg_value[index_seg+1]["words"][0]["start"])
                        else:
                            start_list.append(seg_value[index_seg+1]["end"])

    longest_sentence = max(text_list, key=len)
    #print(text_list)
    print(longest_sentence)
    print(f"识别结果：共有{str(len(text_list))}句话,{str(len(str(text_list)))}个字符,最长的一句话如上({len(longest_sentence)}个字符)")
    print(f"句子开头：{len(start_list)}个，句子结尾：{len(end_list)}个")
    for i, s in zip(start_list,end_list):
        if i>s:
            print("ERROR,字符断句出错，请检查")
            #print(i, s)
        #print(i,s)

    return start_list, end_list, text_list

def gen_srt(start_list, end_list, text_list, trans_tool, output_file):
    i = 1
    with open(output_file, mode='wt+', encoding='utf-8') as f:
        for item1, item2, item3 in tqdm(zip(start_list, end_list, text_list), desc='进度', ncols=80, total=len(text_list)):  
            print()      
            start_time = time_switch(item1)
            stop_time = time_switch(item2)
            raw_text = item3        
            line2 = (start_time+" --> "+stop_time)
            print(i)
            print(start_time, "-->", stop_time, "\n"+raw_text)
            line4=trans_tool(item3)
            print(line4)
            # if youdao, sleep 1 to prevent error(more requests)
            if (trans_tool.__name__) == "youdao":
                time.sleep(1)
            f.write(str(i)+"\n")
            f.write(line2+"\n")
            f.write(raw_text+"\n")
            f.write(line4+"\n"+"\n")
            i += 1
            print()

# input the json filename and the output filename
input_file = r"Y:\Video_whisper\Introduction_to_Commonly_Used_Commands.json"
output_file = r"Y:\Video_whisper\Introduction_to_Commonly_Used_Commands.srt"

# get time_start, time_end, text of each setence
start_list, end_list, text_list = text_split(input_file)

choice = input("请输入y或n继续:")
if choice == "y":
    # var3 is translate_tool(google or youdao)
    gen_srt(start_list, end_list, text_list, google, output_file)
elif choice == "n":
    print("中止")
    sys.exit()
else:
    print("无效输入")
    sys.exit()

print(f"字幕生成完成，路径为\"{output_file}\"")