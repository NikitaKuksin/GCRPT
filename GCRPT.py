import json
from ttkthemes import ThemedTk
from tkinter import ttk,SOLID,END
import pickle
from copy import deepcopy

class Element:

    type = None
    name = None
    padx = None
    pady = None
    sticky = None
    row = None
    column = None
    parent = None
    children = None
    font = None
    lable = None
    element = None
    master = None

    def __init__(self, json, parent=None):
        self.type = json["Type"]
        self.name = json["Name"]
        self.padx = json["Padx"]
        self.pady = json["Pady"]
        self.sticky = json["Sticky"]
        self.row = json["Row"]+1
        self.column = json["Column"]
        self.parent = parent
        self.children = []
        return self
    
    def InitializeElement(self):
        if( self.parent != None ):
            self.parent.children.append(self)
            self.parent.element.rowconfigure( self.row,weight=1 )
            self.parent.element.columnconfigure( self.column,weight=1 )
            self.master = self.parent.element
        self.label = ttk.Label(text=self.name,master=self.master)
        self.label.grid(row=self.row,column=self.column,padx=self.padx,pady=self.pady,sticky=self.sticky)

    def GetElement(self):
        return self.element

    def SetValue(self, value):
        self.name = str(value)
    
    def GetValue(self):
        return self.name

class Aplication(Element):

    geometry = None
    theme = None

    def __init__(self, json, parent=None):
        self.name = json["Name"]
        self.geometry = json["Geometry"]
        self.theme = json["Theme"]
        self.children = []

    def InitializeElement(self):
        self.element = ThemedTk( fonts=True, themebg=True)
        self.element.geometry( self.geometry )
        self.element.title(self.name)
        self.element.resizable(width=False, height=False)
        self.element.set_theme(self.theme)

class Frame(Element):

    def __init__(self, json, parent=None):
        super().__init__( json, parent=parent)

    def InitializeElement(self):
        if( self.parent != None ):
            self.parent.children.append(self)
            self.parent.element.rowconfigure( self.row,weight=1 )
            self.parent.element.columnconfigure( self.column,weight=1 )
            master = self.parent.element
        self.element = ttk.Frame(master=master,borderwidth=1,relief=SOLID)
        self.element.grid(row=self.row, column=self.column,padx=self.padx,pady=self.pady,sticky=self.sticky)
        labelScale = ttk.Label(master=self.element,text=self.name,font=("Arial", 14))
        labelScale.grid( row=0,column=0,padx=self.padx,pady=self.pady,sticky="nw"  )

class Lable(Element):

    def __init__(self, json, parent=None):
        
        super().__init__(json, parent=parent)
        self.text = json["Text"]
        self.patternText = json["PatternText"] 

    def InitializeElement(self):
        super().InitializeElement()
        self.element = self.label
        self.SetValue({"value":self.text})

    def SetValue(self, value):
        self.element["text"] = self.patternText.format(value["value"])        
        if( "background" in value.keys() and "foreground" in value.keys()  ):
            self.element.configure(background=value["background"],foreground=value["foreground"])

class InputElement(Element):

    dependents = None
    root = None
    dominants = None  

    def __init__(self, json, root=None, parent=None):
        super().__init__( json, parent=parent )
        self.root = root
        self.dominants = {}
        if( "Dependents" in json.keys() ):
            self.dependents = []
            for dependent_json in json["Dependents"]:
                self.dependents.append( Dependent( dependent_json, self.root ) )     

    def updateDependents(self, event):
        str_value = self.element.get()
        if( str_value == '' ):
            value = 0
        else:
            try:
                value = float(str_value)
            except Exception as e:
                value = str_value

        for dependent in self.dependents:
            dependent.updateDependentElement( self.name, value )
        
        for dependent in self.dependents:
            dependent.updateDependentElement( self.name, value )
    
    def updateDominant( self, dominant, value ):
        self.dominants[ dominant ] = value 

    def SumValue( self ):
        result = 0
        for key in self.dominants.keys():
            result = result + self.dominants[key]
        return result

    def updateValue( self, dominant, value ):
        self.updateDominant( dominant, value )
        self.element.delete( 0, END )
        self.element.insert(0, str(int( self.SumValue( ) )))

    def GetValue(self):
        try:
            value = float(self.element.get())
        except Exception as e:
            value = self.element.get()
        return value

