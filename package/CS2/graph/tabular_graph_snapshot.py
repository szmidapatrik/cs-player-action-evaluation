from awpy import Demo

import pandas as pd
import polars as pl
import numpy as np

from termcolor import colored
import random
import gc

class TabularGraphSnapshot:

    # INPUT
    # Folder path constants
    MATCH_PATH = None
    PLAYER_STATS_DATA_PATH = None
    MISSING_PLAYER_STATS_DATA_PATH = None
    WEAPON_DATA_PATH = None

    
    # Optional variables
    ticks_per_second = 1
    numerical_match_id = None
    num_permutations_per_round = 1
    build_dictionary = True

    # Other variables
    __nth_tick__ = 1



    # --------------------------------------------------------------------------------------------
    # REGION: Constructor
    # --------------------------------------------------------------------------------------------

    def __init__(self):
        pass
        


    # --------------------------------------------------------------------------------------------
    # REGION: Public functions
    # --------------------------------------------------------------------------------------------

    def process_match(
        self,
        match_path: str,
        player_stats_data_path: str, 
        missing_player_stats_data_path: str,
        weapon_data_path: str,

        ticks_per_second: int = 1,
        numerical_match_id: int = None,
        sum_damages_per_round: bool = False,
        num_permutations_per_round: int = 1,
        build_dictionary: bool = True,

        package: str = 'pandas'
    ):
        """
        Formats the match data and creates the tabular game-snapshot dataset.
        
        Parameters:
            - match_path: name of the match file,
            - player_stats_data_path: path of the player statistics data,
            - missing_player_stats_data_path: path of the missing player statistics data,
            - weapon_data_path: path of the weapon information dataset for the ammo and total ammo left columns,

            - ticks_per_second (optional): how many ticks should be returned for each second. Values: 1, 2, 4, 8, 16, 32 and 64. Default is 1.
            - numerical_match_id (optional): numerical match id to add to the dataset. If value is None, no numerical match id will be added. Default is None.
            - num_permutations_per_round (optional): number of different player permutations to create for the snapshots per round. Default is 1.
            - build_dictionary (optional): whether to build and return a dictionary with the min and max column values. Default is True.
            - package (optional): the package to use for the dataframe parsing. Values: 'pandas' or 'polars'. Default is 'pandas'.
        """

        # INPUT
        self.MATCH_PATH = match_path
        self.PLAYER_STATS_DATA_PATH = player_stats_data_path
        self.MISSING_PLAYER_STATS_DATA_PATH = missing_player_stats_data_path
        self.WEAPON_DATA_PATH = weapon_data_path

        # Other variables
        self.ticks_per_second = ticks_per_second
        self.numerical_match_id = numerical_match_id
        self.num_permutations_per_round = num_permutations_per_round
        self.build_dictionary = build_dictionary



        # 0. Ticks per second operations and package validation
        self.__PREP_ticks_per_second_operations__()
        self.__PREP_validate_package__(package)

        if package == 'polars':

            # 1.
            ticks, kills, rounds, bomb, damages, smokes, infernos, he_grenades = self._POLARS_INIT_dataframes()

            # 2.
            pf = self._POLARS_PLAYER_ingame_stats(ticks, kills, rounds, damages)

            # 3.
            pf = self._POLARS_PLAYER_inventory(pf)
            
            # 4.
            pf = self._POLARS_PLAYER_active_weapons(pf)

            # 5.
            pf = self._POLARS_PLAYER_weapon_ammo_info(pf)

            # 6.
            players = self._POLARS_PLAYER_player_datasets(pf)

            # 7.
            players = self._POLARS_PLAYER_hltv_statistics(players)

            # 8.
            tabular_df = self._POLARS_TABULAR_initial_dataset(players, rounds, self.MATCH_PATH)

            # 9.
            tabular_df = self._POLARS_TABULAR_bomb_info(tabular_df, bomb)

            # 10.
            tabular_df = self._POLARS_TABULAR_INFERNO_bombsite_3x3_split(tabular_df)

            # 11.
            active_infernos, active_smokes, active_he_smokes = self._POLARS_TABULAR_smokes_HEs_infernos(tabular_df, smokes, he_grenades, infernos)

            # 12.
            if self.numerical_match_id is not None:
                tabular_df = self._POLARS_TABULAR_numerical_match_id(tabular_df)

            # 13.
            # Player permutation is not available in Polars
                
            # 14.
            tabular_df = self._POLARS_TABULAR_refactor_player_columns(tabular_df)

            # 15.
            tabular_df = self._POLARS_TABULAR_prefix_universal_columns(tabular_df)

            # 16.
            if build_dictionary:
                tabular_df_dict = self._POLARS_FINAL_build_dictionary(tabular_df)

            # 17.
            tabular_df = self._POLARS_EXT_filter_bomb_defused_rows(tabular_df)
             
        # Pandas
        else:

            # 1.
            ticks, kills, rounds, bomb, damages, smokes, infernos, he_grenades = self._INIT_dataframes()

            # 2.
            pf = self._PLAYER_ingame_stats(ticks, kills, rounds, damages, sum_damages_per_round)

            # 3.
            pf = self._PLAYER_inventory(pf)
            
            # 4.
            pf = self._PLAYER_active_weapons(pf)

            # 5.
            pf = self._PLAYER_weapon_ammo_info(pf)

            # 6.
            players = self._PLAYER_player_datasets(pf)

            # 7.
            players = self._PLAYER_hltv_statistics(players)

            # 8.
            tabular_df = self._TABULAR_initial_dataset(players, rounds, self.MATCH_PATH)

            # 9.
            tabular_df = self._TABULAR_bomb_info(tabular_df, bomb)

            # 10.
            tabular_df = self._TABULAR_INFERNO_bombsite_3x3_split(tabular_df)

            # 11.
            active_infernos, active_smokes, active_he_smokes = self._TABULAR_smokes_HEs_infernos(tabular_df, smokes, he_grenades, infernos)

            # 12.
            if self.numerical_match_id is not None:
                tabular_df = self._TABULAR_numerical_match_id(tabular_df)

            # 13.
            if num_permutations_per_round > 1:
                tabular_df = self._TABULAR_player_permutation(tabular_df, self.num_permutations_per_round)
                
            # 14.
            tabular_df = self._TABULAR_refactor_player_columns(tabular_df)

            # 15.
            tabular_df = self._TABULAR_prefix_universal_columns(tabular_df)

            # 16.
            if build_dictionary:
                tabular_df_dict = self._FINAL_build_dictionary(tabular_df)

            # 17.
            tabular_df = self._EXT_filter_bomb_defused_rows(tabular_df)

        # 18.
        self._FINAL_free_memory(ticks, kills, rounds, bomb, damages, smokes, infernos)

        # Return
        if build_dictionary:
            return tabular_df, tabular_df_dict, active_infernos, active_smokes, active_he_smokes
        else:
            return tabular_df, active_infernos, active_smokes, active_he_smokes



    # --------------------------------------------------------------------------------------------
    # REGION: Process_match private methods - PANDAS
    # --------------------------------------------------------------------------------------------

    # 0. Ticks per second operations
    def __PREP_ticks_per_second_operations__(self):
        
        # Check if the ticks_per_second is valid
        if self.ticks_per_second not in [1, 2, 4, 8, 16, 32, 64]:
            raise ValueError("Invalid ticks_per_second value. Please choose one of the following: 1, 2, 4, 8, 16, 32 or 64.")
        
        # Set the nth_tick value (the type must be integer)
        self.__nth_tick__ = int(64 / self.ticks_per_second)

    def __PREP_validate_package__(self, package):
            
            # Check if the package is valid
            if package not in ['pandas', 'polars']:
                raise ValueError("Invalid package value. Please choose one of the following: 'pandas' or 'polars'.")



    # 1. Get needed dataframes
    def __EXT_fill_smoke_NaNs__(self, smokes, rounds):
        
        # Temporary rounds dataframe with the ending tick of each round
        rounds_temp = rounds[['round', 'official_end']].copy()

        # Merge the smokes dataframe with the rounds dataframe and fill the NaN values with the official_end values
        smokes = smokes.merge(rounds_temp, on='round')
        smokes.loc[smokes['end_tick'].isna(), 'end_tick'] = smokes.loc[smokes['end_tick'].isna(), 'official_end']

        # Drop the official_end column
        smokes = smokes.drop(columns=['official_end'])

        return smokes
    
    def __EXT_fill_infernos_NaNs__(self, infernos, rounds):
        
        # Temporary rounds dataframe with the ending tick of each round
        rounds_temp = rounds[['round', 'official_end']].copy()

        # Merge the infernos dataframe with the rounds dataframe and fill the NaN values with the official_end values
        infernos = infernos.merge(rounds_temp, on='round')
        infernos.loc[infernos['end_tick'].isna(), 'end_tick'] = infernos.loc[infernos['end_tick'].isna(), 'official_end']

        # Drop the official_end column
        infernos = infernos.drop(columns=['official_end'])

        return infernos

    def _INIT_dataframes(self):

        player_cols = [
            'X',
            'Y',
            'Z',
            'health',
            'score',
            'mvps',
            'is_alive',
            'balance',
            'inventory',
            'life_state',
            'pitch',
            'yaw',
            'armor',
            'has_defuser',
            'has_helmet',
            'player_name',
            'team_clan_name',
            'start_balance',
            'total_cash_spent',
            'cash_spent_this_round',
            'jump_velo',
            'fall_velo',
            'in_crouch',
            'ducked',
            'ducking',
            'in_duck_jump',
            'spotted',
            'approximate_spotted_by',
            'time_last_injury',
            'player_state',
            'is_scoped',
            'is_walking',
            'zoom_lvl',
            'is_defusing',
            'in_bomb_zone',
            'stamina',
            'direction',
            'armor_value',
            'velo_modifier',
            'flash_duration',
            'flash_max_alpha',
            'round_start_equip_value',
            'current_equip_value',
            'velocity',
            'velocity_X',
            'velocity_Y',
            'velocity_Z',
            'FIRE',
        ]
        other_cols = [
            'num_player_alive_ct',
            'num_player_alive_t',
            'ct_losing_streak',
            't_losing_streak',
            'active_weapon_name',
            'active_weapon_ammo',
            'total_ammo_left',
            'is_in_reload',
            'alive_time_total',
            'is_bomb_dropped'
        ]

        match = Demo(path=self.MATCH_PATH, player_props=player_cols, other_props=other_cols)

        # Read dataframes
        ticks = match.ticks
        kills = match.kills
        rounds = match.rounds
        bomb = match.bomb
        damages = match.damages
        smokes = match.smokes
        infernos = match.infernos
        he_grenades = match.grenades \
                        .loc[match.grenades['grenade_type'] == 'he_grenade'] \
                        .drop_duplicates(subset=['X', 'Y', 'Z']) \
                        .drop_duplicates(subset=['entity_id'], keep='last')
        
        # Fill the NaN values of the smokes and infernos dataframes
        smokes = self.__EXT_fill_smoke_NaNs__(smokes, rounds)
        infernos = self.__EXT_fill_infernos_NaNs__(infernos, rounds)



        # Output variable handle
        output_variable_values = rounds['winner'].unique().tolist()
        if output_variable_values != ['CT', 'T'] and \
           output_variable_values != ['T', 'CT'] and \
           output_variable_values != [2, 3] and \
           output_variable_values != [3, 2]:
            
            print(colored('Error:', "red", attrs=["bold"]) + f' Incorrect output variable values: {output_variable_values}. Contact the developer for further info.')
            raise ValueError(f"Incorrect output variable values {output_variable_values}. Contact the developer for further info.")

        print(colored('Info:', "light_blue", attrs=["bold"]) + f' The output variable values are {output_variable_values}.')
        rounds['winner'] = rounds['winner'].apply(lambda x: 'CT' if x == 3 else 'T' if x == 2 else x)



        # Create columns to follow the game scores
        rounds['team1_score'] = 0
        rounds['team2_score'] = 0

        # Calculate the team scores in the rounds dataframe
        for idx, row in rounds.iterrows():
            if row['winner'] == 'CT' or row['winner'] == 3:
                if row['round'] <= 12:
                    rounds.loc[idx+1:, 'team1_score'] += 1
                elif row['round'] > 12 and row['round'] <= 24:
                    rounds.loc[idx+1:, 'team2_score'] += 1
                elif row['round'] > 24 and row['round'] <= 27:
                    rounds.loc[idx+1:, 'team1_score'] += 1
                elif row['round'] > 27 and row['round'] <= 30:
                    rounds.loc[idx+1:, 'team2_score'] += 1
                elif row['round'] > 30 and row['round'] <= 33:
                    rounds.loc[idx+1:, 'team1_score'] += 1
                elif row['round'] > 33 and row['round'] <= 36:
                    rounds.loc[idx+1:, 'team2_score'] += 1
                elif row['round'] > 36 and row['round'] <= 39:
                    rounds.loc[idx+1:, 'team1_score'] += 1
                elif row['round'] > 39 and row['round'] <= 42:
                    rounds.loc[idx+1:, 'team2_score'] += 1
                elif row['round'] > 42 and row['round'] <= 45:
                    rounds.loc[idx+1:, 'team1_score'] += 1
                elif row['round'] > 45 and row['round'] <= 48:
                    rounds.loc[idx+1:, 'team2_score'] += 1
                elif row['round'] > 48 and row['round'] <= 51:
                    rounds.loc[idx+1:, 'team1_score'] += 1
                elif row['round'] > 51 and row['round'] <= 54:
                    rounds.loc[idx+1:, 'team2_score'] += 1

            elif row['winner'] == 'T' or row['winner'] == 2:
                if row['round'] <= 12:
                    rounds.loc[idx+1:, 'team2_score'] += 1
                elif row['round'] > 12 and row['round'] <= 24:
                    rounds.loc[idx+1:, 'team1_score'] += 1
                elif row['round'] > 24 and row['round'] <= 27:
                    rounds.loc[idx+1:, 'team2_score'] += 1
                elif row['round'] > 27 and row['round'] <= 30:
                    rounds.loc[idx+1:, 'team1_score'] += 1
                elif row['round'] > 30 and row['round'] <= 33:
                    rounds.loc[idx+1:, 'team2_score'] += 1
                elif row['round'] > 33 and row['round'] <= 36:
                    rounds.loc[idx+1:, 'team1_score'] += 1
                elif row['round'] > 36 and row['round'] <= 39:
                    rounds.loc[idx+1:, 'team2_score'] += 1
                elif row['round'] > 39 and row['round'] <= 42:
                    rounds.loc[idx+1:, 'team1_score'] += 1
                elif row['round'] > 42 and row['round'] <= 45:
                    rounds.loc[idx+1:, 'team2_score'] += 1
                elif row['round'] > 45 and row['round'] <= 48:
                    rounds.loc[idx+1:, 'team1_score'] += 1
                elif row['round'] > 48 and row['round'] <= 51:
                    rounds.loc[idx+1:, 'team2_score'] += 1
                elif row['round'] > 51 and row['round'] <= 54:
                    rounds.loc[idx+1:, 'team1_score'] += 1
        
        rounds['CT_score'] = rounds.apply(lambda x: 
            x['team1_score'] if x['round'] <= 12 else
            x['team2_score'] if x['round'] > 12 and x['round'] <= 24 else
            x['team1_score'] if x['round'] > 24 and x['round'] <= 27 else
            x['team2_score'] if x['round'] > 27 and x['round'] <= 30 else
            x['team1_score'] if x['round'] > 30 and x['round'] <= 33 else
            x['team2_score'] if x['round'] > 33 and x['round'] <= 36 else
            x['team1_score'] if x['round'] > 36 and x['round'] <= 39 else
            x['team2_score'] if x['round'] > 39 and x['round'] <= 42 else
            x['team1_score'] if x['round'] > 42 and x['round'] <= 45 else
            x['team2_score'] if x['round'] > 45 and x['round'] <= 48 else
            x['team1_score'] if x['round'] > 48 and x['round'] <= 51 else
            x['team2_score'] if x['round'] > 51 and x['round'] <= 54 else
            0, axis=1)
        
        rounds['T_score'] = rounds.apply(lambda x:
            x['team2_score'] if x['round'] <= 12 else
            x['team1_score'] if x['round'] > 12 and x['round'] <= 24 else
            x['team2_score'] if x['round'] > 24 and x['round'] <= 27 else
            x['team1_score'] if x['round'] > 27 and x['round'] <= 30 else
            x['team2_score'] if x['round'] > 30 and x['round'] <= 33 else
            x['team1_score'] if x['round'] > 33 and x['round'] <= 36 else
            x['team2_score'] if x['round'] > 36 and x['round'] <= 39 else
            x['team1_score'] if x['round'] > 39 and x['round'] <= 42 else
            x['team2_score'] if x['round'] > 42 and x['round'] <= 45 else
            x['team1_score'] if x['round'] > 45 and x['round'] <= 48 else
            x['team2_score'] if x['round'] > 48 and x['round'] <= 51 else
            x['team1_score'] if x['round'] > 51 and x['round'] <= 54 else
            0, axis=1)
        
        del rounds['team1_score']
        del rounds['team2_score']


        # Filter columns
        rounds = rounds[['round', 'freeze_end', 'end', 'CT_score', 'T_score', 'winner']]

        try:
            ticks = ticks[[
                'tick', 'round', 'team_name', 'team_clan_name', 'name',
                'X', 'Y', 'Z', 'pitch', 'yaw', 'velocity_X', 'velocity_Y', 'velocity_Z', 'inventory',
                'health', 'armor_value', 'active_weapon_name', 'active_weapon_ammo', 'total_ammo_left',
                'is_alive', 'in_crouch', 'ducking', 'in_duck_jump', 'is_walking', 'spotted', 'is_scoped', 'is_defusing', 'is_in_reload', 'in_bomb_zone',
                'zoom_lvl', 'flash_duration', 'flash_max_alpha', 'mvps',
                'velo_modifier', 'balance', 'current_equip_value', 'round_start_equip_value', 'total_cash_spent', 'cash_spent_this_round',
                'ct_losing_streak', 't_losing_streak', 'is_bomb_dropped', 'FIRE'
            ]]

        except:

            print(colored('Warning:', "yellow", attrs=["bold"]) + ' [\'in_crouch\', \'ducking\', \'in_duck_jump\'] columns were missing during the parse. Added the missing columns with values 0.')
            
            ticks = ticks[[
                'tick', 'round', 'team_name', 'team_clan_name', 'name',
                'X', 'Y', 'Z', 'pitch', 'yaw', 'velocity_X', 'velocity_Y', 'velocity_Z', 'inventory',
                'health', 'armor_value', 'active_weapon_name', 'active_weapon_ammo', 'total_ammo_left',
                'is_alive', 'is_walking', 'spotted', 'is_scoped', 'is_defusing', 'is_in_reload', 'in_bomb_zone',
                'zoom_lvl', 'flash_duration', 'flash_max_alpha', 'mvps',
                'velo_modifier', 'balance', 'current_equip_value', 'round_start_equip_value', 'total_cash_spent', 'cash_spent_this_round',
                'ct_losing_streak', 't_losing_streak', 'is_bomb_dropped', 'FIRE'
            ]]
            
            missing_columns = pd.DataFrame({
                'in_crouch': 0,
                'ducking': 0,
                'in_duck_jump': 0,
            }, index=ticks.index)
            ticks = pd.concat([ticks, missing_columns], axis=1)

        
        ticks = ticks.rename(columns={
            'in_crouch'     : 'is_crouching',
            'ducking'       : 'is_ducking',
            'in_duck_jump'  : 'is_duck_jumping',
            'is_walking'    : 'is_walking',
            'spotted'       : 'is_spotted',
            'is_in_reload'  : 'is_reloading',
            'in_bomb_zone'  : 'is_in_bombsite',
            'FIRE'          : 'is_shooting'
        })
        
        return ticks, kills, rounds, bomb, damages, smokes, infernos, he_grenades



    # 2. Calculate ingame player statistics
    def __EXT_damage_per_round_df__(self, damages: pd.DataFrame, damage_type: str = 'all') -> pd.DataFrame:
        """
        Calculates the damages per round for the players.
        
        Parameters:
            - damages: the damages dataframe.
            - damage_type (optional): the type of damage to be calculated. Value can be 'all', 'weapon' and 'nade'. Default is 'all'.
        """


        # Check if the damage_type is valid
        if damage_type not in ['all', 'weapon', 'nade']:
            raise ValueError("Invalid damage_type value. Please choose one of the following: 'all', 'weapon' or 'nade'.")



        # Filter the damages dataframe for friendly fire
        damages = damages.loc[damages['attacker_team_name'] != damages['victim_team_name']]

        # Filter the damages dataframe for the damage type
        if damage_type == 'weapon':
            damages = damages.loc[~damages['weapon'].isin(['inferno', 'molotov', 'hegrenade', 'flashbang', 'smokegrenade'])]

        elif damage_type == 'nade':
            damages = damages.loc[damages['weapon'].isin(['inferno', 'molotov', 'hegrenade', 'flashbang', 'smokegrenade'])]

        # else:
        #    damages = damages



        # Create damages per round dataframe
        dpr = damages.sort_values(by=['round']).groupby(['round', 'attacker_name'])['dmg_health_real'].sum().reset_index()

        # Use cumsum to calculate the damages for the whole match per player
        dpr['dmg_health_real'] = dpr.groupby('attacker_name')['dmg_health_real'].cumsum()

        # Rename columns
        if damage_type == 'all':
            dpr = dpr.rename(columns={'attacker_name': 'name', 'dmg_health_real': 'stat_damage'})
        elif damage_type == 'weapon':
            dpr = dpr.rename(columns={'attacker_name': 'name', 'dmg_health_real': 'stat_weapon_damage'})
        elif damage_type == 'nade':
            dpr = dpr.rename(columns={'attacker_name': 'name', 'dmg_health_real': 'stat_nade_damage'})

        # Increase the round number by 1, as the damages are calculated when the round is over
        dpr['round'] += 1

        return dpr
    
    def _PLAYER_ingame_stats(self, ticks, kills, rounds, damages, sum_damages_per_round):
    
        # Merge playerFrames with rounds
        pf = ticks.merge(rounds, on='round')

        # Rename the mvps column
        pf = pf.rename(columns={'mvps': 'stat_MVPs'})

        # Player team_name column validation
        team_name_values = pf['team_name'].unique().tolist()
        if team_name_values != ['CT', 'TERRORIST'] and team_name_values != ['TERRORIST', 'CT']:
            
            if team_name_values == ['CT', 'TERRORIST', None] or team_name_values == ['TERRORIST', 'CT', None] or \
               team_name_values == ['CT', None, 'TERRORIST'] or team_name_values == ['TERRORIST', None, 'CT'] or \
               team_name_values == [None, 'CT', 'TERRORIST'] or team_name_values == [None, 'TERRORIST', 'CT']:
                
                team_name_missing_ticks = ticks.loc[(ticks['team_name'].isna())]['tick'].unique().tolist()
                print(colored('Warning:', "red", attrs=["bold"]) + f' None value found in team_name column ({team_name_values}) at ticks {team_name_missing_ticks}. Removing ticks.')
                if len(team_name_missing_ticks) > 10:
                    print(colored('Warning:', "red", attrs=["bold"]) + f' More than 10 ticks are corrupted ({len(team_name_missing_ticks)}). Consider not using the data of the whole match.')
                ticks = ticks[~ticks['tick'].isin(team_name_missing_ticks)]

            else:
                print(colored('Error:', "red", attrs=["bold"]) + f' Incorrect player team variable values: {team_name_values}. Contact the developer for further info.')
                raise ValueError(f"Incorrect output variable values {team_name_values}. Contact the developer for further info.")

        # Format CT information
        pf['is_CT'] = pf.apply(lambda x: 1 if x['team_name'] == 'CT' else 0, axis=1)
        del pf['team_name']

        # First kills dataframe
        first_kills = kills.drop_duplicates(subset=['round'], keep='first')

        # Kill stats
        pf['stat_kills'] = 0
        pf['stat_HS_kills'] = 0
        pf['stat_opening_kills'] = 0

        # Death stats
        pf['stat_deaths'] = 0
        pf['stat_opening_deaths'] = 0

        # Assist stats
        pf['stat_assists'] = 0
        pf['stat_flash_assists'] = 0

        # Setting kill-stats
        for _, row in kills.iterrows():

            # Kills
            pf.loc[(pf['tick'] >= row['tick']) & (pf['name'] == row['attacker_name']), 'stat_kills'] += 1
            # HS-kills
            if row['headshot']:
                pf.loc[(pf['tick'] >= row['tick']) & (pf['name'] == row['attacker_name']), 'stat_HS_kills'] += 1


            # Deaths
            pf.loc[(pf['tick'] >= row['tick']) & (pf['name'] == row['victim_name']), 'stat_deaths'] += 1


            # Assists
            if pd.notna(row['assister_name']):
                pf.loc[(pf['tick'] >= row['tick']) & (pf['name'] == row['assister_name']), 'stat_assists'] += 1

            # Flash assists
            if row['assistedflash']:
                pf.loc[(pf['tick'] >= row['tick']) & (pf['name'] == row['assister_name']), 'stat_flash_assists'] += 1


        # Setting opening-kill and opening-death stats
        for _, row in first_kills.iterrows():

            # Opening-kills
            pf.loc[(pf['tick'] >= row['tick']) & (pf['name'] == row['attacker_name']), 'stat_opening_kills'] += 1

            # Opening deaths
            pf.loc[(pf['tick'] >= row['tick']) & (pf['name'] == row['victim_name']), 'stat_opening_deaths'] += 1

        # Sum damages per round
        if sum_damages_per_round:

            # Create damages per round dataframe for the players for all types of damages
            dpr = self.__EXT_damage_per_round_df__(damages, 'all')
            wdpr = self.__EXT_damage_per_round_df__(damages, 'weapon')
            ndpr = self.__EXT_damage_per_round_df__(damages, 'nade')

            # Merge the damages per round dataframe with the player dataframe
            pf = pf.merge(dpr, on=['round', 'name'], how='left')
            pf = pf.merge(wdpr, on=['round', 'name'], how='left')
            pf = pf.merge(ndpr, on=['round', 'name'], how='left')

        # Else calculate the damages per tickrate
        else:

            # Damage stats
            pf['stat_damage'] = 0
            pf['stat_weapon_damage'] = 0
            pf['stat_nade_damage'] = 0

            # Filter the damages dataframe for friendly fire
            damages = damages.loc[damages['attacker_team_name'] != damages['victim_team_name']]

            # Setting kill-stats
            for _, row in damages.iterrows():

                # Damages
                pf.loc[(pf['tick'] >= row['tick']) & (pf['name'] == row['attacker_name']), 'stat_damage'] += row['dmg_health_real']
            
                # Weapon damages
                if row['weapon'] not in ['inferno', 'molotov', 'hegrenade', 'flashbang', 'smokegrenade']:
                    pf.loc[(pf['tick'] >= row['tick']) & (pf['name'] == row['attacker_name']), 'stat_weapon_damage'] += row['dmg_health_real']
                
                # Nade damages
                if row['weapon'] in ['inferno', 'molotov', 'hegrenade', 'flashbang', 'smokegrenade']:
                    pf.loc[(pf['tick'] >= row['tick']) & (pf['name'] == row['attacker_name']), 'stat_nade_damage'] += row['dmg_health_real']


        # Fill NaN values with 0
        pf['stat_damage'] = pf['stat_damage'].fillna(0)
        pf['stat_weapon_damage'] = pf['stat_weapon_damage'].fillna(0)
        pf['stat_nade_damage'] = pf['stat_nade_damage'].fillna(0)


        # Calculate other stats
        pf['stat_survives'] = pf['round'] - pf['stat_deaths']
        pf['stat_KPR'] = pf['stat_kills'] / pf['round']
        pf['stat_ADR'] = pf['stat_damage'] / pf['round']
        pf['stat_DPR'] = pf['stat_deaths'] / pf['round']
        pf['stat_HS%'] = pf['stat_HS_kills'] / pf['stat_kills']
        pf['stat_HS%'] = pf['stat_HS%'].fillna(0)
        pf['stat_SPR'] = pf['stat_survives'] / pf['round']
            
        return pf
    


        # 3. Handle active weapon column
    
    
    
    # 3. Inventory
    def _PLAYER_inventory(self, pf):

        # Inventory weapons
        inventory_weapons = [
            # Other
            'inventory_C4', 'inventory_Taser',
            # Pistols
            'inventory_USP-S', 'inventory_P2000', 'inventory_Glock-18', 'inventory_Dual Berettas', 'inventory_P250', 'inventory_Tec-9', 'inventory_CZ75 Auto', 'inventory_Five-SeveN', 'inventory_Desert Eagle', 'inventory_R8 Revolver',
            # SMGs
            'inventory_MAC-10', 'inventory_MP9', 'inventory_MP7', 'inventory_MP5-SD', 'inventory_UMP-45', 'inventory_PP-Bizon', 'inventory_P90',
            # Heavy
            'inventory_Nova', 'inventory_XM1014', 'inventory_Sawed-Off', 'inventory_MAG-7', 'inventory_M249', 'inventory_Negev',
            # Rifles
            'inventory_FAMAS', 'inventory_Galil AR', 'inventory_AK-47', 'inventory_M4A4', 'inventory_M4A1-S', 'inventory_SG 553', 'inventory_AUG', 'inventory_SSG 08', 'inventory_AWP', 'inventory_G3SG1', 'inventory_SCAR-20',
            # Grenades
            'inventory_HE Grenade', 'inventory_Flashbang', 'inventory_Smoke Grenade', 'inventory_Incendiary Grenade', 'inventory_Molotov', 'inventory_Decoy Grenade'
        ]

        # Create dummie cols
        for col in inventory_weapons:
            pf[col] = pf['inventory'].apply(lambda x: 1 if col.replace('inventory_', '') in x else 0)

        return pf



    # 4. Handle active weapon column
    def _PLAYER_active_weapons(self, pf):

        # If the actifWeapon column value contains the word knife, set the activeWeapon column to 'Knife'
        pf['active_weapon_name'] = pf['active_weapon_name'].fillna('')
        pf['active_weapon_name'] = pf['active_weapon_name'].apply(lambda x: 'Knife' if 'knife' in str.lower(x) else x)
    
        # Active weapons
        active_weapons = [
            # Other
            'active_weapon_C4', 'active_weapon_Knife', 'active_weapon_Taser',
            # Pistols
            'active_weapon_USP-S', 'active_weapon_P2000', 'active_weapon_Glock-18', 'active_weapon_Dual Berettas', 'active_weapon_P250', 'active_weapon_Tec-9', 'active_weapon_CZ75 Auto', 'active_weapon_Five-SeveN', 'active_weapon_Desert Eagle', 'active_weapon_R8 Revolver',
            # SMGs
            'active_weapon_MAC-10', 'active_weapon_MP9', 'active_weapon_MP7', 'active_weapon_MP5-SD', 'active_weapon_UMP-45', 'active_weapon_PP-Bizon', 'active_weapon_P90',
            # Heavy
            'active_weapon_Nova', 'active_weapon_XM1014', 'active_weapon_Sawed-Off', 'active_weapon_MAG-7', 'active_weapon_M249', 'active_weapon_Negev',
            # Rifles
            'active_weapon_FAMAS', 'active_weapon_Galil AR', 'active_weapon_AK-47', 'active_weapon_M4A4', 'active_weapon_M4A1-S', 'active_weapon_SG 553', 'active_weapon_AUG', 'active_weapon_SSG 08', 'active_weapon_AWP', 'active_weapon_G3SG1', 'active_weapon_SCAR-20',
            # Grenades
            'active_weapon_HE Grenade', 'active_weapon_Flashbang', 'active_weapon_Smoke Grenade', 'active_weapon_Incendiary Grenade', 'active_weapon_Molotov', 'active_weapon_Decoy Grenade'
        ]

        # Create dummie cols
        df_dummies = pd.get_dummies(pf['active_weapon_name'], prefix="active_weapon",drop_first=False)
        dummies = pd.DataFrame()
        for col in active_weapons:
            if col not in df_dummies.columns:
                dummies[col] = np.zeros(len(df_dummies))
            else:
                dummies[col] = df_dummies[col]
        
        dummies = dummies*1
        pf = pf.merge(dummies, left_index = True, right_index = True, how = 'left')
        
        return pf
    


    # 5. Handle weapon ammo info
    def _PLAYER_weapon_ammo_info(self, pf):

        # Read weapon data
        weapon_data = pd.read_csv(self.WEAPON_DATA_PATH)

        # Create player ammo info columns
        pf['active_weapon_magazine_size'] = 0
        pf['active_weapon_max_ammo'] = 0
        pf['active_weapon_magazine_ammo_left_%'] = 0
        pf['active_weapon_total_ammo_left_%'] = 0

        # Active weapons
        active_weapons = [
            # Other
            'active_weapon_C4', 'active_weapon_Knife', 'active_weapon_Taser',
            # Pistols
            'active_weapon_USP-S', 'active_weapon_P2000', 'active_weapon_Glock-18', 'active_weapon_Dual Berettas', 'active_weapon_P250', 'active_weapon_Tec-9', 'active_weapon_CZ75 Auto', 'active_weapon_Five-SeveN', 'active_weapon_Desert Eagle', 'active_weapon_R8 Revolver',
            # SMGs
            'active_weapon_MAC-10', 'active_weapon_MP9', 'active_weapon_MP7', 'active_weapon_MP5-SD', 'active_weapon_UMP-45', 'active_weapon_PP-Bizon', 'active_weapon_P90',
            # Heavy
            'active_weapon_Nova', 'active_weapon_XM1014', 'active_weapon_Sawed-Off', 'active_weapon_MAG-7', 'active_weapon_M249', 'active_weapon_Negev',
            # Rifles
            'active_weapon_FAMAS', 'active_weapon_Galil AR', 'active_weapon_AK-47', 'active_weapon_M4A4', 'active_weapon_M4A1-S', 'active_weapon_SG 553', 'active_weapon_AUG', 'active_weapon_SSG 08', 'active_weapon_AWP', 'active_weapon_G3SG1', 'active_weapon_SCAR-20',
            # Grenades
            'active_weapon_HE Grenade', 'active_weapon_Flashbang', 'active_weapon_Smoke Grenade', 'active_weapon_Incendiary Grenade', 'active_weapon_Molotov', 'active_weapon_Decoy Grenade'
        ]

        # Set ammo info
        for col in active_weapons:
            
            pf.loc[pf[col] == 1, 'active_weapon_magazine_size'] = weapon_data.loc[weapon_data['weapon_name'] == col.replace('active_weapon_', '')]['magazine_size'].values[0]
            pf.loc[pf[col] == 1, 'active_weapon_max_ammo']    = weapon_data.loc[weapon_data['weapon_name'] == col.replace('active_weapon_', '')]['total_ammo'].values[0]

        # Create magazine ammo left % column
        # If the player holds a weapon without ammo (e.g. knife), the ammo left is 0, thus we devide by 0
        pf['active_weapon_magazine_ammo_left_%'] = pf['active_weapon_ammo'] / pf['active_weapon_magazine_size']
        # Fix the 0 division
        pf['active_weapon_magazine_ammo_left_%'] = pf['active_weapon_magazine_ammo_left_%'].fillna(0)

        # Create total ammo left % column
        # If the player holds a weapon without ammo (e.g. knife), the ammo left is 0, thus we devide by 0
        pf['active_weapon_total_ammo_left_%'] = pf['total_ammo_left'] / pf['active_weapon_max_ammo']
        # Fix the 0 division
        pf['active_weapon_total_ammo_left_%'] = pf['active_weapon_total_ammo_left_%'].fillna(0)

        return pf



    # 6. Create player dataset
    def _PLAYER_player_datasets(self, pf):
    
        startAsCTPlayerNames = pf[(pf['is_CT'] == True)  & (pf['round'] == 1)]['name'].drop_duplicates().tolist()
        startAsTPlayerNames  = pf[(pf['is_CT'] == False) & (pf['round'] == 1)]['name'].drop_duplicates().tolist()

        startAsCTPlayerNames.sort()
        startAsTPlayerNames.sort()

        players = {}

        # Team 1: start on CT side
        players[0] = pf[pf['name'] == startAsCTPlayerNames[0]].iloc[::self.__nth_tick__].copy()
        players[1] = pf[pf['name'] == startAsCTPlayerNames[1]].iloc[::self.__nth_tick__].copy()
        players[2] = pf[pf['name'] == startAsCTPlayerNames[2]].iloc[::self.__nth_tick__].copy()
        players[3] = pf[pf['name'] == startAsCTPlayerNames[3]].iloc[::self.__nth_tick__].copy()
        players[4] = pf[pf['name'] == startAsCTPlayerNames[4]].iloc[::self.__nth_tick__].copy()

        # Team 2: start on T side
        players[5] = pf[pf['name'] == startAsTPlayerNames[0]].iloc[::self.__nth_tick__].copy()
        players[6] = pf[pf['name'] == startAsTPlayerNames[1]].iloc[::self.__nth_tick__].copy()
        players[7] = pf[pf['name'] == startAsTPlayerNames[2]].iloc[::self.__nth_tick__].copy()
        players[8] = pf[pf['name'] == startAsTPlayerNames[3]].iloc[::self.__nth_tick__].copy()
        players[9] = pf[pf['name'] == startAsTPlayerNames[4]].iloc[::self.__nth_tick__].copy()
        
        return players
    


    # 7. Insert universal player statistics into player dataset
    def __EXT_insert_columns_into_player_dataframes__(self, stat_df, players_df):
        for col in stat_df.columns:
            if col != 'player_name':
                players_df[col] = stat_df.loc[stat_df['player_name'] == players_df['name'].iloc[0]][col].iloc[0]
        return players_df

    def _PLAYER_hltv_statistics(self, players):
        
        # Needed columns
        needed_stats = ['player_name', 'rating_2.0', 'DPR', 'KAST', 'Impact', 'ADR', 'KPR','total_kills', 'HS%', 'total_deaths', 'KD_ratio', 'dmgPR',
        'grenade_dmgPR', 'maps_played', 'saved_by_teammatePR', 'saved_teammatesPR','opening_kill_rating', 'team_W%_after_opening',
        'opening_kill_in_W_rounds', 'rating_1.0_all_Career', 'clutches_1on1_ratio', 'clutches_won_1on1', 'clutches_won_1on2', 'clutches_won_1on3', 'clutches_won_1on4', 'clutches_won_1on5']
        
        stats = pd.read_csv(self.PLAYER_STATS_DATA_PATH).drop_duplicates()

        try:
            stats = stats[needed_stats]

        # If clutches_1on1_ratio column is missing, calculate it here
        except:
            stats['clutches_1on1_ratio'] = stats['clutches_won_1on1'] / stats['clutches_lost_1on1']
            stats['clutches_1on1_ratio'] = stats['clutches_1on1_ratio'].fillna(0)
            stats = stats[needed_stats]

        # Stats dataframe basic formatting
        for col in stats.columns:
            if col != 'player_name':
                stats[col] = stats[col].astype('float32')
                stats.rename(columns={col: "hltv_" + col}, inplace=True)
        
        # Merge stats with players
        for idx in range(0,len(players)):
            # If the stats dataframe contains the player related informations, do the merge
            if len(stats.loc[stats['player_name'] == players[idx]['name'].iloc[0]]) == 1:
                players[idx] = self.__EXT_insert_columns_into_player_dataframes__(stats, players[idx])

            # If the stats dataframe does not contain the player related informations, check if the missing_players_df contains the player
            else:

                mpdf = pd.read_csv(self.MISSING_PLAYER_STATS_DATA_PATH)
                
                try:
                    mpdf = mpdf[needed_stats]
                    
                # If clutches_1on1_ratio column is missing, calculate it here
                except:
                    mpdf['clutches_1on1_ratio'] = mpdf['clutches_won_1on1'] / mpdf['clutches_lost_1on1']
                    mpdf['clutches_1on1_ratio'] = mpdf['clutches_1on1_ratio'].fillna(0)
                    mpdf = mpdf[needed_stats]
                
                for col in mpdf.columns:
                    if col != 'player_name':
                        mpdf[col] = mpdf[col].astype('float32')
                        mpdf.rename(columns={col: "hltv_" + col}, inplace=True)
                        
                # If the missing_players_df contains the player related informations, do the merge
                if len(mpdf.loc[mpdf['player_name'] == players[idx]['name'].iloc[0]]) == 1:
                    players[idx] = self.__EXT_insert_columns_into_player_dataframes__(mpdf, players[idx])

                # Else get imputed values for the player from missing_players_df and do the merge
                else:
                    first_anonim_pro_index = mpdf.index[mpdf['player_name'] == 'anonim_pro'].min()
                    mpdf.at[first_anonim_pro_index, 'player_name'] = players[idx]['name'].iloc[0]
                    players[idx] = self.__EXT_insert_columns_into_player_dataframes__(mpdf, players[idx])
                    
                    # Reverse the column renaming - remove the 'hltv_' prefix
                    for col in mpdf.columns:
                        if col.startswith('hltv_'):
                            new_col = col[len('hltv_'):]
                            mpdf.rename(columns={col: new_col}, inplace=True)

                    mpdf.to_csv(self.MISSING_PLAYER_STATS_DATA_PATH, index=False)
            
        return players
    


    # 8. Create tabular dataset - first version (1 row - 1 graph)
    def __EXT_calculate_ct_equipment_value__(self, row):
        if row['player0_is_CT']:
            return row[['player0_equi_val_alive', 'player1_equi_val_alive', 'player2_equi_val_alive', 'player3_equi_val_alive', 'player4_equi_val_alive']].sum()
        else:
            return row[['player5_equi_val_alive', 'player6_equi_val_alive', 'player7_equi_val_alive', 'player8_equi_val_alive', 'player9_equi_val_alive']].sum()

    def __EXT_calculate_t_equipment_value__(self, row):
        if row['player0_is_CT'] == False:
            return row[['player0_equi_val_alive', 'player1_equi_val_alive', 'player2_equi_val_alive', 'player3_equi_val_alive', 'player4_equi_val_alive']].sum()
        else:
            return row[['player5_equi_val_alive', 'player6_equi_val_alive', 'player7_equi_val_alive', 'player8_equi_val_alive', 'player9_equi_val_alive']].sum()

    def __EXT_calculate_ct_total_hp__(self, row):
        if row['player0_is_CT']:
            return row[['player0_health','player1_health','player2_health','player3_health','player4_health']].sum()
        else:
            return row[['player5_health','player6_health','player7_health','player8_health','player9_health']].sum()

    def __EXT_calculate_t_total_hp__(self, row):
        if row['player0_is_CT'] == False:
            return row[['player0_health','player1_health','player2_health','player3_health','player4_health']].sum()
        else:
            return row[['player5_health','player6_health','player7_health','player8_health','player9_health']].sum()

    def __EXT_calculate_ct_alive_num__(self, row):
        if row['player0_is_CT']:
            return row[['player0_is_alive','player1_is_alive','player2_is_alive','player3_is_alive','player4_is_alive']].sum()
        else:
            return row[['player5_is_alive','player6_is_alive','player7_is_alive','player8_is_alive','player9_is_alive']].sum()

    def __EXT_calculate_t_alive_num__(self, row):
        if row['player0_is_CT'] == False:
            return row[['player0_is_alive','player1_is_alive','player2_is_alive','player3_is_alive','player4_is_alive']].sum()
        else:
            return row[['player5_is_alive','player6_is_alive','player7_is_alive','player8_is_alive','player9_is_alive']].sum()

    def __EXT_delete_useless_columns__(self, graph_data):

        del graph_data['player0_equi_val_alive']
        del graph_data['player1_equi_val_alive']
        del graph_data['player2_equi_val_alive']
        del graph_data['player3_equi_val_alive']
        del graph_data['player4_equi_val_alive']
        del graph_data['player5_equi_val_alive']
        del graph_data['player6_equi_val_alive']
        del graph_data['player7_equi_val_alive']
        del graph_data['player8_equi_val_alive']
        del graph_data['player9_equi_val_alive']
        
        del graph_data['player0_freeze_end']
        del graph_data['player1_freeze_end']
        del graph_data['player2_freeze_end']
        del graph_data['player3_freeze_end']
        del graph_data['player4_freeze_end']
        del graph_data['player5_freeze_end']
        del graph_data['player6_freeze_end']
        del graph_data['player7_freeze_end']
        del graph_data['player8_freeze_end']
        del graph_data['player9_freeze_end']
        
        del graph_data['player0_end']
        del graph_data['player1_end']
        del graph_data['player2_end']
        del graph_data['player3_end']
        del graph_data['player4_end']
        del graph_data['player5_end']
        del graph_data['player6_end']
        del graph_data['player7_end']
        del graph_data['player8_end']
        del graph_data['player9_end']
        
        del graph_data['player0_winner']
        del graph_data['player1_winner']
        del graph_data['player2_winner']
        del graph_data['player3_winner']
        del graph_data['player4_winner']
        del graph_data['player5_winner']
        del graph_data['player6_winner']
        del graph_data['player7_winner']
        del graph_data['player8_winner']
        del graph_data['player9_winner']

        del graph_data['player1_ct_losing_streak']
        del graph_data['player2_ct_losing_streak']
        del graph_data['player3_ct_losing_streak']
        del graph_data['player4_ct_losing_streak']
        del graph_data['player5_ct_losing_streak']
        del graph_data['player6_ct_losing_streak']
        del graph_data['player7_ct_losing_streak']
        del graph_data['player8_ct_losing_streak']
        del graph_data['player9_ct_losing_streak']

        del graph_data['player1_t_losing_streak']
        del graph_data['player2_t_losing_streak']
        del graph_data['player3_t_losing_streak']
        del graph_data['player4_t_losing_streak']
        del graph_data['player5_t_losing_streak']
        del graph_data['player6_t_losing_streak']
        del graph_data['player7_t_losing_streak']
        del graph_data['player8_t_losing_streak']
        del graph_data['player9_t_losing_streak']

        del graph_data['player1_is_bomb_dropped']
        del graph_data['player2_is_bomb_dropped']
        del graph_data['player3_is_bomb_dropped']
        del graph_data['player4_is_bomb_dropped']
        del graph_data['player5_is_bomb_dropped']
        del graph_data['player6_is_bomb_dropped']
        del graph_data['player7_is_bomb_dropped']
        del graph_data['player8_is_bomb_dropped']
        del graph_data['player9_is_bomb_dropped']

        return graph_data

    def __EXT_calculate_time_remaining__(self, row):
        return 115.0 - ((row['tick'] - row['freeze_end']) / 64.0)

    def _TABULAR_initial_dataset(self, players, rounds, match_id):
        """
        Creates the first version of the dataset for the graph model.
        
        Parameters:
            - players: the dataframes of the players.
            - rounds: the dataframes of the rounds.
            - match_id: the id of the match.
        """

        # Copy players object
        graph_players = {}
        for idx in range(0,len(players)):
            graph_players[idx] = players[idx].copy()

        colsNotToRename = ['tick', 'round']

        # Rename columns except for tick, roundNum, seconds, floorSec
        for idx in range(0,len(graph_players)):
            
            for col in graph_players[idx].columns:
                if col not in colsNotToRename:
                    graph_players[idx].rename(columns={col: "player" + str(idx) + "_" + col}, inplace=True)

        # Create a graph dataframe to store all players in 1 row per second
        graph_data = graph_players[0].copy()

        # Merge dataframes
        for i in range(1, len(graph_players)):
            graph_data = graph_data.merge(graph_players[i], on=colsNotToRename)

        graph_data = graph_data.merge(rounds, on=['round'])

        # Output variable
        graph_data['CT_wins'] = graph_data.apply(lambda x: 1 if (x['winner'] == 'CT') else 0, axis=1)

        graph_data['player0_equi_val_alive'] = graph_data['player0_current_equip_value'] * graph_data['player0_is_alive']
        graph_data['player1_equi_val_alive'] = graph_data['player1_current_equip_value'] * graph_data['player1_is_alive']
        graph_data['player2_equi_val_alive'] = graph_data['player2_current_equip_value'] * graph_data['player2_is_alive']
        graph_data['player3_equi_val_alive'] = graph_data['player3_current_equip_value'] * graph_data['player3_is_alive']
        graph_data['player4_equi_val_alive'] = graph_data['player4_current_equip_value'] * graph_data['player4_is_alive']
        graph_data['player5_equi_val_alive'] = graph_data['player5_current_equip_value'] * graph_data['player5_is_alive']
        graph_data['player6_equi_val_alive'] = graph_data['player6_current_equip_value'] * graph_data['player6_is_alive']
        graph_data['player7_equi_val_alive'] = graph_data['player7_current_equip_value'] * graph_data['player7_is_alive']
        graph_data['player8_equi_val_alive'] = graph_data['player8_current_equip_value'] * graph_data['player8_is_alive']
        graph_data['player9_equi_val_alive'] = graph_data['player9_current_equip_value'] * graph_data['player9_is_alive']

        graph_data['CT_alive_num'] = graph_data.apply(self.__EXT_calculate_ct_alive_num__, axis=1)
        graph_data['T_alive_num']  = graph_data.apply(self.__EXT_calculate_t_alive_num__, axis=1)
        
        graph_data['CT_total_hp'] = graph_data.apply(self.__EXT_calculate_ct_total_hp__, axis=1)
        graph_data['T_total_hp']  = graph_data.apply(self.__EXT_calculate_t_total_hp__, axis=1)

        graph_data['CT_equipment_value'] = graph_data.apply(self.__EXT_calculate_ct_equipment_value__, axis=1)
        graph_data['T_equipment_value'] = graph_data.apply(self.__EXT_calculate_t_equipment_value__, axis=1)

        graph_data = graph_data.rename(columns={
            'player0_ct_losing_streak': 'CT_losing_streak', 
            'player0_t_losing_streak': 'T_losing_streak', 
            'player0_is_bomb_dropped': 'is_bomb_dropped',
        })

        graph_data = self.__EXT_delete_useless_columns__(graph_data)

        # Add time remaining column
        new_columns = pd.DataFrame({
            'time': 0.0,
        }, index=graph_data.index)
        graph_data = pd.concat([graph_data, new_columns], axis=1)
        graph_data['time'] = graph_data.apply(self.__EXT_calculate_time_remaining__, axis=1)

        # Create a DataFrame with a single column for match_id
        match_id_df = pd.DataFrame({'match_id': str(match_id)}, index=graph_data.index)
        graph_data_concatenated = pd.concat([graph_data, match_id_df], axis=1)

        return graph_data_concatenated
    


    # 9. Add bomb information to the dataset
    def __EXT_calculate_is_bomb_being_planted__(self, row):
        for i in range(0,10):
            if row['player{}_active_weapon_C4'.format(i)] == 1:
                if row['player{}_is_in_bombsite'.format(i)] == 1:
                    if row['player{}_is_shooting'.format(i)] == 1:
                        return 1
        return 0
    
    def __EXT_calculate_is_bomb_being_defused__(self, row):
        return row['player0_is_defusing'] + row['player1_is_defusing'] + row['player2_is_defusing'] + row['player3_is_defusing'] + row['player4_is_defusing'] + \
               row['player5_is_defusing'] + row['player6_is_defusing'] + row['player7_is_defusing'] + row['player8_is_defusing'] + row['player9_is_defusing']

    def _TABULAR_bomb_info(self, tabular_df, bombdf):

        new_columns = pd.DataFrame({
            'is_bomb_being_planted': 0,
            'is_bomb_being_defused': 0,
            'is_bomb_defused': 0,
            'is_bomb_planted_at_A_site': 0,
            'is_bomb_planted_at_B_site': 0,
            'plant_tick': 0,
            'bomb_X': 0.0,
            'bomb_Y': 0.0,
            'bomb_Z': 0.0
        }, index=tabular_df.index)

        tabular_df = pd.concat([tabular_df, new_columns], axis=1)

        tabular_df['is_bomb_being_planted'] = tabular_df.apply(self.__EXT_calculate_is_bomb_being_planted__, axis=1)
        tabular_df['is_bomb_being_defused'] = tabular_df.apply(self.__EXT_calculate_is_bomb_being_defused__, axis=1)

        for _, row in bombdf.iterrows():

            if (row['event'] == 'planted'):
                tabular_df.loc[(tabular_df['round'] == row['round']) & (tabular_df['tick'] >= row['tick']), 'is_bomb_planted_at_A_site'] = 1 if row['site'] == 'BombsiteA' else 0
                tabular_df.loc[(tabular_df['round'] == row['round']) & (tabular_df['tick'] >= row['tick']), 'is_bomb_planted_at_B_site'] = 1 if row['site'] == 'BombsiteB' else 0
                tabular_df.loc[(tabular_df['round'] == row['round']) & (tabular_df['tick'] >= row['tick']), 'bomb_X'] = row['X']
                tabular_df.loc[(tabular_df['round'] == row['round']) & (tabular_df['tick'] >= row['tick']), 'bomb_Y'] = row['Y']
                tabular_df.loc[(tabular_df['round'] == row['round']) & (tabular_df['tick'] >= row['tick']), 'bomb_Z'] = row['Z']
                tabular_df.loc[(tabular_df['round'] == row['round']), 'plant_tick'] = row['tick']

            if (row['event'] == 'defused'):
                tabular_df.loc[(tabular_df['round'] == row['round']) & (tabular_df['tick'] >= row['tick']), 'is_bomb_being_defused'] = 0
                tabular_df.loc[(tabular_df['round'] == row['round']) & (tabular_df['tick'] >= row['tick']), 'is_bomb_defused'] = 1

        # Time remaining including the plant time
        tabular_df['remaining_time'] = tabular_df['time']
        tabular_df.loc[tabular_df['is_bomb_planted_at_A_site'] == 1, 'remaining_time'] = 40.0 - ((tabular_df['tick'] - tabular_df['plant_tick']) / 64.0)
        tabular_df.loc[tabular_df['is_bomb_planted_at_B_site'] == 1, 'remaining_time'] = 40.0 - ((tabular_df['tick'] - tabular_df['plant_tick']) / 64.0)


        return tabular_df



    # 10. Split the bombsites by 3x3 matrix for bomb position feature
    def __EXT_INFERNO_get_bomb_mx_coordinate__(self, row):
        # If bomb is planted on A
        if row['is_bomb_planted_at_A_site'] == 1:
                # 1st row
                if row['bomb_Y'] >= 650:
                    # 1st column
                    if row['bomb_X'] < 1900:
                        return 1
                    # 2nd column
                    if row['bomb_X'] >= 1900 and row['bomb_X'] < 2050:
                        return 2
                    # 3rd column
                    if row['bomb_X'] >= 2050:
                        return 3
                # 2nd row
                if row['bomb_Y'] < 650 and row['bomb_Y'] >= 325: 
                    # 1st column
                    if row['bomb_X'] < 1900:
                        return 4
                    # 2nd column
                    if row['bomb_X'] >= 1900 and row['bomb_X'] < 2050:
                        return 5
                    # 3rd column
                    if row['bomb_X'] >= 2050:
                        return 6
                # 3rd row
                if row['bomb_Y'] < 325: 
                    # 1st column
                    if row['bomb_X'] < 1900:
                        return 7
                    # 2nd column
                    if row['bomb_X'] >= 1900 and row['bomb_X'] < 2050:
                        return 8
                    # 3rd column
                    if row['bomb_X'] >= 2050:
                        return 9
        
        # If bomb is planted on B
        if row['is_bomb_planted_at_B_site'] == 1:
                # 1st row
                if row['bomb_Y'] >= 2900:
                    # 1st column
                    if row['bomb_X'] < 275:
                        return 1
                    # 2nd column
                    if row['bomb_X'] >= 275 and row['bomb_X'] < 400:
                        return 2
                    # 3rd column
                    if row['bomb_X'] >= 400:
                        return 3
                # 2nd row
                if row['bomb_Y'] < 2900 and row['bomb_Y'] >= 2725: 
                    # 1st column
                    if row['bomb_X'] < 275:
                        return 4
                    # 2nd column
                    if row['bomb_X'] >= 275 and row['bomb_X'] < 400:
                        return 5
                    # 3rd column
                    if row['bomb_X'] >= 400:
                        return 6
                # 3rd row
                if row['bomb_Y'] < 2725: 
                    # 1st column
                    if row['bomb_X'] < 275:
                        return 7
                    # 2nd column
                    if row['bomb_X'] >= 275 and row['bomb_X'] < 400:
                        return 8
                    # 3rd column
                    if row['bomb_X'] >= 400:
                        return 9

    def _TABULAR_INFERNO_bombsite_3x3_split(self, df):
            
        new_columns = pd.DataFrame({
            'bomb_mx_pos': 0
        }, index=df.index)

        df = pd.concat([df, new_columns], axis=1)
        
        df.loc[(df['is_bomb_planted_at_A_site'] == 1) | (df['is_bomb_planted_at_B_site'] == 1), 'bomb_mx_pos'] = df.apply(self.__EXT_INFERNO_get_bomb_mx_coordinate__, axis=1)

        new_columns = pd.DataFrame({
            'bomb_mx_pos1': 0,
            'bomb_mx_pos2': 0,
            'bomb_mx_pos3': 0,
            'bomb_mx_pos4': 0,
            'bomb_mx_pos5': 0,
            'bomb_mx_pos6': 0,
            'bomb_mx_pos7': 0,
            'bomb_mx_pos8': 0,
            'bomb_mx_pos9': 0
        }, index=df.index)

        df = pd.concat([df, new_columns], axis=1)

        df.loc[df['bomb_mx_pos'] == 1, 'bomb_mx_pos1'] = 1
        df.loc[df['bomb_mx_pos'] == 2, 'bomb_mx_pos2'] = 1
        df.loc[df['bomb_mx_pos'] == 3, 'bomb_mx_pos3'] = 1
        df.loc[df['bomb_mx_pos'] == 4, 'bomb_mx_pos4'] = 1
        df.loc[df['bomb_mx_pos'] == 5, 'bomb_mx_pos5'] = 1
        df.loc[df['bomb_mx_pos'] == 6, 'bomb_mx_pos6'] = 1
        df.loc[df['bomb_mx_pos'] == 7, 'bomb_mx_pos7'] = 1
        df.loc[df['bomb_mx_pos'] == 8, 'bomb_mx_pos8'] = 1
        df.loc[df['bomb_mx_pos'] == 9, 'bomb_mx_pos9'] = 1

        df = df.drop(columns=['bomb_mx_pos'])

        return df
    


    # 11. Handle smoke and molotov grenades
    def _TABULAR_smokes_HEs_infernos(self, df, smokes, he_grenades, infernos):

        # Active infernos, smokes and HE explosions dataframe
        active_infernos = None
        active_smokes = None
        active_he_smokes = None
        

        # Handle smokes
        # The round check is necessary because the smokes dataframe contains smokes with the end_tick values being NaN
        for _, row in smokes.iterrows():

            temp_smoke = df[['tick', 'round']].copy()
            temp_smoke = pd.concat([temp_smoke, pd.DataFrame(columns=['X', 'Y', 'Z'])], axis=1)

            startTick = row['start_tick']
            endTick = row['end_tick'] - 112
            temp_smoke.loc[(temp_smoke['round'] == row['round']) & (temp_smoke['tick'] >= startTick) & (temp_smoke['tick'] <= endTick), 'X'] = row['X']
            temp_smoke.loc[(temp_smoke['round'] == row['round']) & (temp_smoke['tick'] >= startTick) & (temp_smoke['tick'] <= endTick), 'Y'] = row['Y']
            temp_smoke.loc[(temp_smoke['round'] == row['round']) & (temp_smoke['tick'] >= startTick) & (temp_smoke['tick'] <= endTick), 'Z'] = row['Z']

            temp_smoke = temp_smoke.dropna()

            if active_smokes is None:
                active_smokes = temp_smoke
            else:
                active_smokes = pd.concat([active_smokes, temp_smoke])

        # Handle HE grenades
        for _, row in he_grenades.iterrows():
                
            temp_HE = df[['tick', 'round']].copy()
            temp_HE = pd.concat([temp_HE, pd.DataFrame(columns=['X', 'Y', 'Z'])], axis=1)

            startTick = row['tick']
            endTick = startTick + 128
            temp_HE.loc[(temp_HE['round'] == row['round']) & (temp_HE['tick'] >= startTick) & (temp_HE['tick'] <= endTick), 'X'] = row['X']
            temp_HE.loc[(temp_HE['round'] == row['round']) & (temp_HE['tick'] >= startTick) & (temp_HE['tick'] <= endTick), 'Y'] = row['Y']
            temp_HE.loc[(temp_HE['round'] == row['round']) & (temp_HE['tick'] >= startTick) & (temp_HE['tick'] <= endTick), 'Z'] = row['Z']
        
            temp_HE = temp_HE.dropna()

            if active_he_smokes is None:
                active_he_smokes = temp_HE
            else:
                active_he_smokes = pd.concat([active_he_smokes, temp_HE])

        # Handle infernos
        for _, row in infernos.iterrows():

            temp_inf = df[['tick', 'round']].copy()
            temp_inf = pd.concat([temp_inf, pd.DataFrame(columns=['X', 'Y', 'Z'])], axis=1)

            startTick = row['start_tick']
            endTick = row['end_tick']
            temp_inf.loc[(temp_inf['round'] == row['round']) & (temp_inf['tick'] >= startTick) & (temp_inf['tick'] <= endTick), 'X'] = row['X']
            temp_inf.loc[(temp_inf['round'] == row['round']) & (temp_inf['tick'] >= startTick) & (temp_inf['tick'] <= endTick), 'Y'] = row['Y']
            temp_inf.loc[(temp_inf['round'] == row['round']) & (temp_inf['tick'] >= startTick) & (temp_inf['tick'] <= endTick), 'Z'] = row['Z']

            temp_inf = temp_inf.dropna()

            if active_infernos is None:
                active_infernos = temp_inf
            else:
                active_infernos = pd.concat([active_infernos, temp_inf])

        return active_infernos, active_smokes, active_he_smokes



    # 12. Add numerical match id
    def _TABULAR_numerical_match_id(self, tabular_df):

        if type(self.numerical_match_id) is not int:
            raise ValueError("Numerical match id must be an integer.")
        
        new_columns = pd.DataFrame({
            'numerical_match_id': self.numerical_match_id
        }, index=tabular_df.index)
        tabular_df = pd.concat([tabular_df, new_columns], axis=1)

        return tabular_df



    # 13. Function to extend the dataframe with copies of the rounds with varied player permutations
    def _TABULAR_player_permutation(self, df, num_permutations_per_round=3):
        """
        Function to extend the dataframe with copies of the rounds with varied player permutations.

        Parameters:
            - df: the dataframe to extend.
            - num_permutations_per_round: the number of permutations to create per round.
        """

        # Get the unique rounds and store team 1 and two player numbers
        team_1_indicies = [0, 1, 2, 3, 4]
        team_2_indicies = [5, 6, 7, 8, 9]
        rounds = df['round'].unique()

        for rnd in rounds:
            for _permutation in range(num_permutations_per_round):
                # Get the round dataframe
                round_df = df[df['round'] == rnd].copy()
                round_df = round_df.reset_index(drop=True)

                # Rename all columns starting with 'player' to start with 'playerPERM'
                player_cols = [col for col in round_df.columns if col.startswith('player')]
                for col in player_cols:
                    round_df.rename(columns={col: 'playerPERM' + col[6:]}, inplace=True)

                # Get random permutations for both teams
                random.shuffle(team_1_indicies)
                random.shuffle(team_1_indicies)

                # Player columns
                player_0_cols = [col for col in round_df.columns if col.startswith('playerPERM0')]
                player_1_cols = [col for col in round_df.columns if col.startswith('playerPERM1')]
                player_2_cols = [col for col in round_df.columns if col.startswith('playerPERM2')]
                player_3_cols = [col for col in round_df.columns if col.startswith('playerPERM3')]
                player_4_cols = [col for col in round_df.columns if col.startswith('playerPERM4')]

                player_5_cols = [col for col in round_df.columns if col.startswith('playerPERM5')]
                player_6_cols = [col for col in round_df.columns if col.startswith('playerPERM6')]
                player_7_cols = [col for col in round_df.columns if col.startswith('playerPERM7')]
                player_8_cols = [col for col in round_df.columns if col.startswith('playerPERM8')]
                player_9_cols = [col for col in round_df.columns if col.startswith('playerPERM9')]

                # Rewrite the player columns with the new permutations
                for col in player_0_cols:
                    round_df.rename(columns={col: 'player' + str(team_1_indicies[0]) + col[11:]}, inplace=True)
                for col in player_1_cols:
                    round_df.rename(columns={col: 'player' + str(team_1_indicies[1]) + col[11:]}, inplace=True)
                for col in player_2_cols:
                    round_df.rename(columns={col: 'player' + str(team_1_indicies[2]) + col[11:]}, inplace=True)
                for col in player_3_cols:
                    round_df.rename(columns={col: 'player' + str(team_1_indicies[3]) + col[11:]}, inplace=True)
                for col in player_4_cols:
                    round_df.rename(columns={col: 'player' + str(team_1_indicies[4]) + col[11:]}, inplace=True)

                for col in player_5_cols:
                    round_df.rename(columns={col: 'player' + str(team_2_indicies[0]) + col[11:]}, inplace=True)
                for col in player_6_cols:
                    round_df.rename(columns={col: 'player' + str(team_2_indicies[1]) + col[11:]}, inplace=True)
                for col in player_7_cols:
                    round_df.rename(columns={col: 'player' + str(team_2_indicies[2]) + col[11:]}, inplace=True)
                for col in player_8_cols:
                    round_df.rename(columns={col: 'player' + str(team_2_indicies[3]) + col[11:]}, inplace=True)
                for col in player_9_cols:
                    round_df.rename(columns={col: 'player' + str(team_2_indicies[4]) + col[11:]}, inplace=True)

                # Append the new round to the dataframe
                df = pd.concat([df, round_df])

        return df



    # 14. Rearrange the player columns so that the CTs are always from 0 to 4 and Ts are from 5 to 9
    def _TABULAR_refactor_player_columns(self, df):

        # Separate the CT and T halves
        team_1_ct = df.loc[df['player0_is_CT'] == True].copy()
        team_2_ct = df.loc[df['player0_is_CT'] == False].copy()

        # Rename the columns for team_1_ct
        for col in team_1_ct.columns:
            if col.startswith('player') and int(col[6]) < 5:
                team_1_ct.rename(columns={col: col.replace('player', 'CT')}, inplace=True)
            elif col.startswith('player') and int(col[6]) >= 5:
                team_1_ct.rename(columns={col: col.replace('player', 'T')}, inplace=True)

        # Rename the columns for team_2_ct
        for col in team_2_ct.columns:
            if col.startswith('player') and int(col[6]) <= 4:
                team_2_ct.rename(columns={col: col.replace('player' + col[6],  'T' + str(int(col[6]) + 5))}, inplace=True)
            elif col.startswith('player') and int(col[6]) > 4:
                team_2_ct.rename(columns={col: col.replace('player' + col[6], 'CT' + str(int(col[6]) - 5))}, inplace=True)


        # Column order
        col_order = [
            'CT0_name', 'CT0_team_clan_name', 'CT0_X', 'CT0_Y', 'CT0_Z', 'CT0_pitch', 'CT0_yaw', 'CT0_velocity_X', 'CT0_velocity_Y', 'CT0_velocity_Z', 'CT0_health', 'CT0_armor_value', 'CT0_active_weapon_magazine_size', 'CT0_active_weapon_ammo', 'CT0_active_weapon_magazine_ammo_left_%', 'CT0_active_weapon_max_ammo', 'CT0_total_ammo_left', 'CT0_active_weapon_total_ammo_left_%', 'CT0_flash_duration', 'CT0_flash_max_alpha', 'CT0_balance', 'CT0_current_equip_value', 'CT0_round_start_equip_value', 'CT0_cash_spent_this_round',
            'CT0_is_alive', 'CT0_is_CT', 'CT0_is_shooting', 'CT0_is_crouching', 'CT0_is_ducking', 'CT0_is_duck_jumping', 'CT0_is_walking', 'CT0_is_spotted', 'CT0_is_scoped', 'CT0_is_defusing', 'CT0_is_reloading', 'CT0_is_in_bombsite',
            'CT0_zoom_lvl', 'CT0_velo_modifier',
            'CT0_stat_kills', 'CT0_stat_HS_kills', 'CT0_stat_opening_kills', 'CT0_stat_MVPs', 'CT0_stat_deaths', 'CT0_stat_opening_deaths', 'CT0_stat_assists', 'CT0_stat_flash_assists', 'CT0_stat_damage', 'CT0_stat_weapon_damage', 'CT0_stat_nade_damage', 'CT0_stat_survives', 'CT0_stat_KPR', 'CT0_stat_ADR', 'CT0_stat_DPR', 'CT0_stat_HS%', 'CT0_stat_SPR', 
            'CT0_inventory_C4', 'CT0_inventory_Taser', 'CT0_inventory_USP-S', 'CT0_inventory_P2000', 'CT0_inventory_Glock-18', 'CT0_inventory_Dual Berettas', 'CT0_inventory_P250', 'CT0_inventory_Tec-9', 'CT0_inventory_CZ75 Auto', 'CT0_inventory_Five-SeveN', 'CT0_inventory_Desert Eagle', 'CT0_inventory_R8 Revolver', 'CT0_inventory_MAC-10', 'CT0_inventory_MP9', 'CT0_inventory_MP7', 'CT0_inventory_MP5-SD', 'CT0_inventory_UMP-45', 'CT0_inventory_PP-Bizon', 'CT0_inventory_P90', 'CT0_inventory_Nova', 'CT0_inventory_XM1014', 'CT0_inventory_Sawed-Off', 'CT0_inventory_MAG-7', 'CT0_inventory_M249', 'CT0_inventory_Negev', 'CT0_inventory_FAMAS', 'CT0_inventory_Galil AR', 'CT0_inventory_AK-47', 'CT0_inventory_M4A4', 'CT0_inventory_M4A1-S', 'CT0_inventory_SG 553', 'CT0_inventory_AUG', 'CT0_inventory_SSG 08', 'CT0_inventory_AWP', 'CT0_inventory_G3SG1', 'CT0_inventory_SCAR-20', 'CT0_inventory_HE Grenade', 'CT0_inventory_Flashbang', 'CT0_inventory_Smoke Grenade', 'CT0_inventory_Incendiary Grenade', 'CT0_inventory_Molotov', 'CT0_inventory_Decoy Grenade',
            'CT0_active_weapon_C4', 'CT0_active_weapon_Knife', 'CT0_active_weapon_Taser', 'CT0_active_weapon_USP-S', 'CT0_active_weapon_P2000', 'CT0_active_weapon_Glock-18', 'CT0_active_weapon_Dual Berettas', 'CT0_active_weapon_P250', 'CT0_active_weapon_Tec-9', 'CT0_active_weapon_CZ75 Auto', 'CT0_active_weapon_Five-SeveN', 'CT0_active_weapon_Desert Eagle', 'CT0_active_weapon_R8 Revolver', 'CT0_active_weapon_MAC-10', 'CT0_active_weapon_MP9', 'CT0_active_weapon_MP7', 'CT0_active_weapon_MP5-SD', 'CT0_active_weapon_UMP-45', 'CT0_active_weapon_PP-Bizon', 'CT0_active_weapon_P90', 'CT0_active_weapon_Nova', 'CT0_active_weapon_XM1014', 'CT0_active_weapon_Sawed-Off', 'CT0_active_weapon_MAG-7', 'CT0_active_weapon_M249', 'CT0_active_weapon_Negev', 'CT0_active_weapon_FAMAS', 'CT0_active_weapon_Galil AR', 'CT0_active_weapon_AK-47', 'CT0_active_weapon_M4A4', 'CT0_active_weapon_M4A1-S', 'CT0_active_weapon_SG 553', 'CT0_active_weapon_AUG', 'CT0_active_weapon_SSG 08', 'CT0_active_weapon_AWP', 'CT0_active_weapon_G3SG1', 'CT0_active_weapon_SCAR-20', 'CT0_active_weapon_HE Grenade', 'CT0_active_weapon_Flashbang', 'CT0_active_weapon_Smoke Grenade', 'CT0_active_weapon_Incendiary Grenade', 'CT0_active_weapon_Molotov', 'CT0_active_weapon_Decoy Grenade',
            'CT0_hltv_rating_2.0', 'CT0_hltv_DPR', 'CT0_hltv_KAST', 'CT0_hltv_Impact', 'CT0_hltv_ADR', 'CT0_hltv_KPR', 'CT0_hltv_total_kills', 'CT0_hltv_HS%', 'CT0_hltv_total_deaths', 'CT0_hltv_KD_ratio', 'CT0_hltv_dmgPR', 'CT0_hltv_grenade_dmgPR', 'CT0_hltv_maps_played', 'CT0_hltv_saved_by_teammatePR', 'CT0_hltv_saved_teammatesPR', 'CT0_hltv_opening_kill_rating', 'CT0_hltv_team_W%_after_opening', 'CT0_hltv_opening_kill_in_W_rounds', 'CT0_hltv_rating_1.0_all_Career', 'CT0_hltv_clutches_1on1_ratio', 'CT0_hltv_clutches_won_1on1', 'CT0_hltv_clutches_won_1on2', 'CT0_hltv_clutches_won_1on3', 'CT0_hltv_clutches_won_1on4', 'CT0_hltv_clutches_won_1on5', 
                
            'CT1_name', 'CT1_team_clan_name', 'CT1_X', 'CT1_Y', 'CT1_Z', 'CT1_pitch', 'CT1_yaw', 'CT1_velocity_X', 'CT1_velocity_Y', 'CT1_velocity_Z', 'CT1_health', 'CT1_armor_value', 'CT1_active_weapon_magazine_size', 'CT1_active_weapon_ammo', 'CT1_active_weapon_magazine_ammo_left_%', 'CT1_active_weapon_max_ammo', 'CT1_total_ammo_left', 'CT1_active_weapon_total_ammo_left_%', 'CT1_flash_duration', 'CT1_flash_max_alpha', 'CT1_balance', 'CT1_current_equip_value', 'CT1_round_start_equip_value', 'CT1_cash_spent_this_round',
            'CT1_is_alive', 'CT1_is_CT', 'CT1_is_shooting', 'CT1_is_crouching', 'CT1_is_ducking', 'CT1_is_duck_jumping', 'CT1_is_walking', 'CT1_is_spotted', 'CT1_is_scoped', 'CT1_is_defusing', 'CT1_is_reloading', 'CT1_is_in_bombsite',
            'CT1_zoom_lvl', 'CT1_velo_modifier',
            'CT1_stat_kills', 'CT1_stat_HS_kills', 'CT1_stat_opening_kills', 'CT1_stat_MVPs', 'CT1_stat_deaths', 'CT1_stat_opening_deaths', 'CT1_stat_assists', 'CT1_stat_flash_assists', 'CT1_stat_damage', 'CT1_stat_weapon_damage', 'CT1_stat_nade_damage', 'CT1_stat_survives', 'CT1_stat_KPR', 'CT1_stat_ADR', 'CT1_stat_DPR', 'CT1_stat_HS%', 'CT1_stat_SPR', 
            'CT1_inventory_C4', 'CT1_inventory_Taser', 'CT1_inventory_USP-S', 'CT1_inventory_P2000', 'CT1_inventory_Glock-18', 'CT1_inventory_Dual Berettas', 'CT1_inventory_P250', 'CT1_inventory_Tec-9', 'CT1_inventory_CZ75 Auto', 'CT1_inventory_Five-SeveN', 'CT1_inventory_Desert Eagle', 'CT1_inventory_R8 Revolver', 'CT1_inventory_MAC-10', 'CT1_inventory_MP9', 'CT1_inventory_MP7', 'CT1_inventory_MP5-SD', 'CT1_inventory_UMP-45', 'CT1_inventory_PP-Bizon', 'CT1_inventory_P90', 'CT1_inventory_Nova', 'CT1_inventory_XM1014', 'CT1_inventory_Sawed-Off', 'CT1_inventory_MAG-7', 'CT1_inventory_M249', 'CT1_inventory_Negev', 'CT1_inventory_FAMAS', 'CT1_inventory_Galil AR', 'CT1_inventory_AK-47', 'CT1_inventory_M4A4', 'CT1_inventory_M4A1-S', 'CT1_inventory_SG 553', 'CT1_inventory_AUG', 'CT1_inventory_SSG 08', 'CT1_inventory_AWP', 'CT1_inventory_G3SG1', 'CT1_inventory_SCAR-20', 'CT1_inventory_HE Grenade', 'CT1_inventory_Flashbang', 'CT1_inventory_Smoke Grenade', 'CT1_inventory_Incendiary Grenade', 'CT1_inventory_Molotov', 'CT1_inventory_Decoy Grenade',
            'CT1_active_weapon_C4', 'CT1_active_weapon_Knife', 'CT1_active_weapon_Taser', 'CT1_active_weapon_USP-S', 'CT1_active_weapon_P2000', 'CT1_active_weapon_Glock-18', 'CT1_active_weapon_Dual Berettas', 'CT1_active_weapon_P250', 'CT1_active_weapon_Tec-9', 'CT1_active_weapon_CZ75 Auto', 'CT1_active_weapon_Five-SeveN', 'CT1_active_weapon_Desert Eagle', 'CT1_active_weapon_R8 Revolver', 'CT1_active_weapon_MAC-10', 'CT1_active_weapon_MP9', 'CT1_active_weapon_MP7', 'CT1_active_weapon_MP5-SD', 'CT1_active_weapon_UMP-45', 'CT1_active_weapon_PP-Bizon', 'CT1_active_weapon_P90', 'CT1_active_weapon_Nova', 'CT1_active_weapon_XM1014', 'CT1_active_weapon_Sawed-Off', 'CT1_active_weapon_MAG-7', 'CT1_active_weapon_M249', 'CT1_active_weapon_Negev', 'CT1_active_weapon_FAMAS', 'CT1_active_weapon_Galil AR', 'CT1_active_weapon_AK-47', 'CT1_active_weapon_M4A4', 'CT1_active_weapon_M4A1-S', 'CT1_active_weapon_SG 553', 'CT1_active_weapon_AUG', 'CT1_active_weapon_SSG 08', 'CT1_active_weapon_AWP', 'CT1_active_weapon_G3SG1', 'CT1_active_weapon_SCAR-20', 'CT1_active_weapon_HE Grenade', 'CT1_active_weapon_Flashbang', 'CT1_active_weapon_Smoke Grenade', 'CT1_active_weapon_Incendiary Grenade', 'CT1_active_weapon_Molotov', 'CT1_active_weapon_Decoy Grenade',
            'CT1_hltv_rating_2.0', 'CT1_hltv_DPR', 'CT1_hltv_KAST', 'CT1_hltv_Impact', 'CT1_hltv_ADR', 'CT1_hltv_KPR', 'CT1_hltv_total_kills', 'CT1_hltv_HS%', 'CT1_hltv_total_deaths', 'CT1_hltv_KD_ratio', 'CT1_hltv_dmgPR', 'CT1_hltv_grenade_dmgPR', 'CT1_hltv_maps_played', 'CT1_hltv_saved_by_teammatePR', 'CT1_hltv_saved_teammatesPR', 'CT1_hltv_opening_kill_rating', 'CT1_hltv_team_W%_after_opening', 'CT1_hltv_opening_kill_in_W_rounds', 'CT1_hltv_rating_1.0_all_Career', 'CT1_hltv_clutches_1on1_ratio', 'CT1_hltv_clutches_won_1on1', 'CT1_hltv_clutches_won_1on2', 'CT1_hltv_clutches_won_1on3', 'CT1_hltv_clutches_won_1on4', 'CT1_hltv_clutches_won_1on5', 

            'CT2_name', 'CT2_team_clan_name', 'CT2_X', 'CT2_Y', 'CT2_Z', 'CT2_pitch', 'CT2_yaw', 'CT2_velocity_X', 'CT2_velocity_Y', 'CT2_velocity_Z', 'CT2_health', 'CT2_armor_value', 'CT2_active_weapon_magazine_size', 'CT2_active_weapon_ammo', 'CT2_active_weapon_magazine_ammo_left_%', 'CT2_active_weapon_max_ammo', 'CT2_total_ammo_left', 'CT2_active_weapon_total_ammo_left_%', 'CT2_flash_duration', 'CT2_flash_max_alpha', 'CT2_balance', 'CT2_current_equip_value', 'CT2_round_start_equip_value', 'CT2_cash_spent_this_round',
            'CT2_is_alive', 'CT2_is_CT', 'CT2_is_shooting', 'CT2_is_crouching', 'CT2_is_ducking', 'CT2_is_duck_jumping', 'CT2_is_walking', 'CT2_is_spotted', 'CT2_is_scoped', 'CT2_is_defusing', 'CT2_is_reloading', 'CT2_is_in_bombsite',
            'CT2_zoom_lvl', 'CT2_velo_modifier',
            'CT2_stat_kills', 'CT2_stat_HS_kills', 'CT2_stat_opening_kills', 'CT2_stat_MVPs', 'CT2_stat_deaths', 'CT2_stat_opening_deaths', 'CT2_stat_assists', 'CT2_stat_flash_assists', 'CT2_stat_damage', 'CT2_stat_weapon_damage', 'CT2_stat_nade_damage', 'CT2_stat_survives', 'CT2_stat_KPR', 'CT2_stat_ADR', 'CT2_stat_DPR', 'CT2_stat_HS%', 'CT2_stat_SPR', 
            'CT2_inventory_C4', 'CT2_inventory_Taser', 'CT2_inventory_USP-S', 'CT2_inventory_P2000', 'CT2_inventory_Glock-18', 'CT2_inventory_Dual Berettas', 'CT2_inventory_P250', 'CT2_inventory_Tec-9', 'CT2_inventory_CZ75 Auto', 'CT2_inventory_Five-SeveN', 'CT2_inventory_Desert Eagle', 'CT2_inventory_R8 Revolver', 'CT2_inventory_MAC-10', 'CT2_inventory_MP9', 'CT2_inventory_MP7', 'CT2_inventory_MP5-SD', 'CT2_inventory_UMP-45', 'CT2_inventory_PP-Bizon', 'CT2_inventory_P90', 'CT2_inventory_Nova', 'CT2_inventory_XM1014', 'CT2_inventory_Sawed-Off', 'CT2_inventory_MAG-7', 'CT2_inventory_M249', 'CT2_inventory_Negev', 'CT2_inventory_FAMAS', 'CT2_inventory_Galil AR', 'CT2_inventory_AK-47', 'CT2_inventory_M4A4', 'CT2_inventory_M4A1-S', 'CT2_inventory_SG 553', 'CT2_inventory_AUG', 'CT2_inventory_SSG 08', 'CT2_inventory_AWP', 'CT2_inventory_G3SG1', 'CT2_inventory_SCAR-20', 'CT2_inventory_HE Grenade', 'CT2_inventory_Flashbang', 'CT2_inventory_Smoke Grenade', 'CT2_inventory_Incendiary Grenade', 'CT2_inventory_Molotov', 'CT2_inventory_Decoy Grenade',
            'CT2_active_weapon_C4', 'CT2_active_weapon_Knife', 'CT2_active_weapon_Taser', 'CT2_active_weapon_USP-S', 'CT2_active_weapon_P2000', 'CT2_active_weapon_Glock-18', 'CT2_active_weapon_Dual Berettas', 'CT2_active_weapon_P250', 'CT2_active_weapon_Tec-9', 'CT2_active_weapon_CZ75 Auto', 'CT2_active_weapon_Five-SeveN', 'CT2_active_weapon_Desert Eagle', 'CT2_active_weapon_R8 Revolver', 'CT2_active_weapon_MAC-10', 'CT2_active_weapon_MP9', 'CT2_active_weapon_MP7', 'CT2_active_weapon_MP5-SD', 'CT2_active_weapon_UMP-45', 'CT2_active_weapon_PP-Bizon', 'CT2_active_weapon_P90', 'CT2_active_weapon_Nova', 'CT2_active_weapon_XM1014', 'CT2_active_weapon_Sawed-Off', 'CT2_active_weapon_MAG-7', 'CT2_active_weapon_M249', 'CT2_active_weapon_Negev', 'CT2_active_weapon_FAMAS', 'CT2_active_weapon_Galil AR', 'CT2_active_weapon_AK-47', 'CT2_active_weapon_M4A4', 'CT2_active_weapon_M4A1-S', 'CT2_active_weapon_SG 553', 'CT2_active_weapon_AUG', 'CT2_active_weapon_SSG 08', 'CT2_active_weapon_AWP', 'CT2_active_weapon_G3SG1', 'CT2_active_weapon_SCAR-20', 'CT2_active_weapon_HE Grenade', 'CT2_active_weapon_Flashbang', 'CT2_active_weapon_Smoke Grenade', 'CT2_active_weapon_Incendiary Grenade', 'CT2_active_weapon_Molotov', 'CT2_active_weapon_Decoy Grenade',
            'CT2_hltv_rating_2.0', 'CT2_hltv_DPR', 'CT2_hltv_KAST', 'CT2_hltv_Impact', 'CT2_hltv_ADR', 'CT2_hltv_KPR', 'CT2_hltv_total_kills', 'CT2_hltv_HS%', 'CT2_hltv_total_deaths', 'CT2_hltv_KD_ratio', 'CT2_hltv_dmgPR', 'CT2_hltv_grenade_dmgPR', 'CT2_hltv_maps_played', 'CT2_hltv_saved_by_teammatePR', 'CT2_hltv_saved_teammatesPR', 'CT2_hltv_opening_kill_rating', 'CT2_hltv_team_W%_after_opening', 'CT2_hltv_opening_kill_in_W_rounds', 'CT2_hltv_rating_1.0_all_Career', 'CT2_hltv_clutches_1on1_ratio', 'CT2_hltv_clutches_won_1on1', 'CT2_hltv_clutches_won_1on2', 'CT2_hltv_clutches_won_1on3', 'CT2_hltv_clutches_won_1on4', 'CT2_hltv_clutches_won_1on5', 

            'CT3_name', 'CT3_team_clan_name', 'CT3_X', 'CT3_Y', 'CT3_Z', 'CT3_pitch', 'CT3_yaw', 'CT3_velocity_X', 'CT3_velocity_Y', 'CT3_velocity_Z', 'CT3_health', 'CT3_armor_value', 'CT3_active_weapon_magazine_size', 'CT3_active_weapon_ammo', 'CT3_active_weapon_magazine_ammo_left_%', 'CT3_active_weapon_max_ammo', 'CT3_total_ammo_left', 'CT3_active_weapon_total_ammo_left_%', 'CT3_flash_duration', 'CT3_flash_max_alpha', 'CT3_balance', 'CT3_current_equip_value', 'CT3_round_start_equip_value', 'CT3_cash_spent_this_round',
            'CT3_is_alive', 'CT3_is_CT', 'CT3_is_shooting', 'CT3_is_crouching', 'CT3_is_ducking', 'CT3_is_duck_jumping', 'CT3_is_walking', 'CT3_is_spotted', 'CT3_is_scoped', 'CT3_is_defusing', 'CT3_is_reloading', 'CT3_is_in_bombsite',
            'CT3_zoom_lvl', 'CT3_velo_modifier',
            'CT3_stat_kills', 'CT3_stat_HS_kills', 'CT3_stat_opening_kills', 'CT3_stat_MVPs', 'CT3_stat_deaths', 'CT3_stat_opening_deaths', 'CT3_stat_assists', 'CT3_stat_flash_assists', 'CT3_stat_damage', 'CT3_stat_weapon_damage', 'CT3_stat_nade_damage', 'CT3_stat_survives', 'CT3_stat_KPR', 'CT3_stat_ADR', 'CT3_stat_DPR', 'CT3_stat_HS%', 'CT3_stat_SPR', 
            'CT3_inventory_C4', 'CT3_inventory_Taser', 'CT3_inventory_USP-S', 'CT3_inventory_P2000', 'CT3_inventory_Glock-18', 'CT3_inventory_Dual Berettas', 'CT3_inventory_P250', 'CT3_inventory_Tec-9', 'CT3_inventory_CZ75 Auto', 'CT3_inventory_Five-SeveN', 'CT3_inventory_Desert Eagle', 'CT3_inventory_R8 Revolver', 'CT3_inventory_MAC-10', 'CT3_inventory_MP9', 'CT3_inventory_MP7', 'CT3_inventory_MP5-SD', 'CT3_inventory_UMP-45', 'CT3_inventory_PP-Bizon', 'CT3_inventory_P90', 'CT3_inventory_Nova', 'CT3_inventory_XM1014', 'CT3_inventory_Sawed-Off', 'CT3_inventory_MAG-7', 'CT3_inventory_M249', 'CT3_inventory_Negev', 'CT3_inventory_FAMAS', 'CT3_inventory_Galil AR', 'CT3_inventory_AK-47', 'CT3_inventory_M4A4', 'CT3_inventory_M4A1-S', 'CT3_inventory_SG 553', 'CT3_inventory_AUG', 'CT3_inventory_SSG 08', 'CT3_inventory_AWP', 'CT3_inventory_G3SG1', 'CT3_inventory_SCAR-20', 'CT3_inventory_HE Grenade', 'CT3_inventory_Flashbang', 'CT3_inventory_Smoke Grenade', 'CT3_inventory_Incendiary Grenade', 'CT3_inventory_Molotov', 'CT3_inventory_Decoy Grenade',
            'CT3_active_weapon_C4', 'CT3_active_weapon_Knife', 'CT3_active_weapon_Taser', 'CT3_active_weapon_USP-S', 'CT3_active_weapon_P2000', 'CT3_active_weapon_Glock-18', 'CT3_active_weapon_Dual Berettas', 'CT3_active_weapon_P250', 'CT3_active_weapon_Tec-9', 'CT3_active_weapon_CZ75 Auto', 'CT3_active_weapon_Five-SeveN', 'CT3_active_weapon_Desert Eagle', 'CT3_active_weapon_R8 Revolver', 'CT3_active_weapon_MAC-10', 'CT3_active_weapon_MP9', 'CT3_active_weapon_MP7', 'CT3_active_weapon_MP5-SD', 'CT3_active_weapon_UMP-45', 'CT3_active_weapon_PP-Bizon', 'CT3_active_weapon_P90', 'CT3_active_weapon_Nova', 'CT3_active_weapon_XM1014', 'CT3_active_weapon_Sawed-Off', 'CT3_active_weapon_MAG-7', 'CT3_active_weapon_M249', 'CT3_active_weapon_Negev', 'CT3_active_weapon_FAMAS', 'CT3_active_weapon_Galil AR', 'CT3_active_weapon_AK-47', 'CT3_active_weapon_M4A4', 'CT3_active_weapon_M4A1-S', 'CT3_active_weapon_SG 553', 'CT3_active_weapon_AUG', 'CT3_active_weapon_SSG 08', 'CT3_active_weapon_AWP', 'CT3_active_weapon_G3SG1', 'CT3_active_weapon_SCAR-20', 'CT3_active_weapon_HE Grenade', 'CT3_active_weapon_Flashbang', 'CT3_active_weapon_Smoke Grenade', 'CT3_active_weapon_Incendiary Grenade', 'CT3_active_weapon_Molotov', 'CT3_active_weapon_Decoy Grenade',
            'CT3_hltv_rating_2.0', 'CT3_hltv_DPR', 'CT3_hltv_KAST', 'CT3_hltv_Impact', 'CT3_hltv_ADR', 'CT3_hltv_KPR', 'CT3_hltv_total_kills', 'CT3_hltv_HS%', 'CT3_hltv_total_deaths', 'CT3_hltv_KD_ratio', 'CT3_hltv_dmgPR', 'CT3_hltv_grenade_dmgPR', 'CT3_hltv_maps_played', 'CT3_hltv_saved_by_teammatePR', 'CT3_hltv_saved_teammatesPR', 'CT3_hltv_opening_kill_rating', 'CT3_hltv_team_W%_after_opening', 'CT3_hltv_opening_kill_in_W_rounds', 'CT3_hltv_rating_1.0_all_Career', 'CT3_hltv_clutches_1on1_ratio', 'CT3_hltv_clutches_won_1on1', 'CT3_hltv_clutches_won_1on2', 'CT3_hltv_clutches_won_1on3', 'CT3_hltv_clutches_won_1on4', 'CT3_hltv_clutches_won_1on5', 

            'CT4_name', 'CT4_team_clan_name', 'CT4_X', 'CT4_Y', 'CT4_Z', 'CT4_pitch', 'CT4_yaw', 'CT4_velocity_X', 'CT4_velocity_Y', 'CT4_velocity_Z', 'CT4_health', 'CT4_armor_value', 'CT4_active_weapon_magazine_size', 'CT4_active_weapon_ammo', 'CT4_active_weapon_magazine_ammo_left_%', 'CT4_active_weapon_max_ammo', 'CT4_total_ammo_left', 'CT4_active_weapon_total_ammo_left_%', 'CT4_flash_duration', 'CT4_flash_max_alpha', 'CT4_balance', 'CT4_current_equip_value', 'CT4_round_start_equip_value', 'CT4_cash_spent_this_round',
            'CT4_is_alive', 'CT4_is_CT', 'CT4_is_shooting', 'CT4_is_crouching', 'CT4_is_ducking', 'CT4_is_duck_jumping', 'CT4_is_walking', 'CT4_is_spotted', 'CT4_is_scoped', 'CT4_is_defusing', 'CT4_is_reloading', 'CT4_is_in_bombsite',
            'CT4_zoom_lvl', 'CT4_velo_modifier',
            'CT4_stat_kills', 'CT4_stat_HS_kills', 'CT4_stat_opening_kills', 'CT4_stat_MVPs', 'CT4_stat_deaths', 'CT4_stat_opening_deaths', 'CT4_stat_assists', 'CT4_stat_flash_assists', 'CT4_stat_damage', 'CT4_stat_weapon_damage', 'CT4_stat_nade_damage', 'CT4_stat_survives', 'CT4_stat_KPR', 'CT4_stat_ADR', 'CT4_stat_DPR', 'CT4_stat_HS%', 'CT4_stat_SPR', 
            'CT4_inventory_C4', 'CT4_inventory_Taser', 'CT4_inventory_USP-S', 'CT4_inventory_P2000', 'CT4_inventory_Glock-18', 'CT4_inventory_Dual Berettas', 'CT4_inventory_P250', 'CT4_inventory_Tec-9', 'CT4_inventory_CZ75 Auto', 'CT4_inventory_Five-SeveN', 'CT4_inventory_Desert Eagle', 'CT4_inventory_R8 Revolver', 'CT4_inventory_MAC-10', 'CT4_inventory_MP9', 'CT4_inventory_MP7', 'CT4_inventory_MP5-SD', 'CT4_inventory_UMP-45', 'CT4_inventory_PP-Bizon', 'CT4_inventory_P90', 'CT4_inventory_Nova', 'CT4_inventory_XM1014', 'CT4_inventory_Sawed-Off', 'CT4_inventory_MAG-7', 'CT4_inventory_M249', 'CT4_inventory_Negev', 'CT4_inventory_FAMAS', 'CT4_inventory_Galil AR', 'CT4_inventory_AK-47', 'CT4_inventory_M4A4', 'CT4_inventory_M4A1-S', 'CT4_inventory_SG 553', 'CT4_inventory_AUG', 'CT4_inventory_SSG 08', 'CT4_inventory_AWP', 'CT4_inventory_G3SG1', 'CT4_inventory_SCAR-20', 'CT4_inventory_HE Grenade', 'CT4_inventory_Flashbang', 'CT4_inventory_Smoke Grenade', 'CT4_inventory_Incendiary Grenade', 'CT4_inventory_Molotov', 'CT4_inventory_Decoy Grenade',
            'CT4_active_weapon_C4', 'CT4_active_weapon_Knife', 'CT4_active_weapon_Taser', 'CT4_active_weapon_USP-S', 'CT4_active_weapon_P2000', 'CT4_active_weapon_Glock-18', 'CT4_active_weapon_Dual Berettas', 'CT4_active_weapon_P250', 'CT4_active_weapon_Tec-9', 'CT4_active_weapon_CZ75 Auto', 'CT4_active_weapon_Five-SeveN', 'CT4_active_weapon_Desert Eagle', 'CT4_active_weapon_R8 Revolver', 'CT4_active_weapon_MAC-10', 'CT4_active_weapon_MP9', 'CT4_active_weapon_MP7', 'CT4_active_weapon_MP5-SD', 'CT4_active_weapon_UMP-45', 'CT4_active_weapon_PP-Bizon', 'CT4_active_weapon_P90', 'CT4_active_weapon_Nova', 'CT4_active_weapon_XM1014', 'CT4_active_weapon_Sawed-Off', 'CT4_active_weapon_MAG-7', 'CT4_active_weapon_M249', 'CT4_active_weapon_Negev', 'CT4_active_weapon_FAMAS', 'CT4_active_weapon_Galil AR', 'CT4_active_weapon_AK-47', 'CT4_active_weapon_M4A4', 'CT4_active_weapon_M4A1-S', 'CT4_active_weapon_SG 553', 'CT4_active_weapon_AUG', 'CT4_active_weapon_SSG 08', 'CT4_active_weapon_AWP', 'CT4_active_weapon_G3SG1', 'CT4_active_weapon_SCAR-20', 'CT4_active_weapon_HE Grenade', 'CT4_active_weapon_Flashbang', 'CT4_active_weapon_Smoke Grenade', 'CT4_active_weapon_Incendiary Grenade', 'CT4_active_weapon_Molotov', 'CT4_active_weapon_Decoy Grenade',
            'CT4_hltv_rating_2.0', 'CT4_hltv_DPR', 'CT4_hltv_KAST', 'CT4_hltv_Impact', 'CT4_hltv_ADR', 'CT4_hltv_KPR', 'CT4_hltv_total_kills', 'CT4_hltv_HS%', 'CT4_hltv_total_deaths', 'CT4_hltv_KD_ratio', 'CT4_hltv_dmgPR', 'CT4_hltv_grenade_dmgPR', 'CT4_hltv_maps_played', 'CT4_hltv_saved_by_teammatePR', 'CT4_hltv_saved_teammatesPR', 'CT4_hltv_opening_kill_rating', 'CT4_hltv_team_W%_after_opening', 'CT4_hltv_opening_kill_in_W_rounds', 'CT4_hltv_rating_1.0_all_Career', 'CT4_hltv_clutches_1on1_ratio', 'CT4_hltv_clutches_won_1on1', 'CT4_hltv_clutches_won_1on2', 'CT4_hltv_clutches_won_1on3', 'CT4_hltv_clutches_won_1on4', 'CT4_hltv_clutches_won_1on5', 

            'T5_name', 'T5_team_clan_name', 'T5_X', 'T5_Y', 'T5_Z', 'T5_pitch', 'T5_yaw', 'T5_velocity_X', 'T5_velocity_Y', 'T5_velocity_Z', 'T5_health', 'T5_armor_value', 'T5_active_weapon_magazine_size', 'T5_active_weapon_ammo', 'T5_active_weapon_magazine_ammo_left_%', 'T5_active_weapon_max_ammo', 'T5_total_ammo_left', 'T5_active_weapon_total_ammo_left_%', 'T5_flash_duration', 'T5_flash_max_alpha', 'T5_balance', 'T5_current_equip_value', 'T5_round_start_equip_value', 'T5_cash_spent_this_round',
            'T5_is_alive', 'T5_is_CT', 'T5_is_shooting', 'T5_is_crouching', 'T5_is_ducking', 'T5_is_duck_jumping', 'T5_is_walking', 'T5_is_spotted', 'T5_is_scoped', 'T5_is_defusing', 'T5_is_reloading', 'T5_is_in_bombsite',
            'T5_zoom_lvl', 'T5_velo_modifier',
            'T5_stat_kills', 'T5_stat_HS_kills', 'T5_stat_opening_kills', 'T5_stat_MVPs', 'T5_stat_deaths', 'T5_stat_opening_deaths', 'T5_stat_assists', 'T5_stat_flash_assists', 'T5_stat_damage', 'T5_stat_weapon_damage', 'T5_stat_nade_damage', 'T5_stat_survives', 'T5_stat_KPR', 'T5_stat_ADR', 'T5_stat_DPR', 'T5_stat_HS%', 'T5_stat_SPR', 
            'T5_inventory_C4', 'T5_inventory_Taser', 'T5_inventory_USP-S', 'T5_inventory_P2000', 'T5_inventory_Glock-18', 'T5_inventory_Dual Berettas', 'T5_inventory_P250', 'T5_inventory_Tec-9', 'T5_inventory_CZ75 Auto', 'T5_inventory_Five-SeveN', 'T5_inventory_Desert Eagle', 'T5_inventory_R8 Revolver', 'T5_inventory_MAC-10', 'T5_inventory_MP9', 'T5_inventory_MP7', 'T5_inventory_MP5-SD', 'T5_inventory_UMP-45', 'T5_inventory_PP-Bizon', 'T5_inventory_P90', 'T5_inventory_Nova', 'T5_inventory_XM1014', 'T5_inventory_Sawed-Off', 'T5_inventory_MAG-7', 'T5_inventory_M249', 'T5_inventory_Negev', 'T5_inventory_FAMAS', 'T5_inventory_Galil AR', 'T5_inventory_AK-47', 'T5_inventory_M4A4', 'T5_inventory_M4A1-S', 'T5_inventory_SG 553', 'T5_inventory_AUG', 'T5_inventory_SSG 08', 'T5_inventory_AWP', 'T5_inventory_G3SG1', 'T5_inventory_SCAR-20', 'T5_inventory_HE Grenade', 'T5_inventory_Flashbang', 'T5_inventory_Smoke Grenade', 'T5_inventory_Incendiary Grenade', 'T5_inventory_Molotov', 'T5_inventory_Decoy Grenade',
            'T5_active_weapon_C4', 'T5_active_weapon_Knife', 'T5_active_weapon_Taser', 'T5_active_weapon_USP-S', 'T5_active_weapon_P2000', 'T5_active_weapon_Glock-18', 'T5_active_weapon_Dual Berettas', 'T5_active_weapon_P250', 'T5_active_weapon_Tec-9', 'T5_active_weapon_CZ75 Auto', 'T5_active_weapon_Five-SeveN', 'T5_active_weapon_Desert Eagle', 'T5_active_weapon_R8 Revolver', 'T5_active_weapon_MAC-10', 'T5_active_weapon_MP9', 'T5_active_weapon_MP7', 'T5_active_weapon_MP5-SD', 'T5_active_weapon_UMP-45', 'T5_active_weapon_PP-Bizon', 'T5_active_weapon_P90', 'T5_active_weapon_Nova', 'T5_active_weapon_XM1014', 'T5_active_weapon_Sawed-Off', 'T5_active_weapon_MAG-7', 'T5_active_weapon_M249', 'T5_active_weapon_Negev', 'T5_active_weapon_FAMAS', 'T5_active_weapon_Galil AR', 'T5_active_weapon_AK-47', 'T5_active_weapon_M4A4', 'T5_active_weapon_M4A1-S', 'T5_active_weapon_SG 553', 'T5_active_weapon_AUG', 'T5_active_weapon_SSG 08', 'T5_active_weapon_AWP', 'T5_active_weapon_G3SG1', 'T5_active_weapon_SCAR-20', 'T5_active_weapon_HE Grenade', 'T5_active_weapon_Flashbang', 'T5_active_weapon_Smoke Grenade', 'T5_active_weapon_Incendiary Grenade', 'T5_active_weapon_Molotov', 'T5_active_weapon_Decoy Grenade',
            'T5_hltv_rating_2.0', 'T5_hltv_DPR', 'T5_hltv_KAST', 'T5_hltv_Impact', 'T5_hltv_ADR', 'T5_hltv_KPR', 'T5_hltv_total_kills', 'T5_hltv_HS%', 'T5_hltv_total_deaths', 'T5_hltv_KD_ratio', 'T5_hltv_dmgPR', 'T5_hltv_grenade_dmgPR', 'T5_hltv_maps_played', 'T5_hltv_saved_by_teammatePR', 'T5_hltv_saved_teammatesPR', 'T5_hltv_opening_kill_rating', 'T5_hltv_team_W%_after_opening', 'T5_hltv_opening_kill_in_W_rounds', 'T5_hltv_rating_1.0_all_Career', 'T5_hltv_clutches_1on1_ratio', 'T5_hltv_clutches_won_1on1', 'T5_hltv_clutches_won_1on2', 'T5_hltv_clutches_won_1on3', 'T5_hltv_clutches_won_1on4', 'T5_hltv_clutches_won_1on5', 

            'T6_name', 'T6_team_clan_name', 'T6_X', 'T6_Y', 'T6_Z', 'T6_pitch', 'T6_yaw', 'T6_velocity_X', 'T6_velocity_Y', 'T6_velocity_Z', 'T6_health', 'T6_armor_value', 'T6_active_weapon_magazine_size', 'T6_active_weapon_ammo', 'T6_active_weapon_magazine_ammo_left_%', 'T6_active_weapon_max_ammo', 'T6_total_ammo_left', 'T6_active_weapon_total_ammo_left_%', 'T6_flash_duration', 'T6_flash_max_alpha', 'T6_balance', 'T6_current_equip_value', 'T6_round_start_equip_value', 'T6_cash_spent_this_round',
            'T6_is_alive', 'T6_is_CT', 'T6_is_shooting', 'T6_is_crouching', 'T6_is_ducking', 'T6_is_duck_jumping', 'T6_is_walking', 'T6_is_spotted', 'T6_is_scoped', 'T6_is_defusing', 'T6_is_reloading', 'T6_is_in_bombsite',
            'T6_zoom_lvl', 'T6_velo_modifier',
            'T6_stat_kills', 'T6_stat_HS_kills', 'T6_stat_opening_kills', 'T6_stat_MVPs', 'T6_stat_deaths', 'T6_stat_opening_deaths', 'T6_stat_assists', 'T6_stat_flash_assists', 'T6_stat_damage', 'T6_stat_weapon_damage', 'T6_stat_nade_damage', 'T6_stat_survives', 'T6_stat_KPR', 'T6_stat_ADR', 'T6_stat_DPR', 'T6_stat_HS%', 'T6_stat_SPR', 
            'T6_inventory_C4', 'T6_inventory_Taser', 'T6_inventory_USP-S', 'T6_inventory_P2000', 'T6_inventory_Glock-18', 'T6_inventory_Dual Berettas', 'T6_inventory_P250', 'T6_inventory_Tec-9', 'T6_inventory_CZ75 Auto', 'T6_inventory_Five-SeveN', 'T6_inventory_Desert Eagle', 'T6_inventory_R8 Revolver', 'T6_inventory_MAC-10', 'T6_inventory_MP9', 'T6_inventory_MP7', 'T6_inventory_MP5-SD', 'T6_inventory_UMP-45', 'T6_inventory_PP-Bizon', 'T6_inventory_P90', 'T6_inventory_Nova', 'T6_inventory_XM1014', 'T6_inventory_Sawed-Off', 'T6_inventory_MAG-7', 'T6_inventory_M249', 'T6_inventory_Negev', 'T6_inventory_FAMAS', 'T6_inventory_Galil AR', 'T6_inventory_AK-47', 'T6_inventory_M4A4', 'T6_inventory_M4A1-S', 'T6_inventory_SG 553', 'T6_inventory_AUG', 'T6_inventory_SSG 08', 'T6_inventory_AWP', 'T6_inventory_G3SG1', 'T6_inventory_SCAR-20', 'T6_inventory_HE Grenade', 'T6_inventory_Flashbang', 'T6_inventory_Smoke Grenade', 'T6_inventory_Incendiary Grenade', 'T6_inventory_Molotov', 'T6_inventory_Decoy Grenade',
            'T6_active_weapon_C4', 'T6_active_weapon_Knife', 'T6_active_weapon_Taser', 'T6_active_weapon_USP-S', 'T6_active_weapon_P2000', 'T6_active_weapon_Glock-18', 'T6_active_weapon_Dual Berettas', 'T6_active_weapon_P250', 'T6_active_weapon_Tec-9', 'T6_active_weapon_CZ75 Auto', 'T6_active_weapon_Five-SeveN', 'T6_active_weapon_Desert Eagle', 'T6_active_weapon_R8 Revolver', 'T6_active_weapon_MAC-10', 'T6_active_weapon_MP9', 'T6_active_weapon_MP7', 'T6_active_weapon_MP5-SD', 'T6_active_weapon_UMP-45', 'T6_active_weapon_PP-Bizon', 'T6_active_weapon_P90', 'T6_active_weapon_Nova', 'T6_active_weapon_XM1014', 'T6_active_weapon_Sawed-Off', 'T6_active_weapon_MAG-7', 'T6_active_weapon_M249', 'T6_active_weapon_Negev', 'T6_active_weapon_FAMAS', 'T6_active_weapon_Galil AR', 'T6_active_weapon_AK-47', 'T6_active_weapon_M4A4', 'T6_active_weapon_M4A1-S', 'T6_active_weapon_SG 553', 'T6_active_weapon_AUG', 'T6_active_weapon_SSG 08', 'T6_active_weapon_AWP', 'T6_active_weapon_G3SG1', 'T6_active_weapon_SCAR-20', 'T6_active_weapon_HE Grenade', 'T6_active_weapon_Flashbang', 'T6_active_weapon_Smoke Grenade', 'T6_active_weapon_Incendiary Grenade', 'T6_active_weapon_Molotov', 'T6_active_weapon_Decoy Grenade',
            'T6_hltv_rating_2.0', 'T6_hltv_DPR', 'T6_hltv_KAST', 'T6_hltv_Impact', 'T6_hltv_ADR', 'T6_hltv_KPR', 'T6_hltv_total_kills', 'T6_hltv_HS%', 'T6_hltv_total_deaths', 'T6_hltv_KD_ratio', 'T6_hltv_dmgPR', 'T6_hltv_grenade_dmgPR', 'T6_hltv_maps_played', 'T6_hltv_saved_by_teammatePR', 'T6_hltv_saved_teammatesPR', 'T6_hltv_opening_kill_rating', 'T6_hltv_team_W%_after_opening', 'T6_hltv_opening_kill_in_W_rounds', 'T6_hltv_rating_1.0_all_Career', 'T6_hltv_clutches_1on1_ratio', 'T6_hltv_clutches_won_1on1', 'T6_hltv_clutches_won_1on2', 'T6_hltv_clutches_won_1on3', 'T6_hltv_clutches_won_1on4', 'T6_hltv_clutches_won_1on5', 

            'T7_name', 'T7_team_clan_name', 'T7_X', 'T7_Y', 'T7_Z', 'T7_pitch', 'T7_yaw', 'T7_velocity_X', 'T7_velocity_Y', 'T7_velocity_Z', 'T7_health', 'T7_armor_value', 'T7_active_weapon_magazine_size', 'T7_active_weapon_ammo', 'T7_active_weapon_magazine_ammo_left_%', 'T7_active_weapon_max_ammo', 'T7_total_ammo_left', 'T7_active_weapon_total_ammo_left_%', 'T7_flash_duration', 'T7_flash_max_alpha', 'T7_balance', 'T7_current_equip_value', 'T7_round_start_equip_value', 'T7_cash_spent_this_round',
            'T7_is_alive', 'T7_is_CT', 'T7_is_shooting', 'T7_is_crouching', 'T7_is_ducking', 'T7_is_duck_jumping', 'T7_is_walking', 'T7_is_spotted', 'T7_is_scoped', 'T7_is_defusing', 'T7_is_reloading', 'T7_is_in_bombsite',
            'T7_zoom_lvl', 'T7_velo_modifier',
            'T7_stat_kills', 'T7_stat_HS_kills', 'T7_stat_opening_kills', 'T7_stat_MVPs', 'T7_stat_deaths', 'T7_stat_opening_deaths', 'T7_stat_assists', 'T7_stat_flash_assists', 'T7_stat_damage', 'T7_stat_weapon_damage', 'T7_stat_nade_damage', 'T7_stat_survives', 'T7_stat_KPR', 'T7_stat_ADR', 'T7_stat_DPR', 'T7_stat_HS%', 'T7_stat_SPR', 
            'T7_inventory_C4', 'T7_inventory_Taser', 'T7_inventory_USP-S', 'T7_inventory_P2000', 'T7_inventory_Glock-18', 'T7_inventory_Dual Berettas', 'T7_inventory_P250', 'T7_inventory_Tec-9', 'T7_inventory_CZ75 Auto', 'T7_inventory_Five-SeveN', 'T7_inventory_Desert Eagle', 'T7_inventory_R8 Revolver', 'T7_inventory_MAC-10', 'T7_inventory_MP9', 'T7_inventory_MP7', 'T7_inventory_MP5-SD', 'T7_inventory_UMP-45', 'T7_inventory_PP-Bizon', 'T7_inventory_P90', 'T7_inventory_Nova', 'T7_inventory_XM1014', 'T7_inventory_Sawed-Off', 'T7_inventory_MAG-7', 'T7_inventory_M249', 'T7_inventory_Negev', 'T7_inventory_FAMAS', 'T7_inventory_Galil AR', 'T7_inventory_AK-47', 'T7_inventory_M4A4', 'T7_inventory_M4A1-S', 'T7_inventory_SG 553', 'T7_inventory_AUG', 'T7_inventory_SSG 08', 'T7_inventory_AWP', 'T7_inventory_G3SG1', 'T7_inventory_SCAR-20', 'T7_inventory_HE Grenade', 'T7_inventory_Flashbang', 'T7_inventory_Smoke Grenade', 'T7_inventory_Incendiary Grenade', 'T7_inventory_Molotov', 'T7_inventory_Decoy Grenade',
            'T7_active_weapon_C4', 'T7_active_weapon_Knife', 'T7_active_weapon_Taser', 'T7_active_weapon_USP-S', 'T7_active_weapon_P2000', 'T7_active_weapon_Glock-18', 'T7_active_weapon_Dual Berettas', 'T7_active_weapon_P250', 'T7_active_weapon_Tec-9', 'T7_active_weapon_CZ75 Auto', 'T7_active_weapon_Five-SeveN', 'T7_active_weapon_Desert Eagle', 'T7_active_weapon_R8 Revolver', 'T7_active_weapon_MAC-10', 'T7_active_weapon_MP9', 'T7_active_weapon_MP7', 'T7_active_weapon_MP5-SD', 'T7_active_weapon_UMP-45', 'T7_active_weapon_PP-Bizon', 'T7_active_weapon_P90', 'T7_active_weapon_Nova', 'T7_active_weapon_XM1014', 'T7_active_weapon_Sawed-Off', 'T7_active_weapon_MAG-7', 'T7_active_weapon_M249', 'T7_active_weapon_Negev', 'T7_active_weapon_FAMAS', 'T7_active_weapon_Galil AR', 'T7_active_weapon_AK-47', 'T7_active_weapon_M4A4', 'T7_active_weapon_M4A1-S', 'T7_active_weapon_SG 553', 'T7_active_weapon_AUG', 'T7_active_weapon_SSG 08', 'T7_active_weapon_AWP', 'T7_active_weapon_G3SG1', 'T7_active_weapon_SCAR-20', 'T7_active_weapon_HE Grenade', 'T7_active_weapon_Flashbang', 'T7_active_weapon_Smoke Grenade', 'T7_active_weapon_Incendiary Grenade', 'T7_active_weapon_Molotov', 'T7_active_weapon_Decoy Grenade',
            'T7_hltv_rating_2.0', 'T7_hltv_DPR', 'T7_hltv_KAST', 'T7_hltv_Impact', 'T7_hltv_ADR', 'T7_hltv_KPR', 'T7_hltv_total_kills', 'T7_hltv_HS%', 'T7_hltv_total_deaths', 'T7_hltv_KD_ratio', 'T7_hltv_dmgPR', 'T7_hltv_grenade_dmgPR', 'T7_hltv_maps_played', 'T7_hltv_saved_by_teammatePR', 'T7_hltv_saved_teammatesPR', 'T7_hltv_opening_kill_rating', 'T7_hltv_team_W%_after_opening', 'T7_hltv_opening_kill_in_W_rounds', 'T7_hltv_rating_1.0_all_Career', 'T7_hltv_clutches_1on1_ratio', 'T7_hltv_clutches_won_1on1', 'T7_hltv_clutches_won_1on2', 'T7_hltv_clutches_won_1on3', 'T7_hltv_clutches_won_1on4', 'T7_hltv_clutches_won_1on5', 

            'T8_name', 'T8_team_clan_name', 'T8_X', 'T8_Y', 'T8_Z', 'T8_pitch', 'T8_yaw', 'T8_velocity_X', 'T8_velocity_Y', 'T8_velocity_Z', 'T8_health', 'T8_armor_value', 'T8_active_weapon_magazine_size', 'T8_active_weapon_ammo', 'T8_active_weapon_magazine_ammo_left_%', 'T8_active_weapon_max_ammo', 'T8_total_ammo_left', 'T8_active_weapon_total_ammo_left_%', 'T8_flash_duration', 'T8_flash_max_alpha', 'T8_balance', 'T8_current_equip_value', 'T8_round_start_equip_value', 'T8_cash_spent_this_round',
            'T8_is_alive', 'T8_is_CT', 'T8_is_shooting', 'T8_is_crouching', 'T8_is_ducking', 'T8_is_duck_jumping', 'T8_is_walking', 'T8_is_spotted', 'T8_is_scoped', 'T8_is_defusing', 'T8_is_reloading', 'T8_is_in_bombsite',
            'T8_zoom_lvl', 'T8_velo_modifier',
            'T8_stat_kills', 'T8_stat_HS_kills', 'T8_stat_opening_kills', 'T8_stat_MVPs', 'T8_stat_deaths', 'T8_stat_opening_deaths', 'T8_stat_assists', 'T8_stat_flash_assists', 'T8_stat_damage', 'T8_stat_weapon_damage', 'T8_stat_nade_damage', 'T8_stat_survives', 'T8_stat_KPR', 'T8_stat_ADR', 'T8_stat_DPR', 'T8_stat_HS%', 'T8_stat_SPR', 
            'T8_inventory_C4', 'T8_inventory_Taser', 'T8_inventory_USP-S', 'T8_inventory_P2000', 'T8_inventory_Glock-18', 'T8_inventory_Dual Berettas', 'T8_inventory_P250', 'T8_inventory_Tec-9', 'T8_inventory_CZ75 Auto', 'T8_inventory_Five-SeveN', 'T8_inventory_Desert Eagle', 'T8_inventory_R8 Revolver', 'T8_inventory_MAC-10', 'T8_inventory_MP9', 'T8_inventory_MP7', 'T8_inventory_MP5-SD', 'T8_inventory_UMP-45', 'T8_inventory_PP-Bizon', 'T8_inventory_P90', 'T8_inventory_Nova', 'T8_inventory_XM1014', 'T8_inventory_Sawed-Off', 'T8_inventory_MAG-7', 'T8_inventory_M249', 'T8_inventory_Negev', 'T8_inventory_FAMAS', 'T8_inventory_Galil AR', 'T8_inventory_AK-47', 'T8_inventory_M4A4', 'T8_inventory_M4A1-S', 'T8_inventory_SG 553', 'T8_inventory_AUG', 'T8_inventory_SSG 08', 'T8_inventory_AWP', 'T8_inventory_G3SG1', 'T8_inventory_SCAR-20', 'T8_inventory_HE Grenade', 'T8_inventory_Flashbang', 'T8_inventory_Smoke Grenade', 'T8_inventory_Incendiary Grenade', 'T8_inventory_Molotov', 'T8_inventory_Decoy Grenade',
            'T8_active_weapon_C4', 'T8_active_weapon_Knife', 'T8_active_weapon_Taser', 'T8_active_weapon_USP-S', 'T8_active_weapon_P2000', 'T8_active_weapon_Glock-18', 'T8_active_weapon_Dual Berettas', 'T8_active_weapon_P250', 'T8_active_weapon_Tec-9', 'T8_active_weapon_CZ75 Auto', 'T8_active_weapon_Five-SeveN', 'T8_active_weapon_Desert Eagle', 'T8_active_weapon_R8 Revolver', 'T8_active_weapon_MAC-10', 'T8_active_weapon_MP9', 'T8_active_weapon_MP7', 'T8_active_weapon_MP5-SD', 'T8_active_weapon_UMP-45', 'T8_active_weapon_PP-Bizon', 'T8_active_weapon_P90', 'T8_active_weapon_Nova', 'T8_active_weapon_XM1014', 'T8_active_weapon_Sawed-Off', 'T8_active_weapon_MAG-7', 'T8_active_weapon_M249', 'T8_active_weapon_Negev', 'T8_active_weapon_FAMAS', 'T8_active_weapon_Galil AR', 'T8_active_weapon_AK-47', 'T8_active_weapon_M4A4', 'T8_active_weapon_M4A1-S', 'T8_active_weapon_SG 553', 'T8_active_weapon_AUG', 'T8_active_weapon_SSG 08', 'T8_active_weapon_AWP', 'T8_active_weapon_G3SG1', 'T8_active_weapon_SCAR-20', 'T8_active_weapon_HE Grenade', 'T8_active_weapon_Flashbang', 'T8_active_weapon_Smoke Grenade', 'T8_active_weapon_Incendiary Grenade', 'T8_active_weapon_Molotov', 'T8_active_weapon_Decoy Grenade',
            'T8_hltv_rating_2.0', 'T8_hltv_DPR', 'T8_hltv_KAST', 'T8_hltv_Impact', 'T8_hltv_ADR', 'T8_hltv_KPR', 'T8_hltv_total_kills', 'T8_hltv_HS%', 'T8_hltv_total_deaths', 'T8_hltv_KD_ratio', 'T8_hltv_dmgPR', 'T8_hltv_grenade_dmgPR', 'T8_hltv_maps_played', 'T8_hltv_saved_by_teammatePR', 'T8_hltv_saved_teammatesPR', 'T8_hltv_opening_kill_rating', 'T8_hltv_team_W%_after_opening', 'T8_hltv_opening_kill_in_W_rounds', 'T8_hltv_rating_1.0_all_Career', 'T8_hltv_clutches_1on1_ratio', 'T8_hltv_clutches_won_1on1', 'T8_hltv_clutches_won_1on2', 'T8_hltv_clutches_won_1on3', 'T8_hltv_clutches_won_1on4', 'T8_hltv_clutches_won_1on5', 

            'T9_name', 'T9_team_clan_name', 'T9_X', 'T9_Y', 'T9_Z', 'T9_pitch', 'T9_yaw', 'T9_velocity_X', 'T9_velocity_Y', 'T9_velocity_Z', 'T9_health', 'T9_armor_value', 'T9_active_weapon_magazine_size', 'T9_active_weapon_ammo', 'T9_active_weapon_magazine_ammo_left_%', 'T9_active_weapon_max_ammo', 'T9_total_ammo_left', 'T9_active_weapon_total_ammo_left_%', 'T9_flash_duration', 'T9_flash_max_alpha', 'T9_balance', 'T9_current_equip_value', 'T9_round_start_equip_value', 'T9_cash_spent_this_round',
            'T9_is_alive', 'T9_is_CT', 'T9_is_shooting', 'T9_is_crouching', 'T9_is_ducking', 'T9_is_duck_jumping', 'T9_is_walking', 'T9_is_spotted', 'T9_is_scoped', 'T9_is_defusing', 'T9_is_reloading', 'T9_is_in_bombsite',
            'T9_zoom_lvl', 'T9_velo_modifier',
            'T9_stat_kills', 'T9_stat_HS_kills', 'T9_stat_opening_kills', 'T9_stat_MVPs', 'T9_stat_deaths', 'T9_stat_opening_deaths', 'T9_stat_assists', 'T9_stat_flash_assists', 'T9_stat_damage', 'T9_stat_weapon_damage', 'T9_stat_nade_damage', 'T9_stat_survives', 'T9_stat_KPR', 'T9_stat_ADR', 'T9_stat_DPR', 'T9_stat_HS%', 'T9_stat_SPR', 
            'T9_inventory_C4', 'T9_inventory_Taser', 'T9_inventory_USP-S', 'T9_inventory_P2000', 'T9_inventory_Glock-18', 'T9_inventory_Dual Berettas', 'T9_inventory_P250', 'T9_inventory_Tec-9', 'T9_inventory_CZ75 Auto', 'T9_inventory_Five-SeveN', 'T9_inventory_Desert Eagle', 'T9_inventory_R8 Revolver', 'T9_inventory_MAC-10', 'T9_inventory_MP9', 'T9_inventory_MP7', 'T9_inventory_MP5-SD', 'T9_inventory_UMP-45', 'T9_inventory_PP-Bizon', 'T9_inventory_P90', 'T9_inventory_Nova', 'T9_inventory_XM1014', 'T9_inventory_Sawed-Off', 'T9_inventory_MAG-7', 'T9_inventory_M249', 'T9_inventory_Negev', 'T9_inventory_FAMAS', 'T9_inventory_Galil AR', 'T9_inventory_AK-47', 'T9_inventory_M4A4', 'T9_inventory_M4A1-S', 'T9_inventory_SG 553', 'T9_inventory_AUG', 'T9_inventory_SSG 08', 'T9_inventory_AWP', 'T9_inventory_G3SG1', 'T9_inventory_SCAR-20', 'T9_inventory_HE Grenade', 'T9_inventory_Flashbang', 'T9_inventory_Smoke Grenade', 'T9_inventory_Incendiary Grenade', 'T9_inventory_Molotov', 'T9_inventory_Decoy Grenade',
            'T9_active_weapon_C4', 'T9_active_weapon_Knife', 'T9_active_weapon_Taser', 'T9_active_weapon_USP-S', 'T9_active_weapon_P2000', 'T9_active_weapon_Glock-18', 'T9_active_weapon_Dual Berettas', 'T9_active_weapon_P250', 'T9_active_weapon_Tec-9', 'T9_active_weapon_CZ75 Auto', 'T9_active_weapon_Five-SeveN', 'T9_active_weapon_Desert Eagle', 'T9_active_weapon_R8 Revolver', 'T9_active_weapon_MAC-10', 'T9_active_weapon_MP9', 'T9_active_weapon_MP7', 'T9_active_weapon_MP5-SD', 'T9_active_weapon_UMP-45', 'T9_active_weapon_PP-Bizon', 'T9_active_weapon_P90', 'T9_active_weapon_Nova', 'T9_active_weapon_XM1014', 'T9_active_weapon_Sawed-Off', 'T9_active_weapon_MAG-7', 'T9_active_weapon_M249', 'T9_active_weapon_Negev', 'T9_active_weapon_FAMAS', 'T9_active_weapon_Galil AR', 'T9_active_weapon_AK-47', 'T9_active_weapon_M4A4', 'T9_active_weapon_M4A1-S', 'T9_active_weapon_SG 553', 'T9_active_weapon_AUG', 'T9_active_weapon_SSG 08', 'T9_active_weapon_AWP', 'T9_active_weapon_G3SG1', 'T9_active_weapon_SCAR-20', 'T9_active_weapon_HE Grenade', 'T9_active_weapon_Flashbang', 'T9_active_weapon_Smoke Grenade', 'T9_active_weapon_Incendiary Grenade', 'T9_active_weapon_Molotov', 'T9_active_weapon_Decoy Grenade',
            'T9_hltv_rating_2.0', 'T9_hltv_DPR', 'T9_hltv_KAST', 'T9_hltv_Impact', 'T9_hltv_ADR', 'T9_hltv_KPR', 'T9_hltv_total_kills', 'T9_hltv_HS%', 'T9_hltv_total_deaths', 'T9_hltv_KD_ratio', 'T9_hltv_dmgPR', 'T9_hltv_grenade_dmgPR', 'T9_hltv_maps_played', 'T9_hltv_saved_by_teammatePR', 'T9_hltv_saved_teammatesPR', 'T9_hltv_opening_kill_rating', 'T9_hltv_team_W%_after_opening', 'T9_hltv_opening_kill_in_W_rounds', 'T9_hltv_rating_1.0_all_Career', 'T9_hltv_clutches_1on1_ratio', 'T9_hltv_clutches_won_1on1', 'T9_hltv_clutches_won_1on2', 'T9_hltv_clutches_won_1on3', 'T9_hltv_clutches_won_1on4', 'T9_hltv_clutches_won_1on5', 

            
            'numerical_match_id', 'match_id', 'tick', 'round', 'time', 'remaining_time', 'freeze_end', 'end', 'CT_wins', 
            'CT_score', 'T_score', 'CT_alive_num', 'T_alive_num', 'CT_total_hp', 'T_total_hp', 'CT_equipment_value', 'T_equipment_value',  'CT_losing_streak', 'T_losing_streak',
            'is_bomb_dropped', 'is_bomb_being_planted', 'is_bomb_being_defused', 'is_bomb_defused', 'is_bomb_planted_at_A_site', 'is_bomb_planted_at_B_site',
            'bomb_X', 'bomb_Y', 'bomb_Z', 'bomb_mx_pos1', 'bomb_mx_pos2', 'bomb_mx_pos3', 'bomb_mx_pos4', 'bomb_mx_pos5', 'bomb_mx_pos6', 'bomb_mx_pos7', 'bomb_mx_pos8', 'bomb_mx_pos9',
        ]

        # Rearrange the column order
        team_1_ct = team_1_ct[col_order]
        team_2_ct = team_2_ct[col_order]

        # Concatenate the two dataframes
        renamed_df = pd.concat([team_1_ct, team_2_ct])

        # Universal clan names
        team_clan_names = pd.DataFrame({
            'CT_clan_name': renamed_df['CT0_team_clan_name'],
            'T_clan_name': renamed_df['T5_team_clan_name']
        })
        renamed_df = pd.concat([renamed_df, team_clan_names], axis=1)

        # Drop the original columns
        for player_idx in range(10):
            if player_idx < 5:
                renamed_df = renamed_df.drop(columns=[f'CT{player_idx}_team_clan_name'])
            else:
                renamed_df = renamed_df.drop(columns=[f'T{player_idx}_team_clan_name'])

        # Order the dataset by tick
        renamed_df = renamed_df.sort_values(by='tick')

        return renamed_df



    # 15. Rename overall columns
    def _TABULAR_prefix_universal_columns(self, df):

        # Get universal columns
        universal_columns = [col for col in df.columns if not col.startswith('CT0') and not col.startswith('T5')
                                                      and not col.startswith('CT1') and not col.startswith('T6')
                                                      and not col.startswith('CT2') and not col.startswith('T7')
                                                      and not col.startswith('CT3') and not col.startswith('T8')
                                                      and not col.startswith('CT4') and not col.startswith('T9')
                                                      and col != 'numerical_match_id' and col != 'match_id']

        # Rename the columns
        df = df.rename(columns={col: 'UNIVERSAL_' + col for col in universal_columns})

        # Rename the match_id and numerical_match_id columns
        df = df.rename(columns={'match_id': 'MATCH_ID', 'numerical_match_id': 'NUMERICAL_MATCH_ID'})

        return df



    # 16. Build column dictionary
    def _FINAL_build_dictionary(self, df):

        # Get the numerical columns
        numeric_cols = [col for col in df.columns if '_name' not in col and col not in ['MATCH_ID', 'NUMERICAL_MATCH_ID' 'UNIVERSAL_smokes_active', 'UNIVERSAL_infernos_active']]

        # Create dictionary dataset
        df_dict = pd.DataFrame(data={
            'column': numeric_cols, 
            'min': df[numeric_cols].min().values, 
            'max': df[numeric_cols].max().values
        })

        return df_dict



    # 17. Drop rows where the bomb is already defused
    def _EXT_filter_bomb_defused_rows(self, df):

        df = df.loc[df['UNIVERSAL_is_bomb_defused'] == 0]
        return df



    # 18. Free memory
    def _FINAL_free_memory(self, ticks, kills, rounds, bomb, damages, smokes, infernos):
        del ticks
        del kills
        del rounds
        del bomb
        del damages
        del smokes
        del infernos
        gc.collect()





    # --------------------------------------------------------------------------------------------
    # REGION: Process_match private methods - POLARS
    # --------------------------------------------------------------------------------------------
    # TODO: Implement the fixes done in the pandas version: output variable error and team_name column error check


    # 0. Ticks per second operations
    def __POLARS_PREP_ticks_per_second_operations__(self):
        
        # Check if the ticks_per_second is valid
        if self.ticks_per_second not in [1, 2, 4, 8, 16, 32, 64]:
            raise ValueError("Invalid ticks_per_second value. Please choose one of the following: 1, 2, 4, 8, 16, 32 or 64.")
        
        # Set the nth_tick value (the type must be integer)
        self.__nth_tick__ = int(64 / self.ticks_per_second)



    # 1. Get needed dataframes
    def __POLARS_EXT_fill_smoke_NaNs__(self, smokes, rounds):
        
        # Temporary rounds dataframe with the ending tick of each round
        rounds_temp = rounds[['round', 'official_end']].copy()

        # Merge the smokes dataframe with the rounds dataframe and fill the NaN values with the official_end values
        smokes = smokes.merge(rounds_temp, on='round')
        smokes.loc[smokes['end_tick'].isna(), 'end_tick'] = smokes.loc[smokes['end_tick'].isna(), 'official_end']

        # Drop the official_end column
        smokes = smokes.drop(columns=['official_end'])

        return smokes
    
    def __POLARS_EXT_fill_infernos_NaNs__(self, infernos, rounds):
        
        # Temporary rounds dataframe with the ending tick of each round
        rounds_temp = rounds[['round', 'official_end']].copy()

        # Merge the infernos dataframe with the rounds dataframe and fill the NaN values with the official_end values
        infernos = infernos.merge(rounds_temp, on='round')
        infernos.loc[infernos['end_tick'].isna(), 'end_tick'] = infernos.loc[infernos['end_tick'].isna(), 'official_end']

        # Drop the official_end column
        infernos = infernos.drop(columns=['official_end'])

        return infernos

    def _POLARS_INIT_dataframes(self):

        player_cols = [
            'X',
            'Y',
            'Z',
            'health',
            'score',
            'mvps',
            'is_alive',
            'balance',
            'inventory',
            'life_state',
            'pitch',
            'yaw',
            'armor',
            'has_defuser',
            'has_helmet',
            'player_name',
            'team_clan_name',
            'start_balance',
            'total_cash_spent',
            'cash_spent_this_round',
            'jump_velo',
            'fall_velo',
            'in_crouch',
            'ducked',
            'ducking',
            'in_duck_jump',
            'spotted',
            'approximate_spotted_by',
            'time_last_injury',
            'player_state',
            'is_scoped',
            'is_walking',
            'zoom_lvl',
            'is_defusing',
            'in_bomb_zone',
            'stamina',
            'direction',
            'armor_value',
            'velo_modifier',
            'flash_duration',
            'flash_max_alpha',
            'round_start_equip_value',
            'current_equip_value',
            'velocity',
            'velocity_X',
            'velocity_Y',
            'velocity_Z',
            'FIRE',
        ]
        other_cols = [
            'num_player_alive_ct',
            'num_player_alive_t',
            'ct_losing_streak',
            't_losing_streak',
            'active_weapon_name',
            'active_weapon_ammo',
            'total_ammo_left',
            'is_in_reload',
            'alive_time_total',
            'is_bomb_dropped'
        ]

        match = Demo(path=self.MATCH_PATH, player_props=player_cols, other_props=other_cols)

        # Read dataframes
        ticks = match.ticks
        kills = match.kills
        rounds = match.rounds
        bomb = match.bomb
        damages = match.damages
        smokes = match.smokes
        infernos = match.infernos
        he_grenades = match.grenades \
                        .loc[match.grenades['grenade_type'] == 'he_grenade'] \
                        .drop_duplicates(subset=['X', 'Y', 'Z']) \
                        .drop_duplicates(subset=['entity_id'], keep='last')
        
        # Fill the NaN values of the smokes and infernos dataframes
        smokes = self.__POLARS_EXT_fill_smoke_NaNs__(smokes, rounds)
        infernos = self.__POLARS_EXT_fill_infernos_NaNs__(infernos, rounds)

        # Create columns to follow the game scores
        rounds['CT_score'] = 0
        rounds['T_score'] = 0

        # Calculate the team scores in the rounds dataframe
        for idx, row in rounds.iterrows():
            if row['winner'] == 'CT':
                if row['round'] <= 12:
                    rounds.loc[idx+1:, 'CT_score'] += 1
                elif row['round'] > 12:
                    rounds.loc[idx+1:, 'T_score'] += 1

            elif row['winner'] == 'T':
                if row['round'] <= 12:
                    rounds.loc[idx+1:, 'T_score'] += 1
                elif row['round'] > 12:
                    rounds.loc[idx+1:, 'CT_score'] += 1

        # Filter columns
        rounds = rounds[['round', 'freeze_end', 'end', 'CT_score', 'T_score', 'winner']]
        ticks = ticks[[
            'tick', 'round', 'team_name', 'team_clan_name', 'name',
            'X', 'Y', 'Z', 'pitch', 'yaw', 'velocity_X', 'velocity_Y', 'velocity_Z', 'inventory',
            'health', 'armor_value', 'active_weapon_name', 'active_weapon_ammo', 'total_ammo_left',
            'is_alive', 'in_crouch', 'ducking', 'in_duck_jump', 'is_walking', 'spotted', 'is_scoped', 'is_defusing', 'is_in_reload', 'in_bomb_zone',
            'zoom_lvl', 'flash_duration', 'flash_max_alpha', 'mvps',
            'velo_modifier', 'balance', 'current_equip_value', 'round_start_equip_value', 'total_cash_spent', 'cash_spent_this_round',
            'ct_losing_streak', 't_losing_streak', 'is_bomb_dropped', 'FIRE'
        ]]
        
        ticks = ticks.rename(columns={
            'in_crouch'     : 'is_crouching',
            'ducking'       : 'is_ducking',
            'in_duck_jump'  : 'is_duck_jumping',
            'is_walking'    : 'is_walking',
            'spotted'       : 'is_spotted',
            'is_in_reload'  : 'is_reloading',
            'in_bomb_zone'  : 'is_in_bombsite',
            'FIRE'          : 'is_shooting'
        })

        # Create polars dataframes
        ticks = pl.from_pandas(ticks)
        kills = pl.from_pandas(kills)
        rounds = pl.from_pandas(rounds)
        bomb = pl.from_pandas(bomb)
        damages = pl.from_pandas(damages)
        smokes = pl.from_pandas(smokes)
        infernos = pl.from_pandas(infernos)
        he_grenades = pl.from_pandas(he_grenades)
        
        return ticks, kills, rounds, bomb, damages, smokes, infernos, he_grenades



    def __POLARS_EXT_damage_per_round_df__(self, damages: pl.DataFrame, damage_type: str = 'all') -> pl.DataFrame:
        """
        Calculates the damages per round for the players.
        
        Parameters:
            - damages: the damages dataframe.
            - damage_type (optional): the type of damage to be calculated. Value can be 'all', 'weapon' and 'nade'. Default is 'all'.
        """
        
        # Check if the damage_type is valid
        if damage_type not in ['all', 'weapon', 'nade']:
            raise ValueError("Invalid damage_type value. Please choose one of the following: 'all', 'weapon' or 'nade'.")

        # Filter the damages dataframe for friendly fire
        damages = damages.filter(pl.col('attacker_team_name') != pl.col('victim_team_name'))

        # Filter the damages dataframe for the damage type
        if damage_type == 'all':
            damages = damages
        if damage_type == 'weapon':
            damages = damages.filter(~pl.col('weapon').is_in(['inferno', 'molotov', 'hegrenade', 'flashbang', 'smokegrenade']))
        elif damage_type == 'nade':
            damages = damages.filter(pl.col('weapon').is_in(['inferno', 'molotov', 'hegrenade', 'flashbang', 'smokegrenade']))

        # Create damages per round dataframe
        dpr = damages.to_pandas().sort_values(by=['round']).groupby(['round', 'attacker_name'])['dmg_health_real'].sum().reset_index()

        # Use cumsum to calculate the damages for the whole match per player
        dpr['dmg_health_real'] = dpr.groupby('attacker_name')['dmg_health_real'].cumsum()

        # Rename columns
        if damage_type == 'all':
            dpr = dpr.rename(columns={'attacker_name': 'name', 'dmg_health_real': 'stat_damage'})
        elif damage_type == 'weapon':
            dpr = dpr.rename(columns={'attacker_name': 'name', 'dmg_health_real': 'stat_weapon_damage'})
        elif damage_type == 'nade':
            dpr = dpr.rename(columns={'attacker_name': 'name', 'dmg_health_real': 'stat_nade_damage'})

        # Increase the round number by 1, as the damages are calculated when the round is over
        dpr['round'] += 1
        dpr = pl.from_pandas(dpr)

        return dpr

    def _POLARS_PLAYER_ingame_stats(self, ticks: pl.DataFrame, kills: pl.DataFrame, rounds: pl.DataFrame, damages: pl.DataFrame):

        # Merge ticks with rounds
        pf = ticks.join(rounds, on='round')

        # Rename the mvps column
        pf = pf.rename({'mvps': 'stat_MVPs'})

        # Format CT information
        pf = pf.with_columns(
            pl.when(pl.col('team_name') == 'CT').then(1).otherwise(0).alias('is_CT')
        ).drop('team_name')

        # First kills dataframe
        first_kills = kills.unique(subset=['round'], keep='first')

        # Initialize stats
        pf = pf.with_columns([
            # Kill stats
            pl.lit(0).alias('stat_kills'),
            pl.lit(0).alias('stat_HS_kills'),
            pl.lit(0).alias('stat_opening_kills'),
            # Death stats
            pl.lit(0).alias('stat_deaths'),
            pl.lit(0).alias('stat_opening_deaths'),
            # Assist stats
            pl.lit(0).alias('stat_assists'),
            pl.lit(0).alias('stat_flash_assists'),
        ])

        # Set kill stats
        for row in kills.iter_rows(named=True):
            tick_filter = (pl.col('tick') >= row['tick'])

            # Kills
            pf = pf.with_columns(
                pl.when(tick_filter & (pl.col('name') == row['attacker_name']))
                .then(pl.col('stat_kills') + 1).otherwise(pl.col('stat_kills')).alias('stat_kills')
            )

            # HS kills
            if row['headshot']:
                pf = pf.with_columns(
                    pl.when(tick_filter & (pl.col('name') == row['attacker_name']))
                    .then(pl.col('stat_HS_kills') + 1).otherwise(pl.col('stat_HS_kills')).alias('stat_HS_kills')
                )

            # Deaths
            pf = pf.with_columns(
                pl.when(tick_filter & (pl.col('name') == row['victim_name']))
                .then(pl.col('stat_deaths') + 1).otherwise(pl.col('stat_deaths')).alias('stat_deaths')
            )

            # Assists
            if row['assister_name'] is not None:
                pf = pf.with_columns(
                    pl.when(tick_filter & (pl.col('name') == row['assister_name']))
                    .then(pl.col('stat_assists') + 1).otherwise(pl.col('stat_assists')).alias('stat_assists')
                )

            # Flash assists
            if row['assistedflash']:
                pf = pf.with_columns(
                    pl.when(tick_filter & (pl.col('name') == row['assister_name']))
                    .then(pl.col('stat_flash_assists') + 1).otherwise(pl.col('stat_flash_assists')).alias('stat_flash_assists')
                )

        # Set opening-kill and opening-death stats
        for row in first_kills.iter_rows(named=True):
            first_kill_tick = kills.filter(pl.col('round') == row['round']).sort('tick').head(1)['tick'][0]

            # Opening kills
            if row['tick'] == first_kill_tick:
                pf = pf.with_columns(
                    pl.when((pl.col('tick') >= row['tick']) & (pl.col('name') == row['attacker_name']))
                    .then(pl.col('stat_opening_kills') + 1).otherwise(pl.col('stat_opening_kills')).alias('stat_opening_kills')
                )

            # Opening deaths
            if row['tick'] == first_kill_tick:
                pf = pf.with_columns(
                    pl.when((pl.col('tick') >= row['tick']) & (pl.col('name') == row['victim_name']))
                    .then(pl.col('stat_opening_deaths') + 1).otherwise(pl.col('stat_opening_deaths')).alias('stat_opening_deaths')
                )

        # Create damages per round dataframe for the players for all types of damages
        dpr = self.__POLARS_EXT_damage_per_round_df__(damages, 'all')
        wdpr = self.__POLARS_EXT_damage_per_round_df__(damages, 'weapon')
        ndpr = self.__POLARS_EXT_damage_per_round_df__(damages, 'nade')

        # Merge the damages per round dataframe with the player dataframe
        pf = pf.join(dpr, on=['round', 'name'], how='left')
        pf = pf.join(wdpr, on=['round', 'name'], how='left')
        pf = pf.join(ndpr, on=['round', 'name'], how='left')

        # Fill NaN values with 0
        pf = pf.with_columns([
            pl.col('stat_damage').fill_nan(0).fill_null(0),
            pl.col('stat_weapon_damage').fill_nan(0).fill_null(0),
            pl.col('stat_nade_damage').fill_nan(0).fill_null(0),
        ])


        # Initialize other stats
        pf = pf.with_columns([
            pl.lit(0).alias('stat_survives'),
            pl.lit(0).alias('stat_KPR'),
            pl.lit(0).alias('stat_ADR'),
            pl.lit(0).alias('stat_DPR'),
            pl.lit(0).alias('stat_HS%'),
            pl.lit(0).alias('stat_SPR'),
        ])

        # Calculate stat_survives
        pf = pf.with_columns(
            (pl.col('round') - pl.col('stat_deaths')).alias('stat_survives')
        )
        
        # Calculate other stats
        pf = pf.with_columns([
            (pl.col('stat_kills') / pl.col('round')).alias('stat_KPR'),
            (pl.col('stat_damage') / pl.col('round')).alias('stat_ADR'),
            (pl.col('stat_deaths') / pl.col('round')).alias('stat_DPR'),
            (pl.col('stat_HS_kills') / pl.col('stat_kills')).fill_nan(0).alias('stat_HS%'),
            (pl.col('stat_survives') / pl.col('round')).alias('stat_SPR'),
        ])

        return pf
    
    
    
    # 3. Inventory
    def _POLARS_PLAYER_inventory(self, pf: pl.DataFrame) -> pl.DataFrame:

        # Inventory weapons
        inventory_weapons = [
            # Other
            'inventory_C4', 'inventory_Taser',
            # Pistols
            'inventory_USP-S', 'inventory_P2000', 'inventory_Glock-18', 'inventory_Dual Berettas', 'inventory_P250', 'inventory_Tec-9', 'inventory_CZ75 Auto', 'inventory_Five-SeveN', 'inventory_Desert Eagle', 'inventory_R8 Revolver',
            # SMGs
            'inventory_MAC-10', 'inventory_MP9', 'inventory_MP7', 'inventory_MP5-SD', 'inventory_UMP-45', 'inventory_PP-Bizon', 'inventory_P90',
            # Heavy
            'inventory_Nova', 'inventory_XM1014', 'inventory_Sawed-Off', 'inventory_MAG-7', 'inventory_M249', 'inventory_Negev',
            # Rifles
            'inventory_FAMAS', 'inventory_Galil AR', 'inventory_AK-47', 'inventory_M4A4', 'inventory_M4A1-S', 'inventory_SG 553', 'inventory_AUG', 'inventory_SSG 08', 'inventory_AWP', 'inventory_G3SG1', 'inventory_SCAR-20',
            # Grenades
            'inventory_HE Grenade', 'inventory_Flashbang', 'inventory_Smoke Grenade', 'inventory_Incendiary Grenade', 'inventory_Molotov', 'inventory_Decoy Grenade'
        ]

        # Create dummy columns using polars' str.contains()
        for weapon in inventory_weapons:
            weapon_name = weapon.replace('inventory_', '')
            pf = pf.with_columns(
                pl.when(pl.col('inventory').list.contains(weapon_name))
                .then(1)
                .otherwise(0)
                .alias(weapon)
            )

        return pf



    # 4. Handle active weapon column
    def _POLARS_PLAYER_active_weapons(self, pf: pl.DataFrame) -> pl.DataFrame:

        # Handle null values
        pf = pf.with_columns(
            pl.col('active_weapon_name').fill_null('').alias('active_weapon_name')
        )

        
        # Handle "Knife" active weapon case
        pf = pf.with_columns(
            pl.when(pl.col("active_weapon_name").str.to_lowercase().str.contains("knife"))
            .then(pl.lit("Knife"))
            .otherwise(pl.col("active_weapon_name"))
            .alias("active_weapon_name")
        )

           
        # Active weapons
        active_weapons = [
            # Other
            'active_weapon_C4', 'active_weapon_Knife', 'active_weapon_Taser',
            # Pistols
            'active_weapon_USP-S', 'active_weapon_P2000', 'active_weapon_Glock-18', 'active_weapon_Dual Berettas', 'active_weapon_P250', 'active_weapon_Tec-9', 'active_weapon_CZ75 Auto', 'active_weapon_Five-SeveN', 'active_weapon_Desert Eagle', 'active_weapon_R8 Revolver',
            # SMGs
            'active_weapon_MAC-10', 'active_weapon_MP9', 'active_weapon_MP7', 'active_weapon_MP5-SD', 'active_weapon_UMP-45', 'active_weapon_PP-Bizon', 'active_weapon_P90',
            # Heavy
            'active_weapon_Nova', 'active_weapon_XM1014', 'active_weapon_Sawed-Off', 'active_weapon_MAG-7', 'active_weapon_M249', 'active_weapon_Negev',
            # Rifles
            'active_weapon_FAMAS', 'active_weapon_Galil AR', 'active_weapon_AK-47', 'active_weapon_M4A4', 'active_weapon_M4A1-S', 'active_weapon_SG 553', 'active_weapon_AUG', 'active_weapon_SSG 08', 'active_weapon_AWP', 'active_weapon_G3SG1', 'active_weapon_SCAR-20',
            # Grenades
            'active_weapon_HE Grenade', 'active_weapon_Flashbang', 'active_weapon_Smoke Grenade', 'active_weapon_Incendiary Grenade', 'active_weapon_Molotov', 'active_weapon_Decoy Grenade'
        ]

        # Create dummy columns using polars' pivot operation
        pf = pf.with_columns(
            [pl.when(pl.col('active_weapon_name') == weapon.replace('active_weapon_', ''))
             .then(1).otherwise(0).alias(weapon) for weapon in active_weapons]
        )
        
        return pf
    


    # 5. Handle weapon ammo info
    def _POLARS_PLAYER_weapon_ammo_info(self, pf):

        # Read weapon data
        weapon_data = pl.read_csv(self.WEAPON_DATA_PATH)

        # Create player ammo info columns
        pf = pf.with_columns([
            pl.lit(0).alias('active_weapon_magazine_size'),
            pl.lit(0).alias('active_weapon_max_ammo'),
            pl.lit(0).alias('active_weapon_magazine_ammo_left_%'),
            pl.lit(0).alias('active_weapon_total_ammo_left_%')
        ])

        # Active weapons
        active_weapons = [
            # Other
            'active_weapon_C4', 'active_weapon_Knife', 'active_weapon_Taser',
            # Pistols
            'active_weapon_USP-S', 'active_weapon_P2000', 'active_weapon_Glock-18', 'active_weapon_Dual Berettas', 'active_weapon_P250', 'active_weapon_Tec-9', 'active_weapon_CZ75 Auto', 'active_weapon_Five-SeveN', 'active_weapon_Desert Eagle', 'active_weapon_R8 Revolver',
            # SMGs
            'active_weapon_MAC-10', 'active_weapon_MP9', 'active_weapon_MP7', 'active_weapon_MP5-SD', 'active_weapon_UMP-45', 'active_weapon_PP-Bizon', 'active_weapon_P90',
            # Heavy
            'active_weapon_Nova', 'active_weapon_XM1014', 'active_weapon_Sawed-Off', 'active_weapon_MAG-7', 'active_weapon_M249', 'active_weapon_Negev',
            # Rifles
            'active_weapon_FAMAS', 'active_weapon_Galil AR', 'active_weapon_AK-47', 'active_weapon_M4A4', 'active_weapon_M4A1-S', 'active_weapon_SG 553', 'active_weapon_AUG', 'active_weapon_SSG 08', 'active_weapon_AWP', 'active_weapon_G3SG1', 'active_weapon_SCAR-20',
            # Grenades
            'active_weapon_HE Grenade', 'active_weapon_Flashbang', 'active_weapon_Smoke Grenade', 'active_weapon_Incendiary Grenade', 'active_weapon_Molotov', 'active_weapon_Decoy Grenade'
        ]

        # Set ammo info
        for col in active_weapons:
            weapon_name = col.replace('active_weapon_', '')
            weapon_info = weapon_data.filter(pl.col('weapon_name') == weapon_name)
            
            if not weapon_info.is_empty():
                mag_size = weapon_info['magazine_size'].to_numpy()[0]
                total_ammo = weapon_info['total_ammo'].to_numpy()[0]
                
                pf = pf.with_columns([
                    pl.when(pl.col(col) == 1).then(mag_size).otherwise(pl.col('active_weapon_magazine_size')).alias('active_weapon_magazine_size'),
                    pl.when(pl.col(col) == 1).then(total_ammo).otherwise(pl.col('active_weapon_max_ammo')).alias('active_weapon_max_ammo')
                ])

        # Create magazine ammo left % column
        pf = pf.with_columns([
            (pl.col('active_weapon_ammo') / pl.col('active_weapon_magazine_size')).fill_nan(0).alias('active_weapon_magazine_ammo_left_%')
        ])

        # Create total ammo left % column
        pf = pf.with_columns([
            (pl.col('total_ammo_left') / pl.col('active_weapon_max_ammo')).fill_nan(0).alias('active_weapon_total_ammo_left_%')
        ])

        return pf



    # 6. Create player dataset
    def _POLARS_PLAYER_player_datasets(self, pf):
    
        startAsCTPlayerNames = pf.filter((pl.col('is_CT') == True) & (pl.col('round') == 1)).select('name').unique().to_series().to_list()
        startAsTPlayerNames  = pf.filter((pl.col('is_CT') == False) & (pl.col('round') == 1)).select('name').unique().to_series().to_list()

        startAsCTPlayerNames.sort()
        startAsTPlayerNames.sort()

        players = {}

        # Team 1: start on CT side
        players[0] = pf.filter(pl.col('name') == startAsCTPlayerNames[0]).gather_every(self.__nth_tick__).clone()
        players[1] = pf.filter(pl.col('name') == startAsCTPlayerNames[1]).gather_every(self.__nth_tick__).clone()
        players[2] = pf.filter(pl.col('name') == startAsCTPlayerNames[2]).gather_every(self.__nth_tick__).clone()
        players[3] = pf.filter(pl.col('name') == startAsCTPlayerNames[3]).gather_every(self.__nth_tick__).clone()
        players[4] = pf.filter(pl.col('name') == startAsCTPlayerNames[4]).gather_every(self.__nth_tick__).clone()

        # Team 2: start on T side
        players[5] = pf.filter(pl.col('name') == startAsTPlayerNames[0]).gather_every(self.__nth_tick__).clone()
        players[6] = pf.filter(pl.col('name') == startAsTPlayerNames[1]).gather_every(self.__nth_tick__).clone()
        players[7] = pf.filter(pl.col('name') == startAsTPlayerNames[2]).gather_every(self.__nth_tick__).clone()
        players[8] = pf.filter(pl.col('name') == startAsTPlayerNames[3]).gather_every(self.__nth_tick__).clone()
        players[9] = pf.filter(pl.col('name') == startAsTPlayerNames[4]).gather_every(self.__nth_tick__).clone()
        
        return players
    


    # 7. Insert universal player statistics into player dataset
    def __POLARS_EXT_insert_columns_into_player_dataframes__(self, stat_df: pl.DataFrame, players_df: pl.DataFrame) -> pl.DataFrame:
        for col in stat_df.columns:
            if col != 'player_name':
                value = stat_df.filter(pl.col('player_name') == players_df['name'][0])[col].item()
                players_df = players_df.with_columns(pl.lit(value).alias(col))
        return players_df

    def _POLARS_PLAYER_hltv_statistics(self, players):

        # Needed columns
        needed_stats = ['player_name', 'rating_2.0', 'DPR', 'KAST', 'Impact', 'ADR', 'KPR','total_kills', 'HS%', 'total_deaths', 'KD_ratio', 'dmgPR',
        'grenade_dmgPR', 'maps_played', 'saved_by_teammatePR', 'saved_teammatesPR','opening_kill_rating', 'team_W%_after_opening',
        'opening_kill_in_W_rounds', 'rating_1.0_all_Career', 'clutches_1on1_ratio', 'clutches_won_1on1', 'clutches_won_1on2', 'clutches_won_1on3', 'clutches_won_1on4', 'clutches_won_1on5']
        
        stats = pl.from_pandas(pd.read_csv(self.PLAYER_STATS_DATA_PATH).drop_duplicates())

        # Try to select needed stats, and if clutches_1on1_ratio is missing, calculate it
        try:
            stats = stats.select(needed_stats)
        except Exception:
            stats = stats.with_columns(
                (pl.col('clutches_won_1on1') / pl.col('clutches_lost_1on1')).fill_null(0).alias('clutches_1on1_ratio')
            )
            stats = stats.select(needed_stats)

        # Stats dataframe basic formatting
        for col in stats.columns:
            if col != 'player_name':
                stats = stats.with_columns(pl.col(col).cast(pl.Float32).alias(col))
                stats = stats.rename({col: "hltv_" + col})

        # Merge stats with players
        for idx in range(len(players)):
            player_name = players[idx]['name'][0]

            # If stats contain player information, merge
            if stats.filter(pl.col('player_name') == player_name).height == 1:
                players[idx] = self.__POLARS_EXT_insert_columns_into_player_dataframes__(stats, players[idx])

            # If stats do not contain player information, check missing_players_df
            else:
                mpdf = pl.read_csv(self.MISSING_PLAYER_STATS_DATA_PATH)

                try:
                    mpdf = mpdf.select(needed_stats)
                except Exception:
                    mpdf = mpdf.with_columns(
                        (pl.col('clutches_won_1on1') / pl.col('clutches_lost_1on1')).fill_null(0).alias('clutches_1on1_ratio')
                    )
                    mpdf = mpdf.select(needed_stats)

                for col in mpdf.columns:
                    if col != 'player_name':
                        mpdf = mpdf.with_columns(pl.col(col).cast(pl.Float32).alias(col))
                        mpdf = mpdf.rename({col: "hltv_" + col})

                # If missing_players_df contains player information, merge
                if mpdf.filter(pl.col('player_name') == player_name).height == 1:
                    players[idx] = self.__POLARS_EXT_insert_columns_into_player_dataframes__(mpdf, players[idx])

                # Else impute values from missing_players_df and merge
                else:
                    first_anonim_pro_index = mpdf.with_row_index().filter(pl.col("player_name") == "anonim_pro").select("index").to_series()[0]

                    mpdf = mpdf.with_columns(
                        pl.when(pl.arange(0, pl.count()).alias("index") == first_anonim_pro_index)
                        .then(pl.lit(player_name))
                        .otherwise(pl.col("player_name"))
                        .alias("player_name")
                    )
                    
                    players[idx] = self.__POLARS_EXT_insert_columns_into_player_dataframes__(mpdf, players[idx])

                    # Reverse the column renaming - remove the 'hltv_' prefix
                    for col in mpdf.columns:
                        if col.startswith('hltv_'):
                            mpdf = mpdf.rename({col: col[len('hltv_'):]})

                    mpdf.write_csv(self.MISSING_PLAYER_STATS_DATA_PATH)

        return players
    


    # 8. Create tabular dataset - first version (1 row - 1 graph)
    def __POLARS_EXT_delete_useless_columns__(self, graph_data: pl.DataFrame) -> pl.DataFrame:

        columns_to_drop = [
            'player0_equi_val_alive', 'player1_equi_val_alive', 'player2_equi_val_alive', 'player3_equi_val_alive', 'player4_equi_val_alive',
            'player5_equi_val_alive', 'player6_equi_val_alive', 'player7_equi_val_alive', 'player8_equi_val_alive', 'player9_equi_val_alive',
            
            'player0_freeze_end', 'player1_freeze_end', 'player2_freeze_end', 'player3_freeze_end', 'player4_freeze_end',
            'player5_freeze_end', 'player6_freeze_end', 'player7_freeze_end', 'player8_freeze_end', 'player9_freeze_end',
            
            'player0_end', 'player1_end', 'player2_end', 'player3_end', 'player4_end',
            'player5_end', 'player6_end', 'player7_end', 'player8_end', 'player9_end',
            
            'player0_winner', 'player1_winner', 'player2_winner', 'player3_winner', 'player4_winner',
            'player5_winner', 'player6_winner', 'player7_winner', 'player8_winner', 'player9_winner',

            'player1_ct_losing_streak', 'player2_ct_losing_streak', 'player3_ct_losing_streak', 'player4_ct_losing_streak',
            'player5_ct_losing_streak', 'player6_ct_losing_streak', 'player7_ct_losing_streak', 'player8_ct_losing_streak', 'player9_ct_losing_streak',

            'player1_t_losing_streak', 'player2_t_losing_streak', 'player3_t_losing_streak', 'player4_t_losing_streak',
            'player5_t_losing_streak', 'player6_t_losing_streak', 'player7_t_losing_streak', 'player8_t_losing_streak', 'player9_t_losing_streak',

            'player1_is_bomb_dropped', 'player2_is_bomb_dropped', 'player3_is_bomb_dropped', 'player4_is_bomb_dropped',
            'player5_is_bomb_dropped', 'player6_is_bomb_dropped', 'player7_is_bomb_dropped', 'player8_is_bomb_dropped', 'player9_is_bomb_dropped'
        ]

        # Drop the columns from the dataframe
        graph_data = graph_data.drop(columns_to_drop)
        
        return graph_data

    def _POLARS_TABULAR_initial_dataset(self, players, rounds, match_id):
        """
        Creates the first version of the dataset for the graph model.
        
        Parameters:
            - players: the dataframes of the players.
            - rounds: the dataframes of the rounds.
            - match_id: the id of the match.
        """

        # Copy players object
        graph_players = {}
        for idx in range(len(players)):
            graph_players[idx] = players[idx].clone()

        colsNotToRename = ['tick', 'round']

        # Rename columns except for tick, roundNum, seconds, floorSec
        for idx in range(len(graph_players)):
            for col in graph_players[idx].columns:
                if col not in colsNotToRename:
                    graph_players[idx] = graph_players[idx].rename({col: f"player{idx}_{col}"})

        # Create a graph dataframe to store all players in 1 row per second
        graph_data = graph_players[0].clone()

        # Merge dataframes
        for i in range(1, len(graph_players)):
            graph_data = graph_data.join(graph_players[i], on=colsNotToRename)

        graph_data = graph_data.join(rounds, on=['round'])
        graph_data = graph_data.with_columns([
            (graph_data['winner'] == 'CT').cast(pl.Int8).alias('CT_wins')
        ])

        for i in range(10):
            graph_data = graph_data.with_columns([
                (graph_data[f'player{i}_current_equip_value'] * graph_data[f'player{i}_is_alive']).alias(f'player{i}_equi_val_alive')
            ])

        graph_data = graph_data.with_columns(
            [pl.col(f'player{idx}_is_alive').cast(pl.Int64) for idx in range(10)]
        )

        # CT and T players alive
        graph_data = graph_data.with_columns(
            pl.when(pl.col('player0_is_CT').cast(pl.Boolean))
            .then(
                pl.col('player0_is_alive') + 
                pl.col('player1_is_alive') + 
                pl.col('player2_is_alive') + 
                pl.col('player3_is_alive') + 
                pl.col('player4_is_alive')
            )
            .otherwise(
                pl.col('player5_is_alive') + 
                pl.col('player6_is_alive') + 
                pl.col('player7_is_alive') + 
                pl.col('player8_is_alive') + 
                pl.col('player9_is_alive')
            )
            .alias('CT_alive_num')
        )

        graph_data = graph_data.with_columns(
            pl.when(pl.col('player0_is_CT').cast(pl.Boolean))
            .then(
                pl.col('player5_is_alive') + 
                pl.col('player6_is_alive') + 
                pl.col('player7_is_alive') + 
                pl.col('player8_is_alive') + 
                pl.col('player9_is_alive')
            )
            .otherwise(
                pl.col('player0_is_alive') + 
                pl.col('player1_is_alive') + 
                pl.col('player2_is_alive') + 
                pl.col('player3_is_alive') + 
                pl.col('player4_is_alive')
            )
            .alias('T_alive_num')
        )


        # CT and T total health
        graph_data = graph_data.with_columns(
            pl.when(pl.col('player0_is_CT').cast(pl.Boolean))
            .then(
                pl.col('player0_health') + 
                pl.col('player1_health') + 
                pl.col('player2_health') + 
                pl.col('player3_health') + 
                pl.col('player4_health')
            )
            .otherwise(
                pl.col('player5_health') + 
                pl.col('player6_health') + 
                pl.col('player7_health') + 
                pl.col('player8_health') + 
                pl.col('player9_health')
            )
            .alias('CT_total_hp')
        )
        
        graph_data = graph_data.with_columns(
            pl.when(pl.col('player0_is_CT').cast(pl.Boolean))
            .then(
                pl.col('player5_health') + 
                pl.col('player6_health') + 
                pl.col('player7_health') + 
                pl.col('player8_health') + 
                pl.col('player9_health')
            )
            .otherwise(
                pl.col('player0_health') + 
                pl.col('player1_health') + 
                pl.col('player2_health') + 
                pl.col('player3_health') + 
                pl.col('player4_health')
            )
            .alias('T_total_hp')
        )


        # CT and T equipment value
        graph_data = graph_data.with_columns(
            pl.when(pl.col('player0_is_CT').cast(pl.Boolean))
            .then(
                pl.col('player0_equi_val_alive') + 
                pl.col('player1_equi_val_alive') + 
                pl.col('player2_equi_val_alive') + 
                pl.col('player3_equi_val_alive') + 
                pl.col('player4_equi_val_alive')
            )
            .otherwise(
                pl.col('player5_equi_val_alive') + 
                pl.col('player6_equi_val_alive') + 
                pl.col('player7_equi_val_alive') + 
                pl.col('player8_equi_val_alive') + 
                pl.col('player9_equi_val_alive')
            )
            .alias('CT_equipment_value')
        )
        
        graph_data = graph_data.with_columns(
            pl.when(pl.col('player0_is_CT').cast(pl.Boolean))
            .then(
                pl.col('player5_equi_val_alive') + 
                pl.col('player6_equi_val_alive') + 
                pl.col('player7_equi_val_alive') + 
                pl.col('player8_equi_val_alive') + 
                pl.col('player9_equi_val_alive')
            )
            .otherwise(
                pl.col('player0_equi_val_alive') + 
                pl.col('player1_equi_val_alive') + 
                pl.col('player2_equi_val_alive') + 
                pl.col('player3_equi_val_alive') + 
                pl.col('player4_equi_val_alive')
            )
            .alias('T_equipment_value')
        )

        

        graph_data = graph_data.rename({
            'player0_ct_losing_streak': 'CT_losing_streak', 
            'player0_t_losing_streak': 'T_losing_streak', 
            'player0_is_bomb_dropped': 'is_bomb_dropped'
        })

        graph_data = self.__POLARS_EXT_delete_useless_columns__(graph_data)

        # Add time remaining column
        graph_data = graph_data.with_columns(
            (115.0 - ((graph_data['tick'] - graph_data['freeze_end']) / 64.0)).alias('time')
        )

        # Create a DataFrame with a single column for match_id
        match_id_df = pl.DataFrame({'match_id': [str(match_id)] * len(graph_data)})
        graph_data_concatenated = pl.concat([graph_data, match_id_df], how='horizontal')

        return graph_data_concatenated



    # 9. Add bomb information to the dataset
    def _POLARS_TABULAR_bomb_info(self, tabular_df: pl.DataFrame, bombdf: pl.DataFrame) -> pl.DataFrame:
        
        # New columns
        tabular_df = tabular_df.with_columns([
            pl.lit(0).alias('is_bomb_being_planted'),
            pl.lit(0).alias('is_bomb_being_defused'),
            pl.lit(0).alias('is_bomb_defused'),
            pl.lit(0).alias('is_bomb_planted_at_A_site'),
            pl.lit(0).alias('is_bomb_planted_at_B_site'),
            pl.lit(0).alias('plant_tick'),
            pl.lit(0.0).alias('bomb_X'),
            pl.lit(0.0).alias('bomb_Y'),
            pl.lit(0.0).alias('bomb_Z'),
        ])

        # Calculate 'is_bomb_being_planted' and 'is_bomb_being_defused'
        for i in range(10):
            active_weapon_C4 = f'player{i}_active_weapon_C4'
            is_in_bombsite = f'player{i}_is_in_bombsite'
            is_shooting = f'player{i}_is_shooting'

            tabular_df = tabular_df.with_columns([
                # Check if the bomb is being planted
                pl.when(
                    (pl.col(active_weapon_C4) == 1) & (pl.col(is_in_bombsite) == 1) & (pl.col(is_shooting) == 1)
                ).then(1).otherwise(pl.col('is_bomb_being_planted')).alias('is_bomb_being_planted'),
            ])


        # Sum up all 'is_defusing' columns
        tabular_df = tabular_df.with_columns(
            pl.sum_horizontal([pl.col(f'player{i}_is_defusing') for i in range(10)])
            .alias("is_bomb_being_defused")
        )
            

        # Process bomb-related events
        for row in bombdf.iter_rows(named=True):
            if row['event'] == 'planted':
                site_column = 'is_bomb_planted_at_A_site' if row['site'] == 'BombsiteA' else 'is_bomb_planted_at_B_site'
                tabular_df = tabular_df.with_columns([
                    pl.when(
                        (pl.col('round') == row['round']) & (pl.col('tick') >= row['tick'])
                    ).then(1).otherwise(pl.col(site_column)).alias(site_column),
                    pl.when(
                        (pl.col('round') == row['round']) & (pl.col('tick') >= row['tick'])
                    ).then(row['X']).otherwise(pl.col('bomb_X')).alias('bomb_X'),
                    pl.when(
                        (pl.col('round') == row['round']) & (pl.col('tick') >= row['tick'])
                    ).then(row['Y']).otherwise(pl.col('bomb_Y')).alias('bomb_Y'),
                    pl.when(
                        (pl.col('round') == row['round']) & (pl.col('tick') >= row['tick'])
                    ).then(row['Z']).otherwise(pl.col('bomb_Z')).alias('bomb_Z'),
                    pl.when(
                        pl.col('round') == row['round']
                    ).then(row['tick']).otherwise(pl.col('plant_tick')).alias('plant_tick')
                ])

            elif row['event'] == 'defused':
                tabular_df = tabular_df.with_columns([
                    pl.when(
                        (pl.col('round') == row['round']) & (pl.col('tick') >= row['tick'])
                    ).then(0).otherwise(pl.col('is_bomb_being_defused')).alias('is_bomb_being_defused'),
                    pl.when(
                        (pl.col('round') == row['round']) & (pl.col('tick') >= row['tick'])
                    ).then(1).otherwise(pl.col('is_bomb_defused')).alias('is_bomb_defused')
                ])

        # Calculate remaining time after the bomb is planted
        tabular_df = tabular_df.with_columns([
            pl.when(
                (pl.col('is_bomb_planted_at_A_site') == 1) | (pl.col('is_bomb_planted_at_B_site') == 1)
            ).then(
                40.0 - ((pl.col('tick') - pl.col('plant_tick')) / 64.0)
            ).otherwise(
                pl.col('time')
            ).alias('remaining_time')
        ])

        return tabular_df



    # 10. Split the bombsites by 3x3 matrix for bomb position feature
    def __POLARS_EXT_get_bomb_mx_coordinate_expr(self, is_bomb_planted_at_A_site, is_bomb_planted_at_B_site, bomb_X, bomb_Y):
        expr = pl.when(is_bomb_planted_at_A_site == 1).then(
            pl.when(bomb_Y >= 650).then(
                pl.when(bomb_X < 1900).then(1)
                .when(bomb_X >= 1900).then(pl.when(bomb_X < 2050).then(2).otherwise(3))
                .otherwise(3)
            ).when(bomb_Y >= 325).then(
                pl.when(bomb_X < 1900).then(4)
                .when(bomb_X >= 1900).then(pl.when(bomb_X < 2050).then(5).otherwise(6))
                .otherwise(6)
            ).when(bomb_Y < 325).then(
                pl.when(bomb_X < 1900).then(7)
                .when(bomb_X >= 1900).then(pl.when(bomb_X < 2050).then(8).otherwise(9))
                .otherwise(9)
            )
        ).when(is_bomb_planted_at_B_site == 1).then(
            pl.when(bomb_Y >= 2900).then(
                pl.when(bomb_X < 275).then(1)
                .when(bomb_X >= 275).then(pl.when(bomb_X < 400).then(2).otherwise(3))
                .otherwise(3)
            ).when(bomb_Y >= 2725).then(
                pl.when(bomb_X < 275).then(4)
                .when(bomb_X >= 275).then(pl.when(bomb_X < 400).then(5).otherwise(6))
                .otherwise(6)
            ).when(bomb_Y < 2725).then(
                pl.when(bomb_X < 275).then(7)
                .when(bomb_X >= 275).then(pl.when(bomb_X < 400).then(8).otherwise(9))
                .otherwise(9)
            )
        ).otherwise(0)

        return expr

    def _POLARS_TABULAR_INFERNO_bombsite_3x3_split(self, tabular_df):

        tabular_df = tabular_df.with_columns(
            self.__POLARS_EXT_get_bomb_mx_coordinate_expr(
                tabular_df['is_bomb_planted_at_A_site'],
                tabular_df['is_bomb_planted_at_B_site'],
                tabular_df['bomb_X'],
                tabular_df['bomb_Y']
            ).alias('bomb_mx_pos')
        )

        # Create the binary columns
        for i in range(1, 10):
            tabular_df = tabular_df.with_columns(
                (pl.col('bomb_mx_pos') == i).cast(pl.Int32).alias(f'bomb_mx_pos{i}')
            )
        
        # Drop the intermediate column
        tabular_df = tabular_df.drop('bomb_mx_pos')

        return tabular_df
    


    # 11. Handle smoke and molotov grenades
    def _POLARS_TABULAR_smokes_HEs_infernos(self, df: pl.DataFrame, smokes: pl.DataFrame, he_grenades: pl.DataFrame, infernos: pl.DataFrame):
    
        # Active infernos, smokes and HE explosions DataFrames
        active_infernos = None
        active_smokes = None
        active_he_smokes = None

        # Handle smokes
        for row in smokes.iter_rows(named=True):
            
            startTick = row['start_tick']
            endTick = row['end_tick'] - 112
            round_value = row['round']
            X = row['X']
            Y = row['Y']
            Z = row['Z']

            temp_smoke = df.select(['tick', 'round']).clone()
            temp_smoke = temp_smoke.with_columns([
                pl.lit(None).alias('X'),
                pl.lit(None).alias('Y'),
                pl.lit(None).alias('Z')
            ])

            temp_smoke = temp_smoke.with_columns([
                pl.when((pl.col('round') == round_value) & 
                        (pl.col('tick') >= startTick) & 
                        (pl.col('tick') <= endTick)).then(pl.lit(X)).otherwise(pl.col('X')).alias('X'),
                pl.when((pl.col('round') == round_value) & 
                        (pl.col('tick') >= startTick) & 
                        (pl.col('tick') <= endTick)).then(pl.lit(Y)).otherwise(pl.col('Y')).alias('Y'),
                pl.when((pl.col('round') == round_value) & 
                        (pl.col('tick') >= startTick) & 
                        (pl.col('tick') <= endTick)).then(pl.lit(Z)).otherwise(pl.col('Z')).alias('Z')
            ])

            temp_smoke = temp_smoke.drop_nulls()

            if active_smokes is None:
                active_smokes = temp_smoke
            else:
                active_smokes = pl.concat([active_smokes, temp_smoke])

        # Handle HE grenades
        for row in he_grenades.iter_rows(named=True):
            
            startTick = row['tick']
            endTick = startTick + 128
            round_value = row['round']
            X = row['X']
            Y = row['Y']
            Z = row['Z']

            temp_HE = df.select(['tick', 'round']).clone()
            temp_HE = temp_HE.with_columns([
                pl.lit(None).alias('X'),
                pl.lit(None).alias('Y'),
                pl.lit(None).alias('Z')
            ])

            temp_HE = temp_HE.with_columns([
                pl.when((pl.col('round') == round_value) & 
                        (pl.col('tick') >= startTick) & 
                        (pl.col('tick') <= endTick)).then(pl.lit(X)).otherwise(pl.col('X')).alias('X'),
                pl.when((pl.col('round') == round_value) & 
                        (pl.col('tick') >= startTick) & 
                        (pl.col('tick') <= endTick)).then(pl.lit(Y)).otherwise(pl.col('Y')).alias('Y'),
                pl.when((pl.col('round') == round_value) & 
                        (pl.col('tick') >= startTick) & 
                        (pl.col('tick') <= endTick)).then(pl.lit(Z)).otherwise(pl.col('Z')).alias('Z')
            ])

            temp_HE = temp_HE.drop_nulls()

            if active_he_smokes is None:
                active_he_smokes = temp_HE
            else:
                active_he_smokes = pl.concat([active_he_smokes, temp_HE])

        # Handle infernos
        for row in infernos.iter_rows(named=True):
            
            startTick = row['start_tick']
            endTick = row['end_tick']
            round_value = row['round']
            X = row['X']
            Y = row['Y']
            Z = row['Z']

            temp_inf = df.select(['tick', 'round']).clone()
            temp_inf = temp_inf.with_columns([
                pl.lit(None).alias('X'),
                pl.lit(None).alias('Y'),
                pl.lit(None).alias('Z')
            ])

            temp_inf = temp_inf.with_columns([
                pl.when((pl.col('round') == round_value) & 
                        (pl.col('tick') >= startTick) & 
                        (pl.col('tick') <= endTick)).then(pl.lit(X)).otherwise(pl.col('X')).alias('X'),
                pl.when((pl.col('round') == round_value) & 
                        (pl.col('tick') >= startTick) & 
                        (pl.col('tick') <= endTick)).then(pl.lit(Y)).otherwise(pl.col('Y')).alias('Y'),
                pl.when((pl.col('round') == round_value) & 
                        (pl.col('tick') >= startTick) & 
                        (pl.col('tick') <= endTick)).then(pl.lit(Z)).otherwise(pl.col('Z')).alias('Z')
            ])

            temp_inf = temp_inf.drop_nulls()

            if active_infernos is None:
                active_infernos = temp_inf
            else:
                active_infernos = pl.concat([active_infernos, temp_inf])

        return active_infernos, active_smokes, active_he_smokes



    # 12. Add numerical match id
    def _POLARS_TABULAR_numerical_match_id(self, tabular_df: pl.DataFrame) -> pl.DataFrame:
    
        if not isinstance(self.numerical_match_id, int):
            raise ValueError("Numerical match id must be an integer.")
        
        # Create a new column with the numerical_match_id value
        tabular_df = tabular_df.with_columns([
            pl.lit(self.numerical_match_id).alias('numerical_match_id'),
        ])


        return tabular_df



    # 13. Rearrange the player columns so that the CTs are always from 0 to 4 and Ts are from 5 to 9
    def _POLARS_TABULAR_refactor_player_columns(self, df: pl.DataFrame) -> pl.DataFrame:

        # Separate the CT and T halves
        team_1_ct = df.filter(pl.col('player0_is_CT') == True).clone()
        team_2_ct = df.filter(pl.col('player0_is_CT') == False).clone()

        # Rename columns for team_1_ct
        team_1_ct = team_1_ct.rename({
            col: col.replace('player', 'CT') for col in team_1_ct.columns
            if col.startswith('player') and int(col[6]) < 5
        })

        team_1_ct = team_1_ct.rename({
            col: col.replace('player', 'T') for col in team_1_ct.columns
            if col.startswith('player') and int(col[6]) >= 5
        })

        # Rename columns for team_2_ct
        team_2_ct = team_2_ct.rename({
            col: col.replace(f'player{col[6]}', f'T{int(col[6]) + 5}') for col in team_2_ct.columns
            if col.startswith('player') and int(col[6]) <= 4
        })

        team_2_ct = team_2_ct.rename({
            col: col.replace(f'player{col[6]}', f'CT{int(col[6]) - 5}') for col in team_2_ct.columns
            if col.startswith('player') and int(col[6]) > 4
        })

        # Column order
        col_order = [
            'CT0_name', 'CT0_team_clan_name', 'CT0_X', 'CT0_Y', 'CT0_Z', 'CT0_pitch', 'CT0_yaw', 'CT0_velocity_X', 'CT0_velocity_Y', 'CT0_velocity_Z', 'CT0_health', 'CT0_armor_value', 'CT0_active_weapon_magazine_size', 'CT0_active_weapon_ammo', 'CT0_active_weapon_magazine_ammo_left_%', 'CT0_active_weapon_max_ammo', 'CT0_total_ammo_left', 'CT0_active_weapon_total_ammo_left_%', 'CT0_flash_duration', 'CT0_flash_max_alpha', 'CT0_balance', 'CT0_current_equip_value', 'CT0_round_start_equip_value', 'CT0_cash_spent_this_round',
            'CT0_is_alive', 'CT0_is_CT', 'CT0_is_shooting', 'CT0_is_crouching', 'CT0_is_ducking', 'CT0_is_duck_jumping', 'CT0_is_walking', 'CT0_is_spotted', 'CT0_is_scoped', 'CT0_is_defusing', 'CT0_is_reloading', 'CT0_is_in_bombsite',
            'CT0_zoom_lvl', 'CT0_velo_modifier',
            'CT0_stat_kills', 'CT0_stat_HS_kills', 'CT0_stat_opening_kills', 'CT0_stat_MVPs', 'CT0_stat_deaths', 'CT0_stat_opening_deaths', 'CT0_stat_assists', 'CT0_stat_flash_assists', 'CT0_stat_damage', 'CT0_stat_weapon_damage', 'CT0_stat_nade_damage', 'CT0_stat_survives', 'CT0_stat_KPR', 'CT0_stat_ADR', 'CT0_stat_DPR', 'CT0_stat_HS%', 'CT0_stat_SPR', 
            'CT0_inventory_C4', 'CT0_inventory_Taser', 'CT0_inventory_USP-S', 'CT0_inventory_P2000', 'CT0_inventory_Glock-18', 'CT0_inventory_Dual Berettas', 'CT0_inventory_P250', 'CT0_inventory_Tec-9', 'CT0_inventory_CZ75 Auto', 'CT0_inventory_Five-SeveN', 'CT0_inventory_Desert Eagle', 'CT0_inventory_R8 Revolver', 'CT0_inventory_MAC-10', 'CT0_inventory_MP9', 'CT0_inventory_MP7', 'CT0_inventory_MP5-SD', 'CT0_inventory_UMP-45', 'CT0_inventory_PP-Bizon', 'CT0_inventory_P90', 'CT0_inventory_Nova', 'CT0_inventory_XM1014', 'CT0_inventory_Sawed-Off', 'CT0_inventory_MAG-7', 'CT0_inventory_M249', 'CT0_inventory_Negev', 'CT0_inventory_FAMAS', 'CT0_inventory_Galil AR', 'CT0_inventory_AK-47', 'CT0_inventory_M4A4', 'CT0_inventory_M4A1-S', 'CT0_inventory_SG 553', 'CT0_inventory_AUG', 'CT0_inventory_SSG 08', 'CT0_inventory_AWP', 'CT0_inventory_G3SG1', 'CT0_inventory_SCAR-20', 'CT0_inventory_HE Grenade', 'CT0_inventory_Flashbang', 'CT0_inventory_Smoke Grenade', 'CT0_inventory_Incendiary Grenade', 'CT0_inventory_Molotov', 'CT0_inventory_Decoy Grenade',
            'CT0_active_weapon_C4', 'CT0_active_weapon_Knife', 'CT0_active_weapon_Taser', 'CT0_active_weapon_USP-S', 'CT0_active_weapon_P2000', 'CT0_active_weapon_Glock-18', 'CT0_active_weapon_Dual Berettas', 'CT0_active_weapon_P250', 'CT0_active_weapon_Tec-9', 'CT0_active_weapon_CZ75 Auto', 'CT0_active_weapon_Five-SeveN', 'CT0_active_weapon_Desert Eagle', 'CT0_active_weapon_R8 Revolver', 'CT0_active_weapon_MAC-10', 'CT0_active_weapon_MP9', 'CT0_active_weapon_MP7', 'CT0_active_weapon_MP5-SD', 'CT0_active_weapon_UMP-45', 'CT0_active_weapon_PP-Bizon', 'CT0_active_weapon_P90', 'CT0_active_weapon_Nova', 'CT0_active_weapon_XM1014', 'CT0_active_weapon_Sawed-Off', 'CT0_active_weapon_MAG-7', 'CT0_active_weapon_M249', 'CT0_active_weapon_Negev', 'CT0_active_weapon_FAMAS', 'CT0_active_weapon_Galil AR', 'CT0_active_weapon_AK-47', 'CT0_active_weapon_M4A4', 'CT0_active_weapon_M4A1-S', 'CT0_active_weapon_SG 553', 'CT0_active_weapon_AUG', 'CT0_active_weapon_SSG 08', 'CT0_active_weapon_AWP', 'CT0_active_weapon_G3SG1', 'CT0_active_weapon_SCAR-20', 'CT0_active_weapon_HE Grenade', 'CT0_active_weapon_Flashbang', 'CT0_active_weapon_Smoke Grenade', 'CT0_active_weapon_Incendiary Grenade', 'CT0_active_weapon_Molotov', 'CT0_active_weapon_Decoy Grenade',
            'CT0_hltv_rating_2.0', 'CT0_hltv_DPR', 'CT0_hltv_KAST', 'CT0_hltv_Impact', 'CT0_hltv_ADR', 'CT0_hltv_KPR', 'CT0_hltv_total_kills', 'CT0_hltv_HS%', 'CT0_hltv_total_deaths', 'CT0_hltv_KD_ratio', 'CT0_hltv_dmgPR', 'CT0_hltv_grenade_dmgPR', 'CT0_hltv_maps_played', 'CT0_hltv_saved_by_teammatePR', 'CT0_hltv_saved_teammatesPR', 'CT0_hltv_opening_kill_rating', 'CT0_hltv_team_W%_after_opening', 'CT0_hltv_opening_kill_in_W_rounds', 'CT0_hltv_rating_1.0_all_Career', 'CT0_hltv_clutches_1on1_ratio', 'CT0_hltv_clutches_won_1on1', 'CT0_hltv_clutches_won_1on2', 'CT0_hltv_clutches_won_1on3', 'CT0_hltv_clutches_won_1on4', 'CT0_hltv_clutches_won_1on5', 
                
            'CT1_name', 'CT1_team_clan_name', 'CT1_X', 'CT1_Y', 'CT1_Z', 'CT1_pitch', 'CT1_yaw', 'CT1_velocity_X', 'CT1_velocity_Y', 'CT1_velocity_Z', 'CT1_health', 'CT1_armor_value', 'CT1_active_weapon_magazine_size', 'CT1_active_weapon_ammo', 'CT1_active_weapon_magazine_ammo_left_%', 'CT1_active_weapon_max_ammo', 'CT1_total_ammo_left', 'CT1_active_weapon_total_ammo_left_%', 'CT1_flash_duration', 'CT1_flash_max_alpha', 'CT1_balance', 'CT1_current_equip_value', 'CT1_round_start_equip_value', 'CT1_cash_spent_this_round',
            'CT1_is_alive', 'CT1_is_CT', 'CT1_is_shooting', 'CT1_is_crouching', 'CT1_is_ducking', 'CT1_is_duck_jumping', 'CT1_is_walking', 'CT1_is_spotted', 'CT1_is_scoped', 'CT1_is_defusing', 'CT1_is_reloading', 'CT1_is_in_bombsite',
            'CT1_zoom_lvl', 'CT1_velo_modifier',
            'CT1_stat_kills', 'CT1_stat_HS_kills', 'CT1_stat_opening_kills', 'CT1_stat_MVPs', 'CT1_stat_deaths', 'CT1_stat_opening_deaths', 'CT1_stat_assists', 'CT1_stat_flash_assists', 'CT1_stat_damage', 'CT1_stat_weapon_damage', 'CT1_stat_nade_damage', 'CT1_stat_survives', 'CT1_stat_KPR', 'CT1_stat_ADR', 'CT1_stat_DPR', 'CT1_stat_HS%', 'CT1_stat_SPR', 
            'CT1_inventory_C4', 'CT1_inventory_Taser', 'CT1_inventory_USP-S', 'CT1_inventory_P2000', 'CT1_inventory_Glock-18', 'CT1_inventory_Dual Berettas', 'CT1_inventory_P250', 'CT1_inventory_Tec-9', 'CT1_inventory_CZ75 Auto', 'CT1_inventory_Five-SeveN', 'CT1_inventory_Desert Eagle', 'CT1_inventory_R8 Revolver', 'CT1_inventory_MAC-10', 'CT1_inventory_MP9', 'CT1_inventory_MP7', 'CT1_inventory_MP5-SD', 'CT1_inventory_UMP-45', 'CT1_inventory_PP-Bizon', 'CT1_inventory_P90', 'CT1_inventory_Nova', 'CT1_inventory_XM1014', 'CT1_inventory_Sawed-Off', 'CT1_inventory_MAG-7', 'CT1_inventory_M249', 'CT1_inventory_Negev', 'CT1_inventory_FAMAS', 'CT1_inventory_Galil AR', 'CT1_inventory_AK-47', 'CT1_inventory_M4A4', 'CT1_inventory_M4A1-S', 'CT1_inventory_SG 553', 'CT1_inventory_AUG', 'CT1_inventory_SSG 08', 'CT1_inventory_AWP', 'CT1_inventory_G3SG1', 'CT1_inventory_SCAR-20', 'CT1_inventory_HE Grenade', 'CT1_inventory_Flashbang', 'CT1_inventory_Smoke Grenade', 'CT1_inventory_Incendiary Grenade', 'CT1_inventory_Molotov', 'CT1_inventory_Decoy Grenade',
            'CT1_active_weapon_C4', 'CT1_active_weapon_Knife', 'CT1_active_weapon_Taser', 'CT1_active_weapon_USP-S', 'CT1_active_weapon_P2000', 'CT1_active_weapon_Glock-18', 'CT1_active_weapon_Dual Berettas', 'CT1_active_weapon_P250', 'CT1_active_weapon_Tec-9', 'CT1_active_weapon_CZ75 Auto', 'CT1_active_weapon_Five-SeveN', 'CT1_active_weapon_Desert Eagle', 'CT1_active_weapon_R8 Revolver', 'CT1_active_weapon_MAC-10', 'CT1_active_weapon_MP9', 'CT1_active_weapon_MP7', 'CT1_active_weapon_MP5-SD', 'CT1_active_weapon_UMP-45', 'CT1_active_weapon_PP-Bizon', 'CT1_active_weapon_P90', 'CT1_active_weapon_Nova', 'CT1_active_weapon_XM1014', 'CT1_active_weapon_Sawed-Off', 'CT1_active_weapon_MAG-7', 'CT1_active_weapon_M249', 'CT1_active_weapon_Negev', 'CT1_active_weapon_FAMAS', 'CT1_active_weapon_Galil AR', 'CT1_active_weapon_AK-47', 'CT1_active_weapon_M4A4', 'CT1_active_weapon_M4A1-S', 'CT1_active_weapon_SG 553', 'CT1_active_weapon_AUG', 'CT1_active_weapon_SSG 08', 'CT1_active_weapon_AWP', 'CT1_active_weapon_G3SG1', 'CT1_active_weapon_SCAR-20', 'CT1_active_weapon_HE Grenade', 'CT1_active_weapon_Flashbang', 'CT1_active_weapon_Smoke Grenade', 'CT1_active_weapon_Incendiary Grenade', 'CT1_active_weapon_Molotov', 'CT1_active_weapon_Decoy Grenade',
            'CT1_hltv_rating_2.0', 'CT1_hltv_DPR', 'CT1_hltv_KAST', 'CT1_hltv_Impact', 'CT1_hltv_ADR', 'CT1_hltv_KPR', 'CT1_hltv_total_kills', 'CT1_hltv_HS%', 'CT1_hltv_total_deaths', 'CT1_hltv_KD_ratio', 'CT1_hltv_dmgPR', 'CT1_hltv_grenade_dmgPR', 'CT1_hltv_maps_played', 'CT1_hltv_saved_by_teammatePR', 'CT1_hltv_saved_teammatesPR', 'CT1_hltv_opening_kill_rating', 'CT1_hltv_team_W%_after_opening', 'CT1_hltv_opening_kill_in_W_rounds', 'CT1_hltv_rating_1.0_all_Career', 'CT1_hltv_clutches_1on1_ratio', 'CT1_hltv_clutches_won_1on1', 'CT1_hltv_clutches_won_1on2', 'CT1_hltv_clutches_won_1on3', 'CT1_hltv_clutches_won_1on4', 'CT1_hltv_clutches_won_1on5', 

            'CT2_name', 'CT2_team_clan_name', 'CT2_X', 'CT2_Y', 'CT2_Z', 'CT2_pitch', 'CT2_yaw', 'CT2_velocity_X', 'CT2_velocity_Y', 'CT2_velocity_Z', 'CT2_health', 'CT2_armor_value', 'CT2_active_weapon_magazine_size', 'CT2_active_weapon_ammo', 'CT2_active_weapon_magazine_ammo_left_%', 'CT2_active_weapon_max_ammo', 'CT2_total_ammo_left', 'CT2_active_weapon_total_ammo_left_%', 'CT2_flash_duration', 'CT2_flash_max_alpha', 'CT2_balance', 'CT2_current_equip_value', 'CT2_round_start_equip_value', 'CT2_cash_spent_this_round',
            'CT2_is_alive', 'CT2_is_CT', 'CT2_is_shooting', 'CT2_is_crouching', 'CT2_is_ducking', 'CT2_is_duck_jumping', 'CT2_is_walking', 'CT2_is_spotted', 'CT2_is_scoped', 'CT2_is_defusing', 'CT2_is_reloading', 'CT2_is_in_bombsite',
            'CT2_zoom_lvl', 'CT2_velo_modifier',
            'CT2_stat_kills', 'CT2_stat_HS_kills', 'CT2_stat_opening_kills', 'CT2_stat_MVPs', 'CT2_stat_deaths', 'CT2_stat_opening_deaths', 'CT2_stat_assists', 'CT2_stat_flash_assists', 'CT2_stat_damage', 'CT2_stat_weapon_damage', 'CT2_stat_nade_damage', 'CT2_stat_survives', 'CT2_stat_KPR', 'CT2_stat_ADR', 'CT2_stat_DPR', 'CT2_stat_HS%', 'CT2_stat_SPR', 
            'CT2_inventory_C4', 'CT2_inventory_Taser', 'CT2_inventory_USP-S', 'CT2_inventory_P2000', 'CT2_inventory_Glock-18', 'CT2_inventory_Dual Berettas', 'CT2_inventory_P250', 'CT2_inventory_Tec-9', 'CT2_inventory_CZ75 Auto', 'CT2_inventory_Five-SeveN', 'CT2_inventory_Desert Eagle', 'CT2_inventory_R8 Revolver', 'CT2_inventory_MAC-10', 'CT2_inventory_MP9', 'CT2_inventory_MP7', 'CT2_inventory_MP5-SD', 'CT2_inventory_UMP-45', 'CT2_inventory_PP-Bizon', 'CT2_inventory_P90', 'CT2_inventory_Nova', 'CT2_inventory_XM1014', 'CT2_inventory_Sawed-Off', 'CT2_inventory_MAG-7', 'CT2_inventory_M249', 'CT2_inventory_Negev', 'CT2_inventory_FAMAS', 'CT2_inventory_Galil AR', 'CT2_inventory_AK-47', 'CT2_inventory_M4A4', 'CT2_inventory_M4A1-S', 'CT2_inventory_SG 553', 'CT2_inventory_AUG', 'CT2_inventory_SSG 08', 'CT2_inventory_AWP', 'CT2_inventory_G3SG1', 'CT2_inventory_SCAR-20', 'CT2_inventory_HE Grenade', 'CT2_inventory_Flashbang', 'CT2_inventory_Smoke Grenade', 'CT2_inventory_Incendiary Grenade', 'CT2_inventory_Molotov', 'CT2_inventory_Decoy Grenade',
            'CT2_active_weapon_C4', 'CT2_active_weapon_Knife', 'CT2_active_weapon_Taser', 'CT2_active_weapon_USP-S', 'CT2_active_weapon_P2000', 'CT2_active_weapon_Glock-18', 'CT2_active_weapon_Dual Berettas', 'CT2_active_weapon_P250', 'CT2_active_weapon_Tec-9', 'CT2_active_weapon_CZ75 Auto', 'CT2_active_weapon_Five-SeveN', 'CT2_active_weapon_Desert Eagle', 'CT2_active_weapon_R8 Revolver', 'CT2_active_weapon_MAC-10', 'CT2_active_weapon_MP9', 'CT2_active_weapon_MP7', 'CT2_active_weapon_MP5-SD', 'CT2_active_weapon_UMP-45', 'CT2_active_weapon_PP-Bizon', 'CT2_active_weapon_P90', 'CT2_active_weapon_Nova', 'CT2_active_weapon_XM1014', 'CT2_active_weapon_Sawed-Off', 'CT2_active_weapon_MAG-7', 'CT2_active_weapon_M249', 'CT2_active_weapon_Negev', 'CT2_active_weapon_FAMAS', 'CT2_active_weapon_Galil AR', 'CT2_active_weapon_AK-47', 'CT2_active_weapon_M4A4', 'CT2_active_weapon_M4A1-S', 'CT2_active_weapon_SG 553', 'CT2_active_weapon_AUG', 'CT2_active_weapon_SSG 08', 'CT2_active_weapon_AWP', 'CT2_active_weapon_G3SG1', 'CT2_active_weapon_SCAR-20', 'CT2_active_weapon_HE Grenade', 'CT2_active_weapon_Flashbang', 'CT2_active_weapon_Smoke Grenade', 'CT2_active_weapon_Incendiary Grenade', 'CT2_active_weapon_Molotov', 'CT2_active_weapon_Decoy Grenade',
            'CT2_hltv_rating_2.0', 'CT2_hltv_DPR', 'CT2_hltv_KAST', 'CT2_hltv_Impact', 'CT2_hltv_ADR', 'CT2_hltv_KPR', 'CT2_hltv_total_kills', 'CT2_hltv_HS%', 'CT2_hltv_total_deaths', 'CT2_hltv_KD_ratio', 'CT2_hltv_dmgPR', 'CT2_hltv_grenade_dmgPR', 'CT2_hltv_maps_played', 'CT2_hltv_saved_by_teammatePR', 'CT2_hltv_saved_teammatesPR', 'CT2_hltv_opening_kill_rating', 'CT2_hltv_team_W%_after_opening', 'CT2_hltv_opening_kill_in_W_rounds', 'CT2_hltv_rating_1.0_all_Career', 'CT2_hltv_clutches_1on1_ratio', 'CT2_hltv_clutches_won_1on1', 'CT2_hltv_clutches_won_1on2', 'CT2_hltv_clutches_won_1on3', 'CT2_hltv_clutches_won_1on4', 'CT2_hltv_clutches_won_1on5', 

            'CT3_name', 'CT3_team_clan_name', 'CT3_X', 'CT3_Y', 'CT3_Z', 'CT3_pitch', 'CT3_yaw', 'CT3_velocity_X', 'CT3_velocity_Y', 'CT3_velocity_Z', 'CT3_health', 'CT3_armor_value', 'CT3_active_weapon_magazine_size', 'CT3_active_weapon_ammo', 'CT3_active_weapon_magazine_ammo_left_%', 'CT3_active_weapon_max_ammo', 'CT3_total_ammo_left', 'CT3_active_weapon_total_ammo_left_%', 'CT3_flash_duration', 'CT3_flash_max_alpha', 'CT3_balance', 'CT3_current_equip_value', 'CT3_round_start_equip_value', 'CT3_cash_spent_this_round',
            'CT3_is_alive', 'CT3_is_CT', 'CT3_is_shooting', 'CT3_is_crouching', 'CT3_is_ducking', 'CT3_is_duck_jumping', 'CT3_is_walking', 'CT3_is_spotted', 'CT3_is_scoped', 'CT3_is_defusing', 'CT3_is_reloading', 'CT3_is_in_bombsite',
            'CT3_zoom_lvl', 'CT3_velo_modifier',
            'CT3_stat_kills', 'CT3_stat_HS_kills', 'CT3_stat_opening_kills', 'CT3_stat_MVPs', 'CT3_stat_deaths', 'CT3_stat_opening_deaths', 'CT3_stat_assists', 'CT3_stat_flash_assists', 'CT3_stat_damage', 'CT3_stat_weapon_damage', 'CT3_stat_nade_damage', 'CT3_stat_survives', 'CT3_stat_KPR', 'CT3_stat_ADR', 'CT3_stat_DPR', 'CT3_stat_HS%', 'CT3_stat_SPR', 
            'CT3_inventory_C4', 'CT3_inventory_Taser', 'CT3_inventory_USP-S', 'CT3_inventory_P2000', 'CT3_inventory_Glock-18', 'CT3_inventory_Dual Berettas', 'CT3_inventory_P250', 'CT3_inventory_Tec-9', 'CT3_inventory_CZ75 Auto', 'CT3_inventory_Five-SeveN', 'CT3_inventory_Desert Eagle', 'CT3_inventory_R8 Revolver', 'CT3_inventory_MAC-10', 'CT3_inventory_MP9', 'CT3_inventory_MP7', 'CT3_inventory_MP5-SD', 'CT3_inventory_UMP-45', 'CT3_inventory_PP-Bizon', 'CT3_inventory_P90', 'CT3_inventory_Nova', 'CT3_inventory_XM1014', 'CT3_inventory_Sawed-Off', 'CT3_inventory_MAG-7', 'CT3_inventory_M249', 'CT3_inventory_Negev', 'CT3_inventory_FAMAS', 'CT3_inventory_Galil AR', 'CT3_inventory_AK-47', 'CT3_inventory_M4A4', 'CT3_inventory_M4A1-S', 'CT3_inventory_SG 553', 'CT3_inventory_AUG', 'CT3_inventory_SSG 08', 'CT3_inventory_AWP', 'CT3_inventory_G3SG1', 'CT3_inventory_SCAR-20', 'CT3_inventory_HE Grenade', 'CT3_inventory_Flashbang', 'CT3_inventory_Smoke Grenade', 'CT3_inventory_Incendiary Grenade', 'CT3_inventory_Molotov', 'CT3_inventory_Decoy Grenade',
            'CT3_active_weapon_C4', 'CT3_active_weapon_Knife', 'CT3_active_weapon_Taser', 'CT3_active_weapon_USP-S', 'CT3_active_weapon_P2000', 'CT3_active_weapon_Glock-18', 'CT3_active_weapon_Dual Berettas', 'CT3_active_weapon_P250', 'CT3_active_weapon_Tec-9', 'CT3_active_weapon_CZ75 Auto', 'CT3_active_weapon_Five-SeveN', 'CT3_active_weapon_Desert Eagle', 'CT3_active_weapon_R8 Revolver', 'CT3_active_weapon_MAC-10', 'CT3_active_weapon_MP9', 'CT3_active_weapon_MP7', 'CT3_active_weapon_MP5-SD', 'CT3_active_weapon_UMP-45', 'CT3_active_weapon_PP-Bizon', 'CT3_active_weapon_P90', 'CT3_active_weapon_Nova', 'CT3_active_weapon_XM1014', 'CT3_active_weapon_Sawed-Off', 'CT3_active_weapon_MAG-7', 'CT3_active_weapon_M249', 'CT3_active_weapon_Negev', 'CT3_active_weapon_FAMAS', 'CT3_active_weapon_Galil AR', 'CT3_active_weapon_AK-47', 'CT3_active_weapon_M4A4', 'CT3_active_weapon_M4A1-S', 'CT3_active_weapon_SG 553', 'CT3_active_weapon_AUG', 'CT3_active_weapon_SSG 08', 'CT3_active_weapon_AWP', 'CT3_active_weapon_G3SG1', 'CT3_active_weapon_SCAR-20', 'CT3_active_weapon_HE Grenade', 'CT3_active_weapon_Flashbang', 'CT3_active_weapon_Smoke Grenade', 'CT3_active_weapon_Incendiary Grenade', 'CT3_active_weapon_Molotov', 'CT3_active_weapon_Decoy Grenade',
            'CT3_hltv_rating_2.0', 'CT3_hltv_DPR', 'CT3_hltv_KAST', 'CT3_hltv_Impact', 'CT3_hltv_ADR', 'CT3_hltv_KPR', 'CT3_hltv_total_kills', 'CT3_hltv_HS%', 'CT3_hltv_total_deaths', 'CT3_hltv_KD_ratio', 'CT3_hltv_dmgPR', 'CT3_hltv_grenade_dmgPR', 'CT3_hltv_maps_played', 'CT3_hltv_saved_by_teammatePR', 'CT3_hltv_saved_teammatesPR', 'CT3_hltv_opening_kill_rating', 'CT3_hltv_team_W%_after_opening', 'CT3_hltv_opening_kill_in_W_rounds', 'CT3_hltv_rating_1.0_all_Career', 'CT3_hltv_clutches_1on1_ratio', 'CT3_hltv_clutches_won_1on1', 'CT3_hltv_clutches_won_1on2', 'CT3_hltv_clutches_won_1on3', 'CT3_hltv_clutches_won_1on4', 'CT3_hltv_clutches_won_1on5', 

            'CT4_name', 'CT4_team_clan_name', 'CT4_X', 'CT4_Y', 'CT4_Z', 'CT4_pitch', 'CT4_yaw', 'CT4_velocity_X', 'CT4_velocity_Y', 'CT4_velocity_Z', 'CT4_health', 'CT4_armor_value', 'CT4_active_weapon_magazine_size', 'CT4_active_weapon_ammo', 'CT4_active_weapon_magazine_ammo_left_%', 'CT4_active_weapon_max_ammo', 'CT4_total_ammo_left', 'CT4_active_weapon_total_ammo_left_%', 'CT4_flash_duration', 'CT4_flash_max_alpha', 'CT4_balance', 'CT4_current_equip_value', 'CT4_round_start_equip_value', 'CT4_cash_spent_this_round',
            'CT4_is_alive', 'CT4_is_CT', 'CT4_is_shooting', 'CT4_is_crouching', 'CT4_is_ducking', 'CT4_is_duck_jumping', 'CT4_is_walking', 'CT4_is_spotted', 'CT4_is_scoped', 'CT4_is_defusing', 'CT4_is_reloading', 'CT4_is_in_bombsite',
            'CT4_zoom_lvl', 'CT4_velo_modifier',
            'CT4_stat_kills', 'CT4_stat_HS_kills', 'CT4_stat_opening_kills', 'CT4_stat_MVPs', 'CT4_stat_deaths', 'CT4_stat_opening_deaths', 'CT4_stat_assists', 'CT4_stat_flash_assists', 'CT4_stat_damage', 'CT4_stat_weapon_damage', 'CT4_stat_nade_damage', 'CT4_stat_survives', 'CT4_stat_KPR', 'CT4_stat_ADR', 'CT4_stat_DPR', 'CT4_stat_HS%', 'CT4_stat_SPR', 
            'CT4_inventory_C4', 'CT4_inventory_Taser', 'CT4_inventory_USP-S', 'CT4_inventory_P2000', 'CT4_inventory_Glock-18', 'CT4_inventory_Dual Berettas', 'CT4_inventory_P250', 'CT4_inventory_Tec-9', 'CT4_inventory_CZ75 Auto', 'CT4_inventory_Five-SeveN', 'CT4_inventory_Desert Eagle', 'CT4_inventory_R8 Revolver', 'CT4_inventory_MAC-10', 'CT4_inventory_MP9', 'CT4_inventory_MP7', 'CT4_inventory_MP5-SD', 'CT4_inventory_UMP-45', 'CT4_inventory_PP-Bizon', 'CT4_inventory_P90', 'CT4_inventory_Nova', 'CT4_inventory_XM1014', 'CT4_inventory_Sawed-Off', 'CT4_inventory_MAG-7', 'CT4_inventory_M249', 'CT4_inventory_Negev', 'CT4_inventory_FAMAS', 'CT4_inventory_Galil AR', 'CT4_inventory_AK-47', 'CT4_inventory_M4A4', 'CT4_inventory_M4A1-S', 'CT4_inventory_SG 553', 'CT4_inventory_AUG', 'CT4_inventory_SSG 08', 'CT4_inventory_AWP', 'CT4_inventory_G3SG1', 'CT4_inventory_SCAR-20', 'CT4_inventory_HE Grenade', 'CT4_inventory_Flashbang', 'CT4_inventory_Smoke Grenade', 'CT4_inventory_Incendiary Grenade', 'CT4_inventory_Molotov', 'CT4_inventory_Decoy Grenade',
            'CT4_active_weapon_C4', 'CT4_active_weapon_Knife', 'CT4_active_weapon_Taser', 'CT4_active_weapon_USP-S', 'CT4_active_weapon_P2000', 'CT4_active_weapon_Glock-18', 'CT4_active_weapon_Dual Berettas', 'CT4_active_weapon_P250', 'CT4_active_weapon_Tec-9', 'CT4_active_weapon_CZ75 Auto', 'CT4_active_weapon_Five-SeveN', 'CT4_active_weapon_Desert Eagle', 'CT4_active_weapon_R8 Revolver', 'CT4_active_weapon_MAC-10', 'CT4_active_weapon_MP9', 'CT4_active_weapon_MP7', 'CT4_active_weapon_MP5-SD', 'CT4_active_weapon_UMP-45', 'CT4_active_weapon_PP-Bizon', 'CT4_active_weapon_P90', 'CT4_active_weapon_Nova', 'CT4_active_weapon_XM1014', 'CT4_active_weapon_Sawed-Off', 'CT4_active_weapon_MAG-7', 'CT4_active_weapon_M249', 'CT4_active_weapon_Negev', 'CT4_active_weapon_FAMAS', 'CT4_active_weapon_Galil AR', 'CT4_active_weapon_AK-47', 'CT4_active_weapon_M4A4', 'CT4_active_weapon_M4A1-S', 'CT4_active_weapon_SG 553', 'CT4_active_weapon_AUG', 'CT4_active_weapon_SSG 08', 'CT4_active_weapon_AWP', 'CT4_active_weapon_G3SG1', 'CT4_active_weapon_SCAR-20', 'CT4_active_weapon_HE Grenade', 'CT4_active_weapon_Flashbang', 'CT4_active_weapon_Smoke Grenade', 'CT4_active_weapon_Incendiary Grenade', 'CT4_active_weapon_Molotov', 'CT4_active_weapon_Decoy Grenade',
            'CT4_hltv_rating_2.0', 'CT4_hltv_DPR', 'CT4_hltv_KAST', 'CT4_hltv_Impact', 'CT4_hltv_ADR', 'CT4_hltv_KPR', 'CT4_hltv_total_kills', 'CT4_hltv_HS%', 'CT4_hltv_total_deaths', 'CT4_hltv_KD_ratio', 'CT4_hltv_dmgPR', 'CT4_hltv_grenade_dmgPR', 'CT4_hltv_maps_played', 'CT4_hltv_saved_by_teammatePR', 'CT4_hltv_saved_teammatesPR', 'CT4_hltv_opening_kill_rating', 'CT4_hltv_team_W%_after_opening', 'CT4_hltv_opening_kill_in_W_rounds', 'CT4_hltv_rating_1.0_all_Career', 'CT4_hltv_clutches_1on1_ratio', 'CT4_hltv_clutches_won_1on1', 'CT4_hltv_clutches_won_1on2', 'CT4_hltv_clutches_won_1on3', 'CT4_hltv_clutches_won_1on4', 'CT4_hltv_clutches_won_1on5', 

            'T5_name', 'T5_team_clan_name', 'T5_X', 'T5_Y', 'T5_Z', 'T5_pitch', 'T5_yaw', 'T5_velocity_X', 'T5_velocity_Y', 'T5_velocity_Z', 'T5_health', 'T5_armor_value', 'T5_active_weapon_magazine_size', 'T5_active_weapon_ammo', 'T5_active_weapon_magazine_ammo_left_%', 'T5_active_weapon_max_ammo', 'T5_total_ammo_left', 'T5_active_weapon_total_ammo_left_%', 'T5_flash_duration', 'T5_flash_max_alpha', 'T5_balance', 'T5_current_equip_value', 'T5_round_start_equip_value', 'T5_cash_spent_this_round',
            'T5_is_alive', 'T5_is_CT', 'T5_is_shooting', 'T5_is_crouching', 'T5_is_ducking', 'T5_is_duck_jumping', 'T5_is_walking', 'T5_is_spotted', 'T5_is_scoped', 'T5_is_defusing', 'T5_is_reloading', 'T5_is_in_bombsite',
            'T5_zoom_lvl', 'T5_velo_modifier',
            'T5_stat_kills', 'T5_stat_HS_kills', 'T5_stat_opening_kills', 'T5_stat_MVPs', 'T5_stat_deaths', 'T5_stat_opening_deaths', 'T5_stat_assists', 'T5_stat_flash_assists', 'T5_stat_damage', 'T5_stat_weapon_damage', 'T5_stat_nade_damage', 'T5_stat_survives', 'T5_stat_KPR', 'T5_stat_ADR', 'T5_stat_DPR', 'T5_stat_HS%', 'T5_stat_SPR', 
            'T5_inventory_C4', 'T5_inventory_Taser', 'T5_inventory_USP-S', 'T5_inventory_P2000', 'T5_inventory_Glock-18', 'T5_inventory_Dual Berettas', 'T5_inventory_P250', 'T5_inventory_Tec-9', 'T5_inventory_CZ75 Auto', 'T5_inventory_Five-SeveN', 'T5_inventory_Desert Eagle', 'T5_inventory_R8 Revolver', 'T5_inventory_MAC-10', 'T5_inventory_MP9', 'T5_inventory_MP7', 'T5_inventory_MP5-SD', 'T5_inventory_UMP-45', 'T5_inventory_PP-Bizon', 'T5_inventory_P90', 'T5_inventory_Nova', 'T5_inventory_XM1014', 'T5_inventory_Sawed-Off', 'T5_inventory_MAG-7', 'T5_inventory_M249', 'T5_inventory_Negev', 'T5_inventory_FAMAS', 'T5_inventory_Galil AR', 'T5_inventory_AK-47', 'T5_inventory_M4A4', 'T5_inventory_M4A1-S', 'T5_inventory_SG 553', 'T5_inventory_AUG', 'T5_inventory_SSG 08', 'T5_inventory_AWP', 'T5_inventory_G3SG1', 'T5_inventory_SCAR-20', 'T5_inventory_HE Grenade', 'T5_inventory_Flashbang', 'T5_inventory_Smoke Grenade', 'T5_inventory_Incendiary Grenade', 'T5_inventory_Molotov', 'T5_inventory_Decoy Grenade',
            'T5_active_weapon_C4', 'T5_active_weapon_Knife', 'T5_active_weapon_Taser', 'T5_active_weapon_USP-S', 'T5_active_weapon_P2000', 'T5_active_weapon_Glock-18', 'T5_active_weapon_Dual Berettas', 'T5_active_weapon_P250', 'T5_active_weapon_Tec-9', 'T5_active_weapon_CZ75 Auto', 'T5_active_weapon_Five-SeveN', 'T5_active_weapon_Desert Eagle', 'T5_active_weapon_R8 Revolver', 'T5_active_weapon_MAC-10', 'T5_active_weapon_MP9', 'T5_active_weapon_MP7', 'T5_active_weapon_MP5-SD', 'T5_active_weapon_UMP-45', 'T5_active_weapon_PP-Bizon', 'T5_active_weapon_P90', 'T5_active_weapon_Nova', 'T5_active_weapon_XM1014', 'T5_active_weapon_Sawed-Off', 'T5_active_weapon_MAG-7', 'T5_active_weapon_M249', 'T5_active_weapon_Negev', 'T5_active_weapon_FAMAS', 'T5_active_weapon_Galil AR', 'T5_active_weapon_AK-47', 'T5_active_weapon_M4A4', 'T5_active_weapon_M4A1-S', 'T5_active_weapon_SG 553', 'T5_active_weapon_AUG', 'T5_active_weapon_SSG 08', 'T5_active_weapon_AWP', 'T5_active_weapon_G3SG1', 'T5_active_weapon_SCAR-20', 'T5_active_weapon_HE Grenade', 'T5_active_weapon_Flashbang', 'T5_active_weapon_Smoke Grenade', 'T5_active_weapon_Incendiary Grenade', 'T5_active_weapon_Molotov', 'T5_active_weapon_Decoy Grenade',
            'T5_hltv_rating_2.0', 'T5_hltv_DPR', 'T5_hltv_KAST', 'T5_hltv_Impact', 'T5_hltv_ADR', 'T5_hltv_KPR', 'T5_hltv_total_kills', 'T5_hltv_HS%', 'T5_hltv_total_deaths', 'T5_hltv_KD_ratio', 'T5_hltv_dmgPR', 'T5_hltv_grenade_dmgPR', 'T5_hltv_maps_played', 'T5_hltv_saved_by_teammatePR', 'T5_hltv_saved_teammatesPR', 'T5_hltv_opening_kill_rating', 'T5_hltv_team_W%_after_opening', 'T5_hltv_opening_kill_in_W_rounds', 'T5_hltv_rating_1.0_all_Career', 'T5_hltv_clutches_1on1_ratio', 'T5_hltv_clutches_won_1on1', 'T5_hltv_clutches_won_1on2', 'T5_hltv_clutches_won_1on3', 'T5_hltv_clutches_won_1on4', 'T5_hltv_clutches_won_1on5', 

            'T6_name', 'T6_team_clan_name', 'T6_X', 'T6_Y', 'T6_Z', 'T6_pitch', 'T6_yaw', 'T6_velocity_X', 'T6_velocity_Y', 'T6_velocity_Z', 'T6_health', 'T6_armor_value', 'T6_active_weapon_magazine_size', 'T6_active_weapon_ammo', 'T6_active_weapon_magazine_ammo_left_%', 'T6_active_weapon_max_ammo', 'T6_total_ammo_left', 'T6_active_weapon_total_ammo_left_%', 'T6_flash_duration', 'T6_flash_max_alpha', 'T6_balance', 'T6_current_equip_value', 'T6_round_start_equip_value', 'T6_cash_spent_this_round',
            'T6_is_alive', 'T6_is_CT', 'T6_is_shooting', 'T6_is_crouching', 'T6_is_ducking', 'T6_is_duck_jumping', 'T6_is_walking', 'T6_is_spotted', 'T6_is_scoped', 'T6_is_defusing', 'T6_is_reloading', 'T6_is_in_bombsite',
            'T6_zoom_lvl', 'T6_velo_modifier',
            'T6_stat_kills', 'T6_stat_HS_kills', 'T6_stat_opening_kills', 'T6_stat_MVPs', 'T6_stat_deaths', 'T6_stat_opening_deaths', 'T6_stat_assists', 'T6_stat_flash_assists', 'T6_stat_damage', 'T6_stat_weapon_damage', 'T6_stat_nade_damage', 'T6_stat_survives', 'T6_stat_KPR', 'T6_stat_ADR', 'T6_stat_DPR', 'T6_stat_HS%', 'T6_stat_SPR', 
            'T6_inventory_C4', 'T6_inventory_Taser', 'T6_inventory_USP-S', 'T6_inventory_P2000', 'T6_inventory_Glock-18', 'T6_inventory_Dual Berettas', 'T6_inventory_P250', 'T6_inventory_Tec-9', 'T6_inventory_CZ75 Auto', 'T6_inventory_Five-SeveN', 'T6_inventory_Desert Eagle', 'T6_inventory_R8 Revolver', 'T6_inventory_MAC-10', 'T6_inventory_MP9', 'T6_inventory_MP7', 'T6_inventory_MP5-SD', 'T6_inventory_UMP-45', 'T6_inventory_PP-Bizon', 'T6_inventory_P90', 'T6_inventory_Nova', 'T6_inventory_XM1014', 'T6_inventory_Sawed-Off', 'T6_inventory_MAG-7', 'T6_inventory_M249', 'T6_inventory_Negev', 'T6_inventory_FAMAS', 'T6_inventory_Galil AR', 'T6_inventory_AK-47', 'T6_inventory_M4A4', 'T6_inventory_M4A1-S', 'T6_inventory_SG 553', 'T6_inventory_AUG', 'T6_inventory_SSG 08', 'T6_inventory_AWP', 'T6_inventory_G3SG1', 'T6_inventory_SCAR-20', 'T6_inventory_HE Grenade', 'T6_inventory_Flashbang', 'T6_inventory_Smoke Grenade', 'T6_inventory_Incendiary Grenade', 'T6_inventory_Molotov', 'T6_inventory_Decoy Grenade',
            'T6_active_weapon_C4', 'T6_active_weapon_Knife', 'T6_active_weapon_Taser', 'T6_active_weapon_USP-S', 'T6_active_weapon_P2000', 'T6_active_weapon_Glock-18', 'T6_active_weapon_Dual Berettas', 'T6_active_weapon_P250', 'T6_active_weapon_Tec-9', 'T6_active_weapon_CZ75 Auto', 'T6_active_weapon_Five-SeveN', 'T6_active_weapon_Desert Eagle', 'T6_active_weapon_R8 Revolver', 'T6_active_weapon_MAC-10', 'T6_active_weapon_MP9', 'T6_active_weapon_MP7', 'T6_active_weapon_MP5-SD', 'T6_active_weapon_UMP-45', 'T6_active_weapon_PP-Bizon', 'T6_active_weapon_P90', 'T6_active_weapon_Nova', 'T6_active_weapon_XM1014', 'T6_active_weapon_Sawed-Off', 'T6_active_weapon_MAG-7', 'T6_active_weapon_M249', 'T6_active_weapon_Negev', 'T6_active_weapon_FAMAS', 'T6_active_weapon_Galil AR', 'T6_active_weapon_AK-47', 'T6_active_weapon_M4A4', 'T6_active_weapon_M4A1-S', 'T6_active_weapon_SG 553', 'T6_active_weapon_AUG', 'T6_active_weapon_SSG 08', 'T6_active_weapon_AWP', 'T6_active_weapon_G3SG1', 'T6_active_weapon_SCAR-20', 'T6_active_weapon_HE Grenade', 'T6_active_weapon_Flashbang', 'T6_active_weapon_Smoke Grenade', 'T6_active_weapon_Incendiary Grenade', 'T6_active_weapon_Molotov', 'T6_active_weapon_Decoy Grenade',
            'T6_hltv_rating_2.0', 'T6_hltv_DPR', 'T6_hltv_KAST', 'T6_hltv_Impact', 'T6_hltv_ADR', 'T6_hltv_KPR', 'T6_hltv_total_kills', 'T6_hltv_HS%', 'T6_hltv_total_deaths', 'T6_hltv_KD_ratio', 'T6_hltv_dmgPR', 'T6_hltv_grenade_dmgPR', 'T6_hltv_maps_played', 'T6_hltv_saved_by_teammatePR', 'T6_hltv_saved_teammatesPR', 'T6_hltv_opening_kill_rating', 'T6_hltv_team_W%_after_opening', 'T6_hltv_opening_kill_in_W_rounds', 'T6_hltv_rating_1.0_all_Career', 'T6_hltv_clutches_1on1_ratio', 'T6_hltv_clutches_won_1on1', 'T6_hltv_clutches_won_1on2', 'T6_hltv_clutches_won_1on3', 'T6_hltv_clutches_won_1on4', 'T6_hltv_clutches_won_1on5', 

            'T7_name', 'T7_team_clan_name', 'T7_X', 'T7_Y', 'T7_Z', 'T7_pitch', 'T7_yaw', 'T7_velocity_X', 'T7_velocity_Y', 'T7_velocity_Z', 'T7_health', 'T7_armor_value', 'T7_active_weapon_magazine_size', 'T7_active_weapon_ammo', 'T7_active_weapon_magazine_ammo_left_%', 'T7_active_weapon_max_ammo', 'T7_total_ammo_left', 'T7_active_weapon_total_ammo_left_%', 'T7_flash_duration', 'T7_flash_max_alpha', 'T7_balance', 'T7_current_equip_value', 'T7_round_start_equip_value', 'T7_cash_spent_this_round',
            'T7_is_alive', 'T7_is_CT', 'T7_is_shooting', 'T7_is_crouching', 'T7_is_ducking', 'T7_is_duck_jumping', 'T7_is_walking', 'T7_is_spotted', 'T7_is_scoped', 'T7_is_defusing', 'T7_is_reloading', 'T7_is_in_bombsite',
            'T7_zoom_lvl', 'T7_velo_modifier',
            'T7_stat_kills', 'T7_stat_HS_kills', 'T7_stat_opening_kills', 'T7_stat_MVPs', 'T7_stat_deaths', 'T7_stat_opening_deaths', 'T7_stat_assists', 'T7_stat_flash_assists', 'T7_stat_damage', 'T7_stat_weapon_damage', 'T7_stat_nade_damage', 'T7_stat_survives', 'T7_stat_KPR', 'T7_stat_ADR', 'T7_stat_DPR', 'T7_stat_HS%', 'T7_stat_SPR', 
            'T7_inventory_C4', 'T7_inventory_Taser', 'T7_inventory_USP-S', 'T7_inventory_P2000', 'T7_inventory_Glock-18', 'T7_inventory_Dual Berettas', 'T7_inventory_P250', 'T7_inventory_Tec-9', 'T7_inventory_CZ75 Auto', 'T7_inventory_Five-SeveN', 'T7_inventory_Desert Eagle', 'T7_inventory_R8 Revolver', 'T7_inventory_MAC-10', 'T7_inventory_MP9', 'T7_inventory_MP7', 'T7_inventory_MP5-SD', 'T7_inventory_UMP-45', 'T7_inventory_PP-Bizon', 'T7_inventory_P90', 'T7_inventory_Nova', 'T7_inventory_XM1014', 'T7_inventory_Sawed-Off', 'T7_inventory_MAG-7', 'T7_inventory_M249', 'T7_inventory_Negev', 'T7_inventory_FAMAS', 'T7_inventory_Galil AR', 'T7_inventory_AK-47', 'T7_inventory_M4A4', 'T7_inventory_M4A1-S', 'T7_inventory_SG 553', 'T7_inventory_AUG', 'T7_inventory_SSG 08', 'T7_inventory_AWP', 'T7_inventory_G3SG1', 'T7_inventory_SCAR-20', 'T7_inventory_HE Grenade', 'T7_inventory_Flashbang', 'T7_inventory_Smoke Grenade', 'T7_inventory_Incendiary Grenade', 'T7_inventory_Molotov', 'T7_inventory_Decoy Grenade',
            'T7_active_weapon_C4', 'T7_active_weapon_Knife', 'T7_active_weapon_Taser', 'T7_active_weapon_USP-S', 'T7_active_weapon_P2000', 'T7_active_weapon_Glock-18', 'T7_active_weapon_Dual Berettas', 'T7_active_weapon_P250', 'T7_active_weapon_Tec-9', 'T7_active_weapon_CZ75 Auto', 'T7_active_weapon_Five-SeveN', 'T7_active_weapon_Desert Eagle', 'T7_active_weapon_R8 Revolver', 'T7_active_weapon_MAC-10', 'T7_active_weapon_MP9', 'T7_active_weapon_MP7', 'T7_active_weapon_MP5-SD', 'T7_active_weapon_UMP-45', 'T7_active_weapon_PP-Bizon', 'T7_active_weapon_P90', 'T7_active_weapon_Nova', 'T7_active_weapon_XM1014', 'T7_active_weapon_Sawed-Off', 'T7_active_weapon_MAG-7', 'T7_active_weapon_M249', 'T7_active_weapon_Negev', 'T7_active_weapon_FAMAS', 'T7_active_weapon_Galil AR', 'T7_active_weapon_AK-47', 'T7_active_weapon_M4A4', 'T7_active_weapon_M4A1-S', 'T7_active_weapon_SG 553', 'T7_active_weapon_AUG', 'T7_active_weapon_SSG 08', 'T7_active_weapon_AWP', 'T7_active_weapon_G3SG1', 'T7_active_weapon_SCAR-20', 'T7_active_weapon_HE Grenade', 'T7_active_weapon_Flashbang', 'T7_active_weapon_Smoke Grenade', 'T7_active_weapon_Incendiary Grenade', 'T7_active_weapon_Molotov', 'T7_active_weapon_Decoy Grenade',
            'T7_hltv_rating_2.0', 'T7_hltv_DPR', 'T7_hltv_KAST', 'T7_hltv_Impact', 'T7_hltv_ADR', 'T7_hltv_KPR', 'T7_hltv_total_kills', 'T7_hltv_HS%', 'T7_hltv_total_deaths', 'T7_hltv_KD_ratio', 'T7_hltv_dmgPR', 'T7_hltv_grenade_dmgPR', 'T7_hltv_maps_played', 'T7_hltv_saved_by_teammatePR', 'T7_hltv_saved_teammatesPR', 'T7_hltv_opening_kill_rating', 'T7_hltv_team_W%_after_opening', 'T7_hltv_opening_kill_in_W_rounds', 'T7_hltv_rating_1.0_all_Career', 'T7_hltv_clutches_1on1_ratio', 'T7_hltv_clutches_won_1on1', 'T7_hltv_clutches_won_1on2', 'T7_hltv_clutches_won_1on3', 'T7_hltv_clutches_won_1on4', 'T7_hltv_clutches_won_1on5', 

            'T8_name', 'T8_team_clan_name', 'T8_X', 'T8_Y', 'T8_Z', 'T8_pitch', 'T8_yaw', 'T8_velocity_X', 'T8_velocity_Y', 'T8_velocity_Z', 'T8_health', 'T8_armor_value', 'T8_active_weapon_magazine_size', 'T8_active_weapon_ammo', 'T8_active_weapon_magazine_ammo_left_%', 'T8_active_weapon_max_ammo', 'T8_total_ammo_left', 'T8_active_weapon_total_ammo_left_%', 'T8_flash_duration', 'T8_flash_max_alpha', 'T8_balance', 'T8_current_equip_value', 'T8_round_start_equip_value', 'T8_cash_spent_this_round',
            'T8_is_alive', 'T8_is_CT', 'T8_is_shooting', 'T8_is_crouching', 'T8_is_ducking', 'T8_is_duck_jumping', 'T8_is_walking', 'T8_is_spotted', 'T8_is_scoped', 'T8_is_defusing', 'T8_is_reloading', 'T8_is_in_bombsite',
            'T8_zoom_lvl', 'T8_velo_modifier',
            'T8_stat_kills', 'T8_stat_HS_kills', 'T8_stat_opening_kills', 'T8_stat_MVPs', 'T8_stat_deaths', 'T8_stat_opening_deaths', 'T8_stat_assists', 'T8_stat_flash_assists', 'T8_stat_damage', 'T8_stat_weapon_damage', 'T8_stat_nade_damage', 'T8_stat_survives', 'T8_stat_KPR', 'T8_stat_ADR', 'T8_stat_DPR', 'T8_stat_HS%', 'T8_stat_SPR', 
            'T8_inventory_C4', 'T8_inventory_Taser', 'T8_inventory_USP-S', 'T8_inventory_P2000', 'T8_inventory_Glock-18', 'T8_inventory_Dual Berettas', 'T8_inventory_P250', 'T8_inventory_Tec-9', 'T8_inventory_CZ75 Auto', 'T8_inventory_Five-SeveN', 'T8_inventory_Desert Eagle', 'T8_inventory_R8 Revolver', 'T8_inventory_MAC-10', 'T8_inventory_MP9', 'T8_inventory_MP7', 'T8_inventory_MP5-SD', 'T8_inventory_UMP-45', 'T8_inventory_PP-Bizon', 'T8_inventory_P90', 'T8_inventory_Nova', 'T8_inventory_XM1014', 'T8_inventory_Sawed-Off', 'T8_inventory_MAG-7', 'T8_inventory_M249', 'T8_inventory_Negev', 'T8_inventory_FAMAS', 'T8_inventory_Galil AR', 'T8_inventory_AK-47', 'T8_inventory_M4A4', 'T8_inventory_M4A1-S', 'T8_inventory_SG 553', 'T8_inventory_AUG', 'T8_inventory_SSG 08', 'T8_inventory_AWP', 'T8_inventory_G3SG1', 'T8_inventory_SCAR-20', 'T8_inventory_HE Grenade', 'T8_inventory_Flashbang', 'T8_inventory_Smoke Grenade', 'T8_inventory_Incendiary Grenade', 'T8_inventory_Molotov', 'T8_inventory_Decoy Grenade',
            'T8_active_weapon_C4', 'T8_active_weapon_Knife', 'T8_active_weapon_Taser', 'T8_active_weapon_USP-S', 'T8_active_weapon_P2000', 'T8_active_weapon_Glock-18', 'T8_active_weapon_Dual Berettas', 'T8_active_weapon_P250', 'T8_active_weapon_Tec-9', 'T8_active_weapon_CZ75 Auto', 'T8_active_weapon_Five-SeveN', 'T8_active_weapon_Desert Eagle', 'T8_active_weapon_R8 Revolver', 'T8_active_weapon_MAC-10', 'T8_active_weapon_MP9', 'T8_active_weapon_MP7', 'T8_active_weapon_MP5-SD', 'T8_active_weapon_UMP-45', 'T8_active_weapon_PP-Bizon', 'T8_active_weapon_P90', 'T8_active_weapon_Nova', 'T8_active_weapon_XM1014', 'T8_active_weapon_Sawed-Off', 'T8_active_weapon_MAG-7', 'T8_active_weapon_M249', 'T8_active_weapon_Negev', 'T8_active_weapon_FAMAS', 'T8_active_weapon_Galil AR', 'T8_active_weapon_AK-47', 'T8_active_weapon_M4A4', 'T8_active_weapon_M4A1-S', 'T8_active_weapon_SG 553', 'T8_active_weapon_AUG', 'T8_active_weapon_SSG 08', 'T8_active_weapon_AWP', 'T8_active_weapon_G3SG1', 'T8_active_weapon_SCAR-20', 'T8_active_weapon_HE Grenade', 'T8_active_weapon_Flashbang', 'T8_active_weapon_Smoke Grenade', 'T8_active_weapon_Incendiary Grenade', 'T8_active_weapon_Molotov', 'T8_active_weapon_Decoy Grenade',
            'T8_hltv_rating_2.0', 'T8_hltv_DPR', 'T8_hltv_KAST', 'T8_hltv_Impact', 'T8_hltv_ADR', 'T8_hltv_KPR', 'T8_hltv_total_kills', 'T8_hltv_HS%', 'T8_hltv_total_deaths', 'T8_hltv_KD_ratio', 'T8_hltv_dmgPR', 'T8_hltv_grenade_dmgPR', 'T8_hltv_maps_played', 'T8_hltv_saved_by_teammatePR', 'T8_hltv_saved_teammatesPR', 'T8_hltv_opening_kill_rating', 'T8_hltv_team_W%_after_opening', 'T8_hltv_opening_kill_in_W_rounds', 'T8_hltv_rating_1.0_all_Career', 'T8_hltv_clutches_1on1_ratio', 'T8_hltv_clutches_won_1on1', 'T8_hltv_clutches_won_1on2', 'T8_hltv_clutches_won_1on3', 'T8_hltv_clutches_won_1on4', 'T8_hltv_clutches_won_1on5', 

            'T9_name', 'T9_team_clan_name', 'T9_X', 'T9_Y', 'T9_Z', 'T9_pitch', 'T9_yaw', 'T9_velocity_X', 'T9_velocity_Y', 'T9_velocity_Z', 'T9_health', 'T9_armor_value', 'T9_active_weapon_magazine_size', 'T9_active_weapon_ammo', 'T9_active_weapon_magazine_ammo_left_%', 'T9_active_weapon_max_ammo', 'T9_total_ammo_left', 'T9_active_weapon_total_ammo_left_%', 'T9_flash_duration', 'T9_flash_max_alpha', 'T9_balance', 'T9_current_equip_value', 'T9_round_start_equip_value', 'T9_cash_spent_this_round',
            'T9_is_alive', 'T9_is_CT', 'T9_is_shooting', 'T9_is_crouching', 'T9_is_ducking', 'T9_is_duck_jumping', 'T9_is_walking', 'T9_is_spotted', 'T9_is_scoped', 'T9_is_defusing', 'T9_is_reloading', 'T9_is_in_bombsite',
            'T9_zoom_lvl', 'T9_velo_modifier',
            'T9_stat_kills', 'T9_stat_HS_kills', 'T9_stat_opening_kills', 'T9_stat_MVPs', 'T9_stat_deaths', 'T9_stat_opening_deaths', 'T9_stat_assists', 'T9_stat_flash_assists', 'T9_stat_damage', 'T9_stat_weapon_damage', 'T9_stat_nade_damage', 'T9_stat_survives', 'T9_stat_KPR', 'T9_stat_ADR', 'T9_stat_DPR', 'T9_stat_HS%', 'T9_stat_SPR', 
            'T9_inventory_C4', 'T9_inventory_Taser', 'T9_inventory_USP-S', 'T9_inventory_P2000', 'T9_inventory_Glock-18', 'T9_inventory_Dual Berettas', 'T9_inventory_P250', 'T9_inventory_Tec-9', 'T9_inventory_CZ75 Auto', 'T9_inventory_Five-SeveN', 'T9_inventory_Desert Eagle', 'T9_inventory_R8 Revolver', 'T9_inventory_MAC-10', 'T9_inventory_MP9', 'T9_inventory_MP7', 'T9_inventory_MP5-SD', 'T9_inventory_UMP-45', 'T9_inventory_PP-Bizon', 'T9_inventory_P90', 'T9_inventory_Nova', 'T9_inventory_XM1014', 'T9_inventory_Sawed-Off', 'T9_inventory_MAG-7', 'T9_inventory_M249', 'T9_inventory_Negev', 'T9_inventory_FAMAS', 'T9_inventory_Galil AR', 'T9_inventory_AK-47', 'T9_inventory_M4A4', 'T9_inventory_M4A1-S', 'T9_inventory_SG 553', 'T9_inventory_AUG', 'T9_inventory_SSG 08', 'T9_inventory_AWP', 'T9_inventory_G3SG1', 'T9_inventory_SCAR-20', 'T9_inventory_HE Grenade', 'T9_inventory_Flashbang', 'T9_inventory_Smoke Grenade', 'T9_inventory_Incendiary Grenade', 'T9_inventory_Molotov', 'T9_inventory_Decoy Grenade',
            'T9_active_weapon_C4', 'T9_active_weapon_Knife', 'T9_active_weapon_Taser', 'T9_active_weapon_USP-S', 'T9_active_weapon_P2000', 'T9_active_weapon_Glock-18', 'T9_active_weapon_Dual Berettas', 'T9_active_weapon_P250', 'T9_active_weapon_Tec-9', 'T9_active_weapon_CZ75 Auto', 'T9_active_weapon_Five-SeveN', 'T9_active_weapon_Desert Eagle', 'T9_active_weapon_R8 Revolver', 'T9_active_weapon_MAC-10', 'T9_active_weapon_MP9', 'T9_active_weapon_MP7', 'T9_active_weapon_MP5-SD', 'T9_active_weapon_UMP-45', 'T9_active_weapon_PP-Bizon', 'T9_active_weapon_P90', 'T9_active_weapon_Nova', 'T9_active_weapon_XM1014', 'T9_active_weapon_Sawed-Off', 'T9_active_weapon_MAG-7', 'T9_active_weapon_M249', 'T9_active_weapon_Negev', 'T9_active_weapon_FAMAS', 'T9_active_weapon_Galil AR', 'T9_active_weapon_AK-47', 'T9_active_weapon_M4A4', 'T9_active_weapon_M4A1-S', 'T9_active_weapon_SG 553', 'T9_active_weapon_AUG', 'T9_active_weapon_SSG 08', 'T9_active_weapon_AWP', 'T9_active_weapon_G3SG1', 'T9_active_weapon_SCAR-20', 'T9_active_weapon_HE Grenade', 'T9_active_weapon_Flashbang', 'T9_active_weapon_Smoke Grenade', 'T9_active_weapon_Incendiary Grenade', 'T9_active_weapon_Molotov', 'T9_active_weapon_Decoy Grenade',
            'T9_hltv_rating_2.0', 'T9_hltv_DPR', 'T9_hltv_KAST', 'T9_hltv_Impact', 'T9_hltv_ADR', 'T9_hltv_KPR', 'T9_hltv_total_kills', 'T9_hltv_HS%', 'T9_hltv_total_deaths', 'T9_hltv_KD_ratio', 'T9_hltv_dmgPR', 'T9_hltv_grenade_dmgPR', 'T9_hltv_maps_played', 'T9_hltv_saved_by_teammatePR', 'T9_hltv_saved_teammatesPR', 'T9_hltv_opening_kill_rating', 'T9_hltv_team_W%_after_opening', 'T9_hltv_opening_kill_in_W_rounds', 'T9_hltv_rating_1.0_all_Career', 'T9_hltv_clutches_1on1_ratio', 'T9_hltv_clutches_won_1on1', 'T9_hltv_clutches_won_1on2', 'T9_hltv_clutches_won_1on3', 'T9_hltv_clutches_won_1on4', 'T9_hltv_clutches_won_1on5', 

            
            'numerical_match_id', 'match_id', 'tick', 'round', 'time', 'remaining_time', 'freeze_end', 'end', 'CT_wins', 
            'CT_score', 'T_score', 'CT_alive_num', 'T_alive_num', 'CT_total_hp', 'T_total_hp', 'CT_equipment_value', 'T_equipment_value',  'CT_losing_streak', 'T_losing_streak',
            'is_bomb_dropped', 'is_bomb_being_planted', 'is_bomb_being_defused', 'is_bomb_defused', 'is_bomb_planted_at_A_site', 'is_bomb_planted_at_B_site',
            'bomb_X', 'bomb_Y', 'bomb_Z', 'bomb_mx_pos1', 'bomb_mx_pos2', 'bomb_mx_pos3', 'bomb_mx_pos4', 'bomb_mx_pos5', 'bomb_mx_pos6', 'bomb_mx_pos7', 'bomb_mx_pos8', 'bomb_mx_pos9',
        ]

        # Rearrange the column order
        team_1_ct = team_1_ct.select(col_order)
        team_2_ct = team_2_ct.select(col_order)

        # Concatenate the two DataFrames
        renamed_df = pl.concat([team_1_ct, team_2_ct])

        # Add a temporary column
        renamed_df = renamed_df.with_columns([
            pl.lit(0).alias('temp_CT_score')
        ])

        # Swap the CT_score and T_score values for the second half
        renamed_df = renamed_df.with_columns([
            pl.when(pl.col('round') > 12)
            .then(pl.col('T_score'))
            .otherwise(pl.col('CT_score')).alias('CT_score'),
            pl.when(pl.col('round') > 12)
            .then(pl.col('CT_score'))
            .otherwise(pl.col('T_score')).alias('T_score')
        ])

        # Drop the temporary column
        renamed_df = renamed_df.drop(['temp_CT_score'])

        # Universal clan names
        renamed_df = renamed_df.with_columns([
            pl.col('CT0_team_clan_name').alias('CT_clan_name'),
            pl.col('T5_team_clan_name').alias('T_clan_name')
        ])

        # Drop the original columns
        renamed_df = renamed_df.drop([
            f'CT{player_idx}_team_clan_name' for player_idx in range(5)
        ] + [
            f'T{player_idx}_team_clan_name' for player_idx in range(5, 10)
        ])

        return renamed_df



    # 14. Rename overall columns
    def _POLARS_TABULAR_prefix_universal_columns(self, df: pl.DataFrame) -> pl.DataFrame:

        # Get universal columns
        universal_columns = [col for col in df.columns if not (col.startswith('CT0') or col.startswith('T5') or 
                                                               col.startswith('CT1') or col.startswith('T6') or 
                                                               col.startswith('CT2') or col.startswith('T7') or 
                                                               col.startswith('CT3') or col.startswith('T8') or 
                                                               col.startswith('CT4') or col.startswith('T9') or 
                                                               col in ['numerical_match_id', 'match_id'])]

        # Rename the columns
        df = df.rename({col: 'UNIVERSAL_' + col for col in universal_columns})

        # Rename the match_id and numerical_match_id columns
        df = df.rename({'match_id': 'MATCH_ID', 'numerical_match_id': 'NUMERICAL_MATCH_ID'})

        return df



    # 15. Build column dictionary
    def _POLARS_FINAL_build_dictionary(self, df: pl.DataFrame) -> pl.DataFrame:

        # Get the numerical columns
        numeric_cols = [col for col in df.columns if '_name' not in col and col not in ['MATCH_ID', 'NUMERICAL_MATCH_ID', 'UNIVERSAL_smokes_active', 'UNIVERSAL_infernos_active']]

        # Create min and max values in Polars
        min_values = df.select([pl.col(col).min().alias(f'min_{col}') for col in numeric_cols])
        max_values = df.select([pl.col(col).max().alias(f'max_{col}') for col in numeric_cols])

        # Extract values and create dictionary DataFrame
        min_values_list = min_values.to_numpy().flatten()
        max_values_list = max_values.to_numpy().flatten()

        df_dict = pl.DataFrame({
            'column': numeric_cols, 
            'min': min_values_list, 
            'max': max_values_list
        })

        return df_dict
    


    # 16. Drop the rows where the bomb is defused
    def _POLARS_EXT_filter_bomb_defused_rows(self, df):
        df = df.filter(pl.col('UNIVERSAL_is_bomb_defused') == 0)
        return df


