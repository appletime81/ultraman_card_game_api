import httpx
import json
from pprint import pprint

URL = "https://api.ultraman-cardgame.com/api/v1/tw/cards?page=page_num&per_page=15&feature=ultra_hero"
TOTAL_PAGE = 10


def get_data():
    character_name_list = []
    for i in range(1, TOTAL_PAGE + 1):
        url = URL.replace("page_num", str(i))
        response = httpx.get(url)
        datas = response.json()["data"]
        for data in datas:
            character_name_list.append(data["detail"]["character_name"])
    return list(set(character_name_list))


def get_detail(character_name_list: list):
    """
    {
        "傑洛": {
            "1" : {
                "rarity": [
                    "U": [
                            {
                                effect: "str",
                                "card_number": "str",
                            }
                    ]
                ]
            }
        }
    }


    """
    datas = list()
    for i in range(1, TOTAL_PAGE + 1):
        url = URL.replace("page_num", str(i))
        response = httpx.get(url)
        temp_datas = response.json()["data"]
        datas += temp_datas

    card_rarity_list = ["C", "U", "R", "RR", "RRR"]
    level_List = ["1", "2", "3"]
    ret = list()
    for character_name in character_name_list:
        temp_dict = {character_name: {}}
        for card_rarity in card_rarity_list:
            for level in level_List:
                filtered_datas = list(
                    filter(
                        lambda x: x["detail"]["character_name"] == character_name
                        and x["rarity"]["description"] == card_rarity
                        and x["level"] == level,
                        datas,
                    )
                )
                if filtered_datas:
                    for filtered_data in filtered_datas:
                        if level not in temp_dict[character_name]:
                            temp_dict[character_name][level] = {}
                        if card_rarity not in temp_dict[character_name][level]:
                            temp_dict[character_name][level][card_rarity] = []

                        temp_dict[character_name][level][card_rarity].append(
                            {
                                "effect": filtered_data["detail"]["effect"],
                                "card_number": filtered_data["number"],
                                "battle_power_1": filtered_data["battle_power_1"],
                                "battle_power_2": filtered_data["battle_power_2"],
                                "battle_power_3": filtered_data["battle_power_3"],
                            }
                        )
        ret.append(temp_dict)
    return ret


if __name__ == "__main__":
    character_name_list = get_data()
    ret = get_detail(character_name_list)

    # save json
    with open("ultraman.json", "w", encoding="utf-8") as f:
        json.dump(ret, f, ensure_ascii=False, indent=4)
