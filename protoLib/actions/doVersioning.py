# -*- coding: utf-8 -*-
from protoLib.getStuff import getDjangoModel
from protoExt.utils.utilsWeb import JsonError
from protoExt.views.protoGrid import getModelDetails
from protoLib.models.versions import VersionHeaders


def doDeleteVersion(modeladmin, request, queryset, parameters):
    """ 
    TODO : Borra los datos de una version existente
    """

    result = getDetailList( modeladmin, request, queryset, parameters )
    if type(result) == list:
        return result 


def doCreateVersion(modeladmin, request, queryset, parameters):
    """ 
    Clear una copia de la informacion bajo una nueva version 
    """

    result = getDetailList( modeladmin, request, queryset )
    if type(result) is not list:
        return result 

    idList0 = []
    idList1 = []

#   Get selected version
    v0 = queryset[0].versionBase 
    v1 = queryset[0].versionCode 

    for pEntity in  result: 
        if not hasattr( pEntity, 'smVersion'): 
            continue 

        #  Se asegura de borrar para no sobre escribir 
        pEntity.objects.filter( smVersion = v1 ).delete()

        #  Hace la copia
        for reg in pEntity.objects.filter( smVersion = v0 ): 
            
            idList0.append( reg.pk )

            reg.smUUID = newUUId 
            reg.smVersion = v1 
            reg.id = None 
            reg.save()

            idList1.append( newUUId )

        # Busca todas los foreignkey  por UUID y los actualiza 


    return {'success':True, 'message' : 'Ok'}


def getDetailList( modeladmin, request, queryset  ):


#   El QSet viene con la lista de Ids  
    if queryset.count() != 1:
        return  {'success':False, 'message' : 'One version needed !!' }
        
    detailList = []
    detailNames = []

#   Get Version Headers 
    for entity in VersionHeaders.objects.all(): 
        addDetailToVersionList( detailNames, detailList,  entity.modelCType.model_class()  )

    return  detailList 


def addDetailToVersionList( detailNames, detailList, model ):

    #  only the last element for dependencies 
    # try:    
    #     ix = detailNames.index (  model._meta.db_table )
    #     del detailNames[ix]
    #     del detailList[ix]
    # except: 
    #     pass 

    detailList.append ( model ) 
    # detailNames.append ( model._meta.db_table ) 

    for detail in model._meta.get_all_related_objects():
        addDetailToVersionList( detailNames, detailList, detail.related_model )

