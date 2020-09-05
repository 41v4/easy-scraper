import os
import json
import subprocess
import threading
import tkinter as tk
import tkinter.font as tkfont
from itertools import zip_longest
from tkinter import filedialog, ttk

from backend import codeGenerator


class menuBar(tk.Menu):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs, tearoff=False)
        self.parent = parent

        menu_bar = tk.Menu(self, tearoff=0)
        menu_bar.add_command(label="Import settings", command=self.import_settings)
        menu_bar.add_command(label="Export settings", command=self.export_settings)
        menu_bar.add_command(label="Exit", command=quit)

        options_menu = tk.Menu(menu_bar, tearoff=0)
        options_menu.add_command(
            label="XPATH combiner", command=self.insert_xpath_comb_win
        )
        options_menu.add_command(label="User agents (TO-DO)", command=None)

        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="About (TO-DO)", command=None)
        # Add cascades
        self.add_cascade(label="File", menu=menu_bar)
        self.add_cascade(label="Options", menu=options_menu)
        self.add_cascade(label="Help", menu=help_menu)

    def import_settings(self):
        # Get path of settings json file
        f = filedialog.askopenfilename(defaultextension=".json")
        if not f:
            return

        self.clear_current_settings()

        # Load json data from the filepath
        with open(f) as json_file:
            settings_data = json.load(json_file)

        # Insert loaded json data to empty widgets
        self.parent.main.project_name_entry.insert(
            tk.END, settings_data["project_name"]
        )
        self.parent.main.checkbutton_var.set(settings_data["overwrite_option"])
        self.insert_all_vals_to_links_box(settings_data["links_to_scrape"])
        self.insert_all_vals_to_sels_box(settings_data["elems_to_select"])
        self.parent.main.saving_format_combobox.set(settings_data["saving_format"])
        self.parent.main.chosen_s_dir.set(settings_data["saving_dir"])

    def clear_current_settings(self):
        self.parent.main.project_name_entry.delete(0, tk.END)
        self.parent.main.links_box.delete(*self.parent.main.links_box.get_children())
        self.parent.main.sels_box.delete(*self.parent.main.sels_box.get_children())
        self.parent.main.clear_logging_box()

    def export_settings(self):
        f = filedialog.asksaveasfile(mode="w", defaultextension=".json")
        if not f:
            return
        # Get settings data, dump to json file, close file
        settings_data = self.get_settings()
        json.dump(obj=settings_data, fp=f, indent=4)
        f.close()

    def get_settings(self):
        settings = {
            "project_name": self.parent.main.project_name_entry.get(),
            "overwrite_option": self.parent.main.checkbutton_var.get(),
            "links_to_scrape": self.get_all_vals_from_links_box(),
            "elems_to_select": self.get_all_vals_from_sels_box(),
            "saving_format": self.parent.main.saving_format_combobox.get(),
            "saving_dir": self.parent.main.chosen_s_dir.get(),
        }
        return settings

    def get_all_vals_from_links_box(self):
        vals = {}
        tree = self.parent.main.links_box
        # Iterate over treeview lines
        for num, line in enumerate(tree.get_children()):
            vals[num] = []
            # Iterate over single line values and append those values
            for value in tree.item(line)["values"]:
                vals[num].append(value)
        return vals

    def get_all_vals_from_sels_box(self):
        higher_lvl_vals = {}
        tree = self.parent.main.sels_box
        # Iterate over treeview main lines
        for num, line in enumerate(tree.get_children()):
            higher_lvl_vals[num] = []
            # Get and append text value of a single main line
            higher_lvl_vals[num].append(tree.item(line)["text"])
            # Iterate over single main line values and append those values
            for value in tree.item(line)["values"]:
                higher_lvl_vals[num].append(value)
            # Continue iterating over sub lines of treeview if they exists
            if tree.get_children(line):
                lower_lvl_vals = {}
                # Iterate over treeview sub lines
                for sub_num, sub_line in enumerate(tree.get_children(line)):
                    lower_lvl_vals[sub_num] = []
                    # Get and append text value of a single sub line
                    lower_lvl_vals[sub_num].append(tree.item(sub_line)["text"])
                    # Iterate over single sub line values and append those values
                    for value in tree.item(sub_line)["values"]:
                        lower_lvl_vals[sub_num].append(value)
                # Append sub line values to main line values
                higher_lvl_vals[num].append(lower_lvl_vals)
        return higher_lvl_vals

    def insert_all_vals_to_links_box(self, data):
        for items in data.values():
            self.parent.main.links_box.insert("", "end", values=(items[0], items[1]))

    def insert_all_vals_to_sels_box(self, data):
        for higher_items in data.values():
            higher_lvl_sel_insertion = self.parent.main.sels_box.insert(
                "",
                "end",
                text=higher_items[0],
                values=tuple(i for i in higher_items[1:6]),
            )
            # Check if the higher items contains lower lvl items
            if len(higher_items) == 7:
                for lower_items in higher_items[6].values():
                    self.parent.main.sels_box.insert(
                        higher_lvl_sel_insertion,
                        "end",
                        text=lower_items[0],
                        values=tuple(i for i in lower_items[1:6]),
                    )

    # Insert (pop-up) XPATH combine window
    def insert_xpath_comb_win(self):
        xpathCombWin(self.parent)


