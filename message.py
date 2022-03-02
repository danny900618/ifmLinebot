import configparser
from abc import ABC, abstractmethod
from re import A
from linebot import LineBotApi
from linebot.models import TemplateSendMessage,TextSendMessage, PostbackAction, MessageAction, URIAction, CarouselColumn, CarouselTemplate, PostbackTemplateAction, FlexSendMessage,ImageSendMessage
from pymongo import MongoClient
from pymongo import message
from pymongo.message import query

# config 環境設定解析
config = configparser.ConfigParser()
config.read("config.ini")

# mongoDB atlas 連線
myMongoClient = MongoClient(config['connect_config']['Mongodb_atlas_URL'])

# 保金系資料庫
myMongoDb2 = myMongoClient["insurance-data"]
dbUserRequest = myMongoDb2['user-request']
dbQuestion = myMongoDb2['qusetion-database']
dbInsurance = myMongoDb2['insurance-advice']
# 訊息抽象類別


class Message(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def content(self):
        pass

# 適合性分析


class Suitability_analysis():
    def __init__(self, user_id):
        self.user_id = user_id

    def content(self):
        def func_answer_append(user_id):
            # 獲取進行分析的使用者資料
            check_data = {"user_id": user_id}
            user_data = dbUserRequest.find_one(check_data)
            # 獲取當前題目
            check_data = {
                "question_number": user_data["question_number"], "question_group": "Suitability_analysis"}
            qusetion = dbQuestion.find_one(check_data)
            # 初始化答案清單, 答案回傳清單
            answer_list = []
            answer_return_list = []
            # 動態添加答案字串
            for answer_conut in range(0, int(qusetion["answer_sum"])):
                if answer_conut == 0:
                    # 答案清單添加答案字串
                    answer_list.append(qusetion["answer1"])
                elif answer_conut == 1:
                    answer_list.append(qusetion["answer2"])
                elif answer_conut == 2:
                    answer_list.append(qusetion["answer3"])
                elif answer_conut == 3:
                    answer_list.append(qusetion["answer4"])
                elif answer_conut == 4:
                    answer_list.append(qusetion["answer5"])
                # 設定按鈕回傳文字
                answer_text = "ans:" + \
                    str(user_data["question_number"]) + \
                    "-" + str(answer_conut + 1)
                # 答案回傳清單添加回傳文字
                answer_return_list.append(answer_text)
            # 如果當前題目是複選題
            if qusetion["question_type"] == "Suitability_analysis_multiple":
                # 新增確定按鈕
                check_button = "[確定]"
                answer_list.append(check_button)
                answer_return_list.append(
                    "ans:" + str(user_data["question_number"]) + "-" + check_button)
            # 回傳題目字串, 答案清單, 答案回傳清單
            return qusetion["description"], answer_list, answer_return_list
        # 初始化按鈕清單
        data_list = []
        # 進入函式處理資料, 取得題目字串, 答案清單, 答案回傳清單
        description, answer_list, answer_return_list = func_answer_append(
            self.user_id)
        # 迴圈添加答案進入按鈕清單
        for label_text, return_text in zip(answer_list, answer_return_list):
            data_bubble = {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "button",
                        "action": {
                            "type": "message",
                            "label": label_text,
                            "text": return_text
                        },
                        "color": "#0367D3",
                        "adjustMode": "shrink-to-fit"
                    }
                ],
                "backgroundColor": "#ffffff"
            }
            data_list.append(data_bubble)
        flex_message = FlexSendMessage(
            alt_text='適合性分析',
            contents={
                "type": "bubble",
                "size": "mega",
                "header": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": description,
                                    "color": "#444444",
                                    "size": "16px",
                                    "flex": 0,
                                    "weight": "regular",
                                    "margin": "xs",
                                    "wrap": True
                                }
                            ]
                        }
                    ],
                    "backgroundColor": "#ffffff",
                    "paddingAll": "20px",
                    "spacing": "md",
                    "height": "120px",
                    "paddingTop": "22px"
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": data_list,
                    "spacing": "xs"
                }
            }
        )
        return flex_message