class Enter(InputElement):

    min_value = None
    max_value = None

    def __init__(self, json, parent=None, root=None):
        super().__init__( json, parent=parent, root=root)
        self.min_value = json["MinValue"]
        self.max_value = json["MaxValue"]

    def InitializeElement(self):
        super().InitializeElement()

        checkNumber = (self.master.register(self.validatecommand), "%P")
        self.element = ttk.Entry(master=self.master, validate="key", validatecommand=checkNumber) 
        self.element.grid(row=self.row,column=self.column+1,padx=self.padx,pady=self.pady,sticky=self.sticky)
        if( self.dependents != None ):
            self.element.bind("<KeyRelease>", self.updateDependents)

    def validatecommand(self,value):
        valid = True
        try:
            if( value != ""):
                value = float(value)
                if( self.min_value<0 or value>self.max_value ):
                    valid = False
        except Exception as e:
            valid = False
        return valid

class Combobox(InputElement):

    values = None

    def __init__(self, json, parent=None, root=None):
        super().__init__( json, parent=parent, root=root)
        self.values = json["Values"]

    def InitializeElement(self):
        super().InitializeElement()
        self.element = ttk.Combobox(values=self.values,master=self.master)
        self.element.grid(row=self.row,column=self.column+1,padx=self.padx,pady=self.pady,sticky=self.sticky)
        if( self.dependents != None ):
            self.element.bind("<<ComboboxSelected>>", self.updateDependents)

class Solver(InputElement):

    def __init__(self, json, parent=None, root=None):
        super().__init__( json, parent=parent, root=root)
        self.buttonText = json["ButtonText"]
        self.modelFile = json["ModelFile"]

        if( "OutputLables" in json.keys() ):
            self.outputLables = []
            for predictor_json in json["OutputLables"]:
                self.outputLables.append( OutputLable( predictor_json, self.root ) )

        if( "Predictors" in json.keys() ):
            self.predictors = []
            for predictor_json in json["Predictors"]:
                self.predictors.append( Predictor( predictor_json, self.root ) )

    def InitializeElement(self):
        if( self.parent != None ):
            self.parent.children.append(self)
            self.parent.element.rowconfigure( self.row,weight=1 )
            self.parent.element.columnconfigure( self.column,weight=1 )
            self.master = self.parent.element
        self.element = ttk.Button(text=self.buttonText,command=self.Pedict,master=self.master)
        self.element.grid( row=self.row,column=self.column,padx=self.padx,pady=self.pady,sticky=self.sticky)
        
        with open( self.modelFile, "br") as f:
            file_model = pickle.load(f)
            self.model = file_model["model"]
            self.minMaxScaler = file_model["minMaxScaler"]

    def GetPredictors(self):
        predictors_values = []
        for predictor in self.predictors:
            value = predictor.getValuePredictor()
            if( value == '' ):
                value = 0
            predictors_values.append( value )
        predictors_values = [predictors_values]    
        return predictors_values

    def printResult(self,value):
        for outputLable in self.outputLables:
            outputLable.updateValue( value )


    def Pedict(self):
        predictors_values = self.GetPredictors()
        predictors_values = self.minMaxScaler.transform( predictors_values )
        result = self.model.predict( predictors_values )
        print( result )
        self.printResult( result[0][0]*100 )

