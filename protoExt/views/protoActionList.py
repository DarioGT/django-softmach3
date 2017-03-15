# -*- coding: utf-8 -*-

from django.http import HttpResponse
# from django.contrib.admin.utils import  get_fields_from_path
from django.utils.encoding import smart_str

from protoExt.utils.utilsBase import verifyList, list2dict, getReadableError

from .protoQbe import getFieldValue, getQbeFilter
from protoLib.getStuff import getModelPermission, getRowById


from protoLib.getStuff import getDjangoModel
from protoExt.utils.utilsWeb import JsonError
from . import validateRequest

import json
from protoExt.utils.utilsBase import traceError
from protoExt.views.getStuff import setContextFilter
from protoExt.views.protoGetPci import getGenericPci
from jsonfield2.utils import JSONEncoder


def protoList(request):
    #   Vista simple para cargar la informacion,

    try:
        cBase, message = prepareListEnv(request)
        if message:
            return message

    except Exception as e:
        traceError()
        message = getReadableError(e)
        return JsonError(message)

    # Fix: Cuando esta en la pagina el filtro continua en la pagina 2 y no muestra nada.
    # if ( ( cBase.page -1 ) *cBase.limit >= pRowsCount ): cBase.page = 1

#   Prepara las cols del Query
    try:
        # Obtiene las filas del cBase.modelo
        Qs = getQSet(cBase)
        cBase.totalCount = len(Qs)
        pRows = Qs[cBase.start: cBase.page * cBase.limit]
        pList = Q2Dict(cBase, pRows)
        bResult = True

    except Exception as e:
        traceError()
        message = getReadableError(e)
        return JsonError(message)

    context = json.dumps({
        'success': bResult,
        'message': message,
        'totalCount': cBase.totalCount,
        'filter': cBase.protoFilter,
        'rows': pList,
    }, cls=JSONEncoder)

    return HttpResponse(context, content_type="application/json")


def prepareListEnv(request):
    """
    Preapar las variables para los llamados de tipo lista ( list, csv )
    """
    PAGESIZE = 50

    cBase, message = validateRequest(request)
    if message:
        return None, message

    msgReturn = getGenericPci(cBase, True)
    if msgReturn:
        return None, msgReturn

    cBase.fieldsDict = list2dict(cBase.protoMeta['fields'], 'name')

#   Parametros de la consulta
    cBase.protoFilter = verifyList(request.POST.get('protoFilter', []))
    cBase.baseFilter = verifyList(request.POST.get('baseFilter', []))
    cBase.sort = verifyList(request.POST.get('sort', []))

#   Tree Grid 
    cBase.node = request.POST.get('node', '')

#   zoomFilter
    cBase.zoomParams = request.POST.get('zoomParams', '')
    if len(cBase.zoomParams):
        cBase.zoomParams = json.loads(cBase.zoomParams)

    cBase.start = int(request.POST.get('start', 0))
    cBase.page = int(request.POST.get('page', 1))
    cBase.limit = int(request.POST.get('limit', PAGESIZE))

    cBase.jsonLookups = []
    cBase.jsonSorters = []
    cBase.qsLookups = []
    cBase.contextFilter = []

    return cBase, message


def getSortOrder(cBase):

    #   Order by
    localSort = cBase.protoMeta.get('localSort', False)
    if not localSort:
        for sField in cBase.sort:

            sName = sField['property']
            if cBase.isProtoModel:
                
                if sName.split('__')[0] in ['smInfo', cBase.jsonField]:
                    cBase.jsonSorters.append(sField)
                    continue

                # Permite el ordenamiento sobre la funcion de presentacion
                if sName == '__str__':
                    sName = 'smNaturalCode'

                # Permite el ordenamiento sobre maestros e impide sobre
                # jsofield
                elif sName.split('__')[0] in ['smInfo', cBase.jsonField]:
                    cBase.jsonSorters.append(sField)
                    continue

            # __str__ is not sortable
            if sName == '__str__':
                continue

            if sField['direction'] == 'DESC':
                sName = '-' + sName
            cBase.orderBy.append(sName)

    cBase.orderBy = tuple(cBase.orderBy)


