import datetime

from modules.utils import read_json, write_json


class DataBase:
    def __init__(self):
        self.subscribed_artists_db_path = "files/subscribed_artists.json"
        self.last_update_file = "files/last_update.txt"

    def is_artist_idx_in_db(self, guild_id, author_id, artist_idx):
        data = read_json(self.subscribed_artists_db_path)
        if str(guild_id) not in data:
            return False
        if str(author_id) not in data[str(guild_id)]:
            return False

        for artist_dict in data[str(guild_id)][str(author_id)]:
            if artist_dict["idx"] == artist_idx:
                return True

        return False

    def add_artist_to_db(self, guild_id, author_id, artist_idx, artist_name):
        data = read_json(self.subscribed_artists_db_path)
        if str(guild_id) not in data:
            data[str(guild_id)] = {}

        if str(author_id) not in data[str(guild_id)]:
            data[str(guild_id)][str(author_id)] = []

        data[str(guild_id)][str(author_id)].append({"idx": artist_idx, "name": artist_name})

        write_json(self.subscribed_artists_db_path, data)

    def remove_artist_from_db(self, guild_id, author_id, artist_idx):
        data = read_json(self.subscribed_artists_db_path)
        if str(guild_id) not in data:
            return False

        if str(author_id) not in data[str(guild_id)]:
            return False

        for artist_dict in data[str(guild_id)][str(author_id)]:
            if artist_dict["idx"] == artist_idx:
                data[str(guild_id)][str(author_id)].remove(artist_dict)
                write_json(self.subscribed_artists_db_path, data)
                return True

        return False

    def get_artists_idx_and_names(self):
        guild_id_list = []
        user_id_list = []
        artist_idx_list = []
        artist_names_list = []

        data = read_json(self.subscribed_artists_db_path)
        for guild_id in data:
            for author_id in data[guild_id]:
                for artist_dict in data[guild_id][author_id]:
                    artist_idx_list.append(artist_dict["idx"])
                    artist_names_list.append(artist_dict["name"])
                    guild_id_list.append(guild_id)
                    user_id_list.append(author_id)
        return artist_idx_list, artist_names_list, guild_id_list, user_id_list

    def get_last_update_datetime(self):
        try:
            with open(self.last_update_file, "r") as f:
                last_update = datetime.datetime.strptime(f.read().strip(), "%Y-%m-%dT%H:%M:%SZ")
        except FileNotFoundError:
            print("\t[Error] couldn't get last update")
            return 0
        return last_update

    def save_new_last_update(self):
        current_datetime = datetime.datetime.now()
        formatted_datetime = current_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")
        with open(self.last_update_file, "w") as file:
            file.write(formatted_datetime)


database = DataBase()
