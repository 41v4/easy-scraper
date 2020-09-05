import logging
import os
import shlex
import subprocess
import threading
import tkinter as tk
from subprocess import PIPE, STDOUT, Popen


class codeGenerator:
    def __init__(self, project_name):
        self.project_name = project_name
        self.create_project()
        self.create_spider()
        self.spider_fp = (
            f"{self.project_name}/{self.project_name}/spiders/auto_generated_spider.py"
        )

    def create_project(self):
        subprocess.run(
            ["scrapy", "startproject", self.project_name], stdout=PIPE, stderr=PIPE
        )

    def create_spider(self):
        if os.path.isdir(f"./{self.project_name}"):
            subprocess.run(
                f"cp default_spider.py {self.project_name}/{self.project_name}/spiders/",
                shell=True,
            )
            subprocess.run(
                f"mv {self.project_name}/{self.project_name}/spiders/default_spider.py {self.project_name}/{self.project_name}/spiders/auto_generated_spider.py",
                shell=True,
            )
        else:
            raise ValueError(
                f"Can't create a spider, because {self.project_name} not exists!"
            )

    def set_name(self, fp, var_title, var_val):
        with open(fp, "r+") as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                if line.strip() == var_title:
                    lines[i] = f'\tname = "{var_val}"\n'
            f.seek(0)
            f.writelines(lines)

    def set_urls(self, fp, var_title, urls):
        with open(fp, "r+") as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                if line.strip() == var_title:
                    del lines[i]
                    for single_url in urls[::-1]:
                        lines.insert(i, f'\t"{single_url}",\n')
            f.seek(0)
            f.writelines(lines)

    def set_elems(self, fp, var_title, elems):
        self.c_l = None

        def set_select_val(sel_type, select_val, attr_val):
            if sel_type.lower() == "css":
                if select_val.lower() == "text":
                    return "::text"
                else:
                    return f"::attr({attr_val})"
            elif sel_type.lower() == "xpath":
                if select_val.lower() == "text":
                    return "/text()"
                else:
                    return f"/@{attr_val}"
            else:
                print("set_select_val error!")

        def ins_for_line(sel_name, sel_type, sel_val, tabs):
            tabs = tabs * "\t"
            lines.insert(
                self.c_l,
                f"{tabs}for {sel_name} in response.{sel_type}('{sel_val}'):\n",
            )
            self.c_l += 1

        def ins_yield_start(tabs):
            tabs = tabs * "\t"
            n_l = "{\n"
            lines.insert(self.c_l, f"{tabs}yield {n_l}")
            self.c_l += 1

        def ins_yield_end(tabs):
            tabs = tabs * "\t"
            n_l = "}\n"
            lines.insert(self.c_l, f"{tabs}{n_l}")
            self.c_l += 1

        def ins_yield_vals(
            sel_name, sel_type, sel_val, iterator, select_val, get_type, tabs
        ):
            tabs = tabs * "\t"
            lines.insert(
                self.c_l,
                f'{tabs}"{sel_name}": {iterator}.{sel_type}("{sel_val}{select_val}").{get_type},\n',
            )
            self.c_l += 1

        def ins_for_block(elem, sel_name, sel_type, sel_val):
            ins_for_line(sel_name, sel_type, sel_val, 2)
            ins_yield_start(3)
            for lower_sel in elem[-1]:
                select_val = set_select_val(lower_sel[1], lower_sel[3], lower_sel[4])
                ins_yield_vals(
                    lower_sel[0],
                    lower_sel[1],
                    lower_sel[2],
                    single_elem[0],
                    select_val,
                    lower_sel[5],
                    4,
                )
            ins_yield_end(3)

        def ins_yield_block(elems):
            ins_yield_start(2)
            for elem in elems:
                select_val = set_select_val(elem[1], elem[3], elem[4])
                ins_yield_vals(
                    elem[0],
                    elem[1],
                    elem[2],
                    "response",
                    select_val,
                    elem[5],
                    3,
                )
            ins_yield_end(2)

        with open(fp, "r+") as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                if line.strip() == var_title:
                    del lines[i]
                    print(elems)
                    self.c_l = i
                    for single_elem in elems[::-1]:
                        # Determine if the higher lvl selector has lower lvl selectors
                        if len(single_elem) == 7:
                            ins_for_block(
                                single_elem,
                                single_elem[0],
                                single_elem[1],
                                single_elem[2],
                            )
                    type_6_elems = [i for i in elems[::-1] if len(i) == 6]
                    if type_6_elems:
                        ins_yield_block(type_6_elems)

            lines.insert(self.c_l, "\n")
            lines.insert(self.c_l + 1, "#_next")
            f.seek(0)
            f.writelines(lines)

    def set_following(self, fp, var_title, follow_sels):
        def ins_next_page_ln(sel, tabs):
            tabs = tabs * "\t"
            lines.insert(
                self.c_l,
                f"{tabs}next_page = {sel}\n",
            )
            self.c_l += 1

        def ins_if_next_page_ln(tabs):
            tabs = tabs * "\t"
            lines.insert(self.c_l, f"{tabs}if next_page is not None:\n")
            self.c_l += 1

        def ins_yield_ln(tabs):
            tabs = tabs * "\t"
            lines.insert(
                self.c_l,
                f"{tabs}yield response.follow(next_page, callback=self.parse)\n",
            )
            self.c_l += 1

        def ins_following_block(sel):
            ins_next_page_ln(sel, 2)
            ins_if_next_page_ln(2)
            ins_yield_ln(3)

        with open(fp, "r+") as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                if line.strip() == var_title:
                    del lines[i]
                    self.c_l = i
                    print(follow_sels)
                    for single_sel in follow_sels:
                        ins_following_block(single_sel)

            f.seek(0)
            f.writelines(lines)

    def start_crawling(self, name, saving_format, saving_dir, logging_box):
        saving_name = name + "_results"
        saving_fn = os.path.join(saving_dir, saving_name)
        print(saving_fn)
        command = f"cd {self.project_name} && scrapy crawl {name} -o {saving_fn}{saving_format}"
        with Popen(
            command,
            shell=True,
            stdout=PIPE,
            stderr=STDOUT,
            bufsize=1,
            universal_newlines=True,
        ) as p:
            for line in p.stdout:
                if "Scraped from" not in line:
                    logging_box.insert(tk.END, line)
