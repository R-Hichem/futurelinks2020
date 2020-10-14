import os
import tkinter.messagebox
from tkinter import *
from tkinter import filedialog
import logging
import linkpred
import networkx as nx
import matplotlib.backends.backend_qt5agg
import matplotlib.pyplot as plt
from tkinter import ttk
from ttkthemes import themed_tk as tk


root = tk.ThemedTk()
root.get_themes()                 # Returns a list of all themes that can be set
root.set_theme("radiance")         # Sets an available theme


statusbar = ttk.Label(root, text="Link Prediction",
                      relief=SUNKEN, anchor=W, font='Times 10 italic')
statusbar.pack(side=BOTTOM, fill=X)

# Create the menubar
menubar = Menu(root)
root.config(menu=menubar)

# Create the submenu

subMenu = Menu(menubar, tearoff=0)

playlist = []
filename_path = []


def browse_file():
    global filename_path
    filename_path = filedialog.askopenfilename(initialdir="/", title="Select file",
                                               filetypes=(("Graph NET", "*.net"), ("all files", "*.*")))
    add_to_playlist(filename_path)


def remove():
    global H
    global filename_path
    log = logging.getLogger(__name__)  # recherche
    G = linkpred.read_network(filename_path)
    H = G.copy()
    num_loops = nx.number_of_selfloops(G)

    if num_loops:

        sentence = ("Network contains {} self-loops. "
                    "Removing..."+format(num_loops))

        H.remove_edges_from(nx.selfloop_edges(G))
        txt.delete(0.0, END)
        txt.insert(0.0, sentence)


def plot():
    global H
    H = nx.dodecahedral_graph()
    nx.draw(H)
    nx.draw(H, pos=nx.spring_layout(H))  # use spring layout
    plt.show()


def prediction():
    global H
    global filename_path
    CommonNeighbours = linkpred.predictors.CommonNeighbours(
        H, excluded=H.edges())
    CommonNeighbours_results = CommonNeighbours.predict()
    top = CommonNeighbours_results.top()
    for authors, score in top.items():
        sentence = ("Il existe une relation thématique et chronologique à exploiter entre : \n" + str(authors) + "\n" + "le score (indice de confiance) est :\n" +
                    str(score)+"\n"+"Plus la valeur est supérieure à 1.0 plus la possibilitée de relation entre ces auteurs est forte\n")
        txt1.insert(0.0, sentence)
       # txt.insert(1.0, score)


def add_to_playlist(filename):
    filename = os.path.basename(filename)
    index = 0
    playlistbox.insert(index, filename)
    playlist.insert(index, filename_path)
    index += 1


menubar.add_cascade(label="File", menu=subMenu)
subMenu.add_command(label="Open", command=browse_file)
subMenu.add_command(label="Exit", command=root.destroy)


def about_us():
    tkinter.messagebox.showinfo(
        'About LinkPredict ', 'This program is created by @AbdelghaniLAIFA for predicting new links between authors')


subMenu = Menu(menubar, tearoff=0)
menubar.add_cascade(label="Help", menu=subMenu)
subMenu.add_command(label="About Us", command=about_us)


root.title("Link predict")
root.iconbitmap(r'images/link.ico')


leftframe = Frame(root)
leftframe.pack(side=LEFT, padx=30, pady=30)

playlistbox = Listbox(leftframe)
playlistbox.pack()

addBtn = ttk.Button(leftframe, text="+ Add", command=browse_file)
addBtn.pack(side=LEFT)


def del_song():
    selected_song = playlistbox.curselection()
    selected_song = int(selected_song[0])
    playlistbox.delete(selected_song)
    playlist.pop(selected_song)


delBtn = ttk.Button(leftframe, text="- Del", command=del_song)
delBtn.pack(side=LEFT)

rightframe = Frame(root)
rightframe.pack(pady=30)

topframe = Frame(rightframe)
topframe.pack()


Linkprediction = ttk.Label(topframe, text='LINK PREDICTION', relief=GROOVE)
Linkprediction.pack()


middleframe = Frame(rightframe)
middleframe.pack(pady=30, padx=30)


playPhoto = PhotoImage(file='images/bouton_predict.png')
playBtn = ttk.Button(middleframe, image=playPhoto, command=prediction)
playBtn.grid(row=0, column=1, padx=10)

stopPhoto = PhotoImage(file='images/bouton_self-loop-remover.png')
stopBtn = ttk.Button(middleframe, image=stopPhoto, command=remove)
stopBtn.grid(row=0, column=0, padx=10)

"""plotPhoto = PhotoImage(file='images/bouton_new-network.png')
plotBtn = ttk.Button(middleframe, image=plotPhoto, command=plot)
plotBtn.grid(row=0, column=2, padx=10)"""


txt1 = Text(middleframe, width=30, height=30, wrap=WORD)
txt1.grid(row=3, columnspan=3, sticky=E)

txt = Text(middleframe, width=25, height=10, wrap=WORD)
txt.grid(row=3, columnspan=2, sticky=W)


def on_closing():

    root.destroy()


root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()
