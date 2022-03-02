""" 退休財務規劃 模板 """

base_select_module = {
    "type": "bubble",
    "header": {
        "type": "box",
        "layout": "vertical",
        "contents": [
            {
                "type": "text",
                "text": "退休財務規劃",
                "weight": "bold",
                "size": "xl"
            }
        ],
        "alignItems": "center"
    },
    "body": {
        "type": "box",
        "layout": "vertical",
        "contents": [],
        "spacing": "md",
        "paddingStart": "md",
        "paddingEnd": "md"
    }
}


setting_module = {
    "type": "box",
    "layout": "horizontal",
    "contents": [
        {
            "type": "text",
            "text": " ",
            "flex": 4,
            "size": "md",
            "weight": "bold",
            "align": "center",
            "gravity": "center",
            "adjustMode": "shrink-to-fit"
        },
        {
            "type": "separator"
        },
        {
            "type": "text",
            "text": " ",
            "flex": 3,
            "size": "md",
            "weight": "bold",
            "align": "center",
            "gravity": "center",
            "adjustMode": "shrink-to-fit"
        },
        {
            "type": "text",
            "text": " ",
            "flex": 1,
            "size": "md",
            "weight": "bold",
            "align": "center",
            "gravity": "center",
            "adjustMode": "shrink-to-fit"
        },
        {
            "type": "filler"
        },
        {
            "type": "button",
            "adjustMode": "shrink-to-fit",
            "action": {
                "type": "postback",
                "label": "設定",
                "data": " "
            },
            "flex": 3,
            "color": "#FF000077",
            "style": "primary",
            "height": "sm"
        }
    ],
    "paddingAll": "sm"
}


base_question_module = {
    "type": "bubble",
    "header": {
        "type": "box",
        "layout": "vertical",
        "contents": [
            {
                "type": "text",
                "text": "退休財務規劃",
                "weight": "bold",
                "size": "xl"
            }
        ],
        "alignItems": "center"
    },
    "hero": {
        "type": "box",
        "layout": "vertical",
        "contents": [
            {
                "type": "text",
                "text": " ",
                "size": "lg",
                "wrap": True
            }
        ],
        "alignItems": "center",
        "paddingStart": "xxl",
        "paddingEnd": "xxl",
        "paddingBottom": "xxl"
    }
}

insurance_type_select_base_module = {
    "type": "bubble",
    "header": {
        "type": "box",
        "layout": "vertical",
        "contents": [
            {
                "type": "text",
                "text": "退休財務規劃",
                "weight": "bold",
                "size": "xl"
            }
        ],
        "alignItems": "center"
    },
    "hero": {
        "type": "box",
        "layout": "vertical",
        "contents": [
            {
                "type": "text",
                "text": "類型選擇",
                "gravity": "center",
                "align": "center",
                "size": "lg"
            }
        ]
    },
    "body": {
        "type": "box",
        "layout": "vertical",
        "contents": [],
        "spacing": "md",
        "paddingStart": "md",
        "paddingEnd": "md"
    }
}

insurance_type_select_option_module = {
    "type": "button",
    "action": {
        "type": "postback",
        "label": "action 1",
        "data": "hello",
        "displayText": "world"
    },
    "color": "#ff000077",
    "style": "primary",
    "height": "md",
    "gravity": "center",
    "adjustMode": "shrink-to-fit"
}


quickreply = {
    "items": [
        {
            "action": {
                "label": "功能列表",
                "text": "功能列表",
                "type": "message"
            },
            "type": "action"
        },
        {
            "action": {
                "label": "適合性分析",
                "text": "適合性分析",
                "type": "message"
            },
            "type": "action"
        },
        {
            "action": {
                "label": "汽車保險規劃",
                "text": "汽車保險規劃",
                "type": "message"
            },
            "type": "action"
        },
        {
            "action": {
                "label": "人生保險規劃1",
                "text": "人生保險規劃1",
                "type": "message"
            },
            "type": "action"
        },
        {
            "action": {
                "label": "人生保險規劃2",
                "text": "人生保險規劃2",
                "type": "message"
            },
            "type": "action"
        },
        {
            "action": {
                "label": "保障缺口分析",
                "text": "保障缺口分析",
                "type": "message"
            },
            "type": "action"
        },
        {
            "action": {
                "label": "退休財務規劃",
                "text": "退休財務規劃",
                "type": "message"
            },
            "type": "action"
        }
    ]
}
