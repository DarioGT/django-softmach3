# -*- coding: utf-8 -*-

import json 

from django.db import models
from django.utils import six

from protoLib.middleware import CurrentUserMiddleware
from .smbase import UserProfile 

class TeamPermissionManager(models.Manager):
 
    def get_queryset(self):
        cuser = CurrentUserMiddleware.get_user( False )

        Qs = super(TeamPermissionManager, self).get_queryset() 
        
        if not cuser or cuser.is_superuser :
            return Qs
            
        if not cuser.has_perm( "%s.%s_%s" % ( self.model._meta.app_label, 'list', self.model._meta.model_name )):
            return Qs.none()  

        userProfile = UserProfile.objects.get_or_create( user = cuser)[0]
        return Qs.filter(smOwningTeam__in=  userProfile.userTree.split(',') )


class UserPermissionManager(models.Manager):
#     PErmission manager 
 
    def get_queryset(self):
        cuser = CurrentUserMiddleware.get_user( False )

        Qs = super(UserPermissionManager, self).get_queryset() 
        
        if not cuser or cuser.is_superuser :
            return Qs
            
        if not cuser.has_perm( "%s.%s_%s" % ( self.model._meta.app_label, 'list', self.model._meta.model_name )):
            return Qs.none()  

        return Qs.filter(smOwningUser =  cuser.id )



class ProtoJSONManager(TeamPermissionManager):
     
    def __init__(self, json_fields=[], *args, **kwargs):
        self.json_fields = json_fields
        super(ProtoJSONManager, self).__init__(*args, **kwargs)
 
    def get_queryset(self):
        return JSONAwareQuerySet(self.json_fields, self.model)    
    

# from jsonfield2.managers import JSONAwareQuerySet

class JSONAwareQuerySet(models.query.QuerySet):
    def __init__(self, json_fields=[], *args, **kwargs):
        self.json_fields = json_fields
        super(JSONAwareQuerySet, self).__init__(*args, **kwargs)

    def _filter_or_exclude(self, negate, *args, **kwargs):
        extra_lookups = {}

        for lookup in kwargs:
            if lookup.split('__')[0] in self.json_fields:
                try:
                    lookupval = lookup.split('__')[1]
                except: 
                    continue 
                if lookupval in ["exact", "iexact", "in", "isnull", "contains", "icontains"]:
                    continue 
                extra_lookups[lookup] = kwargs[lookup]

        for key in extra_lookups:
            kwargs.pop(key)

        clone = super(JSONAwareQuerySet, self)._filter_or_exclude(negate, *args, **kwargs)

        if extra_lookups.keys():
            # self.json_lookups = True  
            len(clone)# Fill the cache

            # Lista de trabajo recorrida reversa para eliminar los no requeridos              
            resultlist = list( clone ) 

            # for item in itertools.product(self, extra_lookups.keys()):
            for i in range(len(resultlist)-1, -1, -1): 
                item = resultlist[ i ]
                for lookupkey in extra_lookups.keys():
                    evalresult = self._evaluate_json_lookup(item, lookupkey, extra_lookups[lookupkey])
                    if negate :  evalresult = not evalresult 
                    if not evalresult : 
                        resultlist.pop( i )
                        break

            clone._result_cache = resultlist

        return clone

    def _evaluate_json_lookup(self, item, lookup, value):
        oper = 'exact'

        evaluators = {
            'icontains': lambda item, value: item.lower() in value.lower(),
            'contains': lambda item, value: item in value,
            'in': lambda item, value: item in value,
            'iexact': lambda item, value: item.lower() == value.lower(),
            'exact': lambda item, value: item == value,
            'lt': lambda item, value: item < value,
            'lte': lambda item, value: item <= value,
            'gt': lambda item, value: item > value,
            'gte': lambda item, value: item >= value,
            'range': lambda item, value: item >= value[0] and item <= value[1],
        }

        def _getattr(obj, key):
            if isinstance(obj, dict):
                return obj[key]
            return getattr(obj, key)

        if lookup.split('__')[-1] in evaluators.keys():
            oper = lookup.split('__')[-1]
            lookup = '__'.join(lookup.split('__')[:-1])

        # DGT Verifica que el objeto json se un dictionario o lo convierte          
        field = getattr(item, lookup.split('__')[0])
        if isinstance(field, dict) : 
            jdict = field
        elif isinstance( field, ( six.string_types, six.text_type, bytes)) :
            try:
                jdict = json.loads(field)
            except :
                return False
        else: return False

        for key in lookup.split('__')[1:]:
            try:
                jdict = _getattr(jdict, key)
            except (AttributeError, KeyError):
                return False

        if isinstance( jdict, str): 
            value = str( value )
            
        return evaluators[oper](jdict, value)


    def _clone(self, *args, **kwargs):
        clone = super(JSONAwareQuerySet, self)._clone(*args, **kwargs)
        clone.json_fields = self.json_fields
        return clone


class JSONAwareManager(models.Manager):
    
    def __init__(self, json_fields=[], *args, **kwargs):
        self.json_fields = json_fields
        super(JSONAwareManager, self).__init__(*args, **kwargs)

    def get_queryset(self):
        return JSONAwareQuerySet(self.json_fields, self.model)


# https://docs.djangoproject.com/en/1.8/topics/db/managers/#manager-names        