#!/usr/bin/env python3

"""NFL draft scraper
Merge into one list of dataframes all the NFL drafts from the indicated years. 
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

from urllib.request import urlopen
from bs4 import BeautifulSoup

class DraftScraper:
    def __init__(self):
        self.draft_dfs_list = []
        self.errors_list = []
        self.draft_df = []

    def scrape_data(self):
        url_template = "http://www.pro-football-reference.com/years/{year}/draft.htm"
        for year in range(1967, 2020):
            url = url_template.format(year=year)
            html = urlopen(url)
            soup = BeautifulSoup(html, "lxml") 
            column_headers_first = [th.getText() for th in soup.findAll('tr', limit=2)[1].findAll('th')]
            column_headers = column_headers_first[:-1]
            column_headers.extend(["College Stats","Player_NFL_Link", "Player_NCAA_Link"])
            table_rows = soup.select("#drafts tr")[2:]
            player_data = self.extract_player_data(table_rows)
            year_df = pd.DataFrame(player_data, columns=column_headers)

            year_df.insert(0, "Draft_Yr", year)
            column_headers = year_df.columns.tolist()
            column_headers[4] = "Player"
            column_headers[19:22] = ["Rush_" + col for col in column_headers[19:22]]
            column_headers[23:25] = ["Rec_" + col for col in column_headers[23:25]]
            column_headers[-6] = "Def_Int"
            column_headers[-4] = "College"
            year_df.columns = column_headers
            # year_df.to_csv(f"data/raw_data/pfr_nfl_draft_data_RAW-{year}.csv", index=False)
            self.draft_dfs_list.append(year_df)

        self.draft_df = pd.concat(self.draft_dfs_list, ignore_index=True, sort=False)

        return self.draft_df

    def extract_player_data(self, table_rows):
        player_data = []
        for row in table_rows:
            draft_round = [row.find("th").get_text()]
            player_td = [td.get_text()[:-4] if td.get_text().endswith(" HOF")
                else td.get_text() for td in row.find_all("td")]
            player_list = draft_round + player_td

            if not player_list:
                continue

            if player_list[0] == 'Rnd':
                continue

            links_dict = {(link.get_text()[:-4]
                           if link.get_text().endswith(" HOF")
                           else link.get_text()) : link["href"] 
                           for link in row.find_all("a", href=True)}
            player_list.append(links_dict.get(player_list[3], ""))
            player_list.append(links_dict.get("College Stats", ""))
            player_data.append(player_list)

        return player_data

    def clean_data(self, df):
        player_ids = df.Player_NFL_Link.str.extract("/.*/.*/(.*)\.", expand=False)
        df["Player_ID"] = player_ids
        pfr_url = "http://www.pro-football-reference.com"
        df.Player_NFL_Link =  pfr_url + df.Player_NFL_Link
        df = df.apply(pd.to_numeric, errors="ignore")
        num_cols = df.columns[df.dtypes != object]
        df.loc[:, num_cols] = df.loc[:, num_cols].fillna(0)
        drop_idx = ~ df.Pos.isin(["FL", "E", "WB", "KR"])
        df = df.loc[drop_idx, :]
        df.loc[df.Tm == "BOS", "Tm"] = "NWE" # Rename, as these teams are more or less identical for our purposes
        df.loc[df.Tm == "PHO", "Tm"] = "ARI"
        df.loc[(df.Tm == "STL") | (df.Tm == 'RAM'), "Tm"] = "LAR"
        df.loc[df.Tm == "RAI", "Tm"] = "OAK"
        df.loc[df.Tm == "SDG", "Tm"] = "LAC"
        df.loc[(df.Pos == "HB") | (df.Pos == "FB"), "Pos"] = "RB" # not making an exception for 84 players, besides they are all RB's
        sns.boxplot(x="Pos", y="CarAV", data=df)
        plt.title("Distribution of Career Approximate Value by Position (1967-2019)")
        plt.savefig('position_values.png')

        return df

    def add_position_categories(self, df):
        df['Position_Category'] = None
        skill_positions = ["QB", "RB", "WR"]
        offensive_lineman = ["T", "G", "TE", "C", "OL"]
        defense = ["ILB", "OLB", "LB", "DB", "S", "CB", "DT", "NT", "DE", "DL"]
        special_teams = ["K", "LS", "P"]
        df.loc[df.Pos.isin(skill_positions), "Position_Category"] = "Skill"
        df.loc[df.Pos.isin(offensive_lineman), "Position_Category"] = "Offensive_Lineman"
        df.loc[df.Pos.isin(defense), "Position_Category"] = "Defense"
        df.loc[df.Pos.isin(special_teams), "Position_Category"] = "Special_Teams"
        df.to_csv('data/clean_modified_data.csv', index=False)

        return df

    # Rookie wage scale:
    # https://www.spotrac.com/nfl/draft/
    def scape_wage_scale():
        url = "https://www.spotrac.com/nfl/draft/"
        html = urlopen(url)
        soup = BeautifulSoup(html, "lxml") 
        column_headers_first = [th.getText() for th in soup.findAll('tr', limit=2)[1].findAll('th')]
        column_headers = column_headers_first[:-1]
        column_headers.extend(["College Stats","Player_NFL_Link", "Player_NCAA_Link"])
        table_rows = soup.select("#drafts tr")[2:]
        player_data = self.extract_player_data(table_rows)
        year_df = pd.DataFrame(player_data, columns=column_headers)



    def commit_data(df, conn):
        df.to_sql('new_table_name', conn, if_exists='replace', index=False)
        pd.read_sql('select * from new_table_name', conn)

    def analyze_positions(self, df):
        round_list = df.Rnd.unique()
        teams_list = df.Tm.unique()
        cats_by_round = {}
        stats_by_round = []
        pos_by_round = {}
        for rnd in round_list:
            for team in teams_list:
                # stats_by_round['round_{0}'.format(rnd)] = 
                team_round = df.loc[(df.Tm == team) & (df.Rnd == rnd)]
                cats_by_round['round_{0}'.format(rnd)][rnd][team] = df.groupby(df['Position_Category']).size()
                pos_by_round['round_{0}'.format(rnd)][team] = df.groupby(df['Pos']).size()
                print(pos_by_round)


if __name__ == '__main__':
    scraper = DraftScraper()
    df = scraper.scrape_data()
    df2 = scraper.clean_data(df)
    df3 = scraper.add_position_categories(df2)
    # df = pd.read_csv('data/clean_modified_data.csv')
    # scraper.analyze_positions(df3)
