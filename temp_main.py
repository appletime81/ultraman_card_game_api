import json
import asyncio
import xlsxwriter
import httpx
import polars as pl
from pprint import pprint
from typing import List


pl.Config.set_tbl_cols(1000)
pl.Config.set_tbl_rows(1000)


async def get_all_cards_list(url: str, max_pages: int):
    all_datas = list()
    for i in range(1, max_pages + 1):
        async with httpx.AsyncClient() as client:
            response = await client.get(url.replace("page_num", str(i)))
            temp_datas = response.json()["data"]
        all_datas.extend(temp_datas)
    return all_datas


def convert_json_to_df(dict_datas: List[dict]):
    temp_all_datas = {
        "類別": list(),
        "名稱": list(),
        "等級": list(),
        "屬性": list(),
        "卡片效果": list(),
        "SINGLE BP": list(),
        "DOUBLE BP": list(),
        "TRIPLE BP": list(),
        "EX BP": list(),
        "可登場回合數": list(),
        "稀有度": list(),
        "稀有度index": list(),
        "卡片編號": list(),
    }
    rarity_index_dict = {
        "C": 0,
        "U": 1,
        "R": 2,
        "RR": 3,
        "RRR": 4,
        "PR": 5,
        "AP": 6,
        "SP": 7,
        "SSSP": 8,
        "UR": 9,
    }

    for dict_data in dict_datas:
        temp_dict_data = {
            "類別": dict_data["feature"]["description"],
            "名稱": (
                dict_data["detail"]["character_name"]
                if dict_data["detail"]["character_name"] != "-"
                else dict_data["detail"]["name"]
            ),
            "等級": int(dict_data["level"]) if dict_data["level"] else 0,
            "屬性": dict_data["type"]["description"] if dict_data["type"] else "無屬性",
            "卡片效果": (
                dict_data["detail"]["effect"]
                if dict_data["detail"]["effect"] != "-"
                else "無效果"
            ),
            "SINGLE BP": (
                str(dict_data["battle_power_1"]) if dict_data["battle_power_1"] else ""
            ),
            "DOUBLE BP": (
                str(dict_data["battle_power_2"]) if dict_data["battle_power_2"] else ""
            ),
            "TRIPLE BP": (
                str(dict_data["battle_power_3"]) if dict_data["battle_power_3"] else ""
            ),
            "EX BP": (
                str(dict_data["battle_power_ex"])
                if dict_data["battle_power_ex"]
                else ""
            ),
            "可登場回合數": int(dict_data["round"]) if dict_data["round"] else 0,
            "稀有度": dict_data["rarity"]["description"],
            "稀有度index": rarity_index_dict[dict_data["rarity"]["description"]],
            "卡片編號": dict_data["number"],
        }
        for key, value in temp_dict_data.items():
            temp_all_datas[key].append(value)

    df = pl.DataFrame(temp_all_datas)
    return df


