import json
import sys
import time
import os
"""
Alfred Script Filter generator class
Version: 0.95
"""


class Items:

    def __init__(self):
        self.item = {}
        self.items = []
        self.mods = {}

    def getItemsLengths(self):
        return len(self.items)

    def setKv(self, key, value):
        """
        Set a key value pair to item
        :param key: Name of the Key (str)
        :param value: value (str)
        """
        self.item.update({key: value})

    def addItem(self):
        """
        finally add an item to the items
        """
        self.items.append(self.item)
        self.item = {}
        self.mods = {}

    def setItem(self, **kwargs):
        """
        Add multiple key values to define an item
        :param kwargs: title,subtitle,arg,valid,quicklookurl,uid,automcomplete,type
        """
        for key, value in kwargs.items():
            self.setKv(key, value)

    def getItem(self, d_type=""):
        """
        get current item definition for validation
        :param d_type: defines returned data format; "JSON" if readable
        json is required for debugging purpose
        :return: readable JSON or JSON data
        """
        if d_type == "":
            return self.item
        else:
            return json.dumps(self.item, indent=4)

    def getItems(self, response_type="json"):
        """
        get the final items data for which represents
        the script filter output
        :param response_type: defines returned data format; "json" if readable "dict" for processing data
        json is required for debugging purpose
        :return: readable JSON or JSON data
        """
        valid_keys = {"json", "dict"}
        if response_type not in valid_keys:
            raise ValueError("Type must be in: %s" % valid_keys)
        the_items = {}
        the_items.update({"items": self.items})
        if response_type == "dict":
            return the_items
        elif response_type == "json":
            return json.dumps(the_items, indent=4)

    def setIcon(self, m_path, m_type=""):
        """
        Set the icon of an item
        :param m_path: File path to the icon
        :param m_type: icon,fileicon or png
        """
        self.setKv("icon", self.__define_icon(m_path, m_type))

    def __define_icon(self,path,m_type=""):
        """
        Private method to create icon set
        :param path: str
        :param m_type: str
        :return: icon dict
        """
        icon = {}
        if m_type != "":
            icon.update({"type": m_type})
        icon.update({"path": path})
        return icon

    def addMod(self, key, arg, subtitle, valid=True, icon_path="", icon_type=""):
        """
        add a mod to an item
        :param key: "alt","cmd","shift" (str)
        :param arg: str
        :param subtitle: str
        :param valid: "true" | "false" (str)
        :param icon_path: str
        :param icon_type: str
        """
        valid_keys = {"alt","cmd","shift","ctrl"}
        if key not in valid_keys:
            raise ValueError("Key must be in: %s" % valid_keys)
        mod = {}
        mod.update({"arg":arg})
        mod.update({"subtitle":subtitle})
        mod.update({"valid":valid})
        if icon_path != "":
            the_icon = self.__define_icon(icon_path,icon_type)
            mod.update({"icon":the_icon})
        self.mods.update({key:mod})

    def addModsToItems(self):
        """
        Finally add mods to the items
        """
        self.setKv("mods", self.mods)

    def updateItem(self, id, key, value):
        """
        Update an Alfred script filter item key with a new value
        :param id: int, list index
        :param key: str, key which needs to be updated
        :param value: int or str, new value
        """
        dict_item = self.items[id]
        kv = dict_item[key]
        dict_item[key] = kv + value
        self.items[id] = dict_item

    def write(self, response_type='json'):
        """
        generate Script Filter Output and write back to stdout
        :param response_type: json or dict as output format
        """
        output = self.getItems(response_type=response_type)
        sys.stdout.write(output)


class Tools:

    @staticmethod
    def getEnv(var):
        try:
            return os.getenv(var)
        except:
            pass

    @staticmethod
    def getArgv(i):
        """
        Get argument values from input in Alfred
        :param i: index of argument value int()
        :return: argv str or None
        """
        try:
            return sys.argv[i]
        except IndexError:
            pass

    @staticmethod
    def getDateStr(float_time, format='%d.%m.%Y'):
        """
        Format float time
        :param float_time: float
        :return: formatted date: str()
        """
        time_struct = time.gmtime(float_time)
        return time.strftime(format, time_struct)

    @staticmethod
    def getDateEpoch(float_time):
        return time.strftime('%d.%m.%Y', time.gmtime(float_time/1000))

    @staticmethod
    def sortListDict(list_dict,key,reverse=True):
        """
        Sort List with Dictionary based on given key in Dict
        :param list_dict: list(dict())
        :param key: str()
        :param reverse: bool()
        """
        return sorted(list_dict, key=lambda k: k[key], reverse=reverse)

    @staticmethod
    def sortListTuple(list_tuple, el,reverse=True):
        """
        Sort List with Tubles based on a given element in Tuple
        :param list_tuple: list(tuple())
        :param el: int in tuple
        :param reverse: bool()
        :return:
        """
        return sorted(list_tuple, key=lambda tup: tup[el], reverse=reverse)

    @staticmethod
    def notify(title, text):
        os.system("""
                  osascript -e 'display notification "{}" with title "{}"'
                  """.format(text, title))

