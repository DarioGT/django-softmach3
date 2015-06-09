# -*- coding: utf-8 -*-

from django.db import models
from jsonfield2 import JSONField, JSONAwareManager

from protoLib.models import * 

"""

DGT: Tablas adicionales para automatizacion de tareas 

"""


class ProtoDefinition(models.Model):
    """
    Esta tabla guarda las definiciones de las pcls y del menu,
    es un contenedor generico para manejar documentos json modificados de lo q
    en principio es la definicion de base de los modelos Django.
    """

    code = models.CharField(unique=True, blank=False, null=False, max_length=200)
    description = models.TextField(verbose_name=u'Description', blank=True, null=True)

    # Si no esta activo no permite la ejecucion 
    # overWrite indica que debe generarse cada vez, 
    active = models.BooleanField(default = True)
    overWrite = models.BooleanField(default = False)

    metaDefinition = JSONField(default={})
    objects = JSONAwareManager(json_fields = ['metaDefinition'])


    def __str__(self):
        return self.code

    protoExt = {
        "gridConfig" : {
            "listDisplay": ["__str__", "description", "active", "overWrite"],
        }
    }



class CustomDefinition(ProtoModelBase):
    """
    maneja las definiciones por grupo 
    aqui se guardan los menus personalizados, y las customOptions
    DGT: por ahora el manejo es solo a nivel de grupos, pero dependiendo 
    el nivel de amdin, se guardara como grupo o usuario
    """

    code = models.CharField(blank=False, null=False, max_length=200)
    description = models.TextField(verbose_name=u'Descriptions', blank=True, null=True)

    # Compatibilidad con ProtoDefinition
    active = models.BooleanField(default=True)
    overWrite = models.BooleanField(default=False)

    metaDefinition = JSONField(default={})
    objects = JSONAwareManager(json_fields = ['metaDefinition'])


    def __str__(self):
        return self.code

    class Meta:
        unique_together = ('smOwningTeam', 'code',)

    protoExt = {
        "gridConfig" : {
            "listDisplay": ["__str__", "description", "smOwningTeam"]
        }
    }

