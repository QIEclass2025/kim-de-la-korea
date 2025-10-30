
import tkinter as tk
from tkinter import font
import random
import json
import urllib.request
import base64

class RockPaperScissorsGUI:
    """
    A GUI for the strategic 'Rock-Paper-Scissors Subtract One' game with API integration.

    Game Rules:
    1. Player chooses two hands.
    2. Computer chooses two hands, which are then revealed to the player.
    3. Player sees the computer's hands and strategically decides which of their own to keep.
    4. The computer uses an AI to predict the player's move and chooses its own hand to counter.
    5. On winning, a wild Pokemon appears to celebrate!
    """
    def __init__(self, master):
        self.master = master
        self.master.title("가위바위보 - 하나빼기 (API 버전)")
        self.master.geometry("500x550")
        self.master.resizable(False, False)

        # Game options and state variables
        self.options = {"바위": "rock", "보": "paper", "가위": "scissors"}
        self.player_choices = []
        self.computer_choices = []
        self.player_score = 0
        self.computer_score = 0
        self.pokemon_image = None # To prevent garbage collection

        # Setup fonts
        self.default_font = font.Font(family="Malgun Gothic", size=12)
        self.info_font = font.Font(family="Malgun Gothic", size=14, weight="bold")
        self.status_font = font.Font(family="Malgun Gothic", size=14, slant="italic")
        self.result_font = font.Font(family="Malgun Gothic", size=16, weight="bold")
        self.label_font = font.Font(family="Malgun Gothic", size=11)

        # --- UI Widgets ---
        self.info_label = tk.Label(master, text="첫 번째 손을 선택하세요", font=self.info_font, pady=10)
        self.info_label.pack()

        self.choice_frame = tk.Frame(master, pady=5)
        self.choice_frame.pack()

        self.buttons = {}
        for text in self.options.keys():
            self.buttons[text] = tk.Button(
                self.choice_frame, text=text, font=self.default_font, width=8,
                command=lambda t=text: self.make_initial_choice(t)
            )
            self.buttons[text].pack(side=tk.LEFT, padx=5)

        # --- Strategic Choice Section ---
        self.strategy_frame = tk.Frame(master, pady=10)
        self.strategy_frame.pack()

        # Player's side
        self.player_strategy_frame = tk.Frame(self.strategy_frame, padx=10)
        self.player_strategy_frame.pack(side=tk.LEFT, anchor='n')
        tk.Label(self.player_strategy_frame, text="[나의 패]", font=self.label_font).pack()
        self.player_selection_frame = tk.Frame(self.player_strategy_frame, pady=10)
        self.player_selection_frame.pack()
        self.final_choice_buttons = []

        # Computer's side
        self.computer_strategy_frame = tk.Frame(self.strategy_frame, padx=10)
        self.computer_strategy_frame.pack(side=tk.RIGHT, anchor='n')
        tk.Label(self.computer_strategy_frame, text="[컴퓨터의 패]", font=self.label_font).pack()
        self.computer_selection_frame = tk.Frame(self.computer_strategy_frame, pady=10)
        self.computer_selection_frame.pack()
        self.computer_hand1_label = tk.Label(self.computer_selection_frame, text="?", font=self.default_font, width=8, relief="solid", borderwidth=1, height=2)
        self.computer_hand2_label = tk.Label(self.computer_selection_frame, text="?", font=self.default_font, width=8, relief="solid", borderwidth=1, height=2)
        self.computer_hand1_label.pack(side=tk.LEFT, padx=5)
        self.computer_hand2_label.pack(side=tk.LEFT, padx=5)
        
        # --- Result Section ---
        self.result_display_frame = tk.Frame(master, pady=15)
        self.result_display_frame.pack()
        self.player_final_label = tk.Label(self.result_display_frame, text="", font=self.result_font, width=8)
        self.vs_label = tk.Label(self.result_display_frame, text="", font=self.default_font)
        self.computer_final_label = tk.Label(self.result_display_frame, text="", font=self.result_font, width=8)
        self.player_final_label.pack(side=tk.LEFT)
        self.vs_label.pack(side=tk.LEFT, padx=10)
        self.computer_final_label.pack(side=tk.LEFT)

        self.status_label = tk.Label(master, text="", font=self.status_font, pady=10)
        self.status_label.pack()

        self.score_label = tk.Label(master, text=self.get_score_text(), font=self.default_font)
        self.score_label.pack()

        self.play_again_button = tk.Button(master, text="다시하기", font=self.default_font, state=tk.DISABLED, command=self.reset_game)
        self.play_again_button.pack(pady=15)

    def get_score_text(self):
        return f"점수: 플레이어 {self.player_score} - {self.computer_score} 컴퓨터"

    def make_initial_choice(self, choice):
        if len(self.player_choices) < 2:
            self.player_choices.append(choice)
            self.buttons[choice].config(state=tk.DISABLED)

        if len(self.player_choices) == 1:
            self.info_label.config(text="두 번째 손을 선택하세요")
        elif len(self.player_choices) == 2:
            self.setup_final_choice_phase()

    def setup_final_choice_phase(self):
        for button in self.buttons.values():
            button.config(state=tk.DISABLED)

        self.computer_choices = random.sample(list(self.options.keys()), 2)
        self.computer_hand1_label.config(text=self.computer_choices[0])
        self.computer_hand2_label.config(text=self.computer_choices[1])
        
        self.info_label.config(text="컴퓨터의 패를 보고 남길 손을 고르세요!")

        for choice in self.player_choices:
            btn = tk.Button(
                self.player_selection_frame, text=choice, font=self.default_font, width=8, height=2,
                command=lambda c=choice: self.play_round(c)
            )
            btn.pack(side=tk.LEFT, padx=5)
            self.final_choice_buttons.append(btn)

    def get_outcome(self, hand1_k, hand2_k):
        h1 = self.options[hand1_k]
        h2 = self.options[hand2_k]
        if h1 == h2: return 0
        if (h1 == 'rock' and h2 == 'scissors') or (h1 == 'scissors' and h2 == 'paper') or (h1 == 'paper' and h2 == 'rock'): return 1
        return -1

    def get_computer_ai_choice(self):
        p_choices = list(set(self.player_choices))
        c1, c2 = self.computer_choices

        player_outcomes_vs_c1 = [self.get_outcome(p, c1) for p in p_choices]
        score_if_c1 = -max(player_outcomes_vs_c1)

        player_outcomes_vs_c2 = [self.get_outcome(p, c2) for p in p_choices]
        score_if_c2 = -max(player_outcomes_vs_c2)

        if score_if_c1 > score_if_c2: return c1
        if score_if_c2 > score_if_c1: return c2
        return random.choice([c1, c2])

    def show_win_popup(self):
        popup = tk.Toplevel(self.master)
        popup.title("승리!")
        popup.geometry("250x280")
        popup.resizable(False, False)

        try:
            pokemon_id = random.randint(1, 898) # Gen 1 to 8
            api_url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}"
            with urllib.request.urlopen(api_url) as response:
                data = json.load(response)
            
            sprite_url = data['sprites']['front_default']
            if not sprite_url: raise ValueError("Sprite URL not found")

            with urllib.request.urlopen(sprite_url) as response:
                image_data = response.read()
            
            base64_data = base64.b64encode(image_data)
            self.pokemon_image = tk.PhotoImage(data=base64_data).zoom(2) # Make image bigger
            
            image_label = tk.Label(popup, image=self.pokemon_image)
            image_label.pack(pady=10)

        except Exception as e:
            print(f"Pokemon API Error: {e}") # Log error for debugging

        win_label = tk.Label(popup, text="이겼어요!", font=self.info_font, fg="green")
        win_label.pack(pady=5)
        
        close_button = tk.Button(popup, text="닫기", command=popup.destroy, font=self.default_font)
        close_button.pack(pady=10)
        popup.transient(self.master)
        popup.grab_set()
        self.master.wait_window(popup)

    def play_round(self, player_final_choice_korean):
        for button in self.final_choice_buttons:
            button.config(state=tk.DISABLED)

        computer_final_choice_korean = self.get_computer_ai_choice()
        outcome = self.get_outcome(player_final_choice_korean, computer_final_choice_korean)
        
        winner = 'draw'
        if outcome == 1:
            winner = 'player'
            self.player_score += 1
        elif outcome == -1:
            winner = 'computer'
            self.computer_score += 1
        
        self.player_final_label.config(text=player_final_choice_korean, fg="blue")
        self.vs_label.config(text="vs")
        self.computer_final_label.config(text=computer_final_choice_korean, fg="red")

        status_messages = {
            'player': ("이겼습니다!", "green"),
            'computer': ("ㅠㅠ. 졌습니다.", "red"),
            'draw': ("비겼습니다!", "gray")
        }
        message, color = status_messages[winner]
        self.status_label.config(text=message, fg=color)
        
        self.score_label.config(text=self.get_score_text())
        self.play_again_button.config(state=tk.NORMAL)

        if winner == 'player':
            self.show_win_popup()

    def reset_game(self):
        self.player_choices = []
        self.computer_choices = []
        self.pokemon_image = None

        self.info_label.config(text="첫 번째 손을 선택하세요")
        
        for button in self.buttons.values():
            button.config(state=tk.NORMAL)

        for button in self.final_choice_buttons:
            button.destroy()
        self.final_choice_buttons = []

        self.computer_hand1_label.config(text="?")
        self.computer_hand2_label.config(text="?")

        self.player_final_label.config(text="")
        self.vs_label.config(text="")
        self.computer_final_label.config(text="")
        self.status_label.config(text="")

        self.play_again_button.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    game = RockPaperScissorsGUI(root)
    root.mainloop()
