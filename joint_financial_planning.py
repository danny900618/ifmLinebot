""" 退休財務規劃 """
import configparser
from decimal import Decimal, ROUND_HALF_UP
from flask_mail import Mail, Message
from linebot.models import TextSendMessage, FlexSendMessage
from pymongo import MongoClient
from typing import List, Dict, Union, Text
import copy
import os
import openpyxl
import re
import shutil

from joint_financial_planning_template import base_select_module, base_question_module, setting_module, insurance_type_select_base_module, insurance_type_select_option_module, quickreply


# config 環境設定解析
config = configparser.ConfigParser()
config.read("config.ini")

# mongoDB atlas 連線
myMongoClient = MongoClient(config['connect_config']['Mongodb_atlas_URL'])

# 保金系資料庫
myMongoDb2 = myMongoClient["insurance-data"]
dbQuestion = myMongoDb2['qusetion-database']
dbUserRequest = myMongoDb2['user-request']
dbInsuranceAdvice = myMongoDb2['insurance-advice']


class Joint_financial():
    """
    class:
        Joint_financial -- Joint financial planning

        attribute:
            financial_data (dict):
                About joint financial data

        methods:
            render_template(user_id: str,
                            mode: str) -> FlexSendMessage:
                Render question template.

            record_answer(user_id: str,
                          mode: str,
                          question: str = None,
                          answer: str = None) -> bool:
                Record question answer.

            total_assets(user_data: dict,
                         year: int) -> Decimal:
                Calculate the total assets after how many years.

            calculate_result(user_id: str,
                             years: int = None) -> TextSendMessage:
                Calculate the result about user's total assets after how many years.

            send_result(user_id: str,
                        mail_object: Mail) -> TextSendMessage:
                Send the joint financial data to user's email.

            on_typing(user_id: str):
                Find on typing joint financial data or not.

            content(user_id: str,
                    calculate: bool = True,
                    get_asset: bool = False,
                    data=None,
                    mail: Mail = None):
                Start a new plan, record answer, and get result.

                When calculate is True and data is None, will start a new planning.

                When calculate is True and data is not None, will record answer and return new question template or send mail to user.

                When calculate is False ,get_asset is True, and data is None, will return template to ask user want to know asset after how many years.

                When calculate is False ,get_asset is True, and data is not None, will return template to show user's total asset after how many years.

                When calculate is False ,get_asset is False, and mail is not None, will send user's joint financial planning to his email address.

    Returns:
        [type]: [description]
    """
    financial_data = {
        "age": {
            "name": "年齡",
            "units": "歲"
        },
        "gender": {
            "name": "性別",
            "units": "性"
        },
        "kid": {
            "name": "兒女數量",
            "units": "位"
        },
        "ROI": {
            "name": "投資報酬率",
            "units": "%"
        },
        "CPI": {
            "name": "通貨膨脹率",
            "units": "%"
        },
        "investable_amount": {
            "name": "可投資金額",
            "units": "萬"
        },
        "salary": {
            "name": "年收入(薪水)",
            "units": "萬"
        },
        "income": {
            "name": "年收入(其他)",
            "units": "萬"
        },
        "cost": {
            "name": "年費用(家用)",
            "units": "萬"
        },
        "loan": {
            "name": "年費用(貸款)",
            "units": "萬"
        },
        "expenditure": {
            "name": "年費用(其他)",
            "units": "萬"
        }
    }

    @staticmethod
    def render_template(user_id: str, mode: str) -> FlexSendMessage:
        """Render question template.

        Args:
            user_id (str): event.source.user_id
            mode (str): ask question type. either question or select.

        Returns:
            FlexSendMessage: Template message
        """
        # 取得資料
        user_data = dbUserRequest.find_one(
            {"user_id": user_id, "status": "Joint_financial_planning"})
        # 製作模板
        if mode == "select":
            content = copy.deepcopy(base_select_module)
            body_content = []
            for field, field_data in Joint_financial.financial_data.items():
                # 問題、單位...
                option = copy.deepcopy(setting_module)
                option['contents'][0]['text'] = field_data['name']
                option['contents'][3]['text'] = field_data['units']
                option['contents'][5]['action']['data'] = str(
                    {"group": "Joint_financial", "question_field": field})
                # 使用者答案
                if field in user_data.keys() and user_data[field] != "":
                    if field == "gender":
                        option['contents'][2]['text'] = "男" if user_data[field] == "1" else "女"
                    else:
                        option['contents'][2]['text'] = user_data[field]
                else:
                    option['contents'][2]['text'] = " "
                body_content.append(option)
            content['body']['contents'] = body_content
        elif mode == "question":
            content = copy.deepcopy(base_question_module)
            content['hero']['contents'][0]['text'] = dbQuestion.find_one(
                {"field_name": user_data['question_number'], "question_group": "joint_financial_planning"})['description']

        return FlexSendMessage(alt_text='退休財務規劃', contents=content)

    @ staticmethod
    def record_answer(user_id: str, mode: str, question: str = None, answer: str = None) -> bool:
        """Record question answer.

        Args:
            user_id (str): event.source.user_id
            mode (str): ask question type. either question or select.
            question (str, optional): question number. Defaults to None.
            answer (str, optional): answer value. Defaults to None.

        Returns:
            bool: Is the input answer legal data?
        """
        # 開始新紀錄
        if question is None and answer is None:
            dbUserRequest.update_one({"user_id": user_id, "status": "Joint_financial_planning"},
                                     {"$set": {"question_number": "1" if mode == "select" else "age", "age": "", "gender": "", "kid": "", "ROI": "", "CPI": "", "investable_amount": "", "salary": "", "income": "", "cost": "", "loan": "", "expenditure": "", "email": ""}}, upsert=True)
        # 設定輸入欄位
        elif question:
            dbUserRequest.update_one({"user_id": user_id, "status": "Joint_financial_planning"},
                                     {"$set": {"question_number": question}}, upsert=True)
        # 設定欄位值
        elif answer:
            user_data = dbUserRequest.find_one(
                {"user_id": user_id, "status": "Joint_financial_planning"})
            # 判斷值是否合法
            if user_data['question_number'] == "age":
                input_data = re.compile(r'\d\d?').search(answer).group()
            elif user_data['question_number'] == "email":
                input_data = re.compile(
                    r'\w+\@\w+\.\w+').search(answer).group()
            elif user_data['question_number'] == "gender":
                if re.compile(r'[男]+[姓]?').search(answer) is not None or (re.compile(r'\d?').search(answer) is not None and re.compile(r'\d?').search(answer).group() == "1"):
                    input_data = "1"
                elif re.compile(r'[女]+[姓]?').search(answer) is not None or (re.compile(r'\d?').search(answer) is not None and re.compile(r'\d?').search(answer).group() == "2"):
                    input_data = "2"
                else:
                    input_data = None
            elif user_data['question_number'] == "kid":
                input_data = re.compile(
                    r'\d?[位]?').search(answer).group()
            else:
                input_data = re.compile(r'\d+\.?\d*').search(answer).group()

            # 如果不合法
            if input_data is '':
                return False
            # 如果合法
            else:
                if mode == "select":
                    # 確認全部資料皆輸入完成
                    input_complete = "0"
                    for data_field in Joint_financial.financial_data.keys():
                        # 因為現在輸入的資料尚未上傳 所以判斷除了現在上傳欄位以外的所有值
                        if user_data[data_field] == "" and data_field != user_data['question_number']:
                            input_complete = "1"
                    # 如果輸入完成 但沒有使用者信箱 且沒有正在輸入信箱
                    if input_complete == "0" and user_data['email'] == "" and user_data['question_number'] != "email":
                        input_complete = "email"
                    dbUserRequest.update_one({"user_id": user_id, "status": "Joint_financial_planning"},
                                             {"$set": {"question_number": input_complete, user_data['question_number']: str(input_data)}}, upsert=True)
                elif mode == "question":
                    now_question = dbQuestion.find_one(
                        {"field_name": user_data['question_number'], "question_group": "joint_financial_planning"})
                    if now_question['final_question'] == "1":
                        dbUserRequest.update_one({"user_id": user_id, "status": "Joint_financial_planning"},
                                                 {"$set": {"question_number": "0", user_data['question_number']: str(input_data)}}, upsert=True)
                    else:
                        next_question = dbQuestion.find_one(
                            {"question_number": str(int(now_question['question_number'])+1), "question_group": "joint_financial_planning"})
                        dbUserRequest.update_one({"user_id": user_id, "status": "Joint_financial_planning"},
                                                 {"$set": {"question_number": next_question['field_name'], user_data['question_number']: str(input_data)}}, upsert=True)
                return True

    @staticmethod
    def total_assets(user_data: dict, year: int) -> Decimal:
        """Calculate the total assets after how many years.

        Args:
            user_data (dict): about user's data.
            year (int): after how many years

        Returns:
            Decimal: total assets
        """
        # 通貨膨脹指數 = (1 + <通貨膨脹指數>) ^ <年數>
        now_cpi = (
            (Decimal("1") + Decimal(user_data['CPI'])/Decimal("100"))**year)
        # 去年總資產
        if year == 0:
            last_year_asset = Decimal(
                user_data['investable_amount'])*Decimal("10000")
        else:
            last_year_asset = Joint_financial.total_assets(user_data, year-1)
        # 年收入 = ( <薪資年收入> + <其他年收入> + <去年累績結餘> * <投資年報酬率> )
        annual_income = (Decimal(user_data['salary'])*Decimal("10000") +
                         Decimal(user_data['income'])*Decimal("10000") +
                         (last_year_asset * Decimal(user_data['ROI']) // Decimal("100"))).quantize(Decimal('.00'), ROUND_HALF_UP)
        # 年費用 = ( <家用年費用> + <其他年費用> ) * <通貨膨脹指數> + <貸款年費用>
        annual_expenditure = ((Decimal(user_data['cost']) * Decimal("10000") +
                               Decimal(user_data['expenditure']) * Decimal("10000")) * now_cpi +
                              Decimal(user_data['loan'])*Decimal("10000")).quantize(Decimal('.00'), ROUND_HALF_UP)
        # <累績結餘> = <去年累積結餘> + <年收入> - <年費用>
        now_asset = (last_year_asset + annual_income - annual_expenditure)
        return now_asset

    @staticmethod
    def calculate_result(user_id: str, years: int = None) -> TextSendMessage:
        """Calculate the result about user's total assets after how many years.

        Args:
            user_id (str): event.source.user_id
            years (int, optional): after how many years. Defaults to None.

        Returns:
            TextSendMessage: calculate result
        """
        # 詢問年數
        if years is None:
            result = dbUserRequest.update_one({"user_id": user_id, "status": "Joint_financial_planning"},
                                              {"$set": {"question_number": "asset"}}, upsert=True)
            return TextSendMessage(text="請問您想知道多少年之後的總資產？")
        # 開始計算
        user_data = dbUserRequest.find_one(
            {"user_id": user_id, "status": "Joint_financial_planning"})
        user_financial_data = {key: value
                               for key, value in user_data.items()
                               if key in Joint_financial.financial_data.keys()}
        result = dbUserRequest.update_one({"user_id": user_id, "status": "Joint_financial_planning"},
                                          {"$set": {"question_number": "0"}}, upsert=True)
        total_asset = (Joint_financial.total_assets(user_financial_data,
                       years) / Decimal("10000")).quantize(Decimal('.00'), ROUND_HALF_UP)

        return TextSendMessage(text="您 {} 年後的總資產為 {} 萬元".format(years, total_asset))

    @staticmethod
    def send_result(user_id: str, mail_instance: Mail, send_mail: bool, select_type_num: int = None) -> List[TextSendMessage]:
        """Send the joint financial data to user's email.

        Args:
            user_id (str): event.source.user_id
            mail_instance (Mail): `flask_mail.Mail` object
            send_mail (bool): send mail
            select_type_num (int, optional): select insurance type number. Defaults to None.

        Returns:
            List[TextSendMessage]: the message to user
        """
        user_data = dbUserRequest.find_one(
            {"user_id": user_id, "status": "Joint_financial_planning"})

        if send_mail:
            # 複製檔案
            original_sheet = r'./joint_financial.xlsx'
            user_sheet = f'{user_id}.xlsx'
            shutil.copyfile(original_sheet, user_sheet)

            # 編輯檔案
            xls_col = ['B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O',
                       'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', 'AA', 'AB', 'AC', 'AD', 'AE', 'AF', 'AG', 'AH', 'AI', 'AJ', 'AK']
            wb = openpyxl.load_workbook(user_sheet)
            sheet = wb['主資料表']
            sheet['B1'] = Decimal(user_data['ROI'])/100
            sheet['B2'] = Decimal(user_data['CPI'])/100
            sheet['B3'] = Decimal(user_data['investable_amount']) * 10000
            sheet['B15'] = Decimal(user_data['age'])
            for index, col in enumerate(xls_col):
                if (index + int(user_data['age'])) < 65:
                    sheet[col+'18'] = Decimal(user_data['salary']) * 10000
                sheet[col+'19'] = Decimal(user_data['income']) * 10000
                sheet[col+'23'] = Decimal(user_data['cost']) * 10000
                sheet[col+'24'] = Decimal(user_data['expenditure']) * 10000
                sheet[col+'25'] = Decimal(user_data['loan']) * 10000
            wb.save(user_sheet)

            # 寄信
            msg = Message(
                "退休財務規劃", recipients=[user_data['email']], body="財務規劃資料")

            with open(user_sheet, "rb") as fp:
                msg.attach("financial.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           fp.read())
                # .xls -> application/vnd.ms-excel
                # .xlsx -> application/vnd.openxmlformats-officedocument.spreadsheetml.sheet

            mail_instance.send(msg)

            if os.path.isfile(os.path.join(os.getcwd(), user_sheet)):
                os.remove(os.path.join(os.getcwd(), user_sheet))

        ''' 保險推薦 '''
        match_data = dbInsuranceAdvice.find({"insurance_group": "joint_financial_planning", "lower_age": {
                                            '$lte': int(user_data['age'])}, "gender": user_data['gender']}).sort([("lower_age", -1)])

        match_list = []
        # 第一次篩選 - 年齡
        if match_data.count() > 1:
            for match_row_data in match_data:
                if "upper_age" in match_row_data.keys() and match_row_data["upper_age"] >= int(user_data['age']):
                    match_list.append(match_row_data)
                elif "upper_age" not in match_row_data.keys():
                    match_list.append(match_row_data)
        elif match_data.count() == 1:
            match_list.append(match_data[0])

        message_list = [TextSendMessage(text="已寄出規劃結果至您的電子郵件信箱")]

        # 沒有結果
        if len(match_list) == 0:
            return message_list.append(TextSendMessage(text="沒有適合您的推薦險種"))
        # 一個結果
        elif len(match_list) == 1:
            type_name = "類型：\n{}".format(match_list[0]["type_name"])
            insurance_list = "建議險種：\n{}".format(
                match_list[0]["insurance_list"].replace(",", "、"))
            guarantee_direction = "保險方向：\n{}".format(
                match_list[0]["guarantee_direction"])
            instruction = "說明：\n{}\n{}\n{}\n{}".format(
                match_list[0]["instruction_a"], match_list[0]["instruction_b"], match_list[0]["instruction_c"], match_list[0]["instruction_d"])
            if match_list[0]["instruction_e"] != "":
                instruction += "\n{}".format(
                    match_list[0]["instruction_e"])
            cost = "保費：\n{} 元".format(match_list[0]["cost"])
            return_text = f"{type_name}\n\n{insurance_list}\n\n{guarantee_direction}\n\n{cost}\n\n{instruction}"

            return message_list.append(TextSendMessage(text=return_text))
        # 多個結果
        else:
            # 第二次篩選 - 是否結婚以及兒女數量
            match_list_2 = []
            for match_row_data in match_list:
                if "merry" in match_row_data.keys() and match_row_data['merry'] == bool(user_data["merry"]) and match_row_data['kid'] == bool(user_data['kid']):
                    match_list_2.append(match_row_data)
                elif "merry" not in match_row_data.keys():
                    match_list_2.append(match_row_data)

            # 沒有結果
            if len(match_list_2) == 0:
                return message_list.append(TextSendMessage(text="沒有適合您的推薦險種"))
            # 一個結果
            elif len(match_list_2) == 1:
                type_name = "類型：\n{}".format(match_list_2[0]["type_name"])
                insurance_list = "建議險種：\n{}".format(
                    match_list_2[0]["insurance_list"].replace(",", "、"))
                guarantee_direction = "保險方向：\n{}".format(
                    match_list_2[0]["guarantee_direction"])
                instruction = "說明：\n{}\n{}\n{}\n{}".format(
                    match_list_2[0]["instruction_a"], match_list_2[0]["instruction_b"], match_list_2[0]["instruction_c"], match_list_2[0]["instruction_d"])
                if match_list_2[0]["instruction_e"] != "":
                    instruction += "\n{}".format(
                        match_list_2[0]["instruction_e"])
                cost = "保費：\n{} 元".format(match_list_2[0]["cost"])
                return_text = f"{type_name}\n\n{insurance_list}\n\n{guarantee_direction}\n\n{cost}\n\n{instruction}"

                return message_list.append(TextSendMessage(text=return_text))
            # 多個結果
            else:
                # 提供選項
                if select_type_num is None:
                    insurance_type_select_base_module, insurance_type_select_option_module
                    content = copy.deepcopy(insurance_type_select_base_module)
                    body_content = []

                    for index, data in enumerate(match_list_2):
                        option = copy.deepcopy(
                            insurance_type_select_option_module)
                        option["action"]["label"] = data["type_name"]
                        option["action"]["data"] = str(
                            {"group": "Joint_financial", "option": str(index)})
                        option["action"]["displayText"] = data["type_name"]
                        body_content.append(option)

                    content["body"]["contents"] = body_content
                    message_list.append(FlexSendMessage(
                        alt_text="請選擇您的類別", contents=content))

                    return message_list
                else:
                    data = match_list_2[select_type_num]
                    # for index, data in enumerate(match_list_2):
                    type_name = "類型：\n{}".format(
                        data["type_name"])
                    insurance_list = "建議險種：\n{}".format(
                        data["insurance_list"].replace(",", "、"))
                    guarantee_direction = "保險方向：\n{}".format(
                        data["guarantee_direction"])
                    instruction = "說明：\n{}\n{}\n{}\n{}".format(
                        data["instruction_a"], data["instruction_b"], data["instruction_c"], data["instruction_d"])
                    if data["instruction_e"] != "":
                        instruction += "\n{}".format(
                            data["instruction_e"])
                    cost = "保費：\n{} 元".format(data["cost"])
                    return_text = f"{type_name}\n\n{insurance_list}\n\n{guarantee_direction}\n\n{cost}\n\n{instruction}"
                    return TextSendMessage(text=return_text)

    @staticmethod
    def on_typing(user_id: str):
        """Find on typing joint financial data or not.

        Args:
            user_id (str): event.source.user_id

        Returns:
            False: Not on typing joint financial data
            str: joint financial field name
        """
        user_data = dbUserRequest.find_one(
            {"user_id": user_id, "status": "Joint_financial_planning"})
        if user_data is None or user_data['question_number'] == "0" or user_data['question_number'] == "1":
            return False
        return user_data['question_number']

    @ staticmethod
    def content(user_id: str, mode: str = "select", calculate: bool = True, get_asset: bool = False, data: Union[str, Dict] = None, mail: Mail = None):
        """Start a new plan, record answer, and get result.

        Args:
            user_id (str): event.source.user_id.
            mode (str, optional): ask question type. either question or select. Defaults to "select".
            calculate (bool, optional): want to start a new one or record answer? Defaults to True.
            get_asset (bool, optional): want to get how many years later the assets? Defaults to False.
            data (Union[str, Dict], optional): dict -> question number; str -> answer value. Defaults to None.
            mail (Mail, optional): `flask_mail.Mail` instance for send mail. Defaults to None.

        Returns:
            TextSendMessage: The message return to user
            FlexSendMessage: The message return to user
        """
        if calculate:
            # 開始新規劃
            if data is None:
                Joint_financial.record_answer(user_id, mode=mode)
            else:
                # 設定輸入欄位 select
                if isinstance(data, dict) and "question_field" in data.keys():
                    Joint_financial.record_answer(user_id,
                                                  mode=mode,
                                                  question=data['question_field'])
                    field_name = Joint_financial.financial_data[data['question_field']]['name']
                    return TextSendMessage(text=f"請輸入 {field_name}")
                # 輸入欄位值 select, question
                elif isinstance(data, dict) and "option" in data.keys():
                    return Joint_financial.send_result(user_id, mail, send_mail=False, select_type_num=int(data["option"]))
                # 輸入欄位值 select, question
                elif isinstance(data, str):
                    # 如果為不合法的值
                    if not Joint_financial.record_answer(user_id, mode=mode, answer=data):
                        return TextSendMessage(text="輸入值不合法")

        # 找紀錄
        result = dbUserRequest.find_one(
            {"user_id": user_id, "status": "Joint_financial_planning"})
        # 如果沒有紀錄
        if result is None:
            Joint_financial.record_answer(user_id, mode=mode)
            return Joint_financial.render_template(user_id, mode=mode)
        # 如果有紀錄
        # 如果紀錄已做完但尚未輸入信箱
        if result['question_number'] == 'email' and mode == "select":
            return TextSendMessage(text="請輸入您的信箱")
        # 如果紀錄已做完且已輸入信箱
        elif result['question_number'] == '0':
            # 開始詢問總資產
            if get_asset:
                return Joint_financial.calculate_result(user_id)
            # 寄出退休財務規劃資料
            return Joint_financial.send_result(user_id, mail, send_mail=True)
        # 如果開始詢問總資產且輸入年數
        elif result['question_number'] == 'asset' and data is not None:
            years = re.compile(r"\d\d?").search(data)
            if years is None:
                return TextSendMessage(text="輸入值不合法")
            return Joint_financial.calculate_result(user_id, int(years.group()))
        # 如果紀錄未做完
        return Joint_financial.render_template(user_id, mode=mode)
