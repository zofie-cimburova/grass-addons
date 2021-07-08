"""!
@package wmsmenu.py

@brief Main python app for handling wms requests for getCapabilities
and getMaps.

Classes:
 - wmsFrame
Functions:
 - DisplayWMSMenu
 
(C) 2006-2011 by the GRASS Development Team
This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.

@author: Maris Nartiss (maris.nartiss gmail.com)
@author Sudeep Singh Walia (Indian Institute of Technology, Kharagpur , sudeep495@gmail.com)
"""

#!/usr/bin/env python

# generated by wxGlade 0.6.3 on Mon Jul 11 04:58:20 2011
import os
import wx
from wxPython.wx import *
from grass.script import core as grass
import imghdr
from wx.lib.pubsub import Publisher
from urllib2 import Request, urlopen, URLError, HTTPError
from parse import *
from WMSMapDisplay import NewImageFrame
from addserver import AddServerFrame
from ServerInfoAPIs import (
    addServerInfo,
    removeServerInfo,
    updateServerInfo,
    initServerInfoBase,
    getAllRows,
)
from LoadConfig import loadConfigFile


class newLayerData:
    """!Data structure to hold relevant details about a fetched layer"""

    name = None
    title = None
    abstract = None
    srsList = None
    queryable = None


class LayerData:
    """!LayerData class to manage LayerTree (Widget used to display fetched layers).
    Includes functionality to add new layers in the LayerTree
    """

    name = None
    title = None
    abstract = None
    srs = None

    def printLayerData(self, layerDataDict):
        """
        @description:Function to print dictionary structure holding information of
                     layers with keys as integers and values as objects of type LayerData()
        @todo:None
        @param1:reference variable
        @param2:Dictionary holding values of type LayerData() object with keys as integers from 0 to len(layerDataDict)
        """
        for key, value in layerDataDict.iteritems():
            print key
            print value.name
            print value.title
            print value.abstract
            srss = value.srs
            for srs in srss:
                a = srs.string
                a = a.split(":")
                print a[0] + " " + a[1]
            print "--------------------------------------------"

    def appendLayerTree(self, layerDataDict, LayerTree, layerTreeRoot):
        """
        @description:Adds layers to LayerTree widget.
        @todo:None
        @param self: reference variable
        @param layerDataDict:{},  Dictionary holding values of type LayerData() object with keys as integers from 0 to len(layerDataDict)
        @param LayerTree: TreeCtrl, widget used to display fetched layers.
        @param layerTreeRoot: TreeItemId,  returned by LayerTree.AddRoot("Layers") (in the init function), used to refer root of the LayerTree.
        @return: None
        """
        for key, value in layerDataDict.iteritems():
            name = value.name
            title = value.title
            abstract = value.abstract
            string = str(key) + "-" + name + ":" + title + ":" + abstract
            LayerTree.AppendItem(layerTreeRoot, string)

    def setKeyToEPSGCodes(self, layerDataDict):
        """
        @description: Builds a dictionary to map keys of layers to EPSG codes
        @todo:None
        @param self: reference variable
        @param layerDataDict:{},  Dictionary holding values of type LayerData() object with keys as integers from 0 to len(layerDataDict)
        @return: Dictionary with key as an integer in the string form str(int), and value a string (EPSG code for the key).
        """
        keytoepsgcodes = {}
        for key, value in layerDataDict.iteritems():
            srss = value.srs
            l = []
            for srs in srss:
                a = srs.string
                a = a.split(":")
                l = l + [a[1]]
            keytoepsgcodes[str(key)] = l
        return keytoepsgcodes


class Message:
    pass


