import sqlite3

economy = sqlite3.connect("economy.db", timeout=3)
eccur = economy.cursor()