def generate_excel(df: pl.DataFrame, save_path: str):
    # VAR
    types_list = ["超人力霸王", "怪獸宇宙人系列", "場景"]
    normal_rare_labels_list = ["C", "U", "R", "RR", "RRR"]
    pr_rare_labels_list = ["PR"]
    much_rare_labels_list = ["AP", "SP", "SSSP", "UR"]

    heros_df = df.filter(df["類別"] == types_list[0])
    monsters_df = df.filter(df["類別"] == types_list[1])
    sences_df = df.filter(df["類別"] == types_list[2])
    unique_hero_names_list = (
        df.filter(df["類別"] == types_list[0])["名稱"].unique().to_list()
    )
    unique_monster_names_list = (
        df.filter(df["類別"] == types_list[1])["名稱"].unique().to_list()
    )

    with xlsxwriter.Workbook(save_path) as workbook:
        # ------------------------------------- 超人們 --------------------------------------
        for hero_name in unique_hero_names_list:
            temp_hero_df = heros_df.filter(heros_df["名稱"] == hero_name)
            temp_hero_df = temp_hero_df.filter(
                pl.col("稀有度").is_in(normal_rare_labels_list)
            )
            non_much_rare_cards_condition = pl.lit(False)
            non_pr_rare_cards_condition = pl.lit(False)
            for temp_label in much_rare_labels_list:
                non_much_rare_cards_condition = (
                    non_much_rare_cards_condition
                    | ~temp_hero_df["卡片編號"].str.contains(temp_label)
                )
            for temp_label in pr_rare_labels_list:
                non_pr_rare_cards_condition = (
                    non_pr_rare_cards_condition
                    | ~temp_hero_df["卡片編號"].str.contains(temp_label)
                )
            temp_hero_df = temp_hero_df.filter(non_much_rare_cards_condition)
            temp_hero_df = temp_hero_df.filter(non_pr_rare_cards_condition)
            temp_hero_df = temp_hero_df.sort(["等級", "稀有度index"]).drop(
                "稀有度index"
            )
            temp_hero_df.write_excel(workbook=workbook, worksheet=hero_name)
        # ----------------------------------------------------------------------------------

        # --------------------------------- 高版本卡片們(含PR卡) ---------------------------------
        much_rare_and_pr_rare_cards_condition = pl.lit(False)
        for label in much_rare_labels_list + pr_rare_labels_list:
            much_rare_and_pr_rare_cards_condition = (
                much_rare_and_pr_rare_cards_condition
                | df["卡片編號"].str.contains(label)
            )

        much_rare_and_pr_rare_cards_df = df.filter(
            much_rare_and_pr_rare_cards_condition
        )
        much_rare_and_pr_rare_cards_df = much_rare_and_pr_rare_cards_df.sort(
            ["名稱", "類別", "等級", "稀有度index"]
        ).drop("稀有度index")
        much_rare_and_pr_rare_cards_df.write_excel(
            workbook=workbook, worksheet="高版本卡片 and PR卡"
        )
        # -------------------------------------------------------------------------------------

        # ------------------------------------- 怪獸們 --------------------------------------
        monsters_df = monsters_df.filter(
            pl.col("稀有度").is_in(normal_rare_labels_list)
        )
        non_much_rare_cards_condition = pl.lit(False)
        non_pr_rare_cards_condition = pl.lit(False)
        for temp_label in much_rare_labels_list:
            non_much_rare_cards_condition = (
                non_much_rare_cards_condition
                | ~monsters_df["卡片編號"].str.contains(temp_label)
            )
        monsters_df = monsters_df.filter(non_much_rare_cards_condition)
        monsters_df = monsters_df.sort(["名稱", "類別", "等級", "稀有度index"]).drop(
            "稀有度index"
        )
        monsters_df.write_excel(workbook=workbook, worksheet="怪獸")
        # ----------------------------------------------------------------------------------

        # ------------------------------------- 場景們 --------------------------------------
        sences_df = sences_df.filter(pl.col("稀有度").is_in(normal_rare_labels_list))
        non_much_rare_cards_condition = pl.lit(False)
        non_pr_rare_cards_condition = pl.lit(False)
        for temp_label in much_rare_labels_list:
            non_much_rare_cards_condition = non_much_rare_cards_condition | ~sences_df[
                "卡片編號"
            ].str.contains(temp_label)
        for temp_label in pr_rare_labels_list:
            non_pr_rare_cards_condition = non_pr_rare_cards_condition | ~sences_df[
                "卡片編號"
            ].str.contains(temp_label)
        sences_df = sences_df.filter(non_much_rare_cards_condition)
        sences_df = sences_df.filter(non_pr_rare_cards_condition)
        sences_df = sences_df.sort(["可登場回合數", "稀有度index"]).drop("稀有度index")
        sences_df.write_excel(workbook=workbook, worksheet="場景")
        # ----------------------------------------------------------------------------------


if __name__ == "__main__":
    URL = "https://api.ultraman-cardgame.com/api/v1/tw/cards?page=page_num&per_page=15"
    MAX_PAGES = 13
    JSON_SAVE_PATH = "all_cards_info.json"
    EXCEL_SAVE_PATH = "all_cards_info.xlsx"

    # 抓取所有卡片資訊，並存成 json 檔
    ret = asyncio.run(get_all_cards_list(URL, MAX_PAGES))
    ret = sorted(ret, key=lambda x: int(x["id"]))
    print(len(ret))
    with open(JSON_SAVE_PATH, "w", encoding="utf-8") as f:
        json.dump(ret, f, ensure_ascii=False, indent=4)

    # 讀取 json 檔
    with open(JSON_SAVE_PATH, "r", encoding="utf-8") as f:
        all_datas = json.load(f)

    df = convert_json_to_df(all_datas)

    # 產生 excel 檔
    generate_excel(df, EXCEL_SAVE_PATH)