class ManageLayerTree:
    """
    Contains functionalities to Manage TreeCtrl widget (LayerTree) , used to display layers.
    """

    def getAllChild(self, LayerTree, parentId):
        """
        @description:Returns all the children nodes of a parent node in the TreeCtrl (LayerTree).
        @todo:None
        @param self: reference variable
        @param LayerTree: TreeCtrl, widget used to display fetched layers.
        @param parentId: TreeItemId, reference to the parent Node in TreeCtrl.
        @return: a list of TreeItemId, the children nodes of parentId(TreeItemId)
        """
        children = []
        currentchild, obj = LayerTree.GetFirstChild(parentId)
        while 1:
            if not currentchild.IsOk():
                break
            children += [currentchild]
            nextchild = LayerTree.GetNextSibling(currentchild)
            currentchild = nextchild
        return children

    def layerTreeItemDFS(self, parent, LayerTree, nodeId):
        """
        @description: performs a DFS(Depth first search) selection on the LayerTree(TreeCtrl), starting from the nodeId(TreeItemId)
        @todo:None
        @param self: reference variable
        @param LayerTree: TreeCtrl, widget used to display fetched layers.
        @param nodeId: TreeItemId, reference to the parent Node in TreeCtrl.
        @return: None
        """
        if not nodeId.IsOk():
            return

        currentLayerDetails = LayerTree.GetItemText(nodeId)
        print currentLayerDetails
        if not (
            currentLayerDetails == "Layers" and currentLayerDetails.count(":") == 0
        ):
            currentLayerName = (currentLayerDetails.split(":")[0]).split("-")[1]
            print "name = " + currentLayerName
            currentLayerKey = (currentLayerDetails.split(":")[0]).split("-")[0]
            print "key = " + currentLayerKey
            if currentLayerKey not in parent.selectedLayersKeys:
                parent.selectedLayersKeys += [currentLayerKey]
                print "selected layers = "
                print parent.selectedLayersKeys
                print "queryable = "
                print int(parent.layerDataDict1[currentLayerKey].queryable)
                if int(parent.layerDataDict1[currentLayerKey].queryable) == 1:
                    parent.epsgList.Append("<" + currentLayerName + ">")
                    listEPSG = parent.layerDataDict1[currentLayerKey].srsList
                    parent.epsgList.AppendItems(listEPSG)
                    parent.layersString += "," + currentLayerName
                    print "layersString = " + parent.layersString
        # allChild = self.getAllChild(LayerTree, nodeId)
        # for child in allChild:
        #    self.layerTreeItemDFS(parent,LayerTree,child)


class wmsFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        # begin wxGlade: wmsFrame.__init__
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.StatusBar = self.CreateStatusBar(1, 0)
        self.URL = wx.StaticText(self, -1, "URL")
        self.ServerList = wx.ComboBox(
            self, -1, choices=[], style=wx.CB_DROPDOWN | wx.CB_SIMPLE
        )
        self.LayerTree = wx.TreeCtrl(
            self,
            -1,
            style=wx.TR_HAS_BUTTONS
            | wx.TR_NO_LINES
            | wx.TR_MULTIPLE
            | wx.TR_MULTIPLE
            | wx.TR_DEFAULT_STYLE
            | wx.SUNKEN_BORDER,
        )
        self.username = wx.StaticText(self, -1, "UserName")
        self.usernameInput = wx.TextCtrl(self, -1, "", style=wx.TE_PROCESS_TAB)
        self.EPSG = wx.StaticText(self, -1, "EPSG")
        self.password = wx.StaticText(self, -1, "Password")
        self.passwordInput = wx.TextCtrl(
            self, -1, "", style=wx.TE_PROCESS_TAB | wx.TE_PASSWORD
        )
        self.epsgList = wx.ComboBox(
            self, -1, choices=[], style=wx.CB_DROPDOWN | wx.CB_SIMPLE | wx.CB_DROPDOWN
        )
        self.GetCapabilities = wx.Button(self, -1, "GetCapabilities")
        self.GetMaps = wx.Button(self, -1, "GetMaps")
        self.addServer = wx.Button(self, -1, "Manage Servers")

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_TEXT_ENTER, self.OnServerListEnter, self.ServerList)
        self.Bind(wx.EVT_COMBOBOX, self.OnServerList, self.ServerList)
        self.Bind(wx.EVT_COMBOBOX, self.OnEPSGList, self.epsgList)
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnLayerTreeSelChanged, self.LayerTree)
        self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.OnLayerTreeActivated, self.LayerTree)
        self.Bind(wx.EVT_BUTTON, self.OnGetCapabilities, self.GetCapabilities)
        self.Bind(wx.EVT_BUTTON, self.OnGetMaps, self.GetMaps)
        self.Bind(wx.EVT_BUTTON, self.OnAddServer, self.addServer)
        # end wxGlade

        self.usernameInput.Disable()
        self.passwordInput.Disable()
        if not loadConfigFile(self):
            grass.fatal_error("Config File Error, Unable to start application...")
            self.Close()
            return

        self.soup, open = initServerInfoBase("ServersList.xml")
        if not open:
            self.Close()
            return
        self.__populate_Url_List(self.ServerList)
        self.selectedURL = "No server selected"
        self.layerTreeRoot = self.LayerTree.AddRoot("Layers")
        Publisher().subscribe(self.onAddServerFrameClose, ("Add_Server_Frame_Closed"))
        Publisher().subscribe(self.onUpdateServerListmessage, ("update.serverList"))
        Publisher().subscribe(
            self.onUpdateMapListmessage, ("update.map_servernameTouid")
        )

        self.keyToEPSGCodes = {}
        self.Bind(wx.EVT_CLOSE, self.OnQuit)
        self.AddServerisClosed = True
        self.layerName = ""
        self.layerDataDict1 = {}
        self.selectedEPSG = None

    def __set_properties(self):
        # begin wxGlade: wmsFrame.__set_properties
        self.SetTitle("wmsFrame")
        self.StatusBar.SetStatusWidths([-1])
        # statusbar fields
        StatusBar_fields = ["StatusBar"]
        for i in range(len(StatusBar_fields)):
            self.StatusBar.SetStatusText(StatusBar_fields[i], i)
        self.LayerTree.SetMinSize((400, 250))
        self.usernameInput.SetMinSize((189, 27))
        self.passwordInput.SetMinSize((189, 27))
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: wmsFrame.__do_layout
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_4 = wx.BoxSizer(wx.HORIZONTAL)
        grid_sizer_1 = wx.FlexGridSizer(2, 3, 1, 1)
        sizer_3 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_3.Add(self.URL, 0, 0, 0)
        sizer_3.Add(self.ServerList, 0, 0, 0)
        sizer_2.Add(sizer_3, 0, 0, 0)
        sizer_2.Add(self.LayerTree, 1, wx.EXPAND, 0)
        grid_sizer_1.Add(self.username, 0, 0, 0)
        grid_sizer_1.Add(self.usernameInput, 0, 0, 0)
        grid_sizer_1.Add(self.EPSG, 0, 0, 0)
        grid_sizer_1.Add(self.password, 0, 0, 0)
        grid_sizer_1.Add(self.passwordInput, 0, 0, 0)
        grid_sizer_1.Add(self.epsgList, 0, 0, 0)
        sizer_2.Add(grid_sizer_1, 0, wx.EXPAND, 0)
        sizer_4.Add(self.GetCapabilities, 0, 0, 0)
        sizer_4.Add(self.GetMaps, 0, 0, 0)
        sizer_4.Add(self.addServer, 0, 0, 0)
        sizer_2.Add(sizer_4, 0, wx.ALIGN_CENTER_HORIZONTAL, 0)
        sizer_1.Add(
            sizer_2,
            1,
            wx.ALL
            | wx.EXPAND
            | wx.ALIGN_RIGHT
            | wx.ALIGN_BOTTOM
            | wx.ALIGN_CENTER_HORIZONTAL
            | wx.ALIGN_CENTER_VERTICAL
            | wx.SHAPED,
            0,
        )
        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
        self.Layout()
        # end wxGlade

    def OnGetCapabilities(self, event):  # wxGlade: wmsFrame.<event_handler>
        """
        @description: called on press of getCapabilities button. Performs fetching of the getCapabilties document for the selected URL.
        @todo:None
        @param self: reference variable
        @param event: event associated.
        @return: None
        """
        if self.selectedURL == "No server selected":
            message = "No Server selected"
            self.ShowMessage(message, "Warning")
            StatusBar_fields = [message]
            self.StatusBar.SetStatusText(StatusBar_fields[0], 0)
            grass.warning(message)
            return
        try:
            self.epsgList.SetSelection(0)
        except:
            message = "epsg list is empty"
            grass.warning(message)
        self.usernameInput.Enable()
        self.passwordInput.Enable()
        self.LayerTree.CollapseAndReset(self.layerTreeRoot)
        url = self.selectedURL
        url = url + "?request=GetCapabilities&service=wms&version=1.1.1"
        StatusBar_fields = ["GetCapabilities Request Sent..."]
        self.StatusBar.SetStatusText(StatusBar_fields[0], 0)
        req = Request(url)
        try:
            response = urlopen(req, None, self.timeoutValueSeconds)
            xml = response.read()
            if not isValidResponse(xml):
                message = "Invalid GetCapabilities response"
                self.ShowMessage(message, "Warning")
                StatusBar_fields = [message]
                self.StatusBar.SetStatusText(StatusBar_fields[0], 0)
                grass.warning(message)
                return
            if isServiceException(xml):
                message = "Service Exception in Get Capabilities"
                self.ShowMessage(message, "Warning")
                StatusBar_fields = [message]
                self.StatusBar.SetStatusText(StatusBar_fields[0], 0)
                grass.warning(message)
                return
            layerDataDict = parsexml2(xml)
            ld = LayerData()
            # ld.appendLayerTree(layerDataDict, self.LayerTree, self.layerTreeRoot)
            self.keyToEPSGCodes = ld.setKeyToEPSGCodes(layerDataDict)
            self.selectedEPSG = None
            self.layerDataDict1 = test(xml, self.LayerTree, self.layerTreeRoot)
            print self.layerDataDict1
            self.LayerTree.Expand(self.layerTreeRoot)
        except HTTPError, e:
            message = "The server couldn't fulfill the request."
            message = str(e)
        except URLError, e:
            message = "Failed to reach a server."
            message = str(e)
        except ValueError, e:
            message = "Value error"
            message = str(e)
        except Exception, e:
            message = "urlopen exception, unable to fetch data for getcapabilities"
            message = str(e)
        else:
            message = "Successful"

        if not message == "Successful":
            self.ShowMessage(message, "Warning")
            StatusBar_fields = [message]
            self.StatusBar.SetStatusText(StatusBar_fields[0], 0)
            grass.warning(message)
        else:
            StatusBar_fields = [message]
            self.StatusBar.SetStatusText(StatusBar_fields[0], 0)
            grass.message(message)
            # Sudeep's Code Ends
        event.Skip()

    def OnGetMaps(self, event):  # wxGlade: wmsFrame.<event_handler>
        """
        @description: called on press of getMaps button. Performs fetching of the Maps for the selected layers of a WMS Service.
        @todo:None
        @param self: reference variable
        @param event: event associated.
        @return: None
        """
        if self.selectedURL == "No server selected":
            message = "No server selected"
            grass.warning(message)
            self.ShowMessage(message, "Warning")
            StatusBar_fields = [message]
            self.StatusBar.SetStatusText(StatusBar_fields[0], 0)
            return

        if self.selectedEPSG is None:
            message = "No EPSG code selected"
            grass.warning(message)
            StatusBar_fields = [message]
            self.StatusBar.SetStatusText(StatusBar_fields[0], 0)
            self.ShowMessage(message, "Warning")
            return
        if not self.selectedEPSG.isdigit():
            message = "EPSG code selected is not a number"
            grass.warning(message)
            StatusBar_fields = [message]
            self.StatusBar.SetStatusText(StatusBar_fields[0], 0)
            self.ShowMessage(message, "Warning")
            return

        bbox = self.getBBOXParameters()
        # bbox = '584344,397868,585500,398500'
        self.url_in = self.selectedURL
        getMap_request_url = self.url_in
        getMap_request_url += (
            "?service=WMS&request=GetMap&version=1.1.1&format=image/png&width=800&height=600&srs=EPSG:"
            + self.selectedEPSG
            + "&layers="
        )
        getMap_request_url += self.layerName + "&bbox=" + bbox
        print getMap_request_url
        req = Request(getMap_request_url)
        try:
            message = "GetMaps request sent. Waiting for response..."
            StatusBar_fields = [message]
            self.StatusBar.SetStatusText(StatusBar_fields[0], 0)
            response = urlopen(req, None, self.timeoutValueSeconds)
            image = response.read()

            if isServiceException(image):
                message = "Service Exception has occured"
                self.ShowMessage(message, "Warning")
                grass.warning(message)
                StatusBar_fields = [message]
                self.StatusBar.SetStatusText(StatusBar_fields[0], 0)
            else:
                TMP = grass.tempfile()
                if TMP is None:
                    grass.fatal("Unable to create temporary files")
                outfile = open(TMP, "wb")
                outfile.write(image)
                outfile.close()
                if imghdr.what(TMP) != "png":
                    message = "Not a valid PNG Image, Unable to display Map"
                    self.ShowMessage(message, "Warning")
                    grass.warning(message)
                    StatusBar_fields = [message]
                    self.StatusBar.SetStatusText(StatusBar_fields[0], 0)
                    return
                message = "GetMap response obtained"
                grass.message(message)
                StatusBar_fields = [message]
                self.StatusBar.SetStatusText(StatusBar_fields[0], 0)
                NewImageFrame(TMP)

        except HTTPError, e:
            message = "The server couldn't fulfill the request."
            message = str(e)
        except URLError, e:
            message = "Failed to reach a server."
            message = str(e)
        except ValueError, e:
            message = "Value error"
            message = str(e)
        except Exception, e:
            message = "urlopen exception, unable to fetch data for getcapabilities"
            message = str(e)
        else:
            message = "Successful"

        if message != "Successful":
            self.ShowMessage(message, "Warning")
            grass.warning(message)
            StatusBar_fields = [message]
            self.StatusBar.SetStatusText(StatusBar_fields[0], 0)
        else:
            grass.message(message)
            StatusBar_fields = [message]
            self.StatusBar.SetStatusText(StatusBar_fields[0], 0)

        event.Skip()

    def OnEPSGList(self, event):
        """
        @description: called on selection of an epsg code from the epsg list(ComboBox) displayed. Sets self.selectedEPSG variable.
        @todo:None
        @param self: reference variable
        @param event: event associated.
        @return: None
        """
        info = self.epsgList.GetValue()
        if not info.isdigit():
            message = "Please select an EPSG Code"
            grass.warning(message)
            seld.show_message(message)
            StatusBar_fields = [message]
            self.StatusBar.SetStatusText(StatusBar_fields[0], 0)
            return
        self.selectedEPSG = info

    def OnServerList(self, event):  # wxGlade: wmsFrame.<event_handler>
        """
        @description: called on selection of a URL from ServerList(ComboBox) displayed. Sets self.selectedURL variable.
        @todo:None
        @param self: reference variable
        @param event: event associated.
        @return: None
        """
        info = self.ServerList.GetValue()
        if len(info) == 0:
            return
        urlarr = info.split(self.name_url_delimiter)
        if len(urlarr) == 2:
            try:
                uid = self.map_servernameTouid[urlarr[0]]
                self.selectedURL = self.servers[uid].url
            except KeyError, e:
                message = "key error reported"
                grass.warning(message)
        else:
            message = "Wrong format of URL selected"
            grass.warning(message)

        event.Skip()

    def OnLayerTreeActivated(self, event):  # wxGlade: wmsFrame.<event_handler>
        event.Skip()

    def OnServerListEnter(self, event):  # wxGlade: wmsFrame.<event_handler>
        event.Skip()

    def OnLayerTreeSelChanged(self, event):  # wxGlade: wmsFrame.<event_handler>"
        """
        @description: called on selection of a layer from self.LayerTree. Sets self.layerName variable.
        @todo:None
        @param self: reference variable
        @param event: event associated.
        @return: None
        """
        self.epsgList.Clear()
        self.epsgList.Append("")
        self.selectedLayerList = []
        keys = []
        self.layerName = ""
        # print len(self.LayerTree.GetSelections())
        res = ""
        self.layersString = ""
        manageLT = ManageLayerTree()
        self.selectedLayersKeys = []
        for sellayer in self.LayerTree.GetSelections():
            # res = res + ','+self.LayerTree.GetItemText(sellayer)
            manageLT.layerTreeItemDFS(self, self.LayerTree, sellayer)

            # print child
        print self.layersString[1:]
        self.layerName = self.layersString[1:]
        # print self.layerDataDict1
        self.selectedEPSG = None
        event.Skip()
        """
        for sellayer in self.LayerTree.GetSelections():
            layerNameString = self.LayerTree.GetItemText(sellayer)
            layerNameStringList = layerNameString.split(':')
            if(len(layerNameStringList)==0):
                message = 'Unable to select layers'
                self.ShowMessage(message, 'Warning')
                grass.warning(message)
                StatusBar_fields = [message]
                self.StatusBar.SetStatusText(StatusBar_fields[0], 0)
                return
            layerName = layerNameStringList[0].split('-')[1]
            key = layerNameStringList[0].split('-')[0]
            self.selectedLayerList += [layerName]
            self.layerName += ","+layerName
            keys += [key]
            lEPSG = self.keyToEPSGCodes[key]
            self.epsgList.Append('<'+layerName+'>')
            self.epsgList.AppendItems(lEPSG)
            
          
        self.layerName = self.layerName[1:]
        print self.layerName
        self.selectedEPSG = None"""

    def OnAddServer(self, event):  # wxGlade: wmsFrame.<event_handler>
        """
        @description: called on ManageServers button press. Calls AddSerevrFrame function to display GUI to Manage Servers.
        @todo:None
        @param self: reference variable
        @param event: event associated.
        @return: None
        """
        self.AddServerisClosed = False
        self.addServer.Disable()
        AddServerFrame(self)
        return

    def onAddServerFrameClose(self, msg):
        """
        @description: called when the AddServer Frame is closed. Re-enables the addServer Button
        @todo:None
        @param self: reference variable
        @param event: event associated.
        @return: None
        """
        self.AddServerisClosed = True
        self.addServer.Enable()

    def onUpdateServerListmessage(self, msg):
        """
        @description: called when the updateserverlist message is received from AddServerFrame. Updates the local server list (self.ServerList)
        @todo:None
        @param self: reference variable
        @param event: event associated.
        @return: None
        """
        self.servers = msg.data
        # self.printDict(self.servers)
        self.__update_Url_List(self.ServerList)

    def onUpdateMapListmessage(self, msg):
        """
        @description: called when the update.map_servernameTouid message is received from AddServerFrame. Updates the local dictionary
         self.map_servernameTouid . This dictionary translates servername to itd Uid.
        @todo:None
        @param self: reference variable
        @param event: event associated.
        @return: None
        """
        self.map_servernameTouid = msg.data
        # self.printDict(self.map_servernameTouid)

    def OnQuit(self, event):
        """
        @description: called when the close button is pressed. Closes the AddServerFrame if it's not closed.
        @todo:None
        @param self: reference variable
        @param event: event associated.
        @return: None
        """
        msg = ""

        if not self.AddServerisClosed:
            Publisher().sendMessage(("WMS_Menu_Close"), msg)
        self.Destroy()
        return

    def ShowMessage(self, message, type="Warning"):
        """
        @description: Display's the message as a pop-up.
        @todo:None
        @param self: reference variable
        @param message: String, message to be displayed.
        @param type: String, the type of message
        @return: None
        """
        wx.MessageBox(message, type)

    def __update_Url_List(self, ComboBox):
        """
        @description: Internal function to update ServerList(ComboBox).
        @todo:None
        @param self: reference variable
        @param ComboBox: ComboBox to be updated.
        @return: None
        """
        ComboBox.Clear()
        ComboBox.Append("")
        for key, value in self.servers.items():
            ComboBox.Append(
                value.servername
                + self.name_url_delimiter
                + value.url[0 : self.urlLength]
            )
        return

    def __populate_Url_List(self, ComboBox):
        """
        @description: Internal function to populate ServerList(ComboBox). Used to populate ServerList for the first time in the init function.
        @todo:None
        @param self: reference variable
        @param ComboBox: ComboBox to be updated.
        @return: None
        """
        self.servers, self.map_servernameTouid = getAllRows(self.soup)
        ComboBox.Append("")
        for key, value in self.servers.items():
            ComboBox.Append(
                value.servername
                + self.name_url_delimiter
                + value.url[0 : self.urlLength]
            )

        return

    def getBBOXParameters(self):
        """
        @description: to parse bounding box parameters in Grass_Region parameter.
        @todo:None
        @param self: reference variable
        @return: a string containing comma separated bounding box parameters.
        """
        n = parseGrass_Region(None, "north")
        s = parseGrass_Region(None, "south")
        e = parseGrass_Region(None, "east")
        w = parseGrass_Region(None, "west")

        if e < w:
            minx = e
            maxx = w
        else:
            minx = w
            maxx = e

        if n < s:
            miny = n
            maxy = s
        else:
            miny = s
            maxy = n

        res = str(minx) + "," + str(miny) + "," + str(maxx) + "," + str(maxy)
        return res

    def printDict(self, dict):
        for key in dict.keys():
            print "the key name is" + key + "and its value is"


# end of class wmsFrame


def DisplayWMSMenu():
    # print os.environ
    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    wms_Frame = wmsFrame(None, -1, "")
    app.SetTopWindow(wms_Frame)
    wms_Frame.Show()
    app.MainLoop()


if __name__ == "__main__":
    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    wms_Frame = wmsFrame(None, -1, "")
    app.SetTopWindow(wms_Frame)
    wms_Frame.Show()
    app.MainLoop()