class xpathCombWin(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.parent = parent

        # Get x and y coordinates of root window
        x = self.winfo_rootx()
        y = self.winfo_rooty()

        # Create TopLevel window
        self.top = tk.Toplevel(self, padx=5)
        self.top.wm_title("XPATH combiner")
        self.top.geometry("+%d+%d" % (x + 50, y))

        # XPath labels and entries
        xpath_1_label = tk.Label(self.top, text="1st XPATH value:")
        xpath_1_label.pack(anchor="w")
        self.xpath_1_entry = tk.Entry(self.top, width=50)
        self.xpath_1_entry.pack(expand=True, fill="x")
        xpath_2_label = tk.Label(self.top, text="2nd XPATH value:")
        xpath_2_label.pack(anchor="w")
        self.xpath_2_entry = tk.Entry(self.top, width=50)
        self.xpath_2_entry.pack(expand=True, fill="x")

        paste_btn = tk.Button(self.top, text="Paste", command=self.paste_val)
        paste_btn.pack()

        # Horizontal separator
        h_sep = ttk.Separator(self.top, orient=tk.HORIZONTAL)
        h_sep.pack(fill="x", padx=5, pady=10, expand=True)

        # Combined XPath label, entry, combine button
        combined_xpath_label = tk.Label(self.top, text="Combined XPATH value:")
        combined_xpath_label.pack()
        self.combined_xpath_value = tk.Entry(self.top, width=50)
        self.combined_xpath_value.pack(expand=True, fill="x")
        combine_btn = tk.Button(self.top, text="COMBINE", command=self.comb_xpaths)
        combine_btn.pack()

        copy_btn = tk.Button(self.top, text="Copy", command=self.copy_comb_xpath)
        copy_btn.pack()

    # Combine joint Xpath from different Xpaths
    def comb_xpaths(self):
        comb_xpath = []

        # Get current XPaths from entries
        xp1 = self.xpath_1_entry.get()
        xp2 = self.xpath_2_entry.get()

        # Split obtained XPaths
        xp1_splitted = xp1.split("/")
        xp2_splitted = xp2.split("/")

        # Compare splitted XPaths
        if len(xp1_splitted) == len(xp2_splitted):
            for x, y in zip(xp1_splitted, xp2_splitted):
                if x == y:
                    comb_xpath.append(x)
                else:
                    x_splitted = x.split("[")
                    y_splitted = y.split("[")
                    if x_splitted[0] == y_splitted[0]:
                        comb_xpath.append(x_splitted[0])
                    else:
                        comb_xpath = ["Can't combine XPATHS"]
                        break
        else:
            comb_xpath = ["Can't combine XPATHS"]

        # Insert combined XPath value
        self.combined_xpath_value.delete(0, tk.END)
        self.combined_xpath_value.insert(tk.END, "/".join(comb_xpath))

    # Paste value from clipboard to active widget (entry)
    def paste_val(self):
        r = tk.Tk()
        r.withdraw()
        val = r.clipboard_get()
        focused_widget = self.focus_get()
        focused_widget.insert(tk.END, val)
        r.destroy()

    # Copy value from combined XPath entry to clipboard
    def copy_comb_xpath(self):
        r = tk.Tk()
        r.withdraw()
        r.clipboard_clear()
        r.clipboard_append(self.combined_xpath_value.get())
        r.update()
        r.destroy()


class insertLinkWin(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.parent = parent

        # Get x and y coordinates of root window
        x = self.winfo_rootx()
        y = self.winfo_rooty()

        # Create TopLevel window
        self.top = tk.Toplevel(self, padx=5)
        self.top.wm_title("Insert link")
        self.top.geometry("+%d+%d" % (x + 50, y))

        # Create URL label and entry
        url_label = tk.Label(self.top, text="URL:")
        url_label.grid(row=0, column=0, sticky="w")
        self.url_entry = tk.Entry(self.top, width=30)
        self.url_entry.grid(row=1, column=0)

        insert_btn = tk.Button(self.top, text="Insert", command=self.insert_url)
        insert_btn.grid(row=2, column=0)

    # Insert URL from URL entry to links box
    def insert_url(self):
        url = self.url_entry.get()

        if url:
            # Insert url to urls box
            self.parent.links_box.insert("", "end", values=("", url))
            # Set proper width of urls box "URL:" column
            self.parent.set_max_width(self.parent.links_box, "Link:", 300)


class followLinkWin(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.parent = parent

        # Get x and y coordinates of root window
        x = self.winfo_rootx()
        y = self.winfo_rooty()

        # Create TopLevel window
        self.top = tk.Toplevel(self)
        self.top.wm_title("Follow links")
        self.top.geometry("+%d+%d" % (x + 50, y))

        # Get selected item id and values from urls box
        if self.parent.links_box.selection():
            self.selected_item_id = self.parent.links_box.selection()[0]
            self.selected_item_vals = self.parent.links_box.item(self.selected_item_id)[
                "values"
            ]

        # CSS label and entry
        css_label = tk.Label(
            self.top, text="Insert follow link line eg.: response.css(...).get():"
        )
        css_label.grid(row=0, column=0, sticky="w")
        self.css_entry = tk.Entry(self.top, width=40)
        self.css_entry.grid(row=1, column=0)

        # If CSS selection exists, then insert that CSS selection to CSS entry widget
        # and change insert button to "insert" or "update" according to the current situation
        if self.selected_item_vals[0]:
            self.css_entry.insert(tk.END, self.selected_item_vals[0])
            insert_btn_text = "Update"
        else:
            insert_btn_text = "Insert"

        insert_btn = tk.Button(self.top, text=insert_btn_text, command=self.insert_css)
        insert_btn.grid(row=2, column=0)

    # Insert CSS to urls box
    def insert_css(self):
        css = self.css_entry.get()
        if css:
            self.parent.links_box.item(
                self.selected_item_id, values=(css, self.selected_item_vals[-1])
            )


class insertElemSelectionWin(tk.Frame):
    def __init__(self, parent, sels_box, edit, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.parent = parent
        self.sels_box = sels_box
        self.edit = edit
        # Global lower lvl selector index
        self.row_idx = 4
        # Local lower lvl selector index
        self.my_idx = 0
        self.lower_lvl_selectors = []
        self.lower_lvl_selects = {}

        # Get x and y coordinates of root window
        x = self.winfo_rootx()
        y = self.winfo_rooty()

        # Create TopLevel window
        self.top = tk.Toplevel(self, padx=5)
        self.top.wm_title("Insert Selector")
        self.top.geometry("+%d+%d" % (x + 50, y))

        # Get selected item id and values from selectors box
        if self.sels_box.selection():
            self.selected_item_id = self.sels_box.selection()[0]
            self.selected_item_vals = self.sels_box.item(self.selected_item_id)[
                "values"
            ]

        # Create "Insert Selector" window frames
        self.higher_lvl_frame = tk.Frame(self.top)
        self.higher_lvl_frame.grid(sticky="w")
        self.lower_lvl_frame = tk.Frame(self.top)
        self.lower_lvl_frame.grid()
        self.ctrls_frame = tk.Frame(self.top)
        self.ctrls_frame.grid()

        # Higher lvl frame title and separator
        self.higher_lvl_frame_title = tk.Label(
            self.higher_lvl_frame, text="Higher lvl. selector:"
        )
        self.higher_lvl_frame_title.grid(row=0, column=0, columnspan=6)
        self.higher_lvl_frame_sep = ttk.Separator(
            self.higher_lvl_frame, orient=tk.HORIZONTAL
        )
        self.higher_lvl_frame_sep.grid(row=1, column=0, columnspan=6, sticky="ew")

        # Higher lvl selector line labels
        higher_lvl_sel_name_label = tk.Label(self.higher_lvl_frame, text="Name:")
        higher_lvl_sel_name_label.grid(row=2, column=0, sticky="w")
        higher_lvl_sel_type_label = tk.Label(self.higher_lvl_frame, text="Sel. type:")
        higher_lvl_sel_type_label.grid(row=2, column=1, sticky="w")
        higher_lvl_sel_val_label = tk.Label(self.higher_lvl_frame, text="Sel. value:")
        higher_lvl_sel_val_label.grid(row=2, column=2, sticky="w")
        higher_lvl_select_label = tk.Label(self.higher_lvl_frame, text="Select:")
        higher_lvl_select_label.grid(row=2, column=3, sticky="w")
        higher_lvl_attr_entry_label = tk.Label(
            self.higher_lvl_frame, text="Attr. val.:"
        )
        higher_lvl_attr_entry_label.grid(row=2, column=4, sticky="w")
        higher_lvl_sel_get_label = tk.Label(self.higher_lvl_frame, text="Get:")
        higher_lvl_sel_get_label.grid(row=2, column=5, sticky="w")

        # Higher lvl selector name entry
        self.higher_lvl_sel_name = tk.Entry(self.higher_lvl_frame, width=15)
        self.higher_lvl_sel_name.grid(row=3, column=0, sticky="w")
        # Higher lvl selector type combobox
        self.higher_lvl_sel_type = ttk.Combobox(
            self.higher_lvl_frame, width=7, values=["css", "xpath"]
        )
        self.higher_lvl_sel_type.grid(row=3, column=1, sticky="w")
        # Higher lvl selector value entry
        self.higher_lvl_sel_val = tk.Entry(self.higher_lvl_frame, width=20)
        self.higher_lvl_sel_val.grid(row=3, column=2, sticky="w")
        # Higher lvl select type combobox
        self.higher_lvl_select_type_vals = ["text", "attr"]
        self.higher_lvl_select_type = ttk.Combobox(
            self.higher_lvl_frame,
            width=6,
            values=self.higher_lvl_select_type_vals,
            state="readonly",
        )
        self.higher_lvl_select_type.set(self.higher_lvl_select_type_vals[0])
        self.higher_lvl_select_type.grid(row=3, column=3, sticky="w")
        self.higher_lvl_select_type.bind(
            "<<ComboboxSelected>>", self.higher_lvl_select_type_callback, add="+"
        )
        # Higher lvl attr entry
        self.higher_lvl_attr_entry = tk.Entry(self.higher_lvl_frame, width=7)
        self.higher_lvl_attr_entry.insert(0, "None")
        self.higher_lvl_attr_entry.configure(state="disabled")
        self.higher_lvl_attr_entry.grid(row=3, column=4, sticky="w")
        # Higher lvl get type values combobox
        self.higher_lvl_get_type_vals = ["get()", "getall()"]
        self.higher_lvl_get_type = ttk.Combobox(
            self.higher_lvl_frame,
            width=6,
            values=self.higher_lvl_get_type_vals,
            state="readonly",
        )
        self.higher_lvl_get_type.set(self.higher_lvl_get_type_vals[0])
        self.higher_lvl_get_type.grid(row=3, column=5, sticky="w")

        # Lower lvl frame title and separator
        self.lower_lvl_frame_title = tk.Label(
            self.lower_lvl_frame, text="Lower lvl. selectors:"
        )
        self.lower_lvl_frame_title.grid(row=0, column=0, columnspan=6)
        self.lower_lvl_frame_sep = ttk.Separator(
            self.lower_lvl_frame, orient=tk.HORIZONTAL
        )
        self.lower_lvl_frame_sep.grid(row=1, column=0, columnspan=6, sticky="ew")

        # Lower lvl frame add button
        self.lower_lvl_frame_add_btn = tk.Button(
            self.lower_lvl_frame, text="+", bd=0, command=self.ins_lower_lvl_sel_line
        )
        self.lower_lvl_frame_add_btn.grid(row=100, column=0, columnspan=7)

        # Change button text and entry values depending on whether the class
        # is used for inserting new value or editing existing value
        if self.edit:
            btn_text = "Update"
            btn_cmd = self.upd_sels
            self.higher_lvl_sel_name.insert(
                tk.END, self.sels_box.item(self.selected_item_id)["text"]
            )
            self.higher_lvl_sel_type.set(self.selected_item_vals[0])
            self.higher_lvl_sel_val.insert(tk.END, self.selected_item_vals[1])
            self.higher_lvl_select_type.set(self.selected_item_vals[2])

            if self.selected_item_vals[2] == self.higher_lvl_select_type_vals[1]:
                self.higher_lvl_attr_entry.configure(state="normal")
                self.higher_lvl_attr_entry.delete(0, tk.END)
                self.higher_lvl_attr_entry.insert(tk.END, self.selected_item_vals[3])

            self.higher_lvl_get_type.set(
                self.sels_box.item(self.selected_item_id)["values"][-1]
            )
            # Set-up existing lower lvl selector lines
            self.set_lower_lvl_sel_lines()
        else:
            btn_text = "Insert"
            btn_cmd = self.ins_sel

        # Insert button
        ins_btn = tk.Button(self.ctrls_frame, text=btn_text, command=btn_cmd)
        ins_btn.grid(row=2, column=0)

    # Callback for higher lvl select type to configure (enable/disable) appropriate attr widget
    def higher_lvl_select_type_callback(self, event):
        selected_higher_lvl_select_type = self.higher_lvl_select_type.get()
        if selected_higher_lvl_select_type == self.higher_lvl_select_type_vals[1]:
            self.higher_lvl_attr_entry.configure(state="normal")
            self.higher_lvl_attr_entry.delete(0, tk.END)
        else:
            self.higher_lvl_attr_entry.delete(0, tk.END)
            self.higher_lvl_attr_entry.insert(0, "None")
            self.higher_lvl_attr_entry.configure(state="disabled")

    # Callback for lower lvl select type to configure (enable/disable) appropriate attr widget
    def lower_lvl_select_type_callback(self, event):
        selected_lower_lvl_select_type = event.widget.get()
        selected_lower_lvl_attr = self.lower_lvl_selects[event.widget]
        if selected_lower_lvl_select_type == self.higher_lvl_select_type_vals[1]:
            selected_lower_lvl_attr.configure(state="normal")
            selected_lower_lvl_attr.delete(0, tk.END)
        else:
            selected_lower_lvl_attr.delete(0, tk.END)
            selected_lower_lvl_attr.insert(0, "None")
            selected_lower_lvl_attr.configure(state="disabled")

    # Set lower lvl selector lines of selected widget (higher lvl selector)
    # Used when editing existing selector
    def set_lower_lvl_sel_lines(self):
        # Get all child
        child = self.sels_box.get_children(self.selected_item_id)
        # Iterate over child
        for i in child:
            text = self.sels_box.item(i)["text"]
            values = self.sels_box.item(i)["values"]
            # Insert empty lower lvl selector line
            self.ins_lower_lvl_sel_line()
            # Set up values for every widget of empty lower lvl selector line
            self.lower_lvl_sel_name.insert(0, text)
            self.lower_lvl_sel_type.set(values[0])
            self.lower_lvl_sel_val.insert(0, values[1])
            self.lower_lvl_select_type.set(values[2])
            self.set_attr_state(values[2], values[3])
            self.lower_elem_get_type_combobox.set(values[-1])

    def set_attr_state(self, sel_type, val):
        if sel_type == self.higher_lvl_select_type_vals[1]:
            self.lower_lvl_attr_entry.configure(state="normal")
            self.lower_lvl_attr_entry.delete(0, tk.END)
            self.lower_lvl_attr_entry.insert(tk.END, val)

    # Get and return higher lvl selectors
    def get_higher_lvl_sel(self):
        sel_name = self.higher_lvl_sel_name.get()
        sel_type = self.higher_lvl_sel_type.get()
        sel_val = self.higher_lvl_sel_val.get()
        select_val = self.higher_lvl_select_type.get()
        attr_val = self.higher_lvl_attr_entry.get()
        get_type = self.higher_lvl_get_type.get()
        return sel_name, sel_type, sel_val, select_val, attr_val, get_type

    # Get and return lower lvl selectors
    def get_lower_lvl_sels(self):
        all_sels = []
        for widget in self.lower_lvl_selectors:
            if widget:
                elem_title = widget[0].get()
                elem_type = widget[1].get()
                elem_val = widget[2].get()
                elem_select = widget[3].get()
                attr_val = widget[4].get()
                elem_get_type = widget[5].get()
                all_sels.append(
                    [
                        elem_title,
                        elem_type,
                        elem_val,
                        elem_select,
                        attr_val,
                        elem_get_type,
                    ]
                )
        return all_sels

    # Insert (not update/edit) higher lvl selectors and lower lvl selectors
    def ins_sel(self):
        # Insert higher lvl selector to selectors box
        higher_lvl_sel = self.get_higher_lvl_sel()
        higher_lvl_sel_insertion = self.sels_box.insert(
            "",
            1,
            text=higher_lvl_sel[0],
            values=tuple(i for i in higher_lvl_sel[1:]),
        )

        # Insert lower lvl selectors to selectors box
        for lower_lvl_sel in self.lower_lvl_selectors:
            if lower_lvl_sel:
                self.sels_box.insert(
                    higher_lvl_sel_insertion,
                    "end",
                    text=lower_lvl_sel[0].get(),
                    values=tuple(i.get() for i in lower_lvl_sel[1:6]),
                )

        # self.parent.set_max_width(self.sels_box, "#0", 90)

    def ins_lower_lvl_sel_line(self):
        # Current lower lvl selector index
        idx = self.my_idx

        # Lower lvl selector
        self.lower_lvl_sel_name = tk.Entry(self.lower_lvl_frame, width=15)
        self.lower_lvl_sel_name.grid(row=self.row_idx, column=0)
        self.lower_lvl_sel_type = ttk.Combobox(
            self.lower_lvl_frame, width=7, values=["css", "xpath"]
        )
        self.lower_lvl_sel_type.grid(row=self.row_idx, column=1)
        self.lower_lvl_sel_val = tk.Entry(self.lower_lvl_frame, width=20)
        self.lower_lvl_sel_val.grid(row=self.row_idx, column=2)
        self.lower_lvl_select_type = ttk.Combobox(
            self.lower_lvl_frame,
            width=6,
            values=self.higher_lvl_select_type_vals,
            state="readonly",
        )
        self.lower_lvl_select_type.bind(
            "<<ComboboxSelected>>", self.lower_lvl_select_type_callback, add="+"
        )
        self.lower_lvl_select_type.set(self.higher_lvl_select_type_vals[0])
        self.lower_lvl_select_type.grid(row=self.row_idx, column=3, sticky="w")
        self.lower_lvl_attr_entry = tk.Entry(self.lower_lvl_frame, width=7)
        self.lower_lvl_attr_entry.insert(0, "None")
        self.lower_lvl_attr_entry.configure(state="disabled")
        self.lower_lvl_attr_entry.grid(row=self.row_idx, column=4, sticky="w")
        self.lower_elem_get_type_combobox = ttk.Combobox(
            self.lower_lvl_frame,
            width=6,
            values=self.higher_lvl_get_type_vals,
            state="readonly",
        )
        self.lower_elem_get_type_combobox.set(self.higher_lvl_get_type_vals[0])
        self.lower_elem_get_type_combobox.grid(row=self.row_idx, column=5, sticky="w")
        # Delete (-) button
        self.del_btn = tk.Button(
            self.lower_lvl_frame,
            text="‒",
            bd=0,
            command=lambda: self.destroy_lower_lvl_sel_line(idx),
        )
        self.del_btn.grid(row=self.row_idx, column=6)

        # Append inserted (created) lower lvl selector line to all lower lvl selectors
        self.lower_lvl_selectors.append(
            [
                self.lower_lvl_sel_name,
                self.lower_lvl_sel_type,
                self.lower_lvl_sel_val,
                self.lower_lvl_select_type,
                self.lower_lvl_attr_entry,
                self.lower_elem_get_type_combobox,
                self.del_btn,
            ]
        )
        # Tie-up lower_lvl_select_type with lower_lvl_attr_entry by inserting to
        # lower_lvl_selects dictionary. It is necessary for correct lower_lvl_attr_entry
        # enabling/disabling
        self.lower_lvl_selects[self.lower_lvl_select_type] = self.lower_lvl_attr_entry
        # Increment global lower lvl index by 1 after insertion
        self.row_idx += 1
        # Increment local lower lvl index by 1 after insertion
        self.my_idx += 1

    # Destroy lower level selector line by provided index
    def destroy_lower_lvl_sel_line(self, i):
        for widget in self.lower_lvl_selectors[i]:
            widget.destroy()
        self.lower_lvl_selectors[i] = ""

    # Update existing selectors
    def upd_sels(self):
        higher_lvl_sel = self.get_higher_lvl_sel()
        self.sels_box.item(
            self.selected_item_id,
            text=higher_lvl_sel[0],
            values=tuple(i for i in higher_lvl_sel[1:]),
        )
        # Get lower level selectors
        lower_lvl_sels = self.get_lower_lvl_sels()

        child = self.sels_box.get_children(self.selected_item_id)

        for i, lower_lvl_sel in zip_longest(child, lower_lvl_sels):
            if lower_lvl_sel:
                if i:
                    self.sels_box.item(
                        i,
                        text=lower_lvl_sel[0],
                        values=tuple(i for i in lower_lvl_sel[1:]),
                    )
                else:
                    self.sels_box.insert(
                        self.selected_item_id,
                        "end",
                        text=lower_lvl_sel[0],
                        values=tuple(i for i in lower_lvl_sel[1:]),
                    )
            else:
                self.sels_box.delete(i)
        self.parent.set_max_width(self.sels_box, "two", 180)


class Main(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.parent = parent
        self.create_widgets()

    def create_widgets(self):
        # Left side frame
        self.l_side_frame = tk.Frame(self)
        self.l_side_frame.grid(row=0, column=0, padx=5, pady=10, sticky="nsew")
        # Right side frame
        self.r_side_frame = tk.Frame(self)
        self.r_side_frame.grid(row=0, column=1, padx=5, pady=10, sticky="nsew")
        # Project name box
        self.project_box_frame = tk.Frame(self.l_side_frame)
        self.project_box_frame.grid(row=0, column=0, sticky="ew")
        # Horizontal separator
        h_sep_0 = ttk.Separator(self.l_side_frame, orient=tk.HORIZONTAL)
        h_sep_0.grid(row=1, column=0, pady=10, sticky="ew")
        # Urls box frame
        self.links_box_frame = tk.Frame(self.l_side_frame)
        self.links_box_frame.grid(row=2, column=0, sticky="ew")
        # Horizontal separator
        h_sep_1 = ttk.Separator(self.l_side_frame, orient=tk.HORIZONTAL)
        h_sep_1.grid(row=3, column=0, pady=10, sticky="ew")
        # Elems box frame
        self.sels_box_frame = tk.Frame(self.l_side_frame)
        self.sels_box_frame.grid(row=4, column=0, sticky="ew")
        # Horizontal separator
        h_sep_2 = ttk.Separator(self.l_side_frame, orient=tk.HORIZONTAL)
        h_sep_2.grid(row=5, column=0, pady=10, sticky="ew")
        # Output frame
        self.output_frame = tk.Frame(self.l_side_frame)
        self.output_frame.grid(row=6, column=0, sticky="ew")
        # Horizontal separator
        h_sep_3 = ttk.Separator(self.l_side_frame, orient=tk.HORIZONTAL)
        h_sep_3.grid(row=7, column=0, pady=10, sticky="ew")
        # Controls (start, pause) frame
        self.controls_frame = tk.Frame(self.l_side_frame)
        self.controls_frame.grid(row=8, column=0)
        # Vertical separator
        v_sep = ttk.Separator(self, orient=tk.VERTICAL)
        v_sep.grid(row=0, column=0, rowspan=7, pady=5, sticky="nse")

        # Project name section
        project_name_label = tk.Label(self.project_box_frame, text="Project name:")
        project_name_label.grid(row=0, column=0, sticky="w")

        default_project_name = "new_project"
        self.project_name_entry = tk.Entry(self.project_box_frame)
        self.project_name_entry.insert(0, default_project_name)
        self.project_name_entry.grid(row=0, column=1, sticky="w")

        self.checkbutton_var = tk.IntVar()
        self.overwrite_checkbutton = tk.Checkbutton(
            self.project_box_frame,
            text="Overwrite existing project?",
            variable=self.checkbutton_var,
        )
        self.overwrite_checkbutton.grid(row=1, column=0, columnspan=2, sticky="w")
        # Urls box section
        links_label = tk.Label(self.links_box_frame, text="Links to scrape:")
        links_label.grid(row=0, column=0, columnspan=4, sticky="w")
        links_box_cols = ("F:", "Link:")
        self.links_box = ttk.Treeview(
            self.links_box_frame,
            columns=links_box_cols,
            height=5,
            show="headings",
        )
        self.links_box.column("F:", width=20, anchor="w", stretch=True)
        self.links_box.column("Link:", width=300, anchor="w", stretch=True)
        for col in links_box_cols:
            self.links_box.heading(col, text=col, anchor="w")
        self.links_box.grid(row=1, column=0, columnspan=4, sticky="w")

        # Horizontal scrollbar for urls box
        links_box_x_scroll = ttk.Scrollbar(self.links_box_frame, orient="horizontal")
        links_box_x_scroll.configure(command=self.links_box.xview)
        self.links_box.configure(xscrollcommand=links_box_x_scroll.set)
        links_box_x_scroll.grid(row=2, column=0, columnspan=4, sticky="nsew")

        # Urls box buttons
        links_box_insert_btn = tk.Button(
            self.links_box_frame,
            text="Insert",
            command=lambda: [self.insert_url(), self.get_urls()],
        )
        links_box_insert_btn.grid(row=3, column=0, sticky="nsew")
        links_box_delete_btn = tk.Button(
            self.links_box_frame,
            text="Delete",
            command=lambda: self.delete_item(self.links_box),
        )
        links_box_delete_btn.grid(row=3, column=1, sticky="nsew")
        links_box_upload_btn = tk.Button(
            self.links_box_frame, text="Upload", command=self.upload_urls
        )
        links_box_upload_btn.grid(row=3, column=2, sticky="nsew")
        self.links_box_follow_btn = tk.Button(
            self.links_box_frame,
            text="Follow",
            width=1,
            state="disabled",
            command=self.insert_follow_css,
        )
        self.links_box_follow_btn.grid(row=3, column=3, sticky="nsew")

        # Change state of F button when urls box element is selected
        self.links_box.bind(
            "<ButtonRelease-1>", lambda event: self.change_btns_state(self.links_box)
        )

        # Elements selection box
        elems_label = tk.Label(self.sels_box_frame, text="Elements to select:")
        elems_label.grid(row=0, column=0, columnspan=5, sticky="w")

        self.sels_box = ttk.Treeview(self.sels_box_frame)
        sels_box_cols = ("Name:", "Type:", "Selector:")
        self.sels_box["columns"] = ("one", "two")
        self.sels_box.column("#0", width=90, minwidth=90, anchor="w", stretch=True)
        self.sels_box.column("one", width=50, minwidth=50, anchor="w", stretch=True)
        self.sels_box.column("two", width=180, anchor="w", stretch=True)
        cols_id = ["#0", "one", "two"]
        for col, col_id in zip(sels_box_cols, cols_id):
            self.sels_box.heading(col_id, text=col, anchor="w")
        self.sels_box.grid(row=1, column=0, columnspan=5, sticky="w")

        # Horizontal scrollbar for elems box
        sels_box_x_scroll = ttk.Scrollbar(self.sels_box_frame, orient="horizontal")
        sels_box_x_scroll.configure(command=self.sels_box.xview)
        self.sels_box.configure(xscrollcommand=sels_box_x_scroll.set)
        sels_box_x_scroll.grid(row=2, column=0, columnspan=5, sticky="nsew")

        # Elements selection box buttons
        sels_box_insert_btn = tk.Button(
            self.sels_box_frame, text="Insert", command=self.insert_elem
        )
        sels_box_insert_btn.grid(row=3, column=0, sticky="nsew")

        self.sels_box_del_btn = tk.Button(
            self.sels_box_frame,
            text="Delete",
            command=lambda: self.delete_item(self.sels_box),
        )
        self.sels_box_del_btn.grid(row=3, column=1, sticky="nsew")

        self.sels_box_edit_btn = tk.Button(
            self.sels_box_frame,
            text="Edit",
            state="disabled",
            command=lambda: self.insert_elem(edit=True),
        )
        self.sels_box_edit_btn.grid(row=3, column=2, sticky="nsew")

        self.sels_box_up_btn = tk.Button(
            self.sels_box_frame,
            width=1,
            text="↑",
            state="disabled",
            command=lambda: self.move_to("up"),
        )
        self.sels_box_up_btn.grid(row=3, column=3, sticky="nsew")

        self.sels_box_down_btn = tk.Button(
            self.sels_box_frame,
            width=1,
            text="↓",
            state="disabled",
            command=lambda: self.move_to("down"),
        )
        self.sels_box_down_btn.grid(row=3, column=4, sticky="nsew")

        # Change state of Edit, Up, Down buttons when urls box element is selected
        self.sels_box.bind(
            "<ButtonRelease-1>", lambda event: self.change_btns_state(self.sels_box)
        )

        # Output (saving) section
        saving_format_label = tk.Label(self.output_frame, text="Saving format: ")
        saving_format_label.grid(row=0, column=0, sticky="w")
        saving_values = [".json", ".csv"]
        self.saving_format_combobox = ttk.Combobox(
            self.output_frame, width=7, values=saving_values, state="readonly"
        )
        self.saving_format_combobox.set(saving_values[0])
        self.saving_format_combobox.grid(row=0, column=1, sticky="w")
        saving_dir_label = tk.Label(self.output_frame, text="Saving dir.: ")
        saving_dir_label.grid(row=1, column=0, sticky="w")
        self.chosen_s_dir = tk.StringVar()
        saving_dir_entry = tk.Entry(
            self.output_frame, textvariable=self.chosen_s_dir, width=14
        )
        saving_dir_entry.grid(row=1, column=1)

        # Filedialog for choosing saving directory
        def select_dir():
            dir_selection = tk.filedialog.askdirectory()
            self.chosen_s_dir.set(dir_selection)

        # Output (saving) section buttons
        select_dir_button = tk.Button(
            self.output_frame, text="Select dir.", command=select_dir
        )
        select_dir_button.grid(row=1, column=2, padx=5)

        # Controls (Start, Pause) section buttons
        start_button = tk.Button(
            self.controls_frame, text="START", command=self.start_scraping
        )
        start_button.grid(row=0, column=0)
        pause_button = tk.Button(self.controls_frame, text="Pause", command=None)
        pause_button.grid(row=0, column=1)

        # Logging box section
        logging_box_label = tk.Label(self.r_side_frame, text="Logging:")
        logging_box_label.pack()
        logging_box_frame = tk.Frame(self.r_side_frame)
        logging_box_frame.pack(fill="both", expand=True)
        self.logging_box = tk.Listbox(logging_box_frame, width=30)

        logging_box_scroll = ttk.Scrollbar(logging_box_frame, orient="vertical")
        logging_box_scroll.configure(command=self.logging_box.yview)
        logging_box_scroll.pack(side="right", fill="y")
        self.logging_box.pack(fill="both", expand=True)
        self.logging_box.configure(yscrollcommand=logging_box_scroll.set)

        clear_logging_button = tk.Button(
            self.r_side_frame,
            text="Clear",
            command=self.clear_logging_box,
        )
        clear_logging_button.pack()
        export_logging_button = tk.Button(
            self.r_side_frame, text="Export logging", command=self.get_urls
        )
        export_logging_button.pack()

    def start_scraping(self):
        name = self.project_name_entry.get()
        project_name = self.set_project_name()
        urls = self.get_urls()
        elems = self.get_higher_lvl_sel()
        follow_sels = self.get_follow_sels()
        saving_format = self.saving_format_combobox.get()
        saving_dir = self.chosen_s_dir.get()

        generator = codeGenerator(project_name)
        generator.set_name(generator.spider_fp, "#_name", name)
        generator.set_urls(generator.spider_fp, "#_urls", urls)
        generator.set_elems(generator.spider_fp, "#_parsing", elems)
        generator.set_following(generator.spider_fp, "#_next", follow_sels)
        t = threading.Thread(
            target=generator.start_crawling,
            args=(name, saving_format, saving_dir, self.logging_box),
        )
        t.daemon
        t.start()

    def set_project_name(self):
        project_name = self.project_name_entry.get()
        checkbutton_state = self.checkbutton_var.get()

        if not checkbutton_state:
            all_dirs = next(os.walk(os.getcwd()))[1]
            if project_name in all_dirs:
                for i in range(100):
                    new_project_name = project_name + "_" + str(i)
                    if not new_project_name in all_dirs:
                        return new_project_name
        else:
            return project_name

    def get_urls(self):
        all_urls = []
        for line in self.links_box.get_children():
            all_urls.append(self.links_box.item(line)["values"][-1])
        return all_urls

    def get_follow_sels(self):
        all_sels = []
        for line in self.links_box.get_children():
            all_sels.append(self.links_box.item(line)["values"][0])
        all_sels = [i for i in all_sels if i]
        return all_sels

    def get_higher_lvl_sel(self):
        all_elems = []
        for top_line in self.sels_box.get_children():
            top_line_children = self.sels_box.get_children(top_line)
            top_line_list = []
            sel_type = self.sels_box.item(top_line)["text"]
            top_line_list.append(sel_type)
            for value in self.sels_box.item(top_line)["values"]:
                top_line_list.append(value)
            if top_line_children:
                mid_lines_list = []
                for mid_line in top_line_children:
                    mid_line_list = []
                    child_sel_type = self.sels_box.item(mid_line)["text"]
                    mid_line_list.append(child_sel_type)
                    for value in self.sels_box.item(mid_line)["values"]:
                        mid_line_list.append(value)
                    mid_lines_list.append(mid_line_list)
                top_line_list.append(mid_lines_list)
            all_elems.append(top_line_list)
        return all_elems

    # Insert url to url box by calling insertUrlWin class
    def insert_url(self):
        insertLinkWin(self)

    # Insert CSS selection to url box by calling followUrlWin class
    def insert_follow_css(self):
        followLinkWin(self)

    # Delete selected items for sepcified box (urls box/elems box)
    def delete_item(self, box):
        selected_items = box.selection()
        for selected_item in selected_items:
            box.delete(selected_item)

        # Change (disable) buttons state after deleting selected items
        self.change_btns_state(box)

        # Set a proper width of box columns
        if box == self.links_box:
            self.set_max_width(self.links_box, "Link:", 300)
        elif box == self.sels_box:
            self.set_max_width(self.sels_box, "Value:", 180)

    # Upload urls to urls box
    def upload_urls(self):
        filename = filedialog.askopenfilename(
            initialdir="/", title="Select file", filetypes=[("All files", "*")]
        )
        if not filename:
            return

        with open(filename) as f:
            urls = f.readlines()
            # max_width = max([self.set_max_width(url) for url in urls])
            for url in urls:
                self.links_box.insert("", "end", values=("", url))

        self.set_max_width(self.links_box, "Link:", 300)

    # Set max width of box by iterating over every box item
    def set_max_width(self, box, col, default_width):
        default_font = tkfont.nametofont("TkDefaultFont")

        all_vals = []
        for child in box.get_children():
            for x in box.item(child)["values"]:
                all_vals.append(x)

            lower_child = box.get_children(child)
            for i in lower_child:
                values = box.item(i)["values"]
                sel_val = values[1]
                all_vals.append(sel_val)

        try:
            max_width = max([default_font.measure(x) for x in all_vals]) + 10
        except ValueError:
            max_width = default_width

        box.column(
            col, width=default_width, minwidth=max_width, anchor="w", stretch=True
        )

    # Insert XPATH/CSS element to elem box by calling insertElemSelectionWin class
    def insert_elem(self, edit=None):
        insertElemSelectionWin(self, self.sels_box, edit)

    # Change the state of urls/elems box buttons
    def change_btns_state(self, box):
        if box == self.sels_box:
            btns_to_disable = [
                self.sels_box_edit_btn,
                self.sels_box_up_btn,
                self.sels_box_down_btn,
            ]
        elif box == self.links_box:
            btns_to_disable = [self.links_box_follow_btn]

        if not box.selection():
            for btn in btns_to_disable:
                btn["state"] = "disabled"
        else:
            for btn in btns_to_disable:
                btn["state"] = "normal"

    # Move elems box item up/down
    def move_to(self, direction=None):
        selected_items = self.sels_box.selection()
        if direction == "up":
            movement = -1
        elif direction == "down":
            movement = 1

        for selected_item in selected_items:
            self.sels_box.move(
                selected_item,
                self.sels_box.parent(selected_item),
                self.sels_box.index(selected_item) + movement,
            )

    def get_saving_dir(self):
        chosen_dir = self.chosen_s_dir.get()
        if chosen_dir:
            return chosen_dir
        else:
            pass

    def clear_logging_box(self):
        self.logging_box.delete(0, tk.END)


class MainApplication(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.main = Main(self)
        self.menu_bar = menuBar(self)
        tk.Tk.config(parent, menu=self.menu_bar)

        self.main.pack(side="right", fill="both", expand=True)
        self.main.grid_rowconfigure(0, weight=1)
        self.main.grid_columnconfigure(1, weight=1)


root = tk.Tk()
if __name__ == "__main__":
    root.title("Easy Scraper")
    MainApplication(root).pack(side="top", fill="both", expand=True)
    root.mainloop()