# 汽車保險規劃


class Car_insurance_planning():
    def __init__(self, user_id):
        self.user_id = user_id

    def content(self):
        def func_answer_append(user_id):
            # 獲取進行規劃的使用者資料
            check_data = {"user_id": user_id}
            user_data = dbUserRequest.find_one(check_data)
            # 獲取當前題目
            check_data = {
                "question_number": user_data["question_number"], "question_group": "Car_insurance_planning"}
            qusetion = dbQuestion.find_one(check_data)
            # 初始化答案清單, 答案回傳清單
            answer_list = []
            answer_return_list = []
            # 動態添加答案字串
            for answer_conut in range(0, int(qusetion["answer_sum"])):
                if answer_conut == 0:
                    # 答案清單添加答案字串
                    answer_list.append(qusetion["answerA"])
                    # 回傳文字尾端字母
                    letter = "A"
                elif answer_conut == 1:
                    answer_list.append(qusetion["answerB"])
                    letter = "B"
                elif answer_conut == 2:
                    answer_list.append(qusetion["answerC"])
                    letter = "C"
                elif answer_conut == 3:
                    answer_list.append(qusetion["answerD"])
                    letter = "D"
                elif answer_conut == 4:
                    answer_list.append(qusetion["answerE"])
                    letter = "E"
                # 設定按鈕回傳文字
                answer_text = "ans:" + \
                    str(user_data["question_number"]) + "-" + letter
                # 答案回傳清單添加回傳文字
                answer_return_list.append(answer_text)
            # 回傳題目字串, 答案清單, 答案回傳清單
            return qusetion["description"], answer_list, answer_return_list
        # 初始化按鈕清單
        data_list = []
        # 進入函式處理資料, 取得題目字串, 答案清單, 答案回傳清單
        description, answer_list, answer_return_list = func_answer_append(
            self.user_id)
        # 迴圈添加答案進入按鈕清單
        for label_text, return_text in zip(answer_list, answer_return_list):
            data_bubble = {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "button",
                        "action": {
                            "type": "message",
                            "label": label_text,
                            "text": return_text
                        },
                        "color": "#0367D3",
                        "adjustMode": "shrink-to-fit"
                    }
                ],
                "backgroundColor": "#ffffff"
            }
            data_list.append(data_bubble)
        flex_message = FlexSendMessage(
            alt_text='汽車保險規劃',
            contents={
                "type": "bubble",
                "size": "mega",
                "header": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": description,
                                    "color": "#444444",
                                    "size": "16px",
                                    "flex": 4,
                                    "weight": "regular",
                                    "margin": "xs",
                                    "wrap": True
                                }
                            ]
                        }
                    ],
                    "backgroundColor": "#ffffff",
                    "paddingAll": "20px",
                    "spacing": "md",
                    "height": "120px",
                    "paddingTop": "22px"
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": data_list,
                    "spacing": "xs"
                }
            }
        )
        return flex_message

# 人生保險規劃1(正式)


