from decimal import Context
from flask import Flask, request, abort
import flask_mail
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, PostbackEvent, TextMessage, TextSendMessage, ImageSendMessage, FlexSendMessage
from message import *
from pymongo import MongoClient
import configparser
import re
import os

from guarantee_gap import Guarantee_gap
from joint_financial_planning import Joint_financial


app = Flask(__name__)
# app.config["ENV"] = "development"
# app.config["DEBUG"] = True

# config 環境設定解析
config = configparser.ConfigParser()
config.read("config.ini")

# Linebot 金鑰
line_bot_api = LineBotApi(config['line_bot']['Channel_Access_Token'])
handler = WebhookHandler(config['line_bot']['Channel_Secret'])

# mongoDB atlas 連線
myMongoClient = MongoClient(config['connect_config']['Mongodb_atlas_URL'])
myMongoDb = myMongoClient["insurance-data"]

# 使用者請求
dbUserRequest = myMongoDb['user-request']
# 適合性分析題庫
dbQuestion = myMongoDb['qusetion-database']
# 投資建議資料庫
dbAdvice = myMongoDb['investment-advice']
# 車險種類資料庫
dbCar_insurance = myMongoDb['car_insurance_type']
# 保險建議資料庫
dbInsurance = myMongoDb['insurance-advice']


app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = config['flask_mail']['MAIL_USERNAME']
app.config['MAIL_PASSWORD'] = config['flask_mail']['MAIL_PASSWORD']
app.config['MAIL_DEFAULT_SENDER'] = app.config['MAIL_USERNAME']
app.config['MAIL_ASCII_ATTACHMENTS'] = False
mail_object = flask_mail.Mail(app)


joint_financial_question_mode = "question"
# Line bot 的主要 function，以下設定如非必要最好別動


@app.route("/callback", methods=['POST'])
def callback():
    # 抓 X-Line-Signature 標頭的值
    signature = request.headers['X-Line-Signature']
    # 抓 request body 的文字
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        # 把文字和標頭存進handler
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'ok'

# message bot 接收到使用者資料時跑的 function


