""" 保障缺口分析 """
import configparser
from linebot.models import TextSendMessage, FlexSendMessage, MessageAction
from pymongo import MongoClient
import copy

from guarantee_gap_template import base_template, title_module, options_module, result_module, insurance_advice_module, quickreply


# config 環境設定解析
config = configparser.ConfigParser()
config.read("config.ini")

# mongoDB atlas 連線
myMongoClient = MongoClient(config['connect_config']['Mongodb_atlas_URL'])

# 保金系資料庫
myMongoDb2 = myMongoClient["insurance-data"]
dbUserRequest = myMongoDb2['user-request']
dbQuestion = myMongoDb2['qusetion-database']
dbInsuranceAdvice = myMongoDb2['insurance-advice']


class Guarantee_gap():
    """
    class:
        Guarantee_gap -- Guarantee gap analysis

        method:
            render_question_template(user_id: str) -> FlexSendMessage:
                Render question template.

            render_result_template(user_id: str) -> [FlexSendMessage]:
                Render result template.

            record_answer(user_id: str,
                          question_number: str = None,
                          answer_number: str = None) -> None:
                Record user's answer.

            content(user_id: str,
                    calculate: bool = True,
                    postback_data: dict = None):
                Start a new analysis, record answer, and get result.

                When calculate is True and postback_data is None, will start a new analysis.

                When calculate is True and postback_data is not None, will record user's data and return next question or analysis result.

                When calculate is False, will according user's answer to return the question or analysis result.

    Returns:
        [FlexSendMessage]: Message return to the user
    """
    @staticmethod
    def render_question_template(user_id: str) -> FlexSendMessage:
        """Render question template

        Args:
            user_id (str): event.source.user_id

        Returns:
            FlexSendMessage: Message returned to the user
        """
        question_number = dbUserRequest.find_one(
            {"user_id": user_id, "status": "Guarantee_gap_analysis"})['question_number']

        content = copy.deepcopy(base_template)
        # 取得問題
        question = dbQuestion.find_one(
            {"question_group": "guarantee_gap_analysis", "question_number": question_number})
        # 製作問題模板
        content["hero"] = copy.deepcopy(title_module)
        content['hero']['contents'][0]['text'] = question['description']
        body_content = []
        for ans_num in range(int(question['answer_sum'])):
            option = copy.deepcopy(options_module)
            option['action']['label'] = question['answer' + str(ans_num + 1)]
            option['action']['data'] = str({
                "group": "Guarantee_gap", "question_number": question_number, "answer_number": str(ans_num + 1)})
            option['action']['displayText'] = question['answer' +
                                                       str(ans_num + 1)]
            body_content.append(option)
        content['body']['contents'] = body_content

        return FlexSendMessage(alt_text='保障缺口計算', contents=content)

    @staticmethod
    def render_result_template(user_id: str) -> [FlexSendMessage]:
        """Render result template

        Args:
            user_id (str): event.source.user_id

        Returns:
            [FlexSendMessage]: The message return to user
        """
        ''' ----- 保障缺口 ----- '''
        # 取得答案
        result = dbUserRequest.find_one({"user_id": user_id, "status": "Guarantee_gap_analysis"})[
            'answer_record_guarantee_gap']
        question_and_answer = {qa.split(':')[0]: qa.split(':')[1]
                               for qa in result.split('-') if qa != ""}
        question_and_value = {}

        # 取得答案值
        for question_number, answer_number in question_and_answer.items():
            raw_data = dbQuestion.find_one(
                {"question_group": "guarantee_gap_analysis", "question_number": question_number})
            if answer_number != '0' and raw_data['question_type'] == "guarantee_gap_analysis_answer":
                question_and_value[question_number] = int(
                    raw_data[f"answer{answer_number}_value"])
            else:
                question_and_value[question_number] = int(answer_number)

        # 現金需求 = 小孩數量 * 小孩花費 + 房屋貸款 + 房租 * 租屋年數 + 喪葬費用 + 借款 + 應急費用
        cash_requirement = question_and_value['3'] * question_and_value['5'] + question_and_value['6'] + question_and_value['7'] * \
            question_and_value['8'] + question_and_value['9'] + \
            question_and_value['10'] + question_and_value['11']
        # 生活費用 = 配偶收入 - 家庭開銷 * 準備年數 + 其它年收
        cost_of_living = question_and_value['2'] - question_and_value['12'] * \
            question_and_value['13'] + question_and_value['14']
        if cost_of_living < 0:
            cost_of_living = 0
        # 已準備 = 身故保障 + 銀行存款 + 投資金額
        ready = question_and_value['15'] + \
            question_and_value['16'] + question_and_value['17']
        # 保障缺口 = 現金需求 + 生活費用 - 已準備
        guarantee_gap = cash_requirement + cost_of_living - ready
        if guarantee_gap < 0:
            guarantee_gap = 0

        # 製作模板
        content = copy.deepcopy(base_template)
        content["hero"] = copy.deepcopy(title_module)
        content['hero']['contents'][0]['text'] = "保障缺口"

        body_content = []
        cash_requirement_result = copy.deepcopy(result_module)
        cash_requirement_result['contents'][1]['text'] = "現金需求"
        cash_requirement_result['contents'][2]['text'] = str(cash_requirement)
        body_content.append(cash_requirement_result)

        cost_of_living_result = copy.deepcopy(result_module)
        cost_of_living_result['contents'][0]['text'] = "+"
        cost_of_living_result['contents'][1]['text'] = "生活費用"
        cost_of_living_result['contents'][2]['text'] = str(cost_of_living)
        body_content.append(cost_of_living_result)

        ready_result = copy.deepcopy(result_module)
        ready_result['contents'][0]['text'] = "-"
        ready_result['contents'][1]['text'] = "已準備"
        ready_result['contents'][2]['text'] = str(ready)
        body_content.append(ready_result)

        body_content.append({"type": "separator"})

        guarantee_gap_result = copy.deepcopy(result_module)
        guarantee_gap_result['contents'][1]['text'] = "保障缺口"
        guarantee_gap_result['contents'][2]['text'] = str(guarantee_gap)
        body_content.append(guarantee_gap_result)

        content['body']['contents'] = body_content
        ''' ----- 推薦險種 ----- '''
        raw = dbInsuranceAdvice.find({"insurance_group": "insurance_type_and_cost", "lower_age": {'$lte': question_and_value['18']}, "lower_guarantee_gap": {
            "$lte": int(guarantee_gap)}}).sort([("lower_age", -1), ("lower_guarantee_gap", -1)]).limit(1)[0]

        insurance = {"life_insurance": "壽險", "term_life_insurance": "定期壽險", "medical_insurance": "醫療險", "cancer_insurance": "癌症險",
                     "major_injury_insurance": "重大傷病險", "accident_insurance": "意外險", "disability_insurance": "失能險"}

        # 製作模板
        content_2 = copy.deepcopy(base_template)
        content_2["hero"] = copy.deepcopy(title_module)
        content_2['hero']['contents'][0]['text'] = "推薦險種"
        body_content_2 = []

        group_module = copy.deepcopy(insurance_advice_module)
        group_module['contents'].pop(2)
        group_module['contents'][0]['flex'] = 1
        group_module['contents'][0]['text'] = "類型"
        group_module['contents'][1]['flex'] = 3
        group_module['contents'][1]['text'] = raw['group']
        body_content_2.append(group_module)

        age_module = copy.deepcopy(insurance_advice_module)
        age_module['contents'][0]['text'] = "年齡群組"
        age_module['contents'][1]['text'] = str(raw['lower_age'])
        age_module['contents'][2]['text'] = "歲"
        if "upper_age" in raw:
            age_module['contents'][1]['text'] += " ~ " + str(raw['upper_age'])
        else:
            age_module['contents'][2]['text'] += "以上"
        body_content_2.append(age_module)

        guarantee_gap_module = copy.deepcopy(insurance_advice_module)
        guarantee_gap_module['contents'][0]['text'] = "保障缺口"
        guarantee_gap_module['contents'][1]['text'] = str(
            raw['lower_guarantee_gap'])
        guarantee_gap_module['contents'][2]['text'] = "萬"
        if "upper_guarantee_gap" in raw:
            guarantee_gap_module['contents'][1]['text'] += " ~ " + \
                str(raw['upper_guarantee_gap'])
        else:
            guarantee_gap_module['contents'][2]['text'] += "以上"
        body_content_2.append(guarantee_gap_module)

        for index, value in raw.items():
            if index in insurance.keys():
                insurance_item = copy.deepcopy(insurance_advice_module)
                insurance_item['contents'][0]['text'] = insurance[index]
                insurance_item['contents'][1]['text'] = str(value)
                insurance_item['contents'][2]['text'] = "萬"
                if "status" in raw:
                    insurance_item['contents'][2]['text'] += "以上" if raw['status'] == "up" else "以下"
                body_content_2.append(insurance_item)

        content_2['body']['contents'] = body_content_2
        ''' ----- 保險說明 ----- '''
        match_data = dbInsuranceAdvice.find(
            {"insurance_group": "insurance_detail", "lower_age": {"$lte": question_and_value['18']}, "upper_age": {"$gte": question_and_value['18']}})
        if match_data.count() > 1:
            for match_row_data in match_data:
                if match_row_data["merry"] == bool(question_and_value['1'] - 1) and match_row_data["kid"] == bool(question_and_value['3']):
                    raw = match_row_data
                    break
                else:
                    raw = None
        elif match_data.count() == 1:
            raw = match_data[0]
        else:
            raw = None

        if raw is not None:
            type_name = "類型：\n{}".format(raw['type_name'])
            description = "描述：\n{}".format(raw['description'])
            insurance_list = "建議保險項目：\n{}".format(
                raw['insurance_list'].replace(',', '、'))
            cost = "保費：\n{} 元".format(raw['cost'])
            instruction = "說明：\n{}\n{}\n{}\n{}\n{}".format(
                raw['instruction_a'], raw['instruction_b'], raw['instruction_c'], raw['instruction_d'], raw['instruction_e'])
            return_text = f"{type_name}\n\n{description}\n\n{insurance_list}\n\n{cost}\n\n{instruction}"

            return [FlexSendMessage(alt_text='保障缺口計算', contents=content), FlexSendMessage(alt_text="推薦險種", contents=content_2), TextSendMessage(text=return_text)]
        return [FlexSendMessage(alt_text='保障缺口計算', contents=content), FlexSendMessage(alt_text="推薦險種", contents=content_2)]

    @ staticmethod
    def record_answer(user_id: str, question_number: str = None, answer_number: str = None) -> None:
        """Record user's answer

        Args:
            user_id (str): event.source.user_id
            question_number (str, optional): question number. Defaults to None.
            answer_number (str, optional): answer option number. Defaults to None.
        """
        # 開始新紀錄
        if question_number is None or answer_number is None:
            dbUserRequest.update_one({"user_id": user_id, "status": "Guarantee_gap_analysis"}, {
                                     "$set": {"question_number": '1', "answer_record_guarantee_gap": ''}}, upsert=True)
        else:
            # 取得使用者紀錄
            user_data = dbUserRequest.find_one(
                {"user_id": user_id, "status": "Guarantee_gap_analysis"})
            # 如果正在回答現在的問題
            if user_data['question_number'] == question_number:
                # 取得現在回答的問題的資料
                now_question = dbQuestion.find_one(
                    {"question_group": "guarantee_gap_analysis", "question_number": question_number})

                if now_question['final_question'] == "1":
                    dbUserRequest.update_one({"user_id": user_id, "status": "Guarantee_gap_analysis"},
                                             {"$set": {"question_number": "0", "answer_record_guarantee_gap": user_data['answer_record_guarantee_gap'] + f"-{user_data['question_number']}:{answer_number}"}}, upsert=True)
                # 如果正在回答且不是正在回答最後一題 但能跳題且選了能跳的選項
                elif now_question['can_skip'] and (now_question['skip_answer'] == str(answer_number)):
                    dbUserRequest.update_one({"user_id": user_id, "status": "Guarantee_gap_analysis"},
                                             {"$set": {"question_number": str(now_question['skip_to_question']), "answer_record_guarantee_gap": user_data['answer_record_guarantee_gap'] + f"-{user_data['question_number']}:{answer_number}-{now_question['skip_answer_value']}"}}, upsert=True)
                # 如果正在回答且不是正在回答最後一題 但不能跳題或選了不能跳的選項
                else:
                    dbUserRequest.update_one({"user_id": user_id, "status": "Guarantee_gap_analysis"},
                                             {"$set": {"question_number": str(int(user_data['question_number']) + 1), "answer_record_guarantee_gap": user_data['answer_record_guarantee_gap'] + f"-{user_data['question_number']}:{answer_number}"}}, upsert=True)

    @ staticmethod
    def content(user_id: str, calculate: bool = True, postback_data: dict = None):
        """Start a new analysis, record answer, and get result.

        Args:
            user_id (str): event.source.user_id
            calculate (bool, optional): want to calculate guarantee gap? Defaults to True.
            postback_data (dict, optional): eval(event.postback.data). Defaults to None.

        Returns:
            TextSendMessage: The message return to user
            FlexSendMessage: The message return to user
        """
        # 如果要計算
        if calculate:
            # 開始新的計算
            if postback_data is None:
                Guarantee_gap.record_answer(user_id)
            # 紀錄計算結果
            else:
                Guarantee_gap.record_answer(
                    user_id, postback_data['question_number'], postback_data['answer_number'])
        # 找紀錄
        result = dbUserRequest.find_one(
            {"user_id": user_id, "status": "Guarantee_gap_analysis"})
        # 沒有紀錄
        if result is None:
            Guarantee_gap.record_answer(user_id)
            return Guarantee_gap.render_question_template("1")
        # 有紀錄且紀錄已做完
        elif result['question_number'] == '0':
            return Guarantee_gap.render_result_template(user_id)
        # 紀錄未做完
        return Guarantee_gap.render_question_template(user_id)