class Life_stage1():
    
    def __init__(self, user_id):
        self.user_id = user_id

    def content(self):
        def func_answer_append(user_id):
            # 獲取進行規劃的使用者資料
            check_data = {"user_id": user_id}
            user_data = dbUserRequest.find_one(check_data)
            # 獲取當前題目
            check_data = {
                "question_number": user_data["question_number"], "question_group": "Life_stage1"}
            qusetion = dbQuestion.find_one(check_data)
            # 初始化答案清單, 答案回傳清單
            answer_list = []
            answer_return_list = []
            # 動態添加答案字串
            for answer_conut in range(0, int(qusetion["answer_sum"])):
                if answer_conut == 0:
                    # 答案清單添加答案字串
                    answer_list.append(qusetion["answer1"])
                elif answer_conut == 1:
                    answer_list.append(qusetion["answer2"])
                elif answer_conut == 2:
                    answer_list.append(qusetion["answer3"])
                elif answer_conut == 3:
                    answer_list.append(qusetion["answer4"])
                elif answer_conut == 4:
                    answer_list.append(qusetion["answer5"])
                elif answer_conut == 5:
                    answer_list.append(qusetion["answer6"])
                # 設定按鈕回傳文字
                answer_text = "ans:" + \
                    str(user_data["question_number"]) + \
                    "-" + str(answer_conut + 1)
                # 答案回傳清單添加回傳文字
                answer_return_list.append(answer_text)
            # 如果當前題目是複選題
            if qusetion["question_type"] == "Life_stage1_multiple":
                # 新增確定按鈕
                check_button = "[確定]"
                answer_list.append(check_button)
                answer_return_list.append(
                    "ans:" + str(user_data["question_number"]) + "-" + check_button)
            # 回傳題目字串, 答案清單, 答案回傳清單
            return qusetion["description"], answer_list, answer_return_list
        # 初始化按鈕清單
        data_list = []
        # 進入函式處理資料, 取得題目字串, 答案清單, 答案回傳清單
        description, answer_list, answer_return_list = func_answer_append(
            self.user_id)
        # 迴圈添加答案進入按鈕清單
        for label_text, return_text in zip(answer_list, answer_return_list):
            data_bubble = {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "button",
                        "action": {
                            "type": "message",
                            "label": label_text,
                            "text": return_text
                        },
                        "color": "#0367D3"
                    }
                ],
                "backgroundColor": "#ffffff"
            }
            data_list.append(data_bubble)
        flex_message = FlexSendMessage(
            alt_text='人生保險規劃',
            contents={
                "type": "bubble",
                "size": "mega",
                "header": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": description,
                                    "color": "#444444",
                                    "size": "12px",
                                    "flex": 4,
                                    "weight": "regular",
                                    "margin": "xs"
                                }
                            ]
                        }
                    ],
                    "backgroundColor": "#ffffff",
                    "paddingAll": "20px",
                    "spacing": "md",
                    "height": "80px",
                    "paddingTop": "22px"
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": data_list,
                    "spacing": "xs"
                }
            }
        )
        return flex_message

