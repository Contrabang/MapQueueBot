import json
import matplotlib.pyplot as plt
import networkx as nx
import os
import pprint
import requests
import textwrap
import webbrowser

from dataclasses import dataclass, field
from enum import Enum

import color_handling

@dataclass
class MapQueueConfig:
    pulls_location: str = 'https://github.com/ParadiseSS13/Paradise/pull/'
    api_link: str = 'https://api.github.com/repos/ParadiseSS13/Paradise/'
    max_page_load: str = 10
    open_amount: int = 100
    config_maps: list = field(default_factory=lambda: [STATIONS.Box, STATIONS.Delta, STATIONS.Meta, STATIONS.Farragus])

    getting_file: str = './data/data.json'
    cache_file: str = './data/cache.json'
    viewing_json: str = './data/viewing_map.json'
    queue_json: str = './data/queues.json'
    readable_queue_json: str = './data/queued_names.json'

    map_output_file: str = './output/mapqueue.jpeg'


    # has no type indicator so it does not show up in the config data
    help_text = """
help (h) - prints out all available commands
quit (q) - quit the program
config (c) - view the config file
fetch (f) - fetch data from the github
isolate (i) - isolate the cache
terminal (t) - print cache to terminal
graph (g) - turn cache into Map Queue Graph
run (r) - runs the fetch, isolate, then graph functions
open PR (o) - open a PR number in browser (e.g. open 20000)
wuh woh (w) - organizes the queues.json into something human-readable
"""

class MQ_STATUS(str, Enum):
    SKIPPED = 'skipped'
    WAITING = 'awaiting'
    LEADER = 'leader'

class STATIONS(str, Enum):
    Box = 'BoxStation'
    Delta = 'DeltaStation'
    Meta = 'MetaStation'
    Farragus = 'CereStation'