@handler.add(MessageEvent, message=(TextMessage))
def handle_message(event):
    # 檢查使用者ID是否存在於資料庫
    check_data = {"user_id": event.source.user_id}
    user_data = dbUserRequest.find(check_data)
    # 初始化回傳文字
    myReply = "請輸入正確的關鍵字！"
    # 如果使用者輸入文字
    if event.message.type == "text":
        typing_field = Joint_financial.on_typing(event.source.user_id)
        if not typing_field:
            # 功能列表
            if re.compile("[功]+[能]+[列]+[表]+").search(event.message.text) is not None:
                # 回復「功能列表」按鈕樣板訊息
                line_bot_api.reply_message(
                    event.reply_token,
                    function_list().content()
                )
                return
            # 使用者適合性分析
            elif re.compile("適合性分析").search(event.message.text) is not None and re.compile("適合性分析結果").search(event.message.text) is None:
                dbUserRequest.update_one({"user_id": event.source.user_id}, {"$set": {"status": "Suitability_analysis", "question_number": "1",
                                                                                      "score": "0", "answer_record_suitability": "", "suitability_analysis_type": "", "multiple_options": ""}}, upsert=True)
                # 回傳適合性分析題目
                myReply = Suitability_analysis(event.source.user_id).content()
                line_bot_api.reply_message(
                    event.reply_token,
                    myReply
                )
                return
            # 使用者汽車保險規劃
            elif re.compile("汽車保險規劃").search(event.message.text) is not None and re.compile("汽車保險規劃結果").search(event.message.text) is None:
                dbUserRequest.update_one({"user_id": event.source.user_id}, {"$set": {
                    "status": "Car_insurance_planning", "question_number": "1", "answer_record_car_insurance": ""}}, upsert=True)
                # 回傳汽車保險規劃題目
                myReply = Car_insurance_planning(
                    event.source.user_id).content()
                line_bot_api.reply_message(
                    event.reply_token,
                    myReply
                )
                return
            # 使用者汽車保險規劃結果
            elif re.compile("汽車保險規劃結果").search(event.message.text) is not None:
                # 如果使用者使用過適合性分析
                if user_data.count() != 0 and user_data[0]["answer_record_car_insurance"] != "":
                    # 分割每題題號和選項
                    answer_record_list = user_data[0]["answer_record_car_insurance"].split(
                        "-")
                    # 回傳保險規劃
                    myReply = "上次汽車保險規劃結果：\n"
                    # 回傳資料格式
                    insurance_record_list = user_data[0]["insurance_record"].split(
                        "-")
                    for record in insurance_record_list:
                        if record != "":
                            myReply += "車險建議：" + record + "\n"
                    myReply += "選項紀錄：" + "\n"
                    for record in answer_record_list:
                        if record != "":
                            myReply += record + "\n"
                            ans = record.split(":")
                            check_data = {
                                "question_number": ans[0], "question_group": "Car_insurance_planning"}
                            qusetion = dbQuestion.find_one(check_data)
                            # 回傳題目字串
                            myReply += "題目:" + qusetion["description"] + "\n"
                            # 依答案選項回傳答案字串
                            myReply += "選項:"
                            if ans[1] == "A":
                                myReply += qusetion["answerA"] + "\n"
                            elif ans[1] == "B":
                                myReply += qusetion["answerB"] + "\n"
                            elif ans[1] == "C":
                                myReply += qusetion["answerC"] + "\n"
                            elif ans[1] == "D":
                                myReply += qusetion["answerD"] + "\n"
                            elif ans[1] == "E":
                                myReply += qusetion["answerE"] + "\n"
                            # 結尾分行
                            myReply += "\n"
                else:
                    myReply = "尚未進行適合性分析"
            # 人生保險規劃1
            elif re.compile("人生保險規劃1").search(event.message.text) is not None:
                dbUserRequest.update_one({"user_id": event.source.user_id}, {"$set": {"status": "Life_stage1", "question_number": "1", "gender": "",
                                         "score": "0", "answer_record_life_stage": "", "life_stage1_type": "", "multiple_options": "","current_Q":"1"}}, upsert=True)
                # 回傳人生保險規劃題目
                myReply = Life_stage1(event.source.user_id).content()
                line_bot_api.reply_message(
                    event.reply_token,
                    myReply
                )
                return
            # 人生保險規劃2
            elif re.compile("人生保險規劃2").search(event.message.text) is not None:
                dbUserRequest.update_one({"user_id": event.source.user_id}, {"$set": {"status": "Life_stage2", "question_number": "1", "gender": "",
                                         "score": "0", "answer_record_life_stage2": "","age":"", "life_stage2_type": "", "multiple_options": "","current_Q":"2","answered":"0"}}, upsert=True)
                myReply = Life_stage2(event.source.user_id).content()
                line_bot_api.reply_message(
                    event.reply_token,
                    myReply
                )
                return
            # 保障缺口分析
            elif re.compile("保障缺口分析").search(event.message.text) is not None:
                # 回傳退休財務分析
                myReply = Guarantee_gap.content(event.source.user_id)  # 冠博程式
                line_bot_api.reply_message(
                    event.reply_token,
                    myReply
                )
                return
            # 退休財務規劃
            elif re.compile("退休財務規劃").search(event.message.text) is not None:
                # 回傳退休財務規劃
                myReply = Joint_financial.content(
                    event.source.user_id, mode=joint_financial_question_mode)  # 冠博程式
                line_bot_api.reply_message(
                    event.reply_token,
                    myReply
                )
                return
            # 保障缺口紀錄
            elif re.compile("保障缺口紀錄").search(event.message.text) is not None:
                # 回傳保障缺口紀錄
                myReply = Guarantee_gap.content(
                    event.source.user_id, False)  # 冠博程式
                line_bot_api.reply_message(
                    event.reply_token,
                    myReply
                )
                return
            # 退休財務紀錄
            elif re.compile("退休財務紀錄").search(event.message.text) is not None:
                # 回傳退休財務規劃
                myReply = Joint_financial.content(
                    event.source.user_id, mode=joint_financial_question_mode, calculate=False, mail=mail_object)  # 冠博程式
                line_bot_api.reply_message(
                    event.reply_token,
                    myReply
                )
                return
            # 退休資產
            elif re.compile("退休資產").search(event.message.text) is not None:
                # 回傳退休資產
                myReply = Joint_financial.content(
                    event.source.user_id, mode=joint_financial_question_mode, calculate=False, get_asset=True)  # 冠博程式
                line_bot_api.reply_message(
                    event.reply_token,
                    myReply
                )
                return
            elif re.compile("婦嬰險").search(event.message.text) is not None:
                myReply = Life_stage1_result.insurance_8(check_data)
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=myReply)
                )
                return
            elif re.compile("醫療險").search(event.message.text) is not None:
                question = dbUserRequest.find_one(check_data)
                myReply = Life_stage1_result.insurance_4(check_data)
                if question["life_stage_type"] == "親親寶貝":
                    line_bot_api.reply_message(
                        event.reply_token,
                        myReply
                    )
                elif question["life_stage1_type"] == "親親寶貝":
                    line_bot_api.reply_message(
                        event.reply_token,
                        myReply
                    )
                elif question["life_stage2_type"] == "親親寶貝":
                    line_bot_api.reply_message(
                        event.reply_token,
                        myReply
                    )
                else:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=myReply)
                    )
                return
            elif re.compile("終身定期").search(event.message.text) is not None:
                myReply = Life_stage1_result.insurance_7(check_data)
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=myReply)
                )
                return
            elif re.compile("癌症險").search(event.message.text) is not None:
                myReply = Life_stage1_result.insurance_6(check_data)
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=myReply)
                )
                return
            elif re.compile("重大疾病險").search(event.message.text) is not None:
                myReply = Life_stage1_result.insurance_3(check_data)
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=myReply)
                )
                return
            elif re.compile("意外險").search(event.message.text) is not None:
                myReply = Life_stage1_result.insurance_1(check_data)
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=myReply)
                )
                return
            elif re.compile("失能險").search(event.message.text) is not None:
                myReply = Life_stage1_result.insurance_2(check_data)
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=myReply)
                )
                return
            elif re.compile("壽險").search(event.message.text) is not None:
                myReply = Life_stage1_result.insurance_5(check_data)
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=myReply)
                )
                return
            elif re.compile("單身貴族_小資族").search(event.message.text) is not None:
                dbUserRequest.update_one({"user_id": event.source.user_id},{
                    "$set": {"life_stage2_type": "單身貴族_小資族"}}, upsert=True)
                Life_stage2.reply_result(line_bot_api,event)
                return
            elif re.compile("單身貴族").search(event.message.text) is not None:
                dbUserRequest.update_one({"user_id": event.source.user_id},{
                    "$set": {"life_stage2_type": "單身貴族"}}, upsert=True)
                Life_stage2.reply_result(line_bot_api,event)
                return
            elif re.compile("青春活力_基本型").search(event.message.text) is not None:
                dbUserRequest.update_one({"user_id": event.source.user_id},{
                    "$set": {"life_stage2_type": "青春活力_基本型"}}, upsert=True)
                Life_stage2.reply_result(line_bot_api,event)
                return
            elif re.compile("青春活力").search(event.message.text) is not None:
                dbUserRequest.update_one({"user_id": event.source.user_id},{
                    "$set": {"life_stage2_type": "青春活力"}}, upsert=True)
                Life_stage2.reply_result(line_bot_api,event)
                return
            # 使用者適合性分析結果
            elif re.compile("適合性分析結果").search(event.message.text) is not None:
                # 如果使用者使用過適合性分析
                if user_data.count() != 0 and user_data[0]["answer_record_suitability"] != "":
                    # 回傳分析結果
                    answer_record_suitability_list = user_data[0]["answer_record_suitability"].split(
                        "-")
                    # 獲取投資類型對應的投資建議
                    check_data = {
                        "suitability_analysis_type": user_data[0]["suitability_analysis_type"]}
                    advice_data = dbAdvice.find(check_data)
                    # 回傳資料格式
                    myReply = "上次適合性分析結果：\n"
                    myReply += "投資類型：" + \
                        user_data[0]["suitability_analysis_type"] + "\n"
                    myReply += "投資建議：" + advice_data[0]["advice"] + "\n"
                    myReply += "加總分數：" + user_data[0]["score"] + "\n"
                    myReply += "選項紀錄：" + "\n"
                    for record in answer_record_suitability_list:
                        if record != "":
                            myReply += record + "\n"
                            ans = record.split(":")
                            check_data = {
                                "question_number": ans[0], "question_group": "Suitability_analysis"}
                            qusetion = dbQuestion.find_one(check_data)
                            # 回傳題目字串
                            myReply += "題目:" + qusetion["description"] + "\n"
                            # 依答案選項回傳答案字串
                            myReply += "選項:"
                            if ans[1] == "1":
                                myReply += qusetion["answer1"] + "\n"
                            elif ans[1] == "2":
                                myReply += qusetion["answer2"] + "\n"
                            elif ans[1] == "3":
                                myReply += qusetion["answer3"] + "\n"
                            elif ans[1] == "4":
                                myReply += qusetion["answer4"] + "\n"
                            elif ans[1] == "5":
                                myReply += qusetion["answer5"] + "\n"
                            else:
                                for i in ans[1]:
                                    if i == "1":
                                        myReply += qusetion["answer1"] + "\n"
                                    elif i == "2":
                                        myReply += qusetion["answer2"] + "\n"
                                    elif i == "3":
                                        myReply += qusetion["answer3"] + "\n"
                                    elif i == "4":
                                        myReply += qusetion["answer4"] + "\n"
                                    elif i == "5":
                                        myReply += qusetion["answer5"] + "\n"
                            # 結尾分行
                            myReply += "\n"

                else:
                    myReply = "尚未進行適合性分析"
            elif re.compile("人生保險規劃紀錄1").search(event.message.text) is not None:
                check_data = {"user_id": event.source.user_id}
                request_data = dbUserRequest.find_one(check_data)
                if request_data["life_stage1_type"]=="":
                    line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="請先完成人生保險規劃1")
                    )
                    return
                myReply = Life_stage1_result().record(check_data, event)
                button_result = Life_stage1_result().result_button(check_data, event)
                line_bot_api.reply_message(
                    event.reply_token,
                    [TextSendMessage(text=myReply), FlexSendMessage(
                        alt_text='險種按鈕', contents=button_result)]
                )
                return
            elif re.compile("人生保險規劃紀錄2").search(event.message.text) is not None:
                check_data = {"user_id": event.source.user_id}
                request_data = dbUserRequest.find_one(check_data)
                if request_data["life_stage2_type"]=="":
                    line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="請先完成人生保險規劃2")
                    )
                    return
                Life_stage2.reply_result(line_bot_api,event)
                return
            # 使用者點選答案按鈕
            if "ans:" in event.message.text:
                # 如果使用者正在進行適合性分析
                if user_data.count() != 0 and user_data[0]["status"] == "Suitability_analysis":
                    # 最後一題總結函式
                    def Suitability_analysis_final_question(sum_score, answer_record_suitability):
                        if sum_score < 14:
                            suitability_analysis_type = "保守型"
                        elif sum_score < 22:
                            suitability_analysis_type = "非常謹慎型"
                        elif sum_score < 31:
                            suitability_analysis_type = "謹慎型"
                        elif sum_score < 40:
                            suitability_analysis_type = "穩健型"
                        elif sum_score < 50:
                            suitability_analysis_type = "積極型"
                        else:
                            suitability_analysis_type = "冒險型"
                        # 獲取投資類型對應的投資建議
                        check_data = {
                            "suitability_analysis_type": suitability_analysis_type}
                        advice_data = dbAdvice.find(check_data)
                        # 回傳分析結果
                        answer_record_suitability_list = answer_record_suitability.split(
                            "-")
                        myReply = "本次適合性分析結果：\n"
                        # 回傳資料格式
                        myReply = "投資類型：" + suitability_analysis_type + "\n"
                        myReply += "投資建議：" + advice_data[0]["advice"] + "\n"
                        myReply += "加總分數：" + str(sum_score) + "\n"
                        myReply += "選項紀錄：" + "\n"
                        for record in answer_record_suitability_list:
                            if record != "":
                                myReply += record + "\n"
                                ans = record.split(":")
                                check_data = {
                                    "question_number": ans[0], "question_group": "Suitability_analysis"}
                                qusetion = dbQuestion.find_one(check_data)
                                # 回傳題目字串
                                myReply += "題目:" + \
                                    qusetion["description"] + "\n"
                                # 依答案選項回傳答案字串
                                myReply += "選項:"
                                if ans[1] == "1":
                                    myReply += qusetion["answer1"] + "\n"
                                elif ans[1] == "2":
                                    myReply += qusetion["answer2"] + "\n"
                                elif ans[1] == "3":
                                    myReply += qusetion["answer3"] + "\n"
                                elif ans[1] == "4":
                                    myReply += qusetion["answer4"] + "\n"
                                elif ans[1] == "5":
                                    myReply += qusetion["answer5"] + "\n"
                                else:
                                    for i in ans[1]:
                                        if i == "1":
                                            myReply += qusetion["answer1"] + "\n"
                                        elif i == "2":
                                            myReply += qusetion["answer2"] + "\n"
                                        elif i == "3":
                                            myReply += qusetion["answer3"] + "\n"
                                        elif i == "4":
                                            myReply += qusetion["answer4"] + "\n"
                                        elif i == "5":
                                            myReply += qusetion["answer5"] + "\n"
                                # 結尾分行
                                myReply += "\n"
                        # 清空請求、紀錄答案及計算分數
                        dbUserRequest.update_one({"user_id": event.source.user_id}, {"$set": {"status": "0", "question_number": "0", "score": str(
                            sum_score), "answer_record_suitability": answer_record_suitability, "suitability_analysis_type": suitability_analysis_type, "multiple_options": ""}}, upsert=True)
                        return myReply
                    # 題目代號
                    question_number = event.message.text.split(":")[
                        1].split("-")[0]
                    # 嘗試取出下列資料
                    try:
                        # 使用者答案
                        answer = event.message.text.split(":")[1].split("-")[1]
                        # 加總新的分數
                        sum_score = int(user_data[0]["score"]) + int(answer)
                        # 紀錄選取答案
                        answer_record_suitability = user_data[0]["answer_record_suitability"] + \
                            "-" + question_number + ":" + answer
                    # 取出資料失敗表示答案不是"ans:1-1"格式, 如:"ans:[確定]"
                    except:
                        pass
                    # 檢查該問題是否已經回答過
                    record_list = []
                    record_data = user_data[0]["answer_record_suitability"].split(
                        "-")
                    for record in record_data:
                        # 如果暫存結果內存在相同題號
                        if record.split(":")[0] == question_number:
                            # 設定警告訊息
                            myReply = "不可重複回答"
                            # 傳送訊息給使用者
                            line_bot_api.reply_message(
                                event.reply_token,
                                TextSendMessage(text=myReply)
                            )
                            return
                    # 獲取當前題目
                    check_data = {"question_number": question_number,
                                  "question_group": "Suitability_analysis"}
                    qusetion = dbQuestion.find_one(check_data)
                    # 如果當前題目不是最後一題且是單選題
                    if qusetion["final_question"] != "1" and qusetion["question_type"] == "Suitability_analysis":
                        # 更換題目、紀錄答案及計算分數
                        dbUserRequest.update_one({"user_id": event.source.user_id}, {"$set": {"status": "Suitability_analysis", "question_number": str(
                            int(question_number)+1), "score": str(sum_score), "answer_record_suitability": answer_record_suitability}}, upsert=True)
                        # 回傳適合性分析題目
                        myReply = Suitability_analysis(
                            event.source.user_id).content()
                        line_bot_api.reply_message(
                            event.reply_token,
                            myReply
                        )
                        return
                # 如果當前題目是最後一題且是單選題
                    elif qusetion["final_question"] == "1" and qusetion["question_type"] == "Suitability_analysis":
                        # 進行最後一題總結
                        myReply = Suitability_analysis_final_question(
                            sum_score, answer_record_suitability)
                    # 如果當前題目是複選題
                    elif qusetion["question_type"] == "Suitability_analysis_multiple":
                        # 如果使用者點選確定之外的選項
                        if "[確定]" not in event.message.text:
                            # 如果答案還沒選過
                            if answer not in user_data[0]["multiple_options"]:
                                # 添加複選答案
                                multiple_options = user_data[0]["multiple_options"] + answer
                            # 如果答案已經選過
                            else:
                                # 刪除複選答案
                                multiple_options = user_data[0]["multiple_options"].replace(
                                    answer, "")
                            # 回傳已選擇的複選答案提示
                            myReply = "已選擇：" + multiple_options
                            # 暫存答案
                            dbUserRequest.update_one({"user_id": event.source.user_id}, {"$set": {
                                "status": "Suitability_analysis", "multiple_options": multiple_options}}, upsert=True)
                        # 如果使用者點選確定
                        else:
                            # 檢查是否有暫存複選題選項
                            check_data = {"user_id": event.source.user_id}
                            check_options = dbUserRequest.find_one(check_data)
                            # 如果複選題選項不為空
                            if check_options["multiple_options"] != "":
                                # 紀錄選取答案
                                answer_record_suitability = user_data[0]["answer_record_suitability"] + \
                                    "-" + question_number + ":" + \
                                    user_data[0]["multiple_options"]
                                # 計算複選答案總分數
                                sub_score = 0
                                for i in range(len(user_data[0]["multiple_options"])):
                                    sub_score += int(user_data[0]
                                                     ["multiple_options"][i])
                                # 添加複選答案總分數
                                sum_score = int(
                                    user_data[0]["score"]) + sub_score
                                # 如果當前題目不是最後一題
                                if qusetion["final_question"] != "1":
                                    # 更換題目、紀錄答案及計算分數
                                    dbUserRequest.update_one({"user_id": event.source.user_id}, {"$set": {"status": "Suitability_analysis", "question_number": str(int(
                                        question_number)+1), "score": str(sum_score), "answer_record_suitability": answer_record_suitability, "multiple_options": ""}}, upsert=True)
                                    # 回傳適合性分析題目
                                    myReply = Suitability_analysis(
                                        event.source.user_id).content()
                                    line_bot_api.reply_message(
                                        event.reply_token,
                                        myReply
                                    )
                                    return
                                # 如果當前題目是最後一題
                                else:
                                    # 進行最後一題總結
                                    myReply = Suitability_analysis_final_question(
                                        sum_score, answer_record_suitability)
                            # 如果複選題選項為空
                            else:
                                myReply = "請選擇至少一項複選題選項"
                
                # 如果使用者正在進行汽車保險規劃
                elif user_data.count() != 0 and user_data[0]["status"] == "Car_insurance_planning":
                    # 最後一題總結函式
                    def Car_insurance_planning_final_question(answer_record_car_insurance):
                        # 初始化選項計數器
                        A_count = 0
                        B_count = 0
                        C_count = 0
                        D_count = 0
                        E_count = 0
                        # 分割每題題號和選項
                        answer_record_list = answer_record_car_insurance.split(
                            "-")
                        for answer_record in answer_record_list:
                            # 如果該選項存在於分割後的字串裡
                            if "A" in answer_record:
                                # 該選項計數器遞增
                                A_count += 1
                            elif "B" in answer_record:
                                B_count += 1
                            elif "C" in answer_record:
                                C_count += 1
                            elif "D" in answer_record:
                                D_count += 1
                            elif "E" in answer_record:
                                E_count += 1
                        # 取出所有車險種類
                        car_insurance_list = dbCar_insurance.find()
                        for car_insurance in car_insurance_list:
                            # 如果五個計數器的值均大於車險底值
                            if A_count >= int(car_insurance["A_count"]) and B_count >= int(car_insurance["B_count"]) and C_count >= int(car_insurance["C_count"]) and D_count >= int(car_insurance["D_count"]) and E_count >= int(car_insurance["E_count"]):
                                # 存取該筆資料推薦的車險
                                insurance_type_list = car_insurance["car_insurance"].split(
                                    "-")
                                # 跳出迴圈
                                break
                        # 初始化車險險種
                        insurance_record = ""
                        # 回傳保險規劃
                        myReply = "本次汽車保險規劃結果：\n"
                        # 回傳資料格式
                        for insurance_type in insurance_type_list:
                            myReply += "車險建議：" + insurance_type + "\n"
                            insurance_record += "-" + insurance_type
                        myReply += "選項紀錄：" + "\n"
                        for record in answer_record_list:
                            if record != "":
                                myReply += record + "\n"
                                ans = record.split(":")
                                check_data = {
                                    "question_number": ans[0], "question_group": "Car_insurance_planning"}
                                qusetion = dbQuestion.find_one(check_data)
                                # 回傳題目字串
                                myReply += "題目:" + \
                                    qusetion["description"] + "\n"
                                # 依答案選項回傳答案字串
                                myReply += "選項:"
                                if ans[1] == "A":
                                    myReply += qusetion["answerA"] + "\n"
                                elif ans[1] == "B":
                                    myReply += qusetion["answerB"] + "\n"
                                elif ans[1] == "C":
                                    myReply += qusetion["answerC"] + "\n"
                                elif ans[1] == "D":
                                    myReply += qusetion["answerD"] + "\n"
                                elif ans[1] == "E":
                                    myReply += qusetion["answerE"] + "\n"
                                # 結尾分行
                                myReply += "\n"
                        # 清空請求、紀錄答案及計算分數
                        dbUserRequest.update_one({"user_id": event.source.user_id}, {"$set": {"status": "0", "question_number": "0",
                                                                                              "answer_record_car_insurance": answer_record_car_insurance, "insurance_record": insurance_record}}, upsert=True)
                        return myReply
                    # 題目代號
                    question_number = event.message.text.split(":")[
                        1].split("-")[0]
                    # 使用者答案
                    answer = event.message.text.split(":")[1].split("-")[1]
                    # 紀錄選取答案
                    answer_record_car_insurance = user_data[0]["answer_record_car_insurance"] + \
                        "-" + question_number + ":" + answer
                    # 檢查該問題是否已經回答過
                    record_list = []
                    record_data = user_data[0]["answer_record_car_insurance"].split(
                        "-")
                    for record in record_data:
                        # 如果暫存結果內存在相同題號
                        if record.split(":")[0] == question_number:
                            # 設定警告訊息
                            myReply = "不可重複回答"
                            # 傳送訊息給使用者
                            line_bot_api.reply_message(
                                event.reply_token,
                                TextSendMessage(text=myReply)
                            )
                            return
                    # 獲取當前題目
                    check_data = {"question_number": question_number,
                                  "question_group": "Car_insurance_planning"}
                    qusetion = dbQuestion.find_one(check_data)
                    # 如果當前題目不是最後一題
                    if qusetion["final_question"] != "1":
                        # 更換題目、紀錄答案及計算分數
                        dbUserRequest.update_one({"user_id": event.source.user_id}, {"$set": {"status": "Car_insurance_planning", "question_number": str(
                            int(question_number)+1), "answer_record_car_insurance": answer_record_car_insurance}}, upsert=True)
                        # 回傳汽車保險規劃題目
                        myReply = Car_insurance_planning(
                            event.source.user_id).content()
                        line_bot_api.reply_message(
                            event.reply_token,
                            myReply
                        )
                        return
                # 如果當前題目是最後一題
                    elif qusetion["final_question"] == "1":
                        # 進行最後一題總結
                        myReply = Car_insurance_planning_final_question(
                            answer_record_car_insurance)
                    # 如果當前題目是複選題

                # 如果使用者正在進行人生保險規劃1
                elif user_data.count() != 0 and user_data[0]["status"] == "Life_stage1":
                    # 最後一題總結函式
                    def Life_stage_final_question(sum_score, answer_record_life_stage):
                        if sum_score < 4:
                            life_stage1_type = "親親寶貝"
                        elif sum_score < 21:
                            life_stage1_type = "青春活力"
                        elif sum_score < 31:
                            life_stage1_type = "單身貴族"
                        elif sum_score < 41:
                            life_stage1_type = "成家立業"
                        elif sum_score < 51:
                            life_stage1_type = "為人父母"
                        else:
                            life_stage1_type = "開始退休規劃"
                        # 獲取投資類型對應的投資建議
                         # 回傳分析結果
                        answer_record_life_stage_list = answer_record_life_stage.split(
                            "-")
                        myReply = "本次適合性分析結果：\n"
                        # # 回傳資料格式
                        myReply = "人生階段:" + life_stage1_type + "\n"
                        myReply += "加總分數：" + str(sum_score) + "\n"
                        # # 清空請求、紀錄答案及計算分數
                        dbUserRequest.update_one({"user_id": event.source.user_id}, {"$set": {"status": "0", "question_number": "0", "score": str(
                            sum_score), "answer_record_life_stage": answer_record_life_stage, "life_stage1_type": life_stage1_type, "multiple_options": ""}}, upsert=True)
                        myReply += "選項紀錄：" + "\n"
                        for i in range(len(answer_record_life_stage_list)):
                            if (i > 0):
                                check_data = {"question_number": str(i),
                                              "question_group": "Life_stage1"}
                                question = dbQuestion.find_one(check_data)
                                myReply += answer_record_life_stage_list[i] + "\n"
                                myReply += "題目:" + \
                                    question['description'] + "\n"
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
                            sex = "男"
                        else:
                            sex = "女"
                        check_data = {
                            "type_name": user_data[0]["life_stage1_type"], "insurance_group": "life_stage1_result", "gender": sex}
                        question = dbInsurance.find_one(check_data)
                        myReply += question["guarantee_direction"] + "\n"
                        first_Reply = Life_stage1_result.first_time_reply(
                            check_data, myReply)
                        line_bot_api.reply_message(
                            event.reply_token,
                            FlexSendMessage(alt_text='險種按鈕',
                                            contents=first_Reply)
                        )
                        return

                    # 題目代號
                    question_number = event.message.text.split(":")[
                        1].split("-")[0]
                    # 嘗試取出下列資料
                    check_data = {"question_number": question_number,
                                  "question_group": "Life_stage1"}
                    qusetion = dbQuestion.find_one(check_data)
                    try:
                        # 使用者答案
                        answer = event.message.text.split(":")[1].split("-")[1]
                        # 加總新的分數(權重)
                        if int(answer) == 1:
                            newanswer = qusetion["answer1_count"]
                        elif int(answer) == 2:
                            newanswer = qusetion["answer2_count"]
                        elif int(answer) == 3:
                            newanswer = qusetion["answer3_count"]
                        elif int(answer) == 4:
                            newanswer = qusetion["answer4_count"]
                        elif int(answer) == 5:
                            newanswer = qusetion["answer5_count"]
                        else:
                            newanswer = qusetion["answer6_count"]
                        sum_score = int(user_data[0]["score"]) + int(newanswer)
                        # 紀錄選取答案
                        answer_record_life_stage = user_data[0]["answer_record_life_stage"] + \
                            "-" + question_number + ":" + str(answer)
                    # 取出資料失敗表示答案不是"ans:1-1"格式, 如:"ans:[確定]"
                    except:
                        pass
                    # 取得使用者性別
                    if (question_number == "2"):
                        if (answer == "1"):  # 男
                            dbUserRequest.update_one({"user_id": event.source.user_id}, {
                                                     "$set": {"gender": "1", }}, upsert=True)
                        elif (answer == "2"):  # 女
                            dbUserRequest.update_one({"user_id": event.source.user_id}, {
                                                     "$set": {"gender": "2", }}, upsert=True)
                    # 檢查該問題是否已經回答過
                    record_list = []
                    record_data = user_data[0]["answer_record_life_stage"].split(
                        "-")
                    for record in record_data:
                        # 如果暫存結果內存在相同題號
                        if record.split(":")[0] == question_number:
                            # 設定警告訊息
                            myReply = "不可重複回答"
                            # 傳送訊息給使用者
                            line_bot_api.reply_message(
                                event.reply_token,
                                TextSendMessage(text=myReply)
                            )
                            return
                    # 獲取當前題目
                    check_data = {"question_number": question_number,
                                  "question_group": "Life_stage1"}
                    qusetion = dbQuestion.find_one(check_data)
                    # 如果當前題目不是最後一題且是單選題
                    if qusetion["final_question"] != "1" and qusetion["question_type"] == "Life_stage1":
                        # 更換題目、紀錄答案及計算分數
                        dbUserRequest.update_one({"user_id": event.source.user_id}, {"$set": {"status": "Life_stage1", "question_number": str(
                            int(question_number)+1), "score": str(sum_score), "answer_record_life_stage": answer_record_life_stage}}, upsert=True)
                        # 回傳適合性分析題目
                        myReply = Life_stage1(event.source.user_id).content()
                        line_bot_api.reply_message(
                            event.reply_token,
                            myReply
                        )
                        return
                    # 如果當前題目是最後一題且是單選題
                    elif qusetion["final_question"] == "1" and qusetion["question_type"] == "Life_stage1":
                        # 進行最後一題總結
                        myReply = Life_stage_final_question(
                            sum_score, answer_record_life_stage)
                    # 如果當前題目是複選題
                    elif qusetion["question_type"] == "Life_stage1_multiple":
                        # 如果使用者點選確定之外的選項
                        if "[確定]" not in event.message.text:
                            # 使用者答案
                            answer = event.message.text.split(
                                ":")[1].split("-")[1]
                            # 加總新的分數(權重)
                            if int(answer) == 1:
                                newanswer = qusetion["answer1_count"]
                            elif int(answer) == 2:
                                newanswer = qusetion["answer2_count"]
                            elif int(answer) == 3:
                                newanswer = qusetion["answer3_count"]
                            elif int(answer) == 4:
                                newanswer = qusetion["answer4_count"]
                            elif int(answer) == 5:
                                newanswer = qusetion["answer5_count"]
                            else:
                                newanswer = qusetion["answer6_count"]
                            sum_score = int(
                                user_data[0]["score"]) + int(newanswer)

                            if answer not in user_data[0]["multiple_options"]:
                                # 添加複選答案
                                multiple_options = user_data[0]["multiple_options"] + answer
                            # 如果答案已經選過
                            else:
                                # 刪除複選答案
                                multiple_options = user_data[0]["multiple_options"].replace(
                                    answer, "")
                                sum_score = int(
                                    user_data[0]["score"]) - int(newanswer)
                            # 回傳已選擇的複選答案提示
                            myReply = "已選擇：" + multiple_options
                            # 暫存答案
                            dbUserRequest.update_one({"user_id": event.source.user_id}, {"$set": {
                                "status": "Life_stage1", "multiple_options": multiple_options, "score": str(sum_score)}}, upsert=True)
                        # 如果使用者點選確定
                        else:
                            # 紀錄選取答案
                            answer_record_life_stage = user_data[0]["answer_record_life_stage"] + \
                                "-" + question_number + ":" + \
                                user_data[0]["multiple_options"]
                            # 計算複選答案總分數
                            sub_score = 0

                            for i in range(len(user_data[0]["multiple_options"])):
                                sub_score += int(user_data[0]
                                                 ["multiple_options"][i])
                            # 添加複選答案總分數
                            sum_score = int(user_data[0]["score"]) + sub_score
                            # 如果當前題目不是最後一題
                            if qusetion["final_question"] != "1":
                                # 更換題目、紀錄答案及計算分數
                                dbUserRequest.update_one({"user_id": event.source.user_id}, {"$set": {"status": "Life_stage1", "question_number": str(
                                    int(question_number)+1), "answer_record_life_stage": answer_record_life_stage, "multiple_options": ""}}, upsert=True)
                                # 回傳適合性分析題目
                                myReply = Life_stage1(
                                    event.source.user_id).content()
                                line_bot_api.reply_message(
                                    event.reply_token,
                                    myReply
                                )
                                return
                            # 如果當前題目是最後一題
                            else:
                                # 進行最後一題總結
                                myReply = Life_stage_final_question(
                                    sum_score, answer_record_life_stage)
                
                # 如果使用者正在進行人生保險規劃2
                elif user_data.count() != 0 and user_data[0]["status"] == "Life_stage2":
                    question_number = event.message.text.split(":")[1].split("-")[0]#題號
                    answer_number = event.message.text.split(":")[1].split("-")[1]#答案選項
                    check_data = {"question_number": question_number,
                    "question_group": "Life_stage2"}
                    qusetion = dbQuestion.find_one(check_data)
                    if question_number=="1":
                        if answer_number=="1":
                            dbUserRequest.update_one({"user_id": event.source.user_id},{
                                "$set": {"age": "0-2","life_stage2_type":"親親寶貝"}}, upsert=True)
                        if answer_number=="2":
                            dbUserRequest.update_one({"user_id": event.source.user_id},{
                                "$set": {"age": "3-21","multiple_options":"1"}}, upsert=True)
                        if answer_number=="3":
                            dbUserRequest.update_one({"user_id": event.source.user_id},{
                                "$set": {"age": "22-30","multiple_options":"1"}}, upsert=True)
                        if answer_number=="4":
                            dbUserRequest.update_one({"user_id": event.source.user_id},{
                                "$set": {"age": "28-35","life_stage2_type":"成家立業"}}, upsert=True)
                        if answer_number=="5":
                            dbUserRequest.update_one({"user_id": event.source.user_id},{
                                "$set": {"age": "30-44","life_stage2_type":"為人父母"}}, upsert=True)
                        if answer_number=="6":
                            dbUserRequest.update_one({"user_id": event.source.user_id},{
                                "$set": {"age": "45-65","life_stage2_type":"開始退休規劃"}}, upsert=True)  
                        if answer_number=="7":
                            dbUserRequest.update_one({"user_id": event.source.user_id},{
                                "$set": {"age": "66+","life_stage2_type":"退休"}}, upsert=True)        
                    if question_number=="2" and qusetion["final_question"]=="1":
                        check_data = {"user_id": event.source.user_id}
                        request_data = dbUserRequest.find_one(check_data)
                        if answer_number=="1":
                            dbUserRequest.update_one({"user_id": event.source.user_id},{
                                "$set": {"gender": "男"}}, upsert=True)
                        else:
                            dbUserRequest.update_one({"user_id": event.source.user_id},{
                                "$set": {"gender": "女"}}, upsert=True)   
                        if request_data["age"]=="3-21":
                            myReply=Life_stage2.multiple_button()
                        elif request_data["age"]=="22-30":
                            myReply=Life_stage2.multiple_button2()
                        else:
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
                            return

                        line_bot_api.reply_message(
                            event.reply_token,
                            myReply
                        )
                        return
                    dbUserRequest.update_one({"user_id": event.source.user_id}, {"$set": {"question_number": str(
                                    int(question_number)+1)}}, upsert=True)
                    myReply = Life_stage2(event.source.user_id).content()
                    line_bot_api.reply_message(
                        event.reply_token,
                        myReply
                    )
                    return

                else:
                    myReply = "尚未進行任何操作"
        # 正在輸入退休財務規劃資料
        else:
            if typing_field == "asset":
                myReply = Joint_financial.content(
                    event.source.user_id, mode=joint_financial_question_mode, calculate=False, get_asset=True, data=event.message.text)
            else:
                myReply = Joint_financial.content(
                    event.source.user_id, mode=joint_financial_question_mode, data=event.message.text, mail=mail_object)
            line_bot_api.reply_message(
                event.reply_token,
                myReply
            )
            return None

        # 傳送訊息給使用者
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=myReply)
        )
        return


@handler.add(PostbackEvent)
def handle_postback(event):
    postback_data = eval(event.postback.data)
    if postback_data['group'] == "Guarantee_gap":
        myReply = Guarantee_gap.content(event.source.user_id,
                                        postback_data=postback_data)
    elif postback_data['group'] == "Joint_financial":
        myReply = Joint_financial.content(event.source.user_id,
                                          mode=joint_financial_question_mode,
                                          data=postback_data,
                                          mail=mail_object)
    else:
        myReply = None

    if myReply is None:
        myReply = TextSendMessage(text="Error")

    line_bot_api.reply_message(
        event.reply_token,
        myReply
    )
    return None


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
