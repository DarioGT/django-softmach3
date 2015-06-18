# This is an auto-generated model module by CeRTAE OMS PlugIn

from reversion.helpers import patch_admin
from .models import ProtoTable
from django.contrib import admin

# -----------------------------------------   Model  
from .actions import doModelPrototype, doDiagram, doExportPrototype, doExportProtoJson, doExport2Json , doImport4Json, doModelDiagram 
from .models import Project,  Model, Property,  Relationship  #, Prototype

class MyModelAdmin( admin.ModelAdmin ):
    actions = [ doModelPrototype, doModelDiagram, doExportPrototype, doExportProtoJson, doExport2Json, doImport4Json ]

admin.site.register(Model, MyModelAdmin)

# ------------------------------------------  Entity
from .actions import  doEntityPrototype
from .models import Entity

class MyEntityAdmin( admin.ModelAdmin ):
    actions = [ doEntityPrototype  ]

admin.site.register(Entity, MyEntityAdmin )


# ------------------------------------------  Entity
from .actions import doImportSchema, doImportOMS

class MyProjectAdmin( admin.ModelAdmin ):
    actions = [ doImportSchema, doImportOMS  ]

admin.site.register(Project, MyProjectAdmin )


# ------------------------------------------

from .models import Diagram

class MyDiagramAdmin( admin.ModelAdmin ):
    actions = [  doDiagram  ]

admin.site.register(Diagram , MyDiagramAdmin)


admin.site.register(Property )
#admin.site.register(PropertyEquivalence )

admin.site.register(Relationship )
admin.site.register( ProtoTable )

patch_admin(Project)
patch_admin(Model)
patch_admin(Entity)
patch_admin(Property)
patch_admin(Relationship)
patch_admin(Diagram)

#admin.site.register( Prototype )

#admin.site.register( Diagram )
#admin.site.register( DiagramEntity )

#admin.site.register( Service )
#admin.site.register( ServiceRef )
