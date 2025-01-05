import datetime
import os


class DataBase:
    def __init__(self):
        self.subscribed_artists_db_path = "files/subscribed_artists.txt"
        self.last_update_file = "files/last_update.txt"

    def is_artist_idx_in_db(self, artist_idx):
        with open(self.subscribed_artists_db_path, "r") as f:
            lines = f.readlines()

        for line in lines:
            idx, artist_name = line.split(";")
            if idx == artist_idx:
                return True
        return False

    def add_artist_to_db(self, artist_idx, artist_name):
        if self.is_artist_idx_in_db(artist_idx):
            return
        with open(self.subscribed_artists_db_path, "a") as f:
            f.write(f"{artist_idx};{artist_name}\n")

    def remove_artist_from_db(self, artist_idx):
        with open(self.subscribed_artists_db_path, "r") as f:
            lines = f.readlines()

        artists_copy = []
        artist_removed = False
        for line in lines:
            idx, artist_name = line.split(";")
            if idx == artist_idx:
                lines.remove(line)
                artist_removed = True
            else:
                artists_copy.append((idx, artist_name))

        artists_copy = sorted(artists_copy, key=lambda x: x[1])

        with open(self.subscribed_artists_db_path, "w") as f:
            for idx, artist in artists_copy:
                self.add_artist_to_db(idx, artist)

        return artist_removed

    def get_artists_idx_and_names(self):
        if not os.path.exists(self.subscribed_artists_db_path):
            print("No subscribed artists or wrong path")
            return []

        with open(self.subscribed_artists_db_path, "r") as f:
            lines = f.readlines()

        idx = []
        names = []
        for line in lines:
            idx_, name = line.split(";")
            idx.append(idx_)
            names.append(name)
        return idx, names

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
