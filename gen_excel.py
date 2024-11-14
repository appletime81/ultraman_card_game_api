import json
import pandas as pd
from pprint import pprint


JSON_FILE_PATH = "ultraman.json"

def load_json():
    with open(JSON_FILE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def gen_excel(data: dict):
    character_name_list = [list(sub_data.keys())[0] for sub_data in data]
    df_dict = {}
    for character_name in character_name_list:
        if character_name not in df_dict:
            df_dict[character_name] = []
        filtered_data = list(filter(lambda x: list(x.keys())[0] == character_name, data))[0]
        for level in list(filtered_data[character_name].keys()):
            for card_rarity in list(filtered_data[character_name][level].keys()):
                for card_data in filtered_data[character_name][level][card_rarity]:
                    if "PR" not in card_data["card_number"]:
                        df_dict[character_name].append(
                            {
                                "超人角色": character_name,
                                "等級": level,
                                "稀有度": card_rarity,
                                "效果": card_data["effect"],
                                "SINGLE BP": card_data["battle_power_1"] if card_data["battle_power_1"] else "無",
                                "DOUBLE BP": card_data["battle_power_2"] if card_data["battle_power_2"] else "無",
                                "TRIPLE BP": card_data["battle_power_3"] if card_data["battle_power_3"] else "無",
                                "卡片編號": card_data["card_number"],
                            }
                        )
    ret = {}
    for character_name in character_name_list:
        temp_dict_data_list = df_dict[character_name]
        temp_df_data_list = []
        for temp_dict_data in temp_dict_data_list:
            temp_df = pd.DataFrame(temp_dict_data, index=[0])
            temp_df_data_list.append(temp_df)
        ret[character_name] = pd.concat(temp_df_data_list, ignore_index=True)

    # every character's data is stored in a separate sheets
    with pd.ExcelWriter("ultraman.xlsx") as writer:
        for character_name in character_name_list:
            ret[character_name].to_excel(writer, sheet_name=character_name, index=False)


if __name__ == "__main__":
    data = load_json()
    gen_excel(data)