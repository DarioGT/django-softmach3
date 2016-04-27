# -*- coding: utf-8 -*-

from django.db import models
from protoExt.utils.utilsConvert import slugify2
from protoLib.models.protomodel import ProtoModelBase
from rai01ref.models.mBase import DocModel
from protoLib.models.smbase import getNodeHierarchy


class Artefact(DocModel):
    refArtefact = models.ForeignKey('Artefact', blank= True, null= True, related_name='+' )
    copyFrom = models.ForeignKey('Artefact', blank= True, null= True, related_name='+' )

    @property
    def fullPath(self):
        return getNodeHierarchy(self , 'refArtefact', 'code', 'fullPath')

    # siempre sera un filtro de dos niveles, documento y tipo, 
    # la tabla de documento define el valor del documento, el tipo viene en el menu 
    _jDefValueDoc  = 'ARTEFACT'

    protoExt = { 
        "jsonField" : "info", 
        "actions": [
            { "name": "doBPD" , "selectionMode" : "sinlge" },
        ],
        "gridConfig" : {
            "listDisplay": [ "code", "description", ],
        },
        "fields" : {
          "fullPath": {"readOnly" : True},
         }    
     } 


class Capacity(DocModel):
    refCapacity = models.ForeignKey('Capacity', blank= True, null= True, related_name='+' )
    copyFrom = models.ForeignKey('Capacity', blank= True, null= True, related_name='+' )

    @property
    def fullPath(self):
        sAux = getNodeHierarchy(self , 'refCapacity', 'code', 'fullPath')
        return sAux 


    _jDefValueDoc  = 'CAPACITY'

    protoExt = { 
        "jsonField" : "info", 
        "gridConfig" : {
            "listDisplay": [ "code", "description", ],
        },
        "fields" : {
          "fullPath": {"readOnly" : True},
         }    
    } 

class Requirement(DocModel):
    refRequirement = models.ForeignKey('Requirement', blank= True, null= True, related_name='+' )
    copyFrom = models.ForeignKey('Requirement', blank= True, null= True, related_name='+' )

    @property
    def fullPath(self):
        return getNodeHierarchy(self , 'refRequirement', 'code', 'fullPath')


    _jDefValueDoc  = 'REQUIREMENT'

    protoExt = { 
        "jsonField" : "info", 
        "gridConfig" : {
            "listDisplay": [ "code", "description", ],
        },
    } 


class ArtefactComposition(ProtoModelBase):
    """ Manejo de arcos, pe. las transiciones en procesos 
    """    
    containerArt = models.ForeignKey('Artefact', blank= False, null= False, related_name='artefactcomposition_set')
    inputArt = models.ForeignKey('Artefact', blank= False, null= False, related_name='+')
    outputArt = models.ForeignKey('Artefact', blank= True, null= True, related_name='+')

    condition  = models.TextField(blank = True, null = True)

    notes = models.TextField(blank = True, null = True)
    description  = models.TextField(blank = True, null = True)

    class Meta:
        app_label = 'rai01ref'

    def __str__(self):
        try: 
            endNode = self.outputArt.code 
        except: endNode = "/*"
        return '{0} -> {1}'.format( slugify2( self.inputArt.code ), endNode ) 


class ArtefactRequirement(ProtoModelBase):
    artefact = models.ForeignKey('Artefact', blank= False, null= False)
    requirement = models.ForeignKey('Requirement', blank= False, null= False)

    notes = models.TextField(blank = True, null = True)
    description  = models.TextField(blank = True, null = True)

    def __str__(self):
        return slugify2(str( self.artefact) +  '-' + str( self.requirement))

    class Meta:
        unique_together = ('artefact','requirement')
        app_label = 'rai01ref'


class ArtefactCapacity(ProtoModelBase):
    artefact = models.ForeignKey('Artefact', blank= False, null= False)
    capacity = models.ForeignKey('Capacity', blank= False, null= False)

    notes = models.TextField(blank = True, null = True)
    description  = models.TextField(blank = True, null = True)

    def __str__(self):
        return slugify2(str( self.artefact) +  '-' + str( self.capacity))

    class Meta:
        unique_together = ('artefact','capacity')
        app_label = 'rai01ref'



class Projet(ProtoModelBase):
    code = models.CharField(blank= False, null= False, max_length= 200)

    notes = models.TextField(blank = True, null = True)
    description  = models.TextField(blank = True, null = True)


    def __str__(self):
        return slugify2( self.code )

    class Meta:
        app_label = 'rai01ref'



class ProjectArtefact(ProtoModelBase):
    projet = models.ForeignKey('Projet', blank= False, null= False)
    artefact = models.ForeignKey('Artefact', blank= False, null= False)

    notes = models.TextField(blank = True, null = True)
    description  = models.TextField(blank = True, null = True)

    def __str__(self):
        return slugify2(str(self.artefact) +  '-' + str( self.projet))

    class Meta:
        unique_together = ('artefact','projet')
        app_label = 'rai01ref'


class ProjectCapacity(ProtoModelBase):

    projet = models.ForeignKey('Projet', blank= False, null= False)
    capacity = models.ForeignKey('Capacity', blank= False, null= False)

    notes = models.TextField(blank = True, null = True)
    description  = models.TextField(blank = True, null = True)

    def __str__(self):
        return slugify2(str( self.projet) +  '-' + str( self.capacity))

    class Meta:
        unique_together = ('projet','capacity')
        app_label = 'rai01ref'


class ProjectRequirement(ProtoModelBase):
    projet = models.ForeignKey('Projet', blank= False, null= False)
    requirement = models.ForeignKey('Requirement', blank= False, null= False)

    notes = models.TextField(blank = True, null = True)
    description  = models.TextField(blank = True, null = True)

    def __str__(self):
        return slugify2(str( self.projet) +  '-' + str( self.requirement))

    class Meta:
        unique_together = ('projet','requirement')
        app_label = 'rai01ref'



class Source(ProtoModelBase):
    """ Document source Localisation  
    """
    code = models.CharField(blank= False, null= False, max_length= 200)
    reference = models.CharField(blank= True, null= True, max_length= 200)

    notes = models.TextField(blank = True, null = True)
    description  = models.TextField(blank = True, null = True)

    def __str__(self):
        return slugify2(self.code)

    class Meta:
        app_label = 'rai01ref'


class ArtefactSource(ProtoModelBase):
    source = models.ForeignKey('Source', blank= True, null= True)
    artefact = models.ForeignKey('Artefact', blank= True, null= True)

    notes = models.TextField(blank = True, null = True)
    description  = models.TextField(blank = True, null = True)

    def __str__(self):
        return 'NoKey'

    class Meta:
        unique_together = ('source', 'artefact')
        app_label = 'rai01ref'