def setZoomFilter(cBase):
    """
    cBase.zoomParams [  
        zoomFilter : contenido del zoomFilter , 
        baseRow    : los datos actuales del registro    
    ]

    Adiciona los filtros a la coleccion cBase.contextFilter 
    retorna : Void 

    * Pueden existir varios filtros q seran separados por ;  

    @filter : patron pais-ciudad implica que deb filtrarse la ciudad por el pais q se encuentra en algun campo del registro, 
    campobase : primero se necesita saber cual es el campo del registro q contiene el pais,  se toma de regData 
    campozoom : luego a que campo del filtro del zoom debe aplicarse, 

    zommFilter : fieldBase, fieldZoom; .. 
    """

    if not cBase.zoomParams:
        return

    # ; permiter separar los filtros 
    for lFilter in cBase.zoomParams.get('zoomFilter').replace(' ', '').split(';'):
        if len(lFilter) == 0:
            continue
        sFilter = _getZoomFilter(lFilter, cBase)

        if not sFilter:
            continue
        cBase.contextFilter.append(sFilter)


def _getZoomFilter(zoomFilter, cBase):
    """ 
    Genera el objeto filterStmt 
    """

    # Debe contener al menos una "," para separar property, filterStmt
    # El filtro siempre sera  property = filterStmt
        # document, Capacity  produce {'property': 'document', 'filterStmt': 'Capacity'}

    # filterStmt puede ser un valor en la fila base para ello se decora con @ 
        # document, @document  produce {'property': 'document', 'filterStmt': 'contenido de la prop document en la fila '}
    
    if zoomFilter.find(',') < 0:
        return

    nProp, nFilter = zoomFilter.split(',')

    # Fixed filter 
    if nFilter[0] != '@': 
        vFilter = nFilter 
    else: 
        vFilter = cBase.zoomParams.get('baseRow').get(nFilter[1:])

    return {'property': nProp, 'filterStmt': vFilter}


def getQSet(cBase):
    """
    Get QuerySet

    1. Ordena y filtra
    2. Filtra Json 
    3. Limita 
    """
    cBase.viewEntity = cBase.protoMeta.get('viewEntity', '')
    cBase.model = getDjangoModel(cBase.viewEntity)

    cBase.isProtoModel = hasattr(cBase.model, '_protoObj')
    cBase.isPJsonModel = hasattr(cBase.model, '_protoJson')
    cBase.jsonField = cBase.protoMeta.get('jsonField', '')
    if cBase.isPJsonModel:
        cBase.jsonField = 'smInfo'

    cBase.fakeId = hasattr(cBase.model, '_fakeId')
    cBase.orderBy = []


#   Tree Grid Filter
#   El manejo de arboles en la grilla maneja un filtro para expandir lo nodos 
#   Si no hay filtro por pk solo leerse los de primer nivel ( autoreferncia == None ) 
    if not hasattr ( cBase, 'pciStyle' ): 
        cBase.pciStyle = 'grid'  


    if cBase.pciStyle == 'tree':
        treeRefField = cBase.protoMeta.get( 'treeRefField', 'pk')  
        if cBase.node == 'root' :
            cBase.baseFilter.append ( {'filterStmt': '=', 'property': treeRefField  } )
        else:
            cBase.baseFilter.append ( {'filterStmt': cBase.node, 'property': treeRefField  } )

#         Node properties 
#         rowdict[ 'viewEntity' ] = cBase.protoMeta.get('viewEntity', '')
#         rowdict[ 'leaf' ] = False; 
#         rowdict[ 'children' ] = []


    setContextFilter(cBase)
    setZoomFilter(cBase)

#   Autentica '
    if not getModelPermission(cBase.userProfile.user, cBase.model, 'list'):
        return cBase.model.objects.none()

#   Separa los filtros
    for sFilter in cBase.baseFilter + cBase.protoFilter + cBase.contextFilter:
        fieldName = sFilter['property']
        if fieldName.startswith(cBase.jsonField + '__'):
            cBase.jsonLookups.append(sFilter)
        else:
            cBase.qsLookups.append(sFilter)

    getSortOrder(cBase)
    QStmt = getQbeFilter(cBase, cBase.qsLookups)

    Qs = cBase.model.objects.filter(QStmt).order_by(*cBase.orderBy)

    if cBase.jsonLookups:
        QStmt = getQbeFilter(cBase, cBase.jsonLookups)
        # se require para el jsonField, debe ir en **kwargs
        QTmp = dict((x, y) for x, y in QStmt.children)
        Qs = Qs.filter(**QTmp)

    return Qs


