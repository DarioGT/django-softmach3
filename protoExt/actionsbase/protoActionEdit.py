# -*- coding: utf-8 -*-

# import traceback


import json
from django.http import HttpResponse
from django.db import models
from django.utils.encoding import smart_str

from protoExt.models import ViewDefinition
from protoLib.getmodels import getDjangoModel

from .protoActionList import Q2Dict

from protoExt.utils.utilsConvert import toInteger, toDate, toDateTime, toTime, toFloat, toDecimal, toBoolean
from protoExt.utils.utilsBase import JSONEncoder, getReadableError, list2dict
from protoExt.utils.utilsWeb import doReturn

from protoLib.getmodels import getUserProfile, getModelPermissions, getUserNodes

# Error Constants
ERR_NOEXIST = '<b>ErrType:</b> KeyNotFound<br>The specifique record does not exist'
ERR_REFONLY = '<b>ErrType:</b> RefOnly<br>The specifique record is reference only'

# Actions 
ACT_INS = 'add'
ACT_UPD = 'change'
ACT_DEL = 'delete'


def protoCreate(request):
    myAction = ACT_INS
    msg = _protoEdit(request, myAction)
    return  msg

def protoUpdate(request):
    myAction = ACT_UPD
    return _protoEdit(request, myAction)

def protoDelete(request):
    myAction = ACT_DEL
    return _protoEdit(request, myAction)

def _protoEdit(request, myAction):

    if not request.user.is_authenticated():
        return doReturn ({'success':False , 'message' : 'readOnly User'})

    if request.method != 'POST':
        return doReturn ({'success':False, 'message' : 'invalid message'})

    message = ''

#   Carga el modelo
#   protoMeta = request.POST.get('protoMeta', '')
#   protoMeta = json.loads(protoMeta)
    viewCode = request.POST.get('viewCode', '')
    try:
        protoDef = ViewDefinition.objects.get(code=viewCode)
        protoMeta = json.loads(protoDef.metaDefinition)
    except Exception as e :
        return doReturn ({'success':False , 'message' : 'ViewDefinition {0} not found '.format( viewCode) })


    viewEntity = protoMeta.get('viewEntity', '')
    model = getDjangoModel(viewEntity)

#   Autentica
    if not getModelPermissions(request.user, model, myAction):
        return doReturn ({'success':False , 'message' : 'No ' + myAction + 'permission'})

#   Obtiene el profile para saber el teamhierarchi
    userProfile = getUserProfile(request.user, 'edit', viewEntity)


#   Verfica si es un protoModel ( maneja TeamHierarchy )
    isProtoModel = hasattr(model , '_protoObj')
    isPJsonModel = hasattr(model , '_protoJson')


#   Verifica si hay registros que son solo de referencia
    userNodes = []
    refAllow = False
    if myAction in [ACT_DEL, ACT_UPD] and isProtoModel and not request.user.is_superuser  :
        refAllow = getModelPermissions(request.user, model, 'refallow')
        if refAllow:
            userNodes = getUserNodes(request.user, viewEntity)

#   WorkFlow
    hasWFlow = hasattr(model , '_WorkFlow') and isProtoModel
    if hasWFlow:
        wfadmin = getModelPermissions(request.user , model, 'wfadmin')
        WFlowControl = getattr(model, '_WorkFlow', {})
        initialWfStatus = WFlowControl.get('initialStatus', '0')

#   Decodifica los eltos
    rows = request.POST.get('rows', [])
    rows = json.loads(rows)


#   Fields 
    fieldsDict = list2dict(protoMeta[ 'fields' ], 'name')