class MapQueueBot:

    def __init__(self, config: MapQueueConfig) -> None:
        if not os.path.exists("./data/"):
            os.makedirs("./data/")
        if not os.path.exists("./output/"):
            os.makedirs("./output/")
        self.config = config
        self.main_loop()

    def main_loop(self):
        while(True):
            list_of_inputs = input("Enter prompt (use help):").lower().split()
            match list_of_inputs[0][0]:
                case "h":
                    print(self.config.help_text)

                case "q":
                    quit()
                    
                case "c":
                    print()
                    pprint.pprint(self.config, width=200)
                    print()
                    
                case "f":
                    self.get_git()

                case "i":
                    self.isolate_maps()

                case "t":
                    self.print_to_terminal()

                case "g":
                    self.make_graph()

                case "r":
                    self.get_git()
                    self.isolate_maps()
                    self.make_graph()
                    print("Graph created.")

                case "o":
                    if(len(list_of_inputs) == 1):
                        print("Enter a PR number first!")
                        continue

                    
                    self.open_pr(int(list_of_inputs[1]))

                case "w":
                    self.queues_to_queuenames()




    def get_git(self):
        basic_link = self.config.api_link + 'pulls?state=open&per_page=' + str(self.config.open_amount) + '&direction=asc'

        relay = requests.get(basic_link)

        data = []
        if(relay.links["next"]):
            word = input("Multiple pages detected, would you like to download more? (y/n):")
            if word[0].lower() == "y":
                counter = 2
                while("next" in relay.links and counter < self.config.max_page_load):
                    print(relay, ", STATUS: ", relay.reason, sep="")
                    if(relay.status_code != 200):
                        print("REQUEST FAILED:", relay.status_code, relay.reason)
                        break
                    data.extend(json.loads(relay.content.decode("utf-8")))
                    print(counter, ". Fetching: ", relay.links["next"]["url"], sep="")
                    relay = requests.get(relay.links["next"]["url"])
                    
                    if("next" in relay.links):
                        print(relay.links["next"])
                        print(relay.links["last"])
                    else:
                        print("reached end of pages")
                        break
                    counter += 1
                print("fetched", counter, "pages")
        
        print(relay, ", STATUS: ", relay.reason, sep="")
        if(relay.status_code != 200):
            print("REQUEST FAILED:", relay.status_code, relay.reason)

        data.extend(json.loads(relay.content.decode("utf-8")))
        
        if(len(data) == 0):
            print("no pull requests recieved.")
            return

        print("saving", len(data), "pull requests")
        with open(self.config.getting_file, 'w') as f:
            f.write(json.dumps(data, indent=4))

    def isolate_maps(self):
        with open(self.config.getting_file, 'r') as f:
            data = json.load(f)

        map_pulls = []

        for pull in data:
            for label in pull["labels"]: 
                if(label["name"] == "Map Edit"):
                    map_pulls.append(pull)

        print("isolated maps (", len(data), " -> ", len(map_pulls), ")", sep="")

        with open(self.config.cache_file, 'w') as f:
            f.write(json.dumps(map_pulls, indent=4))

    def print_to_terminal(self):
        maps = self.config.config_maps.copy()

        default_line_len = 4 + len(maps)

        with open(self.config.cache_file, 'r') as f:
            map_pulls = json.load(f)

        for pull in map_pulls:
            labels = ""
            for label in pull["labels"]: 
                if(label["name"] in maps):
                    labels += label["name"][0]
            intermediary = " (" + str(labels) + ") "
            intermediary = intermediary.ljust(default_line_len)
            if(pull["draft"]):
                intermediary += "*D*"
            intermediary = intermediary.ljust(default_line_len + 3)
            print(pull["number"], intermediary, ": ", pull["title"], sep="")
        
        print("total mapping PRs:", len(map_pulls))

    def make_graph(self):
        maps = self.config.config_maps.copy()
        queues = {}
        for title in maps:
            queues[title] = {}
        queues["Multistation"] = {}
        data = {"items": [], "categories": ["General"] + list(queues.keys())}

        general_queue = {}

        with open(self.config.cache_file, 'r') as f:
            map_pulls = json.load(f)

        index = 0
        for pull in map_pulls:
            new_json = {key:pull[key] for key in ['title', 'number', 'draft']}
            new_json["mql"] = MQ_STATUS.WAITING
            new_json["index"] = index
            index += 1
            new_json["height"] = 0
            new_json["column"] = None
            new_json["is_multi"] = False
            new_json["color"] = "#3cbd55" #green
            new_json["paths"] = []
            if(new_json["draft"]):
                new_json["color"] = "#808080" # gray
            for label in pull["labels"]:
                if("[MQL]" in label["name"]):
                    if("[MQL] --SKIP--" == label["name"]):
                        new_json["mql"] = MQ_STATUS.SKIPPED
                        new_json["color"] = "#db3632" # red
                    else:
                        new_json["mql"] = MQ_STATUS.LEADER
                        new_json["color"] = "#d6bc2d"
                if(label["name"] in maps):
                    if(new_json["column"] == None):
                        new_json["column"] = label["name"]
                    else:
                        if(not new_json["is_multi"]):
                            # First time multistation setting
                            if(len(queues["Multistation"])):
                                new_json["height"] = max(new_json["height"], queues["Multistation"][max(queues["Multistation"], key=int)] + 1) # Make sure its always after the latest multistation one too!
                        new_json["column"] = "Multistation"
                        new_json["is_multi"] = True
                    if(len(queues[label["name"]])):
                        new_json["height"] = max(new_json["height"], queues[label["name"]][max(queues[label["name"]], key=int)] + 1) # latest element
                        previous = str(max(queues[label["name"]], key=int))
                        if(not (previous in new_json["paths"])):
                            new_json["paths"].append(previous)
                        
                    else: # default case
                        new_json["height"] = 1

                    queues[label["name"]][str(new_json["index"])] = new_json["height"]

            if(new_json["is_multi"]):
                queues["Multistation"][str(new_json["index"])] = new_json["height"]
                for key in queues:
                    queue = queues[key]
                    if(str(new_json["index"]) in queue):
                        queue[str(new_json["index"])] = new_json["height"]

            if(new_json["draft"] and new_json["color"] != "#808080"):
                new_json["color"] = color_handling.blend_hex_colors(new_json["color"], "#808080") # mix it with gray

            if(new_json["column"] == None):
                general_queue[new_json["index"]] = new_json
                new_json["height"] = len(general_queue)
                new_json["column"] = "General"

            data["items"].append(new_json)

        with open(self.config.viewing_json, 'w') as f:
            f.write(json.dumps(data, indent=4))

        with open(self.config.queue_json, 'w') as f:
            f.write(json.dumps(queues, indent=4))
        
        G = nx.DiGraph()

        total_nodes = len(data["items"]) + len(data["categories"]) - 1

        facecolor = ["skyblue"] * total_nodes

        nodes = [*range(total_nodes)]
        G.add_nodes_from(nodes)

        edges = set()
        labels = {}
        locations = {}
        drafts = {}

        count = 0
        for pull in data["items"]:
            labels[count] = textwrap.fill(pull["title"], 20)
            locations[count] = (data["categories"].index(pull["column"]), -pull["height"])
            for parent in pull["paths"]:
                edges.add((count, int(parent)))
            facecolor[count] = pull["color"]
            count += 1

        temp = len(locations)
        map_number = 0
        for place in data["categories"]:
            locations[temp] = (map_number, 0)
            labels[temp] = place
            map_number += 1
            temp += 1
                

        G.add_edges_from(edges)

        plt.rcParams['figure.figsize'] = [20, 30]

        # nx.draw_networkx(G, pos = locations, labels = labels, 
        #                  bbox = dict(facecolor = "skyblue",
        #                  boxstyle = "round", ec = "silver", pad = 0.3),
        #                  edge_color = "gray"
        #                 )
        nx.draw_networkx(G, pos = locations, labels = labels, arrows = True,
                        node_shape = "s", node_size = 2000,
                        node_color = facecolor,
                        edge_color = "gray",  #color of the edges
                        edgecolors = "gray")

        nx.draw_networkx_edge_labels(G, pos = locations,
                                    edge_labels=drafts,
                                    font_color='black')

        plt.title("Map Queue")
        plt.savefig(self.config.map_output_file, dpi = 80)
        plt.close()

    
    def open_pr(self, pr_num):
        if(pr_num is None):
            print("No PR number was given")
            return
        destination = self.config.pulls_location + str(pr_num)
        print("directing to", destination)
        webbrowser.open(destination, new=2)

    def queues_to_queuenames(self):
        with open(self.config.viewing_json, 'r') as f:
            data = json.load(f)

        oh_my_god_bruh = {}
        for pull in data["items"]:
            oh_my_god_bruh[str(pull["index"])] = {"title": pull["title"], "number": pull["number"]}

        with open(self.config.queue_json, 'r') as f:
            order = json.load(f)

        new_order = {}
        for station_name in order:
            new_order[station_name] = {}
            for index in order[station_name]:
                new_order[station_name][oh_my_god_bruh[index]["number"]] = oh_my_god_bruh[index]["title"]
            
        with open(self.config.readable_queue_json, 'w') as f:
            f.write(json.dumps(new_order, indent=4))
        

if __name__ == "__main__":
    MapQueueBot(MapQueueConfig())