def Q2Dict(cBase, pRows, userNodes=[]):
    """
    return the row list from given queryset
    """

    rows = []
    relModels = {}      # Tablas de zoom para absorcion de campos

    # cBase.udpFields = []

    # Alimenta la coleccion de zooms, por cada campo pues hay q hacer un
    # select para esto
    for lField in cBase.protoMeta['fields']:
        fName = lField['name']
        myZoomModel = lField.get('zoomModel', '')
        if (len(myZoomModel) > 0) and (myZoomModel != cBase.protoMeta['viewEntity']):
            relModels[fName] = {
                'zoomModel': myZoomModel, 'fkId': lField.get('fkId', ''), 'loaded': False}

    # Verifica si existen reemplazos por hacer ( cpFromField )
    # 1.  Marca los zooms q estan referenciados
    bCopyFromFld = False
    for lField in cBase.protoMeta['fields']:
        fName = lField['name']
        if (lField.get('cpFromField') is None or lField.get('cpFromZoom') is None):
            continue

        bCopyFromFld = True
        lField['isAbsorbed'] = True

        # Marca el zoom
        try:
            relModel = relModels[lField.get('cpFromZoom')]
            relModel['loaded'] = True
        except:
            pass

    # 2.  borra los q no tienen marca
    lAux = list(relModels.keys())
    for relName in lAux:
        relModel = relModels[relName]
        if not relModel['loaded']:
            del relModels[relName]

    #   Esta forma permite agregar las funciones entre ellas el __unicode__
    rowId = 0
    for rowData in pRows:
        rowId += 1
        rowdict = {}

        # limpia los datos de tablas relacionadas
        for relName in relModels:
            relModel = relModels[relName]
            relModel['rowData'] = {}
            relModel['loaded'] = False

        # recorre los campos para obtener su valor
        for lField in cBase.protoMeta['fields']:
            fName = lField['name']
            pName = lField.get('physicalName', fName)

            if lField.get('crudType') == "screenOnly":
                continue

            elif (lField.get('type', 'none') in ['protoN2N', 'none']):
                continue

            # Si el campo es absorbido ( bCopyFromFld es un shortcut para
            # evitar la evulacion en caso de q no haya ningun cpFromField )
            elif bCopyFromFld and (lField.get('isAbsorbed', False)):
                continue

            rowdict[fName] = getFieldValue(
                pName, lField.get('type', 'string'), rowData, cBase)

        # Realiza la absorcion de datos provenientes de un zoom
        if bCopyFromFld:
            rowdict = copyValuesFromFields(cBase, rowdict, relModels)


        # Agrega el Id Siempre como idInterno ( no representa una col,
        # idProperty )
        rowdict['id'] = rowData.pk
        if cBase.fakeId:
            rowdict['id'] = rowId

        # Agrega la fila al diccionario
        rows.append(rowdict)

    return rows


def copyValuesFromFields(cBase, rowdict, relModels):
    """
    Permite copiar campos q vienen de los zooms,
    En el caso de prototipos hace un select a la instancia relacionada
    """

    for lField in cBase.protoMeta['fields']:
        cpFromField = lField.get('cpFromField')
        if not cpFromField:
            continue

        fName = smart_str(lField['name'])
        cpFromField = smart_str(cpFromField)

        if not lField.get('isAbsorbed', False):
            # Es un copy q puede ser resuelto a partir del cBase.modelo objeto
            # esta es la situacion normal cuando no se idetifica un cBase.modelo y se cargan los datos por jerarquia
            # por ahora requiere q el campo este tambien en el cBase.modelo (
            # se puede cambiar si hay la necesidad )

            # Se uso para copiar cosas de discretas,  debia poner por defecto el vr en el campo
            # Si ya contiene algun valor, sale, solo copia cuando es nulo.
            val = rowdict.get(fName, None)
            if (val) and smart_str(val).__len__() > 0:
                continue

            val = rowdict.get(cpFromField, None)
            if (val is None):
                val = ''

        else:
            # Esta es la situacion de los prototipos q requieren el cpFromZoom,
            # se hace un select adicional para obtner el registro relacionado

            cpFromZoom = lField.get('cpFromZoom')

            try:
                relModel = relModels[cpFromZoom]
            except:
                # para envitar volverlo a leer, si son varios campos del mismo
                # registro
                relModel = {'loaded': True, 'rowData': None}

            if not relModel['loaded']:
                # Obtiene el id
                rowId = rowdict[relModel['fkId']]
                if rowId:
                    relModel['rowData'] = getRowById(
                        relModel['zoomModel'], rowId)
                else:
                    relModel['rowData'] = None
                relModel['loaded'] = True

            rowData = relModel['rowData']
            if rowData is not None:
                # interpreta los datos del registro
                val = getFieldValue(
                    cpFromField, lField['type'], rowData, cBase)
            else:
                val = ''

        rowdict[fName] = val

    return rowdict
