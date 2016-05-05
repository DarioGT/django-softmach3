# -*- coding: utf-8 -*-

import json
from protoLib.getStuff import getUserProfile
from protoExt.models import CustomDefinition, ViewDefinition


DOCUMENTS = ('Artefact', 'Capacity', 'Requirement')


def doBuildRaiMenu(request, queryset):
    """ 
    Build Rai Menu  
    """

    currentUser = request.user
    userProfile = getUserProfile(currentUser)
    viewIcon = 'icon-1'

#-- RAI Auto Menu ( documents and selected documents  )
    lMenu = {}
    Ix = 0
    for document in DOCUMENTS:
        lMenu[document] = {
            'text': document.lower(),
            'expanded': True,
            'index':  Ix,
            'iconCls': 'rai_{}'.format(document[:3].lower()),
            'leaf': False,
            'children': [],
        }
        Ix += 1

    for pDoc in queryset:

        viewCode = 'rai01ref.{0}{1}.{2}'.format( pDoc.document , str(pDoc.pk))
        model_dict = {
            'viewCode': viewCode,
            'text': pDoc.dtype,
            'index': Ix,
            'iconCls': viewIcon,
            'leaf': True,
        }
        Ix += 1

        lMenu[pDoc.document]['children'].append(model_dict)

        # Delete previous definition
        ViewDefinition.objects.filter(code=viewCode).delete()


#-- Update Menu in customDefinition -----------------------------------------------------

    viewCode = '__menu'
    protoDef = CustomDefinition.objects.get_or_create(
        code=viewCode, smOwningTeam=userProfile.userTeam,
        defaults={'active': False, 'code': viewCode,
                  'smOwningTeam': userProfile.userTeam}
    )[0]

    # El default solo parece funcionar al insertar en la Db
    if not protoDef.active:
        return {'success': False, 'message': 'Menu not found'}

    menuData = protoDef.metaDefinition


#-- Update  Db ------------------------------------------------------

    try:
        raiMenu = menuData[0]
        if str(raiMenu['text']) == str('RAI MENU'):
            raiMenu = menuData.pop(0)
    except:
        pass

    raiMenu = {
        'text': 'RAI MENU',
        'expanded': False,
        'index':  0,
        'leaf': False,
        'children': [],
    }

    # Python 2 et 3
    try:
        values = lMenu.itervalues()
    except AttributeError:
        values = lMenu.values()

    for raiDoc in values:
        raiMenu['children'].append(raiDoc)

    menuData.insert(0, raiMenu)

    protoDef.metaDefinition = json.dumps(menuData)
    protoDef.save()

    return {'success': False, 'message': 'Menu not found'}
