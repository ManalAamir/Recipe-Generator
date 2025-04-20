import tkinter as tk
from tkinter import messagebox, simpledialog, Text
import requests
import sqlite3 as sql
import urllib
from random import randint
import urllib.parse

FILENAME = "test_recipe_03.db"
con = sql.connect(FILENAME)
C = con.cursor()
IDS = {-1}
APP_ID = "YOUR APP ID"
API_KEY = "YOUR API KEY"
URL = f'https://api.edamam.com/search?/app_id=${APP_ID}&app_key=${API_KEY}'

C.execute('''CREATE TABLE IF NOT EXISTS recipes (
               id INTEGER PRIMARY KEY,
               uri TEXT NOT NULL,
               label TEXT NOT NULL
             )''')
con.commit()

root = tk.Tk()
root.title("Recipe App")
root.geometry("800x600")

label = tk.Label(root, text="Recipe App", font=("Helvetica", 16))
label.pack(pady=10)

result_text = Text(root, height=15, width=70)
result_text.pack(pady=10)


def make_request(url):
    response = requests.get(url)
    data = response.json()
    return data


def get_url_q(key_word, _from=0, to=20):
    return URL + f'&q=${key_word}&to={to}&from={_from}'


def get_url_r(uri):
    return URL + f'&r={uri}'


def display_recipe_labels(data, index):
    result_text.delete(1.0, tk.END)
    result_text.insert(tk.END, "Results:\n")
    for i, recipe in enumerate(data):
        index += 1
        result_text.insert(tk.END, f"   {index}) {recipe['recipe']['label']}\n")
    return index


def select_from_index(max_index):
    select = -1
    while select is None or select <= 0 or select > max_index:
        select = simpledialog.askinteger("Select Recipe", f"Select Recipe # (1-{max_index}):", parent=root)
        if select == 'q':
            return 'q'
        elif select == 'm':
            return 'm'
    return select - 1


def filter_response(recipe):
    curr_recipe = {
        "ingredients_line": recipe["ingredientLines"],
        "label": recipe["label"],
        "url": recipe.get("url", ""),  # Check if "url" is present in the recipe
        "uri": recipe["uri"]
    }
    return curr_recipe


def display_recipe_dict(curr_recipe):
    recipe_text = (f"\n====================================================\n{curr_recipe['label']}"
                   f":\n----------------------------------------------------\n")
    for line in curr_recipe["ingredients_line"]:
        recipe_text += f"    - {line}\n"
    recipe_text += f"\nDirections: {curr_recipe['url']}\n===================================================="
    result_text.delete(1.0, tk.END)
    result_text.insert(tk.END, recipe_text)


def make_request_by_uri(id):
    C.execute(f"SELECT uri FROM recipes WHERE id = ?", (id,))
    uri = C.fetchall()[0][0]
    uri = urllib.parse.quote_plus(uri)
    url = get_url_r(uri)
    data = make_request(url)[0]
    return filter_response(data)


def display_saved_recipe(id):
    recipe = make_request_by_uri(id)
    display_recipe_dict(recipe)


def save_recipe(curr_recipe):
    id = -1
    if id in IDS:
        id = randint(100, 999)
    C.execute("INSERT into recipes (id, uri, label) values (?, ?, ?)",
              (id, curr_recipe["uri"], curr_recipe["label"]))
    C.execute("SELECT label FROM recipes WHERE label = ?", (curr_recipe["label"],))
    result = C.fetchall()
    saved_message = f"You are saving: '{result[0][0]}'\nSAVED"
    result_text.delete(1.0, tk.END)
    result_text.insert(tk.END, saved_message)
    if messagebox.askyesno("Confirm Save", "Confirm?"):
        con.commit()


def search_my_recipes():
    result_text.delete(1.0, tk.END)
    result_text.insert(tk.END, "Saved:\n---------------------------------------------\n")
    C.execute("SELECT label, id FROM recipes")
    result = C.fetchall()
    i = 0
    for recipe in result:
        i += 1
        result_text.insert(tk.END, f"   {i}) {recipe[0]}\n")
    result_text.insert(tk.END, "---------------------------------------------")
    select = ""
    while type(select) is not type(0):
        select = select_from_index(i)
    id = result[select][1]
    display_saved_recipe(id)


def open_recipe_link(curr_recipe):
    url = curr_recipe.get("url", "")
    if url:
        import webbrowser
        webbrowser.open(url)


def query_recipes():
    key_word = simpledialog.askstring("Find New Recipe", "Please enter a keyword:")
    data = make_request(get_url_q(key_word))
    data = data['hits']
    index = display_recipe_labels(data, 0)
    select = select_from_index(index)
    if select == 'm' and index == 20:
        _from = 20
        to = 40
        data2 = make_request(get_url_q(key_word, _from, to))
        data2 = data2['hits']
        index = display_recipe_labels(data2, index)
        data += data2
        select = -1
    select_recipe(data, index, select)


def select_recipe(data, max_index, select):
    invalid = True
    while invalid:
        if select == -1:
            select = select_from_index(max_index)
        if select == 'm':
            display_recipe_labels(data, 0)
            select = select_from_index(max_index)
        if select == 'q':
            return
        try:
            select = int(select)
            invalid = False
        except ValueError:
            invalid = True
            select = -1

    recipe_response = data[select]
    recipe = recipe_response["recipe"]
    curr_recipe = filter_response(recipe)
    display_recipe_dict(curr_recipe)
    if messagebox.askyesno("Save Recipe", "Would you like to save?"):
        save_recipe(curr_recipe)


button_find_recipe = tk.Button(root, text="Find New Recipe", command=query_recipes)
button_find_recipe.pack(pady=10)

button_search_saved = tk.Button(root, text="Search Saved Recipes", command=search_my_recipes)
button_search_saved.pack(pady=10)

button_open_link = tk.Button(root, text="Open Recipe Link", command=lambda: open_recipe_link(curr_recipe))
button_open_link.pack(pady=10)

button_quit = tk.Button(root, text="Quit", command=root.destroy)
button_quit.pack(pady=10)

curr_recipe = None

root.mainloop()