class Life_stage1_result():
    @ staticmethod
    def record(check_data,event):
        user_data = dbUserRequest.find(check_data)
        if user_data.count() != 0:
            # 回傳分析結果
            answer_record_life_stage_list = user_data[0]["answer_record_life_stage"].split(
                "-")
            # 獲取投資類型對應的投資建議
            check_data = {
                "life_stage1_type": user_data[0]["life_stage1_type"]}
            # 回傳資料格式
            myReply = "上次人生保險規劃結果：\n"
            myReply += "人生階段：" + \
                user_data[0]["life_stage1_type"] + "\n"
            myReply += "加總分數：" + user_data[0]["score"] + "\n"
            myReply += "選項紀錄：" + "\n"
            for i in range(len(answer_record_life_stage_list)):
                if (i > 0):
                    check_data = {"question_number": str(i),
                                    "question_group": "Life_stage1"}
                    question = dbQuestion.find_one(check_data)
                    myReply += answer_record_life_stage_list[i] + "\n"
                    myReply += "題目:" + question['description'] + "\n"
                    myReply += "選項:"
                    if (question['question_type'] == "Life_stage1_multiple"):
                        if answer_record_life_stage_list[i].split(":")[1] == "":
                            myReply += "無選擇"
                        for j in range(len(answer_record_life_stage_list[i].split(":")[1])):
                            multiple_answer = ",".join(
                                answer_record_life_stage_list[i].split(":")[1])  # 1,4
                            multiple_answer = multiple_answer.split(
                                ",") 
                            answer = "answer"+multiple_answer[j]
                            myReply += question[answer]+" "
                        myReply += "\n"
                    else:
                        answer = "answer" + \
                            str(answer_record_life_stage_list[i].split(
                                ":")[1])
                        myReply += question[answer] + "\n"
            check_data = {"user_id": event.source.user_id}
            check_options = dbUserRequest.find_one(check_data)
            if check_options["gender"] == "1":
                sex="男"
            else:
                sex="女"
            check_data = {"type_name":user_data[0]["life_stage1_type"],"insurance_group": "life_stage1_result","gender":sex}
            question = dbInsurance.find_one(check_data)
            myReply += question["guarantee_direction"]+ "\n"
            
        else:
            myReply = "尚未進行適合性分析"
        return myReply

    @ staticmethod
    def result_button(check_data,event):
        user_data = dbUserRequest.find(check_data)
        check_data = {"user_id": event.source.user_id}
        check_options = dbUserRequest.find_one(check_data)
        if check_options["gender"] == "1":
            sex="男"
        else:
            sex="女"
        check_data = {"type_name":user_data[0]["life_stage1_type"],"insurance_group": "life_stage1_result","gender":sex}
        question = dbInsurance.find_one(check_data)
        advice = question["insurance_list"].split(",")#險種
        data_list=[]
        for i in range(len(advice)):
            contents={
                    "type": "button",
                    "style": "link",
                    "height": "sm",
                    "action": {
                    "type": "message",
                    "label": advice[i],
                    "text":  advice[i]
                    }
                }
            data_list.append(dict(contents))
        
        link={
            "type": "button",
            "style": "link",
            "height": "sm",
            "action": {
            "type": "uri",
            "label": "網址",
            "uri": question["link_1"]
            }
        }
        data_list.append(dict(link))
        advice_button={
            "type": "bubble",
            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": 
                data_list
            }
            }
        return advice_button
    @ staticmethod
    def result_button2(check_data,event):
        user_data = dbUserRequest.find(check_data)
        check_data = {"user_id": event.source.user_id}
        check_options = dbUserRequest.find_one(check_data)

        check_data = {"type_name":user_data[0]["life_stage2_type"],"insurance_group": "life_stage1_result","gender":check_options["gender"]}
        question = dbInsurance.find_one(check_data)
        advice = question["insurance_list"].split(",")#險種
        data_list=[]
        for i in range(len(advice)):
            contents={
                    "type": "button",
                    "style": "link",
                    "height": "sm",
                    "action": {
                    "type": "message",
                    "label": advice[i],
                    "text":  advice[i]
                    }
                }
            data_list.append(dict(contents))
        
        link={
            "type": "button",
            "style": "link",
            "height": "sm",
            "action": {
            "type": "uri",
            "label": "網址",
            "uri": question["link_1"]
            }
        }
        data_list.append(dict(link))
        advice_button={
            "type": "bubble",
            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": 
                data_list
            }
            }
        return advice_button
    @ staticmethod
    def first_time_reply(check_data,myReply):
        question = dbInsurance.find_one(check_data)
        advice = question["insurance_list"].split(",")#險種
        data_list=[]
        for i in range(len(advice)):
            contents={
                    "type": "button",
                    "style": "link",
                    "height": "sm",
                    "action": {
                    "type": "message",
                    "label": advice[i],
                    "text":  advice[i]
                    }
                }
            data_list.append(dict(contents))
        
        link={
            "type": "button",
            "style": "link",
            "height": "sm",
            "action": {
            "type": "uri",
            "label": "網址",
            "uri": question["link_1"]
            }
        }
        data_list.append(dict(link))
        advice_button={
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": 
                data_list
            }

        first_Reply={
        "type": "bubble",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
            {
                "type": "text",
                "text": myReply,
                "wrap": True
            }
            ]
        },
        "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                advice_button
                ]
                # "contents": 
                # advice_button
            }
        }
        return first_Reply

    @ staticmethod   
    def insurance_1(user_id):#意外險
        question = dbUserRequest.find_one(user_id)
        if question["current_Q"]=="1":
            advice=dbInsurance.find_one({"type_name":question["life_stage1_type"],"button_insurance":"1"})
        else:
            advice=dbInsurance.find_one({"type_name":question["life_stage2_type"],"button_insurance":"1"})
        return advice["意外險"]

    @ staticmethod   
    def insurance_2(user_id):#失能險
        question = dbUserRequest.find_one(user_id)
        if question["current_Q"]=="1":
            advice=dbInsurance.find_one({"type_name":question["life_stage1_type"],"button_insurance":"1"})
        else:
            advice=dbInsurance.find_one({"type_name":question["life_stage2_type"],"button_insurance":"1"})
        return advice["失能險"]

    @ staticmethod   
    def insurance_3(user_id):#重大疾病險
        question = dbUserRequest.find_one(user_id)
        if question["current_Q"]=="1":
            advice=dbInsurance.find_one({"type_name":question["life_stage1_type"],"button_insurance":"1"})
        else:
            advice=dbInsurance.find_one({"type_name":question["life_stage2_type"],"button_insurance":"1"})
        return advice["重大疾病險"]

    @ staticmethod   
    def insurance_4(user_id):#醫療險
        question = dbUserRequest.find_one(user_id)
        if question["life_stage1_type"]=="親親寶貝" or question["life_stage2_type"]=="親親寶貝":
            message=ImageSendMessage(
                original_content_url="https://i.imgur.com/Ioo0wm7.jpg",
                preview_image_url= "https://i.imgur.com/99BQcEj.jpg"
            )
            return message
        advice=dbInsurance.find_one({"type_name":question["life_stage1_type"],"button_insurance":"1"})
        return advice["醫療險"]

    @ staticmethod   
    def insurance_5(user_id):#壽險
        question = dbUserRequest.find_one(user_id)
        if question["current_Q"]=="1":
            advice=dbInsurance.find_one({"type_name":question["life_stage1_type"],"button_insurance":"1"})
        else:
            advice=dbInsurance.find_one({"type_name":question["life_stage2_type"],"button_insurance":"1"})
        return advice["壽險"]

    @ staticmethod   
    def insurance_6(user_id):#癌症險
        question = dbUserRequest.find_one(user_id)
        if question["current_Q"]=="1":
            advice=dbInsurance.find_one({"type_name":question["life_stage1_type"],"button_insurance":"1"})
        else:
            advice=dbInsurance.find_one({"type_name":question["life_stage2_type"],"button_insurance":"1"})
        return advice["癌症險"]

    @ staticmethod   
    def insurance_7(user_id):#終身定期
        question = dbUserRequest.find_one(user_id)
        if question["current_Q"]=="1":
            advice=dbInsurance.find_one({"type_name":question["life_stage1_type"],"button_insurance":"1"})
        else:
            advice=dbInsurance.find_one({"type_name":question["life_stage2_type"],"button_insurance":"1"})
        return advice["終身定期"]

    @ staticmethod   
    def insurance_8(user_id):#婦嬰險
        question = dbUserRequest.find_one(user_id)
        if question["current_Q"]=="1":
            advice=dbInsurance.find_one({"type_name":question["life_stage1_type"],"button_insurance":"1"})
        else:
            advice=dbInsurance.find_one({"type_name":question["life_stage2_type"],"button_insurance":"1"})
        return advice["婦嬰險"]