class СonnectedElement:

    path = None
    connectedElement = None
    root = None

    def __init__( self, json, root, connectedElement=None ):
        
        self.path = json["Path"]
        self.connectedElement = connectedElement
        self.root = root
    
    def FindСonnectedElement( self, names_element = None, element = None ):
        if( names_element == None ):
            names_element = self.path.split("/")
        if( element == None ):
            element = self.root

        if( len(names_element) == 0  ):
            self.connectedElement=element
            return
        elif( len(names_element) > 1 and names_element[0]==element.name ):
            names_element = names_element[1:]

        for child in element.children:
            if( child.name == names_element[0] ):
                self.FindСonnectedElement( names_element = names_element[1:],element = child )
                break

class Predictor(СonnectedElement):
    
    def __init__( self, json, root, connectedElement=None ):
        super().__init__(json, root, connectedElement=connectedElement)

    def getValuePredictor(self):
        if( self.connectedElement == None ):
            self.FindСonnectedElement()
        value = self.connectedElement.GetValue()
        return value 

class Dependent(СonnectedElement):
    
    thresholds = None

    def __init__( self, json, root, connectedElement=None ):
        super().__init__(json, root, connectedElement=connectedElement)
        self.thresholds = json["Thresholds"]

    def CalculateValue( self, value ):
        for threshold in self.thresholds:
            if( threshold["Sign"] == "equivalent" ):
                return deepcopy(value)
            elif( threshold["Sign"] == "<" ):
                if( value < threshold["Value"] ):
                    return deepcopy(threshold[ "Rating" ])
            elif( threshold["Sign"] == "<=" ):
                if( value <= threshold["Value"] ):
                    return deepcopy(threshold[ "Rating" ])
            elif( threshold["Sign"] == ">" ):
                if( value > threshold["Value"] ):
                    return deepcopy(threshold[ "Rating" ])
            elif( threshold["Sign"] == ">=" ):
                if( value >= threshold["Value"] ):
                    return deepcopy(threshold[ "Rating" ])
            elif( threshold["Sign"] == "==" ):
                if( value == threshold["Value"] ):
                    return deepcopy(threshold[ "Rating" ])
        return 0
    

    def updateDependentElement( self, dominant, value ):
        
        if( self.connectedElement == None ):
            self.FindСonnectedElement()
        value = self.CalculateValue( value )
        self.connectedElement.updateValue( dominant, value )

class OutputLable(Dependent):
    
    def __init__( self, json, root, connectedElement=None ):
        super().__init__(json, root, connectedElement=connectedElement)

    def CalculateValue( self, value ):
        result = super().CalculateValue(value)
        if( result["value"]=="__equivalent__" ):
            result["value"] = value
        return result

    def updateValue( self, value ):
        
        if( self.connectedElement == None ):
            self.FindСonnectedElement()
        value = self.CalculateValue( value )
        self.connectedElement.SetValue( value )

def loadElement( parent, elements_json, root=None ):

    element = None
    if( elements_json["Type"] == "MainFrame" ):
        element = Aplication( elements_json )
        element.InitializeElement()
        root = element
    elif( elements_json["Type"] == "Frame" ):
        element = Frame( elements_json, parent=parent )
        element.InitializeElement()
    elif( elements_json["Type"] == "Lable" ):
        element = Lable( elements_json, parent=parent )
        element.InitializeElement()
    elif( elements_json["Type"] == "Combobox" ):
        element = Combobox( elements_json, parent=parent, root=root )
        element.InitializeElement()
    elif( elements_json["Type"] == "Entery" ):
        element = Enter( elements_json, parent=parent, root=root)
        element.InitializeElement()
    elif( elements_json["Type"] == "Solver" ):
        element = Solver( elements_json, parent=parent, root=root)
        element.InitializeElement()

    for element_json in elements_json["Children"]:
        loadElement( element, element_json, root=root )

    return element       


with open(r"GUI.json","r",encoding="UTF-8") as f:
    json_file = json.load( f )

app = loadElement( None, json_file )
app.element.mainloop()




        

       
       