#   JsonField
    jsonField = protoMeta.get('jsonField', '')

    # Verifica q sea una lista de registros, (no deberia pasar, ya desde Extjs se controla )
    if type(rows).__name__ == 'dict':
        rows = [rows]


    pList = []
    for data in rows:

        data['_ptStatus'] = ''

        if myAction == ACT_INS:
            rec = model()
        else:
            try:
                rec = model.objects.get(pk=data['id'])
            except:
                data['_ptStatus'] = data['_ptStatus'] + ERR_NOEXIST + '<br>'
                pList.append(data)
                continue


        # refAllow verifica si corresponde a los registros modificables  ( solo es true en myAction in [ACT_DEL, ACT_UPD] )
        if refAllow and isProtoModel :
            if not (str(rec.smOwningTeam_id) in userNodes) :
                data['_ptStatus'] = ERR_REFONLY + '<br>'
                pList.append(data)
                continue

        if not (myAction == ACT_DEL):
            # Upd, Ins
            for key in data:
                key = smart_str(key)
                if  key in ['id', '_ptStatus', '_ptId', '__str__']:
                    continue

                vFld = fieldsDict[key]
                if vFld.get('crudType')  in ["screenOnly", "linked" ]:
                    continue

                #  Los campos de seguridad se manejan a nivel registro
                if isProtoModel:
                    if key in ['smOwningUser', 'smOwningTeam', 'smOwningUser_id', 'smOwningTeam_id', 'smCreatedBy',  'smModifiedBy', 'smCreatedBy_id',  'smModifiedBy_id', 'smCreatedOn', 'smModifiedOn', 'smWflowStatus', 'smRegStatus', 'smUUID']:
                        continue

                #  JsonField
                if key == jsonField or key.startswith(jsonField + '__'):
                    continue

                try:
                    setRegister(model, rec, key, data)
                except Exception as e:
                    data['_ptStatus'] = data['_ptStatus'] + getReadableError(e)

            if isProtoModel:
                setSecurityInfo(rec, data, userProfile, (myAction == ACT_INS))


            if len(jsonField) > 0:
                jsonInfo = {}
                for key in data:
                    if not key.startswith(jsonField + '__'):
                        continue
                    jKey = key[ len(jsonField) + 2 : ]
                    jsonInfo[ jKey ] = data[ key ]
                setattr(rec, jsonField , jsonInfo)


            # Inicializa el estado del WF
            if hasWFlow:
                setattr(rec, 'smWflowStatus' , initialWfStatus)

            # Guarda el idInterno para concatenar registros nuevos en la grilla
            try:
                _ptId = data['_ptId']
            except:
                _ptId = ''

            try:
                rec.save()

                # -- Los tipos complejos ie. date, generan un error, es necesario hacerlo detalladamente
                # Convierte el registro en una lista y luego toma solo el primer elto de la lista resultado.
                data = Q2Dict(protoMeta , [rec], False)[0]
                data['_ptId'] = _ptId

            except Exception as  e:
                data['_ptStatus'] = data['_ptStatus'] + getReadableError(e)
                data['_ptId'] = _ptId
                # traceback.print_exc()
                # return doReturn ({'success':False ,'message' : str( e )})

        else:# Action Delete
            try:
                rec.delete()

            except Exception as e:
                data['_ptStatus'] = data['_ptStatus'] + getReadableError(e)

        pList.append(data)

        if data.get('_ptStatus', ''):
            message += data['_ptStatus'] + ';'



    context = {
        'totalCount': pList.__len__(),
        'message': message,
        'rows': pList,
        'success': True
    }

    return HttpResponse(json.dumps(context, cls=JSONEncoder), content_type="application/json")


def setSecurityInfo(rec, data, userProfile, insAction):
    """
    rec      : record that the security info is added
    data     : buffer object {} that can be used to return the saved info
    insAction: True if insert,  False if update
    """
    setProtoData(rec, data, 'smModifiedBy', userProfile.user)


    if insAction:
        setProtoData(rec, data, 'smOwningUser', userProfile.user)
        setProtoData(rec, data, 'smOwningTeam', userProfile.userTeam)
        setProtoData(rec, data, 'smCreatedBy', userProfile.user)
        setProtoData(rec, data, 'smRegStatus', '0')


# ---------------------

def setProtoData(rec, data, key, value):
    setattr(rec, key, value)
    if not isinstance(value, models.Model):
        data[ key ] = value


def setRegister(model, rec, key, data):

    try:
        field = model._meta.get_field(key)
    except:
        return

    # Tipo de attr
    cName = field.__class__.__name__

    # Si es definido como no editable en el modelo
    if getattr(field, 'editable', False) == False:
        return
    if  cName == 'AutoField':
        return

    # Obtiene el valor
    value = data[key]

    try:

        if cName == 'CharField' or cName == 'TextField':
            setattr(rec, key, value)
            return

        elif  cName == 'ForeignKey':
            keyId = key + '_id'
            value = data[keyId]
            exec('rec.' + keyId + ' =  ' + smart_str(value))
            return

        elif cName == 'DateField':
            value = toDate(value)
        elif cName == 'TimeField':
            value = toTime(value)
        elif cName == 'DateTimeField':
            value = toDateTime(value)

        elif cName == 'BooleanField':
            value = toBoolean(value)
        elif cName == 'IntegerField':
            value = toInteger(value)
        elif cName == 'DecimalField':
            value = toDecimal(value)
        elif cName == 'FloatField':
            value = toFloat(value)

        setattr(rec, key, value)

    except Exception:
        raise Exception