# 人生保險規劃2(測試_商院資料5)


class Life_stage2():
    def __init__(self, user_id):
        self.user_id = user_id
    def content(self):
        def func_answer_append(user_id):
            # 獲取進行規劃的使用者資料
            check_data = {"user_id": user_id}
            user_data = dbUserRequest.find_one(check_data)
            # 獲取當前題目
            check_data = {
                "question_number": user_data["question_number"], "question_group": "Life_stage2"}
            qusetion = dbQuestion.find_one(check_data)
            # 初始化答案清單, 答案回傳清單
            answer_list = []
            answer_return_list = []
            # 動態添加答案字串
            for answer_conut in range(0, int(qusetion["answer_sum"])):
                if answer_conut == 0:
                    # 答案清單添加答案字串
                    answer_list.append(qusetion["answer1"])
                elif answer_conut == 1:
                    answer_list.append(qusetion["answer2"])
                elif answer_conut == 2:
                    answer_list.append(qusetion["answer3"])
                elif answer_conut == 3:
                    answer_list.append(qusetion["answer4"])
                elif answer_conut == 4:
                    answer_list.append(qusetion["answer5"])
                elif answer_conut == 5:
                    answer_list.append(qusetion["answer6"])
                elif answer_conut == 6:
                    answer_list.append(qusetion["answer7"])
                elif answer_conut == 7:
                    answer_list.append(qusetion["answer8"])
                # 設定按鈕回傳文字
                answer_text = "ans:" + \
                    str(user_data["question_number"]) + \
                    "-" + str(answer_conut + 1)
                # 答案回傳清單添加回傳文字
                answer_return_list.append(answer_text)
            # 回傳題目字串, 答案清單, 答案回傳清單
            return qusetion["description"], answer_list, answer_return_list
        # 初始化按鈕清單
        data_list = []
        # 進入函式處理資料, 取得題目字串, 答案清單, 答案回傳清單
        description, answer_list, answer_return_list = func_answer_append(
            self.user_id)
        # 迴圈添加答案進入按鈕清單
        for label_text, return_text in zip(answer_list, answer_return_list):
            data_bubble = {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "button",
                        "action": {
                            "type": "message",
                            "label": label_text,
                            "text": return_text
                        },
                        "color": "#0367D3"
                    }
                ],
                "backgroundColor": "#ffffff"
            }
            data_list.append(data_bubble)
        flex_message = FlexSendMessage(
            alt_text='人生保險規劃2',
            contents={
                "type": "bubble",
                "size": "mega",
                "header": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": description,
                                    "color": "#444444",
                                    "size": "12px",
                                    "flex": 4,
                                    "weight": "regular",
                                    "margin": "xs"
                                }
                            ]
                        }
                    ],
                    "backgroundColor": "#ffffff",
                    "paddingAll": "20px",
                    "spacing": "md",
                    "height": "80px",
                    "paddingTop": "22px"
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": data_list,
                    "spacing": "xs"
                }
            }
        )
        return flex_message
    
    def reply_result(line_bot_api,event):
        check_data = {"user_id": event.source.user_id}
        request_data = dbUserRequest.find_one(check_data)
        check_data = {"insurance_group": "life_stage1_result","age":"年齡"+request_data["age"]+"歲"}
        reply_data = dbInsurance.find_one(check_data)
        myReply= ""
        myReply +="選擇階段題目："+request_data["life_stage2_type"]+'\n'
        myReply +=reply_data["guarantee_direction"]
        check_data = {"user_id": event.source.user_id}
        button_result = Life_stage1_result().result_button2(check_data, event)
        line_bot_api.reply_message(
            event.reply_token,
            [TextSendMessage(text=myReply), FlexSendMessage(
                alt_text='險種按鈕', contents=button_result)]
        )
    def multiple_button():
        flex_message = FlexSendMessage(
            alt_text='青春活力',
            contents={
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                {
                    "type": "button",
                    "action": {
                    "type": "message",
                    "label": "青春活力",
                    "text": "青春活力"
                    }
                },
                {
                    "type": "button",
                    "action": {
                    "type": "message",
                    "label": "青春活力_基本型",
                    "text": "青春活力_基本型"
                    }
                }
                ]
            }
            })
        return flex_message
    def multiple_button2():
        flex_message = FlexSendMessage(
            alt_text='單身貴族',
            contents={
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                {
                    "type": "button",
                    "action": {
                    "type": "message",
                    "label": "單身貴族",
                    "text": "單身貴族"
                    }
                },
                {
                    "type": "button",
                    "action": {
                    "type": "message",
                    "label": "單身貴族_小資族",
                    "text": "單身貴族_小資族"
                    }
                }
                ]
            }
            })
        return flex_message
