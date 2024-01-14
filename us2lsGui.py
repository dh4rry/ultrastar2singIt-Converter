import tkinter as tk
from tkinter import *
from tkinter import ttk
from tkinter import filedialog as fd
from tkinter.messagebox import showinfo
from configparser import ConfigParser
import ultrastar2singit as us


class ConverterUi:

    def __init__(self, root):
        self.config = ConfigParser()
        self.config.read('config.ini')
        self.root = root

    def draw_ui(self):
        self.root.title('UltraStar Lets Sing Converter')
        self.root.resizable(True, True)
        open_button = ttk.Button( self.root, text='Open UltraStar File', command=self.select_us_file )
        open_button.grid(row=0, column=0, padx='5', pady='5', sticky='ew')
        self.lblTSVTitle = Label(master=self.root,  text='TSV File')
        self.lblTSVTitle.grid(row=5, column=0, padx='5', pady='5', sticky='ew')
        self.TSVTitle = Entry(master=self.root, bg='white', width='30')
        self.TSVTitle.insert(0,self.config.get("main", "TSV", fallback=""))
        self.TSVTitle.grid(row=5, column=1, padx='5', pady='5', sticky='ew')
        self.choose_TSVFile_button = ttk.Button(self.root, text='Select TSV File',command=self.select_tsv)
        self.choose_TSVFile_button.grid(row=5, column=2, padx='5', pady='5', sticky='ew')
        self.lblDLCTitle = Label(master=self.root, text='Core Title Dir')
        self.lblDLCTitle.grid(row=6, column=0, padx='5', pady='5', sticky='ew')
        self.DLCTitle = Entry(master=self.root,  width='30')
        self.DLCTitle.grid(row=6, column=1, padx='5', pady='5', sticky='ew')
        self.DLCTitle.insert(0,self.config.get("main", "DLC", fallback=""))
        self.choose_dlctitle_button = ttk.Button(self.root, text='Select DLC Dir', command=self.select_dlc_Folder )
        self.choose_dlctitle_button.grid(row=6, column=2, padx='5', pady='5', sticky='ew')
        self.us_frame = Frame(self.root)
        self.us_frame.grid(row=2, column=0, columnspan=3, padx='5', pady='5', sticky='ew')


    def save_config(self):
        with open('config.ini', 'w') as configfile:    # save
            self.config.write(configfile)

    def select_us_file(self):
        filetypes = (
            ('text files', '*.txt'),
            ('All files', '*.*')
        )

        filename = fd.askopenfilename(
            title='Open UltraStar file',
            filetypes=filetypes)

        self.us_data = us.parse_file(filename)
        self.show_us_data()

    def select_tsv(self):
        filetypes = (
            ('TSV File', '*.tsv'),
            ('All files', '*.*')
        )

        filename = fd.askopenfilename(
            title='Open TSV file (from Core Title)',
            filetypes=filetypes)
        
        if filename:
            self.TSVTitle.delete(0, tk.END)
            self.TSVTitle.insert(0, filename)
            self.config.set("main", "TSV", filename)
            self.save_config()

    def select_dlc_Folder(self):
        folder = fd.askdirectory()
        if folder:
            self.DLCTitle.delete(0, tk.END)
            self.DLCTitle.insert(0, folder)
            self.config.set("main", "DLC", folder)
            self.save_config()


    def show_us_data(self):
        self.us_stringvars = {}
        self.us_frame.destroy()
        self.us_frame = Frame(self.root, bg="Lightgray", borderwidth=1, relief=RIDGE)
        self.us_frame.grid(row=2, column=0, columnspan=3, padx='5', pady='5', sticky='ew')
        self.show_single_data("ID", "ID", 1)
        self.show_single_data("TITLE", "Titel", 2)
        self.show_single_data("ARTIST", "Artist", 3)
        self.show_single_data("GENRE", "Gerne", 4)
        self.show_single_data("YEAR", "Year", 5)
        self.show_single_data("GAP", "Gap", 6)
        

    def show_single_data(self, key, lable, row):
        string_var = tk.StringVar(self.us_frame, self.us_data[key] , key)
        self.us_stringvars[key] = string_var
        lbl = Label(master=self.us_frame,  text=lable)
        lbl.grid(row=row, column=0, padx='5', pady='5', sticky='ew')
        ent = Entry(master=self.us_frame,  textvariable=string_var)
        ent.grid(row=row, column=1, padx='5', pady='5', sticky='ew')
        string_var.trace_add("write", self.trace_us_data)
        print("test " + "AA")

    def trace_us_data(self, key, *args):
        self.us_data[key] = self.us_stringvars[key].get()
        print(self.us_data)


root = tk.Tk()
ui = ConverterUi(root)
ui.draw_ui()
    # run the application
root.mainloop()