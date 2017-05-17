# -*- coding: utf-8 -*-
# Copyright (C) 2014-2017 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2017 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2017 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2017 Alejandro Alonso <alejandro.alonso@kaleidos.net>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from django.core.exceptions import ObjectDoesNotExist
from django.contrib.contenttypes.models import ContentType

from taiga.base.api import serializers
from taiga.base.fields import Field, MethodField, DateTimeField
from taiga.projects.history import models as history_models
from taiga.projects.attachments import models as attachments_models
from taiga.projects.history import services as history_service

from .fields import (UserRelatedField, HistorySnapshotField, HistoryUserField,
                     HistoryDiffField, HistoryValuesField, FileField)


class HistoryExportSerializer(serializers.LightSerializer):
    user = HistoryUserField()
    diff = HistoryDiffField()
    snapshot = HistorySnapshotField()
    values = HistoryValuesField()
    comment = Field()
    delete_comment_date = DateTimeField()
    delete_comment_user = HistoryUserField()
    comment_versions = Field()
    created_at = DateTimeField()
    edit_comment_date = DateTimeField()
    is_hidden = Field()
    is_snapshot = Field()
    type = Field()


class HistoryExportSerializerMixin(serializers.LightSerializer):
    history = MethodField("get_history")

    def get_history(self, obj):
        history_qs = history_service.get_history_queryset_by_model_instance(
            obj,
            types=(history_models.HistoryType.change, history_models.HistoryType.create,)
        )

        return HistoryExportSerializer(history_qs, many=True).data


class AttachmentExportSerializer(serializers.LightSerializer):
    owner = UserRelatedField()
    attached_file = FileField()
    created_date = DateTimeField()
    modified_date = DateTimeField()
    description = Field()
    is_deprecated = Field()
    name = Field()
    order = Field()
    sha1 = Field()
    size = Field()


class AttachmentExportSerializerMixin(serializers.LightSerializer):
    attachments = MethodField()

    def get_attachments(self, obj):
        content_type = ContentType.objects.get_for_model(obj.__class__)
        attachments_qs = attachments_models.Attachment.objects.filter(object_id=obj.pk,
                                                                      content_type=content_type)
        return AttachmentExportSerializer(attachments_qs, many=True).data


class CustomAttributesValuesExportSerializerMixin(serializers.LightSerializer):
    custom_attributes_values = MethodField("get_custom_attributes_values")

    def custom_attributes_queryset(self, project):
        raise NotImplementedError()

    def get_custom_attributes_values(self, obj):
        def _use_name_instead_id_as_key_in_custom_attributes_values(custom_attributes, values):
            ret = {}
            for attr in custom_attributes:
                value = values.get(str(attr["id"]), None)
                if value is not None:
                    ret[attr["name"]] = value

            return ret

        try:
            values = obj.custom_attributes_values.attributes_values
            custom_attributes = self.custom_attributes_queryset(obj.project)

            return _use_name_instead_id_as_key_in_custom_attributes_values(custom_attributes, values)
        except ObjectDoesNotExist:
            return None


class WatcheableObjectLightSerializerMixin(serializers.LightSerializer):
    watchers = MethodField()

    def get_watchers(self, obj):
        return [user.email for user in obj.get_watchers()]