# 「功能列表」按鈕樣板訊息


class function_list():

    def content(self):
        flex_message = FlexSendMessage(
            alt_text='hello',
            contents={
                "type": "carousel",
                "contents": [
                    {
                        "type": "bubble",
                        "hero": {
                            "type": "image",
                            "url": "https://i.imgur.com/VDmDtHK.png",
                            "size": "full",
                            "aspectRatio": "20:13",
                            "aspectMode": "cover"
                        },
                        "body": {
                            "type": "box",
                            "layout": "vertical",
                            "spacing": "sm",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "適合性分析",
                                    "weight": "bold",
                                    "size": "xl",
                                    "wrap": True,
                                    "contents": []
                                }
                            ]
                        },
                        "footer": {
                            "type": "box",
                            "layout": "vertical",
                            "spacing": "sm",
                            "contents": [
                                {
                                    "type": "button",
                                    "action": {
                                        "type": "message",
                                        "label": "適合性分析",
                                        "text": "適合性分析"
                                    },
                                    "style": "primary"
                                },
                                {
                                    "type": "button",
                                    "action": {
                                        "type": "message",
                                        "label": "適合性分析結果",
                                        "text": "適合性分析結果"
                                    },
                                    "style": "primary"
                                }
                            ]
                        }
                    },
                    {
                        "type": "bubble",
                        "hero": {
                            "type": "image",
                            "url": "https://i.imgur.com/raJzb4s.png",
                            "size": "full",
                            "aspectRatio": "20:13",
                            "aspectMode": "cover"
                        },
                        "body": {
                            "type": "box",
                            "layout": "vertical",
                            "spacing": "sm",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "汽車保險規劃",
                                    "weight": "bold",
                                    "size": "xl",
                                    "wrap": True,
                                    "contents": []
                                }
                            ]
                        },
                        "footer": {
                            "type": "box",
                            "layout": "vertical",
                            "spacing": "sm",
                            "contents": [
                                {
                                    "type": "button",
                                    "action": {
                                        "type": "message",
                                        "label": "汽車保險規劃",
                                        "text": "汽車保險規劃"
                                    },
                                    "style": "primary"
                                },
                                {
                                    "type": "button",
                                    "action": {
                                        "type": "message",
                                        "label": "汽車保險規劃結果",
                                        "text": "汽車保險規劃結果"
                                    },
                                    "style": "primary"
                                }
                            ]
                        }
                    },
                    {
                        "type": "bubble",
                        "hero": {
                            "type": "image",
                            "url": "https://i.imgur.com/omFNQdN.png",
                            "size": "full",
                            "aspectRatio": "20:13",
                            "aspectMode": "cover"
                        },
                        "body": {
                            "type": "box",
                            "layout": "vertical",
                            "spacing": "sm",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "人生保險規劃1",
                                    "weight": "bold",
                                    "size": "xl",
                                    "wrap": True,
                                    "contents": []
                                }
                            ]
                        },
                        "footer": {
                            "type": "box",
                            "layout": "vertical",
                            "spacing": "sm",
                            "contents": [
                                {
                                    "type": "button",
                                    "action": {
                                        "type": "message",
                                        "label": "人生保險規劃1",
                                        "text": "人生保險規劃1"
                                    },
                                    "style": "primary"
                                },
                                {
                                    "type": "button",
                                    "action": {
                                        "type": "message",
                                        "label": "人生保險規劃紀錄1",
                                        "text": "人生保險規劃紀錄1"
                                    },
                                    "style": "primary"
                                }
                            ]
                        }
                    },
                    {
                        "type": "bubble",
                        "hero": {
                            "type": "image",
                            "url": "https://i.imgur.com/omFNQdN.png",
                            "size": "full",
                            "aspectRatio": "20:13",
                            "aspectMode": "cover"
                        },
                        "body": {
                            "type": "box",
                            "layout": "vertical",
                            "spacing": "sm",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "人生保險規劃2",
                                    "weight": "bold",
                                    "size": "xl",
                                    "wrap": True,
                                    "contents": []
                                }
                            ]
                        },
                        "footer": {
                            "type": "box",
                            "layout": "vertical",
                            "spacing": "sm",
                            "contents": [
                                {
                                    "type": "button",
                                    "action": {
                                        "type": "message",
                                        "label": "人生保險規劃2",
                                        "text": "人生保險規劃2"
                                    },
                                    "style": "primary"
                                },
                                {
                                    "type": "button",
                                    "action": {
                                        "type": "message",
                                        "label": "人生保險規劃紀錄2",
                                        "text": "人生保險規劃紀錄2"
                                    },
                                    "style": "primary"
                                }
                            ]
                        }
                    },
                    {
                        "type": "bubble",
                        "hero": {
                            "type": "image",
                            "url": "https://i.imgur.com/IyOugfE.png",
                            "size": "full",
                            "aspectRatio": "20:13",
                            "aspectMode": "cover"
                        },
                        "body": {
                            "type": "box",
                            "layout": "vertical",
                            "spacing": "sm",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "保障缺口分析",
                                    "weight": "bold",
                                    "size": "xl",
                                    "wrap": True,
                                    "contents": []
                                }
                            ]
                        },
                        "footer": {
                            "type": "box",
                            "layout": "vertical",
                            "spacing": "sm",
                            "contents": [
                                {
                                    "type": "button",
                                    "action": {
                                        "type": "message",
                                        "label": "保障缺口分析",
                                        "text": "保障缺口分析"
                                    },
                                    "style": "primary"
                                },
                                {
                                    "type": "button",
                                    "action": {
                                        "type": "message",
                                        "label": "保障缺口紀錄",
                                        "text": "保障缺口紀錄"
                                    },
                                    "style": "primary"
                                }
                            ]
                        }
                    },
                    {
                        "type": "bubble",
                        "hero": {
                            "type": "image",
                            "url": "https://i.imgur.com/1fXiYlv.png",
                            "size": "full",
                            "aspectRatio": "20:13",
                            "aspectMode": "cover"
                        },
                        "body": {
                            "type": "box",
                            "layout": "vertical",
                            "spacing": "sm",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "退休財務規劃",
                                    "weight": "bold",
                                    "size": "xl",
                                    "wrap": True,
                                    "contents": []
                                }
                            ]
                        },
                        "footer": {
                            "type": "box",
                            "layout": "vertical",
                            "spacing": "sm",
                            "contents": [
                                {
                                    "type": "button",
                                    "action": {
                                        "type": "message",
                                        "label": "退休財務規劃",
                                        "text": "退休財務規劃"
                                    },
                                    "style": "primary"
                                },
                                {
                                    "type": "box",
                                    "layout": "horizontal",
                                    "spacing": "sm",
                                    "contents": [
                                        {
                                            "type": "button",
                                            "action": {
                                                "type": "message",
                                                "label": "退休財務紀錄",
                                                "text": "退休財務紀錄"
                                            },
                                            "style": "primary"
                                        },
                                        {
                                            "type": "button",
                                            "action": {
                                                "type": "message",
                                                "label": "退休資產",
                                                "text": "退休資產"
                                            },
                                            "style": "primary"
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                ]
            }
        )
        return flex_message
