import os
import json
from utils.duelEvent import DuelEvent
from discord import Member

PATH = "../players.json"

class DataHolder:
    def __init__(self):
        if os.path.exists(PATH):
            with open(PATH, "r") as file:  # r = read mode, w = write mode
                self.data = json.load(file)  # data is a dict
            print("------ PLAYERS DATA LOADED FROM FILE")
        else:
            self.data: dict = {}
            print("------ PLAYERS DATA FILE NOT FOUND, NEW WILL BE GENERATED AFTER A DUEL")

    def save_to_disk(self):
        with open(PATH, "w") as file: # creates a file if not found
            json.dump(self.data, file, indent=4)
            # TODO: Add backup functionality.
            #  If error occurs at this step, JSON file becomes broken.
            #  No exception handling exists for that right now

    def add_user_if_not_exists(self, user: Member):
        self.data.setdefault(user.id, {"username": user.name, "xp": 0, "wins": 0, "losses": 0, "ties": 0, "games": 0})

    def log_duel_results(self, duel: DuelEvent):
        for player in duel.players:
            self.add_user_if_not_exists(player)
            self.data[player.id]["games"] += 1
        if not duel.is_a_tie:
            self.data[duel.winner.id]["wins"] += 1
            self.data[duel.winner.id]["xp"] += 20
            self.data[duel.loser.id]["losses"] += 1

    def stats(self, user: Member) -> dict:
        self.add_user_if_not_exists(user)
        return self.data[user.id]